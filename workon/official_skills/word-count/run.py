#!/usr/bin/env python3
# coding: utf-8
"""官方技能：文稿字数统计（纯标准库）。

统计 txt / md / docx 文稿的字数、字符数、中文字数、英文单词数、行数与段落数，
结果写入 word-count-report.json，摘要打印到 stdout。

用法：python run.py --inputs a.txt b.docx
"""
import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import unescape

CJK_RE = re.compile(r"[\u3000-\u303f\u3400-\u4dbf\u4e00-\u9fff\uff00-\uffef]")
WORD_RE = re.compile(r"[A-Za-z0-9]+(?:[-''][A-Za-z0-9]+)*")
W_T_RE = re.compile(r"<w:t[^>]*>(.*?)</w:t>", re.S)

# 按优先级尝试的文本编码，末尾有回退：都不行时用 utf-8 + replace 兜底。
ENCODINGS = ("utf-8-sig", "utf-8", "gb18030")


def decode_bytes(raw):
    """按 ENCODINGS 顺序解码字节，全部失败时用 utf-8 容错解码兜底。"""
    for enc in ENCODINGS:
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def read_text(path):
    """读取文稿文本。txt/md 试多种编码；docx 抽 word/document.xml 的文字。"""
    suffix = path.suffix.lower()
    if suffix == ".docx":
        with zipfile.ZipFile(str(path)) as zf:
            xml = zf.read("word/document.xml").decode("utf-8", "replace")
        paragraphs = []
        for para in xml.split("</w:p>"):
            parts = [unescape(m) for m in W_T_RE.findall(para)]
            paragraphs.append("".join(parts))
        return "\n".join(paragraphs), len(paragraphs)
    return decode_bytes(path.read_bytes()), None


def count_text(text, para_hint):
    chars = len(text)
    chars_no_space = len(re.sub(r"\s", "", text))
    chinese = len(CJK_RE.findall(text))
    words = len(WORD_RE.findall(text))
    lines = text.count("\n") + 1 if text else 0
    paragraphs = para_hint if para_hint is not None else sum(
        1 for line in text.splitlines() if line.strip()
    )
    return {
        "chars": chars,
        "chars_no_space": chars_no_space,
        "chinese_chars": chinese,
        "words": words,
        "lines": lines,
        "paragraphs": paragraphs,
    }


def main():
    parser = argparse.ArgumentParser(description="文稿字数统计")
    parser.add_argument("--inputs", nargs="+", required=True, help="文稿文件路径")
    args = parser.parse_args()

    files = []
    failed = []
    total = {"chars": 0, "chars_no_space": 0, "chinese_chars": 0,
             "words": 0, "lines": 0, "paragraphs": 0}
    for item in args.inputs:
        path = Path(item)
        entry = {"name": path.name}
        if not path.is_file():
            entry["error"] = "%s：文件不存在" % path.name
            failed.append(path.name)
        else:
            try:
                text, para_hint = read_text(path)
                entry.update(count_text(text, para_hint))
                for key in total:
                    total[key] += entry.get(key, 0)
            except Exception as exc:
                entry["error"] = "%s：读取失败（%s）" % (path.name, exc)
                failed.append(path.name)
        files.append(entry)

    report = {"files": files, "total": total}
    with open("word-count-report.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)

    print("文稿字数统计结果")
    print("=" * 46)
    for entry in files:
        if "error" in entry:
            print("%s ：统计失败（%s）" % (entry["name"], entry["error"]))
            continue
        print("%s ：字数 %d · 字符 %d · 中文 %d · 段落 %d" % (
            entry["name"], entry["words"] + entry["chinese_chars"],
            entry["chars"], entry["chinese_chars"], entry["paragraphs"]))
    print("-" * 46)
    success = len(files) - len(failed)
    tail = "成功统计 %d 个文件" % success
    if failed:
        tail += "，统计失败 %d 个" % len(failed)
    print("合计：字数 %d · 字符 %d · 中文 %d · 段落 %d（%s）" % (
        total["words"] + total["chinese_chars"], total["chars"],
        total["chinese_chars"], total["paragraphs"], tail))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())

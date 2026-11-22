#!/usr/bin/env python3
# coding: utf-8
"""官方技能：文本整理（纯标准库）。

整理纯文本文档：清空行、去行首尾空格、合并连续空行、批量替换词句。
结果写入 tidied/ 目录，摘要打印到 stdout。

用法：python run.py --inputs a.txt b.txt --find 旧词 --replace 新词
"""
import argparse
import sys
from pathlib import Path

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


def tidy_text(text, find, replace):
    lines = [line.rstrip() for line in text.splitlines()]
    cleaned = []
    blank = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if not blank:
                cleaned.append("")
            blank = True
            continue
        blank = False
        cleaned.append(stripped)
    while cleaned and not cleaned[-1]:
        cleaned.pop()
    result = "\n".join(cleaned)
    if result:
        result += "\n"
    if find:
        result = result.replace(find, replace or "")
    return result


def main():
    parser = argparse.ArgumentParser(description="文本整理")
    parser.add_argument("--inputs", nargs="+", required=True, help="文本文件路径")
    parser.add_argument("--find", default="", help="要替换的词句")
    parser.add_argument("--replace", default="", help="替换成的新词句")
    args = parser.parse_args()

    out_dir = Path("tidied")
    out_dir.mkdir(exist_ok=True)

    ok, failed = [], []
    for item in args.inputs:
        path = Path(item)
        if not path.is_file():
            failed.append("%s：文件不存在" % path.name)
            continue
        try:
            raw = path.read_bytes()
            text = decode_bytes(raw)
            result = tidy_text(text, args.find, args.replace)
            (out_dir / path.name).write_text(result, encoding="utf-8")
            ok.append(path.name)
        except Exception as exc:
            failed.append("%s：%s" % (path.name, exc))

    print("文本整理完成：%d 个成功" % len(ok))
    for name in ok:
        print("  ✓ %s" % name)
    for msg in failed:
        print("  ✗ %s" % msg)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())

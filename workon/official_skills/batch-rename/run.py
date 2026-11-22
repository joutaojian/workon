#!/usr/bin/env python3
# coding: utf-8
"""官方技能：文件批量重命名（纯标准库）。

四种方式：加前缀、加后缀（扩展名前）、替换词句、按顺序编号。
原文件不动，重命名后的副本放在 renamed/ 目录，对照表打印到 stdout。

用法：python run.py --inputs a.pdf b.pdf --mode prefix --text 报销单_ --find ""
"""
import argparse
import shutil
import sys
from pathlib import Path


def new_name(path, mode, text, find, index):
    stem, suffix = path.stem, path.suffix
    if mode == "prefix":
        stem = (text or "") + stem
    elif mode == "suffix":
        stem = stem + (text or "")
    elif mode == "replace":
        stem = stem.replace(find or "", text or "")
    elif mode == "number":
        stem = "%s%d" % (text or "", index)
    return stem + suffix


def main():
    parser = argparse.ArgumentParser(description="文件批量重命名")
    parser.add_argument("--inputs", nargs="+", required=True, help="文件路径")
    parser.add_argument("--mode", default="prefix",
                        choices=["prefix", "suffix", "replace", "number"])
    parser.add_argument("--text", default="", help="前缀/后缀/新词句/编号前缀")
    parser.add_argument("--find", default="", help="mode=replace 时要替换的词句")
    args = parser.parse_args()

    if args.mode == "replace" and not args.find:
        print("mode=replace 时必须填「要替换的词句」")
        return 1

    out_dir = Path("renamed")
    out_dir.mkdir(exist_ok=True)

    used, failed = set(), []
    for index, item in enumerate(args.inputs, 1):
        path = Path(item)
        if not path.is_file():
            failed.append("%s：文件不存在" % path.name)
            continue
        try:
            target = new_name(path, args.mode, args.text, args.find, index)
            if target in used:
                target = "%s_%d%s" % (Path(target).stem, index, path.suffix)
            used.add(target)
            shutil.copy(str(path), str(out_dir / target))
            print("%s  ->  %s" % (path.name, target))
        except Exception as exc:
            failed.append("%s：%s" % (path.name, exc))

    print("重命名完成：%d 个成功，结果在 renamed/ 目录" % len(used))
    for msg in failed:
        print("  ✗ %s" % msg)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())

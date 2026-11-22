#!/usr/bin/env python3
"""示例技能脚本：把输入文本原样或大写后输出。"""
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--text", required=True)
parser.add_argument("--upper", action="store_true")
args = parser.parse_args()

result = args.text.upper() if args.upper else args.text
print(result)

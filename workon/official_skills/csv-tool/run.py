#!/usr/bin/env python3
# coding: utf-8
"""官方技能：表格整理（纯标准库）。

多个表格合并成一个、整行去重、按某一列排序。
支持 csv 与 xlsx（xlsx 用 zipfile 直接解析/生成，不依赖 openpyxl）。
结果写 result.csv 与 result.xlsx，摘要打印到 stdout。

用法：python run.py --inputs a.xlsx b.csv --mode merge --column 姓名
"""
import argparse
import csv
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def read_csv(path):
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", "replace")
    rows = list(csv.reader(text.splitlines()))
    return [[cell.strip() for cell in row] for row in rows if any(c.strip() for c in row)]


def read_xlsx(path):
    with zipfile.ZipFile(str(path)) as zf:
        shared = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.findall("%ssi" % NS):
                shared.append("".join(t.text or "" for t in si.iter("%st" % NS)))
        sheet_name = next(
            (n for n in zf.namelist() if n.startswith("xl/worksheets/sheet")), None)
        if not sheet_name:
            return []
        root = ET.fromstring(zf.read(sheet_name))
        rows = []
        for row in root.iter("%srow" % NS):
            cells = []
            for cell in row.findall("%sc" % NS):
                ctype = cell.get("t", "")
                if ctype == "s":
                    value = cell.find("%sv" % NS)
                    cells.append(shared[int(value.text)] if value is not None else "")
                elif ctype == "inlineStr":
                    cells.append("".join(t.text or "" for t in cell.iter("%st" % NS)))
                else:
                    value = cell.find("%sv" % NS)
                    cells.append((value.text or "").strip() if value is not None else "")
            rows.append(cells)
        return [row for row in rows if any(c.strip() for c in row)]


def write_xlsx(path, rows):
    def col_name(idx):
        name = ""
        idx += 1
        while idx:
            idx, rem = divmod(idx - 1, 26)
            name = chr(65 + rem) + name
        return name

    lines = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
             '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
             "<sheetData>"]
    for r, row in enumerate(rows, 1):
        lines.append('<row r="%d">' % r)
        for c, value in enumerate(row):
            ref = "%s%d" % (col_name(c), r)
            text = (value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            lines.append('<c r="%s" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>' % (ref, text))
        lines.append("</row>")
    lines.append("</sheetData></worksheet>")
    sheet = "".join(lines)

    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>")
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        "</Relationships>")
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>')
    wb_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        "</Relationships>")

    with zipfile.ZipFile(str(path), "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        zf.writestr("xl/worksheets/sheet1.xml", sheet)


def main():
    parser = argparse.ArgumentParser(description="表格整理")
    parser.add_argument("--inputs", nargs="+", required=True, help="表格文件路径")
    parser.add_argument("--mode", default="merge", choices=["merge", "dedupe", "sort"])
    parser.add_argument("--column", default="", help="排序列名（mode=sort 必填）")
    args = parser.parse_args()

    rows, header, failed = [], None, []
    for item in args.inputs:
        path = Path(item)
        if not path.is_file():
            failed.append("%s：文件不存在" % path.name)
            continue
        try:
            table = read_xlsx(path) if path.suffix.lower() == ".xlsx" else read_csv(path)
            if not table:
                failed.append("%s：内容为空" % path.name)
                continue
            if header is None:
                header = table[0]
                rows.extend(table)
            else:
                for row in table[1:] if table[0] == header else table:
                    rows.append(row + [""] * (len(header) - len(row)))
        except Exception as exc:
            failed.append("%s：%s" % (path.name, exc))

    if header is None:
        print("没有读到任何数据")
        return 1

    body = rows[1:]
    removed = 0
    if args.mode == "dedupe":
        seen, body = set(), []
        for row in rows[1:]:
            key = tuple(row)
            if key in seen:
                removed += 1
                continue
            seen.add(key)
            body.append(row)
    elif args.mode == "sort":
        if not args.column:
            print("mode=sort 时必须填「排序列名」")
            return 1
        if args.column not in header:
            print("表头里没有「%s」，现有列：%s" % (args.column, "、".join(header)))
            return 1
        idx = header.index(args.column)
        body = sorted(body, key=lambda row: row[idx] if idx < len(row) else "")

    out_rows = [header] + body
    with open("result.csv", "w", encoding="utf-8-sig", newline="") as fh:
        csv.writer(fh).writerows(out_rows)
    write_xlsx("result.xlsx", out_rows)

    print("表格整理完成（%s）：共 %d 行" % (args.mode, len(out_rows)))
    print("表头：%s" % "、".join(header))
    if removed:
        print("去掉重复行：%d" % removed)
    for msg in failed:
        print("  ✗ %s" % msg)
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())

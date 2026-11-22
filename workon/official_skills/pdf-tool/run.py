#!/usr/bin/env python3
# coding: utf-8
"""官方 PDF 工具：仅用 Python 标准库实现 PDF 合并与拆分。

实现思路：
1. 字节级解析 PDF：读头部、定位 xref（含增量更新的 /Prev 链），解析间接对象；
   xref 流无法解码时退化为全文扫描对象。
2. 递归遍历 /Pages 页树收集 /Type /Page 页对象，并继承父节点的
   /Resources、/MediaBox、/CropBox、/Rotate 等属性。
3. 从页对象出发收集可达对象，重新分配对象号、修正所有引用，
   最后重建 xref 表与 trailer，输出结构完整的新 PDF。
4. 检测到加密、对象流（ObjStm）等纯标准库无法可靠处理的结构时，
   打印中文错误并以非零码退出，绝不静默产出坏文件。
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path
from typing import Any

WS = b"\x00\t\n\x0c\r "
DELIMS = b"()<>[]{}/%"


class PDFError(Exception):
    """可展示给用户的中文 PDF 处理错误。"""


class Name(str):
    """PDF 名称对象，用 str 子类以便与普通字节 token 区分。"""


class Ref:
    """间接引用：num gen R。"""

    __slots__ = ("num", "gen")

    def __init__(self, num: int, gen: int = 0):
        self.num = num
        self.gen = gen

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return f"Ref({self.num},{self.gen})"


class Raw:
    """无需解释、按原字节写回的 token（数字、布尔、字符串等）。"""

    __slots__ = ("data",)

    def __init__(self, data: bytes):
        self.data = data

    def __repr__(self) -> str:  # pragma: no cover - 调试用
        return f"Raw({self.data!r})"


class Stream:
    """带 /Length 的流式对象。"""

    __slots__ = ("dict", "data")

    def __init__(self, d: dict, data: bytes):
        self.dict = d
        self.data = data


# ---------------------------------------------------------------------------
# 词法与对象解析
# ---------------------------------------------------------------------------


class Lexer:
    def __init__(self, data: bytes, pos: int = 0):
        self.data = data
        self.pos = pos

    def skip(self) -> None:
        data = self.data
        n = len(data)
        while self.pos < n:
            c = data[self.pos]
            if c in WS:
                self.pos += 1
            elif c == 0x25:  # '%' 注释延伸到行尾
                nl = data.find(b"\n", self.pos)
                self.pos = n if nl < 0 else nl + 1
            else:
                break

    def bare_token(self) -> bytes:
        start = self.pos
        data = self.data
        while self.pos < len(data) and data[self.pos] not in WS and data[self.pos] not in DELIMS:
            self.pos += 1
        return data[start:self.pos]

    def parse_name(self) -> Name:
        if self.data[self.pos:self.pos + 1] != b"/":
            raise PDFError("解析 PDF 失败：期望名称对象（/Name）")
        self.pos += 1
        buf = bytearray()
        while self.pos < len(self.data):
            c = self.data[self.pos]
            if c in WS or c in DELIMS:
                break
            buf.append(c)
            self.pos += 1
        raw = bytes(buf)
        out = bytearray()
        i = 0
        while i < len(raw):
            if raw[i:i + 1] == b"#" and i + 2 < len(raw):
                try:
                    out.append(int(raw[i + 1:i + 3], 16))
                    i += 3
                    continue
                except ValueError:
                    pass
            out.append(raw[i])
            i += 1
        return Name(out.decode("latin-1"))

    def parse_literal_string(self) -> Raw:
        start = self.pos
        depth = 0
        while self.pos < len(self.data):
            c = self.data[self.pos]
            if c == 0x5C:  # 反斜杠转义，跳过下一个字节
                self.pos += 2
                continue
            if c == 0x28:
                depth += 1
            elif c == 0x29:
                depth -= 1
                if depth == 0:
                    self.pos += 1
                    return Raw(self.data[start:self.pos])
            self.pos += 1
        raise PDFError("解析 PDF 失败：字符串括号未闭合")

    def parse_hex_string(self) -> Raw:
        start = self.pos
        end = self.data.find(b">", self.pos)
        if end < 0:
            raise PDFError("解析 PDF 失败：十六进制字符串未闭合")
        self.pos = end + 1
        return Raw(self.data[start:self.pos])

    def parse_array(self) -> list:
        self.pos += 1  # '['
        result: list = []
        while True:
            self.skip()
            if self.data[self.pos:self.pos + 1] == b"]":
                self.pos += 1
                return result
            if self.pos >= len(self.data):
                raise PDFError("解析 PDF 失败：数组未闭合")
            result.append(self.parse_value())

    def parse_dict(self) -> dict:
        self.pos += 2  # '<<'
        result: dict = {}
        while True:
            self.skip()
            if self.data[self.pos:self.pos + 2] == b">>":
                self.pos += 2
                break
            if self.pos >= len(self.data):
                raise PDFError("解析 PDF 失败：字典未闭合")
            key = self.parse_name()
            value = self.parse_value()
            result[str(key)] = value
        return result

    def parse_value(self) -> Any:
        self.skip()
        data = self.data
        two = data[self.pos:self.pos + 2]
        one = data[self.pos:self.pos + 1]

        if two == b"<<":
            d = self.parse_dict()
            self.skip()
            if data[self.pos:self.pos + 6] == b"stream":
                return self.parse_stream(d)
            return d
        if one == b"[":
            return self.parse_array()
        if one == b"/":
            return self.parse_name()
        if one == b"(":
            return self.parse_literal_string()
        if two.startswith(b"<"):
            return self.parse_hex_string()

        token = self.bare_token()
        if not token:
            raise PDFError("解析 PDF 失败：遇到意外的文件结尾")
        # 数字 + 数字 + R 才是指示引用的形式；否则回退为普通数字 token。
        if re.fullmatch(rb"\d+", token):
            save = self.pos
            self.skip()
            second = self.bare_token()
            if re.fullmatch(rb"\d+", second):
                self.skip()
                nxt = data[self.pos:self.pos + 1]
                after = data[self.pos + 1:self.pos + 2]
                if nxt == b"R" and (not after or after in WS or after in DELIMS):
                    self.pos += 1
                    return Ref(int(token), int(second))
            self.pos = save
        return Raw(token)

    def parse_stream(self, d: dict) -> Stream:
        data = self.data
        self.pos += 6  # 'stream'
        if data[self.pos:self.pos + 2] == b"\r\n":
            self.pos += 2
        elif data[self.pos:self.pos + 1] in (b"\n", b"\r"):
            self.pos += 1

        length = None
        length_val = d.get("Length")
        if isinstance(length_val, Raw):
            try:
                length = int(length_val.data)
            except ValueError:
                length = None
        if length is not None and 0 <= length <= len(data) - self.pos:
            payload = data[self.pos:self.pos + length]
            self.pos += length
            self.skip()
            if data[self.pos:self.pos + 9] == b"endstream":
                self.pos += 9
                return Stream(d, payload)
            length = None  # /Length 与实际不符，改用启发式搜索
        end = data.find(b"endstream", self.pos)
        if end < 0:
            raise PDFError("解析 PDF 失败：流对象缺少 endstream 标记")
        payload = data[self.pos:end]
        if payload.endswith(b"\r\n"):
            payload = payload[:-2]
        elif payload.endswith(b"\n") or payload.endswith(b"\r"):
            payload = payload[:-1]
        self.pos = end + 9
        return Stream(d, payload)


def parse_indirect_object(data: bytes, offset: int) -> tuple[int, Any]:
    p = Lexer(data, offset)
    p.skip()
    m = re.match(rb"(\d+)\s+(\d+)\s+obj\b", data[p.pos:])
    if not m:
        raise PDFError(f"解析 PDF 失败：偏移 {offset} 处没有间接对象")
    num = int(m.group(1))
    p.pos += m.end()
    value = p.parse_value()
    p.skip()
    if data[p.pos:p.pos + 6] == b"endobj":
        p.pos += 6
    return num, value


def as_int(value: Any) -> int | None:
    if isinstance(value, Raw):
        try:
            return int(value.data)
        except ValueError:
            return None
    if isinstance(value, int):
        return value
    return None


# ---------------------------------------------------------------------------
# xref 与对象表
# ---------------------------------------------------------------------------


def parse_xref(data: bytes) -> tuple[dict[int, int], list[dict]]:
    idx = data.rfind(b"startxref")
    if idx < 0:
        return {}, []
    m = re.search(rb"\d+", data[idx + 9:])
    if not m:
        return {}, []
    offset = int(m.group())
    offsets: dict[int, int] = {}
    trailers: list[dict] = []
    visited: set[int] = set()
    while offset is not None and offset not in visited and 0 <= offset < len(data):
        visited.add(offset)
        p = Lexer(data, offset)
        p.skip()
        if data[p.pos:p.pos + 4] == b"xref":
            p.pos += 4
            while True:
                p.skip()
                if data[p.pos:p.pos + 7] == b"trailer":
                    break
                m = re.match(rb"(\d+)\s+(\d+)", data[p.pos:])
                if not m:
                    break
                start, count = int(m.group(1)), int(m.group(2))
                p.pos += m.end()
                for i in range(count):
                    entry = data[p.pos:p.pos + 20]
                    if len(entry) < 20:
                        break
                    p.pos += 20
                    em = re.match(rb"(\d{10})\s+(\d{5})\s+([nf])", entry)
                    if em and em.group(3) == b"n":
                        offsets.setdefault(start + i, int(em.group(1)))
            p.skip()
            if data[p.pos:p.pos + 7] != b"trailer":
                break
            p.pos += 7
            trailer = p.parse_value()
            if not isinstance(trailer, dict):
                break
            trailers.append(trailer)
            prev = as_int(trailer.get("Prev"))
            offset = prev
        else:
            # xref 流：不解码流内容，仅取其字典作为 trailer，对象随后全文扫描。
            try:
                _, obj = parse_indirect_object(data, offset)
            except PDFError:
                break
            if isinstance(obj, Stream) and str(obj.dict.get("Type", "")) == "XRef":
                trailers.append(obj.dict)
                offset = as_int(obj.dict.get("Prev"))
            else:
                break
    return offsets, trailers


def scan_objects(data: bytes) -> dict[int, Any]:
    """当 xref 不可用时，全文搜索形如 ``N G obj`` 的对象头并逐个解析。"""
    objects: dict[int, Any] = {}
    for m in re.finditer(rb"(?<![\d])(\d+)\s+(\d+)\s+obj\b", data):
        num = int(m.group(1))
        if num in objects:
            continue
        try:
            parsed_num, value = parse_indirect_object(data, m.start())
        except PDFError:
            continue
        if parsed_num == num:
            objects[num] = value
    return objects


class PDFDoc:
    def __init__(self, data: bytes, version: bytes, objects: dict[int, Any],
                 pages: list[dict], info: Ref | None, encrypted: bool):
        self.data = data
        self.version = version
        self.objects = objects
        self.pages = pages
        self.info = info
        self.encrypted = encrypted


def resolve(ref: Ref, objects: dict[int, Any]) -> Any:
    seen: set[int] = set()
    cur: Any = ref
    while isinstance(cur, Ref):
        if cur.num in seen:
            return None
        seen.add(cur.num)
        cur = objects.get(cur.num)
    return cur


INHERITABLE = ("Resources", "MediaBox", "CropBox", "Rotate")


def collect_pages(objects: dict[int, Any], root: Any) -> list[dict]:
    """递归收集页树叶子节点，并把父节点的可继承属性补到页对象上。"""
    catalog = resolve(root, objects) if isinstance(root, Ref) else root
    pages_ref = catalog.get("Pages") if isinstance(catalog, dict) else None
    if pages_ref is None:
        raise PDFError("解析 PDF 失败：目录对象缺少 /Pages 页树")
    result: list[dict] = []

    def walk(node: Any, inherited: dict, seen: set[int]) -> None:
        if isinstance(node, Ref):
            if node.num in seen:
                return
            seen.add(node.num)
            node = resolve(node, objects)
        if not isinstance(node, dict):
            return
        nodetype = node.get("Type")
        if isinstance(nodetype, Name) and str(nodetype) == "Page":
            page = dict(node)
            page.pop("Parent", None)
            for key in INHERITABLE:
                if key not in page and key in inherited:
                    page[key] = inherited[key]
            result.append(page)
            return
        kids = node.get("Kids")
        if isinstance(kids, list):
            new_inherited = dict(inherited)
            for key in INHERITABLE:
                if key in node:
                    new_inherited[key] = node[key]
            for kid in kids:
                walk(kid, new_inherited, seen)

    walk(pages_ref, {}, set())
    if not result:
        raise PDFError("解析 PDF 失败：页树中未找到任何页面对象")
    return result


def load_pdf(path: Path) -> PDFDoc:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise PDFError(f"无法读取 PDF 文件 {path.name}：{exc}") from exc
    header = data.find(b"%PDF-")
    if header < 0:
        raise PDFError(f"{path.name} 不是合法的 PDF 文件（缺少 %PDF 头）")
    vm = re.match(rb"%PDF-(\d+\.\d+)", data[header:])
    version = vm.group(1) if vm else b"1.4"

    offsets, trailers = parse_xref(data)
    objects: dict[int, Any] = {}
    for num, off in offsets.items():
        try:
            parsed_num, value = parse_indirect_object(data, off)
        except PDFError:
            continue
        if parsed_num == num:
            objects[num] = value
    if not objects:
        objects = scan_objects(data)
    else:
        for num, value in scan_objects(data).items():
            objects.setdefault(num, value)
    if not objects:
        raise PDFError(f"{path.name} 中没有解析出任何 PDF 对象")

    if any("Encrypt" in t for t in trailers):
        raise PDFError(f"{path.name} 是加密 PDF，无法处理。请先解密后再使用本技能。")
    for obj in objects.values():
        if isinstance(obj, Stream) and str(obj.dict.get("Type", "")) == "ObjStm":
            raise PDFError(
                f"{path.name} 使用了对象流（ObjStm）压缩结构，纯标准库无法可靠处理。"
                "请用 PDF 阅读器另存为兼容模式（取消对象流）后重试。"
            )

    root = trailers[0].get("Root") if trailers else None
    if not isinstance(root, Ref):
        for num, obj in objects.items():
            if isinstance(obj, dict) and str(obj.get("Type", "")) == "Catalog":
                root = Ref(num)
                break
    if not isinstance(root, Ref):
        raise PDFError(f"{path.name} 缺少 /Root 目录对象，无法确定页树")

    pages = collect_pages(objects, root)
    info = None
    if trailers:
        candidate = trailers[0].get("Info")
        if isinstance(candidate, Ref) and candidate.num in objects:
            info = candidate
    return PDFDoc(data, version, objects, pages, info, False)


# ---------------------------------------------------------------------------
# 重新编号与序列化
# ---------------------------------------------------------------------------


def escape_name(name: Name) -> bytes:
    out = bytearray()
    for b in str(name).encode("latin-1", "replace"):
        if b < 33 or b > 126 or b in b"#()<>[]{}/%\\":
            out += b"#" + f"{b:02X}".encode("ascii")
        else:
            out.append(b)
    return b"/" + bytes(out)


def serialize(value: Any) -> bytes:
    if isinstance(value, Ref):
        return f"{value.num} {value.gen} R".encode("ascii")
    if isinstance(value, Name):
        return escape_name(value)
    if isinstance(value, Raw):
        return value.data
    if isinstance(value, Stream):
        return serialize_dict(value.dict) + b"\nstream\n" + value.data + b"\nendstream"
    if isinstance(value, dict):
        return serialize_dict(value)
    if isinstance(value, list):
        return b"[ " + b" ".join(serialize(item) for item in value) + b" ]"
    return Raw(str(value).encode("latin-1", "replace")).data


def serialize_dict(d: dict) -> bytes:
    parts = []
    for key, value in d.items():
        parts.append(escape_name(Name(key)) + b" " + serialize(value))
    return b"<< " + b" ".join(parts) + b" >>"


def build_pdf(pages: list[tuple[int, dict]], docs: list[PDFDoc],
              version: bytes) -> bytes:
    """把选中的页（可来自多个文档）组装成一个结构完整的新 PDF。"""
    new_objects: dict[int, Any] = {
        1: {"Type": Name("Catalog"), "Pages": Ref(2)},
        2: {"Type": Name("Pages"), "Kids": [], "Count": 0},
    }
    mapping: dict[tuple[int, int], int] = {}
    processed: set[tuple[int, int]] = set()
    queue: list[tuple[int, int]] = []
    next_num = 3

    def get_new(doc_index: int, old_num: int) -> Ref:
        nonlocal next_num
        key = (doc_index, old_num)
        if key not in mapping:
            mapping[key] = next_num
            next_num += 1
            queue.append(key)
        return Ref(mapping[key])

    def transform(value: Any, doc_index: int) -> Any:
        if isinstance(value, Ref):
            return get_new(doc_index, value.num)
        if isinstance(value, Stream):
            d = {k: transform(v, doc_index) for k, v in value.dict.items()}
            # /Length 必须是直接整数，且与实际流长度一致。
            d["Length"] = Raw(str(len(value.data)).encode("ascii"))
            return Stream(d, value.data)
        if isinstance(value, dict):
            return {k: transform(v, doc_index) for k, v in value.items()}
        if isinstance(value, list):
            return [transform(v, doc_index) for v in value]
        return value

    pages_node = new_objects[2]
    for doc_index, page in pages:
        page_num = next_num
        next_num += 1
        pages_node["Kids"].append(Ref(page_num))
        new_page = transform(page, doc_index)
        new_page["Parent"] = Ref(2)
        new_objects[page_num] = new_page
    pages_node["Count"] = len(pages)

    info_ref = None
    if docs and docs[0].info is not None:
        info_ref = get_new(0, docs[0].info.num)

    while queue:
        key = queue.pop(0)
        if key in processed:
            continue
        processed.add(key)
        doc_index, old_num = key
        source = docs[doc_index].objects.get(old_num)
        new_objects[mapping[key]] = transform(source, doc_index) if source is not None else Raw(b"null")

    out = bytearray()
    out += b"%PDF-" + version + b"\n"
    out += b"%\xe2\xe3\xcf\xd3\n"
    offsets: dict[int, int] = {}
    for num in sorted(new_objects):
        offsets[num] = len(out)
        out += f"{num} 0 obj\n".encode("ascii")
        out += serialize(new_objects[num])
        out += b"\nendobj\n"
    xref_pos = len(out)
    size = max(new_objects) + 1
    out += f"xref\n0 {size}\n".encode("ascii")
    out += b"0000000000 65535 f \n"
    for num in range(1, size):
        if num in offsets:
            out += f"{offsets[num]:010d} 00000 n \n".encode("ascii")
        else:
            out += b"0000000000 65535 f \n"
    trailer = {"Size": Raw(str(size).encode("ascii")), "Root": Ref(1)}
    if info_ref is not None:
        trailer["Info"] = info_ref
    out += b"trailer\n" + serialize_dict(trailer) + b"\n"
    out += b"startxref\n" + str(xref_pos).encode("ascii") + b"\n%%EOF\n"
    return bytes(out)


# ---------------------------------------------------------------------------
# 命令行入口
# ---------------------------------------------------------------------------


def parse_page_spec(spec: str, total: int) -> list[int]:
    if not spec or not spec.strip():
        return list(range(1, total + 1))
    selected: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            left, right = part.split("-", 1)
            try:
                start, end = int(left), int(right)
            except ValueError as exc:
                raise PDFError(f"页码范围格式错误：{part}，应使用如 1-3,5 的形式") from exc
            if start < 1 or end > total or start > end:
                raise PDFError(f"页码范围 {part} 超出有效范围 1-{total}")
            selected.update(range(start, end + 1))
        else:
            try:
                page = int(part)
            except ValueError as exc:
                raise PDFError(f"页码格式错误：{part}") from exc
            if page < 1 or page > total:
                raise PDFError(f"页码 {page} 超出有效范围 1-{total}")
            selected.add(page)
    if not selected:
        raise PDFError("没有选中任何页面，请检查页码范围参数")
    return sorted(selected)


def do_merge(inputs: list[str]) -> list[str]:
    if len(inputs) < 2:
        raise PDFError("合并模式至少需要两个 PDF 文件")
    docs = [load_pdf(Path(p)) for p in inputs]
    pages = [(index, page) for index, doc in enumerate(docs) for page in doc.pages]
    version = max((doc.version for doc in docs), key=lambda v: tuple(int(x) for x in v.split(b".")))
    output = Path("merged.pdf")
    output.write_bytes(build_pdf(pages, docs, version))
    return [str(output.resolve())]


def do_split(inputs: list[str], page_spec: str) -> list[str]:
    if len(inputs) != 1:
        raise PDFError("拆分模式要求且只要求一个 PDF 文件")
    doc = load_pdf(Path(inputs[0]))
    selected = parse_page_spec(page_spec, len(doc.pages))
    out_dir = Path("split_pages")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    created: list[str] = []
    for number in selected:
        target = out_dir / f"page_{number:04d}.pdf"
        target.write_bytes(build_pdf([(0, doc.pages[number - 1])], [doc], doc.version))
        created.append(str(target.resolve()))
    return created


def main() -> int:
    parser = argparse.ArgumentParser(description="官方 PDF 合并与拆分工具")
    parser.add_argument("--mode", choices=["merge", "split"], default="merge", help="处理模式")
    parser.add_argument("--inputs", nargs="+", required=True, help="输入 PDF 路径（可多个）")
    parser.add_argument("--pages", default="", help="拆分页码范围，如 1-3,5；留空表示全部")
    args = parser.parse_args()
    try:
        if args.mode == "merge":
            outputs = do_merge(args.inputs)
        else:
            outputs = do_split(args.inputs, args.pages)
    except PDFError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # 兜底：同样给出中文提示，不让 runner 暴露裸异常
        print(f"错误：处理 PDF 时发生异常：{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    for path in outputs:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

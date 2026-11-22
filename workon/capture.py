# coding: utf-8
"""技能固化助手：扫描一个工作目录，自动推断并生成 manifest.json。

设计目标：AI agent 完成一次工作后，把脚本目录交给 capture，由它生成符合
workon v0.2 契约的 manifest，人不必手写 manifest、也不必懂字段含义。

推断策略是「务实优先」：
- 从 .py/.js/.sh/.ps1 脚本里找 argparse 定义、sys.argv 与输出文件名；
- 生成一份「最小可用」的 manifest（能跑通、能被 validate 接受）；
- 推断不准的地方留给调用方用 --multiple 或交互向导修正。

本模块只生成/写入 manifest.json，不执行技能，也不访问数据库。
"""
from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import Any, Iterable

from .config import DEFAULT_TIMEOUT  # 超时默认值集中一处，避免魔数

MANIFEST_FILENAME = "manifest.json"

# 入口脚本猜测优先级：约定名优先，其次按扩展名
_SCRIPT_PRIORITY = [
    ("run.py", "python"),
    ("main.py", "python"),
    ("app.py", "python"),
    ("cli.py", "python"),
]
_EXT_COMMAND = [
    (".py", "python"),
    (".js", "node"),
    (".ts", "node"),
    (".sh", "bash"),
    (".ps1", "powershell"),
]
_SCRIPT_EXTS = {".py", ".js", ".jsx", ".ts", ".sh", ".bash", ".ps1"}

# 输出文件扩展名 → manifest 类型
_EXT_TYPE = {
    "xlsx": "xlsx", "xls": "xlsx", "xlsm": "xlsx",
    "docx": "docx", "doc": "docx",
    "json": "json",
    "png": "image", "jpg": "image", "jpeg": "image", "gif": "image", "bmp": "image",
    "txt": "file", "csv": "file", "md": "file", "log": "file", "pdf": "file",
    "zip": "file",
}

# 输入名关键词 → 类型（顺序即优先级）
_TYPE_KEYWORDS = [
    (("xlsx", "excel", "spreadsheet", "表格"), "xlsx"),
    (("docx", "word", "文档"), "docx"),
    (("image", "img", "photo", "picture", "png", "jpg", "jpeg", "图片"), "image"),
    (("dir", "folder", "directory", "目录"), "dir"),
    (("json",), "json"),
    (("file", "path", "src", "source", "upload", "attachment", "文件"), "file"),
]

# 输出文件名关键词（用于从源码里挑出「结果文件」）
_OUTPUT_KEYWORDS = (
    "out", "result", "report", "output", "export", "summary", "生成", "结果", "报表", "输出",
)


# --------------------------------------------------------------------------- #
# 公开 API
# --------------------------------------------------------------------------- #
def scan_directory(
    directory: str | Path,
    skill_id: str | None = None,
    name: str | None = None,
    tags: Iterable[str] | None = None,
    entry: str | dict | None = None,
    description: str = "",
    timeout_seconds: int = DEFAULT_TIMEOUT,
    multiple: Iterable[str] | None = None,
    write: bool = False,
    *,
    id: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """扫描目录并推断生成 manifest dict。

    本函数刻意兼容三种调用方：CLI 用 skill_id=/write=，Web 用位置参数 +
    overwrite=，测试/SDK 用 id= 且 entry 可直接传 dict。
    """
    directory = Path(directory).expanduser().resolve()
    if not directory.is_dir():
        raise ValueError(f"目录不存在或不是文件夹: {directory}")
    skill_id = skill_id or id
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", skill_id or ""):
        raise ValueError("技能 id 只能包含字母、数字、下划线和连字符（1-64 位）")
    write = write or overwrite

    explicit_entry = None
    if isinstance(entry, dict):
        command = str(entry.get("command") or "").strip()
        base_args = [str(a) for a in (entry.get("args") or [])]
        if not command:
            raise ValueError("entry.command 不能为空")
        explicit_entry = {"command": command, "args": base_args}
    else:
        entry = (entry or "").strip() or infer_entry(directory)
        if not entry:
            raise ValueError('未能推断入口命令，请用 --entry 指定，例如 --entry "python run.py"')
        command, base_args = _parse_entry(entry)
        if not command:
            raise ValueError("entry 不能为空")

    sources = _read_script_sources(directory)
    source_text = "\n".join(sources.values())

    input_specs, param_specs = _infer_argparse(source_text)
    if not input_specs and _uses_sys_argv(source_text):
        # 没有 argparse 但用了 sys.argv：保守地推断一个位置输入
        input_specs = [
            {
                "name": "input",
                "flag": "",
                "type": "text",
                "required": False,
                "multiple": False,
                "description": "命令行位置输入",
                "ext": [],
            }
        ]
    outputs = _infer_outputs(source_text)

    multiple_set = {m.strip() for m in (multiple or []) if m and m.strip()}
    manifest_inputs: list[dict[str, Any]] = []
    for spec in input_specs:
        field = _input_field(spec)
        if spec["name"] in multiple_set or spec.get("multiple"):
            field["multiple"] = True
        manifest_inputs.append(field)

    manifest_outputs: list[dict[str, Any]] = []
    for spec in outputs:
        field = _output_field(spec)
        if spec["name"] in multiple_set or spec.get("multiple"):
            field["multiple"] = True
        manifest_outputs.append(field)

    manifest_params = [_param_field(spec) for spec in param_specs]

    # entry 直接传 dict 时 args 已由调用方给定，不再追加推断占位符
    args = base_args if explicit_entry is not None else _build_entry_args(base_args, input_specs, param_specs)

    timeout = timeout_seconds if isinstance(timeout_seconds, int) and timeout_seconds > 0 else DEFAULT_TIMEOUT
    manifest: dict[str, Any] = {
        "id": skill_id,
        "name": (name or "").strip() or skill_id,
        "description": description or "",
        "version": "0.1.0",
        "author": "workon-capture",
        "tags": [str(t).strip() for t in (tags or []) if str(t).strip()],
        "inputs": manifest_inputs,
        "outputs": manifest_outputs,
        "params": manifest_params,
        "entry": {"command": command, "args": args},
        "timeout_seconds": timeout,
        "dependencies": [],
    }
    if write:
        write_manifest(directory, manifest)
    return manifest


def write_manifest(directory: str | Path, manifest: dict[str, Any]) -> Path:
    """把 manifest dict 写入目录，返回写入路径。"""
    directory = Path(directory).expanduser().resolve()
    if not directory.is_dir():
        raise ValueError(f"目录不存在: {directory}")
    path = directory / MANIFEST_FILENAME
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def infer_entry(directory: str | Path) -> str:
    """根据目录内脚本猜测入口命令字符串。"""
    directory = Path(directory)
    if not directory.is_dir():
        return ""
    files = {p.name for p in directory.iterdir() if p.is_file()}
    for filename, command in _SCRIPT_PRIORITY:
        if filename in files:
            return f"{command} {filename}"
    for ext, command in _EXT_COMMAND:
        matches = sorted(directory.glob(f"*{ext}"))
        if matches:
            return f"{command} {matches[0].name}"
    return ""


def interactive_init(directory: str | Path) -> dict[str, Any] | None:
    """交互式向导：询问核心字段，扫描推断，展示并确认后写入 manifest.json。

    用户取消返回 None；写入成功返回 manifest dict。
    """
    directory = Path(directory).expanduser().resolve()
    if not directory.is_dir():
        raise ValueError(f"目录不存在: {directory}")

    manifest_path = directory / MANIFEST_FILENAME
    if manifest_path.exists():
        answer = _prompt("已存在 manifest.json，是否覆盖", "n")
        if answer.lower() not in {"y", "yes"}:
            return None

    default_id = re.sub(r"[^A-Za-z0-9_-]", "-", directory.name).strip("-")[:64] or "skill"
    skill_id = _prompt("技能 id（英文/数字/下划线/连字符）", default_id)
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", skill_id):
        raise ValueError("技能 id 只能包含字母、数字、下划线和连字符（1-64 位）")
    name = _prompt("显示名称", directory.name)
    description = _prompt("描述（一句话说明这件工作）", "")
    tags_raw = _prompt("标签（逗号分隔，方便以后搜索）", "")
    tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    entry = _prompt("执行命令（如 python run.py）", infer_entry(directory) or "python run.py")
    timeout_raw = _prompt("超时秒数", str(DEFAULT_TIMEOUT))
    try:
        timeout = int(timeout_raw)
    except (TypeError, ValueError):
        timeout = DEFAULT_TIMEOUT

    manifest = scan_directory(
        directory,
        skill_id=skill_id,
        name=name,
        tags=tags,
        entry=entry,
        description=description,
        timeout_seconds=timeout,
    )

    print("\n已根据脚本推断出下面的技能契约，请过目：")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    answer = _prompt("确认写入 manifest.json", "y")
    if answer.lower() in {"", "y", "yes"}:
        write_manifest(directory, manifest)
        print(f"已写入 {manifest_path}")
        return manifest
    print("已取消，未写入文件。")
    return None


# --------------------------------------------------------------------------- #
# 内部：脚本扫描与推断
# --------------------------------------------------------------------------- #
def _read_script_sources(directory: Path) -> dict[str, str]:
    """读取目录内脚本文本（每个文件最多 200KB），供启发式推断使用。"""
    result: dict[str, str] = {}
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.suffix.lower() not in _SCRIPT_EXTS:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        result[path.name] = text[:200_000]
    return result


def _extract_calls(source: str, func_name: str) -> list[str]:
    """提取 source 中每个 func_name(...) 调用的括号内部文本（配对括号）。"""
    results: list[str] = []
    idx = 0
    needle = func_name + "("
    while True:
        start = source.find(needle, idx)
        if start < 0:
            break
        i = start + len(needle)
        depth = 1
        quote: str | None = None
        escaped = False
        while i < len(source) and depth > 0:
            ch = source[i]
            if quote:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == quote:
                    quote = None
            else:
                if ch in ("'", '"'):
                    quote = ch
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
            i += 1
        results.append(source[start + len(needle): i - 1])
        idx = i
    return results


def _string_literals(text: str) -> list[str]:
    return [m.group(2) for m in re.finditer(r"(['\"])(.*?)\1", text)]


def _first_group(text: str, pattern: str) -> str:
    match = re.search(pattern, text)
    return match.group(1) if match else ""


def _parse_default(text: str) -> Any:
    raw = _first_group(text, r"default\s*=\s*([^,)]+)").strip()
    if not raw:
        return False  # store_true/false 的默认通常为 False
    raw = raw.strip("\"'")
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    try:
        return int(raw)
    except ValueError:
        return raw


def _uses_sys_argv(source: str) -> bool:
    return "sys.argv" in source


def _infer_type(name: str, option_text: str = "") -> str:
    lowered = (name + " " + option_text).lower()
    for keywords, ftype in _TYPE_KEYWORDS:
        if any(kw in lowered for kw in keywords):
            return ftype
    return "text"


def _infer_ext(ftype: str) -> list[str]:
    return {
        "xlsx": ["xlsx", "xls"],
        "docx": ["docx"],
        "json": ["json"],
        "image": ["png", "jpg", "jpeg", "gif", "bmp"],
    }.get(ftype, [])


def _infer_argparse(source: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """从 argparse 源码推断输入字段与布尔参数。"""
    inputs: list[dict[str, Any]] = []
    params: list[dict[str, Any]] = []
    seen: set[str] = set()

    for inner in _extract_calls(source, "add_argument"):
        literals = _string_literals(inner)
        long_flags = [item for item in literals if item.startswith("--")]
        flag = long_flags[-1] if long_flags else next((item for item in literals if item.startswith("-")), "")
        if not flag or flag in seen:
            continue
        seen.add(flag)

        name = re.sub(r"[^A-Za-z0-9_]", "_", flag.lstrip("-")).strip("_") or "arg"
        action = _first_group(inner, r"action\s*=\s*['\"]([^'\"]+)['\"]")
        required = bool(re.search(r"required\s*=\s*True", inner))
        multiple = bool(
            re.search(r"nargs\s*=\s*['\"]\+['\"]|action\s*=\s*['\"]append['\"]", inner)
        )

        # store_true / store_false / count 作为「开关参数」处理
        if action in {"store_true", "store_false", "count"}:
            params.append(
                {
                    "name": name,
                    "type": "boolean",
                    "flag": flag,
                    "default": _parse_default(inner),
                    "description": _first_group(inner, r"help\s*=\s*['\"]([^'\"]+)['\"]"),
                    "choices": [],
                }
            )
            continue

        ftype = _infer_type(name, inner)
        help_text = _first_group(inner, r"help\s*=\s*['\"]([^'\"]+)['\"]")
        inputs.append(
            {
                "name": name,
                "type": ftype,
                "flag": flag,
                "required": required,
                "multiple": multiple,
                "description": help_text,
                "ext": _infer_ext(ftype),
            }
        )
    return inputs, params


def _infer_outputs(source: str) -> list[dict[str, Any]]:
    """从源码里找带结果类关键词的输出文件名；始终补一条 stdout 文本输出。"""
    outputs: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for literal in _string_literals(source):
        match = re.search(r"\.([A-Za-z0-9]+)$", literal)
        if not match:
            continue
        ftype = _EXT_TYPE.get(match.group(1).lower())
        if not ftype:
            continue
        stem = Path(literal).stem.lower()
        if not any(kw in stem for kw in _OUTPUT_KEYWORDS):
            continue
        if literal in seen_paths:
            continue
        seen_paths.add(literal)
        outputs.append(
            {
                "name": re.sub(r"[^A-Za-z0-9_]", "_", Path(literal).stem) or ftype,
                "type": ftype,
                "path": literal,
                "required": False,
                "multiple": False,
                "description": "脚本生成的结果文件",
            }
        )
    if not any(item["type"] == "text" for item in outputs):
        outputs.append(
            {
                "name": "result",
                "type": "text",
                "source": "stdout",
                "required": False,
                "multiple": False,
                "description": "标准输出文本",
            }
        )
    return outputs


# --------------------------------------------------------------------------- #
# 内部：manifest 字段与命令拼装
# --------------------------------------------------------------------------- #
def _input_field(spec: dict[str, Any]) -> dict[str, Any]:
    field: dict[str, Any] = {
        "name": spec["name"],
        "type": spec["type"],
        "required": bool(spec.get("required", False)),
        "description": spec.get("description", ""),
        "multiple": bool(spec.get("multiple", False)),
    }
    ext = spec.get("ext") or []
    if ext:
        field["ext"] = ext
    return field


def _output_field(spec: dict[str, Any]) -> dict[str, Any]:
    field: dict[str, Any] = {
        "name": spec["name"],
        "type": spec["type"],
        "required": bool(spec.get("required", False)),
        "description": spec.get("description", ""),
        "multiple": bool(spec.get("multiple", False)),
    }
    if spec.get("path"):
        field["path"] = spec["path"]
    if spec.get("json_key"):
        field["json_key"] = spec["json_key"]
    if spec.get("source"):
        field["source"] = spec["source"]
    return field


def _param_field(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": spec["name"],
        "type": spec.get("type", "string"),
        "default": spec.get("default", ""),
        "flag": spec.get("flag", ""),
        "description": spec.get("description", ""),
        "choices": spec.get("choices", []),
    }


def _parse_entry(entry: str) -> tuple[str, list[str]]:
    parts = [p.strip('"').strip("'") for p in shlex.split(entry.strip(), posix=False)]
    if not parts:
        return "", []
    return parts[0], parts[1:]


def _build_entry_args(
    base_args: list[str],
    input_specs: list[dict[str, Any]],
    param_specs: list[dict[str, Any]],
) -> list[str]:
    """在 --entry 给出基础参数之上，补齐输入占位符与布尔开关。"""
    args = list(base_args)
    present = set(args)
    for spec in input_specs:
        token = "{" + spec["name"] + "}"
        if token in present:
            continue
        flag = spec.get("flag", "")
        if flag and flag not in present:
            args.extend([flag, token])
            present.add(flag)
        else:
            # 位置参数（无 flag）直接放占位符，位置由脚本决定
            args.append(token)
        present.add(token)
    for spec in param_specs:
        flag = spec.get("flag", "")
        if flag and flag not in present:
            args.append(flag)
            present.add(flag)
    return args


def _prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    try:
        value = input(f"{label}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return default
    return value or default

# coding: utf-8
"""技能清单（manifest）的数据结构与校验。"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import DEFAULT_TIMEOUT

INPUT_TYPES = {"text", "file", "docx", "xlsx", "json", "image", "dir"}
OUTPUT_TYPES = {"text", "file", "docx", "xlsx", "json", "dir"}
PARAM_TYPES = {"string", "number", "boolean"}

# 会落盘为文件的输入类型；dir 复制为目录；text/json 为数据型。
FILE_INPUT_TYPES = {"file", "docx", "xlsx", "image"}
DIR_TYPES = {"dir"}
TEXTUAL_TYPES = {"text", "json"}


class ManifestError(ValueError):
    pass


def _as_bool(value: Any, default: bool = False) -> bool:
    """把 manifest 中的布尔值安全转换：支持真正的 bool 与字符串 true/false。

    绝不使用 bool(str)——那会把字符串 "false" 判为 True。
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_timeout(value: Any) -> int:
    try:
        timeout = int(value)
        if timeout <= 0:
            raise ValueError
        return timeout
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT


@dataclass
class Skill:
    id: str
    name: str
    description: str
    version: str
    tags: list[str]
    inputs: list[dict[str, Any]]
    outputs: list[dict[str, Any]]
    entry: dict[str, Any]
    params: list[dict[str, Any]]
    timeout_seconds: int
    dependencies: list[str]
    author: str
    path: Path
    source: str
    official: bool = False
    raw: dict[str, Any] = field(default_factory=dict)

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tags": self.tags,
            "author": self.author,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "params": self.params,
            "entry": self.entry,
            "timeout_seconds": self.timeout_seconds,
            "dependencies": self.dependencies,
            "source": self.source,
            "path": str(self.path),
            "official": self.official,
        }


def validate_manifest(raw: dict[str, Any], path: Path, source: str) -> Skill:
    if not isinstance(raw, dict):
        raise ManifestError("manifest.json 根节点必须是对象")

    skill_id = str(raw.get("id", "")).strip()
    if not re_match_id(skill_id):
        raise ManifestError("id 只能包含字母、数字、下划线和连字符")

    entry = raw.get("entry")
    if not isinstance(entry, dict) or not entry.get("command") or not isinstance(entry.get("args", []), list):
        raise ManifestError("entry 必须包含 command 与 args 数组")

    inputs = _validate_fields(raw.get("inputs", []), INPUT_TYPES, "inputs")
    outputs = _validate_fields(raw.get("outputs", []), OUTPUT_TYPES, "outputs")
    params = _validate_params(raw.get("params", []))

    _check_placeholders(entry, inputs, params)

    return Skill(
        id=skill_id,
        name=str(raw.get("name") or skill_id),
        description=str(raw.get("description") or ""),
        version=str(raw.get("version") or "0.1.0"),
        tags=[str(t) for t in raw.get("tags", [])],
        inputs=inputs,
        outputs=outputs,
        entry=entry,
        params=params,
        timeout_seconds=_parse_timeout(raw.get("timeout_seconds", 120)),
        dependencies=[str(d) for d in raw.get("dependencies", [])],
        author=str(raw.get("author") or ""),
        path=path,
        source=source,
        official=_as_bool(raw.get("official", False)),
        raw=raw,
    )


def re_match_id(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value))


# 占位符规则必须与执行器 runner.PLACEHOLDER 完全一致，否则会出现
# 「validate 放行、运行时不展开」的错位（core-audit）。字段名只允许
# 字母/数字/下划线，和 manifest id 的连字符规则刻意区分。
PLACEHOLDER_PATTERN = r"\{([A-Za-z0-9_]+)\}"
_PLACEHOLDER_RE = re.compile(PLACEHOLDER_PATTERN)
# 执行器注入的内置占位符：用户不得在 inputs/params 中声明同名，
# 避免技能脚本拿到被覆盖的非预期值。
_RESERVED_PLACEHOLDERS = {"workdir", "skill_dir", "run_id"}


def _check_placeholders(
    entry: dict[str, Any],
    inputs: list[dict[str, Any]],
    params: list[dict[str, Any]],
) -> None:
    """校验 entry 里的占位符都有来源。

    占位符拼错（或漏声明 inputs/params）以前只在真正执行时才报
    「manifest 引用了未提供的占位符」，那时用户已经点下召唤按钮了。
    这里在加载阶段就拦住，``skill validate`` 也能提前暴露。
    """
    names = {field["name"] for field in inputs} | {field["name"] for field in params}
    # 用户声明的字段不能占用执行器内置占位符名，否则运行时会被注入值覆盖。
    clash = sorted(names & _RESERVED_PLACEHOLDERS)
    if clash:
        raise ManifestError(
            "inputs/params 不得使用内置占位符名: " + ", ".join(sorted("{%s}" % n for n in clash))
        )
    declared = names | _RESERVED_PLACEHOLDERS
    fragments = [str(entry.get("command", ""))]
    fragments.extend(str(arg) for arg in entry.get("args", []) if isinstance(arg, str))

    unknown: list[str] = []
    for fragment in fragments:
        for name in _PLACEHOLDER_RE.findall(fragment):
            if name not in declared and name not in unknown:
                unknown.append(name)
    if unknown:
        known = ", ".join(sorted(declared - _RESERVED_PLACEHOLDERS)) or "（未声明任何输入）"
        raise ManifestError(
            "entry 引用了未声明的占位符: "
            + ", ".join("{%s}" % n for n in unknown)
            + f"；已声明的输入/参数: {known}"
        )


def _validate_fields(items: Any, allowed: set[str], label: str) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        raise ManifestError(f"{label} 必须是数组")
    result = []
    for item in items:
        if not isinstance(item, dict) or not item.get("name"):
            raise ManifestError(f"{label} 的每一项都需要 name")
        ftype = str(item.get("type", "text"))
        if ftype not in allowed:
            raise ManifestError(f"{label}.{item['name']} 的类型 {ftype} 不受支持")
        result.append(
            {
                "name": str(item["name"]),
                "label": str(item.get("label") or ""),
                "type": ftype,
                "required": _as_bool(item.get("required", True), True),
                "description": str(item.get("description") or ""),
                "ext": [str(e).lower().lstrip(".") for e in item.get("ext", [])],
                "source": str(item.get("source") or "stdout"),
                "path": str(item.get("path") or ""),
                "json_key": str(item.get("json_key") or ""),
                "multiple": _as_bool(item.get("multiple", False)),
            }
        )
    return result


def _validate_params(items: Any) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        raise ManifestError("params 必须是数组")
    result = []
    for item in items:
        if not isinstance(item, dict) or not item.get("name"):
            raise ManifestError("params 的每一项都需要 name")
        ptype = str(item.get("type", "string"))
        if ptype not in PARAM_TYPES:
            raise ManifestError(f"params.{item['name']} 的类型 {ptype} 不受支持")
        result.append(
            {
                "name": str(item["name"]),
                "label": str(item.get("label") or ""),
                "type": ptype,
                "default": item.get("default", False if ptype == "boolean" else ""),
                "flag": str(item.get("flag") or ""),
                "description": str(item.get("description") or ""),
                "choices": [str(c) for c in item.get("choices", [])],
                "choices_labels": {
                    str(k): str(v) for k, v in (item.get("choices_labels") or {}).items()
                },
            }
        )
    return result

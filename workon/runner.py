# coding: utf-8
"""技能召唤执行器：校验输入 → 落盘 → 运行脚本 → 收集输出 → 记录历史。"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

from .config import settings
from .models import DIR_TYPES, FILE_INPUT_TYPES, PLACEHOLDER_PATTERN, Skill
from .storage import record_run

# 与 models 校验共用同一规则，避免「validate 放行、运行时不展开」的错位。
PLACEHOLDER = re.compile(PLACEHOLDER_PATTERN)

# 执行相关的固定上限，集中命名，避免魔数散落。
RUN_ID_LENGTH = 12          # run_id 截短长度（展示与文件名友好）
MAX_TIMEOUT_SECONDS = 3600  # 单次执行超时硬上限（1 小时）
MAX_ERROR_CHARS = 2000      # 错误信息保留尾部字符数
MAX_STREAM_CHARS = 20000    # stdout/stderr 各保留尾部字符数


class InvocationError(ValueError):
    """输入校验或执行前置错误。"""


def invoke(skill: Skill, inputs: dict[str, Any], params: dict[str, Any] | None = None) -> dict[str, Any]:
    run_id = uuid.uuid4().hex[:RUN_ID_LENGTH]
    started = time.perf_counter()
    inputs = dict(inputs or {})
    params = dict(params or {})
    workdir: Path | None = None
    status = "success"
    error = ""
    outputs: dict[str, Any] = {"text": {}, "json": {}, "files": []}

    try:
        # 1) 校验输入
        normalized = _validate_inputs(skill, inputs)

        # 2) 校验参数并填默认值
        normalized_params = _validate_params(skill, params)

        # 3) 建立临时工作目录，复制技能脚本并落盘输入
        workdir = Path(tempfile.mkdtemp(prefix=f"workon-{skill.id}-", dir=str(settings.run_root)))
        _copy_skill_files(skill.path, workdir)
        staged = _stage_inputs(skill, normalized, workdir)

        # 4) 构造命令
        command = _build_command(skill, staged, normalized_params, workdir, run_id)

        # 5) 执行
        timeout = min(int(skill.timeout_seconds or settings.default_timeout), MAX_TIMEOUT_SECONDS)
        env = os.environ.copy()
        env["WORKON_RUN_ID"] = run_id
        env["WORKON_WORKDIR"] = str(workdir)
        env.setdefault("PYTHONIOENCODING", "utf-8")

        try:
            proc = subprocess.run(
                command,
                cwd=str(workdir),
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
            stdout, stderr, returncode = proc.stdout or "", proc.stderr or "", proc.returncode
        except subprocess.TimeoutExpired as exc:
            status = "timeout"
            error = f"技能执行超时（{timeout} 秒）"
            stdout = (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = (exc.stderr or b"").decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            returncode = -1
        except FileNotFoundError as exc:
            raise InvocationError(f"找不到执行命令: {exc}") from exc

        # 6) 收集输出；把文件输出复制到持久目录（工作目录随后会被删除）
        outputs = _collect_outputs(skill, workdir, stdout, staged)
        outputs["files"] = _persist_output_files(outputs["files"], run_id)

        if status == "success" and returncode != 0:
            status = "failed"
            error = (stderr or stdout or f"脚本退出码 {returncode}").strip()[-MAX_ERROR_CHARS:]

        outputs["stdout"] = stdout[-MAX_STREAM_CHARS:]
        if stderr:
            outputs["stderr"] = stderr[-MAX_STREAM_CHARS:]
        outputs["returncode"] = returncode

    except InvocationError as exc:
        status = "failed"
        error = str(exc)
    except Exception as exc:  # pragma: no cover - 兜底
        status = "failed"
        error = f"执行器异常: {type(exc).__name__}: {exc}"
    finally:
        duration_ms = int((time.perf_counter() - started) * 1000)
        record_run(
            run_id=run_id,
            skill_id=skill.id,
            skill_name=skill.name,
            status=status,
            duration_ms=duration_ms,
            inputs={k: _safe_input_value(v) for k, v in inputs.items()},
            params=params,
            outputs=outputs,
            error=error,
        )
        if workdir and workdir.exists():
            shutil.rmtree(workdir, ignore_errors=True)

    return {
        "run_id": run_id,
        "skill_id": skill.id,
        "status": status,
        "error": error,
        "duration_ms": duration_ms,
        "outputs": outputs,
    }


def _safe_input_value(value: Any) -> Any:
    if isinstance(value, dict):
        if value.get("_staged_path") or value.get("filename"):
            return {
                "name": value.get("filename") or value.get("name"),
                "type": value.get("type"),
                "size": value.get("size"),
            }
        return {k: _safe_input_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe_input_value(v) for v in value]
    if isinstance(value, (bytes, bytearray)):
        return f"<bytes:{len(value)}>"
    return value if isinstance(value, (str, int, float, bool, type(None))) else str(value)


def _validate_inputs(skill: Skill, inputs: dict[str, Any]) -> dict[str, Any]:
    """校验输入并归一化为统一中间结构。

    single 字段的 items 长度为 1，staged 形状与 v0.1 完全一致；
    multiple 字段的 items 为列表，逐项走同一套校验逻辑。
    """
    normalized: dict[str, Any] = {}
    for field in skill.inputs:
        name = field["name"]
        ftype = field["type"]
        multiple = field.get("multiple", False)
        value = inputs.get(name)

        empty = value in (None, "")
        if multiple and isinstance(value, list):
            empty = not value
        if empty:
            if field["required"]:
                raise InvocationError(f"缺少必填输入: {name}")
            continue

        # 单值字段若收到 list，拒绝而非静默取第一个，避免吞数据
        if isinstance(value, list) and not multiple:
            raise InvocationError(f"输入 {name} 声明了单值（multiple=false），但收到数组")

        raw_items = value if isinstance(value, list) else [value]
        items: list[dict[str, Any]] = []

        if ftype == "text":
            for entry in raw_items:
                items.append({"type": "text", "value": str(entry)})
            normalized[name] = {"type": ftype, "multiple": multiple, "items": items}
            continue

        if ftype == "json" and not multiple and not _is_file_object(value):
            # json 输入一律当数据；对象数组且 multiple 时才可能是文件对象
            normalized[name] = {
                "type": ftype,
                "multiple": False,
                "items": [{"type": "json", "data": value}],
            }
            continue

        for entry in raw_items:
            if ftype == "json" and not _is_file_object(entry):
                items.append({"type": "json", "data": entry})
                continue
            if ftype in DIR_TYPES:
                source = entry if isinstance(entry, str) else (entry.get("path") if isinstance(entry, dict) else None)
                if not source:
                    raise InvocationError(f"输入 {name} 的 dir 缺少 path")
                src_path = Path(source)
                if not src_path.is_dir():
                    raise InvocationError(f"输入目录不存在: {src_path}")
                items.append({"type": ftype, "path": str(src_path), "filename": src_path.name})
                continue
            # file / docx / xlsx / image / json 文件对象
            # 也接受纯路径字符串（便于 CLI 以路径列表传入多个文件）
            if isinstance(entry, str):
                entry = {"path": entry, "filename": Path(entry).name or "upload"}
            if not isinstance(entry, dict):
                raise InvocationError(f"输入 {name} 需要是包含 filename/content 或 path 的对象")
            filename = str(entry.get("filename") or "upload")
            content = entry.get("content")
            source_path = entry.get("path")
            ext = Path(filename).suffix.lower().lstrip(".")
            allowed = field["ext"]
            if ftype in {"docx", "xlsx"}:
                expected = ftype
                if ext and ext != expected:
                    raise InvocationError(f"输入 {name} 需要 .{expected} 文件，实际为 .{ext}")
            if allowed and ext and ext not in allowed:
                raise InvocationError(f"输入 {name} 的扩展名 .{ext} 不受支持")
            if content is None and not source_path:
                raise InvocationError(f"输入 {name} 缺少文件内容")
            items.append(
                {
                    "type": ftype,
                    "filename": filename,
                    "content": content,
                    "path": source_path,
                    "size": len(content) if isinstance(content, (bytes, bytearray)) else 0,
                }
            )
        normalized[name] = {"type": ftype, "multiple": multiple, "items": items}
    return normalized


def _is_file_object(value: Any) -> bool:
    """判断是否为 file-like 输入对象（含 path 或 content/filename）。"""
    return isinstance(value, dict) and bool(value.get("path") or value.get("content") is not None)


def _validate_params(skill: Skill, params: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    declarations = {p["name"]: p for p in skill.params}
    for name, decl in declarations.items():
        has_value = name in params
        value = params.get(name, decl["default"])
        if decl["type"] == "boolean":
            value = value if isinstance(value, bool) else str(value).lower() in {"1", "true", "yes", "on"}
        elif decl["type"] == "number":
            if value is None or value == "":
                if not has_value:
                    continue  # 未传值且无有效默认值：不注入该参数
                raise InvocationError(f"参数 {name} 需要是数字")
            try:
                value = float(value)
            except (TypeError, ValueError) as exc:
                raise InvocationError(f"参数 {name} 需要是数字") from exc
        else:
            value = str(value)
            if decl["choices"] and value not in decl["choices"]:
                raise InvocationError(f"参数 {name} 必须是以下值之一: {', '.join(decl['choices'])}")
        result[name] = value
    for name in params:
        if name not in declarations:
            result[name] = params[name]
    return result


def _copy_skill_files(skill_dir: Path, workdir: Path) -> None:
    """把技能目录中的脚本/依赖文件复制到临时工作目录（跳过 manifest 与说明）。

    递归复制子目录：技能常把依赖拆成 ``lib/``、``templates/`` 等子目录，
    只复制顶层文件会让 ``from lib.helper import ...`` 在运行时炸掉。
    跳过 ``__pycache__``、``.git``、``data`` 等噪音目录，以及每个目录层级的
    manifest.json / README.md / settings.json。
    """
    if not skill_dir.is_dir():
        raise InvocationError(f"技能目录不存在: {skill_dir}")
    skip_names = {"manifest.json", "README.md", "settings.json"}
    skip_dirs = {"__pycache__", ".git", ".venv", "venv", "node_modules", "data"}
    for item in skill_dir.iterdir():
        if item.name in skip_names:
            continue
        if item.is_dir():
            if item.name in skip_dirs:
                continue
            shutil.copytree(
                item,
                workdir / item.name,
                ignore=shutil.ignore_patterns(*skip_dirs, *skip_names),
                dirs_exist_ok=True,
            )
            continue
        shutil.copy2(item, workdir / item.name)


def _safe_filename(name: str) -> str:
    """保留字面量中文范围的安全文件名转换（与 v0.1 完全一致）。"""
    return re.sub(r"[^A-Za-z0-9._\-一-鿿]", "_", Path(name).name) or "upload"


def _unique_target(workdir: Path, base: str, used: set[str]) -> Path:
    """为工作目录内的目标路径生成不重名版本：name, name_1, name_2 ..."""
    candidate = workdir / base
    stem, suffix = Path(base).stem, Path(base).suffix
    index = 1
    while str(candidate).lower() in used or candidate.exists():
        candidate = workdir / f"{stem}_{index}{suffix}"
        index += 1
    used.add(str(candidate).lower())
    return candidate


def _stage_inputs(skill: Skill, normalized: dict[str, Any], workdir: Path) -> dict[str, Any]:
    staged: dict[str, Any] = {}
    used: set[str] = set()
    for name, item in normalized.items():
        ftype = item["type"]
        multiple = item.get("multiple", False)
        entries = item["items"]

        # 文本数据型（single 与 multiple 同构，single 保持原形状）
        if ftype == "text":
            if not multiple and len(entries) == 1:
                staged[name] = {"type": "text", "value": entries[0]["value"]}
            else:
                value = " ".join(str(e["value"]) for e in entries)
                staged[name] = {"type": "text", "value": value, "multiple": True}
            continue

        paths: list[str] = []
        files_meta: list[dict[str, Any]] = []
        staged_items: list[dict[str, Any]] = []

        for entry in entries:
            # json 数据型：序列化为 <name>.json（multiple 时加序号）
            if ftype == "json" and "data" in entry:
                base = f"{_safe_filename(name)}.json"
                target = _unique_target(workdir, base, used)
                target.write_text(
                    json.dumps(entry["data"], ensure_ascii=False, indent=2), encoding="utf-8"
                )
                paths.append(str(target))
                staged_items.append(
                    {
                        "type": "json",
                        "value": str(target),
                        "filename": target.name,
                        "_staged_path": str(target),
                    }
                )
                continue

            # dir 类型：copytree 到工作目录
            if ftype in DIR_TYPES:
                base = _safe_filename(entry.get("filename") or Path(entry["path"]).name)
                target = _unique_target(workdir, base, used)
                source = Path(entry["path"])
                shutil.copytree(source, target)
                paths.append(str(target))
                files_meta.append(
                    {
                        "filename": target.name,
                        "path": str(target),
                        "type": ftype,
                        "size": sum(p.stat().st_size for p in target.rglob("*") if p.is_file()),
                        "is_dir": True,
                    }
                )
                staged_items.append(
                    {
                        "type": ftype,
                        "value": str(target),
                        "filename": target.name,
                        "_staged_path": str(target),
                    }
                )
                continue

            # 文件型：file / docx / xlsx / image / json 文件对象
            filename = Path(entry["filename"]).name or "upload"
            safe_name = _safe_filename(filename)
            target = _unique_target(workdir, safe_name, used)
            content = entry.get("content")
            if isinstance(content, (bytes, bytearray)):
                target.write_bytes(bytes(content))
            elif isinstance(content, str):
                target.write_text(content, encoding="utf-8")
            elif entry.get("path"):
                source = Path(entry["path"])
                if not source.is_file():
                    raise InvocationError(f"输入文件不存在: {source}")
                target.write_bytes(source.read_bytes())
            else:
                raise InvocationError(f"输入 {name} 没有可用内容")
            paths.append(str(target))
            size = target.stat().st_size
            files_meta.append({"filename": target.name, "path": str(target), "type": ftype, "size": size})
            staged_items.append(
                {
                    "type": ftype,
                    "value": str(target),
                    "filename": target.name,
                    "_staged_path": str(target),
                }
            )

        if not multiple and len(staged_items) == 1:
            # 单值形状必须与 v0.1 完全一致，保证 text-echo 与老 manifest 兼容
            staged[name] = staged_items[0]
        else:
            # multiple：带引号路径列表，_build_command 仅在整条 arg 是占位符时分词
            joined = " ".join(f'"{p}"' for p in paths)
            staged[name] = {
                "type": ftype,
                "multiple": True,
                "value": joined,
                "paths": paths,
                "_staged_paths": paths,
                "_staged_path": paths[0] if paths else "",
                "files": files_meta,
            }
    return staged


def _build_command(
    skill: Skill,
    staged: dict[str, Any],
    params: dict[str, Any],
    workdir: Path,
    run_id: str = "",
) -> list[str]:
    from .config import python_command

    entry = skill.entry
    command = str(entry.get("command") or "").strip()
    if not command:
        raise InvocationError("entry.command 不能为空")

    # 白名单检查基于原始命令的第一个 token，避免 Windows 路径反斜杠干扰
    first = command.split(maxsplit=1)[0]
    base = first.lower()
    allowed = {c.lower() for c in settings.allowed_commands}
    if base in {"python", "python3"}:
        # python/python3 视为合法并替换为当前解释器（保留可能的后续参数）
        command = python_command() + command[len(first):]
    elif base in allowed:
        pass
    else:
        raise InvocationError(f"命令 {first!r} 不在允许列表 {sorted(allowed)} 中")

    values: dict[str, str] = {name: str(item["value"]) for name, item in staged.items()}
    for name, value in params.items():
        if isinstance(value, bool):
            # 布尔参数若声明了 flag，则只通过 flag 传递，不进入占位符
            decl = next((p for p in skill.params if p["name"] == name), None)
            if decl and decl.get("flag"):
                continue
            values[name] = "true" if value else "false"
        elif isinstance(value, float) and value.is_integer():
            values[name] = str(int(value))  # number 占位符避免 5.0 这类浮点串
        else:
            values[name] = str(value)
    values.update(
        {
            "workdir": str(workdir),
            "skill_dir": str(skill.path),
            "run_id": run_id,
        }
    )

    def substitute(text: str) -> str:
        def replace(match: re.Match) -> str:
            key = match.group(1)
            if key not in values:
                raise InvocationError(f"manifest 引用了未提供的占位符: {{{key}}}")
            return values[key]

        return PLACEHOLDER.sub(replace, text)

    # multiple 输入：仅当整条 arg 本身就是一个占位符时，才把带引号路径列表
    # 按空格分词展开成多个参数；如 --files={files} 这类嵌套形式仍保持单个参数。
    multiple_keys = {name for name, item in staged.items() if item.get("multiple")}

    def expand_arg(arg: Any) -> list[str]:
        raw = str(arg)
        match = PLACEHOLDER.fullmatch(raw)
        if match and match.group(1) in multiple_keys:
            expanded = substitute(raw)
            return [part.strip('"').strip("'") for part in shlex.split(expanded, posix=False)]
        return [substitute(raw)]

    args: list[str] = []
    for arg in entry.get("args", []):
        args.extend(expand_arg(arg))

    # 布尔参数可作为独立 flag 追加（manifest 中声明 flag 时）
    for decl in skill.params:
        if decl.get("flag") and decl["type"] == "boolean" and params.get(decl["name"]):
            args.append(decl["flag"])

    # 命令本体分词（posix=False 保留 Windows 路径反斜杠），逐段去引号
    cmd_parts = [p.strip('"').strip("'") for p in shlex.split(command, posix=False)]
    return cmd_parts + args


def _persist_output_files(files: list[dict[str, Any]], run_id: str) -> list[dict[str, Any]]:
    """把输出文件从临时工作目录复制到持久目录，避免工作目录被清理后文件丢失。"""
    if not files:
        return files
    dest_dir = settings.run_root / run_id / "outputs"
    dest_dir.mkdir(parents=True, exist_ok=True)
    persisted: list[dict[str, Any]] = []
    for f in files:
        src = Path(f["path"])
        # v0.2 目录输出：copytree 到持久目录（src.is_file() 为 False 时不跳过）
        if f.get("is_dir") and src.is_dir():
            filename = Path(f.get("filename") or src.name).name
            dest = dest_dir / filename
            if dest.exists():
                stem, suffix = dest.stem, dest.suffix
                index = 1
                while dest.exists():
                    dest = dest_dir / f"{stem}_{index}{suffix}"
                    index += 1
            shutil.copytree(src, dest)
            item = dict(f)
            item["path"] = str(dest)
            item["filename"] = dest.name
            item["persisted"] = True
            persisted.append(item)
            continue
        if not src.is_file():
            continue
        filename = Path(f.get("filename") or src.name).name
        dest = dest_dir / filename
        if dest.exists():
            stem, suffix = dest.stem, dest.suffix
            index = 1
            while dest.exists():
                dest = dest_dir / f"{stem}_{index}{suffix}"
                index += 1
        shutil.copy2(src, dest)
        item = dict(f)
        item["path"] = str(dest)
        item["filename"] = dest.name
        item["persisted"] = True
        persisted.append(item)
    return persisted


def _collect_outputs(skill: Skill, workdir: Path, stdout: str, staged: dict[str, Any]) -> dict[str, Any]:
    # 已落盘的输入文件路径：输出收集时必须排除，避免把输入当成输出返回
    staged_inputs: set[str] = set()
    for entry in staged.values():
        for p in entry.get("_staged_paths", []):
            staged_inputs.add(str(Path(p).resolve()))
        single = entry.get("_staged_path")
        if single:
            staged_inputs.add(str(Path(single).resolve()))

    files: list[dict[str, Any]] = []
    seen_files: set[str] = set()
    json_outputs: dict[str, Any] = {}
    for item in skill.outputs:
        otype = item["type"]
        multiple = item.get("multiple", False)
        if otype == "text":
            continue

        raw_path = item.get("path") or ""
        candidates: list[Path] = []
        if raw_path:
            candidate = Path(raw_path.replace("{workdir}", str(workdir)))
            if not candidate.is_absolute():
                candidate = workdir / candidate
            candidates.append(candidate)
        pattern = raw_path or "output.*"
        candidates.extend(sorted(workdir.glob(pattern)))
        for candidate in candidates:
            if str(candidate.resolve()) in staged_inputs:
                continue
            if otype in DIR_TYPES:
                if not candidate.is_dir() or str(candidate) in seen_files:
                    continue
                seen_files.add(str(candidate))
                files.append(
                    {
                        "name": item["name"],
                        "filename": candidate.name,
                        "path": str(candidate),
                        "size": sum(p.stat().st_size for p in candidate.rglob("*") if p.is_file()),
                        "type": otype,
                        "is_dir": True,
                    }
                )
                if not multiple:
                    break
                continue
            if not candidate.is_file() or str(candidate) in seen_files:
                continue
            seen_files.add(str(candidate))
            meta = {
                "name": item["name"],
                "filename": candidate.name,
                "path": str(candidate),
                "size": candidate.stat().st_size,
                "type": otype,
            }
            if otype == "json":
                try:
                    json_outputs.setdefault(item["name"], []).append(
                        json.loads(candidate.read_text(encoding="utf-8"))
                    )
                except Exception:
                    json_outputs.setdefault(item["name"], []).append(None)
            files.append(meta)
            if not multiple:
                break

    # 单值 json 输出解包为单个对象，保持向后兼容
    for name, values in list(json_outputs.items()):
        decl = next((o for o in skill.outputs if o["name"] == name), None)
        if decl and not decl.get("multiple") and len(values) == 1:
            json_outputs[name] = values[0]

    # 文本输出：声明 json_key 时从 stdout 的 JSON 提取，否则直接取 stdout
    texts: dict[str, Any] = {}
    for item in skill.outputs:
        if item["type"] != "text":
            continue
        json_key = item.get("json_key")
        if not json_key:
            texts[item["name"]] = stdout.strip()
            continue
        try:
            payload = json.loads(stdout)
            value = payload
            for key in json_key.split("."):
                value = value[key]
            texts[item["name"]] = value
        except Exception:
            texts[item["name"]] = None

    return {"text": texts, "json": json_outputs, "files": files}

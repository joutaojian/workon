# coding: utf-8
"""把 workon-capture 技能安装进其他 AI Agent 的 skills 目录。

workon 有两种使用姿势：

1. **召唤技能**（本项目自己的技能库）：文员打开 Web/CLI 点一下，确定性复现。
2. **固化技能**（本项目分发出去的 Agent Skill）：在 Claude Code / Codex / WorkBuddy /
   Qoder 里说一句「把这个工作固化到 workon」，那个 Agent 读到 workon-capture 这个
   Agent Skill，就知道该怎么生成 manifest.json 并登记。

本模块只负责第 2 件事的安装：把内置的 ``workon/skills/workon-capture/`` 复制到各
Agent 的用户级 skills 目录，并把「workon 怎么启动」固化成同目录下的启动器脚本
（``workon.cmd`` / ``workon.sh``），让外部 Agent 拿到的是**可直接执行**的命令，
而不是需要它自己改写的前缀。

只写用户级目录，不碰项目级目录，不修改 Agent 的其他配置。
"""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import PROJECT_ROOT, python_command

SKILL_NAME = "workon-capture"

#: workon-capture 这个技能文件自己的版本号（与 workon 包版本独立演进）。
#: 装到 Agent 目录后写在 SKILL.md frontmatter 的 ``metadata.version`` 里，
#: ``workon update-check`` 靠它判断「装过去的说明书是不是旧的」。
SKILL_VERSION = "1.0.0"

#: 技能源目录：优先包内（pip 安装后仍可用），回落仓库根的 skills/（源码直接运行）。
PACKAGE_SKILL_DIR = Path(__file__).resolve().parent / "skills" / SKILL_NAME
PROJECT_SKILL_DIR = PROJECT_ROOT / "skills" / SKILL_NAME

#: 启动器文件名（与 SKILL.md 同目录）。
LAUNCHER_CMD = "workon.cmd"
LAUNCHER_SH = "workon.sh"
#: 安装清单文件名，记录装了什么版本、装到哪，供 update-check / uninstall 参考。
INSTALL_RECORD = ".workon-install.json"

_FRONTMATTER_RE = re.compile(r"---\r?\n(.*?)\r?\n---\r?\n", re.S)
_PLACEHOLDER = "{{WORKON}}"


@dataclass(frozen=True)
class AgentTarget:
    """一个可以安装 Agent Skill 的客户端。"""

    key: str
    label: str
    #: 用户级 skills 根目录；用 ~ 表示家目录，便于跨平台。
    root: str
    #: 该客户端是否已在本机出现（用于默认勾选与提示）。
    detect: tuple[str, ...] = ()
    note: str = ""


#: 已核对过官方文档的目录约定。新增客户端只在这里加一行。
AGENT_TARGETS: tuple[AgentTarget, ...] = (
    AgentTarget(
        key="claude",
        label="Claude Code",
        root="~/.claude/skills",
        detect=("~/.claude",),
        note="官方文档：~/.claude/skills/<name>/SKILL.md",
    ),
    AgentTarget(
        key="codex",
        label="Codex CLI / ChatGPT Codex",
        #: 官方文档（learn.chatgpt.com/docs/build-skills）给的用户级位置就是
        #: $HOME/.agents/skills，与下面的通用目录是同一处，安装时按 dest 去重。
        root="~/.agents/skills",
        detect=("~/.codex", "~/.agents"),
        note="官方用户级位置：~/.agents/skills（与通用目录同一处）；$CODEX_HOME/skills 亦被读取",
    ),
    AgentTarget(
        key="qoder",
        label="Qoder",
        root="~/.qoder/skills",
        detect=("~/.qoder",),
        note="官方文档：~/.qoder/skills/<name>/SKILL.md",
    ),
    AgentTarget(
        key="agents",
        label="通用 Agent Skills 目录",
        root="~/.agents/skills",
        detect=("~/.agents",),
        note="Agent Skills 开放标准的跨客户端目录，Qoder 等会读取",
    ),
    AgentTarget(
        key="workbuddy",
        label="WorkBuddy",
        root="~/.workbuddy/skills",
        detect=("~/.workbuddy", "~/WorkBuddy"),
        note="WorkBuddy 的自定义技能目录（本机已实测）；不同版本若路径不同，请改 AGENT_TARGETS",
    ),
)


def _expand(root: str) -> Path:
    return Path(root).expanduser()


def source_skill_dir() -> Path:
    """技能源目录。pip 安装后走包内副本，源码运行时走仓库 skills/。"""
    for candidate in (PACKAGE_SKILL_DIR, PROJECT_SKILL_DIR):
        if (candidate / "SKILL.md").is_file():
            return candidate
    raise FileNotFoundError(
        "找不到技能源文件 SKILL.md；查过这两个位置：\n"
        f"  - {PACKAGE_SKILL_DIR / 'SKILL.md'}\n"
        f"  - {PROJECT_SKILL_DIR / 'SKILL.md'}\n"
        "如果你是从 PyPI 安装的旧版本，请升级 workon。"
    )


# --------------------------------------------------------------------------- #
# 启动器：让 SKILL.md 里的每条命令都能直接执行
# --------------------------------------------------------------------------- #
def _package_importable_anywhere() -> bool:
    """在任意工作目录下 ``import workon`` 是否成立（pip 装过 / editable 装过）。"""
    try:
        probe = subprocess.run(
            [python_command(), "-c", "import workon"],
            cwd=tempfile.gettempdir(),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return probe.returncode == 0


def launcher_bodies() -> tuple[str, str]:
    """返回 (cmd 启动器内容, sh 启动器内容)。

    能 ``import workon`` 时直接 ``-m workon``；否则补 ``PYTHONPATH`` 指向源码根，
    这样项目没 pip 安装也能被外部 Agent 调用。
    """
    py = python_command()
    root = str(PROJECT_ROOT)
    if _package_importable_anywhere():
        py_args = f'"{py}" -m workon'
        sh_py = f'{shlex.quote(py)} -m workon'
        cmd = f'@echo off\r\nsetlocal\r\nset "PYTHONIOENCODING=utf-8"\r\n{py_args} %*\r\n'
        sh = (
            "#!/bin/sh\n"
            "PYTHONIOENCODING=utf-8\n"
            "export PYTHONIOENCODING\n"
            f"exec {sh_py} \"$@\"\n"
        )
        return cmd, sh

    cmd = (
        "@echo off\r\n"
        "setlocal\r\n"
        'set "PYTHONIOENCODING=utf-8"\r\n'
        f'set "PYTHONPATH={root}"\r\n'
        f'"{py}" -m workon %*\r\n'
    )
    sh = (
        "#!/bin/sh\n"
        f"PYTHONPATH={shlex.quote(root)}\n"
        "PYTHONIOENCODING=utf-8\n"
        "export PYTHONPATH PYTHONIOENCODING\n"
        f"exec {shlex.quote(py)} -m workon \"$@\"\n"
    )
    return cmd, sh


def launcher_command(dest_dir: Path | None = None) -> str:
    """SKILL.md 里 ``{{WORKON}}`` 会被替换成这个**已带引号**的启动器路径。

    必须传入本次安装的目标目录：每份 SKILL.md 里写的必须是**它自己所在目录**里的
    启动器，否则装了 A 目录却让 Agent 去调 B 目录的脚本（B 可能根本没装）。
    """
    if dest_dir is None:
        first = next(iter(resolve_targets(None)), None)
        base = _expand(first.root) if first else (Path.home() / ".agents" / "skills")
        dest_dir = base / SKILL_NAME
    if os.name == "nt":
        return f'"{dest_dir / LAUNCHER_CMD}"'
    return shlex.quote(str(dest_dir / LAUNCHER_SH))


# --------------------------------------------------------------------------- #
# 目标解析
# --------------------------------------------------------------------------- #
def available_targets() -> list[dict]:
    """列出所有目标及本机是否已检测到对应客户端、已装版本。"""
    rows = []
    for target in AGENT_TARGETS:
        detected = any(_expand(p).exists() for p in target.detect)
        dest = _expand(target.root) / SKILL_NAME
        rows.append(
            {
                "key": target.key,
                "label": target.label,
                "root": str(_expand(target.root)),
                "dest": str(dest),
                "installed": (dest / "SKILL.md").is_file(),
                "installed_version": read_installed_version(dest),
                "detected": detected,
                "note": target.note,
            }
        )
    return rows


def _dedupe_by_dest(targets: list[AgentTarget]) -> list[AgentTarget]:
    """多个 Agent 可能共用同一个 skills 目录（如 Codex 与通用目录都读 ~/.agents/skills），
    按目标目录去重，避免同一个文件被写/删两次。"""
    seen: set[str] = set()
    unique: list[AgentTarget] = []
    for target in targets:
        dest = str(_expand(target.root) / SKILL_NAME)
        if dest in seen:
            continue
        seen.add(dest)
        unique.append(target)
    return unique


def resolve_targets(keys: list[str] | None = None) -> list[AgentTarget]:
    """按 key 挑选目标；不传则返回本机检测到的客户端（都没有时回落通用目录）。"""
    if keys:
        by_key = {t.key: t for t in AGENT_TARGETS}
        unknown = [k for k in keys if k not in by_key]
        if unknown:
            raise ValueError(f"未知的 Agent 目标: {', '.join(unknown)}；可选: {', '.join(by_key)}")
        return _dedupe_by_dest([by_key[k] for k in keys])

    detected = _dedupe_by_dest(
        [t for t in AGENT_TARGETS if any(_expand(p).exists() for p in t.detect)]
    )
    return detected or [t for t in AGENT_TARGETS if t.key == "agents"]


# --------------------------------------------------------------------------- #
# SKILL.md 渲染
# --------------------------------------------------------------------------- #
def _split_frontmatter(text: str) -> tuple[str, str]:
    """拆出 (frontmatter 正文, 余下内容)。

    先容忍 BOM / 前导空行（编辑器另存常见），再要求 frontmatter 必须是文件开头。
    找不到就报错——宁可失败，也不生成一个客户端加载不了的技能。
    """
    cleaned = text.lstrip("\ufeff").lstrip("\r\n")
    match = _FRONTMATTER_RE.match(cleaned)
    if not match:
        raise ValueError(
            "SKILL.md 缺少合法的 YAML frontmatter（文件必须以 --- 开头，且前 4 行内闭合）"
        )
    return match.group(1), cleaned[match.end():]


def _with_version(frontmatter: str, version: str) -> str:
    """确保 frontmatter 里有 ``metadata.version``。"""
    lines = frontmatter.splitlines()
    out: list[str] = []
    in_metadata = False
    wrote_version = False

    for line in lines:
        if re.match(r"^metadata\s*:", line):
            in_metadata = True
            out.append(line)
            continue
        if in_metadata:
            if line.strip() == "":
                in_metadata = False
                out.append(line)
                continue
            if not line.startswith((" ", "\t")):
                in_metadata = False
                out.append(line)
                continue
            if re.match(r"^\s+version\s*:", line):
                out.append(f"  version: {version}")
                wrote_version = True
                continue
            out.append(line)
            continue
        out.append(line)

    if not wrote_version:
        if any(re.match(r"^metadata\s*:", l) for l in lines):
            # 已有 metadata 块但没 version：在块内第一条子项之前补一行
            rebuilt: list[str] = []
            for line in out:
                rebuilt.append(line)
                if re.match(r"^metadata\s*:", line):
                    rebuilt.append(f"  version: {version}")
            return "\n".join(rebuilt)
        out.append("metadata:")
        out.append(f"  version: {version}")
    return "\n".join(out)


def render_skill_md(source_text: str, *, workon_cmd: str | None = None) -> str:
    """注入版本号、本机路径与启动器命令，产出可直接执行的 SKILL.md。

    - YAML frontmatter 必须仍在文件最开头（banner 只能放在它后面）；
    - 正文里的 ``{{WORKON}}`` 全部替换成本机启动器路径，避免外部 Agent 照抄
      ``python -m workon`` 后报 ``No module named workon``。
    """
    frontmatter, body = _split_frontmatter(source_text)
    frontmatter = _with_version(frontmatter, SKILL_VERSION)

    cmd = workon_cmd or launcher_command()
    body = body.replace(_PLACEHOLDER, cmd)

    banner = (
        "<!-- 由 workon install-skill 生成；换机器 / 换项目路径后请重新安装 -->\n"
        f"<!-- workon 项目根目录：{PROJECT_ROOT} -->\n"
        f"<!-- 解释器：{python_command()} -->\n"
        f"<!-- 技能版本：{SKILL_VERSION} -->\n"
    )
    inject = f"""
## 本机环境（自动注入，请直接用这些路径）

- workon 启动器（本文所有命令里的 `{cmd}` 就是它）：`{cmd}`
- workon 项目根目录：`{PROJECT_ROOT}`
- Python 解释器：`{python_command()}`

上文命令块中的启动器路径是**本机真实路径**，可以原样复制执行。若它失效（项目被移动、
重装 Python），在 workon 项目根下重新跑一次 `install-skill --force` 即可。
"""
    return f"---\n{frontmatter}\n---\n{banner}{inject}\n{body.lstrip(chr(10))}"


def read_installed_version(dest_dir: Path) -> str:
    """读取已安装 SKILL.md 里的 metadata.version；读不到返回空串。"""
    skill_md = dest_dir / "SKILL.md"
    try:
        text = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    match = _FRONTMATTER_RE.match(text.lstrip("\ufeff"))
    if not match:
        return ""
    found = re.search(r"^\s+version\s*:\s*\"?([^\s\"#]+)\"?\s*$", match.group(1), re.M)
    return found.group(1) if found else ""


# --------------------------------------------------------------------------- #
# 安装 / 卸载
# --------------------------------------------------------------------------- #
def _safe_write(path: Path, content: str) -> None:
    """写文件前先拆掉同名符号链接，避免顺着链接改写树外文件。

    ``newline=""`` 不能省：Windows 下 ``write_text`` 默认会把 ``\\n`` 翻成 ``\\r\\n``，
    而启动器内容里已经带了 ``\\r\\n``，不加就会写成 ``\\r\\r\\n``（cmd 会把多出来的
    ``\\r`` 当成命令的一部分，行为难以预料）。
    """
    if path.is_symlink():
        path.unlink()
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)


def install(keys: list[str] | None = None, *, force: bool = False, dry_run: bool = False) -> dict:
    """把 workon-capture 装到目标 Agent 的用户级 skills 目录。"""
    src_dir = source_skill_dir()
    source = src_dir / "SKILL.md"
    try:
        source_text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise FileNotFoundError(f"无法读取技能源文件 {source}：{exc}") from exc

    cmd_body, sh_body = launcher_bodies()

    results = []
    for target in resolve_targets(keys):
        dest_dir = _expand(target.root) / SKILL_NAME
        dest = dest_dir / "SKILL.md"
        # 每个目标目录各渲染一份：SKILL.md 里的启动器路径必须指向它自己所在的目录。
        content = render_skill_md(source_text, workon_cmd=launcher_command(dest_dir))
        row = {
            "key": target.key,
            "label": target.label,
            "dest": str(dest),
            "skill_version": SKILL_VERSION,
            "action": "",
            "ok": True,
        }
        if dry_run:
            row["action"] = "dry-run"
            results.append(row)
            continue
        try:
            if dest.is_file() and not force:
                existing = dest.read_text(encoding="utf-8", errors="replace")
                if existing == content:
                    row["action"] = "unchanged"
                    results.append(row)
                    continue
                row["action"] = "skipped-exists"
                row["ok"] = False
                row["hint"] = "已存在且内容不同；加 --force 覆盖（或先跑 uninstall-skill）"
                results.append(row)
                continue

            dest_dir.mkdir(parents=True, exist_ok=True)
            _safe_write(dest, content)
            _safe_write(dest_dir / LAUNCHER_CMD, cmd_body)
            sh_path = dest_dir / LAUNCHER_SH
            _safe_write(sh_path, sh_body)
            if os.name != "nt":
                try:
                    sh_path.chmod(sh_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)
                except OSError:
                    pass
            _safe_write(
                dest_dir / INSTALL_RECORD,
                json.dumps(
                    {
                        "skill_version": SKILL_VERSION,
                        "project_root": str(PROJECT_ROOT),
                        "python": python_command(),
                        "installed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
            )
            row["action"] = "installed"
        except OSError as exc:
            row["ok"] = False
            row["action"] = "failed"
            row["error"] = str(exc)
        results.append(row)

    changed = sum(1 for r in results if r["action"] == "installed")
    unchanged = sum(1 for r in results if r["action"] == "unchanged")
    skipped = sum(1 for r in results if r["action"] == "skipped-exists")
    failed = sum(1 for r in results if r["action"] == "failed")
    return {
        "ok": failed == 0 and skipped == 0,
        "skill_version": SKILL_VERSION,
        "changed": changed,
        "unchanged": unchanged,
        "skipped": skipped,
        "failed": failed,
        "results": results,
    }


def uninstall(keys: list[str] | None = None, *, dry_run: bool = False) -> dict:
    """从目标 Agent 目录移除 workon-capture（只删自己那个文件夹）。"""
    results = []
    for target in resolve_targets(keys):
        dest_dir = _expand(target.root) / SKILL_NAME
        row = {"key": target.key, "dest": str(dest_dir), "action": "", "ok": True}
        # 断链的目录符号链接 exists() 为 False，必须再看 is_symlink()，否则会静默残留。
        if not dest_dir.exists() and not dest_dir.is_symlink():
            row["action"] = "absent"
            results.append(row)
            continue
        if dry_run:
            row["action"] = "dry-run"
            results.append(row)
            continue
        try:
            _remove_tree(dest_dir)
            row["action"] = "removed"
        except OSError as exc:
            row["ok"] = False
            row["action"] = "failed"
            row["error"] = str(exc)
        results.append(row)

    return {"ok": all(r["ok"] for r in results), "results": results}


def _remove_tree(directory: Path) -> None:
    """删除技能目录；只允许删名为 SKILL_NAME 的目录，避免误删用户其他技能。

    三种需要单独处理的情况（Windows 上很常见）：
    - 目标是**符号链接**：``shutil.rmtree`` 会拒绝（"Cannot call rmtree on
      a symbolic link"），但删掉这个链接本身是安全的、也是用户的真实意图。
    - 目录里有**只读文件**（``WinError 5``）与被占用文件（``WinError 32``）：
      先把可写位补上再重试一次；被占用的只能报错并如实说明，不做半删。
    - 目录里有 **junction**（Windows 目录联接）：``shutil.rmtree`` 只删链接本身，
      不会穿透删掉外部真实目录里的文件。
    """
    if directory.name != SKILL_NAME:
        raise OSError(f"拒绝删除非 {SKILL_NAME} 目录：{directory}")
    if not directory.exists() and not directory.is_symlink():
        return
    if directory.is_symlink():
        directory.unlink()
        return

    def _retry(func, path, _exc):  # noqa: ANN001 - shutil 回调签名固定
        # 只读属性导致删不掉时，补上写权限后重试一次；其他错误原样抛出。
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except OSError:
            raise

    if sys.version_info >= (3, 12):
        # Python 3.12 起 onerror 废弃，改用 onexc；两者签名不同，按版本分流避免告警。
        shutil.rmtree(directory, onexc=_retry)
    else:
        shutil.rmtree(directory, onerror=_retry)

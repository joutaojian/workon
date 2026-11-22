# coding: utf-8
"""检查本机的 workon 与已安装技能是否需要更新。

两层版本号，各自独立演进：

- **包版本**（``workon.__version__``）：执行引擎本身，跟着 GitHub Releases / PyPI 走。
  ``workon update-check`` 会去上游问一次最新版，告诉用户该不该 ``pip install -U``。
- **技能版本**（``install.SKILL_VERSION``）：``workon-capture`` 这份说明书自身。
  它被复制到各 Agent 的 skills 目录后就不再跟着项目走，所以要用
  ``workon install-skill --force`` 重新装一次才会更新。

本模块只做**只读检查**，不自动下载、不自动覆盖、不写任何文件；装不装由用户决定。
所有网络请求都有超时并失败降级：断网时给出明确提示，而不是抛栈。
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

from . import __version__ as PACKAGE_VERSION
from .config import PROJECT_ROOT as _PROJECT_ROOT
from .install import SKILL_VERSION, available_targets

#: 上游仓库。发布前请连同 pyproject.toml 的 project.urls 一起改成真实地址。
REPO_SLUG = "joutaojian/workon"
#: 注意：PyPI 上 ``workon`` 这个名字**已被别的项目占用**（不是本仓库）。
#: 所以只有确认 PyPI 项目的 homepage/repository 指向本仓库时，才把它的版本当上游，
#: 否则 ``pip install -U workon`` 会装成别人的包 —— 这比「不提示更新」危险得多。
PYPI_NAME = "workon"
_USER_AGENT = f"workon/{PACKAGE_VERSION} (+https://github.com/{REPO_SLUG})"
_TIMEOUT = 6

_VERSION_RE = re.compile(r"(\d+(?:\.\d+)*)")


def _http_json(url: str) -> dict[str, Any]:
    """GET 一个 JSON 接口；任何失败都抛 RuntimeError，由调用方降级处理。"""
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}：{url}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"网络不可达：{exc}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"响应不是合法 JSON：{url}") from exc


def parse_version(text: str) -> tuple[int, ...]:
    """把 ``v1.2.3`` / ``1.2.3-beta`` 之类归一成可比较的元组。"""
    match = _VERSION_RE.search(text or "")
    if not match:
        return ()
    return tuple(int(part) for part in match.group(1).split("."))


def is_newer(candidate: str, current: str) -> bool:
    """candidate 是否比 current 新（按数字段逐位比较，缺失位补 0）。"""
    left, right = parse_version(candidate), parse_version(current)
    if not left:
        return False
    width = max(len(left), len(right))
    left += (0,) * (width - len(left))
    right += (0,) * (width - len(right))
    return left > right


def _pypi_is_ours(payload: dict[str, Any]) -> bool:
    """PyPI 上的同名项目是否**属于本仓库**。

    PyPI 的 ``workon`` 名字被别的项目占着，若不加判断，用户会被提示升级到别人的包。
    判据：项目信息里的任一 URL 指向本仓库。
    """
    info = payload.get("info", {}) or {}
    candidates = []
    for key in ("home_page", "project_url", "download_url"):
        value = info.get(key)
        if isinstance(value, str):
            candidates.append(value)
    # project_urls 通常是 {名称: URL} 字典；要检查的是值（URL），不是键（名称）。
    project_urls = info.get("project_urls") or {}
    if isinstance(project_urls, dict):
        candidates.extend(str(v) for v in project_urls.values() if isinstance(v, str))
    elif isinstance(project_urls, (list, tuple)):
        candidates.extend(str(v) for v in project_urls if isinstance(v, str))
    needle = REPO_SLUG.lower()
    return any(needle in str(value).lower() for value in candidates)


def latest_package_version() -> dict[str, Any]:
    """向上游要最新包版本。先 GitHub Releases → GitHub Tags → PyPI。

    PyPI 放在最后且必须通过 ``_pypi_is_ours`` 校验：宁可少提示一次更新，
    也不能把用户引导去安装另一个作者的同名包。
    """
    try:
        payload = _http_json(f"https://api.github.com/repos/{REPO_SLUG}/releases/latest")
        version = str(payload.get("tag_name") or payload.get("name") or "").strip()
        if version:
            return {"version": version, "source": "github-releases"}
    except RuntimeError:
        pass

    try:
        payload = _http_json(f"https://api.github.com/repos/{REPO_SLUG}/tags")
        if isinstance(payload, list):
            best = ""
            for item in payload:
                tag = str(item.get("name") or "")
                if parse_version(tag) and is_newer(tag, best):
                    best = tag
            if best:
                return {"version": best, "source": "github-tags"}
    except RuntimeError:
        pass

    try:
        payload = _http_json(f"https://pypi.org/pypi/{PYPI_NAME}/json")
        if _pypi_is_ours(payload):
            version = str(payload.get("info", {}).get("version") or "").strip()
            if version:
                return {"version": version, "source": "pypi"}
        else:
            return {
                "version": "",
                "source": "",
                "error": (
                    f"PyPI 上的 {PYPI_NAME} 属于另一个项目（不是本仓库），已忽略；"
                    "本项目尚未发布到 PyPI，请以 GitHub 仓库为准"
                ),
            }
    except RuntimeError:
        pass

    return {"version": "", "source": "", "error": "上游都不可达或没有发布版本（可离线使用，不影响运行）"}


def check(agent_keys: list[str] | None = None, *, offline: bool = False) -> dict[str, Any]:
    """汇总一次检查结果：包是否该升级 + 各 Agent 目录里装的技能是否过期。"""
    if offline:
        upstream: dict[str, Any] = {"version": "", "source": "", "error": "已按 --offline 跳过联网"}
    else:
        upstream = latest_package_version()

    latest = str(upstream.get("version") or "")
    package = {
        "current": PACKAGE_VERSION,
        "latest": latest,
        "update_available": bool(latest) and is_newer(latest, PACKAGE_VERSION),
        "source": upstream.get("source", ""),
    }
    if upstream.get("error"):
        package["error"] = upstream["error"]

    installs = []
    for row in available_targets():
        if agent_keys and row["key"] not in agent_keys:
            continue
        installed = row.get("installed_version") or ""
        installs.append(
            {
                "key": row["key"],
                "label": row["label"],
                "dest": row["dest"],
                "installed": row["installed"],
                "installed_version": installed,
                "outdated": bool(row["installed"]) and bool(installed) and is_newer(SKILL_VERSION, installed),
            }
        )

    skills = {
        "current": SKILL_VERSION,
        "installs": installs,
        "installed_count": sum(1 for i in installs if i["installed"]),
        "outdated_count": sum(1 for i in installs if i["outdated"]),
    }

    hints = []
    if package["update_available"]:
        hints.append(
            f"执行引擎有新版本 {latest}：git -C \"{_PROJECT_ROOT}\" pull 后重装"
            "（本项目尚未发布到 PyPI，别用 pip install -U）"
        )
    if skills["outdated_count"]:
        hints.append("刷新 Agent 里的说明书：workon install-skill --force")
    if skills["installed_count"] == 0:
        hints.append("还没装进任何 Agent：workon install-skill（先看 workon install-skill --list）")
    if not hints:
        hints.append("都是最新的，无需操作")

    return {
        "package": package,
        "skill": skills,
        "need_update": package["update_available"] or skills["outdated_count"] > 0,
        "hints": hints,
    }

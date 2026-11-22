# coding: utf-8
"""Flask Web 界面与 HTTP API（Flask 为可选依赖，CLI 不依赖它）。"""
from __future__ import annotations

import base64
import json
import shutil
import tempfile
from pathlib import Path

import hmac

from flask import Flask, Response, jsonify, redirect, request, session, url_for

from . import __version__
from .capture import scan_directory
from .config import settings
from .pages import HOME_HTML, LOGIN_HTML
from .web_pages import WORKBENCH_HTML
from .models import ManifestError, validate_manifest
from .registry import registry
from .runner import InvocationError, invoke
from .storage import get_run, list_runs


def ok(data=None):
    return jsonify({"code": 0, "message": "success", "data": data})


def fail(message: str, code: int = 1, http_status: int = 400):
    return jsonify({"code": code, "message": message, "data": None}), http_status


def _parse_json_object(raw: str | None, label: str) -> tuple[dict | None, str | None]:
    """安全解析 JSON 对象；失败返回 (None, 错误信息)。"""
    if not raw:
        return {}, None
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return None, f"{label} 不是合法 JSON"
    if not isinstance(value, dict):
        return None, f"{label} 必须是对象"
    return value, None


def _parse_int(raw, default: int) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _validate_settings_payload(payload: dict) -> str | None:
    """校验设置 payload；返回 None 表示合法，否则返回错误信息。"""
    if "skill_dirs" in payload:
        dirs = payload["skill_dirs"]
        if not isinstance(dirs, list) or not all(isinstance(d, str) for d in dirs):
            return "skill_dirs 必须是字符串数组"
    if "password" in payload and not isinstance(payload["password"], str):
        return "password 必须是字符串"
    return None


def _get_skill_or_404(skill_id: str):
    """返回技能对象或 (fail 响应, 状态码)。
    
    调用方：obj = _get_skill_or_404(sid)
            if isinstance(obj, tuple): return obj
    """
    skill = registry.get(skill_id)
    if not skill:
        return fail(f"技能不存在: {skill_id}", http_status=404)
    return skill



def _collect_run_inputs(skill, payload: dict):
    """收集 run 的 inputs/params。返回 (inputs, params, error_response)。"""
    inputs = payload.get("inputs") or {}
    params = payload.get("params") or {}

    # 支持 multipart 文件上传：文件名对应 manifest 中的 input name
    if request.mimetype == "multipart/form-data":
        inputs, err = _parse_json_object(request.form.get("inputs"), "inputs")
        if err:
            return None, None, fail(err)
        params, err = _parse_json_object(request.form.get("params"), "params")
        if err:
            return None, None, fail(err)
        for field in skill.inputs:
            if field["type"] in {"text", "json"}:
                continue
            files = request.files.getlist(field["name"])
            files = [f for f in files if f and f.filename]
            if not files:
                continue
            if field.get("multiple"):
                inputs[field["name"]] = [
                    {"filename": f.filename, "content": f.read()} for f in files
                ]
            else:
                f = files[0]
                inputs[field["name"]] = {
                    "filename": f.filename,
                    "content": f.read(),
                }
    # text/json 数组输入：runner 期望 text 为标量、文件类为 dict；
    # multiple=true 的 text/json 允许列表，原样透传给执行器。
    if not isinstance(inputs, dict) or not isinstance(params, dict):
        return None, None, fail("inputs 与 params 必须是对象")
    return inputs, params, None


def _serialize_outputs(result: dict) -> list[dict]:
    """把 result 中的输出文件转成 base64 可下载列表，原地替换 outputs.files。"""
    files = []
    for f in result["outputs"].get("files", []):
        path = Path(f["path"])
        is_dir = bool(f.get("is_dir") or f.get("kind") == "dir") or (
            path.is_dir() and not path.is_file()
        )
        if is_dir and path.is_dir():
            # 目录输出：遍历持久化目录逐文件回传，文件名带目录名与相对路径
            dirname = f.get("filename") or path.name or "dir"
            for child in sorted(p for p in path.rglob("*") if p.is_file()):
                rel = child.relative_to(path).as_posix()
                files.append(
                    {
                        "name": f.get("name", ""),
                        "filename": f"{dirname}/{rel}",
                        "size": child.stat().st_size,
                        "content_base64": base64.b64encode(child.read_bytes()).decode("ascii"),
                    }
                )
        elif path.is_file():
            files.append(
                {
                    "name": f["name"],
                    "filename": f["filename"],
                    "size": f["size"],
                    "content_base64": base64.b64encode(path.read_bytes()).decode("ascii"),
                }
            )
    result["outputs"]["files"] = files
    return files

def create_app() -> Flask:
    settings.ensure_dirs()
    app = Flask(__name__, static_folder=None)
    app.config["MAX_CONTENT_LENGTH"] = settings.max_upload_mb * 1024 * 1024
    app.secret_key = settings.secret_key
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    def _logged_in() -> bool:
        return bool(session.get("workon_logged_in"))

    @app.before_request
    def _auth_guard():
        """首页/登录/健康检查公开；工作台页面与所有 API 需要登录。"""
        path = request.path
        # /static/* 为预留公开白名单（鉴权约定不变）：当前 Flask 实例 static_folder=None，
        # 页面零外部资源，静态路由已禁用，此分支当前不会命中任何真实请求。
        if path in {"/", "/login", "/health"} or path.startswith("/static/"):
            return None
        if _logged_in():
            return None
        if path.startswith("/api/"):
            return jsonify({"code": 401, "message": "未登录，请先访问 /login", "data": None}), 401
        return redirect(url_for("login"))

    @app.get("/")
    def home():
        """公开首页：展示使用方案，引导登录后进入工作台。"""
        return Response(HOME_HTML, mimetype="text/html; charset=utf-8")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        """密码登录：仅校验单一访问密码，默认 workon。"""
        if request.method == "GET":
            if _logged_in():
                return redirect(url_for("workbench"))
            return Response(
                LOGIN_HTML.replace("__ERROR_MSG__", ""),
                mimetype="text/html; charset=utf-8",
            )
        password = request.form.get("password", "")
        if hmac.compare_digest(password, settings.password):
            session.clear()
            session["workon_logged_in"] = True
            return redirect(url_for("workbench"))
        html = LOGIN_HTML.replace("__ERROR_MSG__", "密码不正确，请重试")
        return Response(html, mimetype="text/html; charset=utf-8"), 401

    @app.get("/logout")
    def logout():
        session.clear()
        return redirect(url_for("home"))

    @app.get("/workbench")
    def workbench():
        """登录后的技能工作台。"""
        html = WORKBENCH_HTML.replace("__VERSION__", __version__)
        return Response(html, mimetype="text/html; charset=utf-8")

    @app.get("/api/skills")
    def api_skills():
        return ok([s.public() for s in registry.list(tag=request.args.get("tag"), query=request.args.get("q"))])

    @app.get("/api/tags")
    def api_tags():
        return ok(registry.tags())

    @app.get("/api/skills/<skill_id>")
    def api_skill_detail(skill_id: str):
        skill = _get_skill_or_404(skill_id)
        if isinstance(skill, tuple):
            return skill
        return ok(skill.public())

    @app.post("/api/skills/reload")
    def api_reload():
        registry.reload()
        return ok({"skills": registry.all_ids(), "errors": registry.errors})

    @app.get("/api/settings")
    def api_settings_get():
        return ok(settings.public())

    @app.post("/api/settings")
    def api_settings_post():
        payload = request.get_json(silent=True) or {}
        err = _validate_settings_payload(payload)
        if err:
            return fail(err)
        try:
            return ok(settings.save(payload))
        except OSError as exc:
            return fail(f"保存设置失败: {exc}", http_status=500)

    @app.post("/api/capture")
    def api_capture():
        """扫描一个已完成工作的目录，生成（可选写入）manifest。"""
        payload = request.get_json(silent=True) or {}
        raw_path = payload.get("path") or payload.get("dir")
        source = Path(str(raw_path or "")).expanduser()
        if not raw_path or not source.is_dir():
            return fail("path 必须是指向已存在目录的路径")
        tags = payload.get("tags")
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]
        elif tags is None:
            tags = []
        elif not isinstance(tags, list):
            return fail("tags 必须是字符串或数组")
        overwrite = bool(payload.get("overwrite", False))
        try:
            manifest = scan_directory(
                str(source),
                payload.get("id"),
                payload.get("name"),
                tags,
                payload.get("entry"),
                overwrite=overwrite,
            )
        except (ValueError, OSError) as exc:  # 仅捕获预期的输入/IO 错误，不吞程序员错误
            return fail(f"扫描目录失败: {type(exc).__name__}: {exc}")
        registry.reload()
        return ok(manifest)

    @app.post("/api/skills/save")
    def api_skill_save():
        """把 AI 生成的脚本目录保存为一个技能（可选）。"""
        payload = request.get_json(silent=True) or {}
        source = Path(str(payload.get("path") or "")).expanduser()
        if not source.is_dir() or not (source / "manifest.json").is_file():
            return fail("path 必须是指向含 manifest.json 的目录")
        try:
            raw = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
            skill = validate_manifest(raw, source, str(source))
        except (ManifestError, json.JSONDecodeError, OSError) as exc:
            return fail(f"manifest 校验失败: {exc}")
        # 官方内置能力不可被用户技能覆盖或冒充
        existing = registry.get(skill.id)
        if existing and existing.official:
            return fail(f"技能 id「{skill.id}」是官方内置能力，不可覆盖")
        dest_root = Path(settings.skill_dirs[0]).resolve()
        dest = dest_root / skill.id
        if dest.exists() and not payload.get("overwrite"):
            return fail(f"技能已存在: {dest}（可传 overwrite=true 覆盖）")
        # 先复制到临时目录，校验无误后再原子替换，避免留下半成品。
        try:
            dest_root.mkdir(parents=True, exist_ok=True)
            tmp_root = Path(tempfile.mkdtemp(prefix=".workon-save-", dir=str(dest_root)))
            try:
                staged = tmp_root / skill.id
                shutil.copytree(source, staged)
                if not (staged / "manifest.json").is_file():
                    raise OSError("复制后 manifest.json 缺失，已中止覆盖")
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.move(str(staged), str(dest))
            finally:
                shutil.rmtree(tmp_root, ignore_errors=True)
        except OSError as exc:
            return fail(f"保存技能失败: {exc}", http_status=500)
        registry.reload()
        return ok({"id": skill.id, "path": str(dest)})

    @app.post("/api/skills/<skill_id>/run")
    def api_run(skill_id: str):
        skill = _get_skill_or_404(skill_id)
        if isinstance(skill, tuple):
            return skill
        payload = request.get_json(silent=True) or {}
        inputs, params, err = _collect_run_inputs(skill, payload)
        if err:
            return err

        try:
            result = invoke(skill, inputs, params)
        except InvocationError as exc:
            return fail(str(exc))

        status = result["status"]
        http_status = 200 if status in {"success", "failed", "timeout"} else 500
        _serialize_outputs(result)
        return jsonify(result), http_status

    @app.get("/api/history")
    def api_history():
        return ok(list_runs(request.args.get("skill"), _parse_int(request.args.get("limit"), 100)))

    @app.get("/api/history/<run_id>")
    def api_history_detail(run_id: str):
        item = get_run(run_id)
        if not item:
            return fail("执行记录不存在", http_status=404)
        return ok(item)

    @app.get("/health")
    def health():
        return ok({"status": "ok", "skills": len(registry.all_ids())})

    return app


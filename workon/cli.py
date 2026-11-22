# coding: utf-8
"""workon 命令行入口：发现、查看、保存、召唤技能。"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import __version__
from .config import settings
from .models import ManifestError, validate_manifest
from .registry import registry
from .runner import InvocationError, invoke
from .storage import get_run, list_runs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workon",
        description="workon — 将固定工作固化为可一键召唤的技能",
    )
    parser.add_argument("--version", action="version", version=f"workon {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="启动 Web 界面与 API 服务")
    serve.add_argument("--host", default=settings.host)
    serve.add_argument("--port", type=int, default=settings.port)
    serve.add_argument("--reload", action="store_true", help="开发模式自动重载")

    skill = sub.add_parser("skill", help="技能管理")
    skill_sub = skill.add_subparsers(dest="skill_command", required=True)

    skill_sub.add_parser("list", help="列出所有技能").add_argument("--tag", help="按标签过滤")
    show = skill_sub.add_parser("show", help="查看技能 manifest")
    show.add_argument("skill_id")
    validate = skill_sub.add_parser("validate", help="校验技能目录")
    validate.add_argument("path")
    add = skill_sub.add_parser("add", help="登记外部技能目录（写入 data/settings.json）")
    add.add_argument("path", help="外部目录路径（私有 git 项目）")
    save = skill_sub.add_parser("save", help="把一个目录保存为内置技能")
    save.add_argument("path", help="源目录（含 manifest.json 与脚本）")
    save.add_argument("--id", help="目标技能 id，默认使用 manifest 的 id")
    skill_sub.add_parser("reload", help="重新扫描技能目录")

    run = skill_sub.add_parser("run", help="召唤技能")
    run.add_argument("skill_id")
    run.add_argument("--input", action="append", default=[], metavar="KEY=VALUE", help="文本输入，可多次")
    run.add_argument("--file", action="append", default=[], metavar="KEY=PATH", help="文件输入，可多次")
    run.add_argument("--param", action="append", default=[], metavar="KEY=VALUE", help="运行参数，可多次")
    run.add_argument("--json", help="从 JSON 文件读取 inputs 与 params")

    capture = sub.add_parser("capture", help="扫描目录自动生成 manifest.json 并固化技能")
    capture.add_argument("path", help="工作目录（含脚本与依赖）")
    capture.add_argument("--id", required=True, help="技能 id（字母/数字/下划线/连字符）")
    capture.add_argument("--name", default="", help="显示名称，默认用 id")
    capture.add_argument("--tags", default="", help="标签，逗号分隔，如 excel,report")
    capture.add_argument("--entry", default="", help='入口命令，如 "python run.py"；留空自动推断')
    capture.add_argument("--description", default="", help="技能描述")
    capture.add_argument("--timeout", type=int, default=120, help="超时秒数，默认 120")
    capture.add_argument(
        "--multiple",
        action="append",
        default=[],
        metavar="FIELD",
        help="把指定输入/输出字段标记为 multiple=true，可多次",
    )
    capture.add_argument(
        "--yes", action="store_true", help="非交互：直接写入 manifest.json 并打印 JSON"
    )

    init = sub.add_parser("init", help="交互式向导生成 manifest.json")
    init.add_argument("path", help="工作目录（含脚本与依赖）")

    install_skill = sub.add_parser(
        "install-skill",
        help="把 workon-capture 技能装进 Claude Code / Codex / Qoder 等 Agent",
    )
    install_skill.add_argument(
        "--agent",
        action="append",
        default=[],
        metavar="KEY",
        help="目标 Agent，可多次；留空则自动装到本机已检测到的客户端",
    )
    install_skill.add_argument("--force", action="store_true", help="覆盖已存在的同名技能")
    install_skill.add_argument("--dry-run", action="store_true", help="只显示会写到哪里，不落盘")
    install_skill.add_argument(
        "--list", action="store_true", dest="list_agents", help="列出所有可安装目标与本机检测情况"
    )

    uninstall_skill = sub.add_parser("uninstall-skill", help="从 Agent 目录移除 workon-capture")
    uninstall_skill.add_argument("--agent", action="append", default=[], metavar="KEY")
    uninstall_skill.add_argument("--dry-run", action="store_true")

    update_check = sub.add_parser(
        "update-check", help="检查 workon 本身与已装技能是否需要更新（只读，不自动升级）"
    )
    update_check.add_argument("--agent", action="append", default=[], metavar="KEY")
    update_check.add_argument(
        "--offline", action="store_true", help="只看本机已装版本，不联网"
    )

    history = sub.add_parser("history", help="查看执行历史")
    history.add_argument("--skill", help="按技能 id 过滤")
    history.add_argument("--limit", type=int, default=20)
    history.add_argument("--run", help="查看某次执行的详情")

    tags = sub.add_parser("tags", help="列出所有标签")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "serve":
        from .web import create_app

        app = create_app()
        app.run(host=args.host, port=args.port, debug=args.reload or settings.debug, use_reloader=args.reload)
        return 0

    if args.command == "tags":
        print_json(registry.tags())
        return 0

    if args.command == "history":
        if args.run:
            print_json(get_run(args.run) or {"error": "run_id 不存在"})
        else:
            print_json(list_runs(args.skill, args.limit))
        return 0

    if args.command == "skill":
        return _handle_skill(args)

    if args.command == "capture":
        return _handle_capture(args)

    if args.command == "init":
        return _handle_init(args)

    if args.command == "install-skill":
        return _handle_install_skill(args)

    if args.command == "uninstall-skill":
        from .install import uninstall

        try:
            result = uninstall(args.agent or None, dry_run=args.dry_run)
        except ValueError as exc:
            print_error(str(exc))
            return 1
        print_json(result)
        return 0 if result.get("ok") else 1

    if args.command == "update-check":
        return _handle_update_check(args)

    parser.print_help()
    return 1


def _handle_skill(args: argparse.Namespace) -> int:
    cmd = args.skill_command

    if cmd == "list":
        print_json([s.public() for s in registry.list(tag=args.tag)])
        return 0

    if cmd == "show":
        skill = registry.get(args.skill_id)
        if not skill:
            print_error(f"技能不存在: {args.skill_id}")
            return 1
        print_json(skill.public())
        return 0

    if cmd == "validate":
        path = Path(args.path)
        manifest = path / "manifest.json"
        if not manifest.is_file():
            print_error(f"找不到 manifest.json: {manifest}")
            return 1
        try:
            skill = validate_manifest(json.loads(manifest.read_text(encoding="utf-8")), path, str(path))
            print_json({"valid": True, "id": skill.id, "name": skill.name})
            return 0
        except (ManifestError, json.JSONDecodeError, OSError) as exc:
            print_error(str(exc))
            return 1

    if cmd == "reload":
        registry.reload()
        print_json({"skills": registry.all_ids(), "errors": registry.errors})
        return 0

    if cmd == "add":
        path = Path(args.path).expanduser().resolve()
        if not path.is_dir():
            print_error(f"目录不存在: {path}")
            return 1
        current = list(settings.skill_dirs)
        if str(path) not in current:
            current.append(str(path))
        print_json(settings.save({"skill_dirs": current}))
        return 0

    if cmd == "save":
        source = Path(args.path).expanduser().resolve()
        manifest = source / "manifest.json"
        if not manifest.is_file():
            print_error(f"找不到 manifest.json: {manifest}")
            return 1
        try:
            raw = json.loads(manifest.read_text(encoding="utf-8"))
            skill_id = args.id or raw.get("id")
            if not skill_id:
                raise ManifestError("manifest 缺少 id")
        except (ManifestError, json.JSONDecodeError, OSError) as exc:
            print_error(str(exc))
            return 1
        dest = Path(settings.skill_dirs[0]).resolve() / skill_id
        if dest.exists():
            print_error(f"目标已存在: {dest}")
            return 1
        shutil.copytree(source, dest)
        registry.reload()
        print_json({"saved": str(dest), "id": skill_id})
        return 0

    if cmd == "run":
        skill = registry.get(args.skill_id)
        if not skill:
            print_error(f"技能不存在: {args.skill_id}")
            return 1
        inputs: dict[str, object] = {}
        params: dict[str, object] = {}
        if args.json:
            payload = json.loads(Path(args.json).read_text(encoding="utf-8"))
            inputs.update(payload.get("inputs", {}))
            params.update(payload.get("params", {}))
        for item in args.input:
            key, _, value = item.partition("=")
            inputs[key] = value
        # 同一 key 多次 --file 时聚合成数组，供 multiple=true 输入使用；
        # 单次仍为单个对象，保持向后兼容。
        file_groups: dict[str, list[dict[str, str]]] = {}
        for item in args.file:
            key, _, value = item.partition("=")
            path = Path(value).expanduser().resolve()
            if not path.is_file():
                print_error(f"输入文件不存在: {path}")
                return 1
            file_groups.setdefault(key, []).append({"filename": path.name, "path": str(path)})
        for key, values in file_groups.items():
            inputs[key] = values[0] if len(values) == 1 else values
        for item in args.param:
            key, _, value = item.partition("=")
            params[key] = value
        try:
            result = invoke(skill, inputs, params)
        except InvocationError as exc:
            print_error(str(exc))
            return 1
        print_json(result)
        return 0 if result["status"] == "success" else 2

    print_error("未知命令")
    return 1


def _handle_capture(args: argparse.Namespace) -> int:
    from .capture import scan_directory, write_manifest

    path = Path(args.path).expanduser().resolve()
    tags = [t.strip() for t in (args.tags or "").split(",") if t.strip()]
    try:
        manifest = scan_directory(
            path,
            skill_id=args.id,
            name=args.name,
            tags=tags,
            entry=args.entry,
            description=args.description,
            timeout_seconds=args.timeout,
            multiple=args.multiple,
            write=bool(args.yes),
        )
    except ValueError as exc:
        print_error(str(exc))
        return 1

    if args.yes:
        # --yes：已由上 writes 落盘，打印包含落盘路径的 JSON 回执
        manifest_path = path / "manifest.json"
        print_json({"manifest": manifest, "path": str(manifest_path), "written": True})
    else:
        # 非 --yes 但也不交互：只预览，不写盘，提示加 --yes 固化
        print_json({"manifest": manifest, "written": False, "hint": "加 --yes 写入 manifest.json"})
    return 0


def _handle_init(args: argparse.Namespace) -> int:
    from .capture import interactive_init

    path = Path(args.path).expanduser().resolve()
    try:
        manifest = interactive_init(path)
    except ValueError as exc:
        print_error(str(exc))
        return 1
    if manifest is None:
        return 1
    print_json({"id": manifest["id"], "name": manifest["name"], "written": True})
    return 0


def _handle_install_skill(args: argparse.Namespace) -> int:
    from .install import available_targets, install

    if args.list_agents:
        print_json(available_targets())
        return 0
    try:
        result = install(args.agent or None, force=args.force, dry_run=args.dry_run)
    except (ValueError, FileNotFoundError) as exc:
        print_error(str(exc))
        return 1
    print_json(result)
    if result.get("ok"):
        return 0
    # 已存在但内容不同不是「失败」，用退出码 2 区分，免得用户误以为装挂了。
    return 2 if result.get("skipped") else 1


def _handle_update_check(args: argparse.Namespace) -> int:
    from .update import check

    try:
        result = check(args.agent or None, offline=args.offline)
    except ValueError as exc:
        print_error(str(exc))
        return 1
    print_json(result)
    return 0


def print_json(data: object) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def print_error(message: str) -> None:
    print(f"错误: {message}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())

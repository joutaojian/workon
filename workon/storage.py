# coding: utf-8
"""本地 SQLite 唯一存储。

本模块是 workon 运行历史的唯一持久化实现：仅使用 Python 标准库 sqlite3，
不依赖任何外部数据库驱动或 ORM。数据库文件由 settings.db_path 指定（本地文件）。
所有改动保持向后兼容：表结构用 CREATE TABLE IF NOT EXISTS，旧行缺字段/非法 JSON
均可安全读取；record_run/list_runs/get_run 的签名保持不变。
"""
from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Any

from .config import settings

_LOCK = threading.Lock()
# init_db 幂等缓存：记录已建表的数据库路径。db_path 变化时自动重建，避免运行时切换路径后缺表。
_INITIALIZED_DB: str | None = None


def _connect() -> sqlite3.Connection:
    settings.ensure_dirs()
    conn = sqlite3.connect(settings.db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def _db():
    with _LOCK:
        conn = _connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()


def _json_dumps(value: Any) -> str:
    """稳健序列化为 JSON 文本；不可序列化对象退化为字符串，绝不抛异常。"""
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        try:
            return json.dumps({} if value is None else str(value), ensure_ascii=False)
        except Exception:
            return "{}"


def _json_loads(value: Any) -> Any:
    """稳健反序列化：兼容旧行（NULL/空串/非法 JSON），失败一律返回空字典。"""
    if value is None or value == "":
        return {}
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return {}


def init_db() -> None:
    global _INITIALIZED_DB
    if _INITIALIZED_DB == settings.db_path:
        return
    with _db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL UNIQUE,
                skill_id TEXT NOT NULL,
                skill_name TEXT,
                status TEXT NOT NULL,
                duration_ms INTEGER DEFAULT 0,
                inputs TEXT,
                params TEXT,
                outputs TEXT,
                error TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_skill ON runs(skill_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_created ON runs(created_at)")
    _INITIALIZED_DB = settings.db_path


def record_run(
    run_id: str,
    skill_id: str,
    skill_name: str,
    status: str,
    duration_ms: int,
    inputs: dict[str, Any],
    params: dict[str, Any],
    outputs: dict[str, Any],
    error: str = "",
) -> None:
    init_db()
    with _db() as conn:
        conn.execute(
            """INSERT INTO runs
               (run_id, skill_id, skill_name, status, duration_ms, inputs, params, outputs, error, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                run_id,
                skill_id,
                skill_name,
                status,
                int(duration_ms),
                _json_dumps(inputs),
                _json_dumps(params),
                _json_dumps(outputs),
                error or "",
                datetime.now().isoformat(timespec="seconds"),
            ),
        )


def list_runs(skill_id: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    init_db()
    with _db() as conn:
        if skill_id:
            rows = conn.execute(
                "SELECT * FROM runs WHERE skill_id=? ORDER BY id DESC LIMIT ?",
                (skill_id, limit),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        for key in ("inputs", "params", "outputs"):
            item[key] = _json_loads(item.get(key))
        result.append(item)
    return result


def get_run(run_id: str) -> dict[str, Any] | None:
    init_db()
    with _db() as conn:
        row = conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
    if not row:
        return None
    item = dict(row)
    for key in ("inputs", "params", "outputs"):
        item[key] = _json_loads(item.get(key))
    return item


def stats() -> dict[str, Any]:
    """返回运行历史的聚合计数（按 skill/status 分组，并附各维度小计与总数）。"""
    init_db()
    with _db() as conn:
        rows = conn.execute(
            "SELECT skill_id, status, COUNT(*) AS count "
            "FROM runs GROUP BY skill_id, status ORDER BY skill_id, status"
        ).fetchall()

    by_skill_status: dict[str, dict[str, int]] = {}
    by_status: dict[str, int] = {}
    by_skill: dict[str, int] = {}
    total = 0
    for row in rows:
        skill = row["skill_id"] or ""
        status = row["status"] or ""
        count = int(row["count"])
        by_skill_status.setdefault(skill, {})[status] = count
        by_status[status] = by_status.get(status, 0) + count
        by_skill[skill] = by_skill.get(skill, 0) + count
        total += count

    return {
        "total": total,
        "by_skill_status": by_skill_status,
        "by_status": by_status,
        "by_skill": by_skill,
    }


init_db()

# coding: utf-8
"""针对 workon v0.2 契约的单元测试。

只依赖标准库 unittest/tempfile，不依赖外部服务。
v0.2 契约要点：
  - INPUT_TYPES / OUTPUT_TYPES 含 json、image、dir
  - 字段带 multiple:bool，字符串 "false" 应解析为 False
  - timeout_seconds 非法值回落 120
  - workon.capture.scan_directory(dir, id, name, tags, entry, overwrite=False) -> dict
  - 存储仅 sqlite3：record_run / list_runs 往返
"""
from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from workon.config import settings
from workon.models import validate_manifest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@contextmanager
def _temp_settings():
    """把数据目录临时指向 tempfile，避免污染项目 data/ 并隔离历史记录。"""
    old_data = settings.data_dir
    old_db = settings.db_path
    old_runs = settings.run_root
    with tempfile.TemporaryDirectory(prefix="workon-v2-test-") as tmp:
        base = Path(tmp)
        settings.data_dir = base
        settings.db_path = base / "workon.db"
        settings.run_root = base / "runs"
        settings.ensure_dirs()
        try:
            yield base
        finally:
            settings.data_dir = old_data
            settings.db_path = old_db
            settings.run_root = old_runs


def _base_manifest(**overrides):
    raw = {
        "id": "v2-skill",
        "name": "v2 测试技能",
        "entry": {"command": "python", "args": ["run.py"]},
        "inputs": [],
        "outputs": [],
        "params": [],
    }
    raw.update(overrides)
    return raw


class TestManifestV2(unittest.TestCase):
    """1) 新类型与 multiple 解析；2) timeout 回落。"""

    def test_accepts_new_types_and_multiple(self):
        raw = _base_manifest(
            inputs=[
                {"name": "payload", "type": "json", "multiple": True},
                {"name": "photo", "type": "image", "multiple": "false"},
                {"name": "folder", "type": "dir", "multiple": True},
            ],
            outputs=[
                {"name": "result", "type": "json", "multiple": False},
                {"name": "files", "type": "file", "multiple": True},
                {"name": "tree", "type": "dir"},
            ],
        )
        skill = validate_manifest(raw, PROJECT_ROOT / "skills", str(PROJECT_ROOT / "skills"))

        inputs = {f["name"]: f for f in skill.inputs}
        self.assertIs(inputs["payload"]["multiple"], True)
        self.assertIs(inputs["photo"]["multiple"], False, '字符串 "false" 应解析为 False')
        self.assertIs(inputs["folder"]["multiple"], True)

        outputs = {f["name"]: f for f in skill.outputs}
        self.assertIs(outputs["result"]["multiple"], False)
        self.assertIs(outputs["files"]["multiple"], True)

    def test_timeout_invalid_falls_back_to_120(self):
        skill = validate_manifest(
            _base_manifest(timeout_seconds="not-a-number"),
            PROJECT_ROOT / "skills",
            str(PROJECT_ROOT / "skills"),
        )
        self.assertEqual(skill.timeout_seconds, 120)

    def test_timeout_valid_is_kept(self):
        skill = validate_manifest(
            _base_manifest(timeout_seconds=45),
            PROJECT_ROOT / "skills",
            str(PROJECT_ROOT / "skills"),
        )
        self.assertEqual(skill.timeout_seconds, 45)


class TestCaptureV2(unittest.TestCase):
    """3) scan_directory 为含 run.py 的目录生成合法 manifest。"""

    def test_scan_directory_generates_valid_manifest(self):
        from workon.capture import scan_directory

        with tempfile.TemporaryDirectory(prefix="workon-capture-") as tmp:
            target = Path(tmp)
            (target / "run.py").write_text("print('ok')\n", encoding="utf-8")

            manifest = scan_directory(
                str(target),
                id="scanned-skill",
                name="Scanned Skill",
                tags=["auto", "test"],
                entry={"command": "python", "args": ["run.py"]},
            )

            self.assertIsInstance(manifest, dict)
            self.assertEqual(manifest.get("id"), "scanned-skill")
            skill = validate_manifest(manifest, target, str(target))
            self.assertEqual(skill.id, "scanned-skill")
            self.assertEqual(skill.entry.get("command"), "python")


class TestStorageSqlite(unittest.TestCase):
    """4) 仅 sqlite3：record_run / list_runs 往返。"""

    def test_record_and_list_roundtrip(self):
        from workon.storage import get_run, list_runs, record_run

        with _temp_settings():
            record_run(
                run_id="roundtrip-001",
                skill_id="v2-skill",
                skill_name="v2 测试",
                status="success",
                duration_ms=12,
                inputs={"text": "hello", "n": 3},
                params={"upper": True},
                outputs={"stdout": "HELLO\n", "returncode": 0},
                error="",
            )
            rows = list_runs(limit=5)
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["run_id"], "roundtrip-001")
            self.assertEqual(row["skill_id"], "v2-skill")
            self.assertEqual(row["status"], "success")
            self.assertEqual(row["inputs"]["text"], "hello")
            self.assertEqual(row["outputs"]["stdout"], "HELLO\n")

            detail = get_run("roundtrip-001")
            self.assertIsNotNone(detail)
            self.assertEqual(detail["params"]["upper"], True)

            filtered = list_runs(skill_id="v2-skill")
            self.assertEqual(len(filtered), 1)
            self.assertEqual(list_runs(skill_id="other"), [])


class TestTextEchoInvoke(unittest.TestCase):
    """5) text-echo 经 runner.invoke 返回 success 且文本输出正确。"""

    def test_text_echo_invoke(self):
        from workon.runner import invoke

        manifest_path = PROJECT_ROOT / "skills" / "text-echo" / "manifest.json"
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        skill = validate_manifest(raw, manifest_path.parent, str(PROJECT_ROOT / "skills"))

        with _temp_settings():
            result = invoke(skill, {"text": "hello"}, {"upper": True})

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["outputs"]["stdout"], "HELLO\n")
        self.assertEqual(result["outputs"]["returncode"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

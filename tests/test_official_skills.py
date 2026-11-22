import json
import unittest
from pathlib import Path

from workon.config import OFFICIAL_SKILLS_DIR
from workon.models import validate_manifest


class OfficialSkillsTest(unittest.TestCase):
    """官方能力回归：目录齐全、manifest 契约合法、纯标准库、run.py 非交互入口在位。"""

    def test_official_skills_valid(self):
        dirs = sorted(p for p in OFFICIAL_SKILLS_DIR.iterdir() if p.is_dir())
        self.assertEqual(len(dirs), 1, "官方技能必须恰好 1 个（仅 pdf-tool），不允许新增或删除")
        ids = set()
        for skill_dir in dirs:
            manifest = skill_dir / "manifest.json"
            raw = json.loads(manifest.read_text(encoding="utf-8"))
            skill = validate_manifest(raw, manifest, str(skill_dir))
            ids.add(skill.id)
            self.assertTrue(raw.get("official"), skill.id)
            self.assertEqual(raw.get("dependencies"), [], skill.id + " 必须纯标准库")
            self.assertTrue((skill_dir / "run.py").is_file(), skill.id + " 缺 run.py")
            self.assertTrue((skill_dir / "README.md").is_file(), skill.id + " 缺 README")
        self.assertEqual(
            ids,
            {"pdf-tool"},
            "官方技能 id 集合是对外契约，仅保留 pdf-tool，不能增删或改名",
        )


if __name__ == "__main__":
    unittest.main()

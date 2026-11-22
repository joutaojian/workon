# coding: utf-8
"""技能发现：扫描内置 skills/ 与外部目录中的 manifest.json。"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from .config import settings
from .models import ManifestError, Skill, validate_manifest

logger = logging.getLogger(__name__)


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
        self.errors: list[str] = []
        self.reload()

    def reload(self) -> dict[str, Skill]:
        skills: dict[str, Skill] = {}
        errors: list[str] = []
        for root in settings.skill_dirs:
            base = Path(root)
            if not base.exists():
                errors.append(f"技能目录不存在: {base}")
                continue
            if not base.is_dir():
                errors.append(f"技能目录不是文件夹: {base}")
                continue
            candidates = [base]
            candidates.extend(sorted(p for p in base.iterdir() if p.is_dir()))
            for candidate in candidates:
                manifest_path = candidate / "manifest.json"
                if not manifest_path.is_file():
                    continue
                try:
                    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
                    skill = validate_manifest(raw, candidate.resolve(), str(base))
                except (OSError, ValueError, ManifestError) as exc:
                    errors.append(f"{manifest_path}: {exc}")
                    continue
                if skill.id in skills:
                    errors.append(f"技能 id 重复，已跳过: {skill.id} ({candidate})")
                    continue
                skills[skill.id] = skill
        self._skills = skills
        self.errors = errors
        for err in errors:
            logger.warning("[skill-registry] %s", err)
        return skills

    def list(self, tag: str | None = None, query: str | None = None) -> list[Skill]:
        items = list(self._skills.values())
        if tag:
            items = [s for s in items if tag in s.tags]
        if query:
            q = query.lower()
            items = [
                s
                for s in items
                if q in s.id.lower() or q in s.name.lower() or q in s.description.lower()
                or any(q in t.lower() for t in s.tags)
            ]
        return sorted(items, key=lambda s: s.id)

    def tags(self) -> list[str]:
        return sorted({t for s in self._skills.values() for t in s.tags})

    def get(self, skill_id: str) -> Skill | None:
        return self._skills.get(skill_id)

    def all_ids(self) -> list[str]:
        return sorted(self._skills)


registry = SkillRegistry()

# coding: utf-8
"""全局配置：全部来自环境变量，敏感信息不落代码库。

v0.2 契约：
  - 存储仅本地 SQLite（sqlite_only=True；DB 文件恒为 data_dir 下的本地文件），
    任何试图经环境变量指定外部数据库的设置一律忽略。
  - INPUT/OUTPUT 类型集合由 workon.models 定义并校验：
    text / file / docx / xlsx / json / image / dir（本模块不重复声明，避免双源失配）。
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

#: 内置示例技能所在目录。pip 安装后它位于 site-packages 里（随包分发的只有
#: workon/skills/ 下的示例），此时没有顶层 skills/ 目录，不能当成「配置错误」报错。
PACKAGE_SKILLS_DIR = Path(__file__).resolve().parent / "skills"
#: 官方内置能力目录（WPS 付费级 PDF 合并/拆分等）。与普通用户技能分开，
#: 不放入 skill_dirs[0]，避免被 skill save 覆盖；始终追加且不可从配置移除。
OFFICIAL_SKILLS_DIR = Path(__file__).resolve().parent / "official_skills"


def _builtin_skill_dir() -> str:
    """内置技能目录：优先仓库根的 skills/，pip 安装后回落到包内 skills/。"""
    for candidate in (PROJECT_ROOT / "skills", PACKAGE_SKILLS_DIR):
        try:
            if candidate.is_dir():
                return str(candidate.resolve())
        except OSError:
            continue
    return str((PROJECT_ROOT / "skills").resolve())

# v0.2：存储后端固定为本地 SQLite，不接受任何外部数据库配置。
SQLITE_ONLY = True
DB_FILENAME = "workon.db"
# 下列环境变量即使被设置也不参与 db_path 计算；此处仅作审计/文档标注，代码从不读取它们。
IGNORED_DB_ENV_VARS = ("WORKON_DB_PATH", "WORKON_DATABASE_URL", "DATABASE_URL")


def load_dotenv(path: Path | None = None) -> None:
    """轻量加载 .env 到环境变量（不覆盖已显式设置的值）。"""
    path = path or (PROJECT_ROOT / ".env")
    if not path.is_file():
        return
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)
    except OSError:
        pass


def env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    value = os.environ.get(name, "")
    parts = [p.strip() for p in re.split(r"[;]", value) if p.strip()]
    return parts if parts else list(default or [])


def _resolve(path: str) -> Path:
    p = Path(path).expanduser()
    return p if p.is_absolute() else (PROJECT_ROOT / p).resolve()


class Settings:
    """运行时设置。技能目录可通过环境变量或 data/settings.json 配置。"""

    SETTINGS_FILE = PROJECT_ROOT / "data" / "settings.json"

    def __init__(self) -> None:
        self.data_dir = _resolve(os.environ.get("WORKON_DATA_DIR", "data"))
        # v0.2：DB 路径恒为 data_dir 下的本地 SQLite 文件；刻意不读取任何外部 DB env。
        self.sqlite_only = SQLITE_ONLY
        self.db_path = self.data_dir / DB_FILENAME
        self.run_root = self.data_dir / "runs"

        # 内置示例技能目录始终启用，再追加外部目录（私有 git 项目）
        builtin = _builtin_skill_dir()
        self._env_dirs = [str(_resolve(p)) for p in env_list("WORKON_SKILL_DIRS", [])]
        official = str(OFFICIAL_SKILLS_DIR.resolve())
        # 官方目录放在 builtin 之后、外部目录之前；始终注入，不可从配置移除。
        self.skill_dirs = list(dict.fromkeys([builtin, official] + self._env_dirs))

        # Web 访问密码：环境变量 > data/settings.json > 默认 "workon"。
        # 默认口令仅用于本地首次启动，登录后应在「设置」中修改。
        self._password_env = os.environ.get("WORKON_PASSWORD")
        self.password = self._password_env or "workon"

        # Flask session 签名密钥：持久化到 data/secret.key，重启后会话不失效。
        self.secret_key = self._load_or_create_secret()

        self.host = os.environ.get("WORKON_HOST", "0.0.0.0")
        self.port = env_int("WORKON_PORT", 8080)
        self.debug = env_bool("WORKON_DEBUG", False)
        self.max_upload_mb = env_int("WORKON_MAX_UPLOAD_MB", 50)
        self.default_timeout = DEFAULT_TIMEOUT
        self.allowed_commands = env_list(
            "WORKON_ALLOWED_COMMANDS",
            ["python", "python3", "node", "bash", "sh", "powershell", "pwsh"],
        )

        self._load_file_settings()

    def _load_or_create_secret(self) -> str:
        """加载或创建 Web session 签名密钥，持久化到 data/secret.key。

        这样服务重启后已登录会话不会失效；文件权限尽力收窄到仅当前用户可读。
        """
        import secrets

        secret_file = self.data_dir / "secret.key"
        try:
            if secret_file.is_file():
                value = secret_file.read_text(encoding="utf-8").strip()
                if value:
                    return value
        except OSError:
            pass
        value = secrets.token_hex(32)
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            secret_file.write_text(value, encoding="utf-8")
            try:
                secret_file.chmod(0o600)
            except OSError:
                pass
        except OSError:
            pass
        return value

    def _rebuild_dirs(self, configured: list[str]) -> None:
        """重建技能目录列表：始终保留内置与官方目录，再合并配置中的外部目录。"""
        builtin = _builtin_skill_dir()
        official = str(OFFICIAL_SKILLS_DIR.resolve())
        extra = [
            str(_resolve(p))
            for p in configured
            if str(_resolve(p)) not in {builtin, official}
        ]
        self.skill_dirs = list(dict.fromkeys([builtin, official] + extra))

    def _load_file_settings(self) -> None:
        """data/settings.json 可追加外部技能目录（不入库）。"""
        if not self.SETTINGS_FILE.exists():
            return
        try:
            data = json.loads(self.SETTINGS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return
        for raw in data.get("skill_dirs", []):
            resolved = str(_resolve(str(raw)))
            if resolved not in self.skill_dirs:
                self.skill_dirs.append(resolved)
        # 密码：settings.json 中的值仅在环境变量未显式指定时生效
        if not self._password_env and isinstance(data.get("password"), str) and data["password"]:
            self.password = data["password"]

    def save(self, payload: dict) -> dict:
        current: dict = {}
        if self.SETTINGS_FILE.exists():
            try:
                current = json.loads(self.SETTINGS_FILE.read_text(encoding="utf-8"))
            except Exception:
                current = {}
        for key in ("skill_dirs",):
            if key in payload:
                # 只持久化非内置、非 env 注入的外部目录；内置与 env 目录始终由代码注入
                builtin = _builtin_skill_dir()
                env_dirs = set(self._env_dirs)
                current[key] = [
                    str(_resolve(str(p)))
                    for p in payload[key]
                    if str(_resolve(str(p))) != builtin and str(_resolve(str(p))) not in env_dirs
                ]
        # 密码可修改：环境变量显式指定时不允许从 Web 覆盖
        if "password" in payload and not self._password_env:
            value = str(payload["password"]).strip()
            if value:
                current["password"] = value
                self.password = value
        self.SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.SETTINGS_FILE.write_text(
            json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        # 重建内存目录：内置 + env + 文件配置，缺一不可
        self._rebuild_dirs(current.get("skill_dirs", []))
        builtin = _builtin_skill_dir()
        for extra in self._env_dirs:
            if extra != builtin and extra not in self.skill_dirs:
                self.skill_dirs.append(extra)
        self.skill_dirs = list(dict.fromkeys(self.skill_dirs))
        return self.public()

    def public(self) -> dict:
        return {
            "data_dir": str(self.data_dir),
            "sqlite_only": self.sqlite_only,
            "db_path": str(self.db_path),
            "skill_dirs": self.skill_dirs,
            "default_timeout": self.default_timeout,
            "max_upload_mb": self.max_upload_mb,
            "allowed_commands": self.allowed_commands,
        }

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.run_root.mkdir(parents=True, exist_ok=True)


# 先加载 .env（不覆盖已有环境变量），再实例化设置
load_dotenv()

#: 脚本执行默认超时（秒）。manifest 未声明 timeout_seconds 时回退到此值；
#: 集中一处，避免魔数散落（core-audit）。须在 load_dotenv() 之后求值，
#: 才能读取 .env 里的 WORKON_TIMEOUT。
DEFAULT_TIMEOUT = env_int("WORKON_TIMEOUT", 120)

settings = Settings()


def python_command() -> str:
    return sys.executable

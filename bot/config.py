"""Конфигурация бота из переменных окружения."""
import os
from pathlib import Path

_env_path = Path(__file__).resolve().parent.parent / ".env"
_env_alt = Path(__file__).resolve().parent.parent / "env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)
elif _env_alt.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_alt)

def _get_env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)

def _parse_admin_ids(value: str | None) -> list[int]:
    if not value or not value.strip():
        return []
    return [int(x.strip()) for x in value.split(",") if x.strip().isdigit()]

BOT_TOKEN = _get_env("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не задан в .env или env")

ADMIN_IDS = _parse_admin_ids(_get_env("ADMIN_IDS", ""))
DB_HOST = _get_env("DB_HOST", "localhost")
DB_PORT = int(_get_env("DB_PORT", "5432"))
DB_NAME = _get_env("DB_NAME", "stat_bot")
DB_USER = _get_env("DB_USER", "")
DB_PASSWORD = _get_env("DB_PASSWORD", "")

def get_database_url() -> str:
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

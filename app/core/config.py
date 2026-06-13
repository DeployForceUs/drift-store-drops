from dataclasses import dataclass
from functools import lru_cache
import os
from pathlib import Path


def load_env_file(path: str = ".env") -> None:
    """Load simple KEY=VALUE pairs from a local .env file if it exists."""

    env_path = Path(path)
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    app_name: str = os.getenv("APP_NAME", "Drift Store Drops")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./drift_store_drops.db")
    secret_key: str = os.getenv("SECRET_KEY", "change-me")

    store_name: str = os.getenv("STORE_NAME", "Drift Store")
    store_phone: str = os.getenv("STORE_PHONE", "+1-555-555-5555")
    store_address: str = os.getenv("STORE_ADDRESS", "123 Main St, Your City, ST")
    store_timezone: str = os.getenv("STORE_TIMEZONE", "America/New_York")
    store_open_time: str = os.getenv("STORE_OPEN_TIME", "10:00")
    store_close_time: str = os.getenv("STORE_CLOSE_TIME", "18:00")
    store_map_url: str = os.getenv("STORE_MAP_URL", "https://www.google.com/maps")

    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_alert_chat_id: str = os.getenv("TELEGRAM_ALERT_CHAT_ID", "")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "change-me")
    owner_secret: str = os.getenv("OWNER_SECRET", "change-me-owner-secret")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings so the app does not reload them on each request."""

    return Settings()


settings = get_settings()

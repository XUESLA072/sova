import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    avito_search_url: str
    telegram_bot_token: str
    telegram_chat_id: str
    user_data_dir: str = './user_data'
    sqlite_db_path: str = './listings.db'
    poll_interval_seconds: int = 60
    headless: bool = True
    timeout_ms: int = 45000


def _to_bool(value: str, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'y', 'on'}


def load_config() -> Config:
    avito_search_url = os.getenv('AVITO_SEARCH_URL', '').strip()
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
    telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID', '').strip()

    missing = []
    if not avito_search_url:
        missing.append('AVITO_SEARCH_URL')
    if not telegram_bot_token:
        missing.append('TELEGRAM_BOT_TOKEN')
    if not telegram_chat_id:
        missing.append('TELEGRAM_CHAT_ID')

    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    return Config(
        avito_search_url=avito_search_url,
        telegram_bot_token=telegram_bot_token,
        telegram_chat_id=telegram_chat_id,
        user_data_dir=os.getenv('USER_DATA_DIR', './user_data').strip(),
        sqlite_db_path=os.getenv('SQLITE_DB_PATH', './listings.db').strip(),
        poll_interval_seconds=int(os.getenv('POLL_INTERVAL_SECONDS', '60')),
        headless=_to_bool(os.getenv('HEADLESS'), default=True),
        timeout_ms=int(os.getenv('PLAYWRIGHT_TIMEOUT_MS', '45000')),
    )

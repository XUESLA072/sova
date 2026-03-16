# Avito → Telegram Monitor

Python project for monitoring new Avito listings and sending notifications to Telegram.

## Features

- Uses **Playwright** with a **persistent browser profile**.
- Monitors a configured Avito search URL.
- Stores seen listings in **SQLite** to avoid duplicates.
- On first run sends the latest **50** listings.
- On subsequent runs sends **only new** listings.
- Extracts:
  - title
  - full apartment price
  - address/location
  - floor
  - square meters
  - publication time
  - link
- Normalizes URLs to reduce duplicate notifications.
- Graceful shutdown on `Ctrl+C`.
- Console logging for activity.

## Project structure

- `main.py` — orchestration loop
- `parser.py` — Avito scraping and parsing
- `telegram_bot.py` — Telegram Bot API client
- `storage.py` — SQLite storage and deduplication
- `config.py` — environment-based configuration
- `requirements.txt`
- `README.md`

## Setup

1. Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

2. Configure environment variables:

```bash
export AVITO_SEARCH_URL="https://www.avito.ru/..."
export TELEGRAM_BOT_TOKEN="123456:ABC..."
export TELEGRAM_CHAT_ID="123456789"

# Optional
export USER_DATA_DIR="./user_data"
export SQLITE_DB_PATH="./listings.db"
export POLL_INTERVAL_SECONDS="60"
export HEADLESS="true"
export PLAYWRIGHT_TIMEOUT_MS="45000"
```

3. Run:

```bash
python main.py
```

## Notes

- Persistent profile is stored in `USER_DATA_DIR`, allowing cookies/session reuse.
- If Avito changes markup, selectors in `parser.py` may need adjustment.
- URL normalization keeps canonical path and only essential query params to reduce duplicates.

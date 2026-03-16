import signal
import time
from typing import List

from config import load_config
from parser import AvitoParser, Listing
from storage import ListingRecord, SQLiteStorage
from telegram_bot import TelegramNotifier


def to_record(item: Listing) -> ListingRecord:
    return ListingRecord(
        fingerprint=item.fingerprint,
        normalized_url=item.normalized_url,
        title=item.title,
        price=item.price,
        address=item.address,
        floor=item.floor,
        area_sqm=item.area_sqm,
        published_at=item.published_at,
        link=item.link,
    )


def send_and_store(notifier: TelegramNotifier, storage: SQLiteStorage, listings: List[Listing]) -> int:
    sent = 0
    for item in listings:
        if storage.is_seen(item.fingerprint):
            continue

        ok = notifier.send_listing(item.to_dict())
        if ok:
            storage.mark_seen(to_record(item))
            sent += 1
            print(f'[main] Sent: {item.title} | {item.price}')
        else:
            print(f'[main] Failed to send message for: {item.link}')

        time.sleep(0.3)

    return sent


def main() -> None:
    config = load_config()
    storage = SQLiteStorage(config.sqlite_db_path)
    notifier = TelegramNotifier(config.telegram_bot_token, config.telegram_chat_id)
    parser = AvitoParser(
        user_data_dir=config.user_data_dir,
        headless=config.headless,
        timeout_ms=config.timeout_ms,
    )

    stop_requested = False

    def _handle_stop(signum, frame):  # noqa: ARG001
        nonlocal stop_requested
        print('\n[main] Stop signal received. Shutting down gracefully...')
        stop_requested = True

    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)

    parser.start()

    try:
        first_cycle = True
        while not stop_requested:
            print('[main] Polling Avito...')
            listings = parser.fetch_listings(config.avito_search_url, limit=120)

            if first_cycle:
                latest_50 = listings[:50]
                print(f'[main] First run: sending latest {len(latest_50)} listings')
                sent = send_and_store(notifier, storage, latest_50)
                print(f'[main] First run complete. Sent {sent} listings.')
                first_cycle = False
            else:
                fresh = [x for x in listings if not storage.is_seen(x.fingerprint)]
                print(f'[main] Found {len(fresh)} new listings')
                sent = send_and_store(notifier, storage, fresh)
                print(f'[main] Sent {sent} new listings')

            if stop_requested:
                break

            print(f'[main] Sleeping for {config.poll_interval_seconds}s...')
            for _ in range(config.poll_interval_seconds):
                if stop_requested:
                    break
                time.sleep(1)

    finally:
        parser.close()
        storage.close()
        print('[main] Shutdown complete.')


if __name__ == '__main__':
    main()

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


@dataclass
class ListingRecord:
    fingerprint: str
    normalized_url: str
    title: str
    price: str
    address: str
    floor: str
    area_sqm: str
    published_at: str
    link: str


class SQLiteStorage:
    def __init__(self, db_path: str) -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.execute('PRAGMA journal_mode=WAL;')
        self.conn.execute('PRAGMA synchronous=NORMAL;')
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
            '''
            CREATE TABLE IF NOT EXISTS seen_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT UNIQUE NOT NULL,
                normalized_url TEXT NOT NULL,
                title TEXT,
                price TEXT,
                address TEXT,
                floor TEXT,
                area_sqm TEXT,
                published_at TEXT,
                link TEXT,
                created_at TEXT NOT NULL
            )
            '''
        )
        self.conn.execute(
            'CREATE INDEX IF NOT EXISTS idx_seen_listings_normalized_url ON seen_listings(normalized_url)'
        )
        self.conn.commit()

    def is_seen(self, fingerprint: str) -> bool:
        row = self.conn.execute(
            'SELECT 1 FROM seen_listings WHERE fingerprint = ? LIMIT 1',
            (fingerprint,),
        ).fetchone()
        return row is not None

    def mark_seen(self, listing: ListingRecord) -> bool:
        try:
            self.conn.execute(
                '''
                INSERT INTO seen_listings (
                    fingerprint, normalized_url, title, price, address, floor, area_sqm, published_at, link, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    listing.fingerprint,
                    listing.normalized_url,
                    listing.title,
                    listing.price,
                    listing.address,
                    listing.floor,
                    listing.area_sqm,
                    listing.published_at,
                    listing.link,
                    datetime.utcnow().isoformat(timespec='seconds') + 'Z',
                ),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def mark_seen_many(self, listings: Iterable[ListingRecord]) -> int:
        inserted = 0
        for listing in listings:
            if self.mark_seen(listing):
                inserted += 1
        return inserted

    def close(self) -> None:
        self.conn.close()

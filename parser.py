import hashlib
import re
from dataclasses import dataclass, asdict
from typing import List
from urllib.parse import urljoin, urlparse, urlunparse, parse_qsl, urlencode

from playwright.sync_api import BrowserContext, Page, sync_playwright


@dataclass
class Listing:
    title: str
    price: str
    address: str
    floor: str
    area_sqm: str
    published_at: str
    link: str
    normalized_url: str
    fingerprint: str

    def to_dict(self) -> dict:
        return asdict(self)


class AvitoParser:
    def __init__(self, user_data_dir: str, headless: bool = True, timeout_ms: int = 45000) -> None:
        self.user_data_dir = user_data_dir
        self.headless = headless
        self.timeout_ms = timeout_ms
        self._playwright = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def start(self) -> None:
        print('[parser] Starting Playwright with persistent profile...')
        self._playwright = sync_playwright().start()
        self.context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=self.headless,
            viewport={'width': 1366, 'height': 900},
        )
        self.context.set_default_timeout(self.timeout_ms)
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()

    def close(self) -> None:
        print('[parser] Closing Playwright...')
        if self.context:
            self.context.close()
        if self._playwright:
            self._playwright.stop()

    @staticmethod
    def normalize_url(raw_url: str) -> str:
        parsed = urlparse(raw_url)
        query_pairs = parse_qsl(parsed.query, keep_blank_values=False)
        allowed_params = {'p'}
        filtered = [(k, v) for k, v in query_pairs if k in allowed_params]
        clean_query = urlencode(filtered)
        return urlunparse((
            parsed.scheme or 'https',
            parsed.netloc,
            parsed.path.rstrip('/'),
            '',
            clean_query,
            '',
        ))

    @staticmethod
    def _extract_floor_and_area(text_blob: str) -> tuple[str, str]:
        floor = 'N/A'
        area = 'N/A'

        floor_match = re.search(r'(\d+)\s*/\s*(\d+)\s*эт', text_blob, re.IGNORECASE)
        if floor_match:
            floor = f"{floor_match.group(1)}/{floor_match.group(2)}"
        else:
            floor_match_alt = re.search(r'Этаж\s*[:\-]?\s*([^,\n]+)', text_blob, re.IGNORECASE)
            if floor_match_alt:
                floor = floor_match_alt.group(1).strip()

        area_match = re.search(r'(\d+[\.,]?\d*)\s*м²', text_blob, re.IGNORECASE)
        if area_match:
            area = area_match.group(1).replace(',', '.') + ' м²'

        return floor, area

    @staticmethod
    def _extract_published_time(text_blob: str) -> str:
        patterns = [
            r'Сегодня\s+в\s+\d{1,2}:\d{2}',
            r'Вчера\s+в\s+\d{1,2}:\d{2}',
            r'\d{1,2}\s+[а-яА-Я]+\s+в\s+\d{1,2}:\d{2}',
            r'\d{1,2}:\d{2}',
        ]
        for pattern in patterns:
            m = re.search(pattern, text_blob, re.IGNORECASE)
            if m:
                return m.group(0)
        return 'N/A'

    @staticmethod
    def _listing_fingerprint(normalized_url: str, title: str, price: str) -> str:
        payload = f'{normalized_url}|{title.strip()}|{price.strip()}'
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

    def fetch_listings(self, search_url: str, limit: int = 100) -> List[Listing]:
        if not self.page:
            raise RuntimeError('Parser is not started. Call start() first.')

        print(f'[parser] Opening search URL: {search_url}')
        self.page.goto(search_url, wait_until='domcontentloaded')
        self.page.wait_for_timeout(2000)

        cards = self.page.locator('article[data-marker="item"], div[data-marker="item"]')
        count = cards.count()
        print(f'[parser] Found {count} listing cards')

        listings: List[Listing] = []
        for i in range(min(count, limit)):
            card = cards.nth(i)

            link_elem = card.locator('a[itemprop="url"]').first
            if link_elem.count() == 0:
                link_elem = card.locator('a[href*="/kvartiry/"]').first
            if link_elem.count() == 0:
                continue

            href = link_elem.get_attribute('href') or ''
            full_link = urljoin('https://www.avito.ru', href)
            normalized = self.normalize_url(full_link)

            title = (link_elem.inner_text() or '').strip() or 'N/A'

            price_text = 'N/A'
            price_locators = [
                'meta[itemprop="price"]',
                '[data-marker="item-price"]',
                '[data-marker="item-price"] span',
            ]
            for sel in price_locators:
                candidate = card.locator(sel).first
                if candidate.count() > 0:
                    if sel.startswith('meta'):
                        content = candidate.get_attribute('content')
                        if content:
                            price_text = f'{content} ₽'
                            break
                    txt = (candidate.inner_text() or '').strip()
                    if txt:
                        price_text = txt
                        break

            address = 'N/A'
            addr_locators = ['[data-marker="item-address"]', '[itemprop="address"]']
            for sel in addr_locators:
                candidate = card.locator(sel).first
                if candidate.count() > 0:
                    txt = (candidate.inner_text() or '').strip()
                    if txt:
                        address = txt
                        break

            text_blob = card.inner_text()
            floor, area = self._extract_floor_and_area(text_blob)
            published_at = self._extract_published_time(text_blob)

            fingerprint = self._listing_fingerprint(normalized, title, price_text)
            listings.append(
                Listing(
                    title=title,
                    price=price_text,
                    address=address,
                    floor=floor,
                    area_sqm=area,
                    published_at=published_at,
                    link=full_link,
                    normalized_url=normalized,
                    fingerprint=fingerprint,
                )
            )

        print(f'[parser] Parsed {len(listings)} listings')
        return listings

import requests


class TelegramNotifier:
    def __init__(self, token: str, chat_id: str) -> None:
        self.token = token
        self.chat_id = chat_id
        self.base_url = f'https://api.telegram.org/bot{token}'

    @staticmethod
    def _escape_markdown(text: str) -> str:
        if text is None:
            return ''
        chars = r'_[]()~`>#+-=|{}.!'
        result = text
        for ch in chars:
            result = result.replace(ch, f'\\{ch}')
        return result

    def format_listing_message(self, listing: dict) -> str:
        title = self._escape_markdown(listing.get('title', 'N/A'))
        price = self._escape_markdown(listing.get('price', 'N/A'))
        address = self._escape_markdown(listing.get('address', 'N/A'))
        floor = self._escape_markdown(listing.get('floor', 'N/A'))
        area = self._escape_markdown(listing.get('area_sqm', 'N/A'))
        published = self._escape_markdown(listing.get('published_at', 'N/A'))
        link = listing.get('link', '')

        return (
            f"🏠 *{title}*\n"
            f"💰 Цена: *{price}*\n"
            f"📍 Адрес: {address}\n"
            f"🏢 Этаж: {floor}\n"
            f"📐 Площадь: {area}\n"
            f"🕒 Время публикации: {published}\n"
            f"🔗 [Открыть объявление]({link})"
        )

    def send_message(self, text: str) -> bool:
        try:
            response = requests.post(
                f'{self.base_url}/sendMessage',
                json={
                    'chat_id': self.chat_id,
                    'text': text,
                    'parse_mode': 'MarkdownV2',
                    'disable_web_page_preview': False,
                },
                timeout=20,
            )
            if response.status_code != 200:
                print(f'[telegram] Failed to send message: {response.status_code} {response.text}')
                return False
            return True
        except requests.RequestException as exc:
            print(f'[telegram] Network error while sending message: {exc}')
            return False

    def send_listing(self, listing: dict) -> bool:
        return self.send_message(self.format_listing_message(listing))

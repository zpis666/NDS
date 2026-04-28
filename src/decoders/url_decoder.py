import re
from urllib.parse import unquote


class UrlDecoder:
    @staticmethod
    def is_url_encoded(text: str) -> bool:
        if not text:
            return False

        text = str(text).strip()

        if '%' not in text:
            return False

        if re.search(r'%[0-9A-Fa-f]{2}', text):
            return True

        return False

    @staticmethod
    def decode(text: str) -> str:
        if not text:
            return text

        text = str(text).strip()

        try:
            return unquote(text, encoding='utf-8')
        except Exception:
            try:
                return unquote(text, encoding='latin-1')
            except Exception:
                return text

    @staticmethod
    def try_decode(text: str) -> tuple:
        if not UrlDecoder.is_url_encoded(text):
            return False, text

        try:
            decoded = UrlDecoder.decode(text)
            return True, decoded
        except Exception:
            return False, text

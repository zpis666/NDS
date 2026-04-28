import base64
import re


class Base64Decoder:
    @staticmethod
    def is_base64(text: str) -> bool:
        if not text:
            return False

        text = str(text).strip()

        if not re.match(r'^[A-Za-z0-9+/]+={0,2}$', text):
            return False

        if len(text) < 4:
            return False

        if len(text) % 4 != 0:
            return False

        return True

    @staticmethod
    def decode(text: str) -> str:
        if not text:
            return text

        text = str(text).strip()

        try:
            decoded_bytes = base64.b64decode(text)
            return decoded_bytes.decode('utf-8')
        except Exception:
            try:
                decoded_bytes = base64.b64decode(text)
                return decoded_bytes.decode('latin-1')
            except Exception:
                return text

    @staticmethod
    def try_decode(text: str) -> tuple:
        if not Base64Decoder.is_base64(text):
            return False, text

        try:
            decoded = Base64Decoder.decode(text)
            return True, decoded
        except Exception:
            return False, text

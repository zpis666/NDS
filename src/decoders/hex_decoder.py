import re


class HexDecoder:
    @staticmethod
    def is_hex(text: str) -> bool:
        if not text:
            return False

        text = str(text).strip()

        if text.startswith('0x') or text.startswith('0X'):
            text = text[2:]

        if not re.match(r'^[0-9A-Fa-f]+$', text):
            return False

        if len(text) < 2 or len(text) % 2 != 0:
            return False

        return True

    @staticmethod
    def decode(text: str) -> str:
        if not text:
            return text

        text = str(text).strip()

        if text.startswith('0x') or text.startswith('0X'):
            text = text[2:]

        try:
            decoded_bytes = bytes.fromhex(text)
            return decoded_bytes.decode('utf-8')
        except Exception:
            try:
                decoded_bytes = bytes.fromhex(text)
                return decoded_bytes.decode('latin-1')
            except Exception:
                return text

    @staticmethod
    def try_decode(text: str) -> tuple:
        if not HexDecoder.is_hex(text):
            return False, text

        try:
            decoded = HexDecoder.decode(text)
            if decoded and all(32 <= ord(c) < 127 or c in '\n\r\t' or '\u4e00' <= c <= '\u9fff' for c in decoded):
                return True, decoded
            return False, text
        except Exception:
            return False, text

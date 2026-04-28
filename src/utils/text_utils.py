import re
import unicodedata


class TextUtils:
    @staticmethod
    def strip_whitespace(text):
        if not text:
            return text
        return text.strip()

    @staticmethod
    def fullwidth_to_halfwidth(text):
        if not text:
            return text
        result = []
        for char in text:
            code = ord(char)
            if code == 0x3000:
                code = 0x0020
            elif 0xFF01 <= code <= 0xFF5E:
                code -= 0xFEE0
            result.append(chr(code))
        return ''.join(result)

    @staticmethod
    def normalize_text(text):
        if not text:
            return text
        text = TextUtils.fullwidth_to_halfwidth(text)
        text = TextUtils.strip_whitespace(text)
        text = unicodedata.normalize('NFKC', text)
        return text

    @staticmethod
    def is_noise_value(value):
        if not value:
            return True
        if re.match(r'^N/A_\d+$', str(value)):
            return True
        if re.match(r'^[0]+$', str(value)):
            return True
        if re.match(r'^[1]+$', str(value)):
            return True
        return False

    @staticmethod
    def clean_extracted_value(value):
        if not value:
            return value
        value = str(value).strip()
        value = value.replace('\n', '').replace('\r', '')
        value = value.replace('\t', ' ')
        value = re.sub(r'\s+', ' ', value)
        return value.strip()

    @staticmethod
    def is_valid_chinese_name(name):
        if not name:
            return False
        if len(name) < 2 or len(name) > 4:
            return False
        if not re.match(r'^[\u4e00-\u9fa5]+$', name):
            return False
        return True

    @staticmethod
    def is_valid_phone(phone):
        if not phone:
            return False
        phone = re.sub(r'[\s\-]', '', phone)
        return bool(re.match(r'^1[3-9]\d{9}$', phone))

    @staticmethod
    def is_valid_id_card(id_card):
        if not id_card:
            return False
        id_card = id_card.strip()
        if len(id_card) != 18:
            return False
        return bool(re.match(r'^\d{17}[\dX]$', id_card))

    @staticmethod
    def is_valid_email(email):
        if not email:
            return False
        return bool(re.match(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$', email))

    @staticmethod
    def is_valid_bank_card(bank_card):
        if not bank_card:
            return False
        bank_card = re.sub(r'\s', '', bank_card)
        return bool(re.match(r'^\d{16,19}$', bank_card))

    @staticmethod
    def is_valid_ip(ip):
        if not ip:
            return False
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        for part in parts:
            try:
                num = int(part)
                if num < 0 or num > 255:
                    return False
            except ValueError:
                return False
        return True

    @staticmethod
    def is_valid_address(address):
        if not address:
            return False
        if len(address) < 10:
            return False
        return True

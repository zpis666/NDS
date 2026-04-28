import re


class TextEnhancer:
    CHAR_REPLACEMENTS = {
        'O': '0', 'o': '0',
        'I': '1', 'l': '1',
        'S': '5', 's': '5',
        'B': '8',
        'Z': '2',
    }

    @staticmethod
    def enhance(text: str) -> str:
        if not text:
            return text

        text = TextEnhancer._fix_line_breaks(text)
        text = TextEnhancer._remove_noise_chars(text)
        text = TextEnhancer._fix_common_errors(text)

        return text

    @staticmethod
    def enhance_for_id_card(text: str) -> str:
        if not text:
            return text

        text = TextEnhancer.enhance(text)
        text = TextEnhancer._fix_id_card_chars(text)

        return text

    @staticmethod
    def enhance_for_phone(text: str) -> str:
        if not text:
            return text

        text = TextEnhancer.enhance(text)
        text = TextEnhancer._fix_phone_chars(text)

        return text

    @staticmethod
    def _fix_line_breaks(text: str) -> str:
        text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)
        text = re.sub(r'(\d)\n(\d)', r'\1\2', text)
        return text

    @staticmethod
    def _remove_noise_chars(text: str) -> str:
        text = re.sub(r'[^\w\s\u4e00-\u9fa5.,;:!?@#$%^&*()\-+=/\\]', '', text)
        return text

    @staticmethod
    def _fix_common_errors(text: str) -> str:
        return text

    @staticmethod
    def _fix_id_card_chars(text: str) -> str:
        if re.match(r'^\d{17}[\dX]$', text):
            return text

        fixed = list(text)
        for i, char in enumerate(fixed):
            if char in TextEnhancer.CHAR_REPLACEMENTS:
                if i < 17:
                    fixed[i] = TextEnhancer.CHAR_REPLACEMENTS[char]

        return ''.join(fixed)

    @staticmethod
    def _fix_phone_chars(text: str) -> str:
        if re.match(r'^1[3-9]\d{9}$', text):
            return text

        fixed = list(text)
        for i, char in enumerate(fixed):
            if char in TextEnhancer.CHAR_REPLACEMENTS:
                fixed[i] = TextEnhancer.CHAR_REPLACEMENTS[char]

        return ''.join(fixed)

    @staticmethod
    def merge_split_value(text: str, value_type: str) -> str:
        if not text:
            return text

        if value_type == 'ID_CARD':
            text = re.sub(r'(\d{6})\s+(\d{8})\s+(\d{3}[\dX])', r'\1\2\3', text)

        elif value_type == 'PHONE_NUMBER':
            text = re.sub(r'(\d{3})\s+(\d{4})\s+(\d{4})', r'\1\2\3', text)

        elif value_type == 'BANK_CARD':
            text = re.sub(r'(\d{4})\s+(\d{4})\s+(\d{4})\s+(\d{4})', r'\1\2\3\4', text)

        return text

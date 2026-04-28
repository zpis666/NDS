from typing import List
from models.candidate import Candidate
from utils.text_utils import TextUtils


class Normalizer:
    def __init__(self):
        self.text_utils = TextUtils()

    def normalize(self, candidates: List[Candidate]) -> List[Candidate]:
        normalized = []

        for candidate in candidates:
            candidate.extracted_value = self._normalize_value(
                candidate.extracted_value,
                candidate.sensitive_type
            )
            candidate.field_name = self.text_utils.strip_whitespace(candidate.field_name)
            candidate.table_name = self.text_utils.strip_whitespace(candidate.table_name)
            candidate.db_name = self.text_utils.strip_whitespace(candidate.db_name)

            normalized.append(candidate)

        return normalized

    def _normalize_value(self, value: str, sensitive_type: str) -> str:
        if not value:
            return value

        value = self.text_utils.strip_whitespace(value)
        value = self.text_utils.fullwidth_to_halfwidth(value)

        if sensitive_type == 'PHONE_NUMBER':
            value = self._normalize_phone(value)
        elif sensitive_type == 'ID_CARD':
            value = self._normalize_id_card(value)
        elif sensitive_type == 'BANK_CARD':
            value = self._normalize_bank_card(value)
        elif sensitive_type == 'EMAIL':
            value = self._normalize_email(value)
        elif sensitive_type == 'LICENSE_PLATE':
            value = self._normalize_license_plate(value)

        return value

    def _normalize_phone(self, phone: str) -> str:
        phone = phone.replace(' ', '').replace('-', '').replace('+86', '')
        return phone

    def _normalize_id_card(self, id_card: str) -> str:
        id_card = id_card.replace(' ', '').replace('-', '')
        return id_card

    def _normalize_bank_card(self, bank_card: str) -> str:
        bank_card = bank_card.replace(' ', '').replace('-', '')
        return bank_card

    def _normalize_email(self, email: str) -> str:
        email = email.replace(' ', '')
        return email

    def _normalize_license_plate(self, plate: str) -> str:
        plate = plate.replace(' ', '').upper()
        return plate

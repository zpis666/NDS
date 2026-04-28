from typing import List
from models.candidate import Candidate
from matchers.field_semantic import field_semantic_mapper


class SemanticCleaner:
    def __init__(self):
        self.mapper = field_semantic_mapper

        self.strict_mismatches = {
            'age': {'PHONE_NUMBER', 'EMAIL', 'ID_CARD', 'BANK_CARD'},
            'status': {'PHONE_NUMBER', 'EMAIL', 'ID_CARD', 'BANK_CARD'},
            'created_at': {'PHONE_NUMBER', 'EMAIL', 'ID_CARD', 'BANK_CARD'},
            'updated_at': {'PHONE_NUMBER', 'EMAIL', 'ID_CARD', 'BANK_CARD'},
        }

    def clean(self, candidates: List[Candidate]) -> List[Candidate]:
        result = []

        for candidate in candidates:
            if self._is_semantic_mismatch(candidate):
                continue

            if candidate.confidence < 0.05:
                continue

            result.append(candidate)

        return result

    def _is_semantic_mismatch(self, candidate: Candidate) -> bool:
        field_lower = candidate.field_name.lower()
        sensitive_type = candidate.sensitive_type

        if field_lower in self.strict_mismatches:
            if sensitive_type in self.strict_mismatches[field_lower]:
                return True

        return False

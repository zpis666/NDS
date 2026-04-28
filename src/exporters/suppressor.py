import re
from typing import List
from models.candidate import Candidate
from matchers.patterns import validate_sensitive_value


class NoiseFilter:
    NOISE_VALUES = {
        'test', 'demo', 'example', 'sample', 'null', 'none', 'undefined',
        'n/a', 'nan', 'nil', 'true', 'false', 'yes', 'no', 'pending',
        'active', 'inactive', 'enabled', 'disabled',
    }

    NOISE_PATTERNS = [
        re.compile(r'^\d{1,2}$'),
        re.compile(r'^[a-zA-Z]{1,3}$'),
        re.compile(r'^[0]+$'),
        re.compile(r'^[1]+$'),
        re.compile(r'^[#@!%^&*]+$'),
        re.compile(r'^[\u4e00-\u9fa5]{1}$'),
    ]

    def is_noise(self, value: str) -> bool:
        if not value or len(value.strip()) < 2:
            return True
        value = value.strip().lower()
        if value in self.NOISE_VALUES:
            return True
        for pattern in self.NOISE_PATTERNS:
            if pattern.match(value):
                return True
        return False


class TypeValidator:
    def validate(self, candidate: Candidate) -> bool:
        value = candidate.extracted_value
        sensitive_type = candidate.sensitive_type

        if not value or len(value.strip()) < 2:
            return False

        return validate_sensitive_value(sensitive_type, value)


class Suppressor:
    def __init__(self):
        self.noise_filter = NoiseFilter()
        self.type_validator = TypeValidator()

    def suppress(self, candidates: List[Candidate]) -> List[Candidate]:
        result = []
        for candidate in candidates:
            if self.noise_filter.is_noise(candidate.extracted_value):
                continue
            if not self.type_validator.validate(candidate):
                continue
            result.append(candidate)
        return result

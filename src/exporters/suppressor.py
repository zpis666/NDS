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
    ADDRESS_PROVINCE_PREFIX = re.compile(
        r'^(?:北京|上海|天津|重庆|河北|山西|辽宁|吉林|黑龙江|江苏|浙江|安徽|福建|江西|山东|河南|湖北|湖南|广东|海南|四川|贵州|云南|陕西|甘肃|青海|台湾|内蒙古|广西|西藏|宁夏|新疆)'
    )

    def __init__(self):
        self.noise_filter = NoiseFilter()
        self.type_validator = TypeValidator()

    def _should_suppress_by_context(self, candidate: Candidate) -> bool:
        # NDS V6: final boost re-adds validated full_address/home_address
        # structured addresses; do not suppress them globally here.
        if (
            candidate.data_form == 'binary_blob'
            and candidate.sensitive_type == 'HOUSING_FUND_NO'
            and re.match(r'^[A-Z]{2}0{6,}$', candidate.extracted_value)
        ):
            return True
        return False

    def suppress(self, candidates: List[Candidate]) -> List[Candidate]:
        result = []
        for candidate in candidates:
            if self._should_suppress_by_context(candidate):
                continue
            if self.noise_filter.is_noise(candidate.extracted_value):
                continue
            if not self.type_validator.validate(candidate):
                continue
            result.append(candidate)
        return result

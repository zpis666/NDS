import re
from typing import List, Tuple
from matchers.patterns import (
    SENSITIVE_PATTERNS, CHINESE_NAME_COMMON_WORDS, SENSITIVE_KEYWORDS,
    CHINESE_SURNAMES_SINGLE, CHINESE_SURNAMES_COMPOUND,
    validate_sensitive_value, is_chinese_name,
)


class SensitiveMatcher:
    def __init__(self):
        self.patterns = SENSITIVE_PATTERNS
        self.chinese_common_words = CHINESE_NAME_COMMON_WORDS
        self.field_type_map = self._build_field_type_map()

    def _build_field_type_map(self):
        mapping = {}
        for sensitive_type, keywords in SENSITIVE_KEYWORDS.items():
            for keyword in keywords:
                mapping[keyword.lower()] = sensitive_type
        return mapping

    def match_all(self, text: str) -> List[Tuple[str, str]]:
        if not text:
            return []

        results = []
        text_str = str(text)
        for sensitive_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = pattern.findall(text_str)
                for match in matches:
                    match = match.strip()
                    if not self._is_noise(match):
                        if sensitive_type == 'ADDRESS':
                            # 对 ADDRESS 类型进行额外验证
                            if not re.search(r'(?:省|市|区|县|镇|乡|路|街|道|号|室)', match):
                                continue
                            if len(match) < 6 or len(match) > 100:
                                continue
                            if re.search(r'(?:医院|学校|银行|保险|公司|政府|法院|公安局|派出所|居委会|街道办)', match):
                                continue
                            if re.search(r'(?:转入|转出|转入市|转出市)', match):
                                continue
                        if validate_sensitive_value(sensitive_type, match):
                            results.append((sensitive_type, match))

        return results

    def match_by_type(self, text: str, sensitive_type: str) -> List[str]:
        if not text:
            return []

        results = []
        text_str = str(text)
        patterns = self.patterns.get(sensitive_type, [])
        for pattern in patterns:
            matches = pattern.findall(text_str)
            for match in matches:
                match = match.strip()
                if not self._is_noise(match):
                    if sensitive_type == 'ADDRESS':
                        # 对 ADDRESS 类型进行额外验证
                        if not re.search(r'(?:省|市|区|县|镇|乡|路|街|道|号|室)', match):
                            continue
                        if len(match) < 6 or len(match) > 100:
                            continue
                        if re.search(r'(?:医院|学校|银行|保险|公司|政府|法院|公安局|派出所|居委会|街道办)', match):
                            continue
                        if re.search(r'(?:转入|转出|转入市|转出市)', match):
                            continue
                    if validate_sensitive_value(sensitive_type, match):
                        results.append(match)

        return results

    def match_chinese_names(self, text: str) -> List[str]:
        if not text:
            return []

        names = []
        text_str = str(text)
        seen = set()

        for surname in CHINESE_SURNAMES_COMPOUND:
            pattern = re.compile(re.escape(surname) + r'[\u4e00-\u9fa5]{1,2}')
            for m in pattern.finditer(text_str):
                name = m.group()
                if name not in self.chinese_common_words and name not in seen:
                    start = m.start()
                    if start > 0 and '\u4e00' <= text_str[start - 1] <= '\u9fa5':
                        continue
                    end = m.end()
                    if end < len(text_str) and '\u4e00' <= text_str[end] <= '\u9fa5':
                        continue
                    seen.add(name)
                    names.append(name)

        surname_pattern = '[' + ''.join(re.escape(s) for s in CHINESE_SURNAMES_SINGLE) + ']'
        pattern = re.compile(
            r'(?<![\u4e00-\u9fa5])' + surname_pattern + r'[\u4e00-\u9fa5]{1,3}(?![\u4e00-\u9fa5])'
        )
        for m in pattern.finditer(text_str):
            name = m.group()
            if len(name) < 2 or len(name) > 4:
                continue
            if name in self.chinese_common_words or name in seen:
                continue
            seen.add(name)
            names.append(name)

        return names

    def match_field_value(self, value: str, field_name: str) -> List[Tuple[str, str, float]]:
        if not value or not field_name:
            return []

        results = []
        value_str = str(value).strip()
        field_lower = field_name.lower()

        guided_type = None
        for keyword, sensitive_type in self.field_type_map.items():
            if re.search(r'(?<![a-zA-Z0-9])' + re.escape(keyword) + r'(?![a-zA-Z0-9])', field_lower):
                guided_type = sensitive_type
                break

        if not guided_type:
            return []

        if guided_type == 'CHINESE_NAME':
            if is_chinese_name(value_str):
                results.append((guided_type, value_str, 0.95))
            elif re.match(r'^[\u4e00-\u9fa5]{2,4}$', value_str) and value_str not in CHINESE_NAME_COMMON_WORDS:
                results.append((guided_type, value_str, 0.85))
        elif guided_type == 'PHONE_NUMBER':
            if re.match(r'^1[3-9]\d{9}$', value_str):
                results.append((guided_type, value_str, 0.95))
        elif guided_type == 'EMAIL':
            if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value_str):
                results.append((guided_type, value_str, 0.95))
        elif guided_type == 'ID_CARD':
            if re.match(r'^\d{17}[\dXx]$', value_str):
                results.append((guided_type, value_str, 0.95))
        elif guided_type == 'BANK_CARD':
            if re.match(r'^\d{16,19}$', value_str):
                results.append((guided_type, value_str, 0.90))
        elif guided_type == 'ADDRESS':
            if re.search(r'(?:省|市|区|县|路|号|室)', value_str) and len(value_str) >= 6:
                results.append((guided_type, value_str, 0.95))
        elif guided_type == 'PASSPORT':
            if re.match(r'^[EGDSPCMH]\d{7,8}$', value_str):
                results.append((guided_type, value_str, 0.95))
        elif guided_type == 'VIN_CODE':
            if re.match(r'^[A-HJ-NPR-Z0-9]{17}$', value_str):
                results.append((guided_type, value_str, 0.95))
        elif guided_type == 'USCC':
            if re.match(r'^[0-9A-HJ-NP-RTUW-Y]{18}$', value_str):
                results.append((guided_type, value_str, 0.95))
        elif guided_type == 'MEDICAL_RECORD_NO':
            if re.match(r'^MR\d{7,12}$', value_str):
                results.append((guided_type, value_str, 0.95))
        elif guided_type == 'MEDICAL_INSURANCE_NO':
            if re.match(r'^YB\d{12,16}$', value_str):
                results.append((guided_type, value_str, 0.95))
        elif guided_type == 'HOUSING_FUND_NO':
            if re.match(r'^[A-Z]{2}(?!MR)(?!YB)\d{9,15}$', value_str):
                results.append((guided_type, value_str, 0.95))
        elif guided_type == 'SOCIAL_SECURITY_NO':
            if re.match(r'^[\u4e00-\u9fa5][A-Z]{2}\d{8,12}$', value_str):
                results.append((guided_type, value_str, 0.90))
        elif guided_type == 'LICENSE_PLATE':
            if re.match(r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁][A-Z][A-Z0-9]{5,6}$', value_str):
                results.append((guided_type, value_str, 0.95))
        elif guided_type == 'PASSWORD_OR_SECRET':
            if len(value_str) >= 6:
                results.append((guided_type, value_str, 0.85))
        else:
            if len(value_str) >= 4:
                results.append((guided_type, value_str, 0.80))

        return results

    def match_with_hints(self, text: str, field_name: str = '') -> List[Tuple[str, str, float]]:
        if not text:
            return []

        results = []
        text_str = str(text)

        field_lower = field_name.lower() if field_name else ''
        hint_types = []
        for keyword, sensitive_type in SENSITIVE_KEYWORDS.items():
            if keyword.lower() in field_lower:
                hint_types.append(sensitive_type)

        for sensitive_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = pattern.findall(text_str)
                for match in matches:
                    match = match.strip()
                    if not self._is_noise(match):
                        if not validate_sensitive_value(sensitive_type, match):
                            continue

                        # 计算置信度
                        confidence = 0.80
                        if sensitive_type in hint_types:
                            confidence = 0.95

                        # 对 ADDRESS 类型进行额外验证
                        if sensitive_type == 'ADDRESS':
                            # 检查是否包含省/市/区等关键词
                            if not re.search(r'(?:省|市|区|县|镇|乡|路|街|道|号|室)', match):
                                continue
                            # 检查长度是否合理
                            if len(match) < 6 or len(match) > 100:
                                continue
                            # 排除医院、学校等机构名称
                            if re.search(r'(?:医院|学校|银行|保险|公司|政府|法院|公安局|派出所|居委会|街道办)', match):
                                continue
                            # 排除"转入"等词语
                            if re.search(r'(?:转入|转出|转入市|转出市)', match):
                                continue
                            # 排除MAC地址格式
                            if re.match(r'^[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}:[0-9a-f]{2}$', match, re.IGNORECASE):
                                continue
                            # 排除IP地址格式
                            if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', match):
                                continue
                            # 提高置信度
                            confidence = max(confidence, 0.90)

                        results.append((sensitive_type, match, confidence))

        return results

    def _is_noise(self, text: str) -> bool:
        if not text or len(text.strip()) < 2:
            return True
        text = text.strip()
        if re.match(r'^\d{1,2}$', text):
            return True
        if re.match(r'^[a-zA-Z]{1,3}$', text):
            return True
        if text.lower() in ('test', 'demo', 'example', 'null', 'none', 'undefined', 'n/a', 'nan'):
            return True
        return False

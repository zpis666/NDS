import re
from typing import List
from .base import BaseDetector
from utils.db_connector import DatabaseConnector
from models.candidate import Candidate
from matchers.patterns import is_chinese_name


class UnstructuredDetector(BaseDetector):
    def __init__(self):
        super().__init__()
        self.data_form = 'unstructured_text'
        self.context_keywords = {
            'CHINESE_NAME': [
                '甲方', '乙方', '丙方', '申请人', '联系人', '负责人',
                '患者', '病人', '姓名', '名字', '委托人', '受益人',
                '客户', '员工', '法人', '代表', '被告', '原告',
                '监护人', '代理人', '收款人', '汇款人', '持卡人',
                '就诊人', '体检人', '被保险人', '车主', '驾驶员',
                '被征地人', '报告人', '丢失人', '来信人', '当事人',
                '报案人', '违规当事人', '负责人', '孕妇', '用户',
                '被回访人', '来电', '协助'
            ],
            'PHONE_NUMBER': [
                '电话', '手机', '联系方式', '联系电话', '手机号',
                'tel', 'phone', 'mobile'
            ],
            'EMAIL': [
                '邮箱', '邮件', 'email', '邮件地址'
            ],
            'ADDRESS': [
                '地址', '住址', '住所', '居住地', '通讯地址',
                '户籍', '家庭地址', '单位地址'
            ],
            'ID_CARD': [
                '身份证', '身份证号', '证件号码', '证件号',
                'ID号', '身份号'
            ],
            'BANK_CARD': [
                '银行卡', '卡号', '账号', '银行账号', '收款账号'
            ]
        }

    def detect(self, connector: DatabaseConnector, db_name: str, db_type: str, fields: list) -> List[Candidate]:
        candidates = []

        for field_info in fields:
            table_name = field_info['table_name']
            column_name = field_info['column_name']
            primary_key = field_info['primary_key']

            if not primary_key:
                continue

            try:
                q = '"' if db_type == 'postgresql' else '`'
                sql = f"SELECT {q}{primary_key}{q}, {q}{column_name}{q} FROM {q}{table_name}{q} WHERE {q}{column_name}{q} IS NOT NULL"

                for batch in connector.execute_batch(sql, batch_size=10000):
                    for row in batch:
                        record_id = str(row[primary_key])
                        value = row[column_name]

                        if not value:
                            continue

                        value_str = str(value)
                        text_candidates = self._extract_from_text(value_str, column_name, db_type, db_name, table_name, record_id)
                        candidates.extend(text_candidates)
                    del batch

            except Exception as e:
                continue

        return candidates

    def _extract_from_text(self, text: str, field_name: str, db_type: str, db_name: str, table_name: str, record_id: str) -> List[Candidate]:
        candidates = []

        context_candidates = self._extract_by_context(text, field_name, db_type, db_name, table_name, record_id)
        candidates.extend(context_candidates)

        regex_candidates = self._extract_by_regex(text, field_name, db_type, db_name, table_name, record_id)
        candidates.extend(regex_candidates)

        name_candidates = self._extract_chinese_names(text, field_name, db_type, db_name, table_name, record_id)
        candidates.extend(name_candidates)

        return candidates

    def _extract_by_context(self, text: str, field_name: str, db_type: str, db_name: str, table_name: str, record_id: str) -> List[Candidate]:
        candidates = []

        for sensitive_type, keywords in self.context_keywords.items():
            for keyword in keywords:
                patterns = [
                    re.compile(rf'{re.escape(keyword)}[：:]\s*([^\s,;，；。、]+)'),
                    re.compile(rf'{re.escape(keyword)}\s*[为是]\s*([^\s,;，；。、]+)'),
                ]
                if sensitive_type == 'CHINESE_NAME':
                    patterns.extend([
                        re.compile(rf'{re.escape(keyword)}\s*([\u4e00-\u9fa5]{{2,4}})(?=[（(，,；;。\s])'),
                        re.compile(rf'{re.escape(keyword)}([\u4e00-\u9fa5]{{2,4}})(?=[（(，,；;。\s])'),
                        re.compile(rf'{re.escape(keyword)}\s*([\u4e00-\u9fa5]{{2,4}})(?=先生|女士|反映|询问|咨询|申诉|举报|报告|称|，|,|。|（|\(|\s)'),
                        re.compile(rf'{re.escape(keyword)}([\u4e00-\u9fa5]{{2,4}})(?=先生|女士|反映|询问|咨询|申诉|举报|报告|称|，|,|。|（|\(|\s)'),
                    ])

                for pattern in patterns:
                    matches = pattern.findall(text)
                    for match in matches:
                        match = match.strip()
                        if not match:
                            continue

                        # 过滤掉明显的噪声
                        if len(match) < 2:
                            continue
                        if re.match(r'^[0-9]+$', match):
                            continue

                        if sensitive_type == 'CHINESE_NAME':
                            if is_chinese_name(match):
                                candidate = self._create_candidate(
                                    db_type=db_type,
                                    db_name=db_name,
                                    table_name=table_name,
                                    field_name=field_name,
                                    record_id=record_id,
                                    sensitive_type='CHINESE_NAME',
                                    extracted_value=match,
                                    confidence=0.95
                                )
                                if candidate:
                                    candidates.append(candidate)
                        else:
                            sub_matches = self.matcher.match_with_hints(match, field_name)
                            for sub_type, sub_value, confidence in sub_matches:
                                if sub_type == sensitive_type:
                                    # 提高上下文匹配的置信度
                                    enhanced_confidence = min(confidence * 1.5, 0.99)
                                    candidate = self._create_candidate(
                                        db_type=db_type,
                                        db_name=db_name,
                                        table_name=table_name,
                                        field_name=field_name,
                                        record_id=record_id,
                                        sensitive_type=sub_type,
                                        extracted_value=sub_value,
                                        confidence=enhanced_confidence
                                    )
                                    if candidate:
                                        candidates.append(candidate)

        return candidates

    def _extract_by_regex(self, text: str, field_name: str, db_type: str, db_name: str, table_name: str, record_id: str) -> List[Candidate]:
        candidates = []

        matches = self.matcher.match_with_hints(text, field_name)

        for sensitive_type, extracted_value, confidence in matches:
            # 过滤掉低置信度的 ADDRESS 匹配（减少误报）
            if sensitive_type == 'ADDRESS' and confidence < 0.85:
                continue
            # 过滤掉包含医院、学校等机构名称的地址
            if sensitive_type == 'ADDRESS' and re.search(r'(?:医院|学校|银行|保险|公司|政府|法院|公安局|派出所|居委会|街道办|转入|转出)', extracted_value):
                continue

            candidate = self._create_candidate(
                db_type=db_type,
                db_name=db_name,
                table_name=table_name,
                field_name=field_name,
                record_id=record_id,
                sensitive_type=sensitive_type,
                extracted_value=extracted_value,
                confidence=confidence
            )
            if candidate:
                candidates.append(candidate)

        return candidates

    def _extract_chinese_names(self, text: str, field_name: str, db_type: str, db_name: str, table_name: str, record_id: str) -> List[Candidate]:
        candidates = []

        names = self.matcher.match_chinese_names(text)

        for name in names:
            candidate = self._create_candidate(
                db_type=db_type,
                db_name=db_name,
                table_name=table_name,
                field_name=field_name,
                record_id=record_id,
                sensitive_type='CHINESE_NAME',
                extracted_value=name,
                confidence=0.85
            )
            if candidate:
                candidates.append(candidate)

        return candidates

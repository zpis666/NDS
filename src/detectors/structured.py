from typing import List
from .base import BaseDetector
from utils.db_connector import DatabaseConnector
from models.candidate import Candidate
from matchers.patterns import is_likely_id_card


class StructuredDetector(BaseDetector):
    def __init__(self):
        super().__init__()
        self.data_form = 'structured'

    def detect(self, connector: DatabaseConnector, db_name: str, db_type: str, fields: list) -> List[Candidate]:
        candidates = []

        for field_info in fields:
            table_name = field_info['table_name']
            column_name = field_info['column_name']
            primary_key = field_info['primary_key']

            if not primary_key:
                continue

            try:
                q = self._quote(db_type)
                sql = f"SELECT {q}{primary_key}{q}, {q}{column_name}{q} FROM {q}{table_name}{q} WHERE {q}{column_name}{q} IS NOT NULL"

                for batch in connector.execute_batch(sql, batch_size=10000):
                    for row in batch:
                        record_id = str(row[primary_key])
                        value = row[column_name]

                        if not value:
                            continue

                        value_str = str(value)

                        guided_matches = self.matcher.match_field_value(value_str, column_name)
                        for sensitive_type, extracted_value, confidence in guided_matches:
                            candidate = self._create_candidate(
                                db_type=db_type,
                                db_name=db_name,
                                table_name=table_name,
                                field_name=column_name,
                                record_id=record_id,
                                sensitive_type=sensitive_type,
                                extracted_value=extracted_value,
                                confidence=confidence
                            )
                            if candidate:
                                candidates.append(candidate)

                        regex_matches = self.matcher.match_with_hints(value_str, column_name)
                        for sensitive_type, extracted_value, confidence in regex_matches:
                            candidate = self._create_candidate(
                                db_type=db_type,
                                db_name=db_name,
                                table_name=table_name,
                                field_name=column_name,
                                record_id=record_id,
                                sensitive_type=sensitive_type,
                                extracted_value=extracted_value,
                                confidence=confidence
                            )
                            if candidate:
                                candidates.append(candidate)
                    del batch

            except Exception as e:
                continue

        seen_tuples = set()
        deduped = []
        TYPE_PRIORITY = {
            'ID_CARD': 10, 'BANK_CARD': 9, 'PHONE_NUMBER': 8, 'EMAIL': 8,
            'PASSPORT': 7, 'USCC': 6, 'VIN_CODE': 6, 'LICENSE_PLATE': 5,
            'MEDICAL_RECORD_NO': 5, 'MEDICAL_INSURANCE_NO': 5,
            'HOUSING_FUND_NO': 5, 'SOCIAL_SECURITY_NO': 5,
            'IP_ADDRESS': 3, 'MAC_ADDRESS': 3, 'GPS_COORDINATE': 3,
        }
        value_best = {}
        for c in candidates:
            tuple_key = (c.record_id, c.sensitive_type, c.extracted_value)
            if tuple_key in seen_tuples:
                continue
            seen_tuples.add(tuple_key)

            val = c.extracted_value
            if val in value_best:
                existing = value_best[val]
                old_pri = TYPE_PRIORITY.get(existing.sensitive_type, 0)
                new_pri = TYPE_PRIORITY.get(c.sensitive_type, 0)
                if new_pri > old_pri:
                    deduped = [x for x in deduped if not (x.extracted_value == val)]
                    deduped.append(c)
                    value_best[val] = c
            else:
                value_best[val] = c
                deduped.append(c)

        promoted = []
        for c in deduped:
            if c.sensitive_type == 'BANK_CARD' and is_likely_id_card(c.extracted_value):
                candidate = self._create_candidate(
                    db_type=c.db_type,
                    db_name=c.db_name,
                    table_name=c.table_name,
                    field_name=c.field_name,
                    record_id=c.record_id,
                    sensitive_type='ID_CARD',
                    extracted_value=c.extracted_value,
                    confidence=c.confidence
                )
                if candidate:
                    promoted.append(candidate)
            else:
                promoted.append(c)

        return promoted

    def _quote(self, db_type: str) -> str:
        if db_type == 'postgresql':
            return '"'
        return '`'

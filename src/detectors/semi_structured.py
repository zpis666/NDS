import ast
import json
from typing import List
from .base import BaseDetector
from utils.db_connector import DatabaseConnector
from models.candidate import Candidate


class SemiStructuredDetector(BaseDetector):
    def __init__(self):
        super().__init__()
        self.data_form = 'semi_structured'

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
                        json_matches = self._extract_from_json(value_str, column_name)

                        for sensitive_type, extracted_value, confidence in json_matches:
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

        return candidates

    def _extract_from_json(self, json_str: str, field_name: str) -> List[tuple]:
        results = []

        try:
            data = json.loads(json_str)
            self._traverse_json(data, field_name, results)
        except (json.JSONDecodeError, TypeError):
            try:
                data = ast.literal_eval(json_str)
                self._traverse_json(data, field_name, results)
            except Exception:
                matches = self.matcher.match_with_hints(json_str, field_name)
                results.extend(matches)

        return results

    def _traverse_json(self, data, field_name: str, results: list):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    matches = self.matcher.match_with_hints(value, key)
                    results.extend(matches)
                    guided = self.matcher.match_field_value(value, key)
                    results.extend(guided)
                elif isinstance(value, (int, float)):
                    matches = self.matcher.match_with_hints(str(value), key)
                    results.extend(matches)
                elif isinstance(value, (dict, list)):
                    self._traverse_json(value, key, results)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    matches = self.matcher.match_with_hints(item, field_name)
                    results.extend(matches)
                    guided = self.matcher.match_field_value(item, field_name)
                    results.extend(guided)
                elif isinstance(item, (int, float)):
                    matches = self.matcher.match_with_hints(str(item), field_name)
                    results.extend(matches)
                elif isinstance(item, (dict, list)):
                    self._traverse_json(item, field_name, results)

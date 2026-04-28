import json
from typing import List
from .base import BaseDetector
from utils.db_connector import DatabaseConnector
from decoders.base64_decoder import Base64Decoder
from decoders.hex_decoder import HexDecoder
from decoders.url_decoder import UrlDecoder
from models.candidate import Candidate


class EncodedDetector(BaseDetector):
    def __init__(self):
        super().__init__()
        self.data_form = 'encoded'
        self.decoders = [
            ('base64', Base64Decoder()),
            ('hex', HexDecoder()),
            ('url', UrlDecoder()),
        ]

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
                        decoded_candidates = self._try_decode_and_match(value_str, column_name, db_type, db_name, table_name, record_id)
                        candidates.extend(decoded_candidates)
                    del batch

            except Exception as e:
                continue

        return candidates

    def _try_kv_parse(self, text: str, field_name: str, db_type: str, db_name: str, table_name: str, record_id: str) -> List[Candidate]:
        candidates = []
        if '|' not in text:
            return candidates

        pairs = text.split('|')
        kv_dict = {}
        for pair in pairs:
            if ':' in pair:
                key, _, val = pair.partition(':')
                key = key.strip()
                val = val.strip()
                if key and val:
                    kv_dict[key] = val

        if not kv_dict:
            return candidates

        for key, val in kv_dict.items():
            key_lower = key.lower()
            matches = self.matcher.match_with_hints(val, key_lower)
            guided = self.matcher.match_field_value(val, key_lower)
            for sensitive_type, extracted_value, confidence in list(matches) + list(guided):
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

    def _try_decode_and_match(self, value: str, field_name: str, db_type: str, db_name: str, table_name: str, record_id: str) -> List[Candidate]:
        candidates = []

        raw_matches = self.matcher.match_with_hints(value, field_name)
        raw_guided = self.matcher.match_field_value(value, field_name)
        for sensitive_type, extracted_value, confidence in list(raw_matches) + list(raw_guided):
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

        if candidates:
            return candidates

        for decoder_name, decoder in self.decoders:
            try:
                is_encoded, decoded = decoder.try_decode(value)

                if is_encoded and decoded != value:
                    json_candidates = self._try_json_parse(decoded, field_name, db_type, db_name, table_name, record_id)
                    if json_candidates:
                        candidates.extend(json_candidates)
                        continue

                    kv_candidates = self._try_kv_parse(decoded, field_name, db_type, db_name, table_name, record_id)
                    if kv_candidates:
                        candidates.extend(kv_candidates)
                        continue

                    matches = self.matcher.match_with_hints(decoded, field_name)
                    guided = self.matcher.match_field_value(decoded, field_name)
                    all_matches = list(matches) + list(guided)

                    for sensitive_type, extracted_value, confidence in all_matches:
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

            except Exception:
                continue

        return candidates

    def _try_json_parse(self, text: str, field_name: str, db_type: str, db_name: str, table_name: str, record_id: str) -> List[Candidate]:
        candidates = []
        try:
            data = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return candidates

        if not isinstance(data, dict):
            return candidates

        for key, val in data.items():
            if not isinstance(val, str) or not val:
                continue
            key_lower = key.lower()
            matches = self.matcher.match_with_hints(val, key_lower)
            guided = self.matcher.match_field_value(val, key_lower)
            for sensitive_type, extracted_value, confidence in list(matches) + list(guided):
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

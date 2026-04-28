import re
import base64
from typing import List
from .base import BaseDetector
from utils.db_connector import DatabaseConnector
from models.candidate import Candidate


class BinaryBlobDetector(BaseDetector):
    def __init__(self):
        super().__init__()
        self.data_form = 'binary_blob'
        self._ocr_engine = None
        self._ocr_failed = False

    def _get_ocr_engine(self):
        if self._ocr_engine is not None:
            return self._ocr_engine
        if self._ocr_failed:
            return None
        try:
            from ocr.engine import OcrEngine
            self._ocr_engine = OcrEngine()
            return self._ocr_engine
        except Exception:
            self._ocr_failed = True
            return None

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

                for batch in connector.execute_batch(sql, batch_size=500):
                    for row in batch:
                        record_id = str(row[primary_key])
                        blob_data = row[column_name]

                        if not blob_data:
                            continue

                        blob_candidates = self._process_blob(
                            blob_data, column_name, db_type, db_name, table_name, record_id
                        )
                        candidates.extend(blob_candidates)
                    del batch

            except Exception:
                continue

        return candidates

    BINARY_SIGNATURES = [
        b'\xff\xd8\xff',      # JPEG
        b'\x89PNG',           # PNG
        b'GIF8',              # GIF
        b'BM',                # BMP
    ]

    SKIP_SIGNATURES = [
        b'PK\x03\x04',       # ZIP/DOCX
        b'%PDF',              # PDF
        b'\x00\x00\x01\x00', # ICO
        b'RIFF',              # RIFF (WEBP)
    ]

    def _process_blob(self, blob_data, field_name: str, db_type: str, db_name: str, table_name: str, record_id: str) -> List[Candidate]:
        candidates = []

        if isinstance(blob_data, str):
            try:
                image_bytes = base64.b64decode(blob_data)
            except Exception:
                image_bytes = blob_data.encode('utf-8', errors='ignore')
        elif isinstance(blob_data, bytes):
            image_bytes = blob_data
        elif isinstance(blob_data, memoryview):
            image_bytes = bytes(blob_data)
        else:
            image_bytes = bytes(blob_data) if blob_data else b''

        if not image_bytes:
            return candidates

        if self._is_skip_binary(image_bytes):
            return candidates

        is_image = self._is_image_file(image_bytes)

        text = ''
        if is_image:
            text = self._ocr_extract(image_bytes)

        if not text:
            text = self._text_fallback(image_bytes)

        if not text:
            return candidates

        text = self._enhance_text(text)

        matches = self.matcher.match_with_hints(text, field_name)

        for sensitive_type, extracted_value, confidence in matches:
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

    def _ocr_extract(self, image_bytes: bytes) -> str:
        engine = self._get_ocr_engine()
        if engine is None:
            return ''

        try:
            preprocessed = self._preprocess_image(image_bytes)
            results = engine.recognize(preprocessed)
            if not results:
                return ''
            texts = [text for text, conf in results if text]
            return ' '.join(texts)
        except Exception:
            return ''

    def _preprocess_image(self, image_bytes: bytes) -> bytes:
        try:
            from ocr.preprocessor import ImagePreprocessor
            return ImagePreprocessor.preprocess(image_bytes)
        except Exception:
            return image_bytes

    def _is_image_file(self, data: bytes) -> bool:
        for sig in self.BINARY_SIGNATURES:
            if data[:len(sig)] == sig:
                return True
        return False

    def _is_skip_binary(self, data: bytes) -> bool:
        for sig in self.SKIP_SIGNATURES:
            if data[:len(sig)] == sig:
                return True
        return False

    def _text_fallback(self, data: bytes) -> str:
        try:
            text = data.decode('utf-8', errors='ignore')
            printable_ratio = sum(1 for c in text if c.isprintable() or c in '\n\r\t') / max(len(text), 1)
            if printable_ratio > 0.7 and len(text) > 10:
                return text
        except Exception:
            pass

        try:
            text = data.decode('gbk', errors='ignore')
            printable_ratio = sum(1 for c in text if c.isprintable() or c in '\n\r\t') / max(len(text), 1)
            if printable_ratio > 0.7 and len(text) > 10:
                return text
        except Exception:
            pass

        return ''

    def _enhance_text(self, text: str) -> str:
        if not text:
            return text

        replacements = {
            '。': '.',
            '，': ',',
            '：': ':',
            '；': ';',
            '（': '(',
            '）': ')',
            '　': ' ',
            '\u00a0': ' ',
        }

        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)

        result = re.sub(r'\s+', ' ', result)
        result = result.strip()

        return result

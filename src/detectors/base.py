from abc import ABC, abstractmethod
from typing import List
from utils.db_connector import DatabaseConnector
from matchers.core import SensitiveMatcher
from models.candidate import Candidate
from config import get_sensitive_level


class BaseDetector(ABC):
    def __init__(self):
        self.matcher = SensitiveMatcher()
        self.data_form = 'structured'

    @abstractmethod
    def detect(self, connector: DatabaseConnector, db_name: str, db_type: str, fields: list) -> List[Candidate]:
        pass

    def _create_candidate(
        self,
        db_type: str,
        db_name: str,
        table_name: str,
        field_name: str,
        record_id: str,
        sensitive_type: str,
        extracted_value: str,
        confidence: float = 1.0
    ) -> Candidate:
        return Candidate(
            db_type=db_type,
            db_name=db_name,
            table_name=table_name,
            field_name=field_name,
            record_id=record_id,
            sensitive_type=sensitive_type,
            extracted_value=extracted_value,
            data_form=self.data_form,
            confidence=confidence,
            sensitive_level=get_sensitive_level(sensitive_type),
        )

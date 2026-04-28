from typing import List
from .base import BaseDetector
from utils.db_connector import DatabaseConnector
from scanners.db_object_scanner import DbObjectScanner
from models.candidate import Candidate


class DbObjectDetector(BaseDetector):
    def __init__(self):
        super().__init__()
        self.data_form = 'db_object'

    def detect(self, connector: DatabaseConnector, db_name: str, db_type: str, fields: list = None) -> List[Candidate]:
        candidates = []

        scanner = DbObjectScanner(connector)

        # 检查存储过程
        procedures = scanner.get_stored_procedures()
        for proc in procedures:
            proc_name = proc['name']
            definition = proc['definition']

            if definition:
                proc_candidates = self._scan_definition(
                    definition, proc_name, '__stored_procedure__',
                    db_type, db_name
                )
                candidates.extend(proc_candidates)

        # 检查视图
        views = scanner.get_views()
        for view in views:
            view_name = view['name']
            definition = view['definition']

            if definition:
                view_candidates = self._scan_definition(
                    definition, view_name, '__view__',
                    db_type, db_name
                )
                candidates.extend(view_candidates)

        return candidates

    def _scan_definition(self, definition: str, object_name: str, table_name: str, db_type: str, db_name: str) -> List[Candidate]:
        candidates = []

        matches = self.matcher.match_with_hints(definition, object_name)

        for sensitive_type, extracted_value, confidence in matches:
            candidate = self._create_candidate(
                db_type=db_type,
                db_name=db_name,
                table_name=table_name,
                field_name=object_name,
                record_id='—',
                sensitive_type=sensitive_type,
                extracted_value=extracted_value,
                confidence=confidence
            )
            if candidate:
                candidates.append(candidate)

        return candidates

from typing import Dict, List, Any
from .structure_scanner import StructureScanner


class FormRouter:
    def __init__(self, scanner: StructureScanner):
        self.scanner = scanner
        self.db_type = scanner.db_type

    def route_all(self) -> Dict[str, List[Dict[str, Any]]]:
        result = {
            'structured': [],
            'semi_structured': [],
            'encoded': [],
            'unstructured': [],
            'binary_blob': [],
        }

        tables = self.scanner.get_table_names()

        for table_name in tables:
            columns = self.scanner.get_columns(table_name)
            primary_key = self.scanner.get_primary_key(table_name)

            for col in columns:
                col_name = col['COLUMN_NAME']
                col_type = col['DATA_TYPE'].lower()

                field_info = {
                    'table_name': table_name,
                    'column_name': col_name,
                    'column_type': col_type,
                    'primary_key': primary_key
                }

                if self._is_blob_type(col_type):
                    result['binary_blob'].append(field_info)
                elif self._is_json_type(col_type):
                    result['semi_structured'].append(field_info)
                elif self._is_encoded_column(col_name, col_type):
                    result['encoded'].append(field_info)
                elif self._is_unstructured_column(col_name, col_type):
                    result['unstructured'].append(field_info)
                else:
                    result['structured'].append(field_info)

        return result

    def _is_blob_type(self, col_type: str) -> bool:
        blob_types = {
            'mysql': {'blob', 'mediumblob', 'longblob', 'binary', 'varbinary', 'tinyblob'},
            'postgresql': {'bytea'}
        }
        return col_type in blob_types.get(self.db_type, set())

    def _is_json_type(self, col_type: str) -> bool:
        json_types = {
            'mysql': {'json'},
            'postgresql': {'json', 'jsonb'}
        }
        return col_type in json_types.get(self.db_type, set())

    def _is_encoded_column(self, col_name: str, col_type: str) -> bool:
        encoded_keywords = ['encoded', 'encrypt', 'cipher', 'base64', 'hex', 'hash', 'token', 'secret', 'credential']
        col_lower = col_name.lower()
        return any(kw in col_lower for kw in encoded_keywords)

    def _is_unstructured_column(self, col_name: str, col_type: str) -> bool:
        unstructured_keywords = ['text', 'content', 'description', 'note', 'log', 'comment',
                                 'feedback', 'message', 'body', 'action_text', 'record',
                                 'memo', 'remark', 'remarks', 'summary', 'detail', 'details']
        col_lower = col_name.lower()

        structured_suffixes = ('_no', '_id', '_number', '_code', '_amount', '_price',
                               '_cost', '_date', '_time', '_count', '_status', '_type',
                               '_level', '_rate', '_ratio', '_score', '_age', '_year')
        if any(col_lower.endswith(s) or col_lower.endswith(s + 's') for s in structured_suffixes):
            return False

        if any(kw in col_lower for kw in unstructured_keywords):
            return True

        text_types = {
            'mysql': {'text', 'mediumtext', 'longtext', 'tinytext'},
            'postgresql': {'text'}
        }
        if col_type in text_types.get(self.db_type, set()):
            return True

        if self.db_type == 'mysql' and col_type in ('varchar', 'char') and col_name.lower() in (
            'description', 'content', 'note', 'notes', 'log', 'comment', 'feedback'
        ):
            return True

        return False

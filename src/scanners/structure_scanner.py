from typing import Dict, List, Any
from utils.db_connector import DatabaseConnector


class StructureScanner:
    def __init__(self, connector: DatabaseConnector):
        self.connector = connector
        self.db_type = connector.db_type
        self.db_name = connector.db_name

    def scan_all(self) -> Dict[str, List[Dict[str, Any]]]:
        result = {}
        tables = self.connector.get_tables()

        for table in tables:
            table_name = table['TABLE_NAME']
            columns = self.connector.get_columns(table_name)
            primary_key = self.connector.get_primary_key(table_name)

            result[table_name] = {
                'columns': columns,
                'primary_key': primary_key
            }

        return result

    def get_table_names(self) -> List[str]:
        tables = self.connector.get_tables()
        return [t['TABLE_NAME'] for t in tables]

    def get_columns(self, table_name: str) -> List[Dict[str, Any]]:
        return self.connector.get_columns(table_name)

    def get_primary_key(self, table_name: str) -> str:
        pk = self.connector.get_primary_key(table_name)
        if pk:
            return pk

        columns = self.connector.get_columns(table_name)
        if columns:
            return columns[0]['COLUMN_NAME']

        return None

    def get_column_types(self, table_name: str) -> Dict[str, str]:
        columns = self.connector.get_columns(table_name)
        return {col['COLUMN_NAME']: col['DATA_TYPE'] for col in columns}

    def get_blob_columns(self, table_name: str) -> List[str]:
        columns = self.connector.get_columns(table_name)
        blob_types = {
            'mysql': {'blob', 'mediumblob', 'longblob', 'binary', 'varbinary', 'tinyblob'},
            'postgresql': {'bytea'}
        }

        result = []
        for col in columns:
            if col['DATA_TYPE'].lower() in blob_types.get(self.db_type, set()):
                result.append(col['COLUMN_NAME'])

        return result

    def get_json_columns(self, table_name: str) -> List[str]:
        columns = self.connector.get_columns(table_name)
        json_types = {
            'mysql': {'json'},
            'postgresql': {'json', 'jsonb'}
        }

        result = []
        for col in columns:
            if col['DATA_TYPE'].lower() in json_types.get(self.db_type, set()):
                result.append(col['COLUMN_NAME'])

        return result

    def get_text_columns(self, table_name: str) -> List[str]:
        columns = self.connector.get_columns(table_name)
        text_types = {
            'mysql': {'char', 'varchar', 'text', 'mediumtext', 'longtext', 'enum', 'set'},
            'postgresql': {'character varying', 'varchar', 'text', 'character', 'char'}
        }

        result = []
        for col in columns:
            if col['DATA_TYPE'].lower() in text_types.get(self.db_type, set()):
                result.append(col['COLUMN_NAME'])

        return result

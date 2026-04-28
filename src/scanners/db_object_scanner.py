from typing import Dict, List, Any
from utils.db_connector import DatabaseConnector


class DbObjectScanner:
    def __init__(self, connector: DatabaseConnector):
        self.connector = connector
        self.db_type = connector.db_type
        self.db_name = connector.db_name

    def scan_all(self) -> Dict[str, List[Dict[str, Any]]]:
        result = {
            'stored_procedures': [],
            'views': []
        }

        procedures = self.connector.get_stored_procedures()
        for proc in procedures:
            proc_name = proc['ROUTINE_NAME']
            definition = self.connector.get_routine_definition(proc_name)
            result['stored_procedures'].append({
                'name': proc_name,
                'definition': definition
            })

        views = self.connector.get_views()
        for view in views:
            view_name = view['TABLE_NAME']
            definition = self.connector.get_view_definition(view_name)
            result['views'].append({
                'name': view_name,
                'definition': definition
            })

        return result

    def get_stored_procedures(self) -> List[Dict[str, Any]]:
        procedures = self.connector.get_stored_procedures()
        result = []

        for proc in procedures:
            proc_name = proc['ROUTINE_NAME']
            definition = self.connector.get_routine_definition(proc_name)
            result.append({
                'name': proc_name,
                'definition': definition
            })

        return result

    def get_views(self) -> List[Dict[str, Any]]:
        views = self.connector.get_views()
        result = []

        for view in views:
            view_name = view['TABLE_NAME']
            definition = self.connector.get_view_definition(view_name)
            result.append({
                'name': view_name,
                'definition': definition
            })

        return result

    def get_stored_procedure_definition(self, proc_name: str) -> str:
        return self.connector.get_routine_definition(proc_name)

    def get_view_definition(self, view_name: str) -> str:
        return self.connector.get_view_definition(view_name)

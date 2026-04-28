import pymysql
import psycopg2
from psycopg2.extras import RealDictCursor
from config import get_db_config


_CP1252_TO_BYTE = {
    0x20AC: 0x80, 0x201A: 0x82, 0x0192: 0x83, 0x201E: 0x84,
    0x2026: 0x85, 0x2020: 0x86, 0x2021: 0x87, 0x02C6: 0x88,
    0x2030: 0x89, 0x0160: 0x8A, 0x2039: 0x8B, 0x0152: 0x8C,
    0x017D: 0x8E, 0x2018: 0x91, 0x2019: 0x92, 0x201C: 0x93,
    0x201D: 0x94, 0x2022: 0x95, 0x2013: 0x96, 0x2014: 0x97,
    0x02DC: 0x98, 0x2122: 0x99, 0x0161: 0x9A, 0x203A: 0x9B,
    0x0153: 0x9C, 0x017E: 0x9E, 0x0178: 0x9F,
}

def fix_mojibake(value):
    if not isinstance(value, str):
        return value
    has_cjk = any('\u4e00' <= c <= '\u9fa5' for c in value)
    if has_cjk:
        return value
    for enc in ('utf-8', 'gbk', 'gb2312', 'gb18030'):
        for src in ('latin1', 'cp1252', 'iso-8859-1'):
            try:
                fixed = value.encode(src).decode(enc)
                if any('\u4e00' <= c <= '\u9fa5' for c in fixed):
                    return fixed
            except (UnicodeDecodeError, UnicodeEncodeError):
                continue
    raw_bytes = bytearray()
    for c in value:
        cp = ord(c)
        if cp < 256:
            raw_bytes.append(cp)
        elif cp in _CP1252_TO_BYTE:
            raw_bytes.append(_CP1252_TO_BYTE[cp])
        else:
            return value
    for enc in ('utf-8', 'gbk', 'gb18030'):
        try:
            fixed = raw_bytes.decode(enc)
            if any('\u4e00' <= c <= '\u9fa5' for c in fixed):
                return fixed
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue
    return value


def fix_row_values(row):
    if isinstance(row, dict):
        return {k: fix_mojibake(v) for k, v in row.items()}
    return row


class DatabaseConnector:
    def __init__(self, db_type, db_name=None):
        self.db_type = db_type
        self.db_name = db_name
        self.connection = None
        self.config = get_db_config(db_type)

    def connect(self):
        if self.db_type == 'mysql':
            self.connection = pymysql.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                database=self.db_name,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
        elif self.db_type == 'postgresql':
            self.connection = psycopg2.connect(
                host=self.config['host'],
                port=self.config['port'],
                user=self.config['user'],
                password=self.config['password'],
                dbname=self.db_name,
                cursor_factory=RealDictCursor
            )
        return self

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute(self, sql, params=None):
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        if self.db_type == 'mysql':
            rows = [fix_row_values(r) for r in rows]
        return rows

    def execute_batch(self, sql, params=None, batch_size=5000):
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        while True:
            rows = cursor.fetchmany(batch_size)
            if not rows:
                break
            if self.db_type == 'mysql':
                rows = [fix_row_values(r) for r in rows]
            yield rows
        cursor.close()

    def execute_one(self, sql, params=None):
        cursor = self.connection.cursor()
        cursor.execute(sql, params)
        row = cursor.fetchone()
        if self.db_type == 'mysql' and row:
            row = fix_row_values(row)
        return row

    def get_tables(self):
        if self.db_type == 'mysql':
            sql = """
                SELECT TABLE_NAME, TABLE_TYPE
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
            """
            return self.execute(sql, (self.db_name,))
        elif self.db_type == 'postgresql':
            sql = """
                SELECT tablename AS table_name
                FROM pg_tables
                WHERE schemaname = 'public'
            """
            rows = self.execute(sql)
            return [{'TABLE_NAME': r['table_name']} for r in rows]

    def get_columns(self, table_name):
        if self.db_type == 'mysql':
            sql = """
                SELECT COLUMN_NAME, DATA_TYPE, COLUMN_KEY
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """
            return self.execute(sql, (self.db_name, table_name))
        elif self.db_type == 'postgresql':
            sql = """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
            """
            rows = self.execute(sql, (table_name,))
            return [{'COLUMN_NAME': r['column_name'], 'DATA_TYPE': r['data_type']} for r in rows]

    def get_primary_key(self, table_name):
        if self.db_type == 'mysql':
            sql = """
                SELECT COLUMN_NAME
                FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND COLUMN_KEY = 'PRI'
            """
            result = self.execute(sql, (self.db_name, table_name))
            return result[0]['COLUMN_NAME'] if result else None
        elif self.db_type == 'postgresql':
            sql = """
                SELECT a.attname AS column_name
                FROM pg_index i
                JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                WHERE i.indrelid = %s::regclass AND i.indisprimary
            """
            result = self.execute(sql, (table_name,))
            return result[0]['column_name'] if result else None

    def get_stored_procedures(self):
        if self.db_type == 'mysql':
            sql = """
                SELECT ROUTINE_NAME
                FROM information_schema.ROUTINES
                WHERE ROUTINE_SCHEMA = %s AND ROUTINE_TYPE = 'PROCEDURE'
            """
            return self.execute(sql, (self.db_name,))
        elif self.db_type == 'postgresql':
            sql = """
                SELECT proname AS routine_name
                FROM pg_proc
                JOIN pg_namespace ON pg_namespace.oid = pg_proc.pronamespace
                WHERE nspname = 'public'
            """
            rows = self.execute(sql)
            return [{'ROUTINE_NAME': r['routine_name']} for r in rows]

    def get_views(self):
        if self.db_type == 'mysql':
            sql = """
                SELECT TABLE_NAME
                FROM information_schema.VIEWS
                WHERE TABLE_SCHEMA = %s
            """
            return self.execute(sql, (self.db_name,))
        elif self.db_type == 'postgresql':
            sql = """
                SELECT table_name
                FROM information_schema.views
                WHERE table_schema = 'public'
            """
            rows = self.execute(sql)
            return [{'TABLE_NAME': r['table_name']} for r in rows]

    def get_routine_definition(self, routine_name):
        if self.db_type == 'mysql':
            sql = """
                SELECT ROUTINE_DEFINITION
                FROM information_schema.ROUTINES
                WHERE ROUTINE_SCHEMA = %s AND ROUTINE_NAME = %s
            """
            result = self.execute_one(sql, (self.db_name, routine_name))
            return result['ROUTINE_DEFINITION'] if result else None
        elif self.db_type == 'postgresql':
            sql = """
                SELECT pg_get_functiondef(p.oid) AS routine_definition
                FROM pg_proc p
                JOIN pg_namespace n ON n.oid = p.pronamespace
                WHERE n.nspname = 'public' AND p.proname = %s
            """
            result = self.execute_one(sql, (routine_name,))
            return result['routine_definition'] if result else None

    def get_view_definition(self, view_name):
        if self.db_type == 'mysql':
            sql = """
                SELECT VIEW_DEFINITION
                FROM information_schema.VIEWS
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """
            result = self.execute_one(sql, (self.db_name, view_name))
            return result['VIEW_DEFINITION'] if result else None
        elif self.db_type == 'postgresql':
            sql = """
                SELECT definition AS view_definition
                FROM pg_views
                WHERE schemaname = 'public' AND viewname = %s
            """
            result = self.execute_one(sql, (view_name,))
            return result['view_definition'] if result else None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

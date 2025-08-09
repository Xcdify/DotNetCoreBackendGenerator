import psycopg2
from psycopg2 import sql
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from utils import pascal_case, snake_case

@dataclass
class Column:
    name: str
    data_type: str
    is_nullable: bool
    column_default: Optional[str] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_info: Optional[Dict[str, str]] = None

@dataclass
class Table:
    name: str
    schema: str
    columns: List[Column] = field(default_factory=list)
    primary_keys: List[str] = field(default_factory=list)
    foreign_keys: List[Dict[str, str]] = field(default_factory=list)

class DatabaseSchemaReader:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.conn = None
        self.cursor = None
    
    def connect(self):
        self.conn = psycopg2.connect(self.connection_string)
        self.cursor = self.conn.cursor()
    
    def disconnect(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
    
    def read_schema(self) -> Dict[str, Any]:
        try:
            self.connect()
            tables = self._get_tables()
            schema_data = {'tables': []}
            
            for table in tables:
                table_info = self._get_table_info(table['table_schema'], table['table_name'])
                schema_data['tables'].append(table_info)
            
            return schema_data
        finally:
            self.disconnect()
    
    def _get_tables(self) -> List[Dict[str, str]]:
        query = """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        AND table_type = 'BASE TABLE'
        ORDER BY table_schema, table_name;
        """
        self.cursor.execute(query)
        return [{'table_schema': row[0], 'table_name': row[1]} for row in self.cursor.fetchall()]
    
    def _get_table_info(self, schema: str, table_name: str) -> Dict[str, Any]:
        columns = self._get_columns(schema, table_name)
        primary_keys = self._get_primary_keys(schema, table_name)
        foreign_keys = self._get_foreign_keys(schema, table_name)
        
        for col in columns:
            if col['name'] in primary_keys:
                col['is_primary_key'] = True
            
            for fk in foreign_keys:
                if col['name'] == fk['column']:
                    col['is_foreign_key'] = True
                    col['foreign_key_info'] = {
                        'referenced_table': fk['referenced_table'],
                        'referenced_column': fk['referenced_column']
                    }
        
        return {
            'name': table_name,
            'schema': schema,
            'columns': columns,
            'primary_keys': primary_keys,
            'foreign_keys': foreign_keys
        }
    
    def _get_columns(self, schema: str, table_name: str) -> List[Dict[str, Any]]:
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length,
            numeric_precision,
            numeric_scale
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position;
        """
        self.cursor.execute(query, (schema, table_name))
        
        columns = []
        for row in self.cursor.fetchall():
            col_name, data_type, is_nullable, column_default, char_max_len, num_precision, num_scale = row
            
            if data_type == 'character varying' and char_max_len:
                data_type = f"varchar({char_max_len})"
            elif data_type == 'numeric' and num_precision and num_scale:
                data_type = f"numeric({num_precision},{num_scale})"
            
            columns.append({
                'name': col_name,
                'data_type': data_type,
                'is_nullable': is_nullable == 'YES',
                'column_default': column_default,
                'is_primary_key': False,
                'is_foreign_key': False,
                'foreign_key_info': None
            })
        
        return columns
    
    def _get_primary_keys(self, schema: str, table_name: str) -> List[str]:
        query = """
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_schema = %s
            AND tc.table_name = %s
        ORDER BY kcu.ordinal_position;
        """
        self.cursor.execute(query, (schema, table_name))
        return [row[0] for row in self.cursor.fetchall()]
    
    def _get_foreign_keys(self, schema: str, table_name: str) -> List[Dict[str, str]]:
        query = """
        SELECT
            kcu.column_name,
            ccu.table_schema AS referenced_schema,
            ccu.table_name AS referenced_table,
            ccu.column_name AS referenced_column
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = %s
            AND tc.table_name = %s;
        """
        self.cursor.execute(query, (schema, table_name))
        
        foreign_keys = []
        for row in self.cursor.fetchall():
            foreign_keys.append({
                'column': row[0],
                'referenced_schema': row[1],
                'referenced_table': row[2],
                'referenced_column': row[3]
            })
        
        return foreign_keys
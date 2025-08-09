import re
from typing import Optional

def pascal_case(text: str) -> str:
    """Convert snake_case or any text to PascalCase"""
    words = re.sub(r'[_\-\s]+', ' ', text).split()
    return ''.join(word.capitalize() for word in words)

def snake_case(text: str) -> str:
    """Convert PascalCase or any text to snake_case"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def camel_case(text: str) -> str:
    """Convert snake_case or any text to camelCase"""
    pascal = pascal_case(text)
    return pascal[0].lower() + pascal[1:] if pascal else ''

def map_postgres_to_csharp(postgres_type: str, is_nullable: bool = False) -> str:
    """Map PostgreSQL data types to C# types"""
    
    postgres_type = postgres_type.lower()
    
    type_mapping = {
        'integer': 'int',
        'int': 'int',
        'int4': 'int',
        'serial': 'int',
        'smallint': 'int',
        'int2': 'int',
        'bigint': 'long',
        'int8': 'long',
        'bigserial': 'long',
        'serial8': 'long',
        'uuid': 'Guid',
        'text': 'string',
        'character varying': 'string',
        'varchar': 'string',
        'character': 'string',
        'char': 'string',
        'boolean': 'bool',
        'bool': 'bool',
        'date': 'DateTime',
        'timestamp': 'DateTime',
        'timestamp without time zone': 'DateTime',
        'timestamp with time zone': 'DateTime',
        'timestamptz': 'DateTime',
        'numeric': 'decimal',
        'decimal': 'decimal',
        'double precision': 'double',
        'float8': 'double',
        'real': 'double',
        'float4': 'float',
        'bytea': 'byte[]',
        'json': 'string',
        'jsonb': 'string',
        'time': 'TimeSpan',
        'time without time zone': 'TimeSpan',
        'time with time zone': 'TimeSpan',
        'interval': 'TimeSpan',
        'money': 'decimal',
    }
    
    base_type = postgres_type.split('(')[0].strip()
    
    csharp_type = type_mapping.get(base_type, 'string')
    
    if is_nullable and csharp_type not in ['string', 'byte[]']:
        csharp_type += '?'
    
    return csharp_type

def get_primary_key_type(columns: list, primary_keys: list) -> Optional[str]:
    """Get the C# type of the primary key column"""
    if not primary_keys:
        return None
    
    pk_name = primary_keys[0]
    for col in columns:
        if col['name'] == pk_name:
            return map_postgres_to_csharp(col['data_type'], col['is_nullable'])
    
    return 'int'

def normalize_connection_string(conn_str: str) -> str:
    """Convert PostgreSQL connection string to Npgsql format"""
    if not conn_str:
        return ""
    
    # If it's already in the postgresql:// format, convert it
    if conn_str.startswith('postgresql://'):
        # Parse postgresql://user:password@host:port/database
        import re
        pattern = r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)'
        match = re.match(pattern, conn_str)
        if match:
            user, password, host, port, database = match.groups()
            return f"host={host};port={port};database={database};username={user};password={password}"
    
    # If it's already in Npgsql format, return as-is
    if any(param in conn_str.lower() for param in ['host=', 'server=']):
        return conn_str
    
    # Default fallback
    return conn_str
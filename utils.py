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

def map_postgres_to_python(postgres_type: str, is_nullable: bool = False) -> str:
    """Map PostgreSQL data types to Python types"""
    
    postgres_type = postgres_type.lower()
    
    type_mapping = {
        'integer': 'int',
        'int': 'int',
        'int4': 'int',
        'serial': 'int',
        'smallint': 'int',
        'int2': 'int',
        'bigint': 'int',
        'int8': 'int',
        'bigserial': 'int',
        'serial8': 'int',
        'uuid': 'UUID',
        'text': 'str',
        'character varying': 'str',
        'varchar': 'str',
        'character': 'str',
        'char': 'str',
        'boolean': 'bool',
        'bool': 'bool',
        'date': 'date',
        'timestamp': 'datetime',
        'timestamp without time zone': 'datetime',
        'timestamp with time zone': 'datetime',
        'timestamptz': 'datetime',
        'numeric': 'Decimal',
        'decimal': 'Decimal',
        'double precision': 'float',
        'float8': 'float',
        'real': 'float',
        'float4': 'float',
        'bytea': 'bytes',
        'json': 'dict',
        'jsonb': 'dict',
        'time': 'time',
        'time without time zone': 'time',
        'time with time zone': 'time',
        'interval': 'timedelta',
        'money': 'Decimal',
    }
    
    base_type = postgres_type.split('(')[0].strip()
    python_type = type_mapping.get(base_type, 'str')
    
    if is_nullable:
        python_type = f'Optional[{python_type}]'
    
    return python_type


def map_postgres_to_sqlalchemy(postgres_type: str, is_nullable: bool = False) -> str:
    """Map PostgreSQL data types to SQLAlchemy column types"""
    
    postgres_type = postgres_type.lower()
    
    type_mapping = {
        'integer': 'Integer',
        'int': 'Integer',
        'int4': 'Integer',
        'serial': 'Integer',
        'smallint': 'SmallInteger',
        'int2': 'SmallInteger',
        'bigint': 'BigInteger',
        'int8': 'BigInteger',
        'bigserial': 'BigInteger',
        'serial8': 'BigInteger',
        'uuid': 'PG_UUID(as_uuid=True)',
        'text': 'Text',
        'character varying': 'String',
        'varchar': 'String',
        'character': 'String',
        'char': 'String',
        'boolean': 'Boolean',
        'bool': 'Boolean',
        'date': 'Date',
        'timestamp': 'DateTime(timezone=True)',
        'timestamp without time zone': 'DateTime',
        'timestamp with time zone': 'DateTime(timezone=True)',
        'timestamptz': 'DateTime(timezone=True)',
        'numeric': 'Numeric',
        'decimal': 'Numeric',
        'double precision': 'Float',
        'float8': 'Float',
        'real': 'Float',
        'float4': 'Float',
        'bytea': 'LargeBinary',
        'json': 'JSON',
        'jsonb': 'JSON',
        'time': 'Time',
        'time without time zone': 'Time',
        'time with time zone': 'Time',
        'interval': 'Interval',
        'money': 'Numeric',
    }
    
    base_type = postgres_type.split('(')[0].strip()
    
    # Handle varchar with length
    if base_type in ['varchar', 'character varying'] and '(' in postgres_type:
        length = postgres_type.split('(')[1].split(')')[0]
        return f'String({length})'
    
    return type_mapping.get(base_type, 'String')


def normalize_connection_string_for_dotnet(conn_str: str) -> str:
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


def normalize_connection_string_for_python(conn_str: str) -> str:
    """Convert PostgreSQL connection string to SQLAlchemy async format"""
    if not conn_str:
        return ""
    
    # If it's already in the postgresql:// format, convert to asyncpg
    if conn_str.startswith('postgresql://'):
        return conn_str.replace('postgresql://', 'postgresql+asyncpg://')
    
    # If it's in Npgsql format, convert to postgresql+asyncpg://
    if any(param in conn_str.lower() for param in ['host=', 'server=']):
        # Parse Npgsql connection string
        params = {}
        for part in conn_str.split(';'):
            if '=' in part:
                key, value = part.split('=', 1)
                params[key.strip().lower()] = value.strip()
        
        host = params.get('host', params.get('server', 'localhost'))
        port = params.get('port', '5432')
        database = params.get('database', 'postgres')
        username = params.get('username', params.get('user', 'postgres'))
        password = params.get('password', '')
        
        return f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
    
    # Default fallback
    return conn_str


def normalize_connection_string(conn_str: str, target_framework: str = 'dotnet') -> str:
    """Normalize connection string for the target framework"""
    if target_framework.lower() == 'fastapi':
        return normalize_connection_string_for_python(conn_str)
    else:
        return normalize_connection_string_for_dotnet(conn_str)
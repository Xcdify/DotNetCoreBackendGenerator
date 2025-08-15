"""
FastAPI Code Generator

This module generates FastAPI applications from PostgreSQL schemas.
"""
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import secrets

from utils import (
    pascal_case, snake_case, camel_case, 
    map_postgres_to_python, map_postgres_to_sqlalchemy,
    normalize_connection_string_for_python
)


class FastAPICodeGenerator:
    """Generator for FastAPI applications."""
    
    def __init__(self):
        """Initialize the generator."""
        self.env = Environment(
            loader=FileSystemLoader('templates/fastapi'),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        
        # Add custom filters
        self.env.filters['pascal_case'] = pascal_case
        self.env.filters['snake_case'] = snake_case
        self.env.filters['camel_case'] = camel_case
    
    def generate_application(
        self, 
        schema: Dict[str, Any], 
        connection_string: str = "",
        table_groups: Optional[Dict[str, List[str]]] = None,
        solution_name: str = "GeneratedApp",
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict[str, str]:
        """
        Generate a complete FastAPI application.
        
        Args:
            schema: Database schema information
            connection_string: Database connection string
            table_groups: Optional table groupings
            solution_name: Name of the solution
            progress_callback: Optional progress callback
            
        Returns:
            Dictionary of file paths and contents
        """
        files = {}
        total_tables = len(schema['tables'])
        current_progress = 0
        
        # If no groups provided, put all tables in General group
        if not table_groups:
            table_groups = {'General': [table['name'] for table in schema['tables']]}
        
        # Create a mapping of table names to groups
        table_to_group = {}
        for group, tables in table_groups.items():
            for table_name in tables:
                table_to_group[table_name] = group
        
        if progress_callback:
            progress_callback(0, "Starting FastAPI generation...")
        
        # Generate files for each table
        for idx, table in enumerate(schema['tables']):
            if progress_callback:
                progress_callback(int((idx / total_tables) * 60), f"Processing table: {table['name']}")
            
            group = table_to_group.get(table['name'], 'General')
            table_data = self._prepare_table_data(table, group)
            
            # Core domain files
            files[f"src/core/entities{table_data['GroupPath']}/{table_data['TableNameSnake']}.py"] = (
                self._generate_entity(table, group)
            )
            
            files[f"src/core/interfaces{table_data['GroupPath']}/{table_data['TableNameSnake']}_repository.py"] = (
                self._generate_repository_interface(table, group)
            )
            
            files[f"src/core/exceptions{table_data['GroupPath']}/{table_data['TableNameSnake']}_exceptions.py"] = (
                self._generate_exceptions(table, group)
            )
            
            # Infrastructure layer files
            files[f"src/infrastructure/database/models{table_data['GroupPath']}/{table_data['TableNameSnake']}_model.py"] = (
                self._generate_sqlalchemy_model(table, group)
            )
            
            files[f"src/infrastructure/database/repositories{table_data['GroupPath']}/{table_data['TableNameSnake']}_repository.py"] = (
                self._generate_repository_impl(table, group)
            )
            
            # Application layer files
            files[f"src/application/dto{table_data['GroupPath']}/{table_data['TableNameSnake']}_dto.py"] = (
                self._generate_dto(table, group)
            )
            
            files[f"src/application/services{table_data['GroupPath']}/{table_data['TableNameSnake']}_service.py"] = (
                self._generate_service(table, group)
            )
            
            # API layer files
            files[f"src/api/v1/routers{table_data['GroupPath']}/{table_data['TableNameSnake']}_router.py"] = (
                self._generate_router(table, group)
            )
            
            files[f"src/api/v1/dependencies{table_data['GroupPath']}/{table_data['TableNameSnake']}_deps.py"] = (
                self._generate_dependencies(table, group)
            )
            
            files[f"src/api/schemas{table_data['GroupPath']}/{table_data['TableNameSnake']}_schema.py"] = (
                self._generate_schema(table, group)
            )
        
        if progress_callback:
            progress_callback(70, "Generating common files...")
        
        # Generate common files
        files.update(self._generate_common_files(schema, solution_name, connection_string, table_groups))
        
        if progress_callback:
            progress_callback(85, "Generating configuration files...")
        
        # Generate configuration files
        files.update(self._generate_config_files(solution_name, connection_string))
        
        if progress_callback:
            progress_callback(95, "Generating Docker and deployment files...")
        
        # Generate Docker and deployment files
        files.update(self._generate_docker_files(solution_name))
        
        if progress_callback:
            progress_callback(100, "FastAPI generation complete!")
        
        return files
    
    def _prepare_table_data(self, table: Dict[str, Any], group: str = 'General') -> Dict[str, Any]:
        """Prepare table data for template rendering."""
        columns = []
        non_primary_columns = []
        primary_key = None
        
        for col in table['columns']:
            col_data = {
                'Name': col['name'],
                'NameSnake': snake_case(col['name']),
                'NamePascal': pascal_case(col['name']),
                'NameCamel': camel_case(col['name']),
                'PythonType': map_postgres_to_python(col['data_type'], col['is_nullable']),
                'SqlAlchemyType': map_postgres_to_sqlalchemy(col['data_type'], col['is_nullable']),
                'IsPrimaryKey': col.get('is_primary_key', False),
                'IsForeignKey': col.get('is_foreign_key', False),
                'IsNullable': col['is_nullable']
            }
            columns.append(col_data)
            
            if not col_data['IsPrimaryKey']:
                non_primary_columns.append(col_data)
            elif primary_key is None:
                primary_key = col_data
        
        # Default primary key if none found
        if primary_key is None:
            primary_key = {
                'Name': 'id',
                'NameSnake': 'id',
                'NamePascal': 'Id',
                'NameCamel': 'id',
                'PythonType': 'UUID',
                'SqlAlchemyType': 'UUID(as_uuid=True)',
                'IsPrimaryKey': True
            }
        
        return {
            'TableName': table['name'],
            'TableNameSnake': snake_case(table['name']),
            'TableNamePascal': pascal_case(table['name']),
            'TableNameCamel': camel_case(table['name']),
            'Columns': columns,
            'NonPrimaryColumns': non_primary_columns,
            'PrimaryKey': primary_key,
            'PrimaryKeys': table.get('primary_keys', []),
            'ForeignKeys': table.get('foreign_keys', []),
            'Group': group,
            'GroupNamespace': f".{group.lower()}" if group != 'General' else "",
            'GroupPath': f"/{group.lower()}" if group != 'General' else ""
        }
    
    def _generate_entity(self, table: Dict[str, Any], group: str = 'General') -> str:
        """Generate domain entity."""
        template = self.env.get_template('core/entity.py.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def _generate_repository_interface(self, table: Dict[str, Any], group: str = 'General') -> str:
        """Generate repository interface."""
        template = self.env.get_template('core/repository_interface.py.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def _generate_exceptions(self, table: Dict[str, Any], group: str = 'General') -> str:
        """Generate domain exceptions."""
        template = self.env.get_template('core/exceptions.py.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def _generate_sqlalchemy_model(self, table: Dict[str, Any], group: str = 'General') -> str:
        """Generate SQLAlchemy model."""
        template = self.env.get_template('infrastructure/sqlalchemy_model.py.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def _generate_repository_impl(self, table: Dict[str, Any], group: str = 'General') -> str:
        """Generate repository implementation."""
        template = self.env.get_template('infrastructure/repository_impl.py.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def _generate_dto(self, table: Dict[str, Any], group: str = 'General') -> str:
        """Generate DTOs."""
        template = self.env.get_template('application/dto.py.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def _generate_service(self, table: Dict[str, Any], group: str = 'General') -> str:
        """Generate service."""
        template = self.env.get_template('application/service.py.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def _generate_router(self, table: Dict[str, Any], group: str = 'General') -> str:
        """Generate FastAPI router."""
        template = self.env.get_template('api/router.py.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def _generate_dependencies(self, table: Dict[str, Any], group: str = 'General') -> str:
        """Generate dependency injection."""
        template = self.env.get_template('api/dependencies.py.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def _generate_schema(self, table: Dict[str, Any], group: str = 'General') -> str:
        """Generate Pydantic schemas."""
        template = self.env.get_template('api/schema.py.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def _generate_common_files(
        self, 
        schema: Dict[str, Any], 
        solution_name: str, 
        connection_string: str,
        table_groups: Dict[str, List[str]]
    ) -> Dict[str, str]:
        """Generate common application files."""
        files = {}
        
        # Prepare grouped tables data
        grouped_tables = {}
        for group, table_names in table_groups.items():
            grouped_tables[group] = []
            for table_name in table_names:
                for table in schema['tables']:
                    if table['name'] == table_name:
                        grouped_tables[group].append({
                            'TableNamePascal': pascal_case(table['name']),
                            'TableNameSnake': snake_case(table['name']),
                            'GroupNamespace': f".{group.lower()}" if group != 'General' else "",
                            'GroupPath': f"/{group.lower()}" if group != 'General' else ""
                        })
                        break
        
        # Common utilities
        files["src/common/result.py"] = self._render_template('common/result.py.j2')
        files["src/common/pagination.py"] = self._render_template('common/pagination.py.j2')
        files["src/common/logging.py"] = self._render_template('common/logging.py.j2')
        
        # Infrastructure base
        files["src/infrastructure/database/session.py"] = self._render_template(
            'infrastructure/database_config.py.j2'
        )
        files["src/infrastructure/database/base.py"] = "from sqlalchemy.ext.declarative import declarative_base\n\nBase = declarative_base()\n"
        
        # Unit of Work
        files["src/infrastructure/database/unit_of_work.py"] = self._render_template(
            'infrastructure/unit_of_work.py.j2', 
            Tables=[
                {
                    'TableNamePascal': pascal_case(table['name']),
                    'TableNameSnake': snake_case(table['name']),
                    'GroupNamespace': f".{table_groups.get(table['name'], {}).get('group', 'general')}" 
                                    if table['name'] in [t for tables in table_groups.values() for t in tables] 
                                    else ""
                }
                for table in schema['tables']
            ]
        )
        
        # Main application
        files["src/api/main.py"] = self._render_template(
            'api/main.py.j2',
            SolutionName=solution_name,
            GroupedTables=grouped_tables
        )
        
        # Middleware
        files["src/api/middleware/correlation.py"] = self._render_template('api/middleware_correlation.py.j2')
        files["src/api/middleware/request_logging.py"] = self._render_template('api/middleware_request_logging.py.j2')
        files["src/api/middleware/error_handler.py"] = self._render_template('api/middleware_error_handler.py.j2')
        
        # __init__.py files
        init_files = [
            "src/__init__.py",
            "src/core/__init__.py",
            "src/core/entities/__init__.py",
            "src/core/interfaces/__init__.py",
            "src/core/exceptions/__init__.py",
            "src/infrastructure/__init__.py",
            "src/infrastructure/database/__init__.py",
            "src/infrastructure/database/models/__init__.py",
            "src/infrastructure/database/repositories/__init__.py",
            "src/application/__init__.py",
            "src/application/dto/__init__.py",
            "src/application/services/__init__.py",
            "src/api/__init__.py",
            "src/api/v1/__init__.py",
            "src/api/v1/routers/__init__.py",
            "src/api/v1/dependencies/__init__.py",
            "src/api/schemas/__init__.py",
            "src/api/middleware/__init__.py",
            "src/common/__init__.py",
            "tests/__init__.py",
            "tests/unit/__init__.py",
            "tests/integration/__init__.py"
        ]
        
        for init_file in init_files:
            files[init_file] = ""
        
        # Group-specific __init__.py files
        for group in table_groups.keys():
            if group != 'General':
                group_path = group.lower()
                group_init_files = [
                    f"src/core/entities/{group_path}/__init__.py",
                    f"src/core/interfaces/{group_path}/__init__.py",
                    f"src/core/exceptions/{group_path}/__init__.py",
                    f"src/infrastructure/database/models/{group_path}/__init__.py",
                    f"src/infrastructure/database/repositories/{group_path}/__init__.py",
                    f"src/application/dto/{group_path}/__init__.py",
                    f"src/application/services/{group_path}/__init__.py",
                    f"src/api/v1/routers/{group_path}/__init__.py",
                    f"src/api/v1/dependencies/{group_path}/__init__.py",
                    f"src/api/schemas/{group_path}/__init__.py"
                ]
                for init_file in group_init_files:
                    files[init_file] = ""
        
        return files
    
    def _generate_config_files(self, solution_name: str, connection_string: str) -> Dict[str, str]:
        """Generate configuration files."""
        files = {}
        
        # Generate a secure secret key
        secret_key = secrets.token_urlsafe(32)
        
        # Settings
        files["src/config/settings.py"] = self._render_template(
            'config/settings.py.j2',
            SolutionName=solution_name,
            ConnectionString=normalize_connection_string_for_python(connection_string),
            SecretKey=secret_key
        )
        
        files["src/config/__init__.py"] = ""
        
        # pyproject.toml
        files["pyproject.toml"] = self._render_template(
            'config/pyproject.toml.j2',
            SolutionName=solution_name
        )
        
        # Main entry point
        files["main.py"] = self._render_template(
            'config/main.py.j2',
            SolutionName=solution_name
        )
        
        # AI Assistant Rules
        files["CLAUDE.md"] = self._render_template(
            'config/claude_rules.md.j2',
            SolutionName=solution_name
        )
        files[".cursorrules"] = self._render_template(
            'config/cursor_rules.md.j2',
            SolutionName=solution_name
        )
        
        # Environment files
        files[".env.example"] = f"""# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/database

# Security
SECRET_KEY={secret_key}

# Application
DEBUG=true
ENVIRONMENT=development

# Optional: Redis
# REDIS_URL=redis://localhost:6379

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
"""
        
        # Alembic configuration
        files["alembic.ini"] = """# A generic, single database configuration.

[alembic]
# path to migration scripts
script_location = migrations

# template used to generate migration file names; The default value is %%(rev)s_%%(slug)s
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d_%%(minute).2d_%%(second).2d_%%(rev)s_%%(slug)s

# sys.path path, will be prepended to sys.path if present.
prepend_sys_path = .

# timezone to use when rendering the date within the migration file
timezone = UTC

# max length of characters to apply to the "slug" field
truncate_slug_length = 40

# set to 'true' to run the environment during the 'revision' command, regardless
# of autogenerate
revision_environment = false

# set to 'true' to allow .pyc and .pyo files without a source .py file to be detected
# as revisions in the versions/ directory
sourceless = false

# version path separator; As mentioned above, this is the character used to split
# version_locations. The default within new alembic.ini files is "os", which uses
# os.pathsep. If this key is omitted entirely, it falls back to the legacy
# behavior of splitting on spaces and/or commas.
version_path_separator = :

# the output encoding used when revision files are written from script.py.mako
output_encoding = utf-8

sqlalchemy.url = driver://user:pass@localhost/dbname


[post_write_hooks]
# post_write_hooks defines scripts or Python functions that are run
# on newly generated revision scripts.  See the documentation for further
# detail and examples

# format using "black" - use the console_scripts runner, against the "black" entrypoint
# hooks = black
# black.type = console_scripts
# black.entrypoint = black
# black.options = -l 79 REVISION_SCRIPT_FILENAME

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
        
        return files
    
    def _generate_docker_files(self, solution_name: str) -> Dict[str, str]:
        """Generate Docker and deployment files."""
        files = {}
        
        files["Dockerfile"] = self._render_template(
            'docker/Dockerfile.j2',
            SolutionName=solution_name
        )
        
        files["docker-compose.yml"] = self._render_template(
            'docker/docker-compose.yml.j2',
            SolutionName=solution_name
        )
        
        # Makefile
        files["Makefile"] = f""".PHONY: help install run test migrate format lint clean

help:
\t@echo "Available commands:"
\t@echo "  install    Install dependencies with uv"
\t@echo "  run        Run the application"
\t@echo "  test       Run tests"
\t@echo "  migrate    Run database migrations"
\t@echo "  format     Format code"
\t@echo "  lint       Lint code"
\t@echo "  clean      Clean cache files"

install:
\tuv sync

run:
\tuv run python main.py

test:
\tuv run pytest tests/ -v --cov=src --cov-report=html

migrate:
\tuv run alembic upgrade head

format:
\tuv run ruff format src/ tests/

lint:
\tuv run ruff check src/ tests/
\tuv run mypy src/

clean:
\tfind . -type d -name __pycache__ -exec rm -rf {{}} +
\tfind . -type f -name "*.pyc" -delete
\trm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/

docker-build:
\tdocker build -t {solution_name.lower()}:latest .

docker-run:
\tdocker-compose up -d

docker-logs:
\tdocker-compose logs -f app

docker-stop:
\tdocker-compose down
"""
        
        # .gitignore
        files[".gitignore"] = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.idea/
.vscode/
*.swp
*.swo
*~

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Database
*.db
*.sqlite
*.sqlite3

# Logs
*.log
logs/

# Docker
.dockerignore

# Alembic
# Keep migrations folder but ignore specific files if needed

# FastAPI specific
.pytest_cache/

# uv
uv.lock

# MyPy
.mypy_cache/
.dmypy.json
dmypy.json
"""
        
        # README.md
        files["README.md"] = f"""# {solution_name}

Auto-generated FastAPI application with Clean Architecture.

## Features

- 🚀 **FastAPI**: Modern, fast web framework for building APIs
- 📊 **PostgreSQL**: Robust relational database
- 🏗️ **Clean Architecture**: Proper separation of concerns
- 📝 **SQLAlchemy 2.0**: Modern async ORM
- 🔒 **Security**: JWT authentication ready
- 📖 **Documentation**: Auto-generated OpenAPI docs
- 🐳 **Docker**: Containerized deployment
- 🧪 **Testing**: Comprehensive test setup
- 📊 **Monitoring**: Health checks and logging

## Quick Start

### Requirements

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager
- PostgreSQL
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd {solution_name.lower()}
```

2. Install dependencies:
```bash
make install
```

3. Set up environment:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Run database migrations:
```bash
make migrate
```

5. Start the application:
```bash
make run
# Or run directly with uvicorn:
uv run uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`.

- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## Project Structure

```
{solution_name.lower()}/
├── src/
│   ├── core/              # Domain layer
│   ├── infrastructure/    # Data access layer
│   ├── application/       # Business logic layer
│   ├── api/              # Presentation layer
│   ├── common/           # Shared utilities
│   └── config/           # Configuration
├── tests/                # Test suite
├── migrations/           # Database migrations
├── docker/              # Docker configuration
└── docs/                # Documentation
```

## API Endpoints

The API provides the following endpoints for each entity:

- `GET /api/v1/{{entity}}/` - List all entities
- `GET /api/v1/{{entity}}/{{id}}` - Get entity by ID
- `GET /api/v1/{{entity}}/paginated` - Get paginated entities
- `POST /api/v1/{{entity}}/` - Create new entity
- `PUT /api/v1/{{entity}}/{{id}}` - Update entity
- `DELETE /api/v1/{{entity}}/{{id}}` - Delete entity

## Development

### Commands

- `make install` - Install dependencies
- `make run` - Run the development server
- `make test` - Run tests
- `make lint` - Lint code
- `make format` - Format code
- `make migrate` - Run database migrations

### Testing

Run the test suite:

```bash
make test
```

Run specific tests:

```bash
uv run pytest tests/unit/
uv run pytest tests/integration/
```

### Database Migrations

Create a new migration:

```bash
uv run alembic revision --autogenerate -m "Description"
```

Apply migrations:

```bash
uv run alembic upgrade head
```

## Deployment

### Docker

Build and run with Docker:

```bash
make docker-build
make docker-run
```

### Production

1. Set environment variables:
```bash
export ENVIRONMENT=production
export DEBUG=false
export DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
```

2. Run with production server:
```bash
uv run gunicorn src.api.main:app -w 4 -k uvicorn.workers.UnicornWorker
```

## Configuration

Configuration is handled through environment variables. See `.env.example` for all available options.

Key settings:

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Secret key for JWT tokens
- `DEBUG`: Enable debug mode
- `ENVIRONMENT`: Environment (development/production)

## License

This project is generated by the FastAPI Generator.
"""
        
        return files
    
    def _render_template(self, template_name: str, **kwargs) -> str:
        """Render a template with the given context."""
        template = self.env.get_template(template_name)
        return template.render(**kwargs)
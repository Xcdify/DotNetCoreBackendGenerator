from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from utils import pascal_case, snake_case, camel_case, map_postgres_to_csharp, get_primary_key_type, normalize_connection_string

class DotNetCodeGenerator:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader('templates'),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def generate_application(self, schema: Dict[str, Any], 
                           connection_string: str = "",
                           progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict[str, str]:
        files = {}
        total_tables = len(schema['tables'])
        current_progress = 0
        
        if progress_callback:
            progress_callback(0, "Starting generation...")
        
        for idx, table in enumerate(schema['tables']):
            if progress_callback:
                progress_callback(int((idx / total_tables) * 70), f"Processing table: {table['name']}")
            
            table_data = self._prepare_table_data(table)
            
            files[f"src/Core/Entities/{table_data['TableNamePascal']}.cs"] = self.generate_entity(table)
            
            files[f"src/Core/Interfaces/I{table_data['TableNamePascal']}Repository.cs"] = self.generate_repository_interface(table)
            
            files[f"src/Infrastructure/Data/{table_data['TableNamePascal']}Repository.cs"] = self.generate_repository_implementation(table)
            
            files[f"src/WebApi/Controllers/{table_data['TableNamePascal']}Controller.cs"] = self.generate_controller(table)
            
            # Generate Application services
            files[f"src/Application/Interfaces/I{table_data['TableNamePascal']}Service.cs"] = self.generate_application_service_interface(table)
            files[f"src/Application/Services/{table_data['TableNamePascal']}Service.cs"] = self.generate_application_service(table)
            
            # Generate DTOs and validators (optional)
            files[f"src/Application/DTOs/{table_data['TableNamePascal']}/Create{table_data['TableNamePascal']}Dto.cs"] = self.generate_create_dto(table)
            files[f"src/Application/DTOs/{table_data['TableNamePascal']}/Update{table_data['TableNamePascal']}Dto.cs"] = self.generate_update_dto(table)
            files[f"src/Application/Validators/{table_data['TableNamePascal']}/{table_data['TableNamePascal']}DtoValidator.cs"] = self.generate_dto_validator(table)
        
        if progress_callback:
            progress_callback(80, "Generating Program.cs and configuration files...")
        
        files["src/WebApi/Program.cs"] = self._generate_program(schema)
        files["src/WebApi/appsettings.json"] = self._generate_appsettings(connection_string)
        files["src/WebApi/appsettings.Development.json"] = self._generate_appsettings_dev()
        
        # Generate project files with proper references
        files["src/Core/Core.csproj"] = self._generate_core_csproj()
        files["src/Application/Application.csproj"] = self._generate_application_csproj()
        files["src/Infrastructure/Infrastructure.csproj"] = self._generate_infrastructure_csproj()
        files["src/WebApi/WebApi.csproj"] = self._generate_webapi_csproj()
        
        # Generate solution file
        files["GeneratedApp.sln"] = self._generate_solution()
        
        # Generate DI extension methods
        files["src/Application/Extensions/ServiceCollectionExtensions.cs"] = self._generate_application_di_extensions(schema)
        files["src/Infrastructure/Extensions/ServiceCollectionExtensions.cs"] = self._generate_infrastructure_di_extensions(schema)
        
        files["src/Application/README.md"] = "# Application Layer\n\nPlace your use cases and application services here."
        files["tests/UnitTests/README.md"] = "# Unit Tests\n\nPlace your unit tests here."
        files["tests/IntegrationTests/README.md"] = "# Integration Tests\n\nPlace your integration tests here."
        
        files[".gitignore"] = self._generate_gitignore()
        files["README.md"] = self._generate_readme()
        
        if progress_callback:
            progress_callback(100, "Generation complete!")
        
        return files
    
    def _prepare_table_data(self, table: Dict[str, Any]) -> Dict[str, Any]:
        columns = []
        non_primary_columns = []
        primary_key = None
        
        for col in table['columns']:
            col_data = {
                'Name': col['name'],
                'NameSnake': snake_case(col['name']),
                'NamePascal': pascal_case(col['name']),
                'NameCamel': camel_case(col['name']),
                'CSharpType': map_postgres_to_csharp(col['data_type'], col['is_nullable']),
                'IsPrimaryKey': col.get('is_primary_key', False),
                'IsForeignKey': col.get('is_foreign_key', False),
                'IsNullable': col['is_nullable']
            }
            columns.append(col_data)
            
            if not col_data['IsPrimaryKey']:
                non_primary_columns.append(col_data)
            elif primary_key is None:
                primary_key = col_data
        
        if primary_key is None and columns:
            primary_key = {
                'Name': 'id',
                'NameSnake': 'id',
                'NamePascal': 'Id',
                'NameCamel': 'id',
                'CSharpType': 'int',
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
            'ForeignKeys': table.get('foreign_keys', [])
        }
    
    def generate_entity(self, table: Dict[str, Any]) -> str:
        template = self.env.get_template('entity.cs.j2')
        data = self._prepare_table_data(table)
        return template.render(**data)
    
    def generate_repository_interface(self, table: Dict[str, Any]) -> str:
        template = self.env.get_template('repository_interface.cs.j2')
        data = self._prepare_table_data(table)
        return template.render(**data)
    
    def generate_repository_implementation(self, table: Dict[str, Any]) -> str:
        template = self.env.get_template('repository_dapper.cs.j2')
        data = self._prepare_table_data(table)
        return template.render(**data)
    
    def generate_controller(self, table: Dict[str, Any]) -> str:
        template = self.env.get_template('controller.cs.j2')
        data = self._prepare_table_data(table)
        return template.render(**data)
    
    def generate_application_service_interface(self, table: Dict[str, Any]) -> str:
        template = self.env.get_template('application_service_interface.cs.j2')
        data = self._prepare_table_data(table)
        return template.render(**data)
    
    def generate_application_service(self, table: Dict[str, Any]) -> str:
        template = self.env.get_template('application_service.cs.j2')
        data = self._prepare_table_data(table)
        return template.render(**data)
    
    def generate_create_dto(self, table: Dict[str, Any]) -> str:
        template = self.env.get_template('create_dto.cs.j2')
        data = self._prepare_table_data(table)
        return template.render(**data)
    
    def generate_update_dto(self, table: Dict[str, Any]) -> str:
        template = self.env.get_template('update_dto.cs.j2')
        data = self._prepare_table_data(table)
        return template.render(**data)
    
    def generate_dto_validator(self, table: Dict[str, Any]) -> str:
        template = self.env.get_template('dto_validator.cs.j2')
        data = self._prepare_table_data(table)
        return template.render(**data)
    
    def _generate_program(self, schema: Dict[str, Any]) -> str:
        template = self.env.get_template('program.cs.j2')
        tables = []
        for table in schema['tables']:
            tables.append({
                'TableNamePascal': pascal_case(table['name'])
            })
        return template.render(Tables=tables)
    
    def _generate_appsettings(self, connection_string: str = "") -> str:
        template = self.env.get_template('appsettings.json.j2')
        normalized_conn_str = normalize_connection_string(connection_string)
        return template.render(connection_string=normalized_conn_str)
    
    def _generate_appsettings_dev(self) -> str:
        return """{
  "Logging": {
    "LogLevel": {
      "Default": "Debug",
      "Microsoft.AspNetCore": "Debug"
    }
  }
}"""
    
    def _generate_core_csproj(self) -> str:
        template = self.env.get_template('core.csproj.j2')
        return template.render()
    
    def _generate_application_csproj(self) -> str:
        template = self.env.get_template('application.csproj.j2')
        return template.render()
    
    def _generate_infrastructure_csproj(self) -> str:
        template = self.env.get_template('infrastructure.csproj.j2')
        return template.render()
    
    def _generate_webapi_csproj(self) -> str:
        template = self.env.get_template('webapi.csproj.j2')
        return template.render()
    
    def _generate_solution(self) -> str:
        template = self.env.get_template('solution.sln.j2')
        return template.render()
    
    def _generate_application_di_extensions(self, schema: Dict[str, Any]) -> str:
        template = self.env.get_template('application_di_extensions.cs.j2')
        tables = []
        for table in schema['tables']:
            tables.append({
                'TableNamePascal': pascal_case(table['name'])
            })
        return template.render(Tables=tables)
    
    def _generate_infrastructure_di_extensions(self, schema: Dict[str, Any]) -> str:
        template = self.env.get_template('infrastructure_di_extensions.cs.j2')
        tables = []
        for table in schema['tables']:
            tables.append({
                'TableNamePascal': pascal_case(table['name'])
            })
        return template.render(Tables=tables)
    
    def _generate_gitignore(self) -> str:
        return """## Ignore Visual Studio temporary files, build results, and
## files generated by popular Visual Studio add-ons.

# User-specific files
*.rsuser
*.suo
*.user
*.userosscache
*.sln.docstates

# Build results
[Dd]ebug/
[Dd]ebugPublic/
[Rr]elease/
[Rr]eleases/
x64/
x86/
[Ww][Ii][Nn]32/
[Aa][Rr][Mm]/
[Aa][Rr][Mm]64/
bld/
[Bb]in/
[Oo]bj/
[Ll]og/
[Ll]ogs/

# Visual Studio 2015/2017 cache/options directory
.vs/

# .NET Core
project.lock.json
project.fragment.lock.json
artifacts/

# Files built by Visual Studio
*_i.c
*_p.c
*_h.h
*.ilk
*.meta
*.obj
*.iobj
*.pch
*.pdb
*.ipdb
*.pgc
*.pgd
*.rsp
*.sbr
*.tlb
*.tli
*.tlh
*.tmp
*.tmp_proj
*_wpftmp.csproj
*.log
*.tlog
*.vspscc
*.vssscc
.builds
*.pidb
*.svclog
*.scc

# Visual Studio profiler
*.psess
*.vsp
*.vspx
*.sap

# Visual Studio Trace Files
*.e2e

# ReSharper is a .NET coding add-in
_ReSharper*/
*.[Rr]e[Ss]harper
*.DotSettings.user

# Visual Studio code coverage results
*.coverage
*.coveragexml

# NuGet
*.nupkg
*.snupkg
**/[Pp]ackages/*
!**/[Pp]ackages/build/
*.nuget.props
*.nuget.targets

# Node.js
node_modules/

# Python
__pycache__/
*.py[cod]
*$py.class

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Visual Studio Code
.vscode/

# JetBrains Rider
.idea/
*.sln.iml

# macOS
.DS_Store

# Windows
Thumbs.db
ehthumbs.db
Desktop.ini"""
    
    def _generate_readme(self) -> str:
        return """# Generated .NET Core Clean Architecture Application

This application was generated from your PostgreSQL database schema.

## Prerequisites

- .NET Core 9.0 SDK
- PostgreSQL database

## Setup

1. Update the connection string in `src/WebApi/appsettings.json`
2. Navigate to the WebApi directory: `cd src/WebApi`
3. Restore dependencies: `dotnet restore`
4. Build the application: `dotnet build`
5. Run the application: `dotnet run`

## Architecture

This application follows Clean Architecture principles:

- **Core**: Contains entities and repository interfaces (no dependencies)
- **Infrastructure**: Contains data access implementations using Dapper
- **Application**: Contains use cases and business logic (placeholder)
- **WebApi**: Contains controllers and API configuration

## API Documentation

When running in development mode, Swagger UI is available at:
`https://localhost:5001/swagger`

## Testing

- Unit tests: `tests/UnitTests/`
- Integration tests: `tests/IntegrationTests/`

Run tests with: `dotnet test`

## Generated with

[.NET Core App Generator](https://github.com/yourusername/netcore-generator)
"""
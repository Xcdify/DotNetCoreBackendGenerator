from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from utils import pascal_case, snake_case, camel_case, map_postgres_to_csharp, get_primary_key_type, normalize_connection_string
from fastapi_generator import FastAPICodeGenerator

class DotNetCodeGenerator:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader('templates'),
            trim_blocks=False,
            lstrip_blocks=False,
            keep_trailing_newline=True
        )
    
    def generate_application(self, schema: Dict[str, Any], 
                           connection_string: str = "",
                           table_groups: Optional[Dict[str, List[str]]] = None,
                           solution_name: str = "GeneratedApp",
                           progress_callback: Optional[Callable[[int, str], None]] = None) -> Dict[str, str]:
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
            progress_callback(0, "Starting generation...")
        
        for idx, table in enumerate(schema['tables']):
            if progress_callback:
                progress_callback(int((idx / total_tables) * 70), f"Processing table: {table['name']}")
            
            # Get the group for this table
            group = table_to_group.get(table['name'], 'General')
            
            table_data = self._prepare_table_data(table, group)
            
            # Generate files with group folders
            files[f"src/Core/Entities/{group}/{table_data['TableNamePascal']}.cs"] = self.generate_entity(table, group)
            
            files[f"src/Core/Interfaces/{group}/I{table_data['TableNamePascal']}Repository.cs"] = self.generate_repository_interface(table, group)
            
            files[f"src/Infrastructure/Data/{group}/{table_data['TableNamePascal']}Repository.cs"] = self.generate_repository_implementation(table, group)
            
            files[f"src/WebApi/Controllers/{group}/{table_data['TableNamePascal']}Controller.cs"] = self.generate_controller(table, group)
            
            # Generate Application services
            files[f"src/Application/Interfaces/{group}/I{table_data['TableNamePascal']}Service.cs"] = self.generate_application_service_interface(table, group)
            files[f"src/Application/Services/{group}/{table_data['TableNamePascal']}Service.cs"] = self.generate_application_service(table, group)
            
            # Generate DTOs and validators (optional)
            files[f"src/Application/DTOs/{group}/{table_data['TableNamePascal']}/Create{table_data['TableNamePascal']}Dto.cs"] = self.generate_create_dto(table, group)
            files[f"src/Application/DTOs/{group}/{table_data['TableNamePascal']}/Update{table_data['TableNamePascal']}Dto.cs"] = self.generate_update_dto(table, group)
            files[f"src/Application/Validators/{group}/{table_data['TableNamePascal']}/{table_data['TableNamePascal']}DtoValidator.cs"] = self.generate_dto_validator(table, group)
            
            # Generate AutoMapper Profile per table
            files[f"src/Application/Mappings/{group}/{table_data['TableNamePascal']}Profile.cs"] = self.generate_mapping_profile(table, group)

            # Generate pagination DTOs
            files[f"src/WebApi/DTOs/{group}/{table_data['TableNamePascal']}FilterRequest.cs"] = self.generate_pagination_dto(table, group)
        
        if progress_callback:
            progress_callback(80, "Generating Program.cs and configuration files...")
        
        # Generate common Result and Error classes
        files["src/Core/Common/Result.cs"] = self._generate_result_class()
        files["src/Core/Common/Error.cs"] = self._generate_error_class()
        files["src/Core/Common/Examples/SensitiveDataExamples.cs"] = self._generate_sensitive_data_examples()
        
        # Generate common pagination response class
        files["src/WebApi/DTOs/Common/PagedResponse.cs"] = self._generate_paged_response_class()
        
        # Generate Serilog configuration and middleware
        files["src/WebApi/Configuration/SerilogConfiguration.cs"] = self._generate_serilog_configuration(solution_name)
        files["src/WebApi/Middleware/CorrelationMiddleware.cs"] = self._generate_correlation_middleware()
        files["src/WebApi/Middleware/RequestLoggingMiddleware.cs"] = self._generate_request_logging_middleware()
        
        files["src/WebApi/Program.cs"] = self._generate_program(schema, solution_name)
        files["src/WebApi/appsettings.json"] = self._generate_appsettings(connection_string, solution_name)
        files["src/WebApi/appsettings.Development.json"] = self._generate_appsettings_dev()
        
        # Generate project files with proper references
        files["src/Core/Core.csproj"] = self._generate_core_csproj()
        files["src/Application/Application.csproj"] = self._generate_application_csproj()
        files["src/Infrastructure/Infrastructure.csproj"] = self._generate_infrastructure_csproj()
        files["src/WebApi/WebApi.csproj"] = self._generate_webapi_csproj()
        
        # Generate solution file with custom name
        files[f"{solution_name}.sln"] = self._generate_solution(solution_name)
        
        # Generate DI extension methods with groups
        grouped_tables = {}
        for group, table_names in table_groups.items():
            grouped_tables[group] = []
            for table_name in table_names:
                for table in schema['tables']:
                    if table['name'] == table_name:
                        grouped_tables[group].append({
                            'TableNamePascal': pascal_case(table['name'])
                        })
                        break
        
        files["src/Application/Extensions/ServiceCollectionExtensions.cs"] = self._generate_application_di_extensions(grouped_tables)
        files["src/Infrastructure/Extensions/ServiceCollectionExtensions.cs"] = self._generate_infrastructure_di_extensions(grouped_tables)
        # Common Infrastructure utilities
        files["src/Infrastructure/Data/Common/SqlQueryBuilder.cs"] = self._generate_sql_query_builder()
        
        files["src/Application/README.md"] = "# Application Layer\n\nPlace your use cases and application services here."
        files["tests/UnitTests/README.md"] = "# Unit Tests\n\nPlace your unit tests here."
        files["tests/IntegrationTests/README.md"] = "# Integration Tests\n\nPlace your integration tests here."
        
        files[".gitignore"] = self._generate_gitignore()
        files["README.md"] = self._generate_readme(solution_name)
        
        # Add AI assistant configuration files
        files[".cursorrules"] = self._generate_cursorrules(solution_name)
        files["CLAUDE.md"] = self._generate_claude_md(solution_name)
        
        if progress_callback:
            progress_callback(100, "Generation complete!")
        
        return files
    
    def _prepare_table_data(self, table: Dict[str, Any], group: str = 'General') -> Dict[str, Any]:
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
            'ForeignKeys': table.get('foreign_keys', []),
            'Group': group,
            'GroupNamespace': f".{group}" if group != 'General' else ""
        }
    
    def generate_entity(self, table: Dict[str, Any], group: str = 'General') -> str:
        template = self.env.get_template('dotnetapi/core/entity.cs.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def generate_repository_interface(self, table: Dict[str, Any], group: str = 'General') -> str:
        template = self.env.get_template('dotnetapi/infrastructure/repository_interface.cs.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def generate_repository_implementation(self, table: Dict[str, Any], group: str = 'General') -> str:
        template = self.env.get_template('dotnetapi/infrastructure/repository_dapper.cs.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def generate_controller(self, table: Dict[str, Any], group: str = 'General') -> str:
        template = self.env.get_template('dotnetapi/application/controller.cs.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def generate_application_service_interface(self, table: Dict[str, Any], group: str = 'General') -> str:
        template = self.env.get_template('dotnetapi/application/application_service_interface.cs.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def generate_application_service(self, table: Dict[str, Any], group: str = 'General') -> str:
        template = self.env.get_template('dotnetapi/application/application_service.cs.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)

    def generate_mapping_profile(self, table: Dict[str, Any], group: str = 'General') -> str:
        template = self.env.get_template('dotnetapi/application/mapping_profile.cs.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def generate_create_dto(self, table: Dict[str, Any], group: str = 'General') -> str:
        template = self.env.get_template('dotnetapi/dtos/create_dto.cs.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def generate_update_dto(self, table: Dict[str, Any], group: str = 'General') -> str:
        template = self.env.get_template('dotnetapi/dtos/update_dto.cs.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def generate_dto_validator(self, table: Dict[str, Any], group: str = 'General') -> str:
        template = self.env.get_template('dotnetapi/dtos/dto_validator.cs.j2')
        data = self._prepare_table_data(table, group)
        return template.render(**data)
    
    def generate_pagination_dto(self, table: Dict[str, Any], group: str = 'General') -> str:
        template = self.env.get_template('dotnetapi/dtos/pagination_request.cs.j2')
        data = self._prepare_table_data(table, group)
        # Add DataType info for columns to enable smart filtering
        for col in data['Columns']:
            col['DataType'] = next((c['data_type'] for c in table['columns'] if c['name'] == col['Name']), 'text')
        for col in data['NonPrimaryColumns']:
            col['DataType'] = next((c['data_type'] for c in table['columns'] if c['name'] == col['Name']), 'text')
        return template.render(**data)
    
    def _generate_program(self, schema: Dict[str, Any], solution_name: str = "GeneratedApp") -> str:
        template = self.env.get_template('dotnetapi/application/program.cs.j2')
        tables = []
        for table in schema['tables']:
            tables.append({
                'TableNamePascal': pascal_case(table['name'])
            })
        return template.render(Tables=tables, SolutionName=solution_name)
    
    def _generate_appsettings(self, connection_string: str = "", solution_name: str = "GeneratedApp") -> str:
        template = self.env.get_template('dotnetapi/configuration/appsettings.json.j2')
        normalized_conn_str = normalize_connection_string(connection_string)
        return template.render(connection_string=normalized_conn_str, SolutionName=solution_name)
    
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
        template = self.env.get_template('dotnetapi/project/core.csproj.j2')
        return template.render()
    
    def _generate_application_csproj(self) -> str:
        template = self.env.get_template('dotnetapi/project/application.csproj.j2')
        return template.render()
    
    def _generate_infrastructure_csproj(self) -> str:
        template = self.env.get_template('dotnetapi/project/infrastructure.csproj.j2')
        return template.render()
    
    def _generate_webapi_csproj(self) -> str:
        template = self.env.get_template('dotnetapi/project/webapi.csproj.j2')
        return template.render()
    
    def _generate_solution(self, solution_name: str = "GeneratedApp") -> str:
        template = self.env.get_template('dotnetapi/project/solution.sln.j2')
        return template.render(SolutionName=solution_name)
    
    def _generate_application_di_extensions(self, grouped_tables: Dict[str, List[Dict]]) -> str:
        template = self.env.get_template('dotnetapi/application/application_di_extensions.cs.j2')
        return template.render(Groups=grouped_tables)
    
    def _generate_infrastructure_di_extensions(self, grouped_tables: Dict[str, List[Dict]]) -> str:
        template = self.env.get_template('dotnetapi/infrastructure/infrastructure_di_extensions.cs.j2')
        return template.render(Groups=grouped_tables)

    def _generate_sql_query_builder(self) -> str:
        template = self.env.get_template('dotnetapi/infrastructure/sql_query_builder.cs.j2')
        return template.render()
    
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
    
    def _generate_readme(self, solution_name: str = "GeneratedApp") -> str:
        return f"""# {solution_name} - .NET Core Clean Architecture Application

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

## AI Assistant Configuration

This project includes configuration files for AI coding assistants:

- **`.cursorrules`**: Configuration for Cursor AI IDE with project-specific coding standards and patterns
- **`CLAUDE.md`**: Instructions for Claude AI assistant to ensure consistent code generation

These files help AI assistants understand the project structure, coding conventions, and architectural patterns to provide better code suggestions and maintain consistency across the codebase.

## Testing

- Unit tests: `tests/UnitTests/`
- Integration tests: `tests/IntegrationTests/`

Run tests with: `dotnet test`

## Generated with

[.NET Core App Generator](https://github.com/yourusername/netcore-generator)
"""

    def _generate_result_class(self) -> str:
        template = self.env.get_template('dotnetapi/core/result.cs.j2')
        return template.render()
    
    def _generate_error_class(self) -> str:
        template = self.env.get_template('dotnetapi/core/error.cs.j2')
        return template.render()

    def _generate_serilog_configuration(self, solution_name: str = "GeneratedApp") -> str:
        template = self.env.get_template('dotnetapi/configuration/serilog_configuration.cs.j2')
        return template.render(SolutionName=solution_name)
    
    def _generate_correlation_middleware(self) -> str:
        template = self.env.get_template('dotnetapi/middleware/correlation_middleware.cs.j2')
        return template.render()
    
    def _generate_request_logging_middleware(self) -> str:
        template = self.env.get_template('dotnetapi/middleware/request_logging_middleware.cs.j2')
        return template.render()
    
    def _generate_sensitive_data_examples(self) -> str:
        template = self.env.get_template('dotnetapi/configuration/sensitive_data_examples.cs.j2')
        return template.render()
    
    def _generate_paged_response_class(self) -> str:
        return """using System.Collections.Generic;

namespace WebApi.DTOs.Common
{
    public class PagedResponse<T>
    {
        public IEnumerable<T> Data { get; set; }
        public int CurrentPage { get; set; }
        public int PageSize { get; set; }
        public int TotalPages { get; set; }
        public int TotalCount { get; set; }
        public bool HasPrevious => CurrentPage > 1;
        public bool HasNext => CurrentPage < TotalPages;
        
        public PagedResponse(IEnumerable<T> data, int count, int pageNumber, int pageSize)
        {
            Data = data;
            TotalCount = count;
            CurrentPage = pageNumber;
            PageSize = pageSize;
            TotalPages = (int)System.Math.Ceiling(count / (double)pageSize);
        }
    }
}"""
    
    def _generate_cursorrules(self, solution_name: str = "GeneratedApp") -> str:
        """Generate .cursorrules file for Cursor AI"""
        template = self.env.get_template('dotnetapi/ai_assistants/cursorrules.txt.j2')
        return template.render(SolutionName=solution_name)
    
    def _generate_claude_md(self, solution_name: str = "GeneratedApp") -> str:
        """Generate CLAUDE.md file for Claude AI"""
        template = self.env.get_template('dotnetapi/ai_assistants/claude.md.j2')
        return template.render(SolutionName=solution_name)


def create_code_generator(framework: str):
    """
    Factory function to create appropriate code generator based on framework.
    
    Args:
        framework: Either 'dotnet' or 'fastapi'
        
    Returns:
        Code generator instance
    """
    if framework.lower() == 'fastapi':
        return FastAPICodeGenerator()
    elif framework.lower() == 'dotnet':
        return DotNetCodeGenerator()
    else:
        raise ValueError(f"Unsupported framework: {framework}. Choose 'dotnet' or 'fastapi'.")
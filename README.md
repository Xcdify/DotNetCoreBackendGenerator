# .NET Core App Generator

A Python utility using Streamlit and uv that generates a clean architecture .NET Core 9 application from PostgreSQL database schemas.

## Features

- 🗄️ **Database Schema Reading**: Connects to PostgreSQL and reads complete schema
- 🏗️ **Clean Architecture**: Generates properly structured .NET Core 9 application
- 🔧 **Dapper Integration**: Uses Dapper for efficient data access
- 🔎 **Fluent SQL Builder**: Reusable `SqlQueryBuilder` for safe dynamic filtering, search, sort, and pagination
- 📝 **Template-Based Generation**: Customizable Jinja2 templates
- 🎯 **Type Mapping**: Automatic PostgreSQL to C# type conversion
- 📦 **ZIP Download**: Download generated application as ZIP
- 🚀 **Fast Execution**: Uses uv for lightweight Python environment

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer
- PostgreSQL database (for schema reading)

## Installation

1. Clone or download this project
2. Install uv if not already installed:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your database credentials:
   ```
   POSTGRES_CONNECTION_STRING=postgresql://username:password@host:port/database
   ```

## Usage

```bash
# Install dependencies
uv pip install streamlit psycopg2-binary jinja2 pydantic python-dotenv

# Run the application
uv run streamlit run app.py
```

The application will start at `http://localhost:8501`

## How to Use

1. **Enter PostgreSQL Connection String**:
   ```
   postgresql://username:password@host:port/database
   ```

2. **Review Schema**: The app will display all detected tables and columns

3. **Preview Code**: See sample generated entity and repository code

4. **Generate Application**: Click "Generate Application" to create the complete .NET Core project

5. **Download**: Download as ZIP or save to specified folder

## Generated Project Structure

```
generated-app/
├── src/
│   ├── Core/
│   │   ├── Entities/          # Domain entities
│   │   └── Interfaces/        # Repository interfaces
│   ├── Infrastructure/
│   │   └── Data/              # Dapper repository implementations
│   ├── Application/           # Use cases (placeholder)
│   └── WebApi/
│       ├── Controllers/       # API controllers
│       ├── Program.cs         # Application startup
│       └── appsettings.json   # Configuration
└── tests/
    ├── UnitTests/
    └── IntegrationTests/
```

## Type Mapping

| PostgreSQL Type | C# Type |
|----------------|---------|
| integer, serial | int |
| bigint, bigserial | long |
| uuid | Guid |
| text, varchar | string |
| boolean | bool |
| date, timestamp | DateTime |
| numeric, decimal | decimal |
| double precision | double |
| bytea | byte[] |
| json, jsonb | string |
| time | TimeSpan |

Nullable columns are mapped to nullable C# types (e.g., `int?`)

## Generated Code Features

- **Entities**: Clean POCO classes with proper C# types
- **Repositories**: Interface-based design with Dapper implementation
- **Controllers**: RESTful API endpoints with async/await
- **Dependency Injection**: Configured in Program.cs
- **Configuration**: Connection string in appsettings.json
- **Swagger**: API documentation enabled

## Running the Generated Application

1. Navigate to the generated project:
   ```bash
   cd generated-app/src/WebApi
   ```

2. Update connection string in `appsettings.json`

3. Build and run:
   ```bash
   dotnet restore
   dotnet build
   dotnet run
   ```

4. Access Swagger UI at: `https://localhost:5001/swagger`

## Customization

### Modifying Templates

Templates are organized in the `templates/` directory by category. Edit these Jinja2 templates to customize generated code:

**Core Templates:**
- `templates/core/entity.cs.j2` - Entity classes
- `templates/core/error.cs.j2` - Error classes
- `templates/core/result.cs.j2` - Result classes

**Infrastructure Templates:**
- `templates/infrastructure/repository_interface.cs.j2` - Repository interfaces
- `templates/infrastructure/repository_dapper.cs.j2` - Dapper implementations
- `templates/infrastructure/sql_query_builder.cs.j2` - Fluent SQL builder utility
- `templates/infrastructure/infrastructure_di_extensions.cs.j2` - DI configuration

**Application Templates:**
- `templates/application/controller.cs.j2` - API controllers
- `templates/application/program.cs.j2` - Application startup
- `templates/application/application_service.cs.j2` - Application services
- `templates/application/application_di_extensions.cs.j2` - DI configuration

**DTOs Templates:**
- `templates/dtos/create_dto.cs.j2` - Create DTOs
- `templates/dtos/update_dto.cs.j2` - Update DTOs
- `templates/dtos/dto_validator.cs.j2` - DTO validators

**Middleware Templates:**
- `templates/middleware/correlation_middleware.cs.j2` - Correlation middleware
- `templates/middleware/request_logging_middleware.cs.j2` - Request logging middleware

**Configuration Templates:**
- `templates/configuration/appsettings.json.j2` - Application settings
- `templates/configuration/serilog_configuration.cs.j2` - Logging configuration
- `templates/configuration/sensitive_data_examples.cs.j2` - Data examples

**Project Templates:**
- `templates/project/solution.sln.j2` - Solution file
- `templates/project/*.csproj.j2` - Project files

### Adding New Templates

1. Create new template in `templates/`
2. Update `code_generator.py` to use the template
3. Add file generation logic

## Troubleshooting

### Connection Issues
- Verify PostgreSQL is running
- Check connection string format
- Ensure database user has schema read permissions

### Generation Issues
- Check that tables have primary keys defined
- Verify column types are supported

### uv Issues
- Ensure uv is properly installed
- Try `uv pip sync` to reset dependencies

## License

MIT

## Contributing

Pull requests welcome! Please test with various database schemas.
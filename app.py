import streamlit as st
import psycopg2
from psycopg2 import sql
import json
from pathlib import Path
import zipfile
import io
import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from database_reader import DatabaseSchemaReader
from code_generator import create_code_generator
from utils import pascal_case, snake_case

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Backend Code Generator",
    page_icon="🚀",
    layout="wide"
)

def generate_folder_structure_preview(groups, framework="dotnet"):
    """Generate a preview of the folder structure"""
    preview = "📁 Generated Project Structure:\n\n"
    
    if framework.lower() == "fastapi":
        preview += "src/\n"
        
        # Core layer
        preview += "├── core/\n"
        preview += "│   ├── entities/\n"
        for group in groups:
            if group != 'General':
                preview += f"│   │   ├── {group.lower()}/\n"
            for table in groups[group][:2]:  # Show first 2 tables
                prefix = f"│   │   {'│   ' if group != 'General' else ''}├── "
                preview += f"{prefix}{snake_case(table)}.py\n"
            if len(groups[group]) > 2:
                prefix = f"│   │   {'│   ' if group != 'General' else ''}└── "
                preview += f"{prefix}... ({len(groups[group]) - 2} more)\n"
        
        preview += "│   ├── interfaces/\n"
        preview += "│   └── exceptions/\n"
        
        # Infrastructure layer
        preview += "├── infrastructure/\n"
        preview += "│   └── database/\n"
        preview += "│       ├── models/\n"
        preview += "│       └── repositories/\n"
        
        # Application layer
        preview += "├── application/\n"
        preview += "│   ├── dto/\n"
        preview += "│   └── services/\n"
        
        # API layer
        preview += "├── api/\n"
        preview += "│   ├── v1/routers/\n"
        preview += "│   └── schemas/\n"
        
        # Config and common
        preview += "├── config/\n"
        preview += "└── common/\n"
        
    else:  # .NET Core
        preview += "src/\n"
        
        # Core layer
        preview += "├── Core/\n"
        preview += "│   ├── Entities/\n"
        for group in groups:
            preview += f"│   │   ├── {group}/\n"
            for table in groups[group][:2]:  # Show first 2 tables
                preview += f"│   │   │   ├── {pascal_case(table)}.cs\n"
            if len(groups[group]) > 2:
                preview += f"│   │   │   └── ... ({len(groups[group]) - 2} more)\n"
        
        preview += "│   └── Interfaces/\n"
        for group in groups:
            preview += f"│       ├── {group}/\n"
        
        # Application layer
        preview += "├── Application/\n"
        preview += "│   ├── Interfaces/\n"
        for group in groups:
            preview += f"│   │   ├── {group}/\n"
        preview += "│   └── Services/\n"
        for group in groups:
            preview += f"│       ├── {group}/\n"
        
        # Infrastructure layer
        preview += "├── Infrastructure/\n"
        preview += "│   └── Data/\n"
        for group in groups:
            preview += f"│       ├── {group}/\n"
        
        # WebApi layer
        preview += "└── WebApi/\n"
        preview += "    └── Controllers/\n"
        for group in groups:
            preview += f"        ├── {group}/\n"
    
    return preview

def main():
    st.title("🚀 Backend Code Generator")
    st.markdown("Generate Clean Architecture backend applications from your PostgreSQL database schema")
    
    # Get default connection string from environment
    default_conn_str = os.getenv('POSTGRES_CONNECTION_STRING', '')
    
    # Alternative: Build from individual components if available
    if not default_conn_str:
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        database = os.getenv('POSTGRES_DATABASE', '')
        user = os.getenv('POSTGRES_USER', '')
        password = os.getenv('POSTGRES_PASSWORD', '')
        
        if database and user:
            default_conn_str = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    with st.sidebar:
        st.header("Configuration")
        
        # Framework selection
        framework = st.selectbox(
            "🎯 Target Framework",
            options=["dotnet", "fastapi"],
            format_func=lambda x: {
                "dotnet": "🟣 .NET Core (C#)",
                "fastapi": "🐍 FastAPI (Python)"
            }[x],
            help="Choose your target backend framework"
        )
        
        connection_string = st.text_input(
            "PostgreSQL Connection String",
            value=default_conn_str,
            placeholder="postgresql://user:password@host:port/database",
            type="password",
            help="Format: postgresql://user:password@host:port/database"
        )
        
        solution_name = st.text_input(
            "Solution Name",
            value="GeneratedApp",
            placeholder="MyApplication",
            help="Name for your .NET solution file (without .sln extension)"
        )
        
        output_folder = st.text_input(
            "Output Folder",
            value="./generated-app",
            help="Folder where the .NET application will be generated"
        )
        
        st.markdown("---")
        
        generate_button = st.button("🔨 Generate Application", type="primary", use_container_width=True)
    
    if connection_string:
        try:
            with st.spinner("Connecting to database..."):
                reader = DatabaseSchemaReader(connection_string)
                schema = reader.read_schema()
            
            st.success(f"✅ Connected successfully! Found {len(schema['tables'])} tables")
            
            # Table selection and grouping section
            st.subheader("📊 Select Tables and Organize into Groups")
            
            # Initialize session state for groups
            if 'table_groups' not in st.session_state:
                st.session_state.table_groups = {}
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.write("**Available Tables:**")
                
                # Create a container for table selection
                table_container = st.container()
                with table_container:
                    # Get already grouped tables
                    grouped_tables = set()
                    for tables in st.session_state.table_groups.values():
                        grouped_tables.update(tables)
                    
                    # Get ungrouped tables
                    ungrouped_tables = [table['name'] for table in schema['tables'] if table['name'] not in grouped_tables]
                    
                    # Select all/none buttons for ungrouped tables only
                    col_select_all, col_select_none = st.columns(2)
                    with col_select_all:
                        if st.button("Select All Ungrouped", use_container_width=True):
                            st.session_state.selected_tables = ungrouped_tables.copy()
                    with col_select_none:
                        if st.button("Clear Selection", use_container_width=True):
                            st.session_state.selected_tables = []
                    
                    # Initialize selected tables
                    if 'selected_tables' not in st.session_state:
                        st.session_state.selected_tables = []
                    
                    # Table checkboxes in a scrollable area
                    st.markdown("---")
                    
                    # Show grouped tables (disabled)
                    if grouped_tables:
                        st.caption("**Grouped Tables (already assigned):**")
                        for table in schema['tables']:
                            if table['name'] in grouped_tables:
                                # Find which group this table belongs to
                                table_group = None
                                for group, tables in st.session_state.table_groups.items():
                                    if table['name'] in tables:
                                        table_group = group
                                        break
                                st.text(f"   ✅ {table['name']} → [{table_group}]")
                        st.markdown("---")
                    
                    # Show ungrouped tables (selectable)
                    if ungrouped_tables:
                        st.caption("**Ungrouped Tables (select to assign):**")
                        for table in schema['tables']:
                            if table['name'] not in grouped_tables:
                                is_selected = st.checkbox(
                                    f"📋 {table['name']}",
                                    key=f"table_{table['name']}",
                                    value=table['name'] in st.session_state.selected_tables
                                )
                                if is_selected and table['name'] not in st.session_state.selected_tables:
                                    st.session_state.selected_tables.append(table['name'])
                                elif not is_selected and table['name'] in st.session_state.selected_tables:
                                    st.session_state.selected_tables.remove(table['name'])
                    else:
                        st.info("All tables have been assigned to groups!")
            
            with col2:
                st.write("**Organize into Groups:**")
                
                # Show selected tables count
                st.info(f"Selected: {len(st.session_state.selected_tables)} tables")
                
                if st.session_state.selected_tables:
                    st.markdown("**Assign to Group:**")
                    
                    # Option to select existing group or create new one
                    assignment_option = st.radio(
                        "Choose an option:",
                        ["Assign to existing group", "Create new group"],
                        key="assignment_option",
                        horizontal=True
                    )
                    
                    if assignment_option == "Assign to existing group":
                        if st.session_state.table_groups:
                            selected_group = st.selectbox(
                                "Select Group",
                                options=list(st.session_state.table_groups.keys()),
                                help="Choose an existing group for the selected tables"
                            )
                            
                            if st.button("✅ Assign to Selected Group", type="primary", use_container_width=True):
                                for table in st.session_state.selected_tables:
                                    if table not in st.session_state.table_groups[selected_group]:
                                        # Remove from other groups
                                        for g in st.session_state.table_groups:
                                            if g != selected_group and table in st.session_state.table_groups[g]:
                                                st.session_state.table_groups[g].remove(table)
                                        st.session_state.table_groups[selected_group].append(table)
                                
                                st.success(f"✅ Assigned {len(st.session_state.selected_tables)} tables to '{selected_group}'")
                                st.session_state.selected_tables = []
                                st.rerun()
                        else:
                            st.warning("No existing groups. Please create a new group first.")
                    
                    else:  # Create new group
                        group_name = st.text_input(
                            "New Group Name (no spaces)",
                            placeholder="e.g., Auth, PurchaseOrder, Inventory",
                            help="Enter a group name without spaces. Use PascalCase for multi-word names."
                        )
                        
                        # Validate group name
                        if group_name and ' ' in group_name:
                            st.error("Group name cannot contain spaces. Use PascalCase instead.")
                            group_name = None
                        
                        if group_name and st.button("➕ Create Group & Assign", type="primary", use_container_width=True):
                            if group_name not in st.session_state.table_groups:
                                st.session_state.table_groups[group_name] = []
                            
                            for table in st.session_state.selected_tables:
                                if table not in st.session_state.table_groups[group_name]:
                                    # Remove from other groups
                                    for g in st.session_state.table_groups:
                                        if g != group_name and table in st.session_state.table_groups[g]:
                                            st.session_state.table_groups[g].remove(table)
                                    st.session_state.table_groups[group_name].append(table)
                            
                            st.success(f"✅ Created group '{group_name}' and assigned {len(st.session_state.selected_tables)} tables")
                            st.session_state.selected_tables = []
                            st.rerun()
                
                # Display current groups
                if st.session_state.table_groups:
                    st.markdown("---")
                    st.write("**Current Groups:**")
                    for group, tables in st.session_state.table_groups.items():
                        with st.expander(f"📁 {group} ({len(tables)} tables)"):
                            for table in tables:
                                st.text(f"  • {table}")
                            if st.button(f"🗑️ Remove Group", key=f"remove_{group}"):
                                del st.session_state.table_groups[group]
                                st.rerun()
                
                # Handle ungrouped tables
                ungrouped_tables = [
                    table['name'] for table in schema['tables']
                    if not any(table['name'] in tables for tables in st.session_state.table_groups.values())
                ]
                
                if ungrouped_tables:
                    st.markdown("---")
                    st.write(f"**Ungrouped Tables ({len(ungrouped_tables)}):**")
                    st.caption("These will be placed in 'General' group")
                    for table in ungrouped_tables[:5]:
                        st.text(f"  • {table}")
                    if len(ungrouped_tables) > 5:
                        st.text(f"  ... and {len(ungrouped_tables) - 5} more")
            
            # Code preview section
            st.markdown("---")
            st.subheader("📝 Preview Generated Structure")
            
            if st.session_state.table_groups or ungrouped_tables:
                # Add ungrouped tables to General group for preview
                all_groups = dict(st.session_state.table_groups)
                if ungrouped_tables:
                    all_groups['General'] = ungrouped_tables
                
                # Show folder structure preview
                st.code(generate_folder_structure_preview(all_groups, framework), language="text")
            
            if generate_button:
                framework_name = {
                    'dotnet': '.NET Core',
                    'fastapi': 'FastAPI'
                }[framework]
                
                with st.spinner(f"Generating {framework_name} application..."):
                    generator = create_code_generator(framework)
                    
                    # Prepare groups with ungrouped tables
                    all_groups = dict(st.session_state.table_groups) if 'table_groups' in st.session_state else {}
                    
                    # Add ungrouped tables to General group
                    ungrouped = [
                        table['name'] for table in schema['tables']
                        if not any(table['name'] in tables for tables in all_groups.values())
                    ]
                    if ungrouped:
                        all_groups['General'] = ungrouped
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    files = generator.generate_application(
                        schema, 
                        connection_string=connection_string,
                        table_groups=all_groups,
                        solution_name=solution_name,
                        progress_callback=lambda p, m: (
                            progress_bar.progress(p),
                            status_text.text(m)
                        )
                    )
                    
                    zip_buffer = create_zip(files)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Generation complete!")
                
                st.success(f"🎉 {framework_name} application generated successfully!")
                
                col1, col2 = st.columns(2)
                with col1:
                    file_extension = "py" if framework == "fastapi" else "cs"
                    st.download_button(
                        label="📦 Download as ZIP",
                        data=zip_buffer.getvalue(),
                        file_name=f"generated-{framework}-app.zip",
                        mime="application/zip"
                    )
                
                with col2:
                    if st.button("💾 Save to Folder"):
                        save_to_folder(files, output_folder)
                        st.success(f"Saved to {output_folder}")
                
                # Framework-specific next steps
                if framework == "fastapi":
                    st.info("**Next Steps:**\n1. Extract the ZIP file\n2. Copy `.env.example` to `.env` and configure\n3. Run `uv sync` to install dependencies\n4. Run `uv run alembic upgrade head` for database migrations\n5. Run `uv run uvicorn src.api.main:app --reload`")
                else:
                    st.info("**Next Steps:**\n1. Extract the ZIP file\n2. Update appsettings.json with your connection string\n3. Run `dotnet restore`\n4. Run `dotnet build`\n5. Run `dotnet run`")
        
        except psycopg2.Error as e:
            st.error(f"❌ Database connection failed: {str(e)}")
        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
    else:
        st.info("👈 Please enter your PostgreSQL connection string in the sidebar to get started")

def create_zip(files: Dict[str, str]) -> io.BytesIO:
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filepath, content in files.items():
            zip_file.writestr(filepath, content)
    zip_buffer.seek(0)
    return zip_buffer

def save_to_folder(files: Dict[str, str], output_folder: str):
    base_path = Path(output_folder)
    for filepath, content in files.items():
        full_path = base_path / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)

if __name__ == "__main__":
    main()
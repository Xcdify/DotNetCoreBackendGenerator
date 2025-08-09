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
from code_generator import DotNetCodeGenerator
from utils import pascal_case, snake_case

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title=".NET Core App Generator",
    page_icon="🚀",
    layout="wide"
)

def main():
    st.title("🚀 .NET Core App Generator")
    st.markdown("Generate a Clean Architecture .NET Core 9 application from your PostgreSQL database schema")
    
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
        
        connection_string = st.text_input(
            "PostgreSQL Connection String",
            value=default_conn_str,
            placeholder="postgresql://user:password@host:port/database",
            type="password",
            help="Format: postgresql://user:password@host:port/database"
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
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Database Schema")
                for table in schema['tables']:
                    with st.expander(f"Table: {table['name']}"):
                        st.write("**Columns:**")
                        for col in table['columns']:
                            nullable = "?" if col['is_nullable'] else ""
                            st.code(f"{col['name']}: {col['data_type']}{nullable}")
                        
                        if table['primary_keys']:
                            st.write("**Primary Keys:**", ", ".join(table['primary_keys']))
                        
                        if table['foreign_keys']:
                            st.write("**Foreign Keys:**")
                            for fk in table['foreign_keys']:
                                st.text(f"  {fk['column']} → {fk['referenced_table']}.{fk['referenced_column']}")
            
            with col2:
                st.subheader("📝 Preview Generated Code")
                
                if schema['tables']:
                    preview_table = schema['tables'][0]
                    generator = DotNetCodeGenerator()
                    
                    entity_preview = generator.generate_entity(preview_table)
                    st.write("**Sample Entity:**")
                    st.code(entity_preview, language="csharp")
                    
                    repo_interface_preview = generator.generate_repository_interface(preview_table)
                    st.write("**Sample Repository Interface:**")
                    st.code(repo_interface_preview, language="csharp")
            
            if generate_button:
                with st.spinner("Generating .NET Core application..."):
                    generator = DotNetCodeGenerator()
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    files = generator.generate_application(
                        schema, 
                        connection_string=connection_string,
                        progress_callback=lambda p, m: (
                            progress_bar.progress(p),
                            status_text.text(m)
                        )
                    )
                    
                    zip_buffer = create_zip(files)
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Generation complete!")
                
                st.success("🎉 Application generated successfully!")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📦 Download as ZIP",
                        data=zip_buffer.getvalue(),
                        file_name="generated-dotnet-app.zip",
                        mime="application/zip"
                    )
                
                with col2:
                    if st.button("💾 Save to Folder"):
                        save_to_folder(files, output_folder)
                        st.success(f"Saved to {output_folder}")
                
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
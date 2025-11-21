"""
Database initialization and connection management for DuckDB
Stores DuckDB file in MinIO for persistence
"""
import duckdb
import os
from pathlib import Path
from typing import Optional

DB_PATH = os.getenv("DUCKDB_PATH", "/app/data/chatbot.db")
MINIO_DB_BUCKET = os.getenv("MINIO_DB_BUCKET", "databases")
MINIO_DB_OBJECT = os.getenv("MINIO_DB_OBJECT", "chatbot.db")

# Ensure data directory exists
Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

# Global connection (will be initialized after syncing from MinIO)
conn = None


def sync_db_from_minio():
    """
    Download DuckDB file from MinIO on startup.
    If file doesn't exist in MinIO, create a new database.
    """
    try:
        from app.core.storage import minio_client, init_buckets
        
        # Ensure databases bucket exists
        init_buckets()
        if not minio_client.bucket_exists(MINIO_DB_BUCKET):
            minio_client.make_bucket(MINIO_DB_BUCKET)
            print(f"Created bucket: {MINIO_DB_BUCKET}")
        
        # Try to download existing database from MinIO
        try:
            response = minio_client.get_object(MINIO_DB_BUCKET, MINIO_DB_OBJECT)
            with open(DB_PATH, "wb") as f:
                for data in response.stream(32*1024):
                    f.write(data)
            response.close()
            response.release_conn()
            print(f"✓ Downloaded DuckDB from MinIO: {MINIO_DB_BUCKET}/{MINIO_DB_OBJECT}")
        except Exception as e:
            # Database doesn't exist in MinIO yet, will create new one
            print(f"Database not found in MinIO, creating new database: {e}")
            
    except Exception as e:
        print(f"Warning: Could not sync from MinIO, using local database: {e}")


def sync_db_to_minio():
    """
    Upload DuckDB file to MinIO.
    Call this on shutdown or periodically to persist database.
    """
    try:
        from app.core.storage import minio_client
        
        if not os.path.exists(DB_PATH):
            print("No database file to upload")
            return
        
        # Ensure bucket exists
        if not minio_client.bucket_exists(MINIO_DB_BUCKET):
            minio_client.make_bucket(MINIO_DB_BUCKET)
        
        # Upload database file to MinIO
        file_size = os.path.getsize(DB_PATH)
        with open(DB_PATH, "rb") as f:
            minio_client.put_object(
                MINIO_DB_BUCKET,
                MINIO_DB_OBJECT,
                f,
                file_size,
                content_type="application/x-duckdb"
            )
        print(f"✓ Uploaded DuckDB to MinIO: {MINIO_DB_BUCKET}/{MINIO_DB_OBJECT}")
        
    except Exception as e:
        print(f"Warning: Could not sync to MinIO: {e}")


def init_connection():
    """Initialize DuckDB connection after syncing from MinIO"""
    global conn
    if conn is None:
        # First sync from MinIO
        sync_db_from_minio()
        # Then connect to local file
        conn = duckdb.connect(DB_PATH)
    return conn


def init_database():
    """Initialize database tables following architecture requirements"""
    global conn
    # Ensure connection is initialized
    if conn is None:
        conn = init_connection()
    
    # Chat messages table - stores all chat messages with token counts
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id VARCHAR PRIMARY KEY,
            user_id VARCHAR,
            role VARCHAR NOT NULL,
            content TEXT NOT NULL,
            token_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            response_time_ms INTEGER,
            session_id VARCHAR
        )
    """)
    
    # Documents table - stores document metadata
    conn.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            document_id VARCHAR PRIMARY KEY,
            filename VARCHAR NOT NULL,
            minio_path VARCHAR NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_size BIGINT,
            mime_type VARCHAR,
            user_id VARCHAR
        )
    """)
    
    # Chunks table - stores document chunk metadata (required for RAG)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chunks (
            chunk_id VARCHAR PRIMARY KEY,
            document_id VARCHAR NOT NULL,
            index_in_document INTEGER NOT NULL,
            start_page INTEGER,
            end_page INTEGER,
            token_count INTEGER,
            text_length INTEGER,
            text_excerpt TEXT,
            minio_path VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(document_id)
        )
    """)
    
    # Analytics events table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analytics_events (
            id VARCHAR PRIMARY KEY,
            event_type VARCHAR NOT NULL,
            metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Retrieval logs table - tracks RAG retrieval operations
    conn.execute("""
        CREATE TABLE IF NOT EXISTS retrieval_logs (
            id VARCHAR PRIMARY KEY,
            query_text TEXT,
            collection_name VARCHAR,
            results_count INTEGER,
            retrieval_time_ms INTEGER,
            user_id VARCHAR,
            session_id VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    print("Database initialized successfully")


def get_connection():
    """Get database connection"""
    global conn
    if conn is None:
        conn = init_connection()
    return conn


# -------------------------------
# HELPER FUNCTIONS FOR DATA LOADING
# -------------------------------

def insert_document_metadata(
    document_id: str,
    filename: str,
    minio_path: str,
    file_size: int,
    mime_type: str,
    user_id: Optional[str] = None
):
    """
    Insert document metadata into DuckDB.
    Architecture requirement: Store metadata in DuckDB.
    """
    conn.execute("""
        INSERT INTO documents (document_id, filename, minio_path, file_size, mime_type, user_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (document_id, filename, minio_path, file_size, mime_type, user_id))
    conn.commit()


def insert_chunk_metadata(
    chunk_id: str,
    document_id: str,
    index_in_document: int,
    start_page: Optional[int],
    end_page: Optional[int],
    token_count: int,
    text_length: int,
    text_excerpt: str,
    minio_path: Optional[str] = None
):
    """
    Insert chunk metadata into DuckDB.
    Architecture requirement: Store chunk metadata before embedding.
    """
    conn.execute("""
        INSERT INTO chunks (
            chunk_id, document_id, index_in_document,
            start_page, end_page, token_count, text_length, text_excerpt, minio_path
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        chunk_id, document_id, index_in_document,
        start_page, end_page, token_count, text_length, text_excerpt, minio_path
    ))
    conn.commit()


def insert_message(
    message_id: str,
    user_id: str,
    role: str,
    content: str,
    token_count: Optional[int] = None,
    session_id: Optional[str] = None,
    response_time_ms: Optional[int] = None
):
    """
    Insert chat message into DuckDB.
    Architecture requirement: Store messages in DuckDB.
    """
    if token_count is None:
        # Approximate token count (1 token ≈ 4 chars)
        token_count = len(content) // 4
    
    conn.execute("""
        INSERT INTO messages (
            message_id, user_id, role, content, token_count, session_id, response_time_ms
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (message_id, user_id, role, content, token_count, session_id, response_time_ms))
    conn.commit()


# -------------------------------
# PARQUET EXPORT FUNCTIONS
# -------------------------------

def export_table_to_parquet(table_name: str, output_path: str) -> str:
    """
    Export a DuckDB table to parquet format.
    
    Args:
        table_name: Name of the table to export (must be a valid table name)
        output_path: Full path where parquet file should be saved
        
    Returns:
        Path to the created parquet file
    """
    # Validate table name to prevent SQL injection
    valid_tables = ["messages", "documents", "chunks", "analytics_events", "retrieval_logs"]
    if table_name not in valid_tables:
        raise ValueError(f"Invalid table name: {table_name}. Must be one of {valid_tables}")
    
    try:
        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Export table to parquet using DuckDB's COPY command
        # Using parameterized query with table name validation
        conn.execute(f"""
            COPY (SELECT * FROM {table_name}) TO '{output_path}' (FORMAT PARQUET)
        """)
        
        print(f"✓ Exported {table_name} to {output_path}")
        return output_path
    except Exception as e:
        raise Exception(f"Error exporting {table_name} to parquet: {e}")


def export_all_tables_to_parquet(output_dir: str) -> dict:
    """
    Export all DuckDB tables to parquet format.
    
    Args:
        output_dir: Directory where parquet files should be saved
        
    Returns:
        Dictionary mapping table names to parquet file paths
    """
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # List of tables to export
    tables = ["messages", "documents", "chunks", "analytics_events", "retrieval_logs"]
    
    exported_files = {}
    
    for table_name in tables:
        try:
            # Check if table exists and has data
            result = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            row_count = result[0] if result else 0
            
            if row_count == 0:
                print(f"⚠️  Table {table_name} is empty, skipping export")
                continue
            
            # Export to parquet
            parquet_path = os.path.join(output_dir, f"{table_name}.parquet")
            export_table_to_parquet(table_name, parquet_path)
            exported_files[table_name] = parquet_path
            
        except Exception as e:
            print(f"✗ Error exporting {table_name}: {e}")
            continue
    
    return exported_files


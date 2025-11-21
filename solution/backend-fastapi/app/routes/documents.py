from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Optional
import os
import uuid
import io

from app.core.database import get_connection, export_all_tables_to_parquet
from app.core.storage import (
    upload_file as upload_to_minio, 
    upload_parquet_file, 
    get_file, 
    list_files,
    get_file_info,
    minio_client
)
from app.core.chunking import chunk_text, chunk_by_pages, count_tokens
from app.core.vector_store import store_document_chunk, embed_text_sync
from app.core.pdf_reader import extract_text_from_pdf, extract_text_by_pages
import tempfile
import shutil

router = APIRouter(prefix="/api", tags=["documents"])


def process_document_content(
    file_content: bytes,
    filename: str,
    content_type: str,
    document_id: str,
    minio_path: str,
    file_size: int,
    user_id: Optional[str] = None
):
    """
    Shared function to process document content (extract, chunk, embed).
    Used by both upload endpoint and MinIO processing endpoint.
    """
    conn = get_connection()
    
    # Extract text based on file type
    text_content = None
    pages = None
    is_pdf = False
    
    # Check if file is PDF
    if content_type == "application/pdf" or (filename and filename.lower().endswith('.pdf')):
        is_pdf = True
        try:
            # Try page-aware extraction first (better for chunking)
            pages = extract_text_by_pages(file_content)
            if pages and any(pages):
                text_content = "\n\n".join(pages)
            else:
                # Fallback to simple extraction
                text_content = extract_text_from_pdf(file_content)
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    elif content_type == "application/json" or (filename and filename.lower().endswith('.json')):
        # Handle JSON files - extract text content
        try:
            import json
            json_data = json.loads(file_content.decode('utf-8'))
            # If JSON has formatted_text field, use it; otherwise format the JSON
            if 'formatted_text' in json_data:
                text_content = json_data['formatted_text']
            elif 'description' in json_data or 'title' in json_data:
                # Format course-like JSON
                text_parts = []
                if 'title' in json_data:
                    text_parts.append(f"Title: {json_data['title']}")
                if 'description' in json_data:
                    text_parts.append(f"Description: {json_data['description']}")
                if 'topics' in json_data and isinstance(json_data['topics'], list):
                    text_parts.append(f"Topics: {', '.join(json_data['topics'])}")
                text_content = "\n\n".join(text_parts)
            else:
                # Fallback: convert JSON to readable text
                text_content = json.dumps(json_data, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Error parsing JSON file: {str(e)}")
    elif content_type and 'text' in content_type:
        # Handle text files
        text_content = file_content.decode('utf-8', errors='ignore')
    else:
        # For unsupported file types
        raise ValueError(f"Text extraction for file type '{content_type}' not yet implemented.")
    
    if not text_content or not text_content.strip():
        raise ValueError("Could not extract text content from the file.")
    
    # Chunk the document (architecture requirement: ALWAYS chunk before embedding)
    if is_pdf and pages and len(pages) > 1:
        # Use page-aware chunking for PDFs
        chunks = chunk_by_pages(
            pages=pages,
            max_tokens_per_chunk=512,  # Architecture requirement: 512-1024 tokens
            overlap_tokens=50  # ~10% overlap
        )
    else:
        # Use regular chunking for text files or single-page PDFs
        chunks = chunk_text(
            text=text_content,
            max_tokens=512,  # Architecture requirement: 512-1024 tokens
            overlap_tokens=50  # ~10% overlap
        )
    
    # Generate embeddings and store in Qdrant (multi-vector)
    chunk_count = 0
    for chunk in chunks:
        # Store chunk metadata in DuckDB
        conn.execute("""
            INSERT INTO chunks (
                chunk_id, document_id, index_in_document,
                start_page, end_page, token_count, text_length, text_excerpt
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chunk['chunk_id'],
            document_id,
            chunk['index'],
            chunk.get('start_page'),
            chunk.get('end_page'),
            chunk['token_count'],
            chunk['text_length'],
            chunk['text'][:500]  # Store excerpt (first 500 chars)
        ))
        
        # Store embedding in Qdrant with multi-vector schema
        store_document_chunk(
            chunk_id=chunk['chunk_id'],
            content=chunk['text'],
            metadata={
                "document_id": document_id,
                "title": filename,
                "source_type": "document",
                "start_page": chunk.get('start_page'),
                "end_page": chunk.get('end_page')
            }
        )
        chunk_count += 1
    
    conn.commit()
    
    return chunk_count


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), user_id: Optional[str] = None):
    """
    Upload a file to MinIO and index it for RAG.
    Follows architecture pipeline:
    1. Upload → MinIO
    2. Metadata → DuckDB
    3. Chunking → Python
    4. Embedding → Model
    5. Vector Storage → Qdrant (multi-vector)
    """
    try:
        # Step 1: Upload to MinIO
        file_content = await file.read()
        file_size = len(file_content)
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        file_ext = os.path.splitext(file.filename)[1]
        object_name = f"{document_id}{file_ext}"
        
        minio_path = upload_to_minio(
            bucket_name="documents",
            object_name=object_name,
            file_data=io.BytesIO(file_content),
            length=file_size,
            content_type=file.content_type or "application/octet-stream"
        )
        
        # Step 2: Store metadata in DuckDB
        conn = get_connection()
        conn.execute("""
            INSERT INTO documents (document_id, filename, minio_path, file_size, mime_type, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (document_id, file.filename, minio_path, file_size, file.content_type, user_id))
        conn.commit()
        
        # Step 3-6: Process document content (extract, chunk, embed)
        try:
            chunk_count = process_document_content(
                file_content=file_content,
                filename=file.filename,
                content_type=file.content_type or "application/octet-stream",
                document_id=document_id,
                minio_path=minio_path,
                file_size=file_size,
                user_id=user_id
            )
        except ValueError as e:
            # For unsupported file types, return success but note processing needed
            return {
                "document_id": document_id,
                "filename": file.filename,
                "minio_path": minio_path,
                "size": file_size,
                "status": "uploaded",
                "note": str(e)
            }
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error processing document: {str(e)}"
            )
        
        return {
            "document_id": document_id,
            "filename": file.filename,
            "minio_path": minio_path,
            "size": file_size,
            "chunks_created": chunk_count,
            "status": "indexed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@router.post("/process-from-minio")
async def process_from_minio(
    bucket_name: str = "documents",
    object_name: Optional[str] = None,
    prefix: str = "",
    user_id: Optional[str] = None,
    process_all: bool = False
):
    """
    Process files that are already uploaded to MinIO.
    You can upload files directly to MinIO (via MinIO console or API) and then call this endpoint to process them.
    
    Args:
        bucket_name: MinIO bucket name (default: "documents")
        object_name: Specific file to process (if None, processes all unprocessed files)
        prefix: Prefix filter for files (e.g., "uploads/" to only process files in that folder)
        user_id: User ID for the documents
        process_all: If True, process all files. If False, only process unprocessed files.
    """
    try:
        conn = get_connection()
        processed_files = []
        errors = []
        
        # Get list of files to process
        if object_name:
            # Process specific file
            files_to_process = [object_name]
        else:
            # List all files in bucket with prefix
            all_files = list_files(bucket_name=bucket_name, prefix=prefix)
            
            if not process_all:
                # Filter out already processed files
                processed_paths = set()
                existing_docs = conn.execute("""
                    SELECT minio_path FROM documents
                """).fetchall()
                processed_paths = {f"{bucket_name}/{row[0].split('/', 1)[1]}" if '/' in row[0] else row[0] for row in existing_docs}
                
                files_to_process = [
                    f for f in all_files 
                    if f"{bucket_name}/{f}" not in processed_paths
                ]
            else:
                files_to_process = all_files
        
        if not files_to_process:
            return {
                "status": "success",
                "message": "No files to process",
                "processed": [],
                "errors": []
            }
        
        # Process each file
        for file_object_name in files_to_process:
            try:
                # Get file info from MinIO
                file_info = get_file_info(bucket_name, file_object_name)
                filename = os.path.basename(file_object_name)
                
                # Download file content
                file_obj = get_file(bucket_name, file_object_name)
                file_content = file_obj.read()
                file_obj.close()
                file_size = len(file_content)
                
                # Generate document ID
                document_id = str(uuid.uuid4())
                minio_path = f"{bucket_name}/{file_object_name}"
                
                # Store metadata in DuckDB
                conn.execute("""
                    INSERT INTO documents (document_id, filename, minio_path, file_size, mime_type, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    document_id,
                    filename,
                    minio_path,
                    file_size,
                    file_info.get("content_type", "application/octet-stream"),
                    user_id
                ))
                conn.commit()
                
                # Process document content
                try:
                    chunk_count = process_document_content(
                        file_content=file_content,
                        filename=filename,
                        content_type=file_info.get("content_type", "application/octet-stream"),
                        document_id=document_id,
                        minio_path=minio_path,
                        file_size=file_size,
                        user_id=user_id
                    )
                    
                    processed_files.append({
                        "document_id": document_id,
                        "filename": filename,
                        "minio_path": minio_path,
                        "size": file_size,
                        "chunks_created": chunk_count,
                        "status": "indexed"
                    })
                except ValueError as e:
                    # Unsupported file type - still mark as uploaded
                    processed_files.append({
                        "document_id": document_id,
                        "filename": filename,
                        "minio_path": minio_path,
                        "size": file_size,
                        "status": "uploaded",
                        "note": str(e)
                    })
                except Exception as e:
                    errors.append({
                        "filename": filename,
                        "minio_path": minio_path,
                        "error": str(e)
                    })
                    
            except Exception as e:
                errors.append({
                    "filename": file_object_name,
                    "error": str(e)
                })
                continue
        
        return {
            "status": "success",
            "message": f"Processed {len(processed_files)} files",
            "processed": processed_files,
            "errors": errors,
            "total_processed": len(processed_files),
            "total_errors": len(errors)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing files from MinIO: {str(e)}")


@router.get("/list-minio-files")
async def list_minio_files(
    bucket_name: str = "documents",
    prefix: str = "",
    show_processed: bool = False
):
    """
    List files in MinIO bucket and show which ones are already processed.
    
    Args:
        bucket_name: MinIO bucket name (default: "documents")
        prefix: Prefix filter for files
        show_processed: If True, show all files. If False, only show unprocessed files.
    """
    try:
        conn = get_connection()
        
        # Get all files in MinIO
        all_files = list_files(bucket_name=bucket_name, prefix=prefix)
        
        # Get processed files from database
        processed_paths = set()
        if not show_processed:
            existing_docs = conn.execute("""
                SELECT minio_path FROM documents
            """).fetchall()
            processed_paths = {f"{bucket_name}/{row[0].split('/', 1)[1]}" if '/' in row[0] else row[0] for row in existing_docs}
        
        # Build file list with status
        file_list = []
        for file_object_name in all_files:
            minio_path = f"{bucket_name}/{file_object_name}"
            is_processed = minio_path in processed_paths
            
            if show_processed or not is_processed:
                try:
                    file_info = get_file_info(bucket_name, file_object_name)
                    file_list.append({
                        "object_name": file_object_name,
                        "filename": os.path.basename(file_object_name),
                        "minio_path": minio_path,
                        "size": file_info.get("size", 0),
                        "content_type": file_info.get("content_type", "unknown"),
                        "last_modified": str(file_info.get("last_modified", "")),
                        "processed": is_processed
                    })
                except Exception as e:
                    file_list.append({
                        "object_name": file_object_name,
                        "filename": os.path.basename(file_object_name),
                        "minio_path": minio_path,
                        "processed": is_processed,
                        "error": str(e)
                    })
        
        return {
            "bucket": bucket_name,
            "prefix": prefix,
            "total_files": len(all_files),
            "files": file_list,
            "unprocessed_count": len([f for f in file_list if not f.get("processed", False)])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing MinIO files: {str(e)}")


@router.post("/export/parquet")
async def export_to_parquet():
    """
    Export all DuckDB tables to parquet format and upload to MinIO.
    This addresses the requirement to store data in parquet format in MinIO.
    """
    try:
        # Create temporary directory for parquet files
        temp_dir = tempfile.mkdtemp(prefix="parquet_export_")
        
        try:
            # Export all tables to parquet
            print(f"Exporting tables to parquet in {temp_dir}...")
            exported_files = export_all_tables_to_parquet(temp_dir)
            
            if not exported_files:
                return {
                    "status": "success",
                    "message": "No tables with data to export",
                    "uploaded_files": []
                }
            
            # Upload each parquet file to MinIO
            uploaded_paths = []
            for table_name, parquet_path in exported_files.items():
                try:
                    minio_path = upload_parquet_file(
                        parquet_path,
                        bucket_name="parquet"
                    )
                    uploaded_paths.append({
                        "table": table_name,
                        "local_path": parquet_path,
                        "minio_path": minio_path
                    })
                    print(f"✓ Uploaded {table_name}.parquet to MinIO: {minio_path}")
                except Exception as e:
                    print(f"✗ Error uploading {table_name}.parquet: {e}")
                    continue
            
            return {
                "status": "success",
                "message": f"Exported {len(uploaded_paths)} tables to parquet and uploaded to MinIO",
                "uploaded_files": uploaded_paths,
                "export_dir": temp_dir
            }
            
        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                print(f"Warning: Could not clean up temp directory {temp_dir}: {e}")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting to parquet: {str(e)}")


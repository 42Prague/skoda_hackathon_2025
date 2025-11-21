"""
MinIO client for object storage
"""
from minio import Minio
from minio.error import S3Error
import os
from typing import Optional, BinaryIO

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_USE_SSL = os.getenv("MINIO_USE_SSL", "false").lower() == "true"

# Initialize MinIO client
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_USE_SSL
)


def init_buckets():
    """Create required buckets if they don't exist"""
    buckets = ["documents", "parquet", "chat-exports", "avatars", "attachments", "databases"]
    
    for bucket_name in buckets:
        try:
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)
                print(f"Created bucket: {bucket_name}")
        except S3Error as e:
            print(f"Error creating bucket {bucket_name}: {e}")


def upload_file(bucket_name: str, object_name: str, file_data: BinaryIO, length: int, content_type: str = "application/octet-stream"):
    """Upload a file to MinIO"""
    try:
        minio_client.put_object(
            bucket_name,
            object_name,
            file_data,
            length,
            content_type=content_type
        )
        return f"{bucket_name}/{object_name}"
    except S3Error as e:
        raise Exception(f"Error uploading file: {e}")


def get_file(bucket_name: str, object_name: str):
    """Download a file from MinIO"""
    try:
        return minio_client.get_object(bucket_name, object_name)
    except S3Error as e:
        raise Exception(f"Error downloading file: {e}")


def delete_file(bucket_name: str, object_name: str):
    """Delete a file from MinIO"""
    try:
        minio_client.remove_object(bucket_name, object_name)
    except S3Error as e:
        raise Exception(f"Error deleting file: {e}")


def list_files(bucket_name: str, prefix: str = "", recursive: bool = True):
    """List files in a MinIO bucket"""
    try:
        objects = minio_client.list_objects(bucket_name, prefix=prefix, recursive=recursive)
        return [obj.object_name for obj in objects]
    except S3Error as e:
        raise Exception(f"Error listing files: {e}")


def get_file_info(bucket_name: str, object_name: str):
    """Get file metadata from MinIO"""
    try:
        stat = minio_client.stat_object(bucket_name, object_name)
        return {
            "object_name": object_name,
            "size": stat.size,
            "content_type": stat.content_type,
            "last_modified": stat.last_modified
        }
    except S3Error as e:
        raise Exception(f"Error getting file info: {e}")


def upload_parquet_file(filepath: str, bucket_name: str = "parquet", prefix: str = "") -> str:
    """
    Upload a parquet file to MinIO.
    
    Args:
        filepath: Local path to the parquet file
        bucket_name: MinIO bucket name (default: "parquet")
        prefix: Prefix for object name (optional, for organizing files)
        
    Returns:
        MinIO path (bucket_name/object_name)
    """
    import os
    from datetime import datetime
    
    filename = os.path.basename(filepath)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create object name with timestamp for versioning
    object_name = f"{prefix}{timestamp}_{filename}" if prefix else f"{timestamp}_{filename}"
    
    try:
        with open(filepath, "rb") as f:
            file_size = os.path.getsize(filepath)
            minio_client.put_object(
                bucket_name,
                object_name,
                f,
                file_size,
                content_type="application/parquet"
            )
        return f"{bucket_name}/{object_name}"
    except S3Error as e:
        raise Exception(f"Error uploading parquet file to MinIO: {e}")
    except Exception as e:
        raise Exception(f"Error reading parquet file: {e}")


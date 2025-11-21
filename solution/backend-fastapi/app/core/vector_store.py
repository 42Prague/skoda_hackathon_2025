"""
Qdrant client for vector storage and similarity search
Following multi-vector architecture requirements:
- Named vectors: text, chunk, image, profile, goal
- Multi-vector weighted search
- Lightweight payloads only
"""
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, 
    VectorParams, 
    PointStruct,
    NamedVector,
    VectorsConfig
)
from openai import OpenAI
import os
import uuid
import numpy as np
from typing import List, Dict, Optional, Any

# Local embedding model
try:
    from sentence_transformers import SentenceTransformer
    LOCAL_EMBEDDING_AVAILABLE = True
except ImportError:
    LOCAL_EMBEDDING_AVAILABLE = False

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))

# Initialize Qdrant client with retry logic
def create_qdrant_client(max_retries=5, retry_delay=2):
    """Create Qdrant client with retry logic and timeout"""
    import time
    for attempt in range(max_retries):
        try:
            client = QdrantClient(
                host=QDRANT_HOST,
                port=QDRANT_PORT,
                timeout=10  # 10 second timeout
            )
            # Test connection by getting collections
            client.get_collections()
            print(f"✓ Connected to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
            return client
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⚠ Qdrant connection attempt {attempt + 1}/{max_retries} failed: {e}")
                print(f"  Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"✗ Failed to connect to Qdrant after {max_retries} attempts")
                raise Exception(f"Failed to connect to Qdrant at {QDRANT_HOST}:{QDRANT_PORT} after {max_retries} attempts: {e}")

qdrant_client = create_qdrant_client()

# Wrapper to keep compatibility across qdrant-client versions
def _search_collection(collection_name: str, vector_name: str, vector: List[float], limit: int, query_filter=None):
    """
    Run a search on the given collection using the appropriate Qdrant client API.
    Uses query_points for newer versions, with 'using' parameter for multi-vector search.
    """
    # Use query_points with 'using' parameter for multi-vector search
    if hasattr(qdrant_client, "query_points"):
        results = qdrant_client.query_points(
            collection_name=collection_name,
            query=vector,  # Pass vector directly
            using=vector_name,  # Specify which named vector to use
            limit=limit,
            query_filter=query_filter
        )
        return results
    # Fallback for older versions (shouldn't be needed with current qdrant-client)
    elif hasattr(qdrant_client, "search_points"):
        return qdrant_client.search_points(
            collection_name=collection_name,
            query_vector=vector,
            using=vector_name,
            limit=limit,
            query_filter=query_filter
        )
    else:
        # Legacy fallback
        return qdrant_client.search(
            collection_name=collection_name,
            query_vector=(vector_name, vector),
            limit=limit,
            filter=query_filter
        )

# Initialize OpenAI client for embeddings
openai_client = None

# Initialize local embedding model
local_embedding_model = None
USE_LOCAL_EMBEDDINGS = os.getenv("USE_LOCAL_EMBEDDINGS", "false").lower() == "true"
LOCAL_EMBEDDING_MODEL_NAME = os.getenv("LOCAL_EMBEDDING_MODEL", "all-mpnet-base-v2")
LOCAL_EMBEDDING_DIM = 768  # all-mpnet-base-v2 outputs 768 dimensions


def get_local_embedding_model():
    """Get or initialize local embedding model"""
    global local_embedding_model
    if local_embedding_model is None and LOCAL_EMBEDDING_AVAILABLE:
        try:
            print(f"Loading local embedding model: {LOCAL_EMBEDDING_MODEL_NAME}")
            local_embedding_model = SentenceTransformer(LOCAL_EMBEDDING_MODEL_NAME)
            print(f"✓ Local embedding model loaded (dimensions: {LOCAL_EMBEDDING_DIM})")
        except Exception as e:
            print(f"✗ Failed to load local embedding model: {e}")
            raise
    return local_embedding_model


def get_openai_client():
    """Get OpenAI client instance"""
    global openai_client
    if openai_client is None:
        # Use Open WebUI as proxy if OPENAI_API_BASE_URL is set
        base_url = os.getenv("OPENAI_API_BASE_URL")
        
        # If routing through Open WebUI, use Open WebUI API token
        # Otherwise, use OpenAI API key directly
        if base_url and "open-webui" in base_url:
            # Use Open WebUI API token for authentication
            api_key = os.getenv("OPEN_WEBUI_API_KEY") or os.getenv("OPENAI_API_KEY")
        else:
            # Use OpenAI API key directly
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("API key not set")
        
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        
        openai_client = OpenAI(**client_kwargs)
    return openai_client


async def embed_text(text: str, model: str = "text-embedding-3-large") -> List[float]:
    """
    Async embedding function.
    Uses local embeddings if USE_LOCAL_EMBEDDINGS=true, otherwise uses OpenAI.
    """
    # For now, use sync version (local models are fast enough)
    return embed_text_sync(text, model)


def embed_text_sync(text: str, model: str = "text-embedding-3-large") -> List[float]:
    """
    Synchronous version of embed_text for compatibility.
    Uses local embeddings if USE_LOCAL_EMBEDDINGS=true, otherwise uses OpenAI.
    """
    if USE_LOCAL_EMBEDDINGS:
        # Use local open-source model
        if not LOCAL_EMBEDDING_AVAILABLE:
            raise ValueError("sentence-transformers not installed. Install with: pip install sentence-transformers")
        
        embedding_model = get_local_embedding_model()
        if embedding_model is None:
            raise ValueError("Failed to load local embedding model")
        
        # Generate embedding using local model
        embedding = embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    else:
        # Use OpenAI embeddings
        client = get_openai_client()
        response = client.embeddings.create(
            model=model,
            input=text,
            dimensions=1536  # OpenAI text-embedding-3-large outputs 1536 dimensions
        )
        return response.data[0].embedding


def init_collections():
    """
    Initialize Qdrant collections with multi-vector schema.
    REQUIRED: All collections MUST use named vectors, never single-vector.
    Uses qdrant-client library with proper error handling.
    """
    from qdrant_client.models import VectorParams, Distance
    
    # Determine embedding dimensions based on embedding type
    if USE_LOCAL_EMBEDDINGS:
        embedding_dim = LOCAL_EMBEDDING_DIM  # 768 for all-mpnet-base-v2
        print(f"Using local embeddings with dimension: {embedding_dim}")
    else:
        embedding_dim = 1536  # OpenAI text-embedding-3-large
        print(f"Using OpenAI embeddings with dimension: {embedding_dim}")
    
    # Standard multi-vector schema as per architecture requirements
    named_vectors = {
        "text": VectorParams(size=embedding_dim, distance=Distance.COSINE),
        "chunk": VectorParams(size=embedding_dim, distance=Distance.COSINE),
        "image": VectorParams(size=1024, distance=Distance.DOT),
        "profile": VectorParams(size=embedding_dim, distance=Distance.COSINE),
        "goal": VectorParams(size=embedding_dim, distance=Distance.COSINE)
    }
    
    collections = ["chat_messages", ""]
    
    for collection_name in collections:
        try:
            # Check if collection exists
            collection_exists = False
            try:
                collection_info = qdrant_client.get_collection(collection_name)
                collection_exists = True
                # Collection exists, verify it has named vectors with correct vector names
                vectors_config = collection_info.config.params.vectors
                
                # Required vector names for multi-vector schema
                required_vector_names = ['text', 'chunk', 'image', 'profile', 'goal']
                
                # Check if it's a named vectors config with correct vector names
                has_named_vectors = False
                actual_vector_names = []
                
                if isinstance(vectors_config, dict):
                    # Qdrant returns vectors as a dict when using named vectors
                    actual_vector_names = list(vectors_config.keys())
                    # Check if all required vector names are present
                    if all(name in actual_vector_names for name in required_vector_names):
                        has_named_vectors = True
                elif hasattr(vectors_config, 'named'):
                    # Check if it's a VectorsConfig with named vectors
                    if vectors_config.named:
                        actual_vector_names = list(vectors_config.named.keys()) if isinstance(vectors_config.named, dict) else []
                        if all(name in actual_vector_names for name in required_vector_names):
                            has_named_vectors = True
                
                if has_named_vectors:
                    print(f"✓ Collection {collection_name} already exists with correct multi-vector config")
                    print(f"  Vector names: {', '.join(actual_vector_names)}")
                else:
                    print(f"⚠ WARNING: Collection {collection_name} exists but doesn't have correct named vectors!")
                    print(f"  Expected vector names: {', '.join(required_vector_names)}")
                    print(f"  Actual vector names: {', '.join(actual_vector_names) if actual_vector_names else 'none'}")
                    print(f"  Recreating collection with proper multi-vector config...")
                    # Delete and recreate
                    qdrant_client.delete_collection(collection_name)
                    collection_exists = False
            except Exception as check_error:
                # Collection doesn't exist - check if it's a 404 error
                from qdrant_client.http.exceptions import UnexpectedResponse
                error_str = str(check_error)
                if isinstance(check_error, UnexpectedResponse):
                    # Check status code or error message
                    if hasattr(check_error, 'status_code') and check_error.status_code == 404:
                        collection_exists = False
                    elif "doesn't exist" in error_str or "404" in error_str:
                        collection_exists = False
                    else:
                        # Collection might exist but check failed - try HTTP check
                        import requests
                        try:
                            qdrant_url = f"http://{QDRANT_HOST}:{QDRANT_PORT}"
                            check_url = f"{qdrant_url}/collections/{collection_name}"
                            resp = requests.get(check_url, timeout=5)
                            if resp.status_code == 200:
                                collection_exists = True
                                print(f"✓ Collection {collection_name} exists (verified via HTTP)")
                            else:
                                collection_exists = False
                        except:
                            collection_exists = False
                elif "doesn't exist" in error_str or "Recreate collection" in error_str:
                    collection_exists = False
                else:
                    # Try HTTP check as fallback
                    import requests
                    try:
                        qdrant_url = f"http://{QDRANT_HOST}:{QDRANT_PORT}"
                        check_url = f"{qdrant_url}/collections/{collection_name}"
                        resp = requests.get(check_url, timeout=5)
                        if resp.status_code == 200:
                            collection_exists = True
                            print(f"✓ Collection {collection_name} exists (verified via HTTP)")
                        else:
                            collection_exists = False
                    except:
                        collection_exists = False
            
            # Create collection if it doesn't exist
            # Skip creation if collection already exists with proper config
            if not collection_exists:
                print(f"  Creating collection {collection_name}...")
                try:
                    # Create collection with named vectors - pass dict directly to vectors_config
                    qdrant_client.create_collection(
                        collection_name=collection_name,
                        vectors_config=named_vectors
                    )
                    print(f"✓ Created multi-vector collection: {collection_name}")
                    print(f"  Vector names: {', '.join(named_vectors.keys())}")
                except Exception as create_error:
                    error_str = str(create_error)
                    # Check if collection already exists
                    if "already exists" in error_str.lower() or "already exist" in error_str.lower():
                        print(f"✓ Collection {collection_name} already exists")
                    else:
                        print(f"⚠️  Collection {collection_name} creation failed: {error_str[:200]}")
                        # Try to verify it exists anyway
                        try:
                            qdrant_client.get_collection(collection_name)
                            print(f"✓ Collection {collection_name} exists (verification successful)")
                        except:
                            print(f"✗ Collection {collection_name} does not exist and creation failed")
                    
        except Exception as e:
            import traceback
            print(f"✗ Error creating/checking collection {collection_name}: {e}")
            print(f"  Traceback: {traceback.format_exc()}")


def store_chat_embedding(message_id: str, content: str, metadata: Dict):
    """
    Store a chat message embedding in Qdrant using multi-vector schema.
    Uses 'text' vector for chat messages.
    Payload contains only lightweight metadata (no full content).
    """
    try:
        # Generate embedding using standard function
        embedding = embed_text_sync(content)
        
        # Create point with named vector
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector={
                "text": embedding  # Use 'text' vector for chat messages
            },
            payload={
                # Lightweight metadata only - full content stored in DuckDB
                "message_id": message_id,
                "user_id": metadata.get("user_id"),
                "session_id": metadata.get("session_id"),
                "role": metadata.get("role"),
                "source_type": "chat_message"
            }
        )
        
        qdrant_client.upsert(
            collection_name="chat_messages",
            points=[point]
        )
        return True
    except Exception as e:
        print(f"Error storing chat embedding: {e}")
        return False


def search_similar_messages(
    query: str, 
    limit: int = 5, 
    filter_dict: Optional[Dict] = None,
    use_multi_vector: bool = True
):
    """
    Search for similar messages using multi-vector weighted search.
    Uses 'text' vector for chat message search.
    Returns message_ids - full content must be retrieved from DuckDB.
    """
    try:
        # Generate query embedding
        query_embedding = embed_text_sync(query)
        
        # Multi-vector search using search_points with 'using' parameter
        # Use 'text' vector for chat message search
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        query_filter = None
        if filter_dict:
            conditions = []
            for key, value in filter_dict.items():
                conditions.append(
                    FieldCondition(key=key, match=MatchValue(value=value))
                )
            query_filter = Filter(must=conditions)
        
        results = _search_collection(
            collection_name="chat_messages",
            vector_name="text",
            vector=query_embedding,
            limit=limit,
            query_filter=query_filter
        )
        
        # Handle QueryResponse from query_points (has .points attribute)
        # or direct list from older APIs
        if hasattr(results, 'points'):
            result_list = results.points
        else:
            result_list = results
        
        # Return message_ids - content must be fetched from DuckDB
        return [
            {
                "score": result.score,
                "message_id": result.payload.get("message_id"),
                "metadata": result.payload  # Lightweight metadata only
            }
            for result in result_list
        ]
    except Exception as e:
        import traceback
        print(f"Error searching similar messages: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return []


def store_document_chunk(chunk_id: str, content: str, metadata: Dict):
    """
    Store a document chunk embedding using multi-vector schema.
    Uses 'chunk' vector for document chunks.
    Payload contains only lightweight metadata (no full content).
    """
    try:
        # Generate embedding using standard function
        embedding = embed_text_sync(content)
        
        # Convert chunk_id to UUID if it's not already a valid UUID
        # Qdrant requires point IDs to be UUIDs or integers
        try:
            # Try to parse as UUID
            point_id = uuid.UUID(chunk_id)
        except (ValueError, TypeError):
            # If not a valid UUID, generate one from the chunk_id string
            # Use UUID5 with a namespace to ensure consistency
            namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
            point_id = uuid.uuid5(namespace, chunk_id)
        
        # Create point with named vector
        point = PointStruct(
            id=str(point_id),  # Convert UUID to string
            vector={
                "chunk": embedding  # Use 'chunk' vector for document chunks
            },
            payload={
                # Lightweight metadata only - full content stored in DuckDB
                "chunk_id": chunk_id,
                "document_id": metadata.get("document_id"),
                "title": metadata.get("title", ""),
                "source_type": metadata.get("source_type", "document"),
                "start_page": metadata.get("start_page"),
                "end_page": metadata.get("end_page")
            }
        )
        
        qdrant_client.upsert(
            collection_name="document_chunks",
            points=[point]
        )
        return True
    except Exception as e:
        print(f"Error storing document chunk: {e}")
        import traceback
        traceback.print_exc()
        return False


def search_courses(
    query: str,
    limit: int = 5,
    metadata_filter: Optional[Dict] = None
):
    """
    Search for courses in the courses collection.
    Courses are stored with single-vector format (not multi-vector).
    
    Args:
        query: Search query text
        limit: Maximum number of results
        metadata_filter: Optional Qdrant filter dict (e.g., {"must": [{"key": "course_level", "match": {"value": "Beginner"}}]})
    """
    try:
        # Generate query embedding
        query_embedding = embed_text_sync(query)
        
        # Build Qdrant filter if provided
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        query_filter = None
        if metadata_filter and metadata_filter.get("must"):
            conditions = []
            for condition in metadata_filter["must"]:
                key = condition.get("key")
                match_value = condition.get("match", {}).get("value")
                if key and match_value:
                    conditions.append(
                        FieldCondition(key=key, match=MatchValue(value=match_value))
                    )
            if conditions:
                query_filter = Filter(must=conditions)
        
        # Search courses collection (single-vector, not multi-vector)
        # Try query_points first (newer API)
        if hasattr(qdrant_client, "query_points"):
            results = qdrant_client.query_points(
                collection_name="courses",
                query=query_embedding,
                limit=limit,
                query_filter=query_filter
            )
        # Fallback to search_points
        elif hasattr(qdrant_client, "search_points"):
            results = qdrant_client.search_points(
                collection_name="courses",
                query_vector=query_embedding,
                limit=limit,
                query_filter=query_filter
            )
        else:
            # Legacy fallback
            results = qdrant_client.search(
                collection_name="courses",
                query_vector=query_embedding,
                limit=limit,
                filter=query_filter
            )
        
        # Handle QueryResponse from query_points (has .points attribute)
        # or direct list from older APIs
        if hasattr(results, 'points'):
            result_list = results.points
        else:
            result_list = results
        
        # Return course results with full metadata
        return [
            {
                "score": result.score,
                "metadata": result.payload  # Full course metadata
            }
            for result in result_list
        ]
    except Exception as e:
        import traceback
        print(f"Error searching courses: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return []


def check_qdrant_health():
    """
    Check if Qdrant is accessible and healthy.
    Returns health status dictionary.
    """
    try:
        collections = qdrant_client.get_collections()
        collection_names = [col.name for col in collections.collections]
        
        # Check required collections exist
        required_collections = ["chat_messages", "document_chunks"]
        missing_collections = [c for c in required_collections if c not in collection_names]
        
        return {
            "status": "healthy",
            "host": QDRANT_HOST,
            "port": QDRANT_PORT,
            "collections_count": len(collection_names),
            "collections": collection_names,
            "required_collections": required_collections,
            "missing_collections": missing_collections,
            "all_required_exist": len(missing_collections) == 0
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "host": QDRANT_HOST,
            "port": QDRANT_PORT,
            "error": str(e)
        }

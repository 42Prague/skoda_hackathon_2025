#!/usr/bin/env python3
"""
Upload vectors from FAISS (faiss_index.bin) + metadata.json into Qdrant.

Docker-ready version:
- Uses environment variables
- Fail-safe logging
- Works inside FastAPI backend container
"""

import os
import json
import faiss
import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct
)


# -----------------------------------------
# ENVIRONMENT VARIABLES
# -----------------------------------------
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "/app/data/faiss_index.bin")
METADATA_PATH    = os.getenv("FAISS_METADATA_PATH", "/app/data/metadata.json")

# Qdrant connection - use environment variables or Docker service defaults
QDRANT_HOST = "qdrant"
QDRANT_PORT = "6333"
# Support direct URL override for external connections
QDRANT_URL = os.getenv("QDRANT_URL", f"http://{QDRANT_HOST}:{QDRANT_PORT}")
QDRANT_API_KEY   = os.getenv("QDRANT_API_KEY", None)
COLLECTION_NAME  = os.getenv("QDRANT_COLLECTION", "courses")

BATCH_SIZE       = int(os.getenv("UPLOAD_BATCH_SIZE", "500"))

print("=== QDRANT UPLOAD SCRIPT ===")
print(f"FAISS index:   {FAISS_INDEX_PATH}")
print(f"Metadata file: {METADATA_PATH}")
print(f"Qdrant URL:    {QDRANT_URL}")
print(f"Collection:    {COLLECTION_NAME}")
print("================================\n")


# -----------------------------------------
# CHECK FILES
# -----------------------------------------
if not os.path.exists(FAISS_INDEX_PATH):
    raise FileNotFoundError(f"FAISS index not found: {FAISS_INDEX_PATH}")

if not os.path.exists(METADATA_PATH):
    raise FileNotFoundError(f"Metadata file not found: {METADATA_PATH}")


# -----------------------------------------
# LOAD FAISS
# -----------------------------------------
print("Loading FAISS index...")
index = faiss.read_index(FAISS_INDEX_PATH)

dimension = index.d
count = index.ntotal

print(f"Loaded FAISS index.")
print(f"Vectors count: {count}")
print(f"Vector dim:    {dimension}\n")


# -----------------------------------------
# LOAD METADATA JSON
# -----------------------------------------
print("Loading metadata...")

with open(METADATA_PATH, "r", encoding="utf-8") as f:
    metadata_list = json.load(f)

if len(metadata_list) != count:
    print("⚠️ Warning: metadata list size does not match FAISS vector count.")
    print(f"Metadata entries: {len(metadata_list)}   |   Vectors: {count}")

print(f"Loaded {len(metadata_list)} metadata entries.\n")


# -----------------------------------------
# RECONSTRUCT ALL VECTORS
# -----------------------------------------
print("Reconstructing vectors from FAISS...")

vectors = np.zeros((count, dimension), dtype="float32")
for i in range(count):
    vectors[i] = index.reconstruct(i)


print("✓ All vectors reconstructed.\n")


# -----------------------------------------
# CONNECT TO QDRANT
# -----------------------------------------
print(f"Connecting to Qdrant at {QDRANT_URL}...")

try:
    qdrant = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY
    )
    # Test connection
    qdrant.get_collections()
    print("✓ Connected.\n")
except Exception as e:
    print(f"❌ Failed to connect to Qdrant: {e}")
    print(f"   Make sure Qdrant is running at {QDRANT_URL}")
    print(f"   If running in Docker, ensure containers are on the same network.")
    raise


# -----------------------------------------
# CREATE OR CHECK COLLECTION (PRESERVE EXISTING DATA)
# -----------------------------------------
collection_exists = False
try:
    collections = qdrant.get_collections()
    collection_exists = any(c.name == COLLECTION_NAME for c in collections.collections)
except Exception as e:
    print(f"⚠️  Could not check existing collections: {e}")

if collection_exists:
    print(f"Collection '{COLLECTION_NAME}' already exists.")
    print("Preserving existing data - will add/update vectors only.\n")
    # Verify collection dimensions match
    try:
        collection_info = qdrant.get_collection(COLLECTION_NAME)
        existing_count = collection_info.points_count
        print(f"Current points in collection: {existing_count}")
        
        if collection_info.config.params.vectors.size != dimension:
            print(f"❌ Error: Collection dimension ({collection_info.config.params.vectors.size}) "
                  f"does not match FAISS dimension ({dimension})")
            raise ValueError("Collection dimension mismatch")
        print("✓ Collection dimensions verified.\n")
    except Exception as e:
        if "dimension mismatch" in str(e).lower():
            raise
        print(f"⚠️  Could not verify collection info: {e}\n")
else:
    print(f"Collection '{COLLECTION_NAME}' does not exist.")
    print(f"Creating new collection '{COLLECTION_NAME}'...")
    qdrant.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=dimension,
            distance=Distance.COSINE
        )
    )
    print("✓ Collection created.\n")


# -----------------------------------------
# UPLOAD/UPDATE IN BATCHES (PRESERVES EXISTING DATA)
# -----------------------------------------
print("Adding/updating vectors in Qdrant (existing data preserved)...\n")

for start in range(0, count, BATCH_SIZE):
    end = min(start + BATCH_SIZE, count)
    batch_vectors = vectors[start:end]

    batch_points = []
    for local_i, vec in enumerate(batch_vectors):
        global_i = start + local_i

        meta = metadata_list[global_i]

        qpoint = PointStruct(
            id=meta.get("id", global_i),
            vector=vec.tolist(),
            payload=meta.get("original", {})  # The actual Qdrant payload
        )

        batch_points.append(qpoint)

    print(f"Uploading {start} → {end} ...")

    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=batch_points
    )

print("\n✓ Upload complete!")
print(f"Total vectors processed: {count}")
print("(Existing vectors were preserved, new/updated vectors were added)")

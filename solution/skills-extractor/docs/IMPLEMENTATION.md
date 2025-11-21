# Implementation Details

## Overview

Successfully implemented a complete LLM-based skill extraction and job matching system with hierarchical taxonomy.

## Technologies Used

**Core Stack**:
- Python 3.11+
- Neo4j 5.16 (Community Edition)
- FastAPI for REST API
- Rich for CLI progress visualization

**Dependencies**:
- `sentence-transformers` - Embedding generation
- `scikit-learn` - DBSCAN clustering
- `neo4j` - Database driver
- `openai` - LLM client (via OpenRouter)
- `pydantic` - Data validation

## Module Breakdown

### 1. Data Models
**File**: `src/models/schemas.py`

Implemented Pydantic models:
- `ExtractedSkill` - Raw skills from LLM
- `NormalizedSkill` - Clustered canonical skills
- `Job` - Job posting data
- `Skill` - Skills with hierarchy
- `JobSkillRelationship` - Job-skill links
- `ValidatedSkill` - Validation results
- API request/response models

### 2. LLM Extraction Module
**Files**:
- `src/extraction/llm_client.py` - OpenRouter/GPT-4 client
- `src/extraction/extractor.py` - Batch processing engine

**Features**:
- OpenRouter integration (GPT-4.1)
- Structured prompts for skill extraction
- Parallel processing (50 concurrent requests)
- Batch processing (50 jobs per batch)
- Retry logic with exponential backoff
- Deduplication cache (hash-based)
- Checkpoint system for resumability
- Rich progress bars with statistics

### 3. Normalization Module
**Files**:
- `src/normalization/normalizer.py` - Embedding-based clustering
- `src/normalization/hierarchy.py` - Parent-child inference

**Clustering Algorithm**:
1. Generate embeddings (`all-mpnet-base-v2`, 768-dim)
2. DBSCAN clustering (configurable eps=0.15)
3. Select canonical name (most common in cluster)
4. Build alias mappings
5. Semantic similarity search (cosine similarity)

### 4. Database Layer
**Files**:
- `src/database/neo4j_client.py` - Connection & schema management
- `src/database/operations.py` - CRUD operations

**Operations**:
- Bulk job/skill creation
- Relationship management
- Hierarchical queries
- Vector similarity search
- Full-text search
- Database statistics

### 5. Query Interface
**File**: `src/api/query_service.py`

**Validation Pipeline**:
```
Input: ["Python", "ReactJS", "kuberntes"]
  │
  ├─ Step 1: Exact Match
  │  └─ "Python" ✓ (canonical)
  │
  ├─ Step 2: Alias Match
  │  └─ "ReactJS" → "React" ✓
  │
  ├─ Step 3: Semantic Search
  │  └─ "kuberntes" → "Kubernetes" ✓ (0.92 similarity)
  │
Output: {
  "validated": ["Python", "React", "Kubernetes"],
  "semantic_matches": {"kuberntes": "Kubernetes"},
  "coverage": 1.0
}
```

### 6. FastAPI Application
**File**: `src/api/main.py`

**Endpoints**:
- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /api/v1/find-jobs` - Find jobs by skills
- `POST /api/v1/find-skills` - Find skills by job title
- `POST /api/v1/extract-skills` - Extract & validate from text
- `GET /api/v1/stats` - System statistics

**Features**:
- Automatic OpenAPI docs (`/docs`)
- CORS middleware
- Error handling
- Async operations
- Request validation

### 7. CLI Tool
**File**: `scripts/cli.py`

**Commands**:
- `init-db` - Initialize Neo4j schema
- `clear-db` - Clear database
- `extract` - Extract skills from jobs
- `normalize` - Normalize and cluster skills
- `infer-hierarchy` - Build skill hierarchy
- `load-db` - Load data into Neo4j
- `stats` - Display database statistics
- `serve` - Start FastAPI server
- `pipeline` - Run complete pipeline

## Architecture Decisions

### Database Choice: Neo4j Only
**Decision**: Use only Neo4j (not Neo4j + Weaviate)

**Rationale**:
- Neo4j 5.x has native vector search
- Single database = simpler deployment
- No sync issues between databases
- Neo4j Browser provides excellent visualization

### LLM: GPT-4.1 via OpenRouter
**Decision**: Use OpenRouter instead of direct Anthropic

**Rationale**:
- Access to GPT-4.1 (latest model)
- Cost-effective alternative
- Compatible with OpenAI client library

### Hierarchical Taxonomy
**Decision**: Implement full parent-child relationships

**Rationale**:
- Enables skill recommendations
- Supports implicit matching (Django → Python)
- Provides skill progression paths

## File Statistics

```
Total Python files: 16
Total lines of code: ~3,500
Total documentation: ~1,200 lines
Test files: 2

Directory structure:
├── src/
│   ├── api/ (3 files)
│   ├── database/ (3 files)
│   ├── extraction/ (3 files)
│   ├── normalization/ (3 files)
│   └── models/ (2 files)
├── scripts/ (4 files)
├── tests/ (2 files)
└── config/ (2 files)
```

## Testing

**Files**:
- `tests/unit/test_models.py` - Model validation tests
- `tests/integration/test_api.py` - API endpoint tests

**Coverage**:
- Pydantic model validation
- API endpoint responses
- Error handling
- Request/response formats

## Performance Optimizations

### 1. Bulk Operations
All inserts use `UNWIND` for batch processing - 1 query for all items instead of 1 query per item.

### 2. Connection Pooling
```python
AsyncGraphDatabase.driver(
    uri,
    max_connection_pool_size=50,
    connection_acquisition_timeout=30.0
)
```

### 3. Caching
- Deduplication cache for extracted skills
- Hash-based lookup to avoid re-extracting duplicates

### 4. Async Processing
- AsyncIO for all I/O operations
- 50 concurrent LLM requests
- Non-blocking database operations

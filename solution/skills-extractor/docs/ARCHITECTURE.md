# System Architecture

## Overview

The Skills Taxonomy System is an LLM-based skill extraction and job matching system with hierarchical taxonomy. It extracts skills from job descriptions using GPT-4, normalizes them using embedding-based clustering, infers hierarchical relationships, and stores everything in a Neo4j graph database.

## Architecture Diagram

```
┌─────────────────┐
│  Job Postings   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│  LLM Extractor  │────►│  GPT-4 (OR)  │
└────────┬────────┘     └──────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│  Normalizer     │────►│  Embeddings  │
└────────┬────────┘     └──────────────┘
         │
         ▼
┌─────────────────┐
│  Hierarchy      │
│  Inference      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│     Neo4j       │◄───►│  FastAPI     │
│   (Graph DB)    │     │     API      │
└─────────────────┘     └──────────────┘
```

## Pipeline Phases

### Phase 0: Initialize Database
- Create Neo4j constraints (unique IDs)
- Create indexes (full-text search, vector search)
- Initialize schema for Job and Skill nodes

### Phase 1: Skill Extraction (LLM)
**File**: `src/extraction/extractor.py`

**Process**:
1. Read CSV file with job descriptions
2. Batch jobs (50 per batch)
3. Extract skills using GPT-4 via OpenRouter
4. Save checkpoint after each batch

**Output Format**:
```json
{
  "job_id": "1",
  "job_title": "Python Developer",
  "skills": [
    {
      "name": "Python",
      "category": "technical",
      "confidence": 0.98,
      "required": true,
      "level": "mid"
    }
  ]
}
```

**Features**:
- 50 concurrent requests for speed
- Automatic retry with exponential backoff
- Checkpoint system for resumability
- Deduplication cache (hash-based)

### Phase 2: Skill Normalization
**File**: `src/normalization/normalizer.py`

**Process**:
1. Collect all extracted skills
2. Generate 768-dim embeddings (sentence-transformers/all-mpnet-base-v2)
3. Cluster similar skills using DBSCAN (eps=0.15)
4. Select canonical name (most common in cluster)
5. Build alias mappings

**Example**:
- Input: ["React", "ReactJS", "React.js", "React 18"]
- Output: "React" (canonical) with aliases

### Phase 3: Hierarchy Inference
**File**: `src/normalization/hierarchy.py`

**Inference Methods**:
1. **Known hierarchies**: Predefined relationships (Python → Django)
2. **Substring matching**: "Python Developer" is child of "Python"
3. **Pattern matching**: "{Framework} Developer" implies framework skill

**Example Hierarchy**:
```
Python
├── Django
├── Flask
└── FastAPI

JavaScript
├── React
├── Vue.js
└── Node.js
```

### Phase 4: Database Loading
**File**: `src/database/operations.py`

**Loading Steps**:
1. Create Job nodes (bulk insert)
2. Create Skill nodes with embeddings
3. Create REQUIRES relationships (Job → Skill)
4. Create PARENT_OF relationships (Skill → Skill)

## Database Schema

### Nodes

**Job**:
```cypher
(:Job {
  id: String,
  title: String,
  description: String,
  company: String,
  location: String,
  salary: Float
})
```

**Skill**:
```cypher
(:Skill {
  canonical_name: String,
  category: String,
  aliases: [String],
  embedding: [Float]  // 768 dimensions
})
```

### Relationships

**REQUIRES** (Job → Skill):
```cypher
[:REQUIRES {
  confidence: Float,
  required: Boolean,
  level: String
}]
```

**PARENT_OF** (Skill → Skill):
```cypher
[:PARENT_OF]
```

### Indexes
- Unique constraints on Job.id, Skill.canonical_name
- Full-text search on job titles/descriptions
- Vector index on Skill.embedding (768-dim, cosine)
- B-tree indexes on categories

## Key Technologies

- **LLM**: GPT-4 (via OpenRouter) for extraction
- **Embeddings**: sentence-transformers/all-mpnet-base-v2
- **Clustering**: DBSCAN (scikit-learn)
- **Database**: Neo4j (graph)
- **API**: FastAPI + Uvicorn
- **Processing**: Async Python (asyncio, aiofiles)

## Query Operations

### 1. Find Jobs by Skills
Validates skills (exact → alias → semantic) and queries Neo4j with optional parent inclusion.

### 2. Find Skills by Job
Full-text search on job titles, returns skills with frequencies and confidence.

### 3. Extract & Validate Skills
LLM extraction from free text with three-tier validation pipeline:
1. Exact match
2. Alias match
3. Semantic search (cosine similarity > 0.85)

## Performance

On a typical setup (M1 MacBook Pro, 16GB RAM):
- **Extraction**: ~100 jobs/minute
- **Normalization**: ~5,000 skills/minute
- **Database loading**: ~10,000 relationships/second
- **API queries**: <100ms for most queries

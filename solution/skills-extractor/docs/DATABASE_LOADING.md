# Database Loading Guide

## Overview

This guide explains Phase 4 of the pipeline: loading all processed data into Neo4j.

## Required Input Files

Before starting Phase 4, these files must exist:

| File | Location | Source Phase |
|------|----------|--------------|
| **Original CSV** | `data/job_descriptions.csv` | User provided |
| **Extraction Results** | `data/checkpoints/extraction_checkpoint.json` | Phase 1 |
| **Normalized Skills** | `data/normalized_skills.json` | Phase 2 |
| **Skill Hierarchies** | `data/skill_hierarchies.json` | Phase 3 |

## Loading Process

### Step 1: Create Job Nodes

**Input**: `data/job_descriptions.csv`

**Process**:
1. Read CSV file
2. Extract: id, title, company, location
3. Bulk insert all jobs in ONE transaction

**Cypher Query**:
```cypher
UNWIND $jobs as job
MERGE (j:Job {id: job.id})
SET j.title = job.title,
    j.description = job.description,
    j.company = job.company,
    j.location = job.location,
    j.updated_at = datetime()
```

### Step 2: Create Skill Nodes

**Input**: `data/normalized_skills.json`

**Process**:
1. Load normalized skills with embeddings
2. Bulk insert with vector data

**Cypher Query**:
```cypher
UNWIND $skills as skill
MERGE (s:Skill {canonical_name: skill.canonical_name})
SET s.category = skill.category,
    s.aliases = skill.aliases,
    s.embedding = skill.embedding,
    s.updated_at = datetime()
```

**Note**: Embedding vector stored as 768-float array for similarity search.

### Step 3: Create Job-Skill Relationships

**Inputs**:
- `data/checkpoints/extraction_checkpoint.json` (raw skills)
- `data/normalized_skills.json` (for alias mapping)

**Process**:
1. Build alias mapping (extracted name → canonical name)
2. For each extraction result:
   - Map skill names to canonical forms
   - Create REQUIRES relationships

**Alias Mapping Example**:
```python
{
  "python": "Python",
  "python3": "Python",
  "django": "Django",
  "django-rest": "Django"
}
```

**Cypher Query**:
```cypher
UNWIND $relationships as rel
MATCH (j:Job {id: rel.job_id})
MATCH (s:Skill {canonical_name: rel.skill_name})
MERGE (j)-[r:REQUIRES]->(s)
SET r.confidence = rel.confidence,
    r.required = rel.required,
    r.level = rel.level
```

### Step 4: Create Skill Hierarchies

**Input**: `data/skill_hierarchies.json`

**Process**:
Create PARENT_OF relationships between skills

**Cypher Query**:
```cypher
UNWIND $hierarchies as hierarchy
MATCH (parent:Skill {canonical_name: hierarchy.parent})
MATCH (child:Skill {canonical_name: hierarchy.child})
MERGE (parent)-[r:PARENT_OF]->(child)
```

**Visual Result**:
```
Python ─────┬─────► Django
            │
            ├─────► Flask
            │
            └─────► FastAPI

JavaScript ─┬─────► React
            │
            └─────► Vue.js
```

## Final Schema

### Job Nodes
```cypher
(:Job {
  id: "1",
  title: "Python Developer",
  description: "...",
  company: "TechCorp",
  location: "San Francisco",
  updated_at: datetime()
})
```

### Skill Nodes
```cypher
(:Skill {
  canonical_name: "Python",
  category: "technical",
  aliases: ["python", "Python3"],
  embedding: [0.123, -0.456, ...],  // 768 floats
  updated_at: datetime()
})
```

### Relationships
```cypher
(:Job)-[:REQUIRES {
  confidence: 0.98,
  required: true,
  level: "mid"
}]->(:Skill)

(:Skill)-[:PARENT_OF]->(:Skill)
```

## Performance

On typical hardware (16GB RAM, SSD):

| Operation | Count | Time | Rate |
|-----------|-------|------|------|
| Load Jobs | 4,523 | 0.5s | ~9,000/sec |
| Load Skills | 1,247 | 0.2s | ~6,000/sec |
| Load Relationships | 18,942 | 2.1s | ~9,000/sec |
| Load Hierarchies | 342 | 0.1s | ~3,400/sec |
| **Total** | **24,054** | **~3s** | **~8,000/sec** |

## Query Examples

### Find Jobs Requiring Python
```cypher
MATCH (j:Job)-[r:REQUIRES]->(s:Skill {canonical_name: "Python"})
RETURN j.title, r.confidence, r.level
ORDER BY r.confidence DESC
LIMIT 10
```

### Find All Skills for a Job Title
```cypher
CALL db.index.fulltext.queryNodes('job_fulltext', 'Machine Learning Engineer')
YIELD node as j, score
MATCH (j)-[r:REQUIRES]->(s:Skill)
RETURN s.canonical_name, avg(r.confidence) as avg_conf
ORDER BY avg_conf DESC
```

### Explore Skill Hierarchy
```cypher
MATCH path = (parent:Skill {canonical_name:"Python"})-[:PARENT_OF*1..3]->(child:Skill)
RETURN path
```

### Find Similar Skills (Vector Search)
```cypher
MATCH (s:Skill {canonical_name: "Kubernetes"})
CALL db.index.vector.queryNodes('skill_embeddings', 5, s.embedding)
YIELD node, score
RETURN node.canonical_name, score
ORDER BY score DESC
```

## Running Phase 4

### Using CLI
```bash
python scripts/cli.py load-db --dataset data/job_descriptions.csv
```

### Using Docker
```bash
docker-compose exec web python scripts/cli.py load-db --dataset data/jobs.csv
```

## Troubleshooting

### Missing Files Error
```
Error: Checkpoint file not found
```
**Solution**: Run Phase 1 first (`python scripts/cli.py extract`)

### Connection Error
```
Failed to connect to Neo4j
```
**Solution**:
```bash
# Check if Neo4j is running
docker-compose ps

# Start if needed
docker-compose up -d neo4j
```

### Constraint Violations
Handled automatically by `MERGE` - updates instead of failing.

## Data Persistence

Phase 4 is **idempotent** (safe to run multiple times):
- Updates existing nodes
- Skips duplicate relationships
- No errors on re-run

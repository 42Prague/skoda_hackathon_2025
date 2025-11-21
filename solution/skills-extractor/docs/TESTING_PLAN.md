# Testing Plan

## Overview

This document outlines the testing strategy for the Skills Taxonomy System, from small-scale verification to large-scale testing.

## Phase 1: Small Scale Test (10 Jobs)

### 1.1 Prepare Environment
```bash
# Clear existing data
python scripts/cli.py clear-db --yes

# Remove checkpoints
rm -f data/checkpoints/*.json
rm -f data/*.json
```

### 1.2 Run Pipeline
```bash
python scripts/cli.py pipeline --dataset data/sample_jobs.csv
```

**Expected Duration**: ~5 minutes

**Expected Output**:
- Phase 0: Database initialized
- Phase 1: 10 jobs extracted → ~50-80 skills
- Phase 2: Normalized → ~50 canonical skills
- Phase 3: Hierarchy → ~30 relationships
- Phase 4: Loaded into Neo4j
- Phase 5: Statistics displayed

### 1.3 Verify Results

**Check Database Stats**:
```bash
python scripts/cli.py stats
```

**Expected Stats**:
- Total jobs: 10
- Total skills: ~50-80
- Job-skill relationships: ~80-100
- Hierarchical relationships: ~30-60

## Phase 2: API Testing

### 2.1 Start API Server
```bash
python scripts/cli.py serve --port 8000
```

### 2.2 Test Endpoints

**Test 1: Find Jobs by Skill**
```bash
curl -X POST "http://localhost:8000/api/v1/find-jobs" \
  -H "Content-Type: application/json" \
  -d '{"skills": ["Python"], "limit": 5}'
```

**Test 2: Find Skills by Job Title**
```bash
curl -X POST "http://localhost:8000/api/v1/find-skills" \
  -H "Content-Type: application/json" \
  -d '{"job_title": "Machine Learning Engineer"}'
```

**Test 3: Extract & Validate Skills**
```bash
curl -X POST "http://localhost:8000/api/v1/extract-skills" \
  -H "Content-Type: application/json" \
  -d '{"text": "I know Django, kuberntes, and React"}'
```

**Expected Results**:
- Validated: Django, React
- Semantic match: "kuberntes" → "Kubernetes"

**Test 4: System Statistics**
```bash
curl "http://localhost:8000/api/v1/stats"
```

## Phase 3: Neo4j Browser Testing

### 3.1 Access Neo4j Browser
Open http://localhost:7474
- Username: `neo4j`
- Password: `skillspassword`

### 3.2 Run Queries

**Query 1: View Skill Hierarchy**
```cypher
MATCH (parent:Skill)-[:PARENT_OF]->(child:Skill)
RETURN parent, child
LIMIT 25
```

**Query 2: Top Required Skills**
```cypher
MATCH (j:Job)-[:REQUIRES]->(s:Skill)
RETURN s.canonical_name, count(j) as jobs
ORDER BY jobs DESC
LIMIT 10
```

**Query 3: Explore Job's Skills**
```cypher
MATCH (j:Job)-[r:REQUIRES]->(s:Skill)
WHERE j.id = "1"
RETURN j, r, s
```

**Query 4: Test Hierarchy Logic**
```cypher
MATCH (child:Skill {canonical_name: "Django"})
OPTIONAL MATCH (parent:Skill)-[:PARENT_OF]->(child)
RETURN child.canonical_name, collect(parent.canonical_name) as parents
```
**Expected**: Django should have Python as parent

## Phase 4: Large Scale Test (10,000 Jobs)

### 4.1 Prerequisites
- Confirm 10-job test passed all checks
- Ensure sufficient disk space (~500MB)
- Verify API rate limits

### 4.2 Run Full Pipeline
```bash
python scripts/cli.py clear-db --yes
python scripts/cli.py pipeline --dataset data/job_descriptions.csv --limit 10000
```

**Expected Duration**: ~2-3 hours
- Phase 1 (Extraction): ~90-120 min
- Phase 2 (Normalization): ~5-10 min
- Phase 3 (Hierarchy): ~2 min
- Phase 4 (Load): ~5 min

### 4.3 Validate Large Scale
```bash
python scripts/cli.py stats
```

**Expected Stats**:
- Total jobs: 10,000
- Total skills: ~500-1,000 (normalized)
- Relationships: ~80,000-100,000
- Hierarchical: ~200-400

## Success Criteria

### 10-Job Test
- ✅ All phases complete without errors
- ✅ Hierarchy logic correct (child → parent)
- ✅ API returns expected results
- ✅ Data persists after restart

### 10,000-Job Test
- ✅ Completes in < 4 hours
- ✅ < 1% job failures
- ✅ All data persisted to Neo4j
- ✅ API performance acceptable (< 500ms per query)
- ✅ Memory usage stable (< 8GB)

## Unit Tests

### Run All Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/unit/test_models.py

# Run integration tests (requires running Neo4j)
pytest tests/integration/
```

## Data Persistence

### Neo4j (Primary Database)
- **Storage**: Docker volume `neo4j_data`
- **Persists**: All nodes and relationships
- **Survives**: Container restarts, system reboots

### Checkpoints (Resume Capability)
- **File**: `data/checkpoints/pipeline_checkpoint.json`
- **Purpose**: Resume failed pipelines

### Cache (Performance)
- **File**: `data/cache/extractions/dedup_cache.json`
- **Purpose**: Avoid re-extracting duplicate job descriptions

## Rollback Plan

If issues occur during large-scale run:
1. Pipeline auto-resumes from last checkpoint
2. Cached extractions are reused
3. Manual resume: `python scripts/cli.py extract --dataset data/jobs.csv --limit 10000`

## Troubleshooting

### Neo4j Not Starting
```bash
docker-compose logs neo4j
docker-compose restart neo4j
```

### API Errors
```bash
# Check OpenRouter API key
grep OPENROUTER_API_KEY .env
```

### Pipeline Crashes
```bash
# Resume from last checkpoint
python scripts/cli.py extract --dataset data/sample_jobs.csv
```

### Out of Memory
```bash
# Process fewer jobs at a time
python scripts/cli.py pipeline --dataset data/jobs.csv --limit 50
```

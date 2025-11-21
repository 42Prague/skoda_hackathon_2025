# Skills Taxonomy System

LLM-based skill extraction and job matching system with hierarchical taxonomy.

## Overview

This system extracts skills from job descriptions using GPT-4, normalizes them using embedding-based clustering, infers hierarchical relationships, and stores everything in a Neo4j graph database for efficient querying.

### Key Features

- **LLM-Powered Extraction**: Uses GPT-4 to extract skills from job descriptions
- **Smart Normalization**: Clusters similar skills using sentence embeddings (DBSCAN)
- **Hierarchical Taxonomy**: Automatically infers parent-child relationships (e.g., "Python" → "Django")
- **Graph Database**: Neo4j for fast bidirectional queries with beautiful visualizations
- **REST API**: FastAPI with automatic documentation
- **Semantic Search**: Vector-based similarity matching for skill validation
- **Progress Tracking**: Rich console output with checkpointing for resumability

## Quick Start

### Prerequisites

- Python 3.11+
- OpenRouter API key
- Neo4j (optional - for database storage, use Docker Compose)

### 1. Clone & Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and update your OpenRouter API key
OPENROUTER_API_KEY=your-api-key-here
```

### 3. Prepare Data (No Neo4j Required)

Prepare all data files locally without Neo4j. **Note:** The CSV is only needed for this step.

```bash
# Prepare data for 250 jobs (~3-5 minutes)
source venv/bin/activate
python scripts/cli.py prepare --dataset data/job_descriptions.csv --limit 250 --batch-size 15
```

This will:
1. Extract skills using GPT-4 via OpenRouter
2. Normalize and cluster similar skills
3. Infer skill hierarchies
4. Generate generic job descriptions

**Output files created:**
- `data/checkpoints/extraction_checkpoint.json` - Extracted skills
- `data/normalized_skills.json` - Clustered canonical skills
- `data/skill_hierarchies.json` - Parent-child relationships
- `data/generated_descriptions.json` - Generic descriptions

### 4. Start Services (Auto-loads Data)

```bash
# Start Neo4j and API (automatically loads prepared data)
docker-compose up -d

# Watch the logs to see data loading
docker-compose logs -f web
```

The entrypoint will automatically:
- ✓ Wait for Neo4j to be ready
- ✓ Initialize Neo4j schema
- ✓ Load all prepared data into Neo4j (from JSON files only, CSV not needed)
- ✓ Start the FastAPI server

### 5. Explore!

**API Documentation**: http://localhost:8002/docs

**Neo4j Browser**: http://localhost:7474 (neo4j/skillspassword)

**Try the API**:
```bash
# Find jobs requiring Python
curl -X POST "http://localhost:8002/api/v1/find-jobs" \
  -H "Content-Type: application/json" \
  -d '{"skills": ["Python"], "limit": 5}'

# Extract skills from text
curl -X POST "http://localhost:8002/api/v1/extract-skills" \
  -H "Content-Type: application/json" \
  -d '{"text": "I know Python, Docker, and React"}'

# Get system statistics
curl "http://localhost:8002/api/v1/stats"
```

## Architecture

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

## CLI Commands

### Pipeline Commands

```bash
# Initialize database schema
python scripts/cli.py init-db

# Extract skills from jobs
python scripts/cli.py extract --dataset data/jobs.csv

# Normalize extracted skills
python scripts/cli.py normalize

# Infer skill hierarchies
python scripts/cli.py infer-hierarchy

# Load all data into Neo4j (from prepared JSON files)
python scripts/cli.py load-db

# View database statistics
python scripts/cli.py stats

# Clear database
python scripts/cli.py clear-db --yes

# Start API server
python scripts/cli.py serve

# Run complete pipeline
python scripts/cli.py pipeline --dataset data/jobs.csv
```

### Examples

```bash
# Extract skills with custom batch size
python scripts/cli.py extract \
  --dataset data/jobs.csv \
  --batch-size 100 \
  --limit 500

# Resume from checkpoint
python scripts/cli.py extract \
  --dataset data/jobs.csv \
  --checkpoint my_checkpoint
```

## API Endpoints

### Find Jobs by Skills

```bash
curl -X POST "http://localhost:8002/api/v1/find-jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "skills": ["Python", "Machine Learning", "Docker"],
    "match_all": false,
    "include_parents": true,
    "limit": 10
  }'
```

### Find Skills by Job Title

```bash
curl -X POST "http://localhost:8000/api/v1/find-skills" \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Machine Learning Engineer",
    "include_children": true
  }'
```

### Extract & Validate Skills from Text

```bash
curl -X POST "http://localhost:8000/api/v1/extract-skills" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I have 5 years of experience with Python and Django, working on ML projects using TensorFlow and Docker."
  }'
```

### Get System Statistics

```bash
curl "http://localhost:8000/api/v1/stats"
```

## Neo4j Visualization

### Access Neo4j Browser

1. Open http://localhost:7474
2. Login: `neo4j` / `skillspassword`

### Useful Cypher Queries

**View skill hierarchy:**
```cypher
MATCH (parent:Skill)-[:PARENT_OF]->(child:Skill)
RETURN parent, child
LIMIT 25
```

**Find jobs requiring Python:**
```cypher
MATCH (j:Job)-[r:REQUIRES]->(s:Skill {canonical_name: "Python"})
RETURN j, r, s
LIMIT 10
```

**Top 10 most required skills:**
```cypher
MATCH (j:Job)-[r:REQUIRES]->(s:Skill)
RETURN s.canonical_name, count(j) as job_count
ORDER BY job_count DESC
LIMIT 10
```

## Project Structure

```
skills-extractor/
├── src/
│   ├── extraction/          # LLM-based skill extraction
│   ├── normalization/       # Skill normalization & clustering
│   ├── database/            # Neo4j operations
│   ├── api/                 # FastAPI application
│   └── models/              # Pydantic models
├── scripts/
│   └── cli.py               # CLI tool for pipeline
├── tests/
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
├── config/
│   └── settings.py          # Configuration
├── docs/                    # Detailed documentation
│   ├── ARCHITECTURE.md      # System architecture
│   ├── IMPLEMENTATION.md    # Implementation details
│   ├── DATABASE_LOADING.md  # Database loading guide
│   └── TESTING_PLAN.md      # Testing strategy
├── data/                    # Data directory
├── docker-compose.yml       # Neo4j setup
├── pyproject.toml           # Dependencies
└── README.md                # This file
```

## Configuration

All settings can be configured via environment variables in `.env`:

```env
# OpenRouter Configuration
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4-turbo

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=skillspassword

# LLM Settings
LLM_BATCH_SIZE=50
LLM_MAX_CONCURRENT=50
LLM_TIMEOUT=30

# Normalization Settings
CLUSTERING_EPS=0.15
SEMANTIC_SIMILARITY_THRESHOLD=0.85

# API Settings
API_PORT=8000
```

## Testing

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

## How It Works

### 1. Skill Extraction

Uses GPT-4 to extract skills from job descriptions:

```json
{
  "skills": [
    {
      "name": "Python",
      "category": "technical",
      "confidence": 0.95,
      "required": true,
      "level": "mid"
    }
  ]
}
```

- Processes 50 jobs per batch
- 50 concurrent requests
- Automatic retry with exponential backoff
- Checkpoint system for resumability

### 2. Skill Normalization

Uses sentence embeddings to cluster similar skills:

1. Generate 768-dim embeddings (`all-mpnet-base-v2`)
2. Cluster using DBSCAN (eps=0.15)
3. Select canonical name (most common)
4. Build alias mappings

Example: `["React", "ReactJS", "React.js"]` → `"React"`

### 3. Hierarchy Inference

Infers parent-child relationships:
- Known hierarchies (Python → Django)
- Substring matching
- Pattern matching

```
Python
├── Django
├── Flask
└── FastAPI
```

### 4. Graph Database

Neo4j stores:
- **Nodes**: Job, Skill
- **Relationships**: REQUIRES, PARENT_OF
- **Indexes**: Full-text, vector (768-dim)

## Troubleshooting

### Neo4j Connection Issues

```bash
# Check if Neo4j is running
docker-compose ps

# View logs
docker-compose logs neo4j

# Restart Neo4j
docker-compose restart neo4j
```

### LLM API Errors

- **Rate limiting**: Reduce `LLM_MAX_CONCURRENT` in `.env`
- **Timeout**: Increase `LLM_TIMEOUT`
- **Invalid API key**: Check `OPENROUTER_API_KEY`

### Memory Issues

- Process in smaller batches using `--limit`
- Embedding model needs ~2GB RAM

### Checkpoint Recovery

```bash
# Resume from last checkpoint
python scripts/cli.py extract --dataset data/jobs.csv

# Or start fresh
python scripts/cli.py extract --dataset data/jobs.csv --no-resume
```

## Performance

On typical hardware (M1 MacBook Pro, 16GB RAM):

- **Extraction**: ~100 jobs/minute
- **Normalization**: ~5,000 skills/minute
- **Database loading**: ~10,000 relationships/second
- **API queries**: <100ms

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System design and data flow
- **[Implementation](docs/IMPLEMENTATION.md)** - Technical implementation details
- **[Database Loading](docs/DATABASE_LOADING.md)** - Guide to Phase 4 of the pipeline
- **[Testing Plan](docs/TESTING_PLAN.md)** - Testing strategy and verification

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- **OpenRouter** for GPT-4 access
- **Neo4j** for the graph database
- **Sentence Transformers** for embedding models
- **FastAPI** for the web framework

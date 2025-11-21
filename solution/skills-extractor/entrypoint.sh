#!/bin/bash
set -e

echo "========================================="
echo "  Skills Taxonomy - Container Startup"
echo "========================================="

# Wait for Neo4j to be ready
echo "Waiting for Neo4j to be ready..."
until python3 -c "
from neo4j import GraphDatabase
import sys
try:
    driver = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', 'skillspassword'))
    driver.verify_connectivity()
    driver.close()
    sys.exit(0)
except Exception as e:
    sys.exit(1)
" 2>/dev/null; do
    echo "  Neo4j not ready yet, waiting..."
    sleep 2
done
echo "  Neo4j is ready!"

# Check if database already has data
echo "Checking if database needs initialization..."
JOB_COUNT=$(python3 -c "
from neo4j import GraphDatabase
driver = GraphDatabase.driver('bolt://neo4j:7687', auth=('neo4j', 'skillspassword'))
with driver.session() as session:
    result = session.run('MATCH (j:Job) RETURN count(j) as count')
    count = result.single()['count']
    print(count)
driver.close()
" 2>/dev/null || echo "0")

if [ "$JOB_COUNT" -eq 0 ]; then
    echo "Database is empty - checking for prepared data..."

    # Check if required data files exist
    REQUIRED_FILES=(
        "/app/data/checkpoints/extraction_checkpoint.json"
        "/app/data/normalized_skills.json"
        "/app/data/skill_hierarchies.json"
    )

    FILES_MISSING=0
    for file in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            echo "  ⚠ Missing: $file"
            FILES_MISSING=1
        fi
    done

    if [ $FILES_MISSING -eq 0 ]; then
        echo "  ✓ All required data files found"
        echo ""
        echo "  Initializing Neo4j schema..."
        python3 scripts/cli.py init-db

        echo "  Loading prepared data into Neo4j..."
        python3 scripts/cli.py load-db --checkpoint extraction_checkpoint

        echo "  ✓ Data loading complete!"
    else
        echo ""
        echo "  ⚠ Cannot load data - missing required files"
        echo "  Run 'python scripts/cli.py prepare' to generate data files first"
    fi
else
    echo "Database already contains $JOB_COUNT jobs - skipping initialization"
fi

echo ""
echo "========================================="
echo "  Starting FastAPI Server"
echo "========================================="
echo ""

# Start the API server
exec uvicorn src.api.main:app --host 0.0.0.0 --port 8000

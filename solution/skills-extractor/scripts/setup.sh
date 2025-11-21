#!/bin/bash

# Quick setup script for Skills Taxonomy System

set -e

echo "╔═══════════════════════════════════════════╗"
echo "║   Skills Taxonomy System - Setup         ║"
echo "╔═══════════════════════════════════════════╗"
echo ""

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version"

# Check Docker
echo ""
echo "🐳 Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi
echo "✅ Docker installed"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi
echo "✅ Docker Compose installed"

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
if command -v poetry &> /dev/null; then
    echo "Using Poetry..."
    poetry install
else
    echo "Using pip..."
    pip install -e .
fi
echo "✅ Dependencies installed"

# Create .env if it doesn't exist
echo ""
echo "⚙️  Setting up environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file (please update with your API keys)"
else
    echo "✅ .env file already exists"
fi

# Create data directories
echo ""
echo "📁 Creating directories..."
mkdir -p data/checkpoints data/cache
echo "✅ Directories created"

# Start Neo4j
echo ""
echo "🚀 Starting Neo4j..."
docker-compose up -d

# Wait for Neo4j to be ready
echo "⏳ Waiting for Neo4j to start..."
sleep 10

# Check Neo4j health
if docker-compose ps | grep -q "Up"; then
    echo "✅ Neo4j is running"
else
    echo "❌ Neo4j failed to start. Check logs with: docker-compose logs"
    exit 1
fi

echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║   Setup Complete! 🎉                     ║"
echo "╚═══════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "1. Update .env with your OpenRouter API key"
echo ""
echo "2. Download the dataset:"
echo "   ./scripts/download_dataset.sh"
echo ""
echo "3. Run the pipeline:"
echo "   python scripts/cli.py pipeline --dataset data/job_descriptions.csv --limit 100"
echo ""
echo "4. Start the API:"
echo "   python scripts/cli.py serve"
echo ""
echo "Useful URLs:"
echo "  • Neo4j Browser: http://localhost:7474 (neo4j / skillspassword)"
echo "  • API Docs: http://localhost:8000/docs (after starting API)"
echo ""

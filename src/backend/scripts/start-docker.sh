#!/bin/bash
# Start ŠKODA Skill Coach in Docker for Production Testing

set -e

echo "🐳 Starting ŠKODA Skill Coach in Docker..."
echo "=========================================="

cd "$(dirname "$0")/.."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please update it with your configuration."
    else
        echo "❌ .env.example not found. Please create .env manually."
        exit 1
    fi
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check docker compose version
if ! docker compose version > /dev/null 2>&1; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Build and start services
echo "🔨 Building Docker images..."
docker compose build

echo "🚀 Starting services..."
docker compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "✅ Services started!"
echo ""
echo "📍 Access Points:"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Adminer: http://localhost:8080"
echo "   - pgAdmin: http://localhost:5050"
echo ""
echo "📋 Useful Commands:"
echo "   - View logs: docker compose logs -f backend"
echo "   - Stop services: docker compose down"
echo "   - Restart: docker compose restart backend"
echo "   - Shell access: docker compose exec backend bash"
echo ""

# Wait a bit and check health
echo "🏥 Checking health..."
sleep 5

if curl -f http://localhost:8000/healthz > /dev/null 2>&1; then
    echo "✅ Backend is healthy!"
else
    echo "⚠️  Backend health check failed. Check logs: docker compose logs backend"
fi

echo ""
echo "🎉 Done! Services are running."

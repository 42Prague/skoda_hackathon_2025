#!/bin/bash

# Test Docker container data mounting

echo "🐳 Testing Docker Data Configuration"
echo "====================================="
echo ""

echo "1️⃣ Checking docker-compose.yml for volume mounts..."
if grep -q "skoda_data:/app/skoda_data" docker-compose.yml 2>/dev/null; then
    echo "   ✅ Found skoda_data volume mount"
elif grep -q "./skoda_data:/app/skoda_data" docker-compose.yml 2>/dev/null; then
    echo "   ✅ Found skoda_data bind mount"
else
    echo "   ⚠️  Note: Check docker-compose.yml for skoda_data mounting"
fi
echo ""

echo "2️⃣ Checking backend docker-compose.yml..."
if [ -f "backend/docker-compose.yml" ]; then
    if grep -q "skoda_data" backend/docker-compose.yml; then
        echo "   ✅ Backend docker-compose references skoda_data"
    else
        echo "   ℹ️  Backend docker-compose found (check configuration)"
    fi
else
    echo "   ℹ️  No separate backend docker-compose.yml"
fi
echo ""

echo "3️⃣ Data files available for mounting:"
echo "   📁 skoda_data/ contains:"
ls -1 skoda_data/*.csv 2>/dev/null | wc -l | xargs -I {} echo "      - {} CSV files"
ls -1 skoda_data/*.py 2>/dev/null | wc -l | xargs -I {} echo "      - {} Python scripts"
echo ""

echo "✅ Docker configuration check complete!"
echo ""
echo "To test with Docker:"
echo "  docker-compose up --build"
echo ""
echo "The backend will automatically use:"
echo "  • /app/skoda_data (in Docker)"
echo "  • Data stored in PostgreSQL container"
echo ""

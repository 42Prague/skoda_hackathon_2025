#!/bin/bash
# Start backend server

cd "$(dirname "$0")/srcs/server"
echo "🚀 Starting backend server..."
echo "📍 Server will be available at http://localhost:5000"
echo ""
python3 run.py


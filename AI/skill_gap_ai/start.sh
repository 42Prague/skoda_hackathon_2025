#!/bin/bash
# Quick start script for Skill Gap AI API

echo "======================================================================="
echo "🚀 SKILL GAP AI - STARTUP"
echo "======================================================================="
echo ""

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

echo "✅ Environment activated"
echo ""

# Start API server
echo "🌐 Starting API server..."
echo "   API will be available at: http://localhost:5000"
echo "   Press Ctrl+C to stop"
echo ""
echo "🎨 Opening demo page in browser..."
echo ""

# Open demo page
xdg-open demo.html &

# Start API
python api.py

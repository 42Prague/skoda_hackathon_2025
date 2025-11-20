#!/bin/bash

# AI Skill Coach - Quick Start Script
# Starts both backend and frontend servers

set -e

echo "🚀 Starting AI Skill Coach..."
echo ""

# Check if backend virtual environment exists
if [ ! -d "backend/venv" ]; then
    echo "❌ Backend virtual environment not found!"
    echo "Please run: cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if frontend node_modules exists
if [ ! -d "frontend/node_modules" ]; then
    echo "❌ Frontend dependencies not installed!"
    echo "Please run: cd frontend && npm install"
    exit 1
fi

# Start backend
echo "🔧 Starting backend server..."
cd backend
./venv/bin/python main.py > backend.log 2>&1 &
BACKEND_PID=$!
cd ..
sleep 2

# Check if backend started successfully
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend running on http://localhost:8000 (PID: $BACKEND_PID)"
else
    echo "❌ Backend failed to start. Check backend/backend.log"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Start frontend
echo "🎨 Starting frontend server..."
cd frontend
npm run dev > frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
sleep 3

# Check if frontend started successfully
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✅ Frontend running on http://localhost:5173 (PID: $FRONTEND_PID)"
else
    echo "❌ Frontend failed to start. Check frontend/frontend.log"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    exit 1
fi

echo ""
echo "🎉 AI Skill Coach is ready!"
echo ""
echo "📋 URLs:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "💡 To stop the servers:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "📝 Logs:"
echo "   Backend:  backend/backend.log"
echo "   Frontend: frontend/frontend.log"
echo ""

# Save PIDs for stopping later
echo "$BACKEND_PID $FRONTEND_PID" > .pids

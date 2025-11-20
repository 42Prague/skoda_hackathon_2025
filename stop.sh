#!/bin/bash

# AI Skill Coach - Stop Script
# Stops both backend and frontend servers

echo "🛑 Stopping AI Skill Coach servers..."

if [ -f ".pids" ]; then
    PIDS=$(cat .pids)
    for PID in $PIDS; do
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            echo "✅ Stopped process $PID"
        fi
    done
    rm .pids
else
    echo "⚠️  No PID file found. Attempting to find and stop processes..."
    pkill -f "python.*main.py" || true
    pkill -f "vite" || true
    echo "✅ Sent stop signals to matching processes"
fi

echo "✅ Servers stopped"

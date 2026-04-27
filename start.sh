#!/usr/bin/env bash

echo "Starting CraveAI Stack..."

# Determine python command
PYTHON="python"
if [ -d ".venv" ]; then
    PYTHON="$(pwd)/.venv/bin/python"
fi

# Run Backend
echo "Starting FastAPI Backend on port 8000..."
"$PYTHON" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# Run Frontend
echo "Starting Vanilla JS Frontend on port 5173..."
cd frontend
"$PYTHON" -m http.server 5173 &
FRONTEND_PID=$!
cd ..

echo "Backend running at: http://localhost:8000"
echo "Frontend running at: http://localhost:5173"
echo "Press Ctrl+C to stop both servers."

# Trap SIGINT to kill both processes
trap "echo 'Stopping servers...'; kill $BACKEND_PID; kill $FRONTEND_PID; exit 0" SIGINT

wait $BACKEND_PID $FRONTEND_PID

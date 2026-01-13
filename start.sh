#!/usr/bin/env bash
# Start script for Render with Python 3

echo "🚀 Starting application..."

# Use python3 explicitly
PYTHON_CMD="python3"
if command -v python3 &> /dev/null; then
    echo "Using python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo "Using python"
else
    # Try the Render virtual environment path
    PYTHON_CMD="/opt/render/project/src/.venv/bin/python"
    echo "Using venv python"
fi

echo "Python command: $PYTHON_CMD"

# Wait a bit
sleep 2

# Run migrations
echo "📦 Running database migrations..."
$PYTHON_CMD -m alembic upgrade head || echo "Migrations may have failed or already applied"

# Start server
echo "🌐 Starting FastAPI server..."
exec $PYTHON_CMD -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --log-level info

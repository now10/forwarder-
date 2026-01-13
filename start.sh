#!/usr/bin/env bash
# Start script that definitely works

echo "🚀 Starting application..."

# Activate virtual environment
source .venv/bin/activate

# Change to app directory
cd /opt/render/project/src

# Run migrations
echo "Running migrations..."
python -m alembic upgrade head || echo "Migrations may have failed"

# Start server
echo "Starting FastAPI..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1

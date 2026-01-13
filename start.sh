#!/usr/bin/env bash
# Render Start Script - Fixed for command not found

echo "🚀 Starting Telegram Forwarder SaaS on Render..."

# Set Python path explicitly
PYTHON_PATH="/opt/render/project/src/.venv/bin/python3"
UVICORN_PATH="/opt/render/project/src/.venv/bin/uvicorn"
echo "Python path: $PYTHON_PATH"

# Wait for services
sleep 3

# Run database migrations (skip if fails)
echo "📦 Attempting database migrations..."
$PYTHON_PATH -m alembic upgrade head || echo "Migrations failed or already applied"

# Start the application
echo "🌐 Starting FastAPI server..."
exec $UVICORN_PATH app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 1 \
    --timeout-keep-alive 30 \
    --log-level info

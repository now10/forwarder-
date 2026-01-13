#!/usr/bin/env bash
# Render Start Script

echo "🚀 Starting Telegram Forwarder SaaS..."

# Wait for PostgreSQL to be ready (Render handles this automatically)
# But we can add a small delay for safety
sleep 2

# Run database migrations
echo "📦 Running database migrations..."
python -m alembic upgrade head

# Start the FastAPI application
echo "🌐 Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4
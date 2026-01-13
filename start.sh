#!/usr/bin/env bash
# Render Start Script - Simplified

echo "🚀 Starting Telegram Forwarder SaaS on Render..."

# Wait for PostgreSQL to be ready
sleep 3

# Run database migrations (skip if fails)
echo "📦 Attempting database migrations..."
python -m alembic upgrade head || echo "Migrations failed or already applied"

# Start the application with single worker (free tier)
echo "🌐 Starting FastAPI server..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 1 \
    --timeout-keep-alive 30 \
    --log-level info

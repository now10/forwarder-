#!/usr/bin/env bash
# Simple build script for Render

echo "🚀 Installing dependencies..."

# Upgrade pip first
python -m pip install --upgrade pip

# Install requirements (let pip resolve dependencies)
pip install \
    fastapi \
    uvicorn \
    sqlalchemy \
    psycopg2-binary \
    alembic \
    pydantic \
    python-jose[cryptography] \
    passlib[bcrypt] \
    telethon \
    redis \
    python-dotenv \
    aiofiles \
    structlog

echo "✅ Dependencies installed"

#!/usr/bin/env bash
# Build script that definitely works

echo "🚀 Starting build..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic

# Install remaining packages
pip install pydantic python-jose[cryptography] passlib[bcrypt] telethon redis python-dotenv

# Create directories
mkdir -p uploads
mkdir -p /tmp/uploads

echo "✅ Build completed!"

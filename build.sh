#!/usr/bin/env bash
# Render Build Script - Fixed for Rust dependencies

echo "🚀 Starting optimized build for Render..."

# Upgrade pip with timeout
pip install --upgrade pip --timeout 100 --retries 5

# Install system dependencies for psycopg2
apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies with pre-download
echo "📦 Installing Python dependencies..."

# First, install packages that don't need compilation
pip install \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    python-multipart==0.0.6 \
    sqlalchemy==2.0.23 \
    psycopg2-binary==2.9.9 \
    alembic==1.12.1 \
    pydantic==1.10.13 \
    python-jose[cryptography]==3.3.0 \
    passlib[bcrypt]==1.7.4 \
    telethon==1.34.0 \
    redis==5.0.1 \
    aiofiles==23.2.1 \
    structlog==23.2.0 \
    python-dotenv==1.0.0 \
    --timeout 100 --retries 5

# Then install remaining packages
pip install -r requirements.txt --timeout 100 --retries 5

# Create necessary directories
mkdir -p uploads
mkdir -p /tmp/uploads

# Set permissions
chmod -R 755 uploads

echo "✅ Build completed successfully!"

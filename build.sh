#!/usr/bin/env bash
# Render Build Script - Fixed for Python path

echo "🚀 Starting build process on Render..."

# Set Python path explicitly
PYTHON_PATH="/opt/render/project/src/.venv/bin/python3"
echo "Python path: $PYTHON_PATH"

# Upgrade pip
$PYTHON_PATH -m pip install --upgrade pip

# Install system dependencies for psycopg2
apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
echo "📦 Installing Python dependencies..."
$PYTHON_PATH -m pip install -r requirements.txt --timeout 100 --retries 5

# Create necessary directories
mkdir -p uploads
mkdir -p /tmp/uploads

# Set permissions
chmod -R 755 uploads

echo "✅ Build completed successfully!"

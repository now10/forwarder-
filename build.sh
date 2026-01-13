#!/usr/bin/env bash
# Build script for Render

echo "🚀 Starting build..."

# Use python3 for everything
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "Using Python: $PYTHON_CMD"

# Upgrade pip using the detected Python
$PYTHON_CMD -m pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
$PYTHON_CMD -m pip install -r requirements.txt

# Create directories
mkdir -p uploads
mkdir -p /tmp/uploads
chmod -R 755 uploads

echo "✅ Build completed!"

#!/usr/bin/env bash
# Render Build Script

echo "🚀 Starting build process..."

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
pip install -r requirements.txt

# Install PostgreSQL client for psycopg2
# Note: Render automatically provides PostgreSQL

# Create uploads directory if it doesn't exist
mkdir -p uploads

# Set proper permissions
chmod -R 755 uploads

echo "✅ Build completed!"
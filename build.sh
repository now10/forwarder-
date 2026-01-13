#!/bin/bash
# Build script without tput

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
RESET='\033[0m'

echo -e "${BLUE}🚀 Starting build process...${RESET}"

# Install system dependencies
apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${RESET}"
pip install --upgrade pip
pip install -r requirements.txt --timeout 100 --retries 5

# Create directories
mkdir -p uploads
mkdir -p /tmp/uploads
chmod -R 755 uploads

echo -e "${GREEN}✅ Build completed successfully!${RESET}"

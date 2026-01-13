#!/bin/bash
# Start script without tput

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
RESET='\033[0m'

echo -e "${BLUE}🚀 Starting Telegram Forwarder SaaS...${RESET}"

# Wait for PostgreSQL
sleep 2

# Run migrations
echo -e "${BLUE}📦 Running database migrations...${RESET}"
python -m alembic upgrade head || echo -e "${RED}⚠️  Migrations failed or already applied${RESET}"

# Start server
echo -e "${BLUE}🌐 Starting FastAPI server...${RESET}"
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1

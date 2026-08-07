#!/bin/bash
# deploy.sh - One-click Koyeb deployment script

set -e

echo "🚀 Deploying Engineers Babu Bot to Koyeb..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for BOT_TOKEN
if [ -z "$BOT_TOKEN" ]; then
    echo -e "${RED}❌ BOT_TOKEN is not set!${NC}"
    echo "Please set BOT_TOKEN environment variable"
    echo "Example: export BOT_TOKEN=your_bot_token"
    exit 1
fi

# Check if Koyeb CLI is installed
if ! command -v koyeb &> /dev/null; then
    echo -e "${YELLOW}🔧 Koyeb CLI not found. Installing...${NC}"
    curl -fsSL https://cli.koyeb.com/install.sh | sh
fi

# Check login status
if ! koyeb whoami &> /dev/null; then
    echo -e "${YELLOW}🔑 Please login to Koyeb...${NC}"
    koyeb login
fi

# Deploy
echo -e "${GREEN}📦 Building and deploying...${NC}"
koyeb service deploy bot \
    --app engineers-babu-bot \
    --region singapore \
    --docker python:3.10-slim \
    --command "bash start-koyeb.sh" \
    --port 8080 \
    --env API_ID=21705536 \
    --env API_HASH=c5bb241f6e3ecf33fe68a444e288de2d \
    --env BOT_TOKEN=$BOT_TOKEN \
    --env AUTH_USERS=1147534909,5957208798 \
    --env WEBHOOK=false \
    --env PORT=8080 \
    --instance-type micro

echo -e "${GREEN}✅ Deployment triggered!${NC}"
echo -e "${GREEN}📊 Check status: koyeb service logs bot --app engineers-babu-bot${NC}"

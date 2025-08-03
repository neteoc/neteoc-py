#!/bin/bash
# Production deployment check script for NetEOC
# This script loads production environment settings and runs Django deployment checks

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}NetEOC Production Deployment Check${NC}"
echo "=================================="

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo -e "${RED}Error: .env.production file not found!${NC}"
    echo "Please create .env.production with your production settings."
    echo "You can use .env.production as a template (but don't commit it!)."
    exit 1
fi

# Backup current .env if it exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}Backing up current .env file...${NC}"
    cp .env .env.backup
fi

# Copy production settings to .env temporarily
echo -e "${YELLOW}Loading production environment settings...${NC}"
cp .env.production .env

# Function to cleanup on exit
cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"
    rm -f .env
    if [ -f ".env.backup" ]; then
        echo -e "${YELLOW}Restoring original .env file...${NC}"
        mv .env.backup .env
    fi
}

# Set trap to cleanup on script exit
trap cleanup EXIT

echo -e "${YELLOW}Running Django deployment checks...${NC}"
echo ""

# Run the deployment check
if uv run python manage.py check --deploy; then
    echo ""
    echo -e "${GREEN}✓ All deployment checks passed!${NC}"
    echo -e "${GREEN}Your application is ready for production deployment.${NC}"
else
    echo ""
    echo -e "${RED}✗ Deployment checks failed!${NC}"
    echo -e "${RED}Please review the errors above and update your .env.production file.${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Additional checks you should perform:${NC}"
echo "• Verify DATABASE_URL points to your production database"
echo "• Confirm AWS/Cloudflare R2 credentials are correct"
echo "• Test SSL certificates and domain configuration"
echo "• Verify ALLOWED_HOSTS includes all production domains"
echo "• Review CSRF_TRUSTED_ORIGINS for your domains"

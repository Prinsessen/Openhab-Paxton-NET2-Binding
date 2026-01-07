#!/bin/bash

# Net2 Binding Deployment Script
# SAFE: Only deploys to local OpenHAB, no system file modifications

set -e

BINDING_DIR="/etc/openhab/net2-binding"
TARGET_JAR="${BINDING_DIR}/target/org.openhab.binding.net2-5.1.0.jar"
OPENHAB_ADDONS="/opt/openhab/addons"
BACKUP_DIR="${OPENHAB_ADDONS}/.backup"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo "Net2 Binding Deployment Script"
echo -e "${BLUE}================================================${NC}"

# Check if JAR exists
if [ ! -f "$TARGET_JAR" ]; then
    echo -e "${RED}Error: JAR file not found: $TARGET_JAR${NC}"
    echo "Build first with: cd $BINDING_DIR && ./build.sh"
    exit 1
fi

# Check if OpenHAB addons directory exists
if [ ! -d "$OPENHAB_ADDONS" ]; then
    echo -e "${RED}Error: OpenHAB addons directory not found: $OPENHAB_ADDONS${NC}"
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check for existing binding
EXISTING_JAR=$(find "$OPENHAB_ADDONS" -maxdepth 1 -name "org.openhab.binding.net2-*.jar" 2>/dev/null | head -1)

if [ -n "$EXISTING_JAR" ]; then
    echo -e "${YELLOW}Found existing binding: $EXISTING_JAR${NC}"
    
    # Backup existing
    BACKUP_NAME="org.openhab.binding.net2-$(date +%Y%m%d-%H%M%S).jar"
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"
    
    echo "Backing up to: $BACKUP_PATH"
    cp "$EXISTING_JAR" "$BACKUP_PATH"
    
    # Remove old
    echo "Removing old binding: $EXISTING_JAR"
    rm "$EXISTING_JAR"
    
    echo -e "${GREEN}✓ Backup created${NC}"
fi

# Deploy new binding
echo ""
echo -e "${YELLOW}Deploying new binding...${NC}"
cp "$TARGET_JAR" "$OPENHAB_ADDONS/"

if [ -f "${OPENHAB_ADDONS}/org.openhab.binding.net2-5.1.0.jar" ]; then
    echo -e "${GREEN}✓ JAR deployed successfully${NC}"
else
    echo -e "${RED}✗ Deployment failed${NC}"
    exit 1
fi

# Ask about restart
echo ""
echo -e "${BLUE}Deployment complete!${NC}"
echo ""
echo "Binding location: ${OPENHAB_ADDONS}/org.openhab.binding.net2-5.1.0.jar"
echo ""

read -p "Do you want to restart OpenHAB now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Restarting OpenHAB...${NC}"
    sudo systemctl restart openhab
    
    # Wait for startup
    sleep 5
    
    # Check status
    if sudo systemctl is-active --quiet openhab; then
        echo -e "${GREEN}✓ OpenHAB restarted successfully${NC}"
        echo ""
        echo "Viewing logs (press Ctrl+C to stop):"
        sleep 2
        tail -f /var/log/openhab/openhab.log 2>/dev/null | grep -E "net2|Net2" | head -20
    else
        echo -e "${RED}✗ OpenHAB failed to start${NC}"
        echo "Check logs with: sudo journalctl -u openhab -n 50"
        exit 1
    fi
else
    echo ""
    echo "To complete installation:"
    echo "1. sudo systemctl restart openhab"
    echo "2. Monitor: tail -f /var/log/openhab/openhab.log"
fi

echo -e "${GREEN}================================================${NC}"
echo "Deployment complete!"
echo -e "${GREEN}================================================${NC}"

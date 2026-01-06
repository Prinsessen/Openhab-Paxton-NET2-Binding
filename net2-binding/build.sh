#!/bin/bash

# Net2 Binding Build Script
# Safe script to build binding without affecting system files

set -e  # Exit on error

BINDING_DIR="/etc/openhab/net2-binding"
BUILD_LOG="${BINDING_DIR}/build.log"
JAR_OUTPUT=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "================================================"
echo "Net2 Binding Build Script"
echo "================================================"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v mvn &> /dev/null; then
    echo -e "${RED}Error: Maven is not installed${NC}"
    echo "Install with: sudo apt-get install maven"
    exit 1
fi

if ! command -v java &> /dev/null; then
    echo -e "${RED}Error: Java is not installed${NC}"
    echo "Install with: sudo apt-get install openjdk-21-jdk"
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | grep -oP '(?<=version ")[^"]+' | head -1)
echo -e "${GREEN}✓ Java ${JAVA_VERSION}${NC}"

MVN_VERSION=$(mvn --version 2>&1 | head -1)
echo -e "${GREEN}✓ ${MVN_VERSION}${NC}"

# Navigate to binding directory
if [ ! -d "${BINDING_DIR}" ]; then
    echo -e "${RED}Error: Binding directory not found: ${BINDING_DIR}${NC}"
    exit 1
fi

cd "${BINDING_DIR}"
echo -e "${GREEN}✓ Working directory: $(pwd)${NC}"

# Build options
BUILD_OPTIONS=""
SKIP_TESTS=false
CLEAN_BUILD=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --no-clean)
            CLEAN_BUILD=false
            shift
            ;;
        --quick)
            SKIP_TESTS=true
            BUILD_OPTIONS="-DskipChecks -Dspotless.check.skip=true"
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --skip-tests        Skip running unit tests"
            echo "  --no-clean          Don't clean before building"
            echo "  --quick             Fast build (skip tests and checks)"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Prepare build command
BUILD_CMD="mvn"
if [ "$CLEAN_BUILD" = true ]; then
    BUILD_CMD="$BUILD_CMD clean"
fi

BUILD_CMD="$BUILD_CMD install"

if [ "$SKIP_TESTS" = true ]; then
    BUILD_CMD="$BUILD_CMD -DskipTests"
fi

if [ -n "$BUILD_OPTIONS" ]; then
    BUILD_CMD="$BUILD_CMD $BUILD_OPTIONS"
fi

# Run build
echo ""
echo -e "${YELLOW}Building Net2 binding...${NC}"
echo "Command: $BUILD_CMD"
echo ""

if $BUILD_CMD 2>&1 | tee "$BUILD_LOG"; then
    echo ""
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}✓ Build successful!${NC}"
    echo -e "${GREEN}================================================${NC}"
    
    # Find JAR
    JAR_OUTPUT=$(find target -name "org.openhab.binding.net2-*.jar" 2>/dev/null | head -1)
    
    if [ -n "$JAR_OUTPUT" ]; then
        JAR_SIZE=$(du -h "$JAR_OUTPUT" | cut -f1)
        echo ""
        echo -e "${GREEN}Output JAR: ${JAR_OUTPUT}${NC}"
        echo -e "${GREEN}Size: ${JAR_SIZE}${NC}"
        echo ""
        echo "Next steps:"
        echo "1. Copy JAR to OpenHAB: cp $JAR_OUTPUT /opt/openhab/addons/"
        echo "2. Restart OpenHAB: sudo systemctl restart openhab"
        echo "3. Check logs: tail -f /var/log/openhab/openhab.log"
    fi
    
    exit 0
else
    echo ""
    echo -e "${RED}================================================${NC}"
    echo -e "${RED}✗ Build failed!${NC}"
    echo -e "${RED}================================================${NC}"
    echo ""
    echo "Build log saved to: $BUILD_LOG"
    echo "See errors above or check: cat $BUILD_LOG"
    exit 1
fi

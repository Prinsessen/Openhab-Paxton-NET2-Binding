#!/bin/bash
# Net2 Binding Development Workflow Reference
# Created: 2026-01-07
# Usage: source net2-binding-workflow.sh OR bash net2-binding-workflow.sh

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║         Net2 SignalR Binding - Development Workflow            ║"
echo "║                  Quick Reference Guide                         ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Define paths
BINDING_SOURCE="/etc/openhab/openhab-addons/bundles/org.openhab.binding.net2"
BINDING_DEPLOYED="/usr/share/openhab/addons/org.openhab.binding.net2-5.1.0.jar"
GITHUB_REPO="/tmp/Openhab-Paxton-NET2-Binding"
SCRIPTS_DIR="/etc/openhab/scripts"

echo -e "${BLUE}════ KEY LOCATIONS ════${NC}"
echo "Binding source:     $BINDING_SOURCE"
echo "Deployed JAR:       $BINDING_DEPLOYED"
echo "GitHub repository:  $GITHUB_REPO"
echo ""

# Function to check binding status
check_status() {
    echo -e "${BLUE}════ CHECKING BINDING STATUS ════${NC}"
    echo ""
    
    echo "OpenHAB Service Status:"
    sudo systemctl status openhab --no-pager | grep -E "Active|running|inactive"
    echo ""
    
    echo "Binding JAR deployed:"
    if [ -f "$BINDING_DEPLOYED" ]; then
        echo -e "${GREEN}✓ Found${NC}"
        ls -lh "$BINDING_DEPLOYED"
    else
        echo -e "${RED}✗ NOT found${NC}"
    fi
    echo ""
}

# Function to view logs
view_logs() {
    echo -e "${BLUE}════ VIEWING NET2 BINDING LOGS ════${NC}"
    echo "Press Ctrl+C to stop following logs"
    echo ""
    tail -f /var/log/openhab/openhab.log | grep -i "net2\|signalr"
}

# Function to quick build and deploy
build_and_deploy() {
    echo -e "${BLUE}════ BUILD & DEPLOY ════${NC}"
    echo ""
    
    echo "Step 1: Building binding..."
    cd "$BINDING_SOURCE"
    mvn clean install -DskipTests
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Build successful${NC}"
        echo ""
        
        echo "Step 2: Deploying to openHAB..."
        sudo cp "$BINDING_SOURCE/target/org.openhab.binding.net2-5.1.0.jar" "$BINDING_DEPLOYED"
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ JAR deployed${NC}"
            echo ""
            
            echo "Step 3: Restarting openHAB..."
            sudo systemctl restart openhab
            
            echo -e "${GREEN}✓ OpenHAB restarted${NC}"
            echo ""
            echo -e "${YELLOW}Waiting for service to start...${NC}"
            sleep 5
            
            echo "Current status:"
            sudo systemctl status openhab --no-pager | grep Active
        else
            echo -e "${RED}✗ Deployment failed${NC}"
        fi
    else
        echo -e "${RED}✗ Build failed${NC}"
    fi
    echo ""
}

# Function to sync to GitHub repo
sync_to_github() {
    echo -e "${BLUE}════ SYNC TO GITHUB REPOSITORY ════${NC}"
    echo ""
    
    echo "Step 1: Copying source to GitHub repo..."
    cp -r "$BINDING_SOURCE"/* "$GITHUB_REPO/"
    echo -e "${GREEN}✓ Source copied${NC}"
    echo ""
    
    echo "Step 2: Committing changes..."
    cd "$GITHUB_REPO"
    
    echo "Current status:"
    git status --short
    echo ""
    
    read -p "Enter commit message (or press Enter to cancel): " commit_msg
    
    if [ -n "$commit_msg" ]; then
        git add .
        git commit -m "$commit_msg"
        
        echo ""
        echo "Step 3: Pushing to GitHub..."
        git push origin main
        
        echo -e "${GREEN}✓ Changes pushed to GitHub${NC}"
    else
        echo -e "${YELLOW}Cancelled${NC}"
    fi
    echo ""
}

# Function to show menu
show_menu() {
    echo -e "${BLUE}════ COMMANDS ════${NC}"
    echo ""
    echo "Available functions (call from this script):"
    echo ""
    echo "  check_status        - Check if binding is running"
    echo "  view_logs           - Follow binding logs in real-time"
    echo "  build_and_deploy    - Build, deploy JAR, and restart openHAB"
    echo "  sync_to_github      - Sync source to GitHub and push"
    echo "  edit_binding        - Open binding source in editor"
    echo "  edit_config         - Open configuration files"
    echo "  show_menu           - Show this menu"
    echo ""
    echo "Example usage:"
    echo "  source net2-binding-workflow.sh"
    echo "  check_status"
    echo "  build_and_deploy"
    echo "  view_logs"
    echo ""
}

# Function to open binding in editor
edit_binding() {
    echo -e "${BLUE}════ OPENING BINDING SOURCE ════${NC}"
    code "$BINDING_SOURCE"
}

# Function to open configuration files
edit_config() {
    echo -e "${BLUE}════ OPENING CONFIGURATION FILES ════${NC}"
    
    # Create workspace file if doesn't exist
    WORKSPACE_FILE="$SCRIPTS_DIR/net2-workspace.code-workspace"
    
    if [ ! -f "$WORKSPACE_FILE" ]; then
        echo "Creating VS Code workspace file..."
        cat > "$WORKSPACE_FILE" << 'EOF'
{
  "folders": [
    {
      "path": "/etc/openhab",
      "name": "OpenHAB Config"
    },
    {
      "path": "/etc/openhab/openhab-addons",
      "name": "Addons (Build)"
    },
    {
      "path": "/tmp/Openhab-Paxton-NET2-Binding",
      "name": "GitHub Repo"
    }
  ],
  "settings": {
    "files.exclude": {
      "**/target": true,
      "**/.git": false
    }
  }
}
EOF
        echo -e "${GREEN}✓ Workspace created at: $WORKSPACE_FILE${NC}"
    fi
    
    echo "Opening VS Code with Net2 workspace..."
    code "$WORKSPACE_FILE"
}

# Quick info
quick_info() {
    echo -e "${BLUE}════ QUICK INFO ════${NC}"
    echo ""
    echo "Binding Status:"
    [ -f "$BINDING_DEPLOYED" ] && echo -e "${GREEN}✓ JAR deployed${NC}" || echo -e "${RED}✗ JAR missing${NC}"
    
    echo ""
    echo "Git Repositories:"
    echo "  openhab-addons (source):  $(cd $BINDING_SOURCE && git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"
    echo "  GitHub (remote):          $(cd $GITHUB_REPO && git rev-parse --short HEAD 2>/dev/null || echo 'N/A')"
    
    echo ""
    echo "Recent commits:"
    echo ""
    echo "Local:"
    cd "$BINDING_SOURCE" && git log --oneline -3 2>/dev/null || echo "  (no git history)"
    echo ""
    echo "GitHub:"
    cd "$GITHUB_REPO" && git log --oneline -3 2>/dev/null || echo "  (no git history)"
    echo ""
}

# Print menu on first run
show_menu
quick_info

echo -e "${YELLOW}NOTE: To use these functions, source this script:${NC}"
echo "  source $SCRIPTS_DIR/net2-binding-workflow.sh"
echo ""

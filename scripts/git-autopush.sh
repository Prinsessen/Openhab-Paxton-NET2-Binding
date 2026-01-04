#!/bin/bash

# OpenHAB Git Auto-Push Script
# This script automatically commits and pushes changes to the git repository

# Configuration
REPO_DIR="/etc/openhab"
LOG_FILE="/var/log/openhab/git-autopush.log"
MAX_LOG_SIZE=10485760  # 10MB

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to rotate log if it gets too large
rotate_log() {
    if [ -f "$LOG_FILE" ] && [ $(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null) -gt $MAX_LOG_SIZE ]; then
        mv "$LOG_FILE" "${LOG_FILE}.old"
        log_message "Log rotated"
    fi
}

# Change to repository directory
cd "$REPO_DIR" || {
    log_message "ERROR: Cannot change to directory $REPO_DIR"
    exit 1
}

# Check if git repository exists
if [ ! -d ".git" ]; then
    log_message "ERROR: Not a git repository. Run 'git init' first."
    exit 1
fi

# Check for changes (including untracked files)
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
    log_message "No changes to commit"
    exit 0
fi

# Rotate log if needed
rotate_log

# Add all changes
log_message "Adding changes to git..."
git add -A

# Check again if there are changes to commit
if git diff --cached --quiet; then
    log_message "No changes after git add"
    exit 0
fi

# Get list of changed files for commit message
CHANGED_FILES=$(git diff --cached --name-only | head -n 10)
NUM_CHANGES=$(git diff --cached --name-only | wc -l)

# Update CHANGELOG.md
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
DATE_ONLY=$(date '+%Y-%m-%d')
log_message "Updating CHANGELOG.md..."

# Get detailed list of changes
DETAILED_CHANGES=$(git diff --cached --name-status | while read status file; do
    case $status in
        A) echo "- Added: $file" ;;
        M) echo "- Modified: $file" ;;
        D) echo "- Deleted: $file" ;;
        R*) echo "- Renamed: $file" ;;
    esac
done)

# Update CHANGELOG with new entry
if [ -f "CHANGELOG.md" ]; then
    # Create temporary file with new entry
    {
        echo "# Changelog"
        echo ""
        echo "All notable changes to this OpenHAB configuration will be documented in this file."
        echo ""
        echo "The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),"
        echo "and this project adheres to semantic versioning for configuration changes."
        echo ""
        echo "## [Unreleased]"
        echo ""
        echo "### Auto-updated - $TIMESTAMP"
        echo "$DETAILED_CHANGES"
        echo ""
        # Append rest of changelog (skip header until first version)
        sed -n '/^## \[/,$p' CHANGELOG.md
    } > CHANGELOG.tmp
    mv CHANGELOG.tmp CHANGELOG.md
    git add CHANGELOG.md
fi

# Update README.md with last update timestamp
log_message "Updating README.md..."
if [ -f "README.md" ]; then
    # Check if Last Auto-Update section exists
    if grep -q "Last Auto-Update:" README.md; then
        # Update existing timestamp
        sed -i "s/Last Auto-Update:.*/Last Auto-Update: $TIMESTAMP/" README.md
    else
        # Add timestamp after the first header
        sed -i "0,/^#/a\\\\n**Last Auto-Update:** $TIMESTAMP" README.md
    fi
    git add README.md
fi

# Create commit message
if [ "$NUM_CHANGES" -eq 1 ]; then
    COMMIT_MSG="Auto-update: $(echo "$CHANGED_FILES" | head -n 1)"
elif [ "$NUM_CHANGES" -le 5 ]; then
    COMMIT_MSG="Auto-update: $NUM_CHANGES files"$'\n\n'"$CHANGED_FILES"
else
    COMMIT_MSG="Auto-update: $NUM_CHANGES files"$'\n\n'"$(echo "$CHANGED_FILES" | head -n 5)"$'\n'"... and $((NUM_CHANGES - 5)) more"
fi

# Commit changes
log_message "Committing changes..."
if git commit -m "$COMMIT_MSG"; then
    log_message "Changes committed successfully"
else
    log_message "ERROR: Failed to commit changes"
    exit 1
fi

# Push to remote
log_message "Pushing to remote repository..."
if git push; then
    log_message "Successfully pushed to remote repository"
else
    log_message "ERROR: Failed to push to remote. Check network and credentials."
    exit 1
fi

log_message "Auto-push completed successfully"
exit 0

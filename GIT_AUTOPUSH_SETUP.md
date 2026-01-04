# Git Auto-Push Service Installation Guide

## Overview
This service automatically commits and pushes changes in the OpenHAB configuration directory to a git repository every 15 minutes.

## Components
- **Script**: `scripts/git-autopush.sh` - Bash script that handles git operations
- **Service**: `services/openhab-git-autopush.service` - Systemd service definition
- **Timer**: `services/openhab-git-autopush.timer` - Systemd timer for scheduling

## Prerequisites

1. **Git repository must be initialized**:
   ```bash
   cd /etc/openhab
   git init
   git remote add origin <your-repo-url>
   ```

2. **Configure Git authentication** (choose one method):

   ### Option A: SSH Key (Recommended)
   ```bash
   # Generate SSH key for openhab user
   sudo -u openhab ssh-keygen -t ed25519 -C "openhab@$(hostname)"
   
   # Add the public key to your Git provider (GitHub/GitLab/etc.)
   sudo cat ~openhab/.ssh/id_ed25519.pub
   
   # Test SSH connection
   sudo -u openhab ssh -T git@github.com
   
   # Use SSH URL for remote
   git remote set-url origin git@github.com:username/repo.git
   ```

   ### Option B: Git Credential Store
   ```bash
   sudo -u openhab git config --global credential.helper store
   sudo -u openhab git push  # Enter credentials once
   ```

   ### Option C: Personal Access Token
   ```bash
   # Use token in URL (not recommended for security)
   git remote set-url origin https://token@github.com/username/repo.git
   ```

3. **Configure Git user** (if not already set):
   ```bash
   sudo -u openhab git config --global user.name "OpenHAB Server"
   sudo -u openhab git config --global user.email "openhab@yourdomain.com"
   ```

## Installation

1. **Make the script executable**:
   ```bash
   chmod +x /etc/openhab/scripts/git-autopush.sh
   ```

2. **Copy service files to systemd**:
   ```bash
   sudo cp /etc/openhab/services/openhab-git-autopush.service /etc/systemd/system/
   sudo cp /etc/openhab/services/openhab-git-autopush.timer /etc/systemd/system/
   ```

3. **Reload systemd**:
   ```bash
   sudo systemctl daemon-reload
   ```

4. **Enable and start the timer**:
   ```bash
   sudo systemctl enable openhab-git-autopush.timer
   sudo systemctl start openhab-git-autopush.timer
   ```

## Usage

### Check Timer Status
```bash
sudo systemctl status openhab-git-autopush.timer
```

### Check Service Status
```bash
sudo systemctl status openhab-git-autopush.service
```

### View Logs
```bash
# View systemd journal logs
sudo journalctl -u openhab-git-autopush.service -f

# View script logs
tail -f /var/log/openhab/git-autopush.log
```

### List Next Run Times
```bash
systemctl list-timers openhab-git-autopush.timer
```

### Manual Trigger
```bash
sudo systemctl start openhab-git-autopush.service
```

## Configuration

### Change Push Frequency
Edit `/etc/systemd/system/openhab-git-autopush.timer`:
```ini
# For every 5 minutes
OnCalendar=*:0/5

# For every hour
OnCalendar=hourly

# For daily at 2 AM
OnCalendar=daily
OnCalendar=02:00
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart openhab-git-autopush.timer
```

### Modify Script Behavior
Edit `/etc/openhab/scripts/git-autopush.sh` to customize:
- Commit message format
- File inclusion/exclusion
- Log location and rotation

## Troubleshooting

### Service Won't Start
```bash
# Check service logs
sudo journalctl -u openhab-git-autopush.service -n 50

# Test script manually
sudo -u openhab bash /etc/openhab/scripts/git-autopush.sh
```

### Authentication Failures
```bash
# Verify git remote
cd /etc/openhab
git remote -v

# Test push manually
sudo -u openhab git push
```

### Permission Issues
```bash
# Ensure openhab user owns the directory
sudo chown -R openhab:openhab /etc/openhab

# Check script permissions
ls -la /etc/openhab/scripts/git-autopush.sh
```

### Timer Not Running
```bash
# Check timer status
systemctl status openhab-git-autopush.timer

# Enable if disabled
sudo systemctl enable openhab-git-autopush.timer
sudo systemctl start openhab-git-autopush.timer
```

## Uninstallation

```bash
# Stop and disable timer
sudo systemctl stop openhab-git-autopush.timer
sudo systemctl disable openhab-git-autopush.timer

# Remove service files
sudo rm /etc/systemd/system/openhab-git-autopush.service
sudo rm /etc/systemd/system/openhab-git-autopush.timer

# Reload systemd
sudo systemctl daemon-reload
```

## Security Notes

- The service runs as the `openhab` user for security
- SSH key authentication is recommended over password-based auth
- The service has restricted file system access via systemd security settings
- Logs are rotated automatically to prevent disk space issues

## Customization Examples

### Exclude Certain Files
Add to `git-autopush.sh` before `git add -A`:
```bash
# Create/update .gitignore
echo "*.log" >> .gitignore
echo "*.tmp" >> .gitignore
```

### Add Pre-Push Validation
Add before push in `git-autopush.sh`:
```bash
# Validate configuration before pushing
if ! openhab-cli validate; then
    log_message "ERROR: Configuration validation failed"
    git reset --soft HEAD^
    exit 1
fi
```

### Notification on Push
Add after successful push in `git-autopush.sh`:
```bash
# Send notification via OpenHAB
curl -X POST http://localhost:8080/rest/items/GitPushNotification \
     -H "Content-Type: text/plain" \
     -d "ON"
```

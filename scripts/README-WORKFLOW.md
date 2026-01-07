# Net2 SignalR Binding - Development Workflow Guide

Quick reference guide for continuing development on the Net2 binding after closing VS Code.

---

## 📍 Key Locations

| Component | Location |
|-----------|----------|
| **Binding Source Code** | `/etc/openhab/openhab-addons/bundles/org.openhab.binding.net2/` |
| **Deployed JAR** | `/usr/share/openhab/addons/org.openhab.binding.net2-5.1.0.jar` |
| **GitHub Repository** | `/tmp/Openhab-Paxton-NET2-Binding/` |
| **Workflow Script** | `/etc/openhab/scripts/net2-binding-workflow.sh` |

---

## 🚀 Quick Start

### Load the Workflow Script
Every time you open a terminal, load the helper functions:

```bash
source /etc/openhab/scripts/net2-binding-workflow.sh
```

This makes all workflow commands available in your session.

---

## 📋 Available Commands

Once you've sourced the script, you can use these commands:

### `check_status`
Check if the binding is deployed and running.

```bash
check_status
```

**Shows:**
- OpenHAB service status
- JAR file location and details
- Whether binding is active

---

### `view_logs`
Follow binding logs in real-time.

```bash
view_logs
```

**Output:**
- All Net2/SignalR related log messages
- Press `Ctrl+C` to stop

---

### `build_and_deploy`
Build the binding, deploy JAR, and restart openHAB in one command.

```bash
build_and_deploy
```

**Steps:**
1. Builds binding with Maven (`mvn clean install -DskipTests`)
2. Copies JAR to `/usr/share/openhab/addons/`
3. Restarts openHAB service
4. Waits 5 seconds for startup
5. Shows current status

---

### `sync_to_github`
Copy source code to GitHub repo and push changes.

```bash
sync_to_github
```

**Steps:**
1. Copies source from `openhab-addons` to GitHub repo
2. Shows current `git status`
3. Prompts for commit message
4. Commits and pushes to `origin/main`

**Example:**
```
Enter commit message: Fix token refresh timeout issue
✓ Changes pushed to GitHub
```

---

### `edit_binding`
Open binding source code in VS Code.

```bash
edit_binding
```

Opens folder: `/etc/openhab/openhab-addons/bundles/org.openhab.binding.net2/`

---

### `edit_config`
Open all configuration folders in VS Code workspace.

```bash
edit_config
```

**Opens 3 folders:**
- `/etc/openhab` - Main openHAB config
- `/etc/openhab/openhab-addons/` - Binding source (for building)
- `/tmp/Openhab-Paxton-NET2-Binding/` - GitHub repository

Also creates a workspace file: `net2-workspace.code-workspace`

---

### `show_menu`
Display all available commands.

```bash
show_menu
```

---

## 🔄 Typical Development Workflow

### Session 1: Initial Setup
```bash
# Open terminal
source /etc/openhab/scripts/net2-binding-workflow.sh

# Check current status
check_status

# Open all code folders
edit_config
```

### Session 2: Make Changes & Test
```bash
# Load script
source /etc/openhab/scripts/net2-binding-workflow.sh

# Edit binding (opens VS Code)
edit_binding
# ...make changes...

# Build and deploy
build_and_deploy

# Watch logs while testing
view_logs
# ...test door events, etc...
# Press Ctrl+C to stop

# Push to GitHub
sync_to_github
```

### Session 3: Fix Issues
```bash
source /etc/openhab/scripts/net2-binding-workflow.sh

# Check what's wrong
view_logs

# Edit relevant files
edit_config

# Rebuild and test
build_and_deploy

# Sync back to GitHub
sync_to_github
```

---

## 📁 Directory Structure

```
/etc/openhab/
├── openhab-addons/              # Official openHAB repo (build here)
│   └── bundles/
│       └── org.openhab.binding.net2/
│           ├── src/
│           │   ├── main/java/    # Java handler classes
│           │   └── main/resources/ # XML configs
│           ├── pom.xml           # Maven config
│           └── target/           # Build output
│
└── scripts/
    ├── net2-binding-workflow.sh  # This workflow helper
    ├── README-WORKFLOW.md        # This file
    └── net2_config.json          # Local configuration (NOT in GitHub)

/tmp/Openhab-Paxton-NET2-Binding/  # GitHub repository
├── README.md                      # Feature overview
├── INSTALLATION.md                # Setup guide
├── CONFIGURATION.md               # Item examples & rules
├── TROUBLESHOOTING.md             # Common issues
├── src/                           # Source code
├── pom.xml                        # Maven config
└── .gitignore                     # Git ignore rules
```

---

## 🔨 Manual Commands (if not using script)

If you prefer to run commands directly:

### Build
```bash
cd /etc/openhab/openhab-addons/bundles/org.openhab.binding.net2
mvn clean install -DskipTests
```

### Deploy
```bash
sudo cp /etc/openhab/openhab-addons/bundles/org.openhab.binding.net2/target/org.openhab.binding.net2-5.1.0.jar \
  /usr/share/openhab/addons/
```

### Restart
```bash
sudo systemctl restart openhab
```

### View Logs
```bash
tail -f /var/log/openhab/openhab.log | grep -i net2
```

### Sync to GitHub
```bash
# Copy source
cp -r /etc/openhab/openhab-addons/bundles/org.openhab.binding.net2/* /tmp/Openhab-Paxton-NET2-Binding/

# Commit and push
cd /tmp/Openhab-Paxton-NET2-Binding
git add .
git commit -m "Your change description"
git push origin main
```

---

## 💡 Tips & Tricks

### View All Git Changes
```bash
cd /etc/openhab/openhab-addons/bundles/org.openhab.binding.net2
git diff
```

### See Recent Commits
```bash
cd /tmp/Openhab-Paxton-NET2-Binding
git log --oneline -10
```

### Check Binding Status in Real-Time
```bash
# One terminal
source /etc/openhab/scripts/net2-binding-workflow.sh
view_logs

# Another terminal
# Make changes and rebuild
build_and_deploy
```

### Quick Build Without Deploy
```bash
cd /etc/openhab/openhab-addons/bundles/org.openhab.binding.net2
mvn clean install -DskipTests
# JAR at: target/org.openhab.binding.net2-5.1.0.jar
```

---

## 📝 File Editing Quick Links

| File | Purpose | Path |
|------|---------|------|
| Server Handler | Bridge & authentication | `src/main/java/.../Net2ServerHandler.java` |
| Door Handler | Door events & status | `src/main/java/.../Net2DoorHandler.java` |
| SignalR Client | WebSocket protocol | `src/main/java/.../Net2SignalRClient.java` |
| Thing Types | Channel definitions | `src/main/resources/OH-INF/thing/thing-types.xml` |
| Binding Metadata | Binding info | `src/main/resources/OH-INF/binding/binding.xml` |

---

## ✅ Health Check Commands

```bash
# Is service running?
sudo systemctl status openhab

# Is JAR deployed?
ls -lh /usr/share/openhab/addons/org.openhab.binding.net2-*.jar

# Any errors in logs?
grep -i error /var/log/openhab/openhab.log | tail -10

# Are Things online?
# Check UI: Things tab or run workflow script:
source /etc/openhab/scripts/net2-binding-workflow.sh
check_status
```

---

## 🔗 Related Documentation

- **README.md** - Features and quick start
- **INSTALLATION.md** - Setup and deployment guide
- **CONFIGURATION.md** - Items, rules, and automation examples
- **TROUBLESHOOTING.md** - Common issues and solutions

---

## ⚡ Keyboard Shortcuts

In VS Code with workspace open:
- `Ctrl+P` - Quick file search
- `Ctrl+F` - Find in file
- `Ctrl+Shift+F` - Find across all files
- `Ctrl+J` - Toggle terminal
- `Ctrl+`` - Open integrated terminal

---

## 📞 When You Need Help

1. Check logs: `view_logs` or `tail -f /var/log/openhab/openhab.log`
2. Review TROUBLESHOOTING.md in GitHub repo
3. Check recent commits: `git log --oneline -5`
4. Rebuild clean: `build_and_deploy`

---

**Last Updated:** 2026-01-07  
**Binding Version:** 5.1.0  
**openHAB Version:** 5.1.0

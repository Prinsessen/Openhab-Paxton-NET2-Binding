# Quick Start Guide for Net2 Binding

## What's Been Created

A complete **OpenHAB 5 binding** for **Paxton Net2 door control** has been created in:
```
/etc/openhab/net2-binding/
```

This is **isolated source code** - it won't affect your system until you explicitly build and deploy it.

## Directory Overview

```
/etc/openhab/net2-binding/
├── pom.xml                    # Maven build configuration
├── build.sh                   # Easy build script
├── deploy.sh                  # Safe deployment script
├── README.md                  # Full binding documentation
├── DEVELOPMENT.md             # Developer guide
├── EXAMPLES.md                # Usage examples & rules
├── src/
│   ├── main/                  # Binding source code
│   │   ├── java/...           # Java handler classes
│   │   └── resources/         # XML configurations
│   └── test/                  # Unit tests
└── target/                    # Build output (created after build)
```

## Hardware Requirements

### ✅ Compatible Controllers
- **Paxton Net2 Plus ACU** ([Manual](https://www.paxton-access.com/wp-content/uploads/2019/03/ins-20006.pdf))
- **Paxton Net2 Classic ACU** (Discontinued)

### ❌ Not Compatible
- **Net2 Nano** ([Info](https://www.paxton-access.com/wp-content/uploads/2019/03/ins-30075.pdf))
- **Paxlock** ([Info](https://www.paxton-access.com/wp-content/uploads/2019/03/ins-20000.pdf))
- **Paxlock Pro** ([Info](https://www.paxton-access.com/wp-content/uploads/2022/05/ins-30229.pdf))

**Note:** Requires Net2 Local API (Plus/Classic only).

## Quick Start

### Step 1: Build the Binding

```bash
cd /etc/openhab/net2-binding
./build.sh
```

**Options:**
```bash
./build.sh --quick          # Fast build (skip tests)
./build.sh --skip-tests     # Build without running tests
./build.sh --no-clean       # Don't clean before build
```

**Output:** `target/org.openhab.binding.net2-5.1.0.jar`

### Step 2: Deploy to OpenHAB

```bash
./deploy.sh
```

This script will:
- Backup existing binding (if any)
- Copy new JAR to `/opt/openhab/addons/`
- Optionally restart OpenHAB
- Show logs for verification

### Step 3: Configure in OpenHAB

Create things and items:

**things/net2.things:**
```
Bridge net2:net2server:myserver [
    hostname="net2.example.com",
    port=8443,
    username="Your Name",
    password="your_secure_password",
    clientId="your_oauth_client_id"
] {
    Thing door fordoor [doorId=6203980, name="Front Door"]
}
```

**items/net2.items:**
```
Switch Front_Door { channel="net2:door:myserver:fordoor:action" }
Switch Front_Door_Status { channel="net2:door:myserver:fordoor:status" }
String Front_Door_LastUser { channel="net2:door:myserver:fordoor:lastAccessUser" }
DateTime Front_Door_LastTime { channel="net2:door:myserver:fordoor:lastAccessTime" }
String Front_Door_EntryLog { channel="net2:door:myserver:fordoor:entryLog" }

// Bridge channels (user management)
String Net2_CreateUser        "Create User"        { channel="net2:net2server:myserver:createUser" }
String Net2_DeleteUser        "Delete User"        { channel="net2:net2server:myserver:deleteUser" }
String Net2_ListAccessLevels  "List Access Levels" { channel="net2:net2server:myserver:listAccessLevels" }
```

### Step 4: Use in Rules

```java
rule "Unlock door"
when Item Command_Unlock received command ON
then
    Front_Door.sendCommand(ON)
end
```

## Features Implemented

✅ **API Communication**
- OAuth2 JWT authentication
- Automatic token refresh (30-min tokens)
- Secure HTTPS connection with cert verification control

✅ **Door Control**
- Hold door open: `POST /commands/door/holdopen`
- Close door: `POST /commands/door/close`
- Get status: `GET /doors/status`

✅ **Real-time Updates**
- Automatic polling (configurable, default 30 sec)
- SignalR event infrastructure (WebSocket ready)
- Entry logging channel for physical badge access events
- Status change notifications

✅ **Discovery Service**
- Auto-detect available doors
- Scan for new doors
- Automatic thing creation

✅ **Channels per Door**
| Channel | Type | Access |
|---------|------|--------|
| `status` | Switch | Read-only |
| `action` | Switch | Read/Write |
| `lastAccessUser` | String | Read-only |
| `lastAccessTime` | DateTime | Read-only |

✅ **User Management (Bridge Channels)**
| Channel | Type | Purpose |
|---------|------|---------|
| `createUser` | String | Create user with access level and PIN: `firstName,lastName,accessLevel,pin` |
| `deleteUser` | String | Delete user by ID |
| `listAccessLevels` | String | Log available access levels |

### Quick Test via REST

```bash
# Create user and assign access level 3
curl -X POST "http://localhost:8080/rest/items/Net2_CreateUser" \
    -H "Content-Type: text/plain" \
    --data "Michael,Agesen,3,7654"

# List access levels
curl -X POST "http://localhost:8080/rest/items/Net2_ListAccessLevels" \
    -H "Content-Type: text/plain" \
    --data "REFRESH"

# Delete user (replace 79 with created ID from logs)
curl -X POST "http://localhost:8080/rest/items/Net2_DeleteUser" \
    -H "Content-Type: text/plain" \
    --data "79"
```

## File Organization

**Safe & Isolated:**
- ✅ All in `/etc/openhab/net2-binding/` - won't affect system
- ✅ No modification of existing OpenHAB files
- ✅ No system-wide installation until you run `./deploy.sh`
- ✅ Easy rollback with backup system
- ✅ Can be safely deleted if not needed

## Documentation Files

- **README.md** - Complete binding documentation
- **DEVELOPMENT.md** - For developers/contributing
- **EXAMPLES.md** - Example rules, sitemaps, items
- **QUICKSTART.md** - This file

## Building from Scratch

If you want to understand the structure:

```bash
# View main binding code
cat src/main/java/org/openhab/binding/net2/handler/Net2ServerHandler.java

# View API client
cat src/main/java/org/openhab/binding/net2/handler/Net2ApiClient.java

# View thing definitions
cat src/main/resources/OH-INF/thing/thing-types.xml
```

## Testing

```bash
# Run unit tests
cd /etc/openhab/net2-binding
mvn test

# View test coverage
mvn jacoco:report
# Open: target/site/jacoco/index.html
```

## Troubleshooting

### Build fails with "Maven not found"
```bash
sudo apt-get install maven
```

### Build fails with "Java version"
```bash
sudo apt-get install openjdk-21-jdk
```

### After deployment, binding doesn't appear
```bash
# Check logs
tail -f /var/log/openhab/openhab.log | grep net2

# Check jar is there
ls -la /opt/openhab/addons/org.openhab.binding.net2-*.jar
```

### Door commands not working
1. Verify Net2 server configuration (hostname, port, credentials)
2. Check bridge is ONLINE in OpenHAB
3. Verify door IDs match Net2 system
4. Check logs for authentication errors

## Next Steps

1. **Read** `README.md` for full documentation
2. **View** `EXAMPLES.md` for automation examples
3. **Build** with `./build.sh`
4. **Deploy** with `./deploy.sh`
5. **Configure** things and items
6. **Automate** with rules and scripts

## Safety Notes

✅ **This binding is safe because:**
- It's source code only until you explicitly build it
- Build output goes to `target/` directory (isolated)
- Deployment requires explicit `./deploy.sh` execution
- Deploy script backs up existing files
- Easy to rollback - just remove JAR and restart OpenHAB

## Support

For issues:
1. Check logs: `/var/log/openhab/openhab.log`
2. Read DEVELOPMENT.md for debugging
3. OpenHAB community: https://community.openhab.org/

## Architecture

```
Your System
└── /etc/openhab/net2-binding/          ← Source code (safe)
    ├── build.sh              ← Compile to JAR
    └── deploy.sh             ← Deploy to OpenHAB
        └── /opt/openhab/addons/        ← JAR installed here
            └── Binding runs within OpenHAB
                └── Controls doors via Net2 API
                    └── https://net2.server:8443/api/v1/...
```

Enjoy! 🚪

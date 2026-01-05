# Paxton Net2 Temporary User Management

## Overview

The `net2_temp_user.py` script provides a safe and easy way to create, manage, and automatically expire temporary users in the Paxton Net2 access control system. All temporary users are prefixed with `TEMP_` for easy identification.

## Features

- ✅ Create time-limited users (hours or days)
- ✅ Assign specific access levels (door permissions)
- ✅ Set PIN codes for door access
- ✅ List all temporary users
- ✅ Delete individual users
- ✅ Automatic cleanup of expired users
- ✅ Safe deletion (confirmation required for non-temporary users)
- ✅ Database-safe operations (uses official API)

## Installation

The script is already installed at `/etc/openhab/scripts/net2_temp_user.py` and is executable.

```bash
cd /etc/openhab/scripts
python3 net2_temp_user.py --help
```

## Available Access Levels

| ID | Name | Description |
|----|------|-------------|
| 0 | Ingen adgang | No access (useful for testing) |
| 1 | Altid - alle døre | Always - all doors (full access) |
| 2 | Arbejdstid | Work hours only |
| 3 | Kirkegade 50 | Access to Kirkegade 50 location |
| 4 | Bohrsvej | Access to Bohrsvej location |
| 5 | Porsevej 19 | Access to Porsevej 19 location |
| 6 | Terndrupvej 81 | Access to Terndrupvej 81 location |

## Usage Examples

### 1. Create a Temporary User

Create a user with 24-hour access to Kirkegade 50:

```bash
python3 net2_temp_user.py add "John" "Doe" --hours 24 --access-level 3 --pin 1234
```

Create a user valid for 7 days with full access:

```bash
python3 net2_temp_user.py add "Jane" "Smith" --days 7 --access-level 1 --pin 5678
```

Create a user with middle name and specific duration:

```bash
python3 net2_temp_user.py add "Bob" "Johnson" --middle-name "Lee" --hours 48 --access-level 6 --pin 9999
```

### 2. List Temporary Users

List all users with the TEMP_ prefix:

```bash
python3 net2_temp_user.py list
```

List ALL users in the system:

```bash
python3 net2_temp_user.py list --all
```

### 3. Show Available Access Levels

```bash
python3 net2_temp_user.py levels
```

### 4. Delete a Specific User

```bash
python3 net2_temp_user.py delete 62
```

**Note:** The script will ask for confirmation if you try to delete a non-temporary user (one without the TEMP_ prefix).

### 5. Cleanup Expired Users

Dry run (see what would be deleted):

```bash
python3 net2_temp_user.py cleanup
```

Actually delete expired users:

```bash
python3 net2_temp_user.py cleanup --confirm
```

## Command Reference

### Add User

```bash
python3 net2_temp_user.py add FIRST_NAME LAST_NAME [OPTIONS]
```

**Options:**
- `--middle-name TEXT` - Middle name (optional)
- `--hours N` - Valid for N hours (default: 24)
- `--days N` - Valid for N days (added to hours)
- `--access-level ID` - Access level ID 0-6 (default: 0 = no access)
- `--pin CODE` - PIN code for door access (optional)
- `--department ID` - Department ID (optional)

**Examples:**
```bash
# 3-hour access
python3 net2_temp_user.py add "Alice" "Brown" --hours 3 --access-level 3 --pin 1111

# 7-day access
python3 net2_temp_user.py add "Carol" "White" --days 7 --access-level 1 --pin 2222

# Combined (2 days + 12 hours = 60 hours total)
python3 net2_temp_user.py add "David" "Green" --days 2 --hours 12 --access-level 3 --pin 3333
```

### List Users

```bash
python3 net2_temp_user.py list [--all]
```

### Delete User

```bash
python3 net2_temp_user.py delete USER_ID
```

### Cleanup Expired Users

```bash
python3 net2_temp_user.py cleanup [--confirm]
```

### Show Access Levels

```bash
python3 net2_temp_user.py levels
```

## Automation Examples

### Cron Job for Automatic Cleanup

Add to crontab to run cleanup every day at 3 AM:

```bash
0 3 * * * cd /etc/openhab/scripts && /usr/bin/python3 net2_temp_user.py cleanup --confirm
```

### OpenHAB Rule Integration

Create a rule that adds a temporary user when triggered:

```java
rule "Add Temporary Contractor"
when
    Item AddContractorAccess received command ON
then
    val result = executeCommandLine(Duration.ofSeconds(30),
        "python3", "/etc/openhab/scripts/net2_temp_user.py",
        "add", "Contractor", "Access",
        "--hours", "8",
        "--access-level", "2",
        "--pin", "1234")
    logInfo("Net2", "Contractor added: " + result)
end
```

## Important Notes

### Database Safety

This script uses the official Paxton Net2 API, which means:
- ✅ All operations are database-safe
- ✅ No direct database manipulation
- ✅ Full transaction support
- ✅ Proper error handling

### Expiry Date Limitation

The Paxton Net2 API automatically truncates expiry dates to midnight (00:00). This is an API limitation, not a script issue. For example:
- Request: `2026-01-05 14:30:00`
- Actual stored: `2026-01-05 00:00:00`

This means users expire at the START of the specified day, not at the exact time requested.

### Temporary User Prefix

All users created by this script are prefixed with `TEMP_` in their first name. This allows:
- Easy identification of temporary users
- Safe cleanup operations
- Separation from permanent users

### Access Level Assignment

Note that when listing users, the access level may show as "Not set" even if one was assigned. This is because the main user list API doesn't return the `doorAccessPermissionSet`. The access level IS correctly set in the database and will work for door access.

## Troubleshooting

### Authentication Failed

If you see "❌ Failed to authenticate":
1. Check that the credentials in the script are correct
2. Verify the Net2 API server is accessible at `milestone.agesen.dk:8443`
3. Ensure network connectivity

### SSL Certificate Warnings

The script disables SSL warnings because the Net2 API uses a self-signed certificate. This is normal and safe for internal use.

### User Creation Fails

If user creation fails:
1. Verify the access level ID is valid (0-6)
2. Check that the PIN is unique (if specified)
3. Ensure you have admin permissions in Net2

### "None" in User Names

If you see "None" in user names (e.g., "TEMP_John None Doe"), this happens when the API returns `null` for the middle name. The latest version of the script handles this correctly.

## Security Considerations

1. **Credentials**: The API credentials are hardcoded in the script. Ensure the script file has proper permissions (readable only by openhab user).

2. **PIN Codes**: Choose secure PINs and don't reuse them across multiple users.

3. **Access Levels**: Always use the minimum required access level. Default is 0 (no access) for safety.

4. **Regular Cleanup**: Run cleanup regularly to remove expired users from the database.

## API Endpoints Used

The script uses these Paxton Net2 API endpoints:
- `POST /api/v1/authorization/tokens` - Authentication
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `DELETE /api/v1/users/{id}` - Delete user
- `GET /api/v1/accesslevels` - List access levels

## Version History

- **2026-01-05**: Initial version
  - User creation with time limits
  - Access level assignment
  - PIN code support
  - List, delete, and cleanup operations
  - Comprehensive error handling

## Support

For issues or questions, check:
1. The script's built-in help: `python3 net2_temp_user.py --help`
2. Individual command help: `python3 net2_temp_user.py add --help`
3. The Paxton Net2 API documentation
4. OpenHAB logs: `/var/log/openhab/openhab.log`

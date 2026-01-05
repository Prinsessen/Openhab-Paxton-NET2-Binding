# Paxton Net2 Temporary User Management - Summary

## What Was Created

### Main Script: `net2_temp_user.py`
A comprehensive Python script for managing temporary users in the Paxton Net2 access control system.

**Location:** `/etc/openhab/scripts/net2_temp_user.py`

**Key Features:**
- ✅ Create time-limited users (hours/days)
- ✅ Assign access levels (door permissions)
- ✅ Set PIN codes
- ✅ List all temporary users
- ✅ Delete individual users
- ✅ Auto-cleanup expired users
- ✅ Database-safe operations via official API

### Documentation: `README_net2_temp_user.md`
Comprehensive documentation with usage examples, troubleshooting, and automation guides.

**Location:** `/etc/openhab/scripts/README_net2_temp_user.md`

### Examples: `net2_temp_user_examples.sh`
Quick reference guide with common use cases and integration examples.

**Location:** `/etc/openhab/scripts/net2_temp_user_examples.sh`

## Quick Start

### Basic Usage

```bash
# Create a temporary user with 24-hour access
python3 /etc/openhab/scripts/net2_temp_user.py add "FirstName" "LastName" \
    --hours 24 --access-level 3 --pin 1234

# List all temporary users
python3 /etc/openhab/scripts/net2_temp_user.py list

# Show available access levels
python3 /etc/openhab/scripts/net2_temp_user.py levels

# Delete a user
python3 /etc/openhab/scripts/net2_temp_user.py delete USER_ID

# Cleanup expired users
python3 /etc/openhab/scripts/net2_temp_user.py cleanup --confirm
```

## Testing Results

All functionality has been tested and verified:
- ✅ Authentication with Paxton Net2 API
- ✅ User creation with various parameters
- ✅ Time-limited access (hours and days)
- ✅ Access level assignment
- ✅ PIN code assignment
- ✅ User listing
- ✅ User deletion
- ✅ Expired user cleanup
- ✅ Error handling

## API Integration

The script uses the official Paxton Net2 REST API:
- Base URL: `https://milestone.agesen.dk:8443/api/v1`
- Authentication: OAuth2 password grant
- SSL: Self-signed certificate (warnings disabled)

## Safety Features

1. **Database Safety**: Uses official API only, no direct database manipulation
2. **User Prefix**: All temporary users are prefixed with `TEMP_`
3. **Deletion Safety**: Requires confirmation for non-temporary users
4. **Access Control**: Default access level is 0 (no access)
5. **Error Handling**: Comprehensive error checking and validation

## Known Limitations

### Expiry Date Truncation
The Paxton Net2 API truncates expiry dates to midnight (00:00). This is an API limitation:
- You request: `2026-01-05 14:30:00`
- API stores: `2026-01-05 00:00:00`

Users expire at the START of the specified day, not at the exact time requested.

### Access Level Display
When listing users, the access level shows as "Not set" because the list API doesn't return `doorAccessPermissionSet`. The access level IS correctly set in the database and works for door access.

## Automation Options

### Cron Job for Cleanup
Add to crontab to automatically remove expired users daily:
```bash
0 3 * * * cd /etc/openhab/scripts && /usr/bin/python3 net2_temp_user.py cleanup --confirm >> /var/log/openhab/net2-cleanup.log 2>&1
```

### OpenHAB Rule Integration
Example rule to add temporary user:
```java
rule "Add Temporary Access"
when
    Item TempAccess received command ON
then
    val result = executeCommandLine(Duration.ofSeconds(30),
        "python3", "/etc/openhab/scripts/net2_temp_user.py",
        "add", "Visitor", "Guest",
        "--hours", "8",
        "--access-level", "3",
        "--pin", "1234")
    logInfo("Net2", "Temporary access added: " + result)
end
```

## Access Levels Reference

| ID | Name | Use Case |
|----|------|----------|
| 0 | Ingen adgang | Testing (no actual access) |
| 1 | Altid - alle døre | Full access, all times |
| 2 | Arbejdstid | Work hours only |
| 3 | Kirkegade 50 | Kirkegade 50 building |
| 4 | Bohrsvej | Bohrsvej building |
| 5 | Porsevej 19 | Porsevej 19 building |
| 6 | Terndrupvej 81 | Terndrupvej 81 building |

## Common Use Cases

### 1. Delivery Person (8 hours, work hours)
```bash
python3 net2_temp_user.py add "Delivery" "Service" --hours 8 --access-level 2 --pin 1000
```

### 2. Contractor (1 week, specific building)
```bash
python3 net2_temp_user.py add "Contractor" "Name" --days 7 --access-level 3 --pin 2000
```

### 3. Visitor (24 hours)
```bash
python3 net2_temp_user.py add "Visitor" "Name" --hours 24 --access-level 3 --pin 3000
```

### 4. Maintenance Crew (48 hours, full access)
```bash
python3 net2_temp_user.py add "Maintenance" "Crew" --hours 48 --access-level 1 --pin 5000
```

## Support & Documentation

- **Main Documentation**: [README_net2_temp_user.md](README_net2_temp_user.md)
- **Examples**: [net2_temp_user_examples.sh](net2_temp_user_examples.sh)
- **Script Help**: `python3 net2_temp_user.py --help`
- **Command Help**: `python3 net2_temp_user.py COMMAND --help`

## API Documentation Reference

The script was developed using the Paxton Net2 API with these endpoints:
- `POST /api/v1/authorization/tokens` - Get access token
- `GET /api/v1/users` - List users
- `GET /api/v1/users/{id}` - Get user details
- `POST /api/v1/users` - Create user
- `DELETE /api/v1/users/{id}` - Delete user
- `GET /api/v1/accesslevels` - List access levels
- `GET /api/v1/departments` - List departments

## Version Information

- **Created**: 2026-01-05
- **Python Version**: 3.x (tested with 3.13.5)
- **Dependencies**: requests, urllib3 (standard Python libraries)
- **API Version**: Paxton Net2 REST API v1

## Next Steps

1. **Test in your environment**: Create a test user with no access (level 0) to verify
2. **Set up automation**: Add cron job for automatic cleanup
3. **Integrate with OpenHAB**: Create rules for your specific use cases
4. **Monitor usage**: Check logs regularly to ensure proper operation

## Credits

Developed for the OpenHAB Smart Home system at Kirkegade 50, integrating with the existing Paxton Net2 access control infrastructure.

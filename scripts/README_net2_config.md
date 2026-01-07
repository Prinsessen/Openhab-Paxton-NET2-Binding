# Paxton Net2 Configuration File

## Overview

All Paxton Net2 scripts now use a centralized configuration file instead of hardcoded credentials. This improves security and makes it easier to update credentials.

## Configuration File Location

`/etc/openhab/scripts/net2_config.json`

## File Format

The configuration file is in JSON format with the following structure:

```json
{
  "base_url": "https://your-net2-server.com:8443/api/v1",
  "username": "your_username",
  "password": "your_secure_password",
  "grant_type": "password",
  "client_id": "your_oauth_client_id"
}
```

## Required Fields

All fields are required:

| Field | Description | Example |
|-------|-------------|---------|
| `base_url` | Paxton Net2 API base URL | `https://your-net2-server.com:8443/api/v1` |
| `username` | API username | `your_username` |
| `password` | API password | `your_secure_password` |
| `grant_type` | OAuth2 grant type | `password` |
| `client_id` | OAuth2 client ID | `your_oauth_client_id` |

## Security

### File Permissions

The configuration file should be readable only by the `openhab` user:

```bash
sudo chmod 640 /etc/openhab/scripts/net2_config.json
sudo chown openhab:openhab /etc/openhab/scripts/net2_config.json
```

Current permissions:
```
-rw-r----- 1 openhab openhab 202 Jan 5 11:57 /etc/openhab/scripts/net2_config.json
```

### Best Practices

1. **Never commit** this file to version control
2. **Restrict access** to the openhab user only
3. **Use strong passwords** for API access
4. **Rotate credentials** periodically
5. **Monitor access** via API logs

## Scripts Using This Configuration

The following scripts automatically load configuration from `net2_config.json`:

1. **net2_temp_user.py** - Temporary user management
2. **net2_user_activity.py** - Standalone activity report generator
3. **net2_user_activity_daemon.py** - Continuous polling daemon

## Updating Configuration

To update the configuration:

1. Edit the config file:
   ```bash
   sudo nano /etc/openhab/scripts/net2_config.json
   ```

2. Update the desired fields (maintain JSON format)

3. Save and exit

4. Restart affected services:
   ```bash
   sudo systemctl restart net2-daemon.service
   ```

5. Test with a simple command:
   ```bash
   python3 /etc/openhab/scripts/net2_temp_user.py levels
   ```

## Troubleshooting

### Configuration File Not Found

If you see:
```
❌ Configuration file not found: /etc/openhab/scripts/net2_config.json
```

Create the file using the template above.

### Permission Denied

If you see:
```
❌ Error loading config file: [Errno 13] Permission denied
```

Fix permissions:
```bash
sudo chmod 640 /etc/openhab/scripts/net2_config.json
sudo chown openhab:openhab /etc/openhab/scripts/net2_config.json
```

### Invalid JSON

If you see:
```
❌ Invalid JSON in config file: ...
```

Validate your JSON syntax:
- Check for missing commas
- Ensure all strings are in double quotes
- Verify bracket/brace matching
- Use a JSON validator (https://jsonlint.com)

### Missing Required Fields

If you see:
```
❌ Missing required fields in config: username, password
```

Ensure all five fields are present in the config file.

## Backup

It's recommended to keep a backup of this configuration file:

```bash
sudo cp /etc/openhab/scripts/net2_config.json /etc/openhab/scripts/net2_config.json.backup
```

## Migration from Hardcoded Credentials

If you're using older versions with hardcoded credentials:

1. Scripts will now fail if `net2_config.json` doesn't exist
2. Create the config file with your existing credentials
3. Scripts will automatically use the new config file
4. No other changes needed

## Example: Multiple Environments

If you need different configurations for testing:

```bash
# Production config
/etc/openhab/scripts/net2_config.json

# Test config
/etc/openhab/scripts/net2_config_test.json
```

To use a different config, temporarily rename it:
```bash
sudo mv /etc/openhab/scripts/net2_config.json /etc/openhab/scripts/net2_config_prod.json
sudo mv /etc/openhab/scripts/net2_config_test.json /etc/openhab/scripts/net2_config.json
sudo systemctl restart net2-daemon.service
```

## Version History

- **2026-01-05**: Initial version - Moved from hardcoded to config file
  - Improved security
  - Centralized configuration
  - Easier credential management

## Related Documentation

- [NET2_TEMP_USER_SUMMARY.md](NET2_TEMP_USER_SUMMARY.md) - Temporary user management
- [README_net2_temp_user.md](README_net2_temp_user.md) - Detailed temp user docs
- [net2_temp_user_examples.sh](net2_temp_user_examples.sh) - Usage examples

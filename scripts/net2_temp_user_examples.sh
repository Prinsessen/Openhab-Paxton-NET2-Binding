#!/bin/bash
# Quick Reference: Paxton Net2 Temporary User Management
# Location: /etc/openhab/scripts/net2_temp_user.py

# ============================================================================
# COMMON USE CASES
# ============================================================================
# Note: Access levels can be specified by ID (0-6) OR by name

# 1. DELIVERY PERSON (8 hours, work hours only)
python3 /etc/openhab/scripts/net2_temp_user.py add "Delivery" "Service" \
    --hours 8 --access-level "Arbejdstid" --pin 1000
# Or use ID: --access-level 2

# 2. CONTRACTOR (1 week, specific building)
python3 /etc/openhab/scripts/net2_temp_user.py add "Contractor" "Name" \
    --days 7 --access-level "Kirkegade 50" --pin 2000
# Or use ID: --access-level 3

# 3. VISITOR (24 hours, limited access)
python3 /etc/openhab/scripts/net2_temp_user.py add "Visitor" "Name" \
    --hours 24 --access-level "kirkegade" --pin 3000
# Partial names work too (case insensitive)

# 4. TEMPORARY EMPLOYEE (1 month, full access)
python3 /etc/openhab/scripts/net2_temp_user.py add "Temp" "Employee" \
    --days 30 --access-level "alle døre" --pin 4000
# Or use ID: --access-level 1

# 5. MAINTENANCE (48 hours, all doors)
python3 /etc/openhab/scripts/net2_temp_user.py add "Maintenance" "Crew" \
    --hours 48 --access-level 1 --pin 5000
# Numbers still work perfectly

# ============================================================================
# MANAGEMENT COMMANDS
# ============================================================================

# List all temporary users
python3 /etc/openhab/scripts/net2_temp_user.py list

# Show access levels
python3 /etc/openhab/scripts/net2_temp_user.py levels

# Check for expired users (dry run)
python3 /etc/openhab/scripts/net2_temp_user.py cleanup

# Remove expired users
python3 /etc/openhab/scripts/net2_temp_user.py cleanup --confirm

# Delete specific user (replace ID)
python3 /etc/openhab/scripts/net2_temp_user.py delete USER_ID

# ============================================================================
# ACCESS LEVEL QUICK REFERENCE
# ============================================================================
# You can use either the ID number OR the name (case insensitive, partial match works)
#
# ID  | Name                        | Usage Examples
# ----|-----------------------------|-----------------------------------------
# 0   | Ingen adgang                | --access-level 0  OR  --access-level "ingen"
# 1   | Altid - alle døre           | --access-level 1  OR  --access-level "alle døre"
# 2   | Arbejdstid                  | --access-level 2  OR  --access-level "arbejdstid"
# 3   | Kirkegade 50                | --access-level 3  OR  --access-level "kirkegade"
# 4   | Bohrsvej                    | --access-level 4  OR  --access-level "bohrsvej"
# 5   | Porsevej 19                 | --access-level 5  OR  --access-level "porsevej"
# 6   | Terndrupvej 81              | --access-level 6  OR  --access-level "terndrupvej"

# ============================================================================
# AUTOMATION SETUP
# ============================================================================

# Add to crontab for automatic cleanup at 3 AM daily:
# 0 3 * * * cd /etc/openhab/scripts && /usr/bin/python3 net2_temp_user.py cleanup --confirm >> /var/log/openhab/net2-cleanup.log 2>&1

# ============================================================================
# OPENHAB INTEGRATION EXAMPLES
# ============================================================================

# Rule to add contractor when button pressed:
# executeCommandLine(Duration.ofSeconds(30),
#     "python3", "/etc/openhab/scripts/net2_temp_user.py",
#     "add", "Contractor", "Access",
#     "--hours", "8", "--access-level", "2", "--pin", "1234")

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

# Test authentication:
# python3 /etc/openhab/scripts/net2_temp_user.py levels

# View all users (including permanent):
# python3 /etc/openhab/scripts/net2_temp_user.py list --all

# Check script help:
# python3 /etc/openhab/scripts/net2_temp_user.py --help
# python3 /etc/openhab/scripts/net2_temp_user.py add --help

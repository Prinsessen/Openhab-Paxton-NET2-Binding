#!/usr/bin/env python3
"""
Paxton Net2 Temporary User Management Script

This script creates temporary users in the Paxton Net2 access control system
with time-limited access and specific permission levels.

Usage:
    # Create a temporary user with 24-hour access
    python3 net2_temp_user.py add "John" "Doe" --hours 24 --access-level 3 --pin 1234
    
    # Create a user valid for 7 days
    python3 net2_temp_user.py add "Jane" "Smith" --days 7 --access-level 1 --pin 5678
    
    # List all temporary users (with TEMP_ prefix)
    python3 net2_temp_user.py list
    
    # Delete a temporary user
    python3 net2_temp_user.py delete 60
    
    # Cleanup expired users
    python3 net2_temp_user.py cleanup

Available Access Levels:
    0 - Ingen adgang (No access)
    1 - Altid - alle døre (Always - all doors)
    2 - Arbejdstid (Work hours)
    3 - Kirkegade 50
    4 - Bohrsvej
    5 - Porsevej 19
    6 - Terndrupvej 81

Author: OpenHAB Smart Home System
Date: 2026-01-05
"""

import requests
import json
import argparse
import os
from datetime import datetime, timedelta
from urllib3.exceptions import InsecureRequestWarning
import sys

# Disable SSL warnings for self-signed certificates
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Configuration file path
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'net2_config.json')

# Temporary user prefix for easy identification
TEMP_USER_PREFIX = "TEMP_"

# Access level mapping
ACCESS_LEVELS = {
    0: "Ingen adgang (No access)",
    1: "Altid - alle døre (Always - all doors)",
    2: "Arbejdstid (Work hours)",
    3: "Kirkegade 50",
    4: "Bohrsvej",
    5: "Porsevej 19",
    6: "Terndrupvej 81"
}


def load_config():
    """
    Load configuration from net2_config.json file
    
    Returns:
        dict: Configuration dictionary with base_url, username, password, grant_type, client_id
    """
    try:
        if not os.path.exists(CONFIG_FILE):
            print(f"❌ Configuration file not found: {CONFIG_FILE}")
            print(f"\nPlease create a configuration file with the following structure:")
            print(json.dumps({
                "base_url": "https://your-server:8443/api/v1",
                "username": "Your Username",
                "password": "Your Password",
                "grant_type": "password",
                "client_id": "your-client-id"
            }, indent=2))
            sys.exit(1)
        
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Validate required fields
        required_fields = ['base_url', 'username', 'password', 'grant_type', 'client_id']
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            print(f"❌ Missing required fields in config file: {', '.join(missing_fields)}")
            sys.exit(1)
        
        return config
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading config file: {e}")
        sys.exit(1)


def parse_access_level(access_level_input):
    """
    Parse access level from either ID (int) or name (string)
    Returns the access level ID or None if invalid
    """
    # If it's already an integer, validate it
    if isinstance(access_level_input, int):
        if access_level_input in ACCESS_LEVELS:
            return access_level_input
        return None
    
    # If it's a string, try to convert to int first
    if isinstance(access_level_input, str):
        # Try as number
        try:
            level_id = int(access_level_input)
            if level_id in ACCESS_LEVELS:
                return level_id
        except ValueError:
            pass
        
        # Try as name (case-insensitive partial match)
        search_term = access_level_input.lower().strip()
        for level_id, level_name in ACCESS_LEVELS.items():
            if search_term in level_name.lower():
                return level_id
    
    return None


class Net2API:
    """Wrapper for Paxton Net2 API calls"""
    
    def __init__(self, config):
        self.config = config
        self.base_url = config['base_url']
        self.token = None
        self.headers = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate and get access token"""
        try:
            payload = {
                'username': self.config['username'],
                'password': self.config['password'],
                'grant_type': self.config['grant_type'],
                'client_id': self.config['client_id']
            }
            response = requests.post(
                f"{self.base_url}/authorization/tokens",
                data=payload,
                verify=False,
                timeout=10
            )
            response.raise_for_status()
            
            self.token = response.json().get("access_token")
            if not self.token:
                raise Exception("Failed to obtain access token")
            
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            return True
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def get_users(self):
        """Get all users from the system"""
        try:
            response = requests.get(
                f"{self.base_url}/users",
                headers=self.headers,
                verify=False,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to fetch users: {e}")
            return []
    
    def create_user(self, user_data):
        """Create a new user"""
        try:
            response = requests.post(
                f"{self.base_url}/users",
                headers=self.headers,
                json=user_data,
                verify=False,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to create user: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Server response: {e.response.text}")
            return None
    
    def delete_user(self, user_id):
        """Delete a user by ID"""
        try:
            response = requests.delete(
                f"{self.base_url}/users/{user_id}",
                headers=self.headers,
                verify=False,
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"❌ Failed to delete user {user_id}: {e}")
            return False
    
    def get_access_levels(self):
        """Get all available access levels"""
        try:
            response = requests.get(
                f"{self.base_url}/accesslevels",
                headers=self.headers,
                verify=False,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to fetch access levels: {e}")
            return []


def add_temporary_user(api, first_name, last_name, middle_name="", hours=24, days=0, 
                      access_level=0, pin=None, department_id=None):
    """
    Add a temporary user to the Net2 system
    
    Args:
        api: Net2API instance
        first_name: User's first name
        last_name: User's last name
        middle_name: User's middle name (optional)
        hours: Number of hours until expiry
        days: Number of days until expiry (added to hours)
        access_level: Access level ID (0-6)
        pin: PIN code for the user (optional)
        department_id: Department ID (optional)
    
    Returns:
        Created user object or None on failure
    """
    
    # Parse and validate access level (accepts ID or name)
    access_level_id = parse_access_level(access_level)
    if access_level_id is None:
        print(f"❌ Invalid access level '{access_level}'.")
        print(f"\nValid options:")
        for level_id, level_name in ACCESS_LEVELS.items():
            print(f"  {level_id} - {level_name}")
        return None
    
    access_level = access_level_id  # Use the parsed ID
    
    # Calculate dates
    now = datetime.now()
    activate_date = now
    expiry_date = now + timedelta(hours=hours, days=days)
    
    # Prepare user data
    user_data = {
        "firstName": f"{TEMP_USER_PREFIX}{first_name}",
        "lastName": last_name,
        "middleName": middle_name or "",
        "expiryDate": expiry_date.isoformat(),
        "activateDate": activate_date.isoformat(),
        "isAntiPassbackUser": False,
        "isAlarmUser": False,
        "isLockdownExempt": False,
        "doorAccessPermissionSet": {
            "accessLevels": [access_level],
            "individualPermissions": []
        }
    }
    
    # Add optional fields
    if pin:
        user_data["pin"] = str(pin)
    
    if department_id:
        user_data["departmentId"] = department_id
    
    # Create user
    print(f"\n📝 Creating temporary user:")
    print(f"   Name: {user_data['firstName']} {middle_name} {last_name}".replace("  ", " "))
    print(f"   Access Level: {access_level} - {ACCESS_LEVELS[access_level]}")
    print(f"   Active From: {activate_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Expires On: {expiry_date.strftime('%Y-%m-%d %H:%M')}")
    if pin:
        print(f"   PIN: {pin}")
    
    created_user = api.create_user(user_data)
    
    if created_user:
        print(f"\n✅ User created successfully!")
        print(f"   User ID: {created_user['id']}")
        print(f"   Full Name: {created_user['firstName']} {created_user.get('middleName', '')} {created_user['lastName']}".replace("  ", " "))
        print(f"\n💡 To delete this user, run:")
        print(f"   python3 net2_temp_user.py delete {created_user['id']}")
        return created_user
    
    return None


def list_temporary_users(api, show_all=False):
    """
    List all temporary users (with TEMP_ prefix) or all users
    
    Args:
        api: Net2API instance
        show_all: If True, show all users, not just temporary ones
    """
    users = api.get_users()
    
    if not users:
        print("❌ No users found or failed to fetch users")
        return
    
    # Filter temporary users unless show_all is True
    if not show_all:
        users = [u for u in users if u.get('firstName', '').startswith(TEMP_USER_PREFIX)]
    
    if not users:
        print("✓ No temporary users found")
        return
    
    print(f"\n{'='*80}")
    print(f"{'ID':<6} {'Name':<30} {'Expiry Date':<20} {'Access Level':<15}")
    print(f"{'='*80}")
    
    from datetime import timezone
    now = datetime.now(timezone.utc)
    
    for user in sorted(users, key=lambda x: x.get('expiryDate') or '9999'):
        user_id = user.get('id', 'N/A')
        first_name = user.get('firstName', '')
        middle_name = user.get('middleName') or ''
        last_name = user.get('lastName', '')
        full_name = f"{first_name} {middle_name} {last_name}".replace("  ", " ").strip()
        
        expiry = user.get('expiryDate')
        if expiry:
            expiry_dt = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
            expiry_str = expiry_dt.strftime('%Y-%m-%d %H:%M')
            if expiry_dt < now:
                expiry_str += " (EXPIRED)"
        else:
            expiry_str = "Never"
        
        # Get access level from doorAccessPermissionSet
        access_info = "Not set"
        door_perms = user.get('doorAccessPermissionSet')
        if door_perms and door_perms.get('accessLevels'):
            levels = door_perms['accessLevels']
            if levels:
                level_id = levels[0]
                level_name = ACCESS_LEVELS.get(level_id, f"Unknown({level_id})")
                access_info = f"{level_id}"
        
        print(f"{user_id:<6} {full_name:<30} {expiry_str:<20} {access_info:<15}")
    
    print(f"{'='*80}")
    print(f"Total: {len(users)} users")


def delete_temporary_user(api, user_id):
    """
    Delete a user by ID (with confirmation)
    
    Args:
        api: Net2API instance
        user_id: ID of the user to delete
    """
    # Fetch user details first
    users = api.get_users()
    user = next((u for u in users if u.get('id') == user_id), None)
    
    if not user:
        print(f"❌ User with ID {user_id} not found")
        return False
    
    # Display user info
    first_name = user.get('firstName', '')
    middle_name = user.get('middleName') or ''
    last_name = user.get('lastName', '')
    full_name = f"{first_name} {middle_name} {last_name}".replace("  ", " ").strip()
    
    print(f"\n⚠️  About to delete user:")
    print(f"   ID: {user_id}")
    print(f"   Name: {full_name}")
    print(f"   Expiry: {user.get('expiryDate', 'Never')}")
    
    # Confirm deletion (skip for TEMP_ users)
    if not first_name.startswith(TEMP_USER_PREFIX):
        response = input("\n⚠️  This is NOT a temporary user. Are you sure you want to delete? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Deletion cancelled")
            return False
    
    # Delete user
    if api.delete_user(user_id):
        print(f"✅ User {user_id} ({full_name}) deleted successfully")
        return True
    
    return False


def cleanup_expired_users(api, dry_run=False):
    """
    Delete all expired temporary users
    
    Args:
        api: Net2API instance
        dry_run: If True, only show what would be deleted without actually deleting
    """
    users = api.get_users()
    temp_users = [u for u in users if u.get('firstName', '').startswith(TEMP_USER_PREFIX)]
    
    if not temp_users:
        print("✓ No temporary users found")
        return
    
    from datetime import timezone
    now = datetime.now(timezone.utc)
    expired_users = []
    
    for user in temp_users:
        expiry = user.get('expiryDate')
        if expiry:
            expiry_dt = datetime.fromisoformat(expiry.replace('Z', '+00:00'))
            if expiry_dt < now:
                expired_users.append(user)
    
    if not expired_users:
        print("✓ No expired temporary users found")
        return
    
    print(f"\n{'='*80}")
    print(f"Found {len(expired_users)} expired temporary user(s):")
    print(f"{'='*80}")
    
    for user in expired_users:
        user_id = user.get('id')
        first_name = user.get('firstName', '')
        middle_name = user.get('middleName') or ''
        last_name = user.get('lastName', '')
        full_name = f"{first_name} {middle_name} {last_name}".replace("  ", " ").strip()
        expiry = user.get('expiryDate')
        
        print(f"ID {user_id}: {full_name} (expired: {expiry})")
    
    if dry_run:
        print(f"\n💡 This was a dry run. Use --confirm to actually delete these users.")
        return
    
    # Confirm deletion
    response = input(f"\n⚠️  Delete all {len(expired_users)} expired users? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cleanup cancelled")
        return
    
    # Delete expired users
    deleted_count = 0
    for user in expired_users:
        user_id = user.get('id')
        if api.delete_user(user_id):
            deleted_count += 1
            print(f"✅ Deleted user {user_id}")
        else:
            print(f"❌ Failed to delete user {user_id}")
    
    print(f"\n✅ Cleanup complete: {deleted_count}/{len(expired_users)} users deleted")


def show_access_levels(api):
    """Display all available access levels"""
    levels = api.get_access_levels()
    
    print(f"\n{'='*60}")
    print("Available Access Levels:")
    print(f"{'='*60}")
    print(f"{'ID':<6} {'Name':<50}")
    print(f"{'='*60}")
    
    for level in levels:
        print(f"{level['id']:<6} {level['name']:<50}")
    
    print(f"{'='*60}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Manage temporary users in Paxton Net2 access control system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create user with 24-hour access to Kirkegade 50
  %(prog)s add "John" "Doe" --hours 24 --access-level 3 --pin 1234
  
  # Create user valid for 7 days with full access
  %(prog)s add "Jane" "Smith" --days 7 --access-level 1 --pin 5678
  
  # List all temporary users
  %(prog)s list
  
  # Show available access levels
  %(prog)s levels
  
  # Delete a specific user
  %(prog)s delete 60
  
  # Cleanup expired users (dry run)
  %(prog)s cleanup
  
  # Cleanup expired users (actually delete)
  %(prog)s cleanup --confirm
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add user command
    add_parser = subparsers.add_parser('add', help='Add a temporary user')
    add_parser.add_argument('first_name', help='First name')
    add_parser.add_argument('last_name', help='Last name')
    add_parser.add_argument('--middle-name', default='', help='Middle name (optional)')
    add_parser.add_argument('--hours', type=int, default=24, help='Valid for N hours (default: 24)')
    add_parser.add_argument('--days', type=int, default=0, help='Valid for N days (added to hours)')
    add_parser.add_argument('--access-level', default='0', 
                          help='Access level: use ID (0-6) or name (e.g., "Kirkegade 50", "alle døre"). Default: 0 (no access)')
    add_parser.add_argument('--pin', help='PIN code for door access (optional)')
    add_parser.add_argument('--department', type=int, help='Department ID (optional)')
    
    # List users command
    list_parser = subparsers.add_parser('list', help='List temporary users')
    list_parser.add_argument('--all', action='store_true', help='Show all users, not just temporary')
    
    # Delete user command
    delete_parser = subparsers.add_parser('delete', help='Delete a user')
    delete_parser.add_argument('user_id', type=int, help='User ID to delete')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Delete expired temporary users')
    cleanup_parser.add_argument('--confirm', action='store_true', 
                               help='Actually delete (without this, only shows what would be deleted)')
    
    # Show access levels command
    levels_parser = subparsers.add_parser('levels', help='Show available access levels')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Load configuration
    config = load_config()
    
    # Initialize API
    print("🔐 Authenticating with Paxton Net2...")
    api = Net2API(config)
    
    if not api.token:
        print("❌ Failed to authenticate. Please check credentials.")
        sys.exit(1)
    
    print("✅ Authentication successful")
    
    # Execute command
    if args.command == 'add':
        add_temporary_user(
            api,
            args.first_name,
            args.last_name,
            args.middle_name,
            args.hours,
            args.days,
            args.access_level,
            args.pin,
            args.department
        )
    
    elif args.command == 'list':
        list_temporary_users(api, args.all)
    
    elif args.command == 'delete':
        delete_temporary_user(api, args.user_id)
    
    elif args.command == 'cleanup':
        cleanup_expired_users(api, dry_run=not args.confirm)
    
    elif args.command == 'levels':
        show_access_levels(api)


if __name__ == '__main__':
    main()

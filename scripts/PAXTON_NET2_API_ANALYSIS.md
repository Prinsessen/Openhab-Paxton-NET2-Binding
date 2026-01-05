# Paxton Net2 API - Comprehensive Analysis

## Server Details
- **Base URL**: `https://milestone.agesen.dk:8443/api/v1`
- **Authentication**: OAuth2 (password grant type)
- **Current Version**: Net2 v6.7+ (with extended API)

---

## Authentication

### Endpoint: `/api/v1/authorization/tokens`
**Method**: POST

**Credentials**:
- Username: Nanna Agesen
- Password: [configured]
- Grant Type: password
- Client ID: 00aab996-6439-4f16-89b4-6c0cc851e8f3

**Returns**: Bearer token for subsequent API calls

---

## Available API Endpoints

### ✅ Working Endpoints

#### 1. **Events** - `/api/v1/events`
**Status**: ✅ Working  
**Purpose**: Retrieve access control events, door activity, system events

**Event Types Discovered**:
- **Type 20**: Adgang godkendt - med kort (Access granted - with card)
- **Type 26**: Adgang godkendt - med PIN kode (Access granted - with PIN)
- **Type 24**: Adgang nægtet - ugyldig PIN (Access denied - invalid PIN)
- **Type 23**: Other access denied reasons
- **Type 28/46**: Dør åbnet (Door opened)
- **Type 29/47**: Dør lukket (Door closed)
- **Type 93**: Dør holdt åben (Door held open)
- **Type 65**: En Net2 regel blev udført (Net2 rule executed)
- **Type 550**: Systembruger (System user login)
- **Type 552**: Backup gennemført (Backup completed)
- **Type 723**: Batteriniveau er kritisk lavt (Battery critically low)

**Fields**:
```json
{
  "eventTime": "2026-01-05T06:00:01.017+01:00",
  "id": 1545681,
  "deviceName": "Kirkegade50 - Garage Port - ACU:7242929",
  "cardNo": 1908,
  "eventType": 26,
  "eventDescription": "Adgang godkendt - med PIN kode",
  "eventSubType": 0,
  "eventDetails": null,
  "linkedEvent": null,
  "firstName": "Nanna",
  "middleName": "Sloth",
  "surname": "Agesen",
  "userID": 8,
  "priority": 15,
  "address": 7242929,
  "peripheralID": 427,
  "ioBoardID": null,
  "doorGroupID": 0,
  "deviceDeleted": false
}
```

**Parameters**:
- `startDate`: ISO datetime
- `endDate`: ISO datetime
- `pageSize`: Number of results (max tested: 1000)

---

#### 2. **Users** - `/api/v1/users`
**Status**: ✅ Working  
**Purpose**: Retrieve user information, PINs, access levels, card numbers

**List All Users**: GET `/api/v1/users`  
**Get Single User**: GET `/api/v1/users/{userId}`

**Fields**:
```json
{
  "id": 8,
  "firstName": "Nanna",
  "middleName": "Sloth",
  "lastName": "Agesen",
  "expiryDate": null,
  "activateDate": "2013-11-11T00:00:00+01:00",
  "pin": "1275",
  "telephone": "98232011",
  "extension": null,
  "fax": null,
  "isAntiPassbackUser": true,
  "isAlarmUser": true,
  "isLockdownExempt": false,
  "hasImage": true,
  "customFields": [...],
  "doorAccessPermissionSet": {
    "accessLevels": [1],
    "individualPermissions": []
  }
}
```

**Capabilities**:
- Get user details
- Check access levels
- View PIN codes
- Check active/expiry dates
- Anti-passback status
- Alarm user status
- Custom fields

---

#### 3. **Doors** - `/api/v1/doors`
**Status**: ✅ Working  
**Purpose**: List all doors/access points in the system

**Response**:
```json
[
  {
    "name": "Andreas Udv.Kælder -  ACU 01038236",
    "id": 6626578
  },
  {
    "name": "Garage Port - ACU:7242929",
    "id": 7242929
  }
]
```

**Your Doors**:
1. Andreas Udv.Kælder - ACU 01038236 (ID: 6626578)
2. Fordør - ACU 6612642 (ID: 6612642)
3. Fordør Porsevej - ACU:967438 (ID: 7319051)
4. Fordør Terndrupvej - ACU:6203980 (ID: 6203980)
5. Garage Port - ACU:7242929 (ID: 7242929)
6. Værksted - ACU 01265688 (ID: 1265688)
7. Værksted Dør - Central 03962494 (ID: 3962494)

---

#### 4. **Door Control** - `/api/v1/commands/door/control`
**Status**: ✅ Working (from net2.py)  
**Purpose**: Control doors (open, close, lock/unlock)

**Method**: POST

**Payload**:
```json
{
  "DoorId": 6612642,
  "RelayFunction": {
    "RelayId": "Relay1",
    "RelayAction": "TimedOpen",
    "RelayOpenTime": 8000
  },
  "LedFlash": 3
}
```

**Relay Actions**:
- `TimedOpen`: Open for specified duration
- `Unlock`: Permanently unlock
- `Lock`: Lock the door

---

#### 5. **Access Levels** - `/api/v1/accesslevels`
**Status**: ✅ Working  
**Purpose**: List access level definitions

**Response**:
```json
[
  {
    "id": 0,
    "name": "Ingen adgang"
  },
  {
    "id": 1,
    "name": "Altid - alle døre"
  },
  {
    "id": 2,
    "name": "Arbejdstid"
  },
  {
    "id": 3,
    "name": "Kirkegade 50"
  },
  {
    "id": 4,
    "name": "Bohrsvej"
  },
  {
    "id": 5,
    "name": "Porsevej 19"
  },
  {
    "id": 6,
    "name": "Terndrupvej 81"
  }
]
```

---

#### 6. **Operators** - `/api/v1/operators`
**Status**: ✅ Working  
**Purpose**: List system operators (admin users)

**Response**:
```json
[
  {
    "userID": 8,
    "firstName": "Nanna",
    "surname": "Agesen",
    "displayName": "Nanna Agesen"
  }
]
```

---

#### 7. **Departments** - `/api/v1/departments`
**Status**: ✅ Working  
**Purpose**: List organizational departments/locations

**Your Departments**:
- Bohrsvej 2 (ID: 3)
- Kirkegade 50 (ID: 4)
- Porsevej 19 (ID: 5)
- Terndrupvej 81 (ID: 6)
- AD_Originated (ID: 10)

---

#### 8. **Timezones** - `/api/v1/timezones`
**Status**: ✅ Working  
**Purpose**: List access control time zones

---

### ❌ Not Available (404) Endpoints

- `/api/v1/areas` - Area management
- `/api/v1/devices` - Device management
- `/api/v1/holidays` - Holiday schedules
- `/api/v1/sites` - Site management
- `/api/v1/commands` - General commands (only door/control works)
- `/api/v1/monitoring` - Live monitoring
- `/api/v1/reports` - Pre-built reports

---

## Existing Scripts

### 1. **net2.py** - Door Control
**Purpose**: Open/control a specific door  
**Capabilities**:
- OAuth2 authentication
- Send door control commands
- Specify relay action and timing
- LED flash control

### 2. **net2_user_activity.py** - Activity Reports
**Purpose**: Generate HTML reports of user access activity  
**Capabilities**:
- Retrieve events from API
- Filter door-related events
- Generate main user activity report
- Generate per-door reports (last 10 events)
- Auto-refresh HTML pages
- Event classification (granted/denied)

---

## Potential Comprehensive Script Features

### 📊 **Data Collection & Monitoring**
1. ✅ **Event Monitoring** (Already implemented)
   - Real-time event collection
   - Historical event retrieval
   - Event filtering by type

2. **User Management**
   - List all users
   - Get user details
   - Check access permissions
   - View PIN codes
   - Monitor expiry dates
   - Track active/inactive users

3. **Door Status & Control**
   - List all doors
   - Get door status
   - Control doors remotely
   - Monitor door open/close events
   - Track most used doors

4. **Access Level Analysis**
   - Map users to access levels
   - Identify permission gaps
   - Generate access matrices

5. **Department Reports**
   - Group users by department
   - Department access statistics
   - Cross-department access analysis

### 📈 **Analytics & Reports**
1. **User Activity Analytics**
   - Most active users
   - Peak usage times
   - Access patterns
   - Failed access attempts
   - Anti-passback violations

2. **Door Analytics**
   - Door usage frequency
   - Peak hours per door
   - Average time between accesses
   - Failed access rates

3. **Security Reports**
   - Failed access attempts by user
   - Unusual access patterns
   - After-hours access
   - Multiple location conflicts
   - Alarm user activity

4. **System Health**
   - Battery status alerts
   - Device offline notifications
   - Backup status
   - System events log

### 🔔 **Alerting & Notifications**
1. **Security Alerts**
   - Multiple failed access attempts
   - Access denied events
   - After-hours access
   - Door held open too long

2. **System Alerts**
   - Low battery warnings
   - Device offline
   - User expiry upcoming
   - Backup failures

### 🎨 **Visualization & Dashboards**
1. **Real-time Dashboard**
   - Live event feed
   - Current door states
   - Active users today
   - System health status

2. **Historical Dashboards**
   - Access trends over time
   - User activity heatmaps
   - Department usage charts
   - Door utilization graphs

### 🔧 **Management Functions**
1. **User Management** (if POST/PUT available)
   - Add/edit users
   - Change PINs
   - Update access levels
   - Set expiry dates

2. **Door Control**
   - Remote door opening
   - Scheduled door unlocking
   - Lockdown activation
   - Emergency access

### 📤 **Integration & Export**
1. **Data Export**
   - CSV export of events
   - JSON API for other systems
   - Database synchronization
   - Backup data extraction

2. **OpenHAB Integration**
   - Items for each door
   - Rules for automation
   - Sitemap widgets
   - Presence detection

---

## Recommended Comprehensive Script Structure

### **Module 1: API Client Library**
```python
class PaxtonNet2Client:
    - authenticate()
    - get_events()
    - get_users()
    - get_doors()
    - get_access_levels()
    - control_door()
    - get_user_detail()
    - get_operators()
    - get_departments()
```

### **Module 2: Data Processors**
```python
- EventProcessor: Parse and categorize events
- UserProcessor: Analyze user data
- DoorProcessor: Process door information
- SecurityAnalyzer: Detect security issues
```

### **Module 3: Report Generators**
```python
- HTMLReportGenerator: Create web dashboards
- CSVExporter: Export data to CSV
- PDFGenerator: Create PDF reports
- EmailReporter: Send email summaries
```

### **Module 4: Monitoring & Alerts**
```python
- EventMonitor: Real-time event watching
- AlertManager: Send notifications
- ThresholdChecker: Detect anomalies
```

### **Module 5: OpenHAB Integration**
```python
- ItemsGenerator: Create OpenHAB items
- RulesGenerator: Generate automation rules
- SitemapBuilder: Build UI elements
```

---

## Data Storage Recommendations

### Option 1: SQLite Database
**Pros**: Simple, file-based, no server needed  
**Cons**: Limited concurrent access

**Schema**:
- `events` - All access events
- `users` - User information cache
- `doors` - Door list cache
- `alerts` - Generated alerts
- `statistics` - Pre-calculated stats

### Option 2: InfluxDB
**Pros**: Time-series optimized, great for analytics  
**Cons**: Additional service required

### Option 3: JSON Files
**Pros**: Simple, human-readable  
**Cons**: Not scalable, slow queries

---

## Next Steps - Discussion Points

1. **What is the primary goal?**
   - Real-time monitoring?
   - Historical analysis?
   - Security auditing?
   - Management automation?

2. **What reports are most valuable?**
   - Daily activity summaries?
   - Security incident reports?
   - User access audits?
   - Door usage analytics?

3. **Integration needs?**
   - OpenHAB automation?
   - Email notifications?
   - Mobile app?
   - Web dashboard?

4. **Data retention?**
   - How long to keep events?
   - Local database vs API only?
   - Backup strategy?

5. **Update frequency?**
   - Real-time monitoring?
   - Hourly reports?
   - Daily summaries?

6. **Alert priorities?**
   - Security issues?
   - System health?
   - User management?
   - Door problems?

---

## Current Implementation Status

✅ **Completed**:
- Basic event retrieval
- User activity HTML reports
- Per-door activity reports (last 10 events)
- Door control commands
- Auto-refresh dashboards

🔄 **Partially Implemented**:
- Event filtering
- HTML report generation

❌ **Not Yet Implemented**:
- User management interface
- Real-time monitoring
- Alert system
- Database storage
- CSV/PDF exports
- Analytics dashboard
- Security auditing
- OpenHAB automation rules
- Email notifications

---

## Questions for You

1. What's the **most important feature** you need?
2. Do you want **real-time monitoring** or periodic reports?
3. Should the script **store historical data** locally?
4. Do you need **alerts/notifications** (email, SMS, OpenHAB)?
5. What **security concerns** should we prioritize?
6. Do you want **automated actions** based on events?
7. Should we create a **unified dashboard** or separate tools?
8. What **time ranges** are most important (hourly, daily, weekly)?

Let's discuss which direction would be most valuable for your use case!

#!/usr/bin/python

import requests

headers = { 
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': 'bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1bmlxdWVfbmFtZSI6Ik5hbm5hIEFnZXNlbiIsInVzZXJfaWQiOjgsInJvbGUiOiJTdXBlcnZpc29yIiwibGl2ZV9ldmVudHMiOiJyZWFkIiwiY2xpZW50X2lkIjoiMDBhYWI5OTYtNjQzOS00ZjE2LTg5YjQtNmMwY2M4NTFlOGYzIiwidGVuYW50IjoiQlVMTE9DSyIsImF1ZCI6Ik5ldDJMb2NhbFdlYkFwaSIsImp0aSI6ImU2MTAyOTZmYjNhNjRjNDFiOTc1ZGZmMWI1NTM2YWMxIiwibmJmIjoxNTgwNTY4MzUwLCJleHAiOjE1ODA1NzAxNTAsImlhdCI6MTU4MDU2ODM1MCwiaXNzIjoiTmV0MkxvY2FsV2ViQXBpIn0.K4LmrH_3wMBD40OxuqD24ISs6JBEz0OW11ExtPty8TPmsDl3pD4364w6NOZvdSnDVBFo1VFj2hn5foJn_fEUlK96d0f0uMpbEicUrV0m_487DSg5SQD4FamHYyHSYXRbCe7gglMwJhMmKBqiEi37CwErBUp8ABirnH5DUCBqc9iHbOo8COuELwMvLq3VjhmppCEL_jW6tqbWpbOP_mJKCOLOaX9zns8lST4uWVKehtmYu0l90S3eiytBEFhvZts7G-0NtoMQXo1zzU72GAl8t0FmiFnASODpYuVI7VltTTQnQrJlU6DOIRIacJdpMCywcRZINGg_xK4-5J1LFCe1Ig',
}

data = '{"DoorId": 6612642, "RelayFunction": {"RelayId": "Relay1", "RelayAction": "TimedOpen", "RelayOpenTime": 7000}, "LedFlash": 3}'

response = requests.post('http://bullock:8080/api/v1/commands/door/control', headers=headers, data=data)

print response.content

#!/usr/bin/python

# importing the requests library 
import json, requests

#  Values that you need to provide

Paxton_auth = "http://bullock:8080/api/v1/authorization/tokens"
Paxton_open_door = "http://bullock:8080/api/v1/commands/door/control"

username = "Nanna Agesen"
password = "Jekboapj110"
grant_type = "password"
client_id = "00aab996-6439-4f16-89b4-6c0cc851e8f3"

DoorId = "6612642"
RelayId = "Relay1"
RelayAction = "TimedOpen"
RelayOpenTime = 7000
LedFlash = 3

#  Do not change below

payload_auth = {
    'username': username,
    'password': password,
    'grant_type': grant_type,
    'client_id': client_id
    		
}


data = '{"DoorId": 6612642, "RelayFunction": {"RelayId": "Relay1", "RelayAction": "TimedOpen", "RelayOpenTime": 7000}, "LedFlash": 3}'


r = requests.post( url = Paxton_auth, data = payload_auth)

body = json.loads(r.content)

token = body["access_token"]

r = requests.post(url = Paxton_open_door, headers = {'Content-Type': 'application/json',
    'Accept': 'application/json','Authorization':'Bearer ' + token}, data = data)

print r.content
print r
 












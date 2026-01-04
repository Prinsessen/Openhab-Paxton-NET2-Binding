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
DoorId = 3962475
RelayId = "Relay2"
RelayAction = "TimedOpen"
RelayOpenTime = 7
LedFlash =  3

#  Do not change below

payload_auth = {
    'username': username,
    'password': password,
    'grant_type': grant_type,
    'client_id': client_id
    		
}

print payload_auth


payload_doorid = '{ \\ \n   "DoorId": 6612642, \\ \n   "RelayFunction": { \\ \n     "RelayId": "Relay1", \\ \n     "RelayAction": "TimedOpen", \\ \n     "RelayOpenTime": 7000 \\ \n   }, \\ \n   "LedFlash": 3 \\ \n }'




print payload_doorid


r = requests.post( url = Paxton_auth, data = payload_auth)

body = json.loads(r.content)

token = body["access_token"]

print token

r = requests.post(url = Paxton_open_door, headers = {'Content-Type': 'application/json',
    'Accept': 'application/json',"Authorization":"Bearer " + token}, data = payload_doorid)

print r.content
 












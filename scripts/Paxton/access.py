#!/usr/bin/python

# importing the requests library 
import json, requests

#  Values that you need to provide

Paxton_auth = "http://bullock:8080/api/v1/authorization/tokens"
Paxton_events = "http://bullock:8080/api/v1/events/latestunknowntokens?max=5"

username = "System tekniker"
password = "remote110"
grant_type = "password"
client_id = "00aab996-6439-4f16-89b4-6c0cc851e8f3"
DoorId = "6612642"

#  Do not change below

payload_auth = {
    'username': username,
    'password': password,
    'grant_type': grant_type,
    'client_id': client_id
    		
}


r = requests.post( url = Paxton_auth, data = payload_auth)

body = json.loads(r.content)

token = body["access_token"]

# print token

r = requests.get(url = Paxton_events, headers = {"Authorization":"Bearer " + token})


# extracting response text  
body = r.text 

body = json.loads(r.text)

token = body["id"]

# print token


 

 












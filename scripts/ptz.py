#!/usr/bin/python

# importing the requests library

import requests
from requests.auth import HTTPDigestAuth

# make request
url = "http://192.168.100.128/ISAPI/PTZCtrl/channels/1/presets/2/goto"
r = requests.put(url, auth=HTTPDigestAuth('admin', 'Jekboapj110'), stream=True)

print(r.text)


print(r.headers)
print(r.status_code)


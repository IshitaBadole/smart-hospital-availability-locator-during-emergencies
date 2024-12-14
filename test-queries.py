#!/usr/bin/env python3

import json
import os
import random
import time

import jsonpickle
import requests

#
# Use localhost & port 5000 if not specified by environment variable REST
#
REST = os.getenv("REST") or "localhost:5000"

##
# The following routine makes a JSON REST query of the specified type
# and if a successful JSON reply is made, it pretty-prints the reply
##


def mkReq(reqmethod, endpoint, data, verbose=True):
    print(f"Response to http://{REST}/{endpoint} request is {type(data)}")
    jsonData = jsonpickle.encode(data)
    if verbose and data != None:
        print(f"Make request http://{REST}/{endpoint} with json {data.keys()}")
        print(f"mp3 is of type {type(data['mp3'])} and length {len(data['mp3'])} ")
    response = reqmethod(
        f"http://{REST}/{endpoint}",
        data=jsonData,
        headers={"Content-type": "application/json"},
    )
    if response.status_code == 200:
        jsonResponse = json.dumps(response.json(), indent=4, sort_keys=True)
        print(jsonResponse)
        return
    else:
        print(
            f"response code is {response.status_code}, raw response is {response.text}"
        )
        return response.text


hospital_name = "BAYHEALTH HOSPITAL, SUSSEX CAMPUS"
endpoint = "/api/v1/query"
json_data = {"hospital_name": hospital_name}
response = requests.post(
    f"http://{REST}/{endpoint}",
    json=json_data,
    headers={"Content-type": "application/json"},
)
print(response.text)

endpoint = "/api/v1/queue"
response2 = requests.get(f"http://{REST}/{endpoint}")
print(response2.text)

time.sleep(10)
task_id = json.loads(response.text)["id"]
print(task_id)
endpoint = f"/api/v1/result/{task_id}"
response3 = requests.get(f"http://{REST}/{endpoint}")
print(response3.text)

"""
app: The entry point for the mqtt-service.
"""

import os
import datetime
import jsonapi_requests

import paho.mqtt.client as mqtt
from flask import Flask, escape

API = jsonapi_requests.Api.config({
    'API_ROOT': 'http://resource/',
    'VALIDATE_SSL': False,
    'TIMEOUT': 1,
})

CLIENT = mqtt.Client("mqtt-service-" + os.uname()[1])

APP = Flask(__name__)

@APP.route("/")
def root():
    """
    root: The root-route, only used for debugging.
    """
    endpoint = API.endpoint('mqtt-message')
    req = endpoint.post(object=jsonapi_requests.JsonApiObject(
        type='mqtt-message',
        attributes={
            "message-type": "CONNECT",
            "topic": "Hello",
            "body": "World",
            "retain": False,
            "created-at": str(datetime.datetime.now())
        },
    ))
    return escape(f"{req}")

if __name__ == "__main__":
    APP.run(host="0.0.0.0", port=80)

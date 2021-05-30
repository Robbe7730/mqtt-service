"""
app: The entry point for the mqtt-service.
"""

import os
import datetime
import jsonapi_requests
import configparser
import sys
import logging

from enum import Enum
import paho.mqtt.client as mqtt
from flask import Flask, escape

API = jsonapi_requests.Api.config({
    'API_ROOT': 'http://resource/',
    'VALIDATE_SSL': False,
    'TIMEOUT': 1,
})

APP = Flask(__name__)

class MessageType(Enum):
    CONNECT = 1
    DISCONNECT = 2
    PUBLISH = 3
    SUBSCRIBE = 4

class Message:
    def __init__(
            self,
            message_type: MessageType,
            topic: str,
            body: str = "",
            retain: bool = False
        ):
        self.message_type = message_type
        self.created_at = str(datetime.datetime.now())
        self.topic = topic
        self.body = body
        self.retain = retain

    def to_jsonapi(self):
        return jsonapi_requests.JsonApiObject(
            type='mqtt-message',
            attributes={
                "message-type": self.message_type.name,
                "topic": self.topic,
                "body": self.body,
                "retain": self.retain,
                "created-at": self.created_at
            },
        )

    @staticmethod
    def from_mqtt(mqtt_message):
        return Message(
            MessageType.PUBLISH,
            mqtt_message.topic,
            mqtt_message.payload.decode("utf-8"),
            mqtt_message.retain
        )

@APP.route("/")
def root():
    """
    root: The root-route, only used for debugging.
    """
    return "Hello world!"

def log_message(message: Message):
    try:
        endpoint = API.endpoint('mqtt-message')
        endpoint.post(object=message.to_jsonapi())
    except Exception as e:
        logging.error(e)


def on_message(client, userdata, mqtt_message):
    message = Message.from_mqtt(mqtt_message)
    log_message(message)

def on_connect(client, userdata, flags, rc):
    logging.info("Connected")
    client.subscribe("#")

def main():
    # Read/create the config file
    if not os.path.exists('config'):
        os.makedirs('config')
    config = configparser.ConfigParser()
    config.read("config/config.ini")

    if "mqtt" not in config:
        config["mqtt"] = {}

    if "broker-ip" not in config["mqtt"]:
        config["mqtt"]["broker-ip"] = "your-ip-here"
        with open('config/config.ini', 'w') as configfile:
            config.write(configfile)
        exit("Please specify the brokers IP in config/config.ini")

    # Connect to the broker
    client = mqtt.Client("mqtt-service-" + os.uname()[1])
    client.connect(config["mqtt"]["broker-ip"])
    client.on_message = on_message
    client.on_connect = on_connect
    client.loop_start()

    # Start the flask app
    APP.run(host="0.0.0.0", port=80)

    # Disconnect from the broker
    client.loop_stop()

if __name__ == "__main__":
    main()

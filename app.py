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
from flask import Flask, escape, request, jsonify

API = jsonapi_requests.Api.config({
    'API_ROOT': 'http://resource/',
    'VALIDATE_SSL': False,
    'TIMEOUT': 1,
})

CLIENT = mqtt.Client("mqtt-service-" + os.uname()[1])

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
            type='mqtt-messages',
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

    @staticmethod
    def from_json(json_data):
        #TODO: this should probably be handled by a JSON:API implementation
        if json_data is None or "data" not in json_data:
            return None, "Invalid JSON data or missing 'data' field."

        data = json_data["data"]

        if data.get("type", None) != "mqtt-messages":
            return None, "mqtt-service can only handle type 'mqtt-messages'."

        attributes = data.get("attributes", None)

        if attributes is None:
            return None, "Missing 'attributes' field."

        if attributes.get("message-type", "PUBLISH") != "PUBLISH":
            return None, "Can only PUBLISH new messages."

        topic = attributes.get("topic", None)

        if topic is None:
            return None, "Missing 'topic'"

        message = Message(
            MessageType.PUBLISH,
            topic
        )

        if "body" in attributes:
            message.body = attributes["body"]

        if "retain" in attributes:
            message.retain = attributes["retain"]

        # 'created-at' is ignored and only written by this service

        return message, "OK"


@APP.route("/", methods=["GET", "POST"])
def root():
    if request.method == "GET":
        return "Hello world!"
    if request.method == "POST":
        data = request.get_json()
        message, text = Message.from_json(data)

        if message is None:
            return jsonify({
                "errors": [text]
            }), 400

        publish_message(message)

        return jsonify({
            "data": {
                "type": "mqtt-messages"
            }
        }), 202

def log_message(message: Message):
    try:
        endpoint = API.endpoint('mqtt-messages')
        endpoint.post(object=message.to_jsonapi())
    except Exception as e:
        logging.exception(e)

def publish_message(message: Message):
    if message.message_type != MessageType.PUBLISH:
        logging.error("Only PUBLISH messages can be published")
        return

    CLIENT.publish(
        message.topic,
        message.body,
        retain=message.retain
    )

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
    CLIENT.connect(config["mqtt"]["broker-ip"])
    CLIENT.on_message = on_message
    CLIENT.on_connect = on_connect
    CLIENT.loop_start()

    # Start the flask app
    APP.run(host="0.0.0.0", port=80)

    # Disconnect from the broker
    client.loop_stop()

if __name__ == "__main__":
    main()

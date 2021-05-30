# mqtt-service

A microservice that dispatches and logs MQTT messages, made for use with the
mu-semtech stack.

## Endpoints

`POST /publish`: Publish a message to the MQTT network. A message consists of at
least a string `topic`, optionally containing a string `body`, and a `retain`
flag (boolean).

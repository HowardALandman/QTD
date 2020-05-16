#!/usr/bin/python3

import time
import paho.mqtt.client as mqtt

mqtt_server_name = "mqtt.eclipse.org"

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected to",mqtt_server_name,"with result code",rc)

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("QTD/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic,msg.payload.decode('UTF-8'))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(mqtt_server_name, 1883, 60)

client.loop_forever()


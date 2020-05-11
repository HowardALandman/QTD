#!/usr/bin/python3

import os
import time
import paho.mqtt.client as mqtt

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    #client.subscribe("$SYS/#")

# The callback for when a PUBLISH message is received from the server.
#def on_message(client, userdata, msg):
#    print(msg.topic+" "+str(msg.payload))

client = mqtt.Client()
client.on_connect = on_connect
#client.on_message = on_message

client.connect("mqtt.eclipse.org", 1883, 60)

cpu_temp_filename = "/sys/class/thermal/thermal_zone0/temp"
gpu_temp_command = "vcgencmd measure_temp"
temp = None

while True:
    try:
        cpu_temp_file = open(cpu_temp_filename)
    except:
        print("Couldn't open",cpu_temp_filename)
    else:
        temp_line = list(cpu_temp_file)[0]
        #temp = int(temp_line)
        # Smooth
        new_temp = int(temp_line)
        if temp is None:
            temp = new_temp
        else:
            temp = (temp + new_temp) / 2
        rounded = round(temp/1000,1)
        #print("CPU temp =",rounded)
    client.publish(topic="QTD/VDGG/qtd-0W/cpu_temp",payload=rounded,retain=True)

    try:
        gpu_temp = (os.popen(gpu_temp_command).read())[5:9]
    except:
        print("Running",gpu_temp_command,"failed.")
        gpu_temp = "Failed"
    else:
        #print("GPU temp =",gpu_temp)
        pass
    client.publish(topic="QTD/VDGG/qtd-0W/gpu_temp",payload=gpu_temp,retain=True)
    client.loop()
    print(".",end="")
    time.sleep(5)

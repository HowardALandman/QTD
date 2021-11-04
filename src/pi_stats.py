#!/usr/bin/python3
"""Publish Raspberry Pi status, updating once per minute."""

import time
import os
import signal
import sys
import socket
import paho.mqtt.client as mqtt

# Handle ^C keyboard interrupt.
def sigint_handler(sig, frame):
    """Exit as gracefully as possible."""
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)

# I2C bus devices
import board
import busio
import adafruit_si5351
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
i2c = busio.I2C(board.SCL, board.SDA)
#
# Si5351 clock generator, i2c address 0x60
# Used to generate 16 MHz clock for the tdc7201.
try:
    si5351 = adafruit_si5351.SI5351(i2c)	# may throw ValueError
    print('Si5351: Device found.')
    # Only needs to be initialized once, so may as well do it here.
    # Generate 16 MHz clock by 25 MHz x 16 / 25.
    print('Si5351: Input clock assumed to be 25 MHz.')
    # Configure multiplier (to PLL A).
    si5351.pll_a.configure_integer(16)
    print('Si5351: PLL A multiplier set to 16.')
    print('Si5351: PLL A set to {0} MHz'.format(si5351.pll_a.frequency / 1000000))
    # Configure divider (from PLL A).
    si5351.clock_1.configure_integer(si5351.pll_a, 25)
    print('Si5351: Clock 1 set to divide PLL A by 25.')
    print('Si5351: Clock 1 set to {0} MHz'.format(si5351.clock_1.frequency / 1000000))
    # Turn outputs on.
    si5351.outputs_enabled = True
    print('Si5351: Clock outputs enabled')
except ValueError:
    print('Si5351: ERROR: Device not found.')
    si5351 = None

# ads1115 4-channel 16-bit ADC, i2c address 0x48
# Used to monitor supply voltages
try:
    ads1115 = ADS.ADS1115(i2c)	# may throw ValueError
    print('ads1115: Device found.')
    #ads1115.mode = Mode.SINGLE	# in Adafruit code, but doesn't work
    ads1115.gain = 1
    voltage5v0 = AnalogIn(ads1115, ADS.P0)	# RPi 5V rail
    voltage3v7 = AnalogIn(ads1115, ADS.P1)	# lithium battery 3.7V
    voltage3v3 = AnalogIn(ads1115, ADS.P2)	# RPi 3.3V rail
except ValueError:
    print('ads1115: ERROR: Device not found.')
    ads1115 = None

# MQTT stuff.
#MQTT_SERVER_NAME = "mqtt.eclipse.org"
MQTT_SERVER_NAME = "test.mosquitto.org"

def on_connect(mqtt_client, userdata, flags, result_code):
    """MQTT callback for when the client receives a CONNACK response from the server."""
    print("Connected to", MQTT_SERVER_NAME, "with result code", result_code)
    # Any subscribes should go here, so they get re-subscribed on a reconnect.

def on_disconnect(mqtt_client, userdata, rc):
    print("MQTT disconnected with code", rc, ". Attempting to reconnect.")
    try:
        mqttc.reconnect()
    except socket.error:
        print("Reconnect failed, exiting.")
        sys.exit(0)

mqttc = mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_disconnect = on_disconnect
mqttc.connect(MQTT_SERVER_NAME, 1883, 300)

def publish_uname():
    """Publish uname() data to the MQTT server."""
    # What hardware are we running on?
    uname = os.uname()
    nodename = uname.nodename
    machine = uname.machine
    sysname = uname.sysname
    release = uname.release
    version = uname.version
    mqttc.publish(topic="QTD/VDDG/"+nodename+"/nodename",
                   payload=nodename, retain=True)
    mqttc.publish(topic="QTD/VDDG/"+nodename+"/machine",
                   payload=machine, retain=True)
    mqttc.publish(topic="QTD/VDDG/"+nodename+"/OS",
                   payload=sysname+" "+release+" "+version, retain=True)

cpu_temp = None
def publish_cpu_temp(f_name="/sys/class/thermal/thermal_zone0/temp"):
    """Publish the CPU temperature to the MQTT server."""
    global cpu_temp
    try:
        with open(f_name) as cpu_temp_file:
            temp_line = list(cpu_temp_file)[0]
    except IOError:
        print("Couldn't open", cpu_temp_file)
    else:
        # Smooth
        new_temp = int(temp_line)
        if cpu_temp is None:
            cpu_temp = new_temp
            #print("New temp =", cpu_temp/1000)
        else:
            cpu_temp = (3*cpu_temp + new_temp) / 4
            #print("Averaged temp =", cpu_temp/1000)
        rounded = round(cpu_temp/1000, 1)
        #print("CPU temp =", rounded)
    mqttc.publish(topic="QTD/VDGG/CPU/cpu_temp", payload=rounded)

def publish_gpu_temp(cmd="vcgencmd measure_temp"):
    """Publish the GPU temperature to the MQTT server."""
    try:
        with os.popen(cmd) as pipe:
            gpu_temp = pipe.read()[5:9]
    except IOError:
        print("Running", cmd, "failed.")
        gpu_temp = "Failed"
    else:
        #print("GPU temp =", gpu_temp)
        pass
    mqttc.publish(topic="QTD/VDGG/CPU/gpu_temp", payload=gpu_temp)

def publish_os_name():
    """Publish the OS name to the MQTT server."""
    # Get "pretty" OS name
    try:
        fname = '/etc/os-release'
        with open(fname) as f:
            os_name = f.read().split('"')[1] + ' '
    except IOError:
        print("Couldn't open", fname)
        os_name = 'unknown '
    # Get exact version-date.
    try:
        fname = "/etc/rpi-issue"
        with open(fname) as f:
            os_name += f.read().split()[3]
    except IOError:
        print("Couldn't open", fname)
        os_name += "XXXX-XX-XX"
    #print("OS name =", os_name)
    mqttc.publish(topic="QTD/VDDG/CPU/os_name", payload=os_name, retain=True)

def publish_cpu_info(f_name="/proc/cpuinfo"):
    """Publish the Raspberry Pi type name to the MQTT server."""
    try:
        with open(f_name) as cpu_info_file:
            hw_list = list(cpu_info_file)[-4:]
    except IOError:
        print("Couldn't open", cpu_info_file)
    else:
        for line in hw_list:
            #print(line, end='')
            hw_pair = line.split()
            if len(hw_pair) >= 2:
                topic = "QTD/VDDG/CPU/"+hw_pair[0]
                #print(topic)
                mqttc.publish(topic=topic, payload=" ".join(hw_pair[2:]), retain=True)

def publish_disk_space(fs="/",name="root"):
    """Publish filesystem fullness to the MQTT server."""
    cmd="df " + fs
    size = None
    used = None
    try:
        with os.popen(cmd) as pipe:
            words = list(pipe)[1].split()
            size = words[1]
            used = words[2]
            full_pct = round((int(used)/int(size))*100.0,3)
            #print("Disk", fs, full_pct, "percent full")
    except IOError:
        print("Running", cmd, "failed.")
    #except ValueError:
        #pass
    mqttc.publish(topic="QTD/VDGG/CPU/"+name, payload=str(full_pct))

def publish_load_avg(cmd="uptime"):
    """Publish the load average to the MQTT server."""
    try:
        with os.popen(cmd) as pipe:
            load = pipe.read().split(':')[-1].split(',')[0]
    except IOError:
        print("Running", cmd, "failed.")
        load = "Failed"
    else:
        #print("Load average =", load)
        pass
    mqttc.publish(topic="QTD/VDGG/CPU/load", payload=load)

def publish_voltages():
    if ads1115 is None:
        #print("No ads1115 found.")
        return None
    try:
        v = voltage5v0.voltage	# May throw OSError if i2c bus problem.
        mqttc.publish(topic="QTD/VDGG/CPU/5v0", payload='{:.5f}'.format(v))
    except OSError:
        # Measurement failed due to bus error?
        print("5v0 measurement failed due to OSError.")
    try:
        v = voltage3v7.voltage	# May throw OSError if i2c bus problem.
        mqttc.publish(topic="QTD/VDGG/CPU/3v7", payload='{:.5f}'.format(v))
    except OSError:
        # Measurement failed due to bus error?
        print("3v7 measurement failed due to OSError.")
    try:
        v = voltage3v3.voltage	# May throw OSError if i2c bus problem.
        mqttc.publish(topic="QTD/VDGG/CPU/3v3", payload='{:.5f}'.format(v))
    except OSError:
        # Measurement failed due to bus error?
        print("3v3 measurement failed due to OSError.")

publish_uname()
publish_os_name()
publish_cpu_info()

while True:
    mqttc.loop()
    publish_cpu_temp()
    publish_load_avg()
    publish_disk_space()
    publish_disk_space(fs="/mnt/qtd", name="data")
    publish_voltages()
    time.sleep(60)

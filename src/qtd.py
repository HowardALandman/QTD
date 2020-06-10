#!/usr/bin/python3
"""Run the (real or simulated) QTD experiment on a SPI-attached TDC7201 chip."""

import time
import os
import signal
import sys
import json
import paho.mqtt.client as mqtt
import tdc7201


# Handle ^C keyboard interrupt.
def sigint_handler(sig, frame):
    """Exit as gracefully as possible."""
    payload = "unknown"
    print('')
    try:
        tdc.cleanup()
        payload = "OFF"
        #print("Turned TDC7201 off while exiting.")
    except NameError:
        pass
    mqttc.publish(topic="QTD/VDDG/tdc7201/runstate", payload=payload)
    sys.exit(0)

signal.signal(signal.SIGINT, sigint_handler)


# MQTT stuff.
MQTT_SERVER_NAME = "mqtt.eclipse.org"

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

def publish_tdc7201_driver():
    """Publish the version number of the TDC7201 driver to the MQTT server."""
    try:
        # the fast easy way
        driver = tdc7201.__version__	# exists in versions 0.6b1 and later
    except AttributeError:
        # This is grotesquely slow, but should work with any version
        command = "python3 -m pip show tdc7201 | grep Version"
        try:
            with os.popen(command) as pipe:
                driver = pipe.read().split()[1]
        except IOError:
            driver = "unknown"
    print("TDC7201 driver version =", driver)
    mqttc.publish(topic="QTD/VDGG/tdc7201/driver", payload=driver)

tdc = tdc7201.TDC7201()	# Create TDC object with SPI interface.

# Set RPi pin directions and default values for non-SPI signals.
# These should stay the same for entire run.
# This also puts the chip into reset ("off") state.
tdc.initGPIO(trig2=None, int2=None)

# Setting and checking clock speed.
tdc.set_SPI_clock_speed(22500000)	# 22.5 MHz
#tdc.set_SPI_clock_speed(tdc._maxSPIspeed // 2)

# Internal timing
#print("UNIX time settings:")
#print("Epoch (time == 0):", time.asctime(time.gmtime(0)))
NOW = time.time()
#print("Time since epoch in seconds:", NOW)
#print("Current time (UTC):", time.asctime(time.gmtime(NOW)))
print("Current time (local):", time.asctime(time.localtime(NOW)), time.strftime("%Z"))
#print("Time since reset asserted:", NOW - reset_start)
publish_tdc7201_driver()	# Takes a few seconds.
#time.sleep(0.1)	# ensure a reasonable reset time
#print("Time since reset asserted:", NOW - reset_start)

# Turn the chip on.
tdc.on(meas_mode=2, num_stop=3, clock_cntr_stop=1, timeout=0.0005)
#tdc.on(meas_mode=1, num_stop=2, clock_cntr_stop=1, timeout=0.0005)
mqttc.publish(topic="QTD/VDDG/tdc7201/runstate", payload="ON")

# Make sure our internal copy of the register state is up to date.
#print("Reading chip side #1 register state:")
tdc.read_regs()
#tdc.print_regs1()

batches = -1	# number of batches, negative means run forever
#ITERS = 32768 # measurements per batch
ITERS = 16384 # measurements per batch
#ITERS = 8192 # measurements per batch
mqttc.publish(topic="QTD/VDDG/tdc7201/batchsize", payload=str(ITERS))
#RESULT_NAME = ("0", "1", "2", "3", "4", "5",
#               "No calibration", "INT1 fall timeout", "TRIG1 fall timeout",
#               "INT1 early", "TRIG1 rise timeout", "START_MEAS active",
#               "TRIG1 active", "INT1 active")
cum_results = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

while batches != 0:
    print("batches =", batches)
    mqttc.loop()
    #resultDict = {}
    # Measure average time per measurement.
    THEN = time.time()
    result_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for m in range(ITERS):
        result_list[tdc.measure(simulate=True)] += 1
        # Clear interrupt register bits to prepare for next measurement.
        tdc.clear_status()
    for i in range(len(result_list)):
        cum_results[i] += result_list[i]
    PAYLOAD = json.dumps(result_list)
    print(PAYLOAD)
    mqttc.publish(topic="QTD/VDDG/tdc7201/batch", payload=PAYLOAD)
    print(cum_results)
    NOW = time.time()
    DURATION = NOW - THEN
    #print(ITERS, "measurements in", DURATION, "seconds")
    print((ITERS/DURATION), "measurements per second")
    #print((result_list[2]/DURATION), "valid measurements per second")
    #print((DURATION/ITERS), "seconds per measurement")

    batches -= 1

# Turn the chip off.
tdc.off()
mqttc.publish(topic="QTD/VDDG/tdc7201/runstate", payload="OFF")

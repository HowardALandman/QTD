#!/usr/bin/python3
"""Run the (real or simulated) QTD experiment on a SPI-attached TDC7201 chip."""

import time
import os
import resource
import signal
import sys
import socket	# just for exception handling
import json
import paho.mqtt.client as mqtt
import tdc7201


# Handle ^C keyboard interrupt.
def sigint_handler(sig, frame):
    """Exit as gracefully as possible."""
    print('\nCaught SIGINT')
    payload = "SIGINT - interrupted (probably by keyboard ^C)"
    try:
        tdc.cleanup()
    except NameError:
        pass
    else:
        payload = "OFF"
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
    """MQTT callback for when the client is disconnected from the server."""
    print("MQTT disconnected with code", rc, ". Attempting to reconnect.")
    try:
        mqttc.reconnect()
    except socket.error:
        print("Reconnect failed, exiting.")
        sys.exit(0)

mqttc = mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_disconnect = on_disconnect
try:
    mqttc.connect(MQTT_SERVER_NAME, 1883, 600)
except socket.gaierror:
    print("ERROR: getaddrinfo() failed. Couldn't connect to MQTT server", MQTT_SERVER_NAME+".")
    print("MQTT status logging will not work!!!")

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
# Pin assignments should stay the same for entire run.
# This also puts the chip into reset ("off") state.
tdc.initGPIO(trig2=None, int2=None, stop=None)

# Setting and checking clock speed.
tdc.set_SPI_clock_speed(25000000)	# 25 MHz is spec max

# Internal timing
now = time.time()
print("Current time (UTC):", time.asctime(time.gmtime(now)))
print("Current time (local):", time.asctime(time.localtime(now)), time.strftime("%Z"))
publish_tdc7201_driver()

# Turn the chip on and configure it.
tdc.on()
NUM_STOP = 3	# We check against this later.
tdc.configure(side=1, meas_mode=2, num_stop=NUM_STOP, clock_cntr_stop=1, timeout=0.000165, calibration2_periods=40)
mqttc.publish(topic="QTD/VDDG/tdc7201/runstate", payload="ON")

# Make sure our internal copy of the register state is up to date.
#print("Reading chip side #1 register state:")
tdc.read_regs()
#tdc.print_regs1()

batches = -1	# number of batches, negative means run forever
ITERS = 100000 # measurements per batch
mqttc.publish(topic="QTD/VDDG/tdc7201/batchsize", payload=str(ITERS))
#RESULT_NAME = ("0", "1", "2", "3", "4", "5",
#               "No calibration", "INT1 fall timeout", "TRIG1 fall timeout",
#               "INT1 early", "TRIG1 rise timeout", "START_MEAS active",
#               "TRIG1 active", "INT1 active")
cum_results = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
result_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

now = time.time()
while batches != 0:
    print("batches =", batches)
    mqttc.loop()
    # Measure average time per measurement.
    then = now
    timestamp = time.strftime("%Y%m%d%H%M%S")
    #print(timestamp)
    data_fname = '/mnt/qtd/data/' + timestamp + ".txt"
    try:
        data_file = open(data_fname,'w')
    except (IOError, OSError):
        print("Couldn't open", data_fname, "for writing.")
        tdc.cleanup()
        sys.exit()
    data_file.write("QTD experiment data file\n")
    data_file.write("Time : " + str(then) + "\n")
    data_file.write("Date : " + timestamp + "\n")
    data_file.write("Batch : " + str(abs(batches)) + "\n")	# NOT CORRECT for batches > 0 !
    data_file.write("Batch_size : " + str(ITERS) + "\n")
    data_file.write("Config : " + str(tdc.reg1[0:12]) + "\n")
    #result_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    for m in range(ITERS):
        m_str = str(m) + ' '
        result = tdc.measure(simulate=True, error_prefix=m_str, log_file=data_file)
        result_list[result] += 1
        if result==2:
            # Record results in microseconds
            decay = 1000000 * (tdc.tof2 - tdc.tof1)
            # Record raw register data, so we can analyze differently later if needed,
            # as well as the computed delay between STOP1 and STOP2.
            tof_line = m_str + str(tdc.reg1[0x10:0x1C]) + ' ' + str(decay) + '\n'
            data_file.write(tof_line)
        elif result > NUM_STOP and result <= 5:
            print("ERROR: Too Many Pulses:", result, str(tdc.reg1[0x10:0x1D]))
    data_file.write('Tot : ' + str(result_list) + "\n")
    PAYLOAD = json.dumps(result_list)
    print(PAYLOAD)
    mqttc.publish(topic="QTD/VDDG/tdc7201/batch", payload=PAYLOAD)
    now = time.time()
    DURATION = now - then
    #print(ITERS, "measurements in", DURATION, "seconds")
    #print((ITERS/DURATION), "measurements per second")
    #print((DURATION/ITERS), "seconds per measurement")
    pulse_pair_rate = result_list[2] / DURATION
    # MQTT "payload" = entire message, but
    # node-red "payload" = field inside message.
    # It's confusing.
    mqttc.publish(topic="QTD/VDDG/tdc7201/p2ps", payload=pulse_pair_rate)
    for i in range(len(result_list)):
        cum_results[i] += result_list[i]
        result_list[i] = 0
    data_file.write('Cum : ' + str(cum_results) + "\n")
    data_file.close()
    print(cum_results)
    #print('Memory usage: %s (kb)' % resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    print(pulse_pair_rate, "valid measurements per second")

    batches -= 1

# Turn the chip off.
tdc.off()
mqttc.publish(topic="QTD/VDDG/tdc7201/runstate", payload="OFF")

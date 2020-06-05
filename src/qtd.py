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
#def publish_cpu_temp(f_name="/sys/class/thermal/thermal_zone0/temp", __temp=None):
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
    mqttc.publish(topic="QTD/VDGG/qtd-0w/cpu_temp", payload=rounded)

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
    mqttc.publish(topic="QTD/VDGG/qtd-0w/gpu_temp", payload=gpu_temp)

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
    print("OS name =", os_name)
    mqttc.publish(topic="QTD/VDDG/qtd-0w/os_name", payload=os_name, retain=True)

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
            topic = "QTD/VDDG/qtd-0w/"+hw_pair[0]
            #print(topic)
            mqttc.publish(topic=topic, payload=" ".join(hw_pair[2:]), retain=True)

publish_uname()
publish_os_name()
publish_cpu_info()

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
#iters = 32768 # measurements per batch
#iters = 16384 # measurements per batch
ITERS = 8192 # measurements per batch
mqttc.publish(topic="QTD/VDDG/tdc7201/batchsize", payload=str(ITERS))
#RESULT_NAME = ("0", "1", "2", "3", "4", "5",
#               "No calibration", "INT1 fall timeout", "TRIG1 fall timeout",
#               "INT1 early", "TRIG1 rise timeout", "START_MEAS active",
#               "TRIG1 active", "INT1 active")
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
    #for i in range(len(result_list)):
    #    resultDict[RESULT_NAME[i]] = result_list[i]
    PAYLOAD = json.dumps(result_list)
    print(PAYLOAD)
    mqttc.publish(topic="QTD/VDDG/tdc7201/batch", payload=PAYLOAD)
    NOW = time.time()
    DURATION = NOW - THEN
    #print(ITERS, "measurements in", DURATION, "seconds")
    print((ITERS/DURATION), "measurements per second")
    #print((DURATION/ITERS), "seconds per measurement")

    publish_cpu_temp()

    batches -= 1

# Turn the chip off.
tdc.off()
mqttc.publish(topic="QTD/VDDG/tdc7201/runstate", payload="OFF")

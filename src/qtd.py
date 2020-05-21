#!/usr/bin/python3

import time
# sys for exit()
import sys
import os
import tdc7201
import paho.mqtt.client as mqtt
import json

mqtt_server_name = "mqtt.eclipse.org"

# MQTT callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    #print("Connected with result code "+str(rc))
    print("Connected to", mqtt_server_name, "with result code", rc)

client = mqtt.Client()
client.on_connect = on_connect
client.connect(mqtt_server_name, 1883, 60)

def publish_tdc7201_driver():
    command = "python3 -m pip show tdc7201 | grep Version"
    try:
        driver = os.popen(command).read().split()[1]
    except:
        driver = "unknown"
    print("TDC7201 driver version =",driver)
    client.publish(topic="QTD/VDGG/tdc7201/driver",payload=driver)

cpu_temp_filename = "/sys/class/thermal/thermal_zone0/temp"
gpu_temp_command = "vcgencmd measure_temp"
temp = None

# What hardware are we running on?
uname = os.uname()
nodename = uname.nodename
machine = uname.machine
sysname = uname.sysname
release = uname.release
version = uname.version
client.publish(topic="QTD/VDDG/"+nodename+"/nodename",payload=nodename,retain=True)
client.publish(topic="QTD/VDDG/"+nodename+"/machine",payload=machine,retain=True)
client.publish(topic="QTD/VDDG/"+nodename+"/OS",payload=sysname+" "+release+" "+version,retain=True)
# Get "pretty" OS name
try:
    os_name = os.popen("head -1 /etc/os-release").read()
    print("OS name =",os_name)
    os_name = os_name.split('"')[1]
    print("OS name =",os_name)
    client.publish(topic="QTD/VDDG/"+nodename+"/os_name",payload=os_name,retain=True)
except:
    pass
cpuinfo_filename = "/proc/cpuinfo"
try:
    cpuinfo = open(cpuinfo_filename)
except:
    print("Couldn't open",cpuinfo_filename)
else:
    hw = list(cpuinfo)[-4:]
    for line in hw:
        #print(line,end='')
        hw_pair = line.split()
        topic = "QTD/VDDG/"+nodename+"/"+hw_pair[0]
        print(topic)
        client.publish(topic=topic,payload=" ".join(hw_pair[2:]),retain=True)

tdc = tdc7201.TDC7201()	# Create TDC object with SPI interface.

# Set RPi pin directions and default values for non-SPI signals.
# These should stay the same for entire run.
# This also puts the chip into reset ("off") state.
tdc.initGPIO(trig2=None,int2=None)

# Setting and checking clock speed.
tdc.set_SPI_clock_speed(tdc._maxSPIspeed)
#tdc.set_SPI_clock_speed(tdc._maxSPIspeed // 2)

# Internal timing
#print("UNIX time settings:")
#print("Epoch (time == 0):", time.asctime(time.gmtime(0)))
now = time.time()
#print("Time since epoch in seconds:", now)
#print("Current time (UTC):", time.asctime(time.gmtime(now)))
print("Current time (local):", time.asctime(time.localtime(now)), time.strftime("%Z"))
#print("Time since reset asserted:", now - reset_start)
publish_tdc7201_driver()	# Takes a few seconds.
#time.sleep(0.1)	# ensure a reasonable reset time
#print("Time since reset asserted:", now - reset_start)

# Turn the chip on.
tdc.on(meas_mode=2,num_stop=5,clock_cntr_stop=1,timeout=0.0005)
#tdc.on(meas_mode=1,num_stop=2,clock_cntr_stop=1,timeout=0.0005)
client.publish(topic="QTD/VDDG/tdc7201/runstate",payload="ON")

# Make sure our internal copy of the register state is up to date.
#print("Reading chip side #1 register state:")
tdc.read_regs()
#tdc.print_regs1()

batches = -1	# number of batches, negative means run forever
#iters = 32768 # measurements per batch
#iters = 16384 # measurements per batch
iters = 8192 # measurements per batch
client.publish(topic="QTD/VDDG/tdc7201/batchsize",payload=str(iters))
result_name = ("0","1","2","3","4","5","No calibration","INT1 fall timeout","TRIG1 fall timeout","INT1 early","TRIG1 rise timeout","START_MEAS active","TRIG1 active","INT1 active")
while batches != 0:
    print("batches =",batches)
    client.loop()
    resultDict = {}
    # Measure average time per measurement.
    then = time.time()
    resultList = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    for m in range(iters):
        resultList[tdc.measure(simulate=True)] += 1
        # Clear interrupt register bits to prepare for next measurement.
        tdc.clear_status()
    #for i in range(len(resultList)):
    #    resultDict[result_name[i]] = resultList[i]
    #payload = json.dumps(resultDict)
    payload = json.dumps(resultList)
    print(payload)
    client.publish(topic="QTD/VDDG/tdc7201/batch",payload=payload)
    now = time.time()
    duration = now - then
    #print(iters,"measurements in",duration,"seconds")
    print((iters/duration),"measurements per second")
    #print((duration/iters),"seconds per measurement")

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
    client.publish(topic="QTD/VDGG/qtd-0W/cpu_temp",payload=rounded)

    try:
        gpu_temp = (os.popen(gpu_temp_command).read())[5:9]
    except:
        print("Running",gpu_temp_command,"failed.")
        gpu_temp = "Failed"
    else:
        #print("GPU temp =",gpu_temp)
        pass
    client.publish(topic="QTD/VDGG/qtd-0W/gpu_temp",payload=gpu_temp)

    batches -= 1

# Turn the chip off.
tdc.off()
client.publish(topic="QTD/VDDG/tdc7201/runstate",payload="OFF")

#!/usr/bin/python3

#import RPi.GPIO as GPIO
# Needs to be 0.5.1 or later for interrupts to work.
# This code was written and tested on 0.6.3.
# print("GPIO version =", GPIO.VERSION)
#import spidev
import time
# sys for exit()
import sys
# random for creating stimuli for testing
import random
import tdc7201

# Execute if called as a program (and not if imported as a library)
if __name__ == "__main__":
    tdc = tdc7201.TDC7201()	# Create TDC object with SPI interface.
    tdc.initGPIO()	# Set pin directions and default values for non-SPI signals.

    # Setting and checking clock speed.
    tdc.set_SPI_clock_speed(25000000)
    #print("")

    # Internal timing
    #print("UNIX time settings:")
    #print("Epoch (time == 0):", time.asctime(time.gmtime(0)))
    now = time.time()
    #print("Time since epoch in seconds:", now)
    #print("Current time (UTC):", time.asctime(time.gmtime(now)))
    print("Current time (local):", time.asctime(time.localtime(now)), time.strftime("%Z"))
    #print("Time since reset asserted:", now - reset_start)
    time.sleep(0.1)	# ensure a reasonable reset time
    #print("Time since reset asserted:", now - reset_start)

    # Turn the chip on.
    tdc.on()

    # Make sure our internal copy of the register state is up to date.
    #print("Reading chip side #1 register state:")
    tdc.read_regs1()
    #tdc.print_regs1()

    # Measure average time per measurement.
    iters = 1000
    then = time.time()
    resultList = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    for m in range(iters):
        resultList[tdc.measure(simulate=True)] += 1
        # Clear interrupt register bits to prepare for next measurement.
        tdc.clear_status()
    print(resultList)
    now = time.time()
    duration = now - then
    print(iters,"measurements in",duration,"seconds")
    print((iters/duration),"measurements per second")
    print((duration/iters),"seconds per measurement")
    # Read it back to make sure.
    #tdc.read_regs1()
    #tdc.print_regs1()

    # Turn the chip off.
    tdc.off()

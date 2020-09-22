#!/usr/bin/python3

""" Create simulated muon decay pulses for qtd.py to consume.
"""

import random
import RPi.GPIO as GPIO

__version__ = '0.0'

GPIO.setmode(GPIO.BOARD)        # Use header pin numbers, not GPIO numbers.
GPIO.setwarnings(False)

# These must not conflict with the pins used by qtd.py.
START = 18	# GPIO 24 = header pin 18
STOP = 22	# GPIO 25 = header pin 22
TRIG = 7	# GPIO  4 = header pin  7
# Don't handle falling-edge for now, just assume rising-edge.
GPIO.setup(START, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(STOP, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(TRIG, GPIO.IN)

n_stop = 3
upper_limit = 1 << 32
assert upper_limit > 1 << n_stop*2
while(True):
    GPIO.wait_for_edge(TRIG, GPIO.RISING)
    GPIO.output(START, GPIO.HIGH)
    GPIO.output(START, GPIO.LOW)
    # Send 0 to NSTOP pulses.
    # Spread them out a little ... density 1/16 => expected number 2
    r = random.randrange(upper_limit) & random.randrange(upper_limit)
    r &= random.randrange(upper_limit) & random.randrange(upper_limit)
    # ... and make sure each pulse is at least 2 ticks wide.
    r |= r << 1
    # Note that this DOES NOT ensure it will stay low for at least 2 ticks.
    while r > 0:
        GPIO.output(STOP, r & 1)
        r >>= 1
    GPIO.output(STOP, 0)

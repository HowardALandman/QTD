#!/usr/bin/python

# Support for the Texas Instruments tdc7201 time-to-digital converter chip.
# Web page: http://www.ti.com/product/tdc7201
#
# This code assumes that you are working with the TDC7201-ZAX-EVM
# evaluation board. For the most part, things won't change for the raw chip,
# Differences will be noted where appropriate.
#
# This code requires SPI to talk to the chip and set control registers and
# read result registers. SPI must be turned on at the kernel level.
# You can do this in Preferences -> Raspberry Pi Configuration -> Interfaces;
# it will require a reboot. If it is on, there should be an uncommented line
# like "dtparam=spi=on" in /boot/config.txt.
# Written and tested on a Raspberry Pi 3.

import RPi.GPIO as GPIO
import spidev
import time

# Needs to be 0.5.1 or later for interrupts to work.
# This code was written and tested on 0.6.3.
# print "GPIO version =", GPIO.VERSION

# Map of EVM board header pinout.
# "." means No Connect, parentheses mean probably unused.
#      +3.3V  1	 21 .		 (DTG_TRIG) 40	20 GND
#     ENABLE  2  22 GND		(MSP_START) 39	19 TRIG1
#          .  3  23 .		        CS2 38 	18 CS1
#          .  4  24 .		      TRIG2 37	17 .
# OSC_ENABLE  5  25 .		          . 36	16 .
#          .  6  26 .		          . 35	15 DIN
#       SCLK  7  27 .		     (SCLK) 34	14 DOUT1
#          .  8  28 .		          . 33	13 INT1
#      DOUT2  9  29 .		          . 32	12 INT2
#      (DIN) 10  30 .		          . 31	11 .

# +3.3V and *both* GND pins need to be hardwired,
# and SPI signals need to be handled by spidev,
# but everything else has to be assigned to a GPIO pin.
# The assignments are arbitrary but must match hardware wiring.
# Here we use only GPIO with no "alternate function",
ENABLE = 12	# GPIO 18 = header pin 12 (arbitrary)
OSC_ENABLE = 16	# GPIO 23 = header pin 16 (arbitrary)
# Don't need DOUT2 if only using side #1, but assign for completenes.
# It can be shorted to DOUT1, but lets make that a jumper
# since the EVM brings it out separately.
#DOUT2 = 18	# GPIO  24 = header pin 18 (arbitrary)
# We could set up both sides of the chip, but for now only side #1.
# TRIG1 and INT1 only need to be set if you are using the #1 side of chip.
TRIG1 = 7	# GPIO  4 = header pin  7  (arbitrary)
INT1 = 37	# GPIO 26 = header pin 37 (arbitrary)
# GPIO 27 = header pin 13 (arbitrary)
# TRIG2 and INT2 only need to be set if you are using the #2 side of chip.
TRIG2 = 11	# GPIO 17 = header pin 11 (arbitrary)
INT2 = 32	# GPIO 12 = header pin 32 (arbitrary)
# SPI pins must NOT be set using GPIO lib.
SCLK = 23	# GPIO 11 = header pin 23 is hardwired for SPI0 SCLK
CS1 = 24	# GPIO  8 = header pin 24 is hardwired for SPI0 CS0
CS2 = 26	# GPIO  7 = header pin 26 is hardwired for SPI0 CS1
MOSI = 19	# DIN	# GPIO 10 = header pin 19 is hardwired for SPI0 MOSI
MISO = 21	# DOUT1	# GPIO  9 = header pin 21 is hardwired for SPI0 MISO
## NOTE that chip CS1 and CS2 are wired to Pi3 CS0 and CS1 respectively!
## Don't get confused and think that Pi3 CS1 drives chip CS1! It doesn't!
# DOUT2 = MISO2 can be shorted to DOUT1 = MISO1, as long as
# CS1 and CS2 are *NEVER* both asserted low at the same time.

# TDC bit masks
TDC_AI = 0x80		# 0b10000000
TDC_WRITE = 0x40	# 0b01000000
TDC_ADDRESS = 0x3F	# 0b00111111
# TDC7201 register addresses - 8-bit
TDCx_CONFIG1			= 0x00
TDCx_CONFIG2			= 0x01
TDCx_INT_STATUS			= 0x02
TDCx_INT_MASK			= 0x03
TDCx_COARSE_CNTR_OVF_H		= 0x04
TDCx_COARSE_CNTR_OVF_L		= 0x05
TDCx_CLOCK_CNTR_OVF_H		= 0x06
TDCx_CLOCK_CNTR_OVF_L		= 0x07
TDCx_CLOCK_CNTR_STOP_MASK_H	= 0x08
TDCx_CLOCK_CNTR_STOP_MASK_L	= 0x09
# TDC7201 register addresses - 24-bit
TDCx_TIME1			= 0x10
TDCx_CLOCK_COUNT1		= 0x11
TDCx_TIME2			= 0x12
TDCx_CLOCK_COUNT2		= 0x13
TDCx_TIME3			= 0x14
TDCx_CLOCK_COUNT3		= 0x15
TDCx_TIME4			= 0x16
TDCx_CLOCK_COUNT4		= 0x17
TDCx_TIME5			= 0x18
TDCx_CLOCK_COUNT5		= 0x19
TDCx_TIME6			= 0x1A
TDCx_CALIBRATION1		= 0x1B
TDCx_CALIBRATION2		= 0x1C
# Note that side #1 and #2 of the chip EACH have a full set of registers!
# Which one you are talking to depends on the chip select!
# Within spidev, you need to close one side and then open the other to switch.



# Call this at the very beginning to intialize the chip	
def init():
    GPIO.setmode(GPIO.BOARD)	# Use header pin numbers, not GPIO numbers.
    GPIO.setwarnings(False)

    print "Initializing tdc7201."

    # Initialize the ENABLE pin to low, which resets the tdc7201.
    GPIO.setup(ENABLE,GPIO.OUT,initial=GPIO.LOW)
    # We need to hold reset for a bit, so remember when we started.
    reset_start = time.time()
    print "tdc7201 reset asserted (ENABLE = low) on pin", ENABLE, "."

    # Both chip selects must start out HIGH (inactive)
    # Not sure we can do that through GPIO lib though.
    # For intial tests, disable side 2.
    #GPIO.setup(CS1,GPIO.OUT,initial=GPIO.HIGH)
    # Permanently (?) turn off SPI on side #2.
    #GPIO.setup(CS2,GPIO.OUT,initial=GPIO.HIGH)

    # Start the on-board clock generator running.
    # May not be necessary if you supply an external clock.
    GPIO.setup(OSC_ENABLE,GPIO.OUT,initial=GPIO.HIGH)
    print "TDC7201-ZAX-EVM clock started (OSC_ENABLE = high) on pin", OSC_ENABLE, "."

    # At the moment we don't use TRIG1 on the RPi.
    # It can be used to trigger other hardware.
    #GPIO.setup(TRIG1,GPIO.IN)

    # Set up INT1 pin for interrupt-driven reads from tdc7201.
    GPIO.setup(INT1,GPIO.IN)
    print "Set INT1 to input on pin", INT1, "."

    # much later ...
    spi = spidev.SpiDev()	# create SPI object
    spi.open(0,0)		# open SPI port 0, RPi CS0 = chip CS1
    print "SPI interface started to tdc7201 side 1."

    # Check all SPI settings.
    print "Default SPI settings:"
    print "SPI bits per word (should be 8):", spi.bits_per_word
    print "SPI chip select high? (should be False):", spi.cshigh
    print "SPI loopback? (should be False):", spi.loop
    print "SPI LSB-first? (should be False):", spi.lsbfirst
    print "SPI default clock speed:", spi.max_speed_hz
    print "SPI mode (CPOL|CPHA):", spi.mode
    print "SPI threewire? (should be False):", spi.threewire

    # Setting and checking clock speed.
    # 25 MHz is max for the chip, but probably Rpi can't set that exactly.
    # Will probably end up at 15.6 MHz.
    # But for early bringup, go with slower default speed.
    print "Setting SPI clock speed to 16 MHz."
    spi.max_speed_hz = 16000000	# 25 MHz is top SPI speed for chip.
    #print "Setting SPI clock speed to 25 MHz."
    #spi.max_speed_hz = 25000000	# 25 MHz is top SPI speed for chip.
    #print "SPI clock speed:", spi.max_speed_hz
    print ""

    # Internal timing
    print "UNIX time settings:"
    #print "Epoch (time == 0):", time.asctime(time.gmtime(0))
    now = time.time()
    print "Time since epoch in seconds:", now
    print "Current time (UTC):", time.asctime(time.gmtime(now))
    print "Current time (local):", time.asctime(time.localtime(now)), time.strftime("%Z")
    #print "Time since reset asserted:", now - reset_start
    time.sleep(0.1)	# ensure a reasonable reset time
    #print "Time since reset asserted:", now - reset_start

    # Turn the chip on.
    GPIO.output(ENABLE,GPIO.HIGH)
    now = time.time()
    print "tdc7201 enabled at", now
    time.sleep(0.1)	# Wait 100 mS for chip to settle and calibrate
    			# Data sheet says only 1.5 mS required.
			# SPI available sooner, but we're not in a hurry.

    # For now, try reading the entire register state just to make sure we can.
    # This should really be a loop.
    # Note that for xfer2 to actually see the register value,
    # we need to send an extra byte at the end (hence the ",0x00")
    # and ignore an initial zero byte returned (hence "result[1]").
    print "Reading chip side #1 register state:"
    result = spi.xfer2([TDCx_CONFIG1,0x00])
    print "TDC1_CONFIG1                (default 0x00):", result[1]
    result = spi.xfer2([TDCx_CONFIG2,0x00])
    print "TDC1_CONFIG2                (default 0x40):", result[1]
    result = spi.xfer2([TDCx_INT_STATUS,0x00])
    print "TDC1_INT_STATUS             (default 0x00):", result[1]
    result = spi.xfer2([TDCx_INT_MASK,0x00])
    print "TDC1_INT_MASK               (default 0x07):", result[1]
    result = spi.xfer2([TDCx_COARSE_CNTR_OVF_H,0x00])
    print "TDC1_COARSE_CNTR_OVF_H      (default 0xFF):", result[1]
    result = spi.xfer2([TDCx_COARSE_CNTR_OVF_L,0x00])
    print "TDC1_COARSE_CNTR_OVF_L      (default 0xFF):", result[1]
    result = spi.xfer2([TDCx_CLOCK_CNTR_OVF_H,0x00])
    print "TDC1_CLOCK_CNTR_OVF_H       (default 0xFF):", result[1]
    result = spi.xfer2([TDCx_CLOCK_CNTR_OVF_L,0x00])
    print "TDC1_CLOCK_CNTR_OVF_L       (default 0xFF):", result[1]
    result = spi.xfer2([TDCx_CLOCK_CNTR_STOP_MASK_H,0x00])
    print "TDC1_CLOCK_CNTR_STOP_MASK_H (default 0x00):", result[1]
    result = spi.xfer2([TDCx_CLOCK_CNTR_STOP_MASK_L,0x00])
    print "TDC1_CLOCK_CNTR_STOP_MASK_L (default 0x00):", result[1]

    # Then try setting all the right modes, and reading state again
    # to make sure it all happened.
    # Set measurement mode 2.
    print "Setting measurement mode 2."
    result = spi.xfer2([TDCx_CONFIG1 | TDC_WRITE, 0x02])
    # Read it back to make sure.
    result = spi.xfer2([TDCx_CONFIG1,0x00])
    print "TDC1_CONFIG1                (default 0x00):", result[1]
    # Change calibration periods from 2 to 40, and two stops.
    print "Setting 40-clock-period calibration and 2 stop pulses."
    result = spi.xfer2([TDCx_CONFIG2 | TDC_WRITE,0xC1])
    # Read it back to make sure.
    result = spi.xfer2([TDCx_CONFIG2,0x00])
    print "TDC1_CONFIG2                (default 0x40):", result[1]

    # To start measurement, need to set START_MEAS in TDCx_CONFIG1 register.
    #time.sleep(10)
    spi.close()
    # Turn the chip off.
    GPIO.output(ENABLE,GPIO.LOW)

init()

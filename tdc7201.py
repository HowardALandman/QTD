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
# Needs to be 0.5.1 or later for interrupts to work.
# This code was written and tested on 0.6.3.
# print "GPIO version =", GPIO.VERSION
import spidev
import time


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


# Try defining a class for the chip as a subclass of SpiDev
class TDC7201(spidev.SpiDev):
    REGNAME = [	"CONFIG1",			# 0x00
		"CONFIG2",			# 0x01
		"INT_STATUS",			# 0x02
		"INT_MASK",			# 0x03
		"COARSE_CNTR_OVF_H",		# 0x04
		"COARSE_CNTR_OVF_L",		# 0x05
		"CLOCK_CNTR_OVF_H",		# 0x06
		"CLOCK_CNTR_OVF_L",		# 0x07
		"CLOCK_CNTR_STOP_MASK_H",	# 0x08
		"CLOCK_CNTR_STOP_MASK_L",	# 0x09
		"",				# 0x0A
		"",				# 0x0B
		"",				# 0x0C
		"",				# 0x0D
		"",				# 0x0E
		"",				# 0x0F
		"TIME1",			# 0x10
		"CLOCK_COUNT1",			# 0x11
		"TIME2",			# 0x12
		"CLOCK_COUNT2",			# 0x13
		"TIME3",			# 0x14
		"CLOCK_COUNT3",			# 0x15
		"TIME4",			# 0x16
		"CLOCK_COUNT4",			# 0x17
		"TIME5",			# 0x18
		"CLOCK_COUNT5",			# 0x19
		"TIME6",			# 0x1A
		"CALIBRATION1",			# 0x1B
		"CALIBRATION2"			# 0x1C
	      ]

    # PIN DEFINITIONS
    # +3.3V and *both* GND pins need to be hardwired,
    # and SPI signals need to be handled by spidev,
    # but everything else has to be assigned to a GPIO pin.
    # The assignments are arbitrary but must match hardware wiring.
    # Here we use only GPIO with no "alternate function",
    # for maximum flexibility.
    #
    # ENABLE high turns chip on, ENABLE low forces complete reset.
    ENABLE = 12	# GPIO 18 = header pin 12 (arbitrary)
    #
    # OSC_ENABLE turns on the EVM's clock generator chip.
    # It is a board function, not a chip function.
    # You don't need it if you are supplying an external clock.
    OSC_ENABLE = 16	# GPIO 23 = header pin 16 (arbitrary)
    #
    # The TRIGx signal indicates that the converter is ready to start.
    # Typically you would either use it to directly trigger some hardware,
    # or wait for it in your processor before starting a measurement.
    # We assume the latter here, so assign a pin to it.
    # Note that measurement does not start until converter gets the START signal.
    # The INTx signal indicates that measurement has stopped.
    # This can be because of success, or timeout; you need to read INT_STATUS
    # to determine which.
    # TRIG1 and INT1 only need to be set if you are using the #1 side of chip.
    TRIG1 = 7	# GPIO  4 = header pin  7  (arbitrary)
    INT1 = 37	# GPIO 26 = header pin 37 (arbitrary)
    # TRIG2 and INT2 only need to be set if you are using the #2 side of chip.
    TRIG2 = 11	# GPIO 17 = header pin 11 (arbitrary)
    INT2 = 32	# GPIO 12 = header pin 32 (arbitrary)
    #
    # SPI pins are owned by spidev and must NOT be set using GPIO lib.
    SCLK = 23	# GPIO 11 = header pin 23 is hardwired for SPI0 SCLK
    CS1 = 24	# GPIO  8 = header pin 24 is hardwired for SPI0 CS0
    CS2 = 26	# GPIO  7 = header pin 26 is hardwired for SPI0 CS1
    MOSI = 19	# DIN	# GPIO 10 = header pin 19 is hardwired for SPI0 MOSI
    MISO = 21	# DOUT1	# GPIO  9 = header pin 21 is hardwired for SPI0 MISO
    # NOTE that chip CS1 and CS2 are wired to Pi3 CS0 and CS1 respectively!
    # Don't get confused and think that Pi3 CS1 drives chip CS1! It doesn't!
    # DOUT2 = MISO2 can be shorted to DOUT1 = MISO1, as long as
    # CS1 and CS2 are *NEVER* both asserted low at the same time
    # but I'm not sure what spidev does about that, so leave it separate.
    # The EVM brings it out separately.
    # Note that we CANNOT read side #2 of the chip in this configuration.
    # Don't need DOUT2 if only using side #1, but assign for completenes.
    #DOUT2 = 18	# GPIO  24 = header pin 18 (arbitrary)
 
    # TDC bit masks
    AI = 0x80		# 0b10000000
    WRITE = 0x40	# 0b01000000
    ADDRESS = 0x3F	# 0b00111111
    # TDC7201 register addresses - 8-bit
    # These can be read or written.
    CONFIG1			= 0x00
    CONFIG2			= 0x01
    INT_STATUS			= 0x02
    INT_MASK			= 0x03
    COARSE_CNTR_OVF_H		= 0x04
    COARSE_CNTR_OVF_L		= 0x05
    CLOCK_CNTR_OVF_H		= 0x06
    CLOCK_CNTR_OVF_L		= 0x07
    CLOCK_CNTR_STOP_MASK_H	= 0x08
    CLOCK_CNTR_STOP_MASK_L	= 0x09
    # TDC7201 register addresses - 24-bit
    # These can be read but usually should not be written,
    # as they contain results of measurement or calibration.
    TIME1			= 0x10
    CLOCK_COUNT1		= 0x11
    TIME2			= 0x12
    CLOCK_COUNT2		= 0x13
    TIME3			= 0x14
    CLOCK_COUNT3		= 0x15
    TIME4			= 0x16
    CLOCK_COUNT4		= 0x17
    TIME5			= 0x18
    CLOCK_COUNT5		= 0x19
    TIME6			= 0x1A
    CALIBRATION1		= 0x1B
    CALIBRATION2		= 0x1C
    # Note that side #1 and #2 of the chip EACH have a full set of registers!
    # Which one you are talking to depends on the chip select!
    # Within spidev, you need to close one side and then open the other to switch.


    def __init__(self):
    	spidev.SpiDev.__init__(self)


    def setGPIO(self):
	GPIO.setmode(GPIO.BOARD)	# Use header pin numbers, not GPIO numbers.
	GPIO.setwarnings(False) 
	print "Initializing Paspberry Pi pin directions for tdc7201 driver."

	# Initialize the ENABLE pin to low, which resets the tdc7201.
	GPIO.setup(self.ENABLE,GPIO.OUT,initial=GPIO.LOW)
	# We need to hold reset for a bit, so remember when we started.
	reset_start = time.time()
	print "Reset asserted (ENABLE = low) on pin", self.ENABLE, "."

	# Both chip selects must start out HIGH (inactive).
	# Not sure we can do that through GPIO lib though.
	# For intial tests, disable side 2.
	#GPIO.setup(self.CS1,GPIO.OUT,initial=GPIO.HIGH)
	# Permanently (?) turn off SPI on side #2.
	#GPIO.setup(self.CS2,GPIO.OUT,initial=GPIO.HIGH)

	# Start the on-board clock generator running.
	# May not be necessary if you supply an external clock.
	GPIO.setup(self.OSC_ENABLE,GPIO.OUT,initial=GPIO.HIGH)
	print "Clock started (OSC_ENABLE = high) on pin", self.OSC_ENABLE, "."

	# Set up TRIG1 pin to know when chip is ready to measure.
	GPIO.setup(self.TRIG1,GPIO.IN)
	print "Set TRIG1 to input on pin", self.TRIG1, "."
	# Set up INT1 pin for interrupt-driven reads from tdc7201.
	GPIO.setup(self.INT1,GPIO.IN)
	print "Set INT1 to input on pin", self.INT1, "."

	# We're not using side #2 of the chip so far, but we wired these.
	# Set up TRIG2 pin to know when chip is ready to measure.
	GPIO.setup(self.TRIG2,GPIO.IN)
	print "Set TRIG2 to input on pin", self.TRIG2, "."
	# Set up INT2 pin for interrupt-driven reads from tdc7201.
	GPIO.setup(self.INT2,GPIO.IN)
	print "Set INT2 to input on pin", self.INT2, "."


# much later ...
#tdc = tdc7201.TDC7201()
tdc = TDC7201()	# Create TDC object with SPI interface.
tdc.setGPIO()	# Set pin directions and default values for non-SPI signals.
tdc.open(0,0)	# Open SPI port 0, RPi CS0 = chip CS1.
print "SPI interface started to tdc7201 side 1."

# Check all SPI settings.
print "Default SPI settings:"
print "SPI bits per word (should be 8):", tdc.bits_per_word
print "SPI chip select high? (should be False):", tdc.cshigh
print "SPI loopback? (should be False):", tdc.loop
print "SPI LSB-first? (should be False):", tdc.lsbfirst
print "SPI default clock speed:", tdc.max_speed_hz
print "SPI mode (CPOL|CPHA):", tdc.mode
print "SPI threewire? (should be False):", tdc.threewire

# Setting and checking clock speed.
# 25 MHz is max for the chip, but probably Rpi can't set that exactly.
# Will probably end up at 15.6 MHz.
print "Setting SPI clock speed to 16 MHz."
tdc.max_speed_hz = 16000000	# 25 MHz is top SPI speed for chip.
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
GPIO.output(tdc.ENABLE,GPIO.HIGH)
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
for r in range(tdc.CONFIG1,tdc.CLOCK_CNTR_STOP_MASK_L):
    result = tdc.xfer2([r,0x00])
    print tdc.REGNAME[r], ":", result[1]
#result = tdc.xfer2([TDCx_CONFIG1,0x00])
#print "TDC1_CONFIG1                (default 0x00):", result[1]
#result = tdc.xfer2([TDCx_CONFIG2,0x00])
#print "TDC1_CONFIG2                (default 0x40):", result[1]
#result = tdc.xfer2([TDCx_INT_STATUS,0x00])
#print "TDC1_INT_STATUS             (default 0x00):", result[1]
#result = tdc.xfer2([TDCx_INT_MASK,0x00])
#print "TDC1_INT_MASK               (default 0x07):", result[1]
#result = tdc.xfer2([TDCx_COARSE_CNTR_OVF_H,0x00])
#print "TDC1_COARSE_CNTR_OVF_H      (default 0xFF):", result[1]
#result = tdc.xfer2([TDCx_COARSE_CNTR_OVF_L,0x00])
#print "TDC1_COARSE_CNTR_OVF_L      (default 0xFF):", result[1]
#result = tdc.xfer2([TDCx_CLOCK_CNTR_OVF_H,0x00])
#print "TDC1_CLOCK_CNTR_OVF_H       (default 0xFF):", result[1]
#result = tdc.xfer2([TDCx_CLOCK_CNTR_OVF_L,0x00])
#print "TDC1_CLOCK_CNTR_OVF_L       (default 0xFF):", result[1]
#result = tdc.xfer2([TDCx_CLOCK_CNTR_STOP_MASK_H,0x00])
#print "TDC1_CLOCK_CNTR_STOP_MASK_H (default 0x00):", result[1]
#result = tdc.xfer2([TDCx_CLOCK_CNTR_STOP_MASK_L,0x00])
#print "TDC1_CLOCK_CNTR_STOP_MASK_L (default 0x00):", result[1]

# Then try setting all the right modes, and reading state again
# to make sure it all happened.
# Set measurement mode 2.
print "Setting measurement mode 2."
result = tdc.xfer2([tdc.CONFIG1 | tdc.WRITE, 0x02])
# Read it back to make sure.
result = tdc.xfer2([tdc.CONFIG1,0x00])
#print "TDC1_CONFIG1                (default 0x00):", result[1]
print tdc.REGNAME[tdc.CONFIG1], ":", result[1]
# Change calibration periods from 2 to 40, and two stops.
print "Setting 40-clock-period calibration and 2 stop pulses."
result = tdc.xfer2([tdc.CONFIG2|tdc.WRITE, 0xC1])
# Read it back to make sure.
result = tdc.xfer2([tdc.CONFIG2,0x00])
#print "TDC1_CONFIG2                (default 0x40):", result[1]
print tdc.REGNAME[tdc.CONFIG2], ":", result[1]

# Try reading a 24-bit register that might be non-zero.
print "Checking calibration registers."
result = tdc.xfer2([tdc.CALIBRATION1,0x00,0x00,0x00])
print "TDC1_CALIBRATION1       (default 0x000000):", result
result = tdc.xfer2([tdc.CALIBRATION2,0x00,0x00,0x00])
print "TDC1_CALIBRATION2       (default 0x000000):", result

# To start measurement, need to set START_MEAS in TDCx_CONFIG1 register.

#time.sleep(10)
# Close SPI.
tdc.close()
# Turn the chip off.
GPIO.output(tdc.ENABLE,GPIO.LOW)


#!/usr/bin/python3

""" Driver for the Texas Instruments tdc7201 time-to-digital converter chip.
    Web page: http://www.ti.com/product/tdc7201

    This code assumes that you are working with the TDC7201-ZAX-EVM
    evaluation board. For the most part, things won't change for the raw chip,

    This code requires SPI to talk to the chip and set control registers
    and read result registers. SPI must be turned on at the kernel level.
    You can do this in Preferences -> Raspberry Pi Configuration ->
    Interfaces in the GUI, or using raspi-config from the command line;
    it will require a reboot. If it is on, there should be an uncommented
    line like "dtparam=spi=on" in /boot/config.txt.

    Written and tested on a Raspberry Pi 3B+ and Raspberry Pi Zero W,
    but should work on any model with a 2x20 pin header..
"""
# pylint: disable=E1101

import time
# sys for exit()
import sys
# random for creating stimuli for testing
import random
import RPi.GPIO as GPIO
# Needs to be 0.5.1 or later for interrupts to work.
# This code was written and tested on 0.6.3.
# print("RPi.GPIO version =", GPIO.VERSION)
import spidev

__version__ = '0.8b7'

# Map of EVM board header pinout.
# "." means No Connect, parentheses mean probably optional.
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


class TDC7201():
    """Interface to a Texas Instruments tdc7201 time-to-digital converter chip."""
    # Chip registers and a few combinations of registers
    REGNAME = ("CONFIG1",			# 0x00
               "CONFIG2",			# 0x01
               "INT_STATUS",			# 0x02
               "INT_MASK",			# 0x03
               "COARSE_CNTR_OVF_H",		# 0x04
               "COARSE_CNTR_OVF_L",		# 0x05
               "CLOCK_CNTR_OVF_H",		# 0x06
               "CLOCK_CNTR_OVF_L",		# 0x07
               "CLOCK_CNTR_STOP_MASK_H",	# 0x08
               "CLOCK_CNTR_STOP_MASK_L",	# 0x09
               "COARSE_CNTR_OVF",		# 0x0A (combination)
               "CLOCK_CNTR_OVF",		# 0x0B (combination)
               "CLOCK_CNTR_STOP_MASK",		# 0x0C (combination)
               "",				# 0x0D
               "",				# 0x0E
               "",				# 0x0F
               "TIME1",				# 0x10
               "CLOCK_COUNT1",			# 0x11
               "TIME2",				# 0x12
               "CLOCK_COUNT2",			# 0x13
               "TIME3",				# 0x14
               "CLOCK_COUNT3",			# 0x15
               "TIME4",				# 0x16
               "CLOCK_COUNT4",			# 0x17
               "TIME5",				# 0x18
               "CLOCK_COUNT5",			# 0x19
               "TIME6",				# 0x1A
               "CALIBRATION1",			# 0x1B
               "CALIBRATION2"			# 0x1C
              )

    # TDC register address bit masks
    _AI = 0x80		# 0b10000000	# bit mask
    _WRITE = 0x40	# 0b01000000	# bit mask
    _ADDRESS = 0x3F	# 0b00111111	# bit mask
    #
    # TDC7201 register addresses - 8-bit
    # These can be read or written.
    CONFIG1 = 0x00
    CONFIG2 = 0x01
    INT_STATUS = 0x02
    INT_MASK = 0x03
    COARSE_CNTR_OVF_H = 0x04
    COARSE_CNTR_OVF_L = 0x05
    CLOCK_CNTR_OVF_H = 0x06
    CLOCK_CNTR_OVF_L = 0x07
    CLOCK_CNTR_STOP_MASK_H = 0x08
    CLOCK_CNTR_STOP_MASK_L = 0x09
    MINREG8 = 0x00
    MAXREG8 = 0x09
    #REG8RANGE = range(MINREG8,MAXREG8+1)
    # Not actual chip registers, but 16-bit pairs of 8
    COARSE_CNTR_OVF = 0x0A
    CLOCK_CNTR_OVF = 0x0B
    CLOCK_CNTR_STOP_MASK = 0x0C
    #
    # CONFIG1 register bit masks
    # Calibrate after every measurement, even if interrupted?
    _CF1_FORCE_CAL = 0b10000000
    # Add a parity bit (even parity) for 24-bit registers?
    _CF1_PARITY_EN = 0b01000000
    # Invert TRIGG signals (falling edge instead of rising edge)?
    _CF1_TRIGG_EDGE = 0b00100000
    # Inverted STOP signals (falling edge instead of rising edge)?
    _CF1_STOP_EDGE = 0b00010000
    # Inverted START signals (falling edge instead of rising edge)?
    _CF1_START_EDGE = 0b00001000
    # Neasurememnt mode 1 or 2? (Other values reserved.)
    _CF1_MEAS_MODE = 0b00000110	# bit mask
    _CF1_MM1 = 0b00000000
    _CF1_MM2 = 0b00000010
    # Start new measurement
    # Automagically starts a measurement.
    # Is automagically cleared when a measurement is complete.
    # DO NOT poll this to see when a measurement is done!
    # Use the INT1 (or INT2) signal instead.
    _CF1_START_MEAS = 0b00000001
    #
    # CONFIG2 register bit masks
    # Number of calibration periods
    _CF2_CALIBRATION_PERIODS = 0b11000000	# bit mask
    _CF2_CAL_PERS_2 = 0b00000000
    _CF2_CAL_PERS_10 = 0b01000000	# default on reset
    _CF2_CAL_PERS_20 = 0b10000000
    _CF2_CAL_PERS_40 = 0b11000000
    # Number of cycles to average over
    _CF2_AVG_CYCLES = 0b00111000	# bit mask
    _CF2_AVG_CYC_1 = 0b00000000	# no averaging, default
    _CF2_AVG_CYC_2 = 0b00001000
    _CF2_AVG_CYC_4 = 0b00010000
    _CF2_AVG_CYC_8 = 0b00011000
    _CF2_AVG_CYC_16 = 0b00100000
    _CF2_AVG_CYC_32 = 0b00101000
    _CF2_AVG_CYC_64 = 0b00110000
    _CF2_AVG_CYC_128 = 0b00111000
    # Number of stop pulses to wait for.
    _CF2_NUM_STOP = 0b00000111	# bit mask
    _CF2_NSTOP_1 = 0b00000000	# default on reset
    _CF2_NSTOP_2 = 0b00000001
    _CF2_NSTOP_3 = 0b00000010
    _CF2_NSTOP_4 = 0b00000011
    _CF2_NSTOP_5 = 0b00000100
    #
    # INT_STATUS register bit masks
    # Upper 3 bits are reserved.
    # Writing a 1 to any of the other bits should clear their status.
    # Did the measurement complete?
    _IS_COMPLETE = 0b00010000
    # Has the measurement started?
    _IS_STARTED = 0b00001000
    # Did the clock overflow?
    _IS_CLOCK_OVF = 0b00000100
    # Did the coarse counter overflow?
    _IS_COARSE_OVF = 0b00000010
    # Was an interrupt generated?
    # May be identical information to _IS_COMPLETE.
    _IS_INTERRUPT = 0b00000001
    #
    # INT_MASK register bit masks
    # Upper 5 bits are reserved.
    # Is the clock counter overflow enabled?
    _IM_CLOCK_OVF = 0b00000100
    # Is the coarse counter overflow enabled?
    _IM_COARSE_OVF = 0b00000010
    # Is the measurement complete interrupt enabled?
    _IM_MEASUREMENT = 0b00000001
    #
    # TDC7201 register addresses - 24-bit
    # These can be read but usually should not be written,
    # as they contain results of measurement or calibration.
    TIME1 = 0x10
    CLOCK_COUNT1 = 0x11
    TIME2 = 0x12
    CLOCK_COUNT2 = 0x13
    TIME3 = 0x14
    CLOCK_COUNT3 = 0x15
    TIME4 = 0x16
    CLOCK_COUNT4 = 0x17
    TIME5 = 0x18
    CLOCK_COUNT5 = 0x19
    TIME6 = 0x1A
    CALIBRATION1 = 0x1B
    CALIBRATION2 = 0x1C
    MINREG24 = 0x10
    MAXREG24 = 0x1C
    #REG24RANGE = range(MINREG24,MAXREG24+1)
    #REGRANGE = range(0,MAXREG24+1)
    # Note that side #1 and #2 of the chip EACH have a full set of registers!
    # Which one you are talking to depends on the chip select!
    # Within spidev, you need to close one side and then open the other to switch.

    # TDC7201 clock, for calculating actual TOFs
    clockFrequency = 8000000		# usually 8 MHz, though 16 is better
    clockPeriod = 1.0 / clockFrequency	# usually 125 nS

    _minSPIspeed = 50000
    _maxSPIspeed = 25000000


    def __init__(self):
        # Instance variables
        self._spi = spidev.SpiDev()
        self.reg1 = [None for i in range(self.MAXREG24+1)]
        #self.reg2 = [None for i in range(self.MAXREG24+1)]
        # Open SPI to side 1 of the chip
        # Later we should write routines.
        try:
            self._spi.open(0, 0)	# Open SPI port 0, RPi CS0 = chip CS1.
        except FileNotFoundError:
            print("Unable to open SPI device. Is SPI enabled?")
            print("You can use 'lsmod | grep spi' to check if any SPI kernel modules are loaded.")
            print("If not, turn SPI on using raspi-config -> Interfacing Options -> SPI")
            print("or Menu -> Preferences -> Raspberry Pi Configuration -> Interfaces.")
            print("You will then need to reboot.")
            raise RuntimeError("SPI not available")
        self.chip_select = 1
        #print("SPI interface started to tdc7201 side 1.")
        # Check all SPI settings.
        #print("Default SPI settings:")
        #print("SPI bits per word (should be 8):", self._spi.bits_per_word)
        if self._spi.bits_per_word != 8:
            print("Setting bits per word to 8")
            self._spi.bits_per_word = 8
        #print("SPI chip select high? (should be False):", self._spi.cshigh)
        if self._spi.cshigh:
            print("Setting chip selects to active low")
            self._spi.cshigh = False
        #print("SPI loopback? (should be False):", self._spi.loop)
        if self._spi.loop:
            print("Setting loopback to False")
            self._spi.loop = False
        #print("SPI LSB-first? (should be False):", self._spi.lsbfirst)
        if self._spi.lsbfirst:
            print("Setting bit order to MSB-first")
            self._spi.lsbfirst = False
        #print("SPI default clock speed:", self._spi.max_speed_hz)
        #print("SPI mode (CPOL|CPHA) (should be 0b00):", self._spi.mode)
        if self._spi.mode != 0:
            print("Setting polarity and phase to normal")
            self._spi.mode = 0
        #print("SPI threewire? (should be False):", self._spi.threewire)
        if self._spi.threewire:
            print("Setting 3-wire to False")
            self._spi.threewire = False

    def initGPIO(self,
                 enable=12,	# GPIO 18 = header pin 12
                 osc_enable=16,	# GPIO 23 = header pin 16
                 trig1=7,	# GPIO  4 = header pin  7
                 int1=37,	# GPIO 26 = header pin 37
                 trig2=11,	# GPIO 17 = header pin 11
                 int2=32,	# GPIO 12 = header pin 32
                 start=18,	# GPIO 24 = header pin 18
                 stop=22,	# GPIO 25 = header pin 22
                 verbose=False
                ):
        """Initialize all the non-SPI GPIO pins.

           +3.3V and *both* GND pins need to be hardwired, and SPI
           signals need to be handled by spidev, but all other used
           signals must be assigned to a GPIO pin.
           The assignments are arbitrary but must match hardware wiring.
           The defaults use only GPIO with no "alternate function",
           for maximum flexibility.

           SPI pins are owned by spidev and must NOT be set using GPIO lib.
           NOTE that chip CS1 and CS2 are wired to Pi CE0 and CE1 respectively!
           Don't get confused and think that Pi CE1 drives chip CS1! It doesn't!
           DOUT2 = MISO2 can be shorted to DOUT1 = MISO1, as long as
           CS1 and CS2 are *NEVER* both asserted low at the same time
           but I'm not sure what spidev does about that, so leave it separate.
           The EVM brings it out separately.
           Note that we CANNOT read side #2 of the chip in this configuration.
           Don't need DOUT2 if only using side #1, but assign for completenes.

           ENABLE high turns chip on, ENABLE low forces complete reset.

           OSC_ENABLE high turns on the EVM's clock generator chip (marked Y1).
           It is a board function, not a chip function.
           If OSC_ENABLE is low,
           then you must supply an external clock, connected to the board's
           EXT_CLOCK pin.
           (I think. I haven't tested this.)

           The TRIGx signal indicates that the converter is ready to start.
           Typically you would either use it to directly trigger some hardware,
           or wait for it in your processor before sending out your own trigger.
           We assume the latter here, so assign a pin to it.
           Note that measurement does not start until converter gets the START signal.

           The INTx signal going low indicates that measurement has stopped.
           This can be because of success, or timeout; you need to read INT_STATUS
           to determine which.

           TRIG1 and INT1 only need to be set if you are using the #1 side of chip.
           TRIG2 and INT2 only need to be set if you are using the #2 side of chip.

           The START signal may be supplied externally to each side,
           separately through START_EXT1 and START_EXT2 SMA connectors,
           or together through the COMMON_START SMA connector.
           If you want to drive one of these from the RPi, then the
           MSP_START signal needs to be wired up to TP10, a PCB mount SMA connector
           needs to be soldered into the EVM board at TP10, you need to put
           a cable from TP10 to one of the START SMA connectors mentioned above,
           and the GPIO needs to be declared.

           The STOP signals on the EVM board come in through SMA connectors,
           and therefore do not have pins on the header.
           The STOP pin is only used for simulating data.
           If you want to use that feature, then the STOP output pin on the RPi
           needs to be wired to an SMA conector,
           and that connector cabled to the appropriate SMA connector on the EVM.

           Unused signals may be set to None to save a pin.
        """
        GPIO.setmode(GPIO.BOARD)	# Use header pin numbers, not GPIO numbers.
        GPIO.setwarnings(False)
        #print("Initializing Raspberry Pi pin directions for tdc7201 driver.")
        print("Initializing tdc7201 driver.")

        # Keep track of which pins we've already used.
        pin_used = [None for pin in range(41)]

        def reserve_pin(name, number):
            if number is None:
                return
            if pin_used[number] is None:
                pin_used[number] = name
            else:
                print("ERROR: Can't reserve pin", number, "for", name,
                      ": pin already used for", pin_used[number])
                raise RuntimeError("GPIO pin conflict")

        # SPI pins MUST be reserved for spidev use.
        # GPIO 11 = header pin 23 is hardwired for SPI0 SCLK
        self.sclk = 23
        reserve_pin("SCLK", 23)
        # GPIO  9 = header pin 21 is hardwired for SPI0 MISO
        self.miso = 21	# DOUT1
        reserve_pin("MISO", 21)
        # GPIO 10 = header pin 19 is hardwired for SPI0 MOSI
        self.mosi = 19	# DIN
        reserve_pin("MOSI", 19)
        # GPIO  8 = header pin 24 is hardwired for SPI0 CS0
        self.cs1 = 24
        reserve_pin("CS1", 24)
        # GPIO  7 = header pin 26 is hardwired for SPI0 CS1
        self.cs2 = 26
        reserve_pin("CS2", 26)
        # Need more stuff here for side 2 of the chip to work.
        #DOUT2 = 15
        # GPIO  22 = header pin 15 (arbitrary)
        if verbose:
            print("Reserved SPI pins (SCLK=", self.sclk, ",MISO=", self.miso, ",MOSI=", self.mosi,
                  ",CS1(= Pi ce0)=", self.cs1, ",CS2(= Pi ce1)=", self.cs2, ")", sep='')
        # Initialize the ENABLE pin to low, which resets the tdc7201.
        self.enable = enable # remember it
        if enable is not None:
            reserve_pin("ENABLE", enable)
            GPIO.setup(enable, GPIO.OUT, initial=GPIO.LOW)
            if verbose:
                print("Set ENABLE to output on pin", enable)
                print("Reset asserted (ENABLE = low) on pin", enable)
        else:
             print("WARNING: ENABLE is not assigned. Driver will not be able to reset the chip.")

        # Both chip selects must start out HIGH (inactive).
        # Not sure we can do that through GPIO lib though.
        # For intial tests, disable side 2.
        #GPIO.setup(self.cs1, GPIO.OUT, initial=GPIO.HIGH)
        # Permanently (?) turn off SPI on side #2.
        #GPIO.setup(self.cs2, GPIO.OUT, initial=GPIO.HIGH)

        # Start the on-board clock generator running.
        # May not be necessary if you supply an external clock.
        self.osc_enable = osc_enable # remember it
        if osc_enable is not None:
            reserve_pin("OSC_ENABLE", osc_enable)
            GPIO.setup(osc_enable, GPIO.OUT, initial=GPIO.HIGH)
            if verbose:
                print("Set OSC_ENABLE to output on pin", osc_enable)
                print("Clock started (OSC_ENABLE = high) on pin", osc_enable)
        else:
            print("WARNING: OSC_ENABLE pin is not assigned. You must drive it elsewhere.")

        # Set up TRIG1 pin to know when chip is ready to measure.
        self.trig1 = trig1 # remember it
        if trig1 is not None:
            reserve_pin("TRIG1", trig1)
            GPIO.setup(trig1, GPIO.IN)
            if verbose:
                print("Set TRIG1 to input on pin", trig1)
        else:
            print("WARNING: TRIG1 pin is not assigned. Cannot guarantee that side #1 of the chip will be ready before START arrives.")

        # Set up INT1 pin for interrupt-driven reads from tdc7201.
        reserve_pin("INT1", int1)
        self.int1 = int1 # remember it
        if int1 is not None:
            GPIO.setup(int1, GPIO.IN)
            if verbose:
                print("Set INT1 to input on pin", int1)
        else:
            print("WARNING: INT1 pin is not assigned. Cannot measure using side #1 of the chip.")

        # We're not using side #2 of the chip so far, but we wired these.

        # Set up TRIG2 pin to know when chip is ready to measure.
        self.trig2 = trig2 # remember it
        reserve_pin("TRIG2", trig2)
        if trig2 is not None:
            GPIO.setup(trig2, GPIO.IN)
            if verbose:
                print("Set TRIG2 to input on pin", trig2)
        else:
            print("WARNING: TRIG2 pin is not assigned. Cannot guarantee that side #2 of the chip will be ready before START arrives.")

        # Set up INT2 pin for interrupt-driven reads from tdc7201.
        self.int2 = int2 # remember it
        if int2 is not None:
            reserve_pin("INT2", int2)
            GPIO.setup(int2, GPIO.IN)
            if verbose:
                print("Set INT2 to input on pin", int2)
        else:
            if verbose:
                print("INT2 pin is not assigned. Side 2 of the chip may not work.")

        # Set up START and STOP, initially inactive.
        self.start = start # remember it
        if start is not None:
            reserve_pin("START", start)
            GPIO.setup(start, GPIO.OUT, initial=GPIO.LOW)
            if verbose:
                print("Set START to output (low) on pin", start)
        else:
            print("WARNING: START pin is not assigned. Simulating START signals will not work.")

        self.stop = stop # remember it
        if stop is not None:
            reserve_pin("STOP", stop)
            GPIO.setup(stop, GPIO.OUT, initial=GPIO.LOW)
            if verbose:
                print("Set STOP to output (low) on pin", stop, ".")
        else:
            print("WARNING: STOP pin is not assigned. Simulating STOP signals will not work.")

    def off(self):
        """Close SPI, turn TDC7201 off, and wait for reset to take effect."""
        print("Turning off tdc7201.")
        GPIO.output(self.enable, GPIO.LOW)
        # There is no specified minimum reset time,
        # but let's wait at least a microsecond to be safe.
        time.sleep(0.000001)

    def on(self):
        """Turn TDC7201 on and wait for it to stabilize."""
        now = time.time()
        print("tdc7201 enabled at", now)
        # Turn on chip enable.
        GPIO.output(self.enable, GPIO.HIGH)
        # Wait for chip to settle.
        # SPI available in 0.1 mS.
        # LDO is mostly settled (within 0.3%) in 0.3 mS,
        # fully settled in 1.5 mS.
        # Might be better to use the time configuring.
        time.sleep(0.0015)

    def configure(self,
           side=1,	# Which side of the chip to configure
           force_cal=True,	# Only this works for now.
           meas_mode=2,
           trig_falling=False,	# HW reset default
           falling=False,	# HW reset default
           calibration2_periods=10,	# HW reset default
           avg_cycles=1,	# no averaging, HW reset default
           num_stop=1,		# HW reset default
           clock_cntr_stop=0,	# HW reset default
           clock_cntr_ovf=0xFFFF,	# HW reset default
           timeout=None,	# Alternate way to specify clock overflow
           retain_state=False,	# Use existing state, ignore other arguments
          ):
        # Configuration register 1
        if retain_state:
            cf1_state = self.reg1[self.CONFIG1]
        else:
            cf1_state = 0 # The default after power-on or reset
            if force_cal:
                cf1_state |= self._CF1_FORCE_CAL
                print("Set forced calibration.")
            if trig_falling:
                cf1_state |= self._CF1_TRIGG_EDGE
                print("Set TRIG1 to use falling edge.")
            if falling:
                cf1_state |= self._CF1_STOP_EDGE
                cf1_state |= self._CF1_START_EDGE
                print("Set START and STOP to trigger on falling edge.")
            if meas_mode == 1:
                pass
                #cf1_state |= self._CF1_MM1 # Does nothing since MM1 == 00.
                #print("Set measurement mode 1.") # default value
            elif meas_mode == 2:
                cf1_state |= self._CF1_MM2
                print("Set measurement mode 2.")
            else:
                print(meas_mode, "is not a legal measurement mode.")
                print("Defaulting to measurement mode 1.")
                cf1_state |= self._CF1_MM1
                meas_mode = 1
            self.reg1[self.CONFIG1] = cf1_state
        self.meas_mode = meas_mode
        # Write+read occasionally fails when SPI is overclocked.
        # That is, the value you read back is not what you wrote.
        # Repeat until success.
        # Should usually only take 1 attempt, although there are
        # sometimes clusters of failures immediately after on().
        self.write8(self.CONFIG1, cf1_state)
        cf1_read = self.read8(self.CONFIG1)
        if cf1_read == 0 and cf1_state != 0:
            print("Are you sure the TDC7201 is connected to the Pi's SPI interface?")
            self.exit()
        while cf1_read != cf1_state:
            print("Failed to set CONFIG1.", format(cf1_state, "08b"), "=>", format(cf1_read, "08b"))
            self.write8(self.CONFIG1, cf1_state)
            cf1_read = self.read8(self.CONFIG1)

        # Configuration register 2
        if retain_state:
            cf2_state = self.reg1[self.CONFIG2]
        else:
            cf2_state = 0 # Power-on default is 0b01_000_000
            # Always calibrate for AT LEAST as many cycles as requested.
            # Should probably warn if value is not exact ...
            if calibration2_periods <= 2:
                #cf2_state |= self._CF2_CAL_PERS_2 # No effect since equals 0.
                self.cal_pers = 2
                print("Set 2-clock-period calibration.")
            elif calibration2_periods <= 10:
                cf2_state |= self._CF2_CAL_PERS_10
                self.cal_pers = 10
                #print("Set 10-clock-period calibration.") # the hardware default
            elif calibration2_periods <= 20:
                cf2_state |= self._CF2_CAL_PERS_20
                self.cal_pers = 20
                print("Set 20-clock-period calibration.")
            else:
                cf2_state |= self._CF2_CAL_PERS_40
                self.cal_pers = 40
                print("Set 40-clock-period calibration.")
            if avg_cycles <= 1:
                pass
                #cf2_state |= self._CF2_AVG_CYC_1 # No effect since equals 0.
                #print("No averaging.") # default on reset
            elif avg_cycles <= 2:
                cf2_state |= self._CF2_AVG_CYC_2
                print("Averaging over 2 measurement cycles.")
            elif avg_cycles <= 4:
                cf2_state |= self._CF2_AVG_CYC_4
                print("Averaging over 4 measurement cycles.")
            elif avg_cycles <= 8:
                cf2_state |= self._CF2_AVG_CYC_8
                print("Averaging over 8 measurement cycles.")
            elif avg_cycles <= 16:
                cf2_state |= self._CF2_AVG_CYC_16
                print("Averaging over 16 measurement cycles.")
            elif avg_cycles <= 32:
                cf2_state |= self._CF2_AVG_CYC_32
                print("Averaging over 32 measurement cycles.")
            elif avg_cycles <= 64:
                cf2_state |= self._CF2_AVG_CYC_64
                print("Averaging over 64 measurement cycles.")
            elif avg_cycles <= 128:
                cf2_state |= self._CF2_AVG_CYC_128
                print("Averaging over 128 measurement cycles.")
            else:
                #cf2_state |= self._CF2_AVG_CYC_1 # No effect since equals 0.
                print(avg_cycles,
                      "is not a valid number of cycles to average over, defaulting to no averaging.")
            if num_stop == 1:
                pass
                #cf2_state |= self._CF2_NSTOP_1 # No effect since equals 0.
                #print("Set 1 stop pulse.") # default on reset
            elif num_stop == 2:
                cf2_state |= self._CF2_NSTOP_2
                print("Set 2 stop pulses.")
            elif num_stop == 3:
                cf2_state |= self._CF2_NSTOP_3
                print("Set 3 stop pulses.")
            elif num_stop == 4:
                cf2_state |= self._CF2_NSTOP_4
                print("Set 4 stop pulses.")
            elif num_stop == 5:
                cf2_state |= self._CF2_NSTOP_5
                print("Set 5 stop pulses.")
            else:
                # Other codes (for 6, 7, 8) are invalid and give 1.
                cf2_state |= self._CF2_NSTOP_1
                print(num_stop, "is not a valid number of stop pulses, defaulting to 1.")
            self.reg1[self.CONFIG2] = cf2_state
        # Writing occasionally fails. Repeat until success.
        # Should usually only take 1 attempt.
        self.write8(self.CONFIG2, cf2_state)
        cf2_read = self.read8(self.CONFIG2)
        while cf2_read != cf2_state:
            print("Failed to set CONFIG2.", format(cf2_state, "08b"), "=>", format(cf2_read, "08b"))
            self.write8(self.CONFIG2, cf2_state)
            cf2_read = self.read8(self.CONFIG2)

        # Interrupt mask
        if retain_state:
            im_state = self.reg1[self.INT_MASK]
        else:
            if meas_mode == 1:
                im_state = self._IM_COARSE_OVF | self._IM_MEASUREMENT
            elif meas_mode == 2:
                im_state = self._IM_CLOCK_OVF | self._IM_MEASUREMENT
            else:
                # error?
                im_state = 0
            self.reg1[self.INT_MASK] = im_state
        self.write8(self.INT_MASK, im_state)
        # Writing occasionally fails. Repeat until success.
        # Should usually only take 1 attempt.
        self.write8(self.INT_MASK, im_state)
        while self.read8(self.INT_MASK) != im_state:
            print("Failed to set INT_MASK.")
            self.write8(self.INT_MASK, im_state)

        # CLOCK_CNTR_STOP
        if retain_state:
            clock_cntr_stop = self.reg1[self.CLOCK_CNTR_STOP_MASK]
        else:
            print("Skipping STOP pulses for", clock_cntr_stop, "clock periods =",
                  clock_cntr_stop*self.clockPeriod, "S")
            self.reg1[self.CLOCK_CNTR_STOP_MASK] = clock_cntr_stop & 0xFFFF
            if self.reg1[self.CLOCK_CNTR_STOP_MASK] != clock_cntr_stop:
                print("clock_cntr_stop", clock_cntr_stop, "too large, using", self.reg1[self.CLOCK_CNTR_STOP_MASK])
            self.reg1[self.CLOCK_CNTR_STOP_MASK_H] = (clock_cntr_stop >> 8) & 0xFF
            self.reg1[self.CLOCK_CNTR_STOP_MASK_L] = clock_cntr_stop & 0xFF
        self.write16(self.CLOCK_CNTR_STOP_MASK_H, clock_cntr_stop)
        # Writing occasionally fails. Repeat until success.
        # Should usually only take 1 attempt.
        while self.read16(self.CLOCK_CNTR_STOP_MASK_H) != clock_cntr_stop:
            print("Failed to set CLOCK_CNTR_STOP_MASK.")
            self.write16(self.CLOCK_CNTR_STOP_MASK_H, clock_cntr_stop)

        # Set overflow timeout.
        if retain_state:
            ovf = self.reg1[self.CLOCK_CNTR_OVF]
            timeout = ovf * self.clockPeriod
            #print("Setting overflow timeout from retained state:", ovf, "=", timeout, "S.")
        elif timeout is None:
            ovf = clock_cntr_ovf
            timeout = clock_cntr_ovf * self.clockPeriod
            print("Setting overflow timeout from clock_cntr_ovf:", ovf, "=", timeout, "S.")
        else:
            ovf = int(timeout / self.clockPeriod)
            print("Setting overflow timeout from timeout:", ovf, "=", timeout, "S.")
        if (meas_mode == 2) and (timeout < 0.000002):
            print("WARNING: Timeout < 2000 nS and meas_mode == 2.")
            print("Maybe measurement mode 1 would be better?")
        elif (meas_mode == 1) and (timeout > 0.000002):
            print("WARNING: Timeout > 2000 nS and meas_mode == 1.")
            print("Maybe measurement mode 2 would be better?")
        if ovf <= clock_cntr_stop:
            print("WARNING: clock_cntr_ovf must be greater than clock_cntr_stop,")
            print("otherwise your measurement will stop before it starts.")
            ovf = clock_cntr_stop + 1
            print("Set clock_cntr_ovf to", hex(ovf))
        if ovf > 0xFFFF:
            print("FATAL: clock_cntr_ovf exceeds max of 0xFFFF.")
            self.exit()
        self.reg1[self.CLOCK_CNTR_OVF] = ovf
        self.reg1[self.CLOCK_CNTR_OVF_H] = (ovf >> 8) & 0xFF
        self.reg1[self.CLOCK_CNTR_OVF_L] = ovf & 0xFF
        self.write16(self.CLOCK_CNTR_OVF_H, ovf)
        # Writing occasionally fails. Repeat until success.
        # Should usually only take 1 attempt.
        while self.read16(self.CLOCK_CNTR_OVF_H) != ovf:
            print("Failed to set CLOCK_CNTR_OVF_H.")
            self.write16(self.CLOCK_CNTR_OVF_H, ovf)

    def write8(self, reg, val):
        """Write one 8-bit register."""
        #assert (reg >= self.MINREG8) and (reg <= self.MAXREG8)
        #self._spi.xfer([reg|self._WRITE, val&0xFF])
        self._spi.xfer([reg|self._WRITE, val])

    def read8(self, reg):
        """Read one 8-bit register."""
        #assert (reg >= self.MINREG8) and (reg <= self.MAXREG8)
        result = self._spi.xfer([reg, 0x00])
        return result[1]

    def write16(self, reg, val):
        """Write a 16-bit value to a pair of 8-bit registers."""
        # There are only 3 register pairs for which this makes sense.
        #assert (reg == self.COARSE_CNTR_OVF_H) or
        #       (reg == self.CLOCK_CNTR_OVF_H) or
        #       (reg == self.CLOCK_CNTR_STOP_MASK_H)
        self._spi.xfer([reg|self._WRITE|self._AI, (val>>8)&0xFF, val&0xFF])

    def read16(self, reg):
        """Read a pair of 8-bit registers and convert them to a 16-bit value."""
        # There are only 3 register pairs for which this makes sense.
        #assert (reg == self.COARSE_CNTR_OVF_H) or
        #       (reg == self.CLOCK_CNTR_OVF_H) or
        #       (reg == self.CLOCK_CNTR_STOP_MASK_H)
        result = self._spi.xfer([reg|self._AI, 0x00, 0x00])
        return (result[1] << 8) | result[2]

    def read24(self, reg):
        """Read one 24-bit register."""
        #assert (reg >= self.MINREG24) and (reg <= self.MAXREG24)
        result = self._spi.xfer([reg, 0x00, 0x00, 0x00])
        # data is MSB-first
        return (result[1] << 16) | (result[2] << 8) | result[3]

    REG8_TUPLE_WITH_PADDING = (MINREG8|_AI,
                               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00)
    def read_regs8(self):
        """Read all 8-bit registers, using auto-increment feature."""
        result8 = self._spi.xfer(self.REG8_TUPLE_WITH_PADDING)
        # First (0th) byte is always 0, rest are desired values.
        self.reg1[0:self.MAXREG8] = result8[1:]
        # 16-bit combinations
        self.reg1[self.COARSE_CNTR_OVF] = (
            (self.reg1[self.COARSE_CNTR_OVF_H] << 8) | self.reg1[self.COARSE_CNTR_OVF_L])
        self.reg1[self.CLOCK_CNTR_OVF] = (
            (self.reg1[self.CLOCK_CNTR_OVF_H] << 8) | self.reg1[self.CLOCK_CNTR_OVF_L])
        self.reg1[self.CLOCK_CNTR_STOP_MASK] = (
            (self.reg1[self.CLOCK_CNTR_STOP_MASK_H] << 8) | self.reg1[self.CLOCK_CNTR_STOP_MASK_L])

    REG24_TUPLE_WITH_PADDING = (MINREG24|_AI,
                               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                               0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00)
    def read_regs24(self):
        """Read all 24-bit chip registers, using auto-increment feature."""
        result24 = self._spi.xfer(self.REG24_TUPLE_WITH_PADDING)
        i = 1	# First (0th) byte is always 0, rest are desired values.
        for reg in range(self.MINREG24, self.MAXREG24+1):
            # Data comes in MSB first.
            self.reg1[reg] = (result24[i] << 16) | (result24[i+1] << 8) | result24[i+2]
            # Unfortunately, the built in method is MUCH slower.
            #self.reg1[reg] = int.from_bytes(result24[i:i+2],byteorder='big')
            i += 3

    def read_regs(self):
        """Read all chip registers, using auto-increment feature."""
        self.read_regs8()
        self.read_regs24()

    def read_regs1(self):
        """Deprecated, use read_regs instead."""
        print("read_regs1() is deprecated, use read_regs() instead.")
        self.read_regs()

    def print_regs1(self):
        """Print out all the (copies of the) register values."""
        for reg in range(self.MINREG8, self.MAXREG8+1):
            print(self.REGNAME[reg], hex(self.reg1[reg]))
        # Use combined registers for brevity.
        for reg in range(self.COARSE_CNTR_OVF, self.CLOCK_CNTR_STOP_MASK+1):
            print(self.REGNAME[reg], self.reg1[reg])
        for reg in range(self.MINREG24, self.MAXREG24+1):
            print(self.REGNAME[reg], self.reg1[reg])

    def tof_mm1(self, time_n):
        """Compute a Time-Of-Flight assuming measurement mode 1."""
        assert self.meas_mode == self._CF1_MM1
        # Compute time-of-flight from START to a STOP.
        if self.reg1[time_n]:
            return self.norm_lsb*self.reg1[time_n]
        return 0

    def tof_mm2(self, time1, time_n, count, avg):
        """Compute a Time-Of-Flight assuming measurement mode 2."""
        assert self.meas_mode == self._CF1_MM2
        # Compute time-of-flight given Measurement Mode 2 data for two adjacent stops.
        if (self.reg1[time_n] or self.reg1[count]):
            return self.norm_lsb*(self.reg1[time1]-self.reg1[time_n]) + \
                   (self.reg1[count]/avg)*self.clockPeriod
        return 0

    # Check if we got any pulses and calculate the TOFs.
    def compute_tofs(self):
        """Compute all the Time-Of-Flights."""
        #print("Computing TOFs.")
        self.cal_count = ((self.reg1[self.CALIBRATION2] - self.reg1[self.CALIBRATION1])
                          / (self.cal_pers - 1))
        #print("cal_count:", self.cal_count)
        if self.cal_count == 0:
            print("No calibration, therefore can't compute timing.")
            return 6	# No calibration, therefore can't compute timing.
        self.norm_lsb = self.clockPeriod / self.cal_count
        #print("clockPeriod:", self.clockPeriod)
        #print("norm_lsb:", self.norm_lsb)
        pulses = 0
        if self.meas_mode == self._CF1_MM1:
            # According to manual, needs no adjustment for averaging.
            self.tof1 = self.tof_mm1(self.TIME1)
            #print("TOF1 =", self.tof1)
            pulses += bool(self.tof1)
            self.tof2 = self.tof_mm1(self.TIME2)
            #print("TOF2 =", self.tof2)
            pulses += bool(self.tof2)
            self.tof3 = self.tof_mm1(self.TIME3)
            pulses += bool(self.tof3)
            self.tof4 = self.tof_mm1(self.TIME4)
            pulses += bool(self.tof4)
            self.tof5 = self.tof_mm1(self.TIME5)
            pulses += bool(self.tof5)
        elif self.meas_mode == self._CF1_MM2:
            # Average cycles
            log_avg = (self.reg1[self.CONFIG2] & self._CF2_AVG_CYCLES) >> 3
            #print("log_avg =", log_avg)
            avg = 1 << log_avg
            #print("avg =", avg)
            self.tof1 = self.tof_mm2(self.TIME1, self.TIME2, self.CLOCK_COUNT1, avg)
            pulses += bool(self.tof1)
            self.tof2 = self.tof_mm2(self.TIME1, self.TIME3, self.CLOCK_COUNT2, avg)
            pulses += bool(self.tof2)
            self.tof3 = self.tof_mm2(self.TIME1, self.TIME4, self.CLOCK_COUNT3, avg)
            pulses += bool(self.tof3)
            self.tof4 = self.tof_mm2(self.TIME1, self.TIME5, self.CLOCK_COUNT4, avg)
            pulses += bool(self.tof4)
            self.tof5 = self.tof_mm2(self.TIME1, self.TIME6, self.CLOCK_COUNT5, avg)
            pulses += bool(self.tof5)
        else:
            print("Illegal measurement mode", self.meas_mode)
        log_line = "P " + str(pulses)
        if pulses >= 2:
            log_line += " " + str(self.tof2 - self.tof1)
            if pulses >= 3:
                log_line += " " + str(self.tof3 - self.tof2)
                if pulses >= 4:
                    log_line += " " + str(self.tof4 - self.tof3)
                    if pulses >= 5:
                        log_line += " " + str(self.tof5 - self.tof4)
        #if pulses >= 2:
        #    print(log_line)
        #print(pulses, "pulses detected")
        #if pulses >= 2:
        #    print("Decay time =", (self.tof2 - self.tof1))
        return pulses

    def clear_status(self, verbose=False, force=False):
        """Clear interrupt register bits to prepare for next measurement."""
        if verbose:
            print("Checking interrupt status register.")
        if force:
            # Assume all bits are set and need clearing.
            int_stat = 0b00011111
        else:
            int_stat = self.read8(self.INT_STATUS)
        if verbose:
            print("Status was", bin(int_stat))
        if int_stat:
            # Write a 1 to each set bit to clear it.
            self.write8(self.INT_STATUS, int_stat)
            int_stat = self.read8(self.INT_STATUS)
            self.reg1[self.INT_STATUS] = int_stat # Update internal copy.
            if verbose:
                print("After clearing we got", bin(int_stat))
        else:
            if verbose:
                print("No need to clear.")

    def measure(self, simulate=False, error_prefix='', log_file=None):
        """Run one measurement.
           If simulate=True, also send out fake data to measure.
           Prepend error_prefix to every error message.
           If log_file is given, write errors there, else print them.
        """
#        # Check GPIO state doesn't indicate a measurement is happening.
#        if not GPIO.input(self.int1):
#            err_str = error_prefix + "ERROR 13: INT1 already active (low)."
#            if log_file:
#                log_file.write(err_str+'\n')
#            else:
#                print(err_str)
#            # Try to fix it
#            self.clear_status()
#            return 13
        # TRIG should be low if rising-edge, high if falling-edge.
        # Don't check this is trig1 is set to None.
        if self.trig1:
            trig_falling = (self.reg1[self.CONFIG1] & self._CF1_TRIGG_EDGE) > 0
            trig_error = False
            if GPIO.input(self.trig1) and not trig_falling:
                err_str = error_prefix + "ERROR 12: TRIG1 should be low."
                trig_error = True
            elif not GPIO.input(self.trig1) and trig_falling:
                err_str = error_prefix + "ERROR 12: TRIG1 should be high."
                trig_error = True
            if trig_error:
                if log_file:
                    log_file.write(err_str+'\n')
                else:
                    print(err_str)
                # This is a very serious error that means the chip is wedged.
                # Clearing the status register does NOT fix it.
                # Only hope is to reset the chip.
                self.off()
                self.on()
                self.configure(retain_state=True)
                return 12
        # To start measurement, need to set START_MEAS in TDCx_CONFIG1 register.
        cf1_state = self.reg1[self.CONFIG1]
        # All error 11s follow an error 7 in the previous measurement.
        # If we can fix the error 7s, these should disappear too.
#        # First read current value.
#        cf1_read = self.read8(self.CONFIG1)
#        # Check it's not already set.
#        if cf1_read & self._CF1_START_MEAS:
#            err_str = error_prefix + "ERROR 11: CONFIG1 already has START_MEAS bit set."
#            if log_file:
#                log_file.write(err_str+'\n')
#            else:
#                print(err_str)
#            return 11
        timed_out = False
        #print("Starting measurement.")
        cf1_write = cf1_state | self._CF1_START_MEAS
        self.write8(self.CONFIG1, cf1_write)
#        # Double check to help debug error 7s.
#        # THIS NEVER HAPPENS (except sometimes when SPI is overclocked above 28.5 MHz).
#        cf1_read = self.read8(self.CONFIG1)
#        if cf1_read != cf1_write:
#            print("ERROR 10.5: Measurement start error:", format(cf1_write, "08b"), "=>", format(cf1_read, "08b"))
        # Wait for edge on TRIG1 (unless trig1 == None).
        if self.trig1:
            # Don't wait more than 0.5 mS.
            # THIS IS ONLY CORRECT FOR MM2!
            timeout = time.time() + 0.0005
            if trig_falling:
                #print("Somehow trig_falling got set True!")
                while (GPIO.input(self.trig1)):
                    if (time.time() > timeout):
                        timed_out = True
                        break
            else:
                while (not GPIO.input(self.trig1)):
                    if (time.time() > timeout):
                        timed_out = True
                        break
            if timed_out:
                if trig_falling:
                    err_str = error_prefix + "ERROR 10: Timed out waiting for TRIG1 to fall."
                else:
                    err_str = error_prefix + "ERROR 10: Timed out waiting for TRIG1 to rise."
                if log_file:
                    log_file.write(err_str+'\n')
                else:
                    print(err_str)
                return 10
# NEVER HAPPENS
#        # Check that INT1 is inactive (high) as expected.
#        if not GPIO.input(self.int1):
#            err_str = error_prefix + "ERROR 9: INT1 is active (low) too early!"
#            if log_file:
#                log_file.write(err_str+'\n')
#            else:
#                print(err_str)
#            # Try to fix it
#            self.clear_status()
#            return 9

        # Last chance to check registers before sending START pulse?
        #print(tdc.REGNAME[tdc.CONFIG2], ":", hex(tdc.read8(tdc.CONFIG2)))
        if simulate:
            if self.start is not None:
                # We got a trigger, so issue a START pulse.
                GPIO.output(self.start, GPIO.HIGH)
                #time.sleep(0.000000005)
                GPIO.output(self.start, GPIO.LOW)
                #print("Generated START pulse.")
            # former error 8 code:
            # We used to wait here for TRIG to return to inactive state,
            # but the chip spec doesn't specify the timing of that behavior.
            # Deleted that check. Hope it's OK.
            if self.stop is not None:
                # Send 0 to NSTOP pulses. FOR TESTING ONLY.
                n_stop = (self.reg1[self.CONFIG2] & self._CF2_NUM_STOP) + 1
                upper_limit = 1 << n_stop*2
                r = random.randrange(upper_limit)
                while r > 0:
                    GPIO.output(self.stop, r & 1)
                    r >>= 1
                GPIO.output(self.stop, 0)
#        GPIO.wait_for_edge(self.int1, GPIO.FALLING)
        # Note that the chip may already be finished by now.
        # Therefore, GPIO.wait_for_edge() is not guaranteed to see an edge.
        # Wait for INT1. This is inefficient, but OK for now.
        # INT1 is active low.
        # I tried not having a timeout here, but unfortunately,
        # about 1 in every 20 million measurements actually does hang forever.
        # Having the timeout time be fairly long does NOT significantly hurt
        # performance, since the longer INT1 timings are extremely rare.
        timeout = time.time() + (self.clockPeriod * self.reg1[self.CLOCK_CNTR_OVF]) + 0.009
        timed_out = False
        while (GPIO.input(self.int1)):
            if (time.time() > timeout):
                timed_out = True
                break
        if timed_out:
            err_str = error_prefix + "ERROR 7: Timed out waiting for INT1."
#            # Let's debug this sucker.
#            cf1_state = self.reg1[self.CONFIG1]
#            cf1_read = self.read8(self.CONFIG1)
#            print(error_prefix+"ERROR 7: INT1 timeout:", format(cf1_state, "08b"), "=>", format(cf1_read, "08b"))
            if log_file:
                log_file.write(err_str+'\n')
            else:
                print(err_str)
            return 7

        # Read everything in and see what we got.
        #print("Reading chip side #1 register state:")
        self.read_regs24()
        return_code = self.compute_tofs()
        #self.clear_status()	# clear interrupts
        return return_code # 0-5 for number of pulses (< NSTOP implies timeout),
                           # 8 is currently unassigned
                           # 6-7 and 9-13 for error,

    def set_SPI_clock_speed(self, speed, force=False):
        """Attempt to set the SPI clock speed, within chip limits."""
        # Spec max for SPI clock is 25 MHz.
        # However, this can be overclocked a little,
        # and we want to allow that for research purposes.
        # On my board, 33.4 MHz and higher fails completely.
        # 29.0 to 33.3 MHz works almost all the time,
        # but I see occasional clusters of SPI errors,
        # especially right after coming out of reset.
        # These manifest as unreliable write-read, e.g.
        # you write a single 8-bit register and read it back
        # and get something different from what you wrote.
        # The differences tend to look approximately like
        # read_value = write_value | (write_value >> 1),
        # for example you might write 01000010 and then
        # read back 01100011 or maybe 01100010. It is
        # not clear to me yet whether this corresponds
        # to write errors, read errors, or some of both;
        # I suspect some of both. I have never seen a written 1
        # turn into a read 0, or a written 00 turn into read 01.
        # Anyway, the above is why I set the limits below the way I do.

        # Force=True bypasses all the sanity checks (for testing).
        if force:
            self._spi.max_speed_hz = speed
            if speed > self._maxSPIspeed:
                print("WARNING: forcing SPI clock speed to", speed, "Hz.")
            return

        # Check against minimum.
        if speed < self._minSPIspeed:
            print("WARNING: SPI clock speed", speed,
                  "is too low, using", self._minSPIspeed, "instead.")
            speed = self._minSPIspeed

        # Check against maximum.
        abs_max = 33300000	# highest seen to work at all
        safe_max = 28500000	# highest seen to work with zero write-read errors
        if speed > self._maxSPIspeed:
            if speed > abs_max:
                print("WARNING: SPI clock speed", speed,
                      "Hz is way too high, using", abs_max, "Hz instead.")
                speed = abs_max
            if speed > safe_max:
                print("WARNING: SPI clock speed", speed,
                      "Hz may cause occasional write or read errors.")
            print("WARNING: SPI clock speed", speed,
                  "Hz is above maximum rated speed of", self._maxSPIspeed, "Hz.")
        print("Setting SPI clock speed to", speed/1000000.0, "MHz.")
        self._spi.max_speed_hz = speed

    def cleanup(self):
        """Turn off TDC7201, close SPI, and free up GPIO."""
        self.off()
        self._spi.close()
        self.chip_select = 0
        GPIO.cleanup()

    def exit(self):
        self.cleanup()
        sys.exit()

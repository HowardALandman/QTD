TDC7201 driver for Raspberry Pi
===============================

This project contains a python3 module for interfacing with the Texas Instruments TDC7201 Time-to-Digital-Converter chip through SPI.
As much as possible, it hides the internal implementation details (like SPI transactions, and chip registers and their field encodings) from the user.

All code is GPLv3+ licensed unless explicitly stated otherwise.

Usage
-----

```python
import tdc7201
tdc = tdc7201.TDC7201() # Create TDC object with SPI interface.
tdc.initGPIO() # Set pin directions and default values for non-SPI signals.
tdc.set_SPI_clock_speed(25000000)
tdc.on(meas_mode=2,num_stop=3,clock_cntr_stop=1,timeout=0.0005)
result = tdc.measure(simulate=True)
tdc.off()
```
Settings
--------

Most important parameters are set in the on() method, since the chip can only be reconfigured after it has come out of reset. See below.

Methods
-------

    initGPIO()

Sets up all the non-SPI pins. Currently this is hard-coded and accepts no arguments. Your actual hardware needs to match this setup.

    on(force_cal=True,meas_mode=2,calibration2_periods=10,avg_cycles=1,num_stop=1,clock_cntr_stop=0,clock_cntr_ovf=0xFFFF,timeout=None)

Take the chip out of reset and set up various control parameters.
* `force_cal` - If True, will recalibrate the chip after every attempted measurement. This is recommended (and, in this version, required). If False, will only recalibrate after a "successful" measurement, with timeouts and some other results considered unsuccessful. (This currently does not work.)
* `meas_mode` - Sets the measurement mode. Mode 1 is recommended for times less than 2000 nS; mode 2 for greater.
* `calibration2_periods` - The number of clock cycles to recalibrate for. The allowed values are 2, 10 (hardware default), 20, and 40.
* `avg_cycles` - The number of measurements to average over. The allowed values are 1, 2, 4, 8, 16, 32, 64, and 128. The default is 1, which means no averaging. If you use anything larger, the chip will run that many measurements and then report only the average values. This can be useful in a noisy environment.
* `num_stop` - The chip starts timing on a pulse on the START pin, and then can report timings for up to 5 pulses on the STOP pin. The default is 1, which means the measurement will terminate as soon as a single STOP pulse is received.
* `clock_cntr_stop = N` - If N is non-zero, the chip will ignore STOP pulses for N clock cycles after START.
* `clock_cntr_ovf = N` - The chip will end measurement ("time out") after N clock cycles even if num_stop STOP pulses have not been received. Default (and maximum) is 65535 = 0xFFFF.
* `timeout = T` - You can also specify the overflow period as a time in seconds. For example, if T is 0.0005, the timeout period will be 500 microseconds. If both timeout and clock_cntr_ovf are specified, timeout wins.

    measure(simulate=False)

Runs a single measurement, polling the chip INT1 pin until it indicates completion. (This should really be an interrupt.) Will time out after 0.1 seconds if measurement doesn't complete. If it does complete, calls read_regs1() and compute_tofs() so that both raw and processed data are available. If simulate==True, then generates START and STOP signals to send to the chip (for testing when your actual signal source is not yet available); this requires that the appropriate RPi pins be connected to START and STOP.

    off()

Asserts reset. This will terminate any measurement in progress, and make the chip unresponsive to SPI.

    write8(reg,val)

Low-level routine to write a single 8-bit value to an 8-bit chip register.

    read8(reg)

Low-level routine to read a single 8-bit value from an 8-bit chip register.

    write24(reg,val)

Low-level routine to write a 24-bit value to a 24-bit chip register.

    read24(reg)

Low-level routine to read a 24-bit value from an 24-bit chip register.

    read_regs1()

Read all of the side 1 chip registers (including measurement results) into the tdc.reg1 list. (There should be a similar method to read the side 2 registers, but there isn't yet.)

    print_regs1()

Print the internal copy of the side 1 chip registers. Note that, if this is not immediately preceded by read_regs1(), the internal copy and the actual chip registers may be out of sync.

    tof_mm2(time1,time2,count)

Compute time-of-flight given Measurement Mode 2 data for two adjacent stops.

    compute_tofs()

Check how many pulses we got, and compute the inter-pulse time for each adjacent pair.

    clear_status(verbose=False,force=False)

Clear interrupt register bits to prepare for next measurement. This isn't supposed to be necessary, but I was having problems without doing it. If verbose==True, prints detailed step-by-step results for debugging. If force==True, does a write even if the none of the bits appears to be set.

    set_SPI_clock(speed)

Attempts to set the SPI interface clock speed to speed (in Hz). Minimum legal value is 50000 (50 kHz) and maximum is 25000000 (25 MHz). The SPI clock is a hardware division of the CPU clock, so there are two important things to note. (1) The exact clock speed set may be restricted (by hardware) to only certain values in that range, so you may not get exactly what you ask for. (2) The CPU (and this module) can not tell what the CPU clock speed is, so the SPI clock will slow down or speed up if the CPU clock does (for example, for thermal management, turbo mode, or due to user over- or under-clocking of the Raspberry Pi). But this should mostly be invisible to the user, as it only affects SPI communication speed, and does not affect performance of the TDC7201 measurements (unless the TDC7201 is also being clocked by some submultiple of the Pi clock, which is a really really bad idea).


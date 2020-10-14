# TDC7201 driver for Raspberry Pi

This project contains a python3 module for interfacing with the Texas Instruments TDC7201 Time-to-Digital-Converter chip through SPI.
As much as possible, it hides the internal implementation details (like SPI transactions, and chip registers and their field encodings) from the user.

All code is GPLv3+ licensed unless explicitly stated otherwise.

For more information on the chip, see https://www.ti.com/product/TDC7201

## Usage

```python
import tdc7201
tdc = tdc7201.TDC7201() # Create TDC object with SPI interface.
tdc.initGPIO() # Set pin directions and default values for non-SPI signals.
tdc.set_SPI_clock_speed(12500000)
tdc.on()
tdc.configure(meas_mode=2,num_stop=3,clock_cntr_stop=1,timeout=0.0005)
status = tdc.measure(simulate=True)
tdc.off()
```

## Settings

Hardware pin assignments are done in `initGPIO()`, which should only be called once.
Most other important parameters are set in the `on()` method,
since the chip can only be reconfigured after it has come out of reset.
If you want to change parameters, it is cleanest to turn the chip `off()`, and then `on()` again with the new parameters.

## Methods

    initGPIO(enable=12,osc_enable=16,trig1=7,int1=37,trig2=11,int2=32,start=18,stop=22,verbose=False)

Assigns and initializes all the non-SPI pins.
Your actual hardware (wiring between RPi and chip) needs to match this setup.
No arguments are required, but the defaults match my prototype and are somewhat arbitrary.
You can see all assignments by calling with `verbose=True`.
Pin numbers follow `GPIO.BOARD` conventions,
i.e. they are the pin numbers on the 2x20 pin header.
Only 3 pins (`enable`,`trig1`,`int1`) are absolutely required;
the others can be skipped by assigning `None` to them.
If `osc_enable` is `None`, then there will be no signal to turn an external clock on or off; this is OK if you supply the chip clock yourself.
If `trig2` and/or `int2` is `None`, then side 2 of the chip will not work correctly, but side 1 still will.
The `stop` pin is only required if you want the Raspberry Pi to generate STOP signals for testing, i.e. if you plan to run `tdc.measure(simulate=True)`.
If you are hooked up to real signals to measure, then you can and should set `stop=None`.
The `start` pin is only required if you want the Raspberry Pi to generate a START signal; this could be hooked directly to the chip START, or used to trigger some external hardware.
Note that if you start a measurement, and the chip never sees a START signal, it will hang indefinitely waiting for one.

    on()

Takes the chip out of reset.

    configure(side=1,force_cal=True,meas_mode=2,trig_falling=False,falling=False,
calibration2_periods=10,avg_cycles=1,num_stop=1,clock_cntr_stop=0,clock_cntr_ovf=0xFFFF,timeout=None)

Set up various control parameters in the chip configuration registers.

* `side` -
Which side of the chip to configure. Default is 1. 2 does not work yet.
* `retain_state` -
Default `False`.
If `True`, will ignore all other arguments, and instead use the same settings
as from the previous call to `on()`.
Behavior is undefined if there was no previous call.
* `force_cal` -
If `True`, will recalibrate the chip after every attempted measurement.
This is recommended (and, in this version, required and default).
If `False`, will only recalibrate after a "successful" measurement,
with timeouts and some other results considered unsuccessful.
(This currently does not work.)
* `meas_mode` -
Sets the measurement mode.
Mode 1 is recommended for times less than 2000 nS; mode 2 for greater.
* `trig_falling` -
If `True`, sets the chip to use falling edge on TRIG to indicate chip is ready.
The default is `False`, which has it use rising edge on TRIG.
* `falling` -
If `True`, sets the chip to trigger on falling edges of START and STOP.
The default is `False`, which has it trigger on rising edges.
* `calibration2_periods` - The number of clock cycles to recalibrate for. The allowed values are 2, 10 (hardware default), 20, and 40.
If you specify any other value, will round up (if below 40) or down (if above 40) to the next legal value.
* `avg_cycles` -
The number of measurements to average over.
The allowed values are 1, 2, 4, 8, 16, 32, 64, and 128.
The default is 1, which means no averaging.
If you use anything larger, the chip will run that many measurements and then report only the average values.
This can be useful in a noisy environment.
(Averaging does not currently work with `measure(simulate=True)`.)
* `num_stop` -
The chip starts timing on a pulse on the START pin, and then can record timings for up to 5 pulses on the STOP pin.
Allowed values are 1, 2, 3, 4, 5.
The default is 1, which means the measurement will terminate as soon as a single STOP pulse is received.
If `num_stop==3`, the measurement will terminate after recording 3 STOP pulses or after timing out, whichever comes first.
* `clock_cntr_stop = N` - If N is non-zero, the chip will ignore STOP pulses for N clock cycles after START.
* `clock_cntr_ovf = N` - The chip will end measurement ("time out" or "clock counter overflow") after N clock cycles even if `num_stop` STOP pulses have not been received.
Default (and maximum) is 65535 = 0xFFFF.
* `timeout = T` - You can also specify the overflow period as a time in seconds. For example, if T is 0.0005, the timeout period will be 500 microseconds. If both `timeout` and `clock_cntr_ovf` are specified, `timeout` wins.

Note that `clock_cntr_ovf` must be greater than `clock_cntr_stop`,
or the measurement will time out before it begins accepting stop pulses.

    measure(simulate=False,error_prefix='',log_file=None)

Runs a single measurement, polling the chip INT1 pin until it indicates completion.
(This should really be an interrupt.)
Will time out after 0.1 seconds if measurement doesn't complete.
If it does complete, calls `read_regs24()` and `compute_tofs()` so that both raw and processed data are available.
If `simulate=True`, then generates START and/or STOP signals to send to the chip
(for testing when your actual signal source is not yet available);
this requires that the appropriate RPi pins be connected to START and/or STOP,
and that `initGPIO()` not be called with `start=None` or `stop=None` respectively.
(Simulate does not currently work with averaging.)
The `error_prefix` string will be prepended to any error messages from this call to `measure()`;
this allows you to easily identify which call had the problem.
If `log_file` is an already-open file handle,
will write any error messages to that file instead of printing them.

    off()

Asserts reset and waits 1 uS for it to take effect.
This will terminate any measurement in progress,
and make the chip unresponsive to SPI until the next call to on().

    clear_status(verbose=False,force=False)

Clears any set interrupt status register bits to prepare for next measurement.
This isn't supposed to be necessary, but I was having problems without doing it.
If `verbose==True`, prints detailed step-by-step results for debugging.
If `force==True`, tries to clear all IS bits even if some or all of them appear not to be set.

    set_SPI_clock_speed(speed,force=False)

Attempts to set the SPI interface clock speed to `speed` (in Hz).
Minimum legal value is 50000 (50 kHz), spec maximum is 25000000 (25 MHz),
and highest "overclocked" speed we've seen work is 33300000 (33.3 MHz).
The SPI clock is a hardware division of the CPU clock, so there are two important things to note.
(1) The exact clock speed set may be restricted (by hardware) to only certain values in that range, so you may not get exactly what you ask for.
(2) The SPI clock will slow down or speed up if the CPU clock does (for example, for thermal management, turbo mode, or due to user over- or under-clocking of the Raspberry Pi).
 The CPU (and the SPI driver, and this module) can not tell what the CPU clock speed is, so there is no way to compensate for this in software.
Therefore, it's probably a bad idea to overclock the SPI speed
if you know that your CPU will also be overclocked,
since that might result in a speed that doesn't work.
But all this should mostly be invisible to the user, as it only affects SPI communication speed, and does not affect performance of the TDC7201 measurements (unless the TDC7201 is also being clocked by some submultiple of the Pi clock, which is a really really bad idea).
* If `force=False`, values in the spec range are silent,
and overclocking up to 33.3 MHz is allowed with a warning.
If `force=True`, all speeds are allowed with a warning.
This should only be used for testing, not production.

The casual user should be able to get by with only the above methods; the following low-level methods give more detailed access to the hardware, but you'll need to know what you're doing.

    write8(reg,val)

Write a single 8-bit value to an 8-bit chip register.
This only makes sense for 8-bit registers (addresses 0 through 9).

    read8(reg)

Read a single 8-bit value from an 8-bit chip register.
This only makes sense for 8-bit registers (addresses 0 through 9).

    write16(reg,val)

Write a 16-bit value to a pair of 8-bit registers.
This only makes sense if reg is `COARSE_CNTR_OVF_H` (4), `CLOCK_CNTR_OVF_H` (6), or `CLOCK_CNTR_STOP_MASK_H` (8).

    read16(reg)

Read a pair of 8-bit registers and return them as a 16-bit value.
This only makes sense if reg is `COARSE_CNTR_OVF_H` (4), `CLOCK_CNTR_OVF_H` (6), or `CLOCK_CNTR_STOP_MASK_H` (8).

    write24(reg,val)

Write a 24-bit value to a 24-bit chip register.
This should probably never be used since those contain measurement and calibration results.

    read24(reg)

Read a 24-bit value from a 24-bit chip register.
This only makes sense for 24-bit registers (addresses 16 through 28).

    read_regs8()

Read all of the 8-bit side 1 chip registers into the tdc.reg1 list.
(It should be possible to make this read the side 2 registers, but it doesn't yet.)
This is much faster than looping over the registers in Python.

    read_regs24()

Read all of the 24-bit side 1 chip registers (measurement and calibration results) into the tdc.reg1 list.
(It should be possible to make this read the side 2 registers, but it doesn't yet.)
This is much faster than looping over the registers in Python.

    read_regs()

Read all of the side 1 chip registers (including measurement results) into the tdc.reg1 list.
(It should be possible to make this read the side 2 registers, but it doesn't yet.)
This is much faster than looping over the registers in Python.
Equivalent to `read_regs8()` plus `read_regs24()`.

    print_regs1()

Print the internal copy of the side 1 chip registers. Note that, if this is not immediately preceded by `read_regs()`, the internal copy and the actual chip registers may be out of sync.

    tof_mm1(time_n)

Compute time-of-flight in seconds using Measurement Mode 1 equation.

    tof_mm2(time1,time_n,count)

Compute time-of-flight in seconds using Measurement Mode 2 equations.

    compute_tofs()

Check how many pulses we got, and compute the TOF for each pulse.

    cleanup()

Put the TDC7201 into reset, close the SPI device, and free all the GPIO pins.
Should normally only be called just before exiting.
The tdc object will still exist,
but you would have to manually reopen `tdc._spi` and set its parameters,
plus call `initGPIO()` and `on()`,
before it would be usable again.

    exit()

Clean up the SPI and GPIO pins (i.e. call `cleanup()`), and then exit.


import board
import busio
import adafruit_si5351

i2c = busio.I2C(board.SCL, board.SDA)

si5351 = adafruit_si5351.SI5351(i2c)

# In the simplest use, the 25 MHz base clock needs to be multiplied by an
# integer from 15 to 90, and then divided by an integer from 4 to ???.
#
# 25 MHz * 64 / 100 should give 16 MHz but doesn't (more like 11.2 MHz).
# 25 MHz * 32 / 50 works.
# 25 MHz * 16 / 25 works.
# 25 MHz * 15 / 15 gives 25 MHz as expected.

# Configure multiplier (to PLL A).
si5351.pll_a.configure_integer(16)
print('PLL A set to {0} MHz'.format(si5351.pll_a.frequency / 1000000))

# Configure divider (from PLL A).
si5351.clock_1.configure_integer(si5351.pll_a, 25)
print('Clock 1 set to {0} MHz'.format(si5351.clock_1.frequency / 1000000))

# Turn outputs on.
si5351.outputs_enabled = True

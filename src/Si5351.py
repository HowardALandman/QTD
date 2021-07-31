import board
import busio
import adafruit_si5351

i2c = busio.I2C(board.SCL, board.SDA)

si5351 = adafruit_si5351.SI5351(i2c)

# 25 MHz base clock needs to be multiplied by an integer from 15 to 90,
# and then divided by an integer between 4 and ???

#si5351.pll_a.configure_integer(64)
# 25 MHz x 64 = 1600 MHz
si5351.pll_a.configure_integer(16)
print('PLL A set to {0} MHz'.format(si5351.pll_a.frequency / 1000000))

#si5351.clock_1.configure_integer(si5351.pll_a, 100)
# 1600 MHz / 100 = 16 MHz
si5351.clock_1.configure_integer(si5351.pll_a, 25)
print('Clock 1 set to {0} MHz'.format(si5351.clock_1.frequency / 1000000))

# Turn them on
si5351.outputs_enabled = True

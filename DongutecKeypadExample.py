"""
Reading a keypad through USB -> I2C.

USB I2C interface: https://thepihut.com/products/usb-uart-i2c-debugger
Keypad and interface: https://www.aliexpress.com/item/32829892555.html

USB I2C interface is a MCP2221 USB to I2C/UART/GPIO device.
Keypad interface is a MCP23008 I2C to GPIO device.
"""

from PyMCP2221A import PyMCP2221A

print('-'*50)
print('Read Dongutec Keypad')
print('-'*50)
mcp2221 = PyMCP2221A.PyMCP2221A()

mcp2221.I2C_Init()


class DongutecKeypad(object):

    def __init__(self, i2c_device, i2c_address=0x27):
        # The keypad is connected to a MCP23008 controller, which is an I2C
        # controlled 8 pin GPIO expander.
        # In order to access the GPIO pins it is necessary to confgure the I2C
        # device appropriately, and then scan the rows followed by the columns.
        # By default the I2C device is configured to be I2C address 0x27. The
        # contacts on the board can be soldered change this address, each bit
        # negating the default address.

        # The rows will be in the low bits, and the columns in the high bits.
        # If you connect the cable a different way around you may find that
        # this is reversed, but this was how I connected it.

        # What we will do is to power the bottom 4 bits, and read the top
        # 4 bits. This will tell us which row the pressed button is on.
        # Then we change the inputs around and power the top 4 bits, and
        # read the bottom 4 bits. This will tell us the column the button
        # is on.
        # Using a lookup table we can see what key was actually pressed
        # with a lookup of the two values.

        self.i2c_device = i2c_device
        self.i2c_address = i2c_address

        self.gpio_lookup = {}
        for key in range(16):
            row_mask = 1<<(3-(key & 3))
            column_mask = 16<<(3-(key>>2))
            self.gpio_lookup[row_mask | column_mask] = key
            #print("Value = {:#010b} => {}".format(row_mask | column_mask, key))

        # Set up the MCP23008 so that all the input pins are inverted (it's
        # just easier when we're reading the results)
        self.i2c_write([1, 255])  # All of the pins are inverted

        # And configure all the pins to be pull up so that there's no floating
        # values (which would pick up static very easily). It's noted in some
        # of the online discussions that the pull ups are very weak, but they
        # appear sufficient for this task.
        self.i2c_write([6, 255])  # Set pins to 1 with pull up

    def i2c_write(self, values):
        self.i2c_device.I2C_Write(self.i2c_address, values)

    def i2c_read(self, size):
        values = self.i2c_device.I2C_Read(self.i2c_address, size)
        if values == -1:
            # If we didn't read anything then there cannot be anything pressed.
            values = [0]
        return values

    def get_key(self):
        self.i2c_write([0, 240])   # Set the top 4 pins as inputs
        self.i2c_write([9])        # Address we will read is the GPIO pins, at address 9
        row_value = self.i2c_read(1)[0]

        self.i2c_write([0, 15])    # Set the bottom 4 pins as inputs
        self.i2c_write([9])        # Address we will read is the GPIO pins, at address 9
        column_value = self.i2c_read(1)[0]

        return self.gpio_lookup.get(row_value | column_value, None)


dk = DongutecKeypad(mcp2221)
while True:
    key = dk.get_key()
    print("Key = %s" % (key,))

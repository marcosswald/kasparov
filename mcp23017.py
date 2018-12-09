import smbus
import time

class MCP23017:
    # Registers
    IODIRA = 0x00 # Pin direction register A
    IODIRB = 0x01 # Pin direction register B
    GPIOA  = 0x12 # Register for inputs A
    GPIOB  = 0x13 # Register for inputs B
    GPPUA = 0x0C # Register for internal pullups A
    GPPUB = 0x0D # Register for internal pullups B

    def __init__(self, device_address):
        self._device = 0x20 + device_address # Device address (A0-A2)
        self._bus = smbus.SMBus(1) # Rev 2 Pi uses 1

        # Set all pins as inputs
        self._bus.write_byte_data(self._device,self.IODIRA,0xFF)
        self._bus.write_byte_data(self._device,self.IODIRB,0xFF)

        # Enable internal pullups
        self._bus.write_byte_data(self._device,self.GPPUA,0xFF)
        self._bus.write_byte_data(self._device,self.GPPUB,0xFF)

    def _readGPA(self):
        return self._bus.read_byte_data(self._device,self.GPIOA)

    def _readGPB(self):
        return self._bus.read_byte_data(self._device,self.GPIOB)

    def readAll(self):
        return [self._readGPA(), self._readGPB()]

if __name__ == '__main__':
    mcp = MCP23017(0)
    # Loop until user presses CTRL-C
    while True:
        # Read state of GPIOA register
        MySwitch = mcp.readAll()
        
        print(MySwitch)
        time.sleep(0.1)
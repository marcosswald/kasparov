import smbus
import time
import RPi.GPIO as GPIO

class MCP23017:
    # Registers
    IODIRA = 0x00 # Pin direction register A
    IODIRB = 0x01 # Pin direction register B
    GPINTENA = 0x04 # Interrupt on change control register A
    GPINTENB = 0x05 # Interrupt on change control register B
    DEFVALA = 0x06 # Interrupt compare register A
    DEFVALB = 0x07 # Interrupt compare register B
    INTCONA = 0x08 # Interrupt control register A
    INTCONB = 0x09 # Interrupt control register B
    IOCON = 0x0A # Configuration register
    GPPUA = 0x0C # Register for internal pullups A
    GPPUB = 0x0D # Register for internal pullups B
    GPIOA  = 0x12 # Register for inputs A
    GPIOB  = 0x13 # Register for inputs B

    def __init__(self, device_address):
        self._device = 0x20 + device_address # Device address (A0-A2)
        self._bus = smbus.SMBus(1) # Rev 2 Pi uses 1

        # Set all pins as inputs
        self._bus.write_byte_data(self._device,self.IODIRA,0xFF)
        self._bus.write_byte_data(self._device,self.IODIRB,0xFF)

        # Enable internal pullups
        self._bus.write_byte_data(self._device,self.GPPUA,0xFF)
        self._bus.write_byte_data(self._device,self.GPPUB,0xFF)

        # Set configuration (IntA and IntB connected, open drain)
        self._bus.write_byte_data(self._device,self.IOCON,0x44)

        # Enable interrupt on change (compared against previous value)
        self._bus.write_byte_data(self._device,self.GPINTENA,0xFF)
        self._bus.write_byte_data(self._device,self.GPINTENB,0xFF)
        self._bus.write_byte_data(self._device,self.INTCONA,0x00)
        self._bus.write_byte_data(self._device,self.INTCONB,0x00)
    
    def __del__(self):
        GPIO.cleanup()

    def _readGPA(self):
        return self._bus.read_byte_data(self._device,self.GPIOA)

    def _readGPB(self):
        return self._bus.read_byte_data(self._device,self.GPIOB)

    def readAll(self):
        return [self._readGPA(), self._readGPB()]

    def registerInterruptCallback(self, cb, pin):
        GPIO.setmode(GPIO.BCM) # set GPIO numbering
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        lambda_cb = lambda channel, device=self: cb(channel, device)
        GPIO.add_event_detect(pin, GPIO.FALLING, callback=lambda_cb, bouncetime=10)
        self.readAll() # clear interrupt

def test_callback(channel, device):
    print("Interrupt detected")
    print(device.readAll())

if __name__ == '__main__':
    GPIO.setmode(GPIO.BCM) # set GPIO numbering
    GPIO.setup(27, GPIO.OUT)
    GPIO.output(17, GPIO.LOW) # reset device
    time.sleep(0.1)
    GPIO.output(17, GPIO.HIGH)
    mcp = MCP23017(1)
    mcp.registerInterruptCallback(test_callback,17)

    while True:
        time.sleep(1)
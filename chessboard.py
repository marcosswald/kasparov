import time
import RPi.GPIO as GPIO
from mcp23017 import MCP23017

class Chessboard:

    def __init__(self):
        # Pin definition
        self._reset_pin = 27
        self._interrupt_pin = 17
        self._led_green = 14
        self._led_yellow = 15
        self._led_red = 18

        # Set GPIOs
        GPIO.setmode(GPIO.BCM) # set GPIO numbering
        GPIO.setup(self._reset_pin, GPIO.OUT)
        GPIO.setup(self._interrupt_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self._led_green, GPIO.OUT)
        GPIO.setup(self._led_yellow, GPIO.OUT)
        GPIO.setup(self._led_red, GPIO.OUT)

        # MCP
        GPIO.output(self._reset_pin, GPIO.LOW) # reset all devices
        time.sleep(0.1)
        GPIO.output(self._reset_pin, GPIO.HIGH)
        self._rowAB = MCP23017(0) # Device address 0
        self._rowCD = MCP23017(1) # Device address 1
        self._rowEF = MCP23017(2) # Device address 2
        self._rowGH = MCP23017(3) # Device address 3
        self._positions = [0]*8

        # register interrupt callback
        GPIO.add_event_detect(self._interrupt_pin, GPIO.FALLING, callback=self._onInterruptEvent, bouncetime=10)
        self.readPositions() # clear interrupt

    def _onInterruptEvent(self, channel):
        print(self.readPositions())

    def getLastPositions(self):
        return self._positions

    def readPositions(self):
        self._positions[0:2] = self._rowAB.readAll()
        self._positions[2:4] = self._rowCD.readAll()
        self._positions[4:6] = self._rowEF.readAll()
        self._positions[6:8] = self._rowGH.readAll()
        return self._positions

def test_callback(channel, device):
    print(self._rowAB.readAll())
    print(self._rowCD.readAll())
    print(self._rowEF.readAll())
    print(self._rowGH.readAll())

if __name__ == '__main__':
    chessboard = Chessboard()

    while True:
        time.sleep(1)
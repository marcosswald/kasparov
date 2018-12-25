import chess
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
        GPIO.output(self._led_red, GPIO.HIGH)
        GPIO.output(self._led_yellow, GPIO.HIGH)
        GPIO.output(self._led_green, GPIO.HIGH)

        # MCP
        GPIO.output(self._reset_pin, GPIO.LOW) # reset all devices
        time.sleep(0.1)
        GPIO.output(self._reset_pin, GPIO.HIGH)
        self._rowAB = MCP23017(0) # Device address 0
        self._rowCD = MCP23017(1) # Device address 1
        self._rowEF = MCP23017(2) # Device address 2
        self._rowGH = MCP23017(3) # Device address 3
        self._positions = [[1]*8]*8

        # register interrupt callback
        GPIO.add_event_detect(self._interrupt_pin, GPIO.FALLING, callback=self._onInterruptEvent, bouncetime=10)
        self._board_initialized = False # board has not yet been initialized
        self.readPositions() # clear interrupt

    def _initBoard(self):
        self._two_pieces_active = False
        self._last_action = "SET"
        self._last_active = ""
        self._board_initialized = True
        self.board = chess.Board()

    def _onInterruptEvent(self, channel):
        # read new positions
        new_pos = self.readPositions()

        # get the move but only if board has been initialized
        if self._board_initialized:
            # find active field
            rows = ['1','2','3','4','5','6','7','8']
            cols = ['a','b','c','d','e','f','g','h']
            for i,r in enumerate(rows):
                for j,c in enumerate(cols):
                    if new_pos[i][j] != self._positions[i][j]:
                        active_field = c+r
                        if new_pos[i][j] == 0:
                            action = "SET"
                        else:
                            action = "MOVING"
                        # find move
                        if action == "MOVING":
                            if self._last_action == "MOVING":
                                self._two_pieces_active = True
                                self._last_active = [active_field, self._last_active]
                            else:
                                self._two_pieces_active = False
                                self._last_active = active_field  
                        elif (action == "SET" and not (self._two_pieces_active)):
                            move = self._last_active+active_field
                            self._last_active = ""
                            print("Simple move:",move)
                            self.board.push(chess.Move.from_uci(move)) # update board
                            print(self.board)
                        elif (action == "SET" and self._two_pieces_active):
                            print("Complex move:")
                            self._last_active = ""
                        self._last_action = action

        # store position
        self._positions = new_pos

    def getLastPositions(self):
        return self._positions

    def readPositions(self):
        pos_int = [1]*8
        pos_int[6:8] = self._rowAB.readAll()[::-1]
        pos_int[4:6] = self._rowCD.readAll()[::-1]
        pos_int[2:4] = self._rowEF.readAll()[::-1]
        pos_int[0:2] = self._rowGH.readAll()[::-1]
        
        # convert positions to binary
        positions = [[1]*8]*8
        i = 0
        for val in pos_int:
            positions[i] = [int(x) for x in "{0:08b}".format(val)]
            if i == 1 or i == 3 or i == 5 or i == 7:
                positions[i] = positions[i][::-1]
            i += 1

        # check if start position was detected
        if pos_int == [0,0,255,255,255,255,0,0]:
            print("Start position detected. Starting new game.")
            self._initBoard()
            self._positions = positions
        
        return positions

if __name__ == '__main__':
    chessboard = Chessboard()

    while True:
        time.sleep(1)
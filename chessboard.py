import chess
import time
import RPi.GPIO as GPIO
from mcp23017 import MCP23017

class Chessboard:

    # constants
    LED_ON = 0
    LED_OFF = 1
    ACTION_SET = 0
    ACTION_REMOVE = 1

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
        self.setStatusLed(self._led_green,self.LED_OFF)
        self.setStatusLed(self._led_yellow,self.LED_OFF)
        self.setStatusLed(self._led_red,self.LED_ON)

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

    def __del__(self):
        GPIO.cleanup()

    def _initBoard(self):
        self._last_action = self.ACTION_SET
        self._pieces = None
        self._squares = None
        self._board_initialized = True
        self.board = chess.Board()
        self.setStatusLed(self._led_green,self.LED_ON)
        self.setStatusLed(self._led_yellow,self.LED_OFF)
        self.setStatusLed(self._led_red,self.LED_OFF)

    def _onInterruptEvent(self, channel):
        # read new positions
        new_pos = self.readPositions()

        # get the move but only if board has been initialized
        if self._board_initialized:
            # find active field
            for i,r in enumerate(chess.RANK_NAMES):
                for j,c in enumerate(chess.FILE_NAMES):
                    if new_pos[i][j] != self._positions[i][j]:
                        square = chess.square(j,i)
                        if new_pos[i][j] == 0:
                            action = self.ACTION_SET
                        else:
                            action = self.ACTION_REMOVE
                            self.setStatusLed(self._led_yellow,self.LED_ON)
                        # find move
                        if action == self.ACTION_REMOVE: # remove action
                            piece = self.board.remove_piece_at(square) # remove the piece
                            if self._last_action == self.ACTION_REMOVE:
                                self._pieces = [piece, self._pieces]
                                self._squares = [square, self._squares]
                            else:
                                self._pieces = piece
                                self._squares = square  
                        elif action == self.ACTION_SET: # set action
                            if (type(self._pieces) is not list): # simple move
                                print("Simple move: " + self._pieces.symbol() + " from " + chess.SQUARE_NAMES[self._squares] + " to " + chess.SQUARE_NAMES[square])
                                self.board.set_piece_at(square,self._pieces)
                                print(self.board)
                                self.setStatusLed(self._led_yellow,self.LED_OFF)
                            elif (type(self._pieces) is list and len(self._pieces) == 2): # capture move
                                # we assume that the captured piece was at the active square
                                cap_square_id = self._squares.index(square) # get the index of the active square from last squares
                                captured_piece = self._pieces[cap_square_id].symbol()
                                del self._pieces[cap_square_id] # remove the captured piece
                                del self._squares[cap_square_id] # remove the capture square from last squares
                                survivor = self._pieces[0] # the remaining piece is the survivor
                                from_square = self._squares[0] # the remaining square is the place where the survivor started from
                                self.board.set_piece_at(square, survivor) # now set the piece
                                print("Capture move: " + survivor.symbol() + " from " + chess.SQUARE_NAMES[from_square] + " to " + chess.SQUARE_NAMES[square] + " (" + captured_piece + " captured)")
                                print(self.board)
                                self.setStatusLed(self._led_yellow,self.LED_OFF)
                            else:
                                print("Error: Lost synchronization!")
                                self.setStatusLed(self._led_green,self.LED_OFF)
                                self.setStatusLed(self._led_red,self.LED_ON)
                            
                        self._last_action = action

        # store position
        self._positions = new_pos

    def setStatusLed(self,led,state):
        if state == self.LED_ON:
            GPIO.setup(led, GPIO.OUT)
            GPIO.output(led,self.LED_ON)
        else:
            GPIO.setup(led, GPIO.IN) # set pin to high impedance (to be sure that LED is turned off when cathode at 5V)

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
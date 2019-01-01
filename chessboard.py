import chess
import chess.uci
import time
import copy
import RPi.GPIO as GPIO
from mcp23017 import MCP23017

class Chessboard:

    # constants
    LED_ON = 0
    LED_OFF = 1
    ACTION_SET = 0
    ACTION_REMOVE = 1

    # modes
    ONE_PLAYER_MODE = 0
    TWO_PLAYER_MODE = 1

    # piece types
    PIECE_NAMES = ["Piece", "Pawn", "Knight", "Bishop", "Rook", "Queen", "King"]

    def __init__(self):
        # Pin definition
        self._reset_pin = 27
        self._interrupt_pin = 17
        self._led_green = 14
        self._led_yellow = 15
        self._led_red = 18

        # settings
        self.mode = self.TWO_PLAYER_MODE
        self._computer_color = chess.BLACK

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

        # start stockfish engine
        self._engine = chess.uci.popen_engine("stockfish")

        # register interrupt callback
        GPIO.add_event_detect(self._interrupt_pin, GPIO.FALLING, callback=self._onInterruptEvent, bouncetime=10)
        self._board_initialized = False # board has not yet been initialized
        self.readPositions() # clear interrupt

    def __del__(self):
        print("cleaning up...")
        GPIO.cleanup()

    def _initBoard(self):
        self._last_action = self.ACTION_SET
        self._pieces = []
        self._squares = []
        self._board_initialized = True
        self._game_is_over = False
        self.board = chess.Board()
        self._engine.ucinewgame()
        self._info_handler = chess.uci.InfoHandler()
        self._engine.info_handlers.append(self._info_handler)
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
                                if (len(self._pieces) > 1) or (self._pieces[0].color == piece.color):
                                    self._lostSync()
                                    return False 
                                self._pieces.append(piece)
                                self._squares.append(square)
                            else:
                                self._pieces = [piece]
                                self._squares = [square]
                        elif action == self.ACTION_SET: # set action
                            if len(self._pieces) == 1: # simple move
                                print("Simple move: " + self._pieces[0].symbol() + " from " + chess.SQUARE_NAMES[self._squares[0]] + " to " + chess.SQUARE_NAMES[square])
                            elif len(self._pieces) == 2: # capture move
                                # we assume that the captured piece was at the active square
                                try:
                                    cap_square_id = self._squares.index(square) # get the index of the active square from last squares
                                    captured_piece = self._pieces[cap_square_id].symbol()
                                    del self._pieces[cap_square_id] # remove the captured piece
                                    del self._squares[cap_square_id] # remove the capture square from last squares
                                    print("Capture move: " + self._pieces[0].symbol() + " from " + chess.SQUARE_NAMES[self._squares[0]] + " to " + chess.SQUARE_NAMES[square] + " (" + captured_piece + " captured)")
                                except:
                                    self._lostSync()
                                    return False 
                            else:
                                self._lostSync()
                                return False
                            # now set the piece
                            self.board.set_piece_at(square, self._pieces[0])
                            print(self.board)
                            # update stats
                            if self._pieces[0].color == chess.WHITE and self.board.turn == chess.WHITE:
                                self.board.turn = chess.BLACK
                            elif self._pieces[0].color == chess.BLACK and self.board.turn == chess.BLACK:
                                self.board.turn = chess.WHITE
                                self.board.fullmove_number += 1
                            self.setStatusLed(self._led_yellow,self.LED_OFF)
                            # check if game is over
                            if self.board.is_game_over():
                                print("Game Over! Result " + self.board.result())
                                self._board_initialized = False
                                self._game_is_over = True
                            
                        # store last action
                        self._last_action = action

        # store position
        self._positions = new_pos
        return True

    def _lostSync(self):
        print("Error: Lost synchronization!")
        self.setStatusLed(self._led_green,self.LED_OFF)
        self.setStatusLed(self._led_yellow,self.LED_OFF)
        self.setStatusLed(self._led_red,self.LED_ON)
        self._board_initialized = False

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

    def isReady(self):
        return self._board_initialized
    
    def isGameOver(self):
        return self._game_is_over

    def getWinnerText(self):
        if self.board.result() == "1/2-1/2":
            return "It is a draw."
        winner = "white" if self.board.result() == "1-0" else "black"
        return "{} has won.".format(winner)
    
    def getBestMove(self, _movetime):
        try:
            self._engine.position(self.board)
            move = self._engine.go(movetime=_movetime)
            return move
        except chess.engine.EngineTerminatedException:
            print("An engine terminate exception occured!")
            return None
    
    def getBestMoveText(self, _movetime=2000):
        move = self.getBestMove(_movetime)
        if move is None:
            return None
        piece_type = self.board.piece_type_at(move.bestmove.from_square)
        if piece_type is not None:
            piece = self.PIECE_NAMES[piece_type]
        else:
            piece = "Piece"
        move_string = "move your " + piece + " from " + chess.SQUARE_NAMES[move.bestmove.from_square] + " to " + chess.SQUARE_NAMES[move.bestmove.to_square] 
        return move_string
    
    def getScore(self):
        try:
            movetime = 1000
            self._engine.position(self.board)
            self._engine.go(movetime=movetime)
            score = self._info_handler.info["score"][1]
            return score
        except chess.engine.EngineTerminatedException:
            print("An engine terminate exception occured!")
            return None

    def getScoreText(self):
        score = self.getScore()
        if score is None:
            return None  
        if score.mate is not None:
            color = "black" if (self.board.turn == chess.WHITE and score.mate > 0) or (self.board.turn == chess.BLACK and score.mate < 0) else "white"
            score_string = color + " can be mated in {}".format(abs(score.mate)) + " moves"
        else:
            color = "white" if self.board.turn == chess.WHITE else "black"
            pos = "ahead" if score.cp > 0 else "behind"
            score_string = color + " is {:.1f}".format(abs(score.cp)/100) + " points " + pos
        return score_string

    def getTurnText(self):
        color = "white" if self.board.turn == chess.WHITE else "black"
        return "it is {}'s turn.".format(color)

if __name__ == '__main__':
    chessboard = Chessboard()

    while True:
        input("Press key to continue...")
        if chessboard.isReady():
            #print(chessboard.getBestMove(2000))
            print(chessboard.getScoreText())
            #print(chessboard.getTurnText())
        time.sleep(1)
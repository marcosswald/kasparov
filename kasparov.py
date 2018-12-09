from enum import Enum
import time

from chessboard import Chessboard
from stockfish import Stockfish

# global variables
State = Enum('State','WAIT_INIT WAIT_MOVE LOST_SYNC')
current_state = State.WAIT_INIT
chessboard = Chessboard()

# functions
def checkStartPosition():
    if chessboard.readPositions() == [0xFF, 0xFF, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF]:
        print("Valid start position detected!")
        return True
    else:
        return False

# main
if __name__ == '__main__':
    # main loop
    while True:
        if current_state == State.WAIT_INIT:
            if (checkStartPosition()):
                # start new game
                stockfish = Stockfish()
                current_state = State.WAIT_MOVE

        time.sleep(0.1)

    # stockfish methods
    print(stockfish.is_move_correct('e2e4'))
    stockfish.set_position(['e2e4'])
    print(stockfish.get_best_move())
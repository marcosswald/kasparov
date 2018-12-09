from enum import Enum
import time

from stockfish import Stockfish

# global variables
State = Enum('State','WAIT_INIT WAIT_MOVE LOST_SYNC')
current_state = State.WAIT_INIT

# functions
def checkStartPosition():
    return False

# main
if __name__ == '__main__':
    # main loop
    while True:
        if current_state == State.WAIT_INIT:
            if (checkStartPosition()):
                current_state = State.WAIT_MOVE

        print(current_state)
        time.sleep(0.1)

    # start new game
    stockfish = Stockfish()
    print(stockfish.is_move_correct('e2e4'))
    stockfish.set_position(['e2e4'])
    print(stockfish.get_best_move())
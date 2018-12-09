from mcp23017 import MCP23017

class Chessboard:

    def __init__(self):
        self._rowAB = MCP23017(0) # Device address 0
        self._rowCD = MCP23017(0) # Device address 1
        self._rowEF = MCP23017(0) # Device address 2
        self._rowGH = MCP23017(0) # Device address 3
        self._positions = [0]*8

    def getLastPositions(self):
        return self._positions

    def readPositions(self):
        self._positions[0:2] = self._rowAB.readAll()
        self._positions[2:4] = self._rowCD.readAll()
        self._positions[4:6] = self._rowEF.readAll()
        self._positions[6:8] = self._rowGH.readAll()
        return self._positions

if __name__ == '__main__':
    chessboard = Chessboard()
    print(chessboard.getLastPositions())
    print(chessboard.readPositions())
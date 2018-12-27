from flask import Flask
from flask_ask import Ask, statement, question, session
from chessboard import Chessboard

# create chess board
# chessboard = Chessboard()

app = Flask(__name__)
ask = Ask(app, '/')

@app.route('/')
def homepage():
    return "Hi there, kasparov is up and running"

@ask.intent('BestMoveIntent')
def best_move():
    return statement("Kasparov says that you should move your king.")

# main
if __name__ == '__main__':
    app.run(debug=True)
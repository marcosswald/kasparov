from flask import Flask
from flask_ask import Ask, statement, question, session
from chessboard import Chessboard

# create chess board
chessboard = Chessboard()

app = Flask(__name__)
ask = Ask(app, '/kasparov')

@app.route('/')
def homepage():
    return "Hi there, kasparov is up and running"

@ask.intent('BestMoveIntent')
def best_move():
    best_move = chessboard.getBestMove(_movetime=2000)
    return statement("Kasparoff says that " + best_move)

# main
if __name__ == '__main__':
    app.run(host='0.0.0.0',ssl_context=('certificate/certificate.pem', 'certificate/private-key.pem'))
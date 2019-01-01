from flask import Flask, request
from flask_ask import Ask, statement, question, session
from chessboard import Chessboard

# create chess board
chessboard = Chessboard()

app = Flask(__name__)
ask = Ask(app, '/kasparov')

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/')
def homepage():
    return "Hi there, kasparov is up and running"

@ask.launch
def start_skill():
    return question('Do you want to start a new game of chess?')

@ask.intent('YesIntent')
def yes():
    global chessboard
    chessboard.__del__()
    chessboard = Chessboard()
    return statement("Ok. Please put all pieces in their starting position.")

@ask.intent('NoIntent')
def no():
    return statement("Ok.")

@ask.intent('AMAZON.FallbackIntent')
def fallback():
    return statement("Kasparov dosen't know how to respond to your question.")

@ask.intent('AMAZON.StopIntent')
def stop():
    global chessboard
    chessboard.__del__()
    shutdown_server()
    return statement("Shutting down Kasparov.")

@ask.intent('TurnIntent')
def get_turn():
    if chessboard.isReady():
        turn = chessboard.getTurnText()
        if turn is not None:
            return statement("Kasparov says that {}".format(turn))
        else:
            return statement("Kasparov does not know who's turn it is.")
    else:
        return statement("Kasparov was not following the game and says you should start a new one.")

@ask.intent('ScoreIntent')
def get_score():
    if chessboard.isReady():
        score = chessboard.getScoreText()
        if score is not None:
            return statement("Kasparov thinks that {}".format(score))
        else:
            return statement("Kasparov does not know how to interpret the current situation.")
    else:
        return statement("Kasparov was not following the game and says you should start a new one.")

@ask.intent('BestMoveIntent')
def best_move():
    if chessboard.isReady():
        best_move = chessboard.getBestMoveText(_movetime=2000)
        if best_move is not None:
            return statement("Kasparov says that you should {}".format(best_move))
        else:
            return statement("Kasparov does not know what to do.")
    else:
        return statement("Kasparov lost track of your game and says you should start a new one.")

# main
if __name__ == '__main__':
    app.run(host='0.0.0.0',ssl_context=('certificate/certificate.pem', 'certificate/private-key.pem'))
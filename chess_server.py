import chess
import chess.engine

# curl -X POST -d '{"move": "d2d4", "max_ms": "0.1", "board": "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"}' localhost:9000
# {"board": "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq - 0 1", "move": "g8f6"}

class ChessInkServer:
    def __init__(self):
        self.board = chess.Board()
    def get_board_fen(self):
        return self.board.fen()
    def set_board(self, board_fen, move_uci):
        self.board = chess.Board(board_fen)
        move = self.board.parse_uci(move_uci)
        self.board.push(move)
    def play(self, max_ms):
        engine = chess.engine.SimpleEngine.popen_uci(r"/root/Stockfish-sf_15/src/stockfish")
        result = engine.play(self.board, chess.engine.Limit(time=max_ms))
        engine.quit()
        self.board.push(result.move)
        return result.move.uci()

from http.server import BaseHTTPRequestHandler, HTTPServer
import json

hostName = "localhost"
hostPort = 9000

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        cs = ChessInkServer()
        game = {'board': cs.get_board_fen()}
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(bytes(json.dumps(game)+"\n", "utf-8"))
    def do_POST(self):
        try:
            content = self.rfile.read(int(self.headers['Content-Length']))
            game = json.loads(content.decode("utf-8"))
            cs = ChessInkServer()
            cs.set_board(game['board'], game['move'])
            move = cs.play(float(game['max_ms']))
            game = {'board': cs.get_board_fen(), 'move': move}
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(json.dumps(game)+"\n", "utf-8"))
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(bytes(repr(e)+"\n", "utf-8"))

myServer = HTTPServer((hostName, hostPort), MyServer)

try:
    myServer.serve_forever()
except KeyboardInterrupt:
    pass

myServer.server_close()

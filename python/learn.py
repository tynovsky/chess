#!/usr/bin/env python3

import numpy as np
import random
import chess2

# --- Encoding ---

PIECE_CHANNEL = {1: 0, 2: 0, 3: 1, 4: 2, 5: 3, 6: 3, 7: 4, 8: 5, 9: 5}
INPUT_SIZE = 768  # 64 squares * 12 channels (6 piece types * 2 colors)

def encode_board(board):
    x = np.zeros(INPUT_SIZE)
    for i in range(64):
        p = board[i]
        if p > 0:
            x[i * 12 + PIECE_CHANNEL[p]] = 1.0
        elif p < 0:
            x[i * 12 + 6 + PIECE_CHANNEL[-p]] = 1.0
    return x

# --- Network ---

class Network:
    def __init__(self, sizes):
        self.weights = []
        self.biases = []
        for i in range(len(sizes) - 1):
            w = np.random.randn(sizes[i], sizes[i + 1]) * np.sqrt(2.0 / sizes[i])
            b = np.zeros(sizes[i + 1])
            self.weights.append(w)
            self.biases.append(b)
        self._acts = None

    def forward(self, x):
        acts = [x]
        for i in range(len(self.weights) - 1):
            x = x @ self.weights[i] + self.biases[i]
            x = np.maximum(0, x)
            acts.append(x)
        x = x @ self.weights[-1] + self.biases[-1]
        x = np.tanh(x)
        acts.append(x)
        self._acts = acts
        return x[0]

    def update(self, target, lr):
        output = self._acts[-1]
        grad = (output - target) * (1 - output ** 2)
        for i in range(len(self.weights) - 1, -1, -1):
            dw = self._acts[i].reshape(-1, 1) @ grad.reshape(1, -1)
            db = grad
            grad = grad @ self.weights[i].T
            if i > 0:
                grad = grad * (self._acts[i] > 0)
            self.weights[i] -= lr * dw
            self.biases[i] -= lr * db

    def save(self, path):
        np.savez(path, *self.weights, *self.biases)

    def load(self, path):
        data = np.load(path)
        n = len(self.weights)
        for i in range(n):
            self.weights[i] = data[f'arr_{i}']
            self.biases[i] = data[f'arr_{n + i}']

# --- Search ---

def nn_search(board, depth, net, alpha, beta):
    if depth == 0:
        return net.forward(encode_board(board)), None
    moves = chess2.possible_moves(board)
    if not moves:
        if chess2.is_attacked(chess2.find_king(board), board):
            return -1.0, None
        return 0.0, None
    best_move = moves[0]
    for move in moves:
        b = board.copy()
        chess2.do_move(move, b)
        s = -nn_search(chess2.flip_sides(b), depth - 1, net, -beta, -alpha)[0]
        if s > alpha:
            alpha = s
            best_move = move
        if alpha >= beta:
            break
    return alpha, best_move

def nn_pick_move(board, depth, net, explore=False):
    moves = chess2.possible_moves(board)
    if not moves:
        return None
    if explore and random.random() < 0.1:
        return random.choice(moves)
    alpha = -2.0
    scored = []
    for move in moves:
        b = board.copy()
        chess2.do_move(move, b)
        s = -nn_search(chess2.flip_sides(b), depth - 1, net, -2.0, -alpha)[0]
        scored.append((s, move))
        if s > alpha:
            alpha = s
    scored.sort(key=lambda x: x[0], reverse=True)
    if explore:
        return random.choice(scored[:3])[1]
    return scored[0][1]

# --- Training ---

def self_play(net, depth=1):
    game = chess2.new_game()
    boards = []
    while True:
        result = chess2.is_over(game)
        if result:
            break
        boards.append(game['board'].copy())
        move = nn_pick_move(game['board'], depth, net, explore=True)
        chess2.game_do_move(game, move)

    if result == "checkmate":
        final_value = -1.0
    else:
        final_value = 0.0

    return boards, final_value, result

def make_net(path=None):
    net = Network([INPUT_SIZE, 128, 32, 1])
    if path:
        net.load(path)
    return net

def train(num_games=1000, depth=1, lr=0.001, model_path=None, save_path="chess_model"):
    net = make_net(model_path)
    chess2.initialize_move_map()

    results = {"checkmate": 0, "stalemate": 0,
               "insufficient material": 0,
               "threefold repetition": 0, "50-move rule": 0}

    for g in range(num_games):
        boards, final_value, result = self_play(net, depth)
        results[result] += 1

        encoded = [encode_board(b) for b in boards]
        values = [net.forward(e) for e in encoded]

        for t in range(len(encoded)):
            if t == len(encoded) - 1:
                target = -final_value
            else:
                target = -values[t + 1]
            net.forward(encoded[t])
            net.update(np.array([target]), lr)

        if (g + 1) % 10 == 0:
            print(f"game {g + 1}/{num_games}, {len(boards)} moves, {result}")
            net.save(save_path)

    print("results:", results)
    net.save(save_path)
    return net

# --- Play vs human ---

PIECE_NAMES = {
    1: "♟", 2: "♟", 3: "♞", 4: "♝", 5: "♜", 6: "♜", 7: "♛", 8: "♚", 9: "♚",
    -1: "♙", -2: "♙", -3: "♘", -4: "♗", -5: "♖", -6: "♖", -7: "♕", -8: "♔", -9: "♔",
}

def format_move(move, board):
    src, dst, promote = chess2.MOVE_ARRAY[move]
    sc = chr(ord('a') + src % 8) + str(src // 8 + 1)
    dc = chr(ord('a') + dst % 8) + str(dst // 8 + 1)
    piece = PIECE_NAMES.get(board[src], "?")
    capture = "x" if board[dst] != 0 else "-"
    s = f"{piece}{sc}{capture}{dc}"
    if promote is not None:
        s += "=" + PIECE_NAMES.get(promote, "?")
    return s

def parse_human_move(text, moves, board):
    text = text.strip().lower()
    for move in moves:
        if format_move(move, board).lower().replace("♟", "").replace("♞", "n").replace("♝", "b").replace("♜", "r").replace("♛", "q").replace("♚", "k") == text:
            return move
    src_dst = text.replace("-", "").replace("x", "")
    if len(src_dst) >= 4:
        for move in moves:
            s, d, p = chess2.MOVE_ARRAY[move]
            sc = chr(ord('a') + s % 8) + str(s // 8 + 1)
            dc = chr(ord('a') + d % 8) + str(d // 8 + 1)
            if sc + dc == src_dst[:4]:
                if p is not None and len(src_dst) > 4:
                    promo_map = {'q': 7, 'r': 5, 'b': 4, 'n': 3}
                    if promo_map.get(src_dst[4]) != p:
                        continue
                return move
    return None

def play_human(model_path="chess_model.npz", depth=2, human_color="white"):
    chess2.initialize_move_map()
    net = make_net(model_path)
    game = chess2.new_game()
    ply = 0

    while True:
        chess2.print_board(game['board'])
        result = chess2.is_over(game)
        if result:
            print(result)
            break

        is_human = (human_color == "white" and ply % 2 == 0) or \
                   (human_color == "black" and ply % 2 == 1)

        moves = chess2.possible_moves(game['board'])

        if is_human:
            print("moves:", " ".join(format_move(m, game['board']) for m in moves))
            while True:
                text = input("your move: ")
                move = parse_human_move(text, moves, game['board'])
                if move is not None:
                    break
                print("invalid move, try again (e.g. e2e4)")
        else:
            move = nn_pick_move(game['board'], depth, net)
            print(f"engine: {format_move(move, game['board'])}")

        chess2.game_do_move(game, move)
        ply += 1

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "play":
        model = sys.argv[2] if len(sys.argv) > 2 else "chess_model.npz"
        play_human(model_path=model)
    else:
        model = sys.argv[1] if len(sys.argv) > 1 else None
        train(num_games=100, depth=1, model_path=model)

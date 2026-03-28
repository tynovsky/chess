#!/usr/bin/env python3

import random

# constants
ROW_SIZE = 8
BOARD_SIZE = 64
PAWN = 1
PAWN_ENPASSANT = 2
KNIGHT = 3
BISHOP = 4
ROOK = 5
ROOK_NOTMOVED = 6
QUEEN = 7
KING = 8
KING_NOTMOVED = 9
ROOK_DIRS = ((0,1),(0,-1),(1,0),(-1,0))
BISHOP_DIRS = ((1,1),(1,-1),(-1,1),(-1,-1))
KNIGHT_DIRS = ((1,2),(-1,2),(1,-2),(-1,-2),(2,1),(-2,1),(2,-1),(-2,-1))
QUEEN_DIRS = ROOK_DIRS + BISHOP_DIRS
PAWN_CAPTURE_DIRS = ((1,1),(-1,1))
BACK_ROW = [ ROOK_NOTMOVED, KNIGHT, BISHOP, QUEEN,
    KING_NOTMOVED, BISHOP, KNIGHT, ROOK_NOTMOVED ]
INIT_BOARD = BACK_ROW + [PAWN]*8 + [0]*32 + [-PAWN]*8 + [-x for x in BACK_ROW]

MOVE_MAP   = {} # to be initialized
MOVE_ARRAY = [] # to be initialized

_bkp = [[0] * BOARD_SIZE for _ in range(4)]

def find_king(board):
    for i in range(BOARD_SIZE):
        if board[i] == KING or board[i] == KING_NOTMOVED:
            return i

def flip_sides_inplace(board):
    for i in range(BOARD_SIZE // 2):
        j = BOARD_SIZE - 1 - i
        board[i], board[j] = -board[j], -board[i]

def new_game():
    board = INIT_BOARD.copy()
    return {
        'board': board,
        'positions': {tuple(board): 1},
        'halfmove_clock': 0,
    }

def is_over(game):
    board = game['board']
    if not has_sufficient_material(board):
        return "insufficient material"
    key = tuple(board)
    if game['positions'].get(key, 0) >= 3:
        return "threefold repetition"
    if game['halfmove_clock'] >= 100:
        return "50-move rule"
    moves = possible_moves(board)
    if len(moves) == 0:
        if is_king_attacked(board):
            return "checkmate"
        return "stalemate"
    return None

def game_do_move(game, move):
    board = game['board']
    src, dst, _ = MOVE_ARRAY[move]
    is_pawn = board[src] in (PAWN, PAWN_ENPASSANT)
    is_capture = board[dst] != 0

    do_move(move, board)
    board = flip_sides(board)
    game['board'] = board

    key = tuple(board)
    game['positions'][key] = game['positions'].get(key, 0) + 1

    if is_pawn or is_capture:
        game['halfmove_clock'] = 0
    else:
        game['halfmove_clock'] += 1

def possible_moves(board):
    moves = []
    for src in range(BOARD_SIZE):
        piece = board[src]
        if piece == ROOK or piece == ROOK_NOTMOVED:
            moves.extend(straight_moves(src, ROOK_DIRS, board))
            continue
        if piece == BISHOP:
            moves.extend(straight_moves(src, BISHOP_DIRS, board))
            continue
        if piece == QUEEN:
            moves.extend(straight_moves(src, QUEEN_DIRS, board))
            continue
        if piece == KNIGHT:
            moves.extend(knight_moves(src, board))
            continue
        if piece == PAWN or piece == PAWN_ENPASSANT:
            moves.extend(pawn_moves(src, board))
            continue
        if piece == KING or piece == KING_NOTMOVED:
            moves.extend(king_moves(src, board))
            continue

    king_pos = find_king(board)
    legal_moves = []
    for m in moves:
        kp = m[1] if board[m[0]] in (KING, KING_NOTMOVED) else king_pos
        b = board.copy()
        do_move(MOVE_MAP[m], b)
        if not is_attacked(kp, b):
            legal_moves.append(MOVE_MAP[m])

    return legal_moves

def is_king_attacked(b):
    king_square = None
    for i in range(BOARD_SIZE):
        if b[i] == KING or b[i] == KING_NOTMOVED:
            king_square = i
            break
    return is_attacked(king_square, b)

def straight_moves(src, dirs, board):
    dsts = []
    for horizontal, vertical in dirs:
        dsts.extend(straight_dsts_one_dir(src, horizontal, vertical, board))

    return destinations_to_moves(src, dsts, board)

def straight_dsts_one_dir(src, horizontal, vertical, board):
    dsts = []
    dst = src
    while True:
        dst = jump(dst, horizontal, vertical)
        if dst is None or board[dst] > 0: # no dst or occupied by white
            break
        dsts.append(dst)
        if board[dst] != 0: # dst occupied by black => capture
            break
    return dsts

def knight_moves(src, board):
    dsts = []
    for horizontal, vertical in KNIGHT_DIRS:
        dst = jump(src, horizontal, vertical)
        if dst is None or board[dst] > 0: # no dst or occupied by white
            continue
        dsts.append(dst)
    return destinations_to_moves(src, dsts, board)

def pawn_moves(src, board):
    dsts = []

    dst = jump(src, 0, 1)
    if dst and board[dst] == 0:
        dsts.append(dst)
        if src // 8 == 1:
            dst2 = jump(src, 0, 2)
            if dst2 is not None and board[dst2] == 0:
                dsts.append(dst2)

    for horizontal, vertical in PAWN_CAPTURE_DIRS:
        dst = jump(src, horizontal, vertical)
        if dst is None or board[dst] > 0: # no dst or occupied by white
            continue
        if board[dst] < 0: # black piece to capture
            dsts.append(dst)
        enpassant = jump(dst, 0, -1)
        if board[enpassant] == -PAWN_ENPASSANT and board[dst] == 0:
            dsts.append(dst)

    return destinations_to_moves(src, dsts, board)

def king_moves(src, board):
    dsts = []
    for horizontal, vertical in QUEEN_DIRS:
        dst = jump(src, horizontal, vertical)
        if dst is None or board[dst] > 0: # no dst or occupied by white
            continue
        dsts.append(dst)

    # castles
    if board[src] != KING_NOTMOVED or is_attacked(src, board):
        return destinations_to_moves(src, dsts, board)

    if board[0] == ROOK_NOTMOVED and \
        board[src-1] == 0 and \
        not is_attacked(src-1, board) and \
        board[src-2] == 0 and \
        board[1] == 0 and \
        not is_attacked(src-2, board):
            dsts.append(src-2)

    if board[7] == ROOK_NOTMOVED and \
        board[src+1] == 0 and \
        not is_attacked(src+1, board) and \
        board[src+2] == 0 and \
        board[6] == 0 and \
        not is_attacked(src+2, board):
            dsts.append(src+2)

    return destinations_to_moves(src, dsts, board)

def jump(src, horizontal, vertical, debug = False):
    increment = horizontal + ROW_SIZE * vertical
    dst = src + increment

    on_board = dst >= 0 and dst < BOARD_SIZE
    expected_vertical = dst % ROW_SIZE == (src % ROW_SIZE) + horizontal

    if on_board and expected_vertical:
        return dst
    else:
        return

def destinations_to_moves(src, dsts, board):
    moves = []
    for dst in dsts:
        if dst >= BOARD_SIZE - ROW_SIZE and board[src] == PAWN:
            moves.extend([
                (src, dst, QUEEN),
                (src, dst, ROOK),
                (src, dst, BISHOP),
                (src, dst, KNIGHT)
            ])
        else:
            moves.append((src, dst, None))
    return moves

def is_attacked(pos, board):
    for m in straight_moves(pos, ROOK_DIRS, board):
        piece = -board[m[1]]
        if piece == ROOK or \
            piece == ROOK_NOTMOVED or \
            piece == QUEEN:
                return True
    for m in straight_moves(pos, BISHOP_DIRS, board):
        piece = -board[m[1]]
        if piece == BISHOP or piece == QUEEN:
            return True

    for m in knight_moves(pos, board):
        piece = -board[m[1]]
        if piece == KNIGHT:
            return True

    for horizontal, vertical in PAWN_CAPTURE_DIRS:
        dst = jump(pos, horizontal, vertical)
        if dst is not None and \
            (-board[dst] == PAWN or -board[dst] == PAWN_ENPASSANT):
                return True

    for horizontal, vertical in QUEEN_DIRS:
        dst = jump(pos, horizontal, vertical)
        if dst is not None and \
            (-board[dst] == KING or -board[dst] == KING_NOTMOVED):
                return True

    return False

def flip_sides(board):
    return [-x for x in reversed(board)]

def do_move(move, board):
    src, dst, promote_to = MOVE_ARRAY[move]

    # enpassant expiration
    for i in range(BOARD_SIZE):
        if board[i] == PAWN_ENPASSANT:
            board[i] = PAWN

    if board[src] == PAWN:
        if src % ROW_SIZE != dst % ROW_SIZE and board[dst] == 0:
            assert board[dst - ROW_SIZE] == -PAWN_ENPASSANT, "enpassant"
            board[dst - ROW_SIZE] = 0

        if promote_to is not None:
            board[dst] = promote_to
        elif dst - src == 2 * ROW_SIZE:
            board[dst] = PAWN_ENPASSANT
        else:
            board[dst] = board[src]

    elif board[src] == KING_NOTMOVED:
        board[dst] = KING
        if dst - src == 2:
            assert board[7] == ROOK_NOTMOVED, "castle"
            board[dst - 1] = ROOK
            board[7] = 0
        if dst - src == -2:
            assert board[0] == ROOK_NOTMOVED, "castle"
            board[dst + 1] = ROOK
            board[0] = 0

    elif board[src] == ROOK_NOTMOVED:
        board[dst] = ROOK

    else:
        board[dst] = board[src]

    board[src] = 0

    return board

def print_board(board):
    piece = {
        0: ".",
        1: "♟", -1: "♙", 2: "♟", -2: "♙",
        3: "♞", -3: "♘",
        4: "♝", -4: "♗",
        5: "♜", -5: "♖", 6: "♜", -6: "♖",
        7: "♛", -7: "♕",
        8: "♚", -8: "♔", 9: "♚", -9: "♔"
    }

    row = ""
    for i in range(BOARD_SIZE):
        if i % 8 == 0:
            line_no = 8 - i // 8
            if line_no < 8: print(chr(ord("₁") + line_no), end=" ")
            print(row)
            row = ""
        row = piece[board[BOARD_SIZE-i-1]] + " " + row

    print("₁", end=" ")
    print(row)
    print("  ᵃ ᵇ ᶜ ᵈ ᵉ ᶠ ᵍ ʰ")

def has_sufficient_material(board):
    white_knights = 0
    white_bishops = 0
    black_knights = 0
    black_bishops = 0
    for p in board:
        a = abs(p)
        if a in [PAWN, PAWN_ENPASSANT, ROOK, ROOK_NOTMOVED, QUEEN]:
            return True
        if p ==  KNIGHT: white_knights += 1
        if p ==  BISHOP: white_bishops += 1
        if p == -KNIGHT: black_knights += 1
        if p == -BISHOP: black_bishops += 1

    if white_bishops >= 2 or black_bishops >= 2:
        return True
    if white_bishops == 1 and white_knights > 0:
        return True
    if black_bishops == 1 and black_knights > 0:
        return True
    if white_knights > 2 or black_knights > 2:
        return True

    return False

PIECE_VALUE = {
    PAWN: 100, PAWN_ENPASSANT: 100,
    KNIGHT: 300, BISHOP: 300,
    ROOK: 500, ROOK_NOTMOVED: 500,
    QUEEN: 900,
    KING: 0, KING_NOTMOVED: 0,
}

def evaluate(board):
    score = 0
    for p in board:
        if p > 0: score += PIECE_VALUE[p]
        elif p < 0: score -= PIECE_VALUE[-p]
    return score

def search(board, depth, score, alpha, beta):
    if depth == 0:
        return score, None
    moves = possible_moves(board)
    if not moves:
        if is_attacked(find_king(board), board):
            return -99999, None
        return 0, None
    best_move = moves[0]
    for move in moves:
        src, dst, promote = MOVE_ARRAY[move]
        delta = 0
        captured = board[dst]
        if captured < 0:
            delta += PIECE_VALUE[-captured]
        if board[src] in (PAWN, PAWN_ENPASSANT) and src % 8 != dst % 8 and captured == 0:
            delta += PIECE_VALUE[PAWN]
        if promote is not None:
            delta += PIECE_VALUE[promote] - PIECE_VALUE[PAWN]
        b = board.copy()
        do_move(move, b)
        s = -search(flip_sides(b), depth - 1, -(score + delta), -beta, -alpha)[0]
        if s > alpha:
            alpha = s
            best_move = move
        if alpha >= beta:
            break
    return alpha, best_move

def pick_move(board, depth, score):
    moves = possible_moves(board)
    alpha = -99999
    scored = []
    for move in moves:
        src, dst, promote = MOVE_ARRAY[move]
        delta = 0
        captured = board[dst]
        if captured < 0:
            delta += PIECE_VALUE[-captured]
        if board[src] in (PAWN, PAWN_ENPASSANT) and src % 8 != dst % 8 and captured == 0:
            delta += PIECE_VALUE[PAWN]
        if promote is not None:
            delta += PIECE_VALUE[promote] - PIECE_VALUE[PAWN]
        b = board.copy()
        do_move(move, b)
        s = -search(flip_sides(b), depth - 1, -(score + delta), -99999, -alpha)[0]
        scored.append((s, move))
        if s > alpha:
            alpha = s
    scored.sort(key=lambda x: x[0], reverse=True)
    return random.choice(scored[:3])[1]

def play():
    game = new_game()
    while True:
        result = is_over(game)
        if result:
            print(result)
            break
        score = evaluate(game['board'])
        move = pick_move(game['board'], 3, score)
        game_do_move(game, move)

def random_play():
    game = new_game()
    while True:
        result = is_over(game)
        if result:
            print(result)
            break
        moves = possible_moves(game['board'])
        move = random.choice(moves)
        game_do_move(game, move)

def initialize_move_map():
    board = [0] * BOARD_SIZE
    moves = []
    for i in range(BOARD_SIZE):
        moves.extend(straight_moves(i, QUEEN_DIRS, board))
        moves.extend(knight_moves(i, board))
    promotions = []
    for m in moves:
        if  m[0] // ROW_SIZE == 6 and \
            m[1] // ROW_SIZE == 7 and \
            abs(m[1] - ROW_SIZE - m[0]) <= 1:
                promotions.append((m[0], m[1], QUEEN))
                promotions.append((m[0], m[1], ROOK))
                promotions.append((m[0], m[1], BISHOP))
                promotions.append((m[0], m[1], KNIGHT))
    moves.extend(promotions)

    i = 0
    for m in moves:
        MOVE_MAP[m] = i
        MOVE_ARRAY.append(m)
        i += 1

def main():
    initialize_move_map()
    play()

if __name__ == "__main__":
    main()

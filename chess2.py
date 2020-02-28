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
ROOK_DIRS = [[0,1],[0,-1],[1,0],[-1,0]]
BISHOP_DIRS = [[1,1],[1,-1],[-1,1],[-1,-1]]
KNIGHT_DIRS = [[1,2],[-1,2],[1,-2],[-1,-2],[2,1],[-2,1],[2,-1],[-2,-1]]
QUEEN_DIRS = ROOK_DIRS + BISHOP_DIRS
INITIAL_BOARD = [
    ROOK_NOTMOVED, KNIGHT, BISHOP, QUEEN,
    KING_NOTMOVED, BISHOP, KNIGHT, ROOK_NOTMOVED,
    PAWN, PAWN, PAWN, PAWN, PAWN, PAWN, PAWN, PAWN,
] + [0] * 32 + [
    -PAWN, -PAWN, -PAWN, -PAWN, -PAWN, -PAWN, -PAWN, -PAWN,
    -ROOK_NOTMOVED, -KNIGHT, -BISHOP, -QUEEN,
    -KING_NOTMOVED, -BISHOP, -KNIGHT, -ROOK_NOTMOVED,
]

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

    legal_moves = []
    for m in moves:
        b = board.copy()
        do_move(m, b)
        king_square = None
        for i in range(BOARD_SIZE):
            if b[i] == KING or b[i] == KING_NOTMOVED:
                king_square = i
                break
        if not is_attacked(king_square, b):
            legal_moves.append(m)

    return legal_moves

def straight_moves(src, dirs, board):
    dsts = []
    for d in dirs:
        dsts.extend(straight_dsts_one_dir(src, d, board))

    return destinations_to_moves(src, dsts, board)

def straight_dsts_one_dir(src, d, board):
    dsts = []
    dst = src
    while True:
        dst = jump(dst, d[0], d[1])
        if dst is None or board[dst] > 0: # no dst or occupied by white
            break
        dsts.append(dst)
        if board[dst] != 0: # dst occupied by black => capture
            break
    return dsts

def knight_moves(src, board):
    dsts = []
    for d in KNIGHT_DIRS:
        dst = jump(src, d[0], d[1])
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
        dst = jump(src, 0, 2)
        if dst is not None and board[dst] == 0:
            dsts.append(dst)

    capture_dirs = [[1,1],[-1,1]]
    for d in capture_dirs:
        dst = jump(src, d[0], d[1])
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
    for d in QUEEN_DIRS:
        dst = jump(src, d[0], d[1])
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
    correct_horizontal = dst %  ROW_SIZE == (src %  ROW_SIZE) + horizontal
    correct_vertical   = dst // ROW_SIZE == (src // ROW_SIZE) + vertical

    if on_board and correct_vertical and correct_vertical:
        return dst
    else:
        return

def destinations_to_moves(src, dsts, board):
    moves = []
    for dst in dsts:
        if dst >= BOARD_SIZE - ROW_SIZE and board[src] == PAWN:
            moves.extend([
                [src, dst, QUEEN],
                [src, dst, ROOK],
                [src, dst, BISHOP],
                [src, dst, KNIGHT]
            ])
        else:
            moves.append([src, dst, None])
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

    capture_dirs = [[1,1],[-1,1]]
    for d in capture_dirs:
        dst = jump(pos, d[0], d[1])
        if dst is not None and -board[dst] == PAWN:
            return True

    for d in QUEEN_DIRS:
        dst = jump(pos, d[0], d[1])
        if dst is not None and (-board[dst] == KING or -board[dst] == KING_NOTMOVED):
            return True

    return False

def flip_sides(board):
    return [-x for x in reversed(board)]

def do_move(move, board):
    src, dst, promote_to = move[:]

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
            line_no = 9 - i // 8
            if line_no < 9: print(chr(ord("₁") + line_no), end=" ")
            print(row)
            row = ""
        row = piece[board[BOARD_SIZE-i-1]] + " " + row

    print(1, end=" ")
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

def main():
    board = INITIAL_BOARD
    c = 0
    while True:
        if not has_sufficient_material(board):
            print("insufficient material")
            break
        moves = possible_moves(board)
        if len(moves) == 0:
            print("checkmate / stalemate")
            break
        move = random.choice(moves)
        do_move(move, board)
        if c % 2 == 0: print(c//2+1); print_board(board)
        board = flip_sides(board)
        if c % 2 == 1: print_board(board)
        c += 1

if __name__ == "__main__":
    main()

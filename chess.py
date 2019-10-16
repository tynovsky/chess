#!/usr/bin/env python3

from enum import IntEnum
from termcolor import colored, cprint
from pprint import pprint
import random
import time

class Board:
    def __init__(self, size, pieces):
        self.grid = []
        self.size = size
        self.shadow = None
        for i in range(0, size):
            self.grid.append([])
            for j in range(0, size):
                self.grid[i].append(None)
        for piece in pieces:
            self.grid[piece.square.x][piece.square.y] = piece
            piece.board = self
        self.cache = {}

    def draw(self):
        for j in range(self.size - 1, -1, -1):
            print(chr(ord("₁")+j), end=' ')
            for i in range(0, self.size):
                piece = self.grid[i][j]
                square_color = 'grey' if (i + j)%2==0 else 'white'
                if piece is None:
                    #cprint("■ ", square_color, end='')
                    cprint("· ", square_color, end='')
                else:
                    print(str(piece) + " ", end='')
            print()
        print("  ᵃ ᵇ ᶜ ᵈ ᵉ ᶠ ᵍ ʰ")

    def __str__(self):
        s = ''
        for j in range(self.size -1, -1, -1):
            for i in range(0, self.size):
                piece = self.grid[i][j]
                s += str(piece)
        return s

    def valid_square(self, square):
        return square.x >= 0 and square.x < self.size and square.y >= 0 and square.y < self.size

    def get_piece(self, square):
        return self.grid[square.x][square.y]

    def do_move(self, move):
        move.piece.moved += 1
        shadow = move.shadow_removed = self.shadow
        self.shadow = move.shadow_added

        if move.promote_to:
            self.grid[move.start.x][move.start.y] = None
            self.grid[move.end.x][move.end.y] = move.promote_to
            return

        self.grid[move.start.x][move.start.y] = None
        move.piece.square = move.end
        if move.captured_piece:
            self.grid[move.captured_piece.square.x][move.captured_piece.square.y] = None
        self.grid[move.end.x][move.end.y] = move.piece

        if move.castle == "short":
            rook = self.grid[7][move.start.y]
            rook.square.x = 5
            self.grid[7][move.start.y] = None
            self.grid[5][move.start.y] = rook
        if move.castle == "long":
            rook = self.grid[0][move.start.y]
            rook.square.x = 3
            self.grid[0][move.start.y] = None
            self.grid[3][move.start.y] = rook

    def undo_move(self, move):
        move.piece.moved -= 1
        self.shadow = move.shadow_removed
        move.piece.square = move.start
        self.grid[move.start.x][move.start.y] = move.piece
        self.grid[move.end.x][move.end.y] = None

        if move.captured_piece:
            self.grid[move.captured_piece.square.x][move.captured_piece.square.y] = move.captured_piece

        if move.castle == "short":
            rook = self.grid[5][move.start.y]
            rook.square.x = 7
            self.grid[5][move.start.y] = None
            self.grid[7][move.start.y] = rook

        if move.castle == "long":
            rook = self.grid[3][move.start.y]
            rook.square.x = 0
            self.grid[3][move.start.y] = None
            self.grid[0][move.start.y] = rook

    def get_pieces(self):
        for row in self.grid:
            for piece in row:
                if piece is not None:
                    yield piece

    def get_king(self, color):
        for p in self.get_pieces():
            if p.is_king() and p.color == color:
                return p

    def possible_moves(self, color):
        key = str(color) + str(self) + str(self.shadow)
        if key in self.cache:
            return self.cache[key]
        moves = []

        for piece in self.get_pieces():
            if piece.color != color:
                continue
            for m in piece.possible_moves():
                self.do_move(m)
                king = self.get_king(color)
                if not king.is_in_check():
                    moves.append(m)
                self.undo_move(m)
        self.cache[key] = moves
        return moves

class Game:
    def __init__(self, board, onturn):
        self.board = board
        self.onturn = onturn
        self.position_count = {}

    def possible_moves(self):
        return self.board.possible_moves(self.onturn)

    def do_move(self, move):
        self.board.do_move(move)
        self.onturn = -self.onturn
        # self.position_count[self.serialize_position()] += 1

    def undo_move(self, move):
        # self.position_count[self.serialize_position()] -= 1
        self.board.undo_move(move)
        self.onturn = -self.onturn

    def is_checkmate(self):
        king = self.board.get_king(self.onturn)
        if not king.is_in_check():
            return False
        possible_moves = list(self.possible_moves())
        if len(possible_moves) > 0:
            return False
        return True

    def is_stalemate(self):
        possible_moves = list(self.possible_moves())
        if len(possible_moves) > 0:
            return False
        king = self.board.get_king(self.onturn)
        if king.is_in_check():
            return False
        return True

    # def is_repetition(self):
    #     if self.position_count[self.serialize_position()] > 3:
    #         return True
    #     return False

    def is_over(self):
        possible_moves = list(self.possible_moves())

        if len(possible_moves) == 0:
            return True
        pieces = self.board.get_pieces()
        white_knights = 0
        white_bishops = 0
        black_knights = 0
        black_bishops = 0
        for p in pieces:
            if p.is_queen():
                return False
            if p.is_rook():
                return False
            if p.is_pawn():
                return False
            if p.is_knight():
                if p.color == Color.WHITE:
                    white_knights += 1
                else:
                    black_knights += 1
            if p.is_bishop():
                if p.color == Color.WHITE:
                    white_bishops += 1
                else:
                    black_bishops += 1
        if white_bishops >= 2 or black_bishops >= 2:
            return False
        if white_bishops == 1 and white_knights > 0:
            return False
        if black_bishops == 1 and black_knights > 0:
            return False

        return True

class Color(IntEnum):
    WHITE = 1
    BLACK = -1

class Square:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    @classmethod
    def from_notation(cls, notation):
        notes = list(notation)
        x = ord(notes[0]) - ord("a")
        y = int(notes[1]) - 1
        return cls(x, y)

    def __add__(self, t):
        return Square(self.x + t[0], self.y + t[1])

    def __sub__(self, t):
        return Square(self.x - t[0], self.y - t[1])

    def __eq__(self, c):
        return self.x == c.x and self.y == c.y

    def t(self):
        return (self.x, self.y)

    def __str__(self):
        x = chr(ord('a') + self.x)
        y = str(self.y + 1)
        return str(x + y)

class Move:
    def __init__(self, piece, end, captured_piece=None, promote_to=None, shadow = None, en_passant = False, castle = None):
        self.piece = piece
        self.start = piece.square
        self.end = end
        self.captured_piece = captured_piece
        self.promote_to = promote_to
        self.shadow_added = shadow
        self.shadow_removed = None
        self.castle = castle

    def __str__(self):
        if self.castle == "short":
            return "O-O"
        if self.castle == "long":
            return "O-O-O"
        moves_or_takes = "x" if self.captured_piece is not None else "-"
        move = str(self.piece) + str(self.start) + moves_or_takes + str(self.end)
        if self.promote_to is not None:
            move += " -> " + str(self.promote_to)
        return move

class Piece:
    def __init__(self, color, square, board=None):
        self.color = color
        self.square = square
        self.board = board
        self.moved = 0
        self.dir_vectors = {
            "up":         tuple(color * x for x in (0, 1)),
            "down":       tuple(color * x for x in (0, -1)),
            "left":       tuple(color * x for x in (-1, 0)),
            "right":      tuple(color * x for x in (1, 0)),
            "up_left":    tuple(self.color * x for x in (-1, 1)),
            "up_right":   tuple(self.color * x for x in (1, 1)),
            "down_left":  tuple(self.color * x for x in (-1, -1)),
            "down_right": tuple(self.color * x for x in (1, -1)),
        }

    def direction(self, vector_name):
        v = self.dir_vectors[vector_name]
        c = self.square + v
        while self.board.valid_square(c):
            yield c
            c += v

    def row(self):
        if self.color == Color.WHITE:
            return self.square.y
        else:
            return self.board.size - self.square.y -1

    def col(self):
        if self.color == Color.WHITE:
            return self.square.x
        else:
            return self.board.size - self.square.x - 1

    def possible_captures(self):
        for c in self.candidate_captures():
            piece = self.board.get_piece(c)
            if piece is not None and piece.color != self.color:
                yield Move(piece = self, end = c, captured_piece = piece)

    def possible_noncaptures(self):
        for c in self.candidate_noncaptures():
            piece = self.board.get_piece(c)
            if piece is None:
                yield Move(piece = self, end = c)

    def candidate_captures(self):
        for d in self.directions:
            for c in self.direction(d):
                if self.board.get_piece(c) is not None:
                    yield c
                    break

    def candidate_noncaptures(self):
        for d in self.directions:
            for c in self.direction(d):
                if self.board.get_piece(c) is not None:
                    break
                yield c

    def possible_moves(self):
        for c in self.possible_captures():
            yield c
        for n in self.possible_noncaptures():
            yield n

    def is_king(self):
        return False

    def is_queen(self):
        return False

    def is_rook(self):
        return False

    def is_bishop(self):
        return False

    def is_knight(self):
        return False

    def is_pawn(self):
        return False


class Pawn(Piece):
    def possible_captures(self):
        for d in ["up_left", "up_right"]:
            end = self.square + self.dir_vectors[d]
            if not self.board.valid_square(end):
                continue
            if self.board.shadow and end == self.board.shadow:
                captured_piece = self.board.get_piece(end + self.dir_vectors["down"])
                yield Move(piece = self, end = end, captured_piece = captured_piece)
            captured_piece = self.board.get_piece(end)
            if captured_piece is None:
                continue
            if captured_piece.color == self.color:
                continue
            if self.row() == 6:
                for p in [Queen, Rook, Bishop, Knight]:
                    yield Move(
                        piece = self,
                        end = end,
                        promote_to = p(self.color, end, board = self.board),
                        captured_piece = captured_piece,
                    )
            else:
                yield Move(piece = self, end = end, captured_piece = captured_piece)

    def possible_noncaptures(self):
        up = list(self.direction("up"))
        if self.board.get_piece(up[0]) is not None:
            return
        if self.row() == 1:
            yield Move(piece = self, end = up[0])
            if self.board.get_piece(up[1]) is None:
                yield Move(piece = self, end = up[1], shadow = up[0])
        elif self.row() == 6:
            for p in [Queen, Rook, Bishop, Knight]:
                yield Move(
                    piece = self,
                    end = up[0],
                    promote_to = p(self.color, up[0], board = self.board),
                )
        else:
            yield Move(piece = self, end = up[0])

    def __str__(self):
        return "♟" if self.color == Color.WHITE else "♙"

    def is_pawn(self):
        return True

class Rook(Piece):
    directions = ["up", "down", "left", "right"]

    def __str__(self):
        return "♜" if self.color == Color.WHITE else "♖"

    def is_rook(self):
        return True

class Bishop(Piece):
    directions = ["up_left", "up_right", "down_left", "down_right"]

    def __str__(self):
        return "♝" if self.color == Color.WHITE else "♗"

    def is_bishop(self):
        return True

class Queen(Piece):
    directions = ["up", "down", "left", "right", "up_left", "up_right", "down_left", "down_right"]

    def __str__(self):
        return "♛" if self.color == Color.WHITE else "♕"

    def is_queen(self):
        return True

class King(Piece):
    directions = ["up", "down", "left", "right", "up_left", "up_right", "down_left", "down_right"]

    def __init__(self, color, square, board=None):
        super().__init__(color, square, board)
        self.mirror_figures = [ kind(self.color, self.square) for kind in [Queen, Rook, Knight, Bishop, Pawn] ]

    def candidate_captures(self):
        for d in self.directions:
            c = self.square + self.dir_vectors[d]
            if self.board.valid_square(c):
                yield c

    def candidate_noncaptures(self):
        return self.candidate_captures()

    def possible_noncaptures(self):
        for m in super().possible_noncaptures():
            yield m

        if self.moved > 0:
            return

        for m in self.short_castle():
            yield m

        for m in self.long_castle():
            yield m

    def short_castle(self):
        # print(self)
        rook_square = Square(7, self.square.y)
        rook = self.board.get_piece(rook_square)
        if not rook:
            return
        if not rook.is_rook():
            return
        if rook.moved > 0:
            return

        for x in [5, 6]:
            square = Square(x, self.square.y)
            piece = self.board.get_piece(square)
            if piece is not None:
                return

        for x in [4, 5, 6]:
            if self.is_attacked( Square(x, self.square.y) ):
                return

        yield Move(piece = self, end = Square(6, self.square.y), castle = "short")

    def long_castle(self):
        rook_square = Square(0, self.square.y)
        rook = self.board.get_piece(rook_square)
        if not rook:
            return
        if not rook.is_rook():
            return
        if rook.moved > 0:
            return

        for x in [1, 2, 3]:
            square = Square(x, self.square.y)
            piece = self.board.get_piece(square)
            if piece is not None:
                return

        for x in [2, 3, 4]:
            if self.is_attacked( Square(x, self.square.y) ):
                return

        yield Move(piece = self, end = Square(2, self.square.y), castle = "long")

    def __str__(self):
        return "♚" if self.color == Color.WHITE else "♔"

    def is_king(self):
        return True

    def is_in_check(self):
        if self.is_attacked(self.square):
            return True

        for c in self.possible_captures():
            if type(c.captured_piece) is King:
                return True

        return False

    def is_attacked(self, square):
        for p in self.mirror_figures:
            p.square = square
            p.board = self.board
            captures = p.possible_captures()
            for c in captures:
                if type(c.captured_piece) is type(p):
                    return True


class Knight(Piece):
    def candidate_captures(self):
        for v in [(1, 2), (-1, 2), (1, -2), (-1, -2), (2, 1), (-2, 1), (2, -1), (-2, -1)]:
            c = self.square + v
            if self.board.valid_square(c):
                yield c

    def candidate_noncaptures(self):
        return self.candidate_captures()

    def __str__(self):
        return "♞" if self.color == Color.WHITE else "♘"

    def is_knight(self):
        return True

def init_game():
    white = Color.WHITE
    black = Color.BLACK

    pieces = [
        Rook(white, Square.from_notation("a1")),
        Rook(white, Square.from_notation("h1")),
        Knight(white, Square.from_notation("b1")),
        Knight(white, Square.from_notation("g1")),
        Bishop(white, Square.from_notation("c1")),
        Bishop(white, Square.from_notation("f1")),
        Queen(white, Square.from_notation("d1")),
        King(white, Square.from_notation("e1")),
        Pawn(white, Square.from_notation("a2")),
        Pawn(white, Square.from_notation("b2")),
        Pawn(white, Square.from_notation("c2")),
        Pawn(white, Square.from_notation("d2")),
        Pawn(white, Square.from_notation("e2")),
        Pawn(white, Square.from_notation("f2")),
        Pawn(white, Square.from_notation("g2")),
        Pawn(white, Square.from_notation("h2")),

        Rook(black, Square.from_notation("a8")),
        Rook(black, Square.from_notation("h8")),
        Knight(black, Square.from_notation("b8")),
        Knight(black, Square.from_notation("g8")),
        Bishop(black, Square.from_notation("c8")),
        Bishop(black, Square.from_notation("f8")),
        Queen(black, Square.from_notation("d8")),
        King(black, Square.from_notation("e8")),
        Pawn(black, Square.from_notation("a7")),
        Pawn(black, Square.from_notation("b7")),
        Pawn(black, Square.from_notation("c7")),
        Pawn(black, Square.from_notation("d7")),
        Pawn(black, Square.from_notation("e7")),
        Pawn(black, Square.from_notation("f7")),
        Pawn(black, Square.from_notation("g7")),
        Pawn(black, Square.from_notation("h7")),
    ]
    board = Board(size=8, pieces=pieces)
    game = Game(board=board, onturn=white)
    return game

def pick_move(game, candidates):
    for m in candidates:
        game.do_move(m)
        if game.is_checkmate():
            game.undo_move(m)
            return m
        game.undo_move(m)
    return random.choice(candidates)

def test():
    # random.seed("sedi bubak na dubu")
    game = init_game()

    move_count = 0
    while True:
        move_count += 1
        if game.is_over():
            break

        possible_moves = list(game.possible_moves())
        move = pick_move(game, possible_moves)

        game.board.draw()
        print("-----------------")
        if move_count % 2 == 0:
            print("%d. ... %s" % (move_count / 2, str(move)))
        else:
            print("%d. %s" % ((move_count + 1) / 2, str(move)))
        game.do_move(move)

    game.board.draw()

if __name__ == "__main__":
    test()

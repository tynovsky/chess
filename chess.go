package main

import (
	"fmt"
)

const Size int8 = 8


type Color int8
const White Color = 1
const Black Color = -1


type Board struct {
	Grid [Size][Size]*Piece
	Shadow Square
}

func (b *Board) GetPiece(s *Square) *Piece {
	return b.Grid[s.x][s.y]
}

func (b *Board) doMove(m *Move) {
}

func (b *Board) undoMove(m *Move) {
}

func (b *Board) getPieces() []*Piece {
	return []*Piece{}
}

func (b *Board) getKing(c Color) *King {
	return &King{}
}

func (b *Board) possibleMoves() []*Move {
	return []*Move{}
}

func (b *Board) possibleMoveCandidates() []*Move {
	return []*Move{}
}

func (b *Board) possibleMoveCandidatesWithoutKing() []*Move {
	return []*Move{}
}


type Square struct {
	x int8
	y int8
}

func (s *Square) IsValid() bool {
	return s.x >= 0 && s.y >= 0 && s.x < Size && s.y < Size
}

func (s *Square) AddVector(v *Vector) *Square {
	return &Square{x: s.x + v.x, y: s.y + v.y}
}

type Vector struct {
	x int8
	y int8
}

type DirectionName int8
const (
	Up DirectionName = iota
	Down
	Left
	Right
	UpLeft
	UpRight
	DownLeft
	DownRight
)

var DirVectors map[Color]map[DirectionName]Vector = map[Color]map[DirectionName]Vector {
	White: map[DirectionName]Vector {
		Up: Vector{x: 0, y: 1},
		Down: Vector{x: 0, y: -1},
		Left: Vector{x: -1, y: 0},
		Right: Vector{x: 1, y: 0},
		UpLeft: Vector{x: -1, y: 1},
		UpRight: Vector{x: 1, y: 1},
		DownLeft: Vector{x: -1, y: -1},
		DownRight: Vector{x: 1, y: -1},
	},
	Black: map[DirectionName]Vector {
		Up: Vector{x: 0, y: -1},
		Down: Vector{x: 0, y: 1},
		Left: Vector{x: 1, y: 0},
		Right: Vector{x: -1, y: 0},
		UpLeft: Vector{x: 1, y: -1},
		UpRight: Vector{x: -1, y: -1},
		DownLeft: Vector{x: 1, y: 1},
		DownRight: Vector{x: -1, y: 1},
	},
}

type PieceBase struct {
	Color Color
	Square *Square
	Board *Board
	MoveCounter int
}

type Piece interface {
	Direction(DirectionName) []*Square
	Row() int8
	PossibleCaptures() []*Move
	CandidateCaptures() []*Move
	PossibleNonCaptures() []*Move
	CandidateNonCaptures() []*Move
}

func (p *PieceBase) Direction(directionName DirectionName) []*Square {
	v := DirVectors[p.Color][directionName]
	squares := make([]*Square, 0, 8)
	s := p.Square.AddVector(&v)
	for s.IsValid() {
		squares = append(squares, s)
	}
	return squares
}

func (p *PieceBase) Row() int8 {
	if p.Color == White {
		return p.Square.y
	} else {
		return Size - p.Square.y
	}
}

func (p *PieceBase) PossibleCaptures() []*Move {
	candidates := p.CandidateCaptures()
	moves := make([]*Move, 0, 8)
	for i := 0; i < len(candidates); i++ {
		c := candidates[i]
		capturedPiece := p.Board.GetPiece(c)
		if capturedPiece != nil && capturedPiece.Color != p.Color {
			m := Move {
				Piece: p,
				End: c,
				CapturedPiece: capturedPiece,
			}
			moves = append(moves, &m)
		}
	}
	return moves
}

type King struct {
	Piece
}


type Move struct {
	Piece *Piece
	End *Square
	CapturedPiece *Piece
}



func main() {
	fmt.Println("a")
}

package main

import (
	"fmt"
)

const Size int8 = 8


type Color int8
const White Color = 1
const Black Color = -1


type Board struct {
	Grid [Size][Size]Piece
	Shadow Square
}

func (b *Board) GetPiece(s *Square) Piece {
	return b.Grid[s.x][s.y]
}

func (b *Board) doMove(m *Move) {
}

func (b *Board) undoMove(m *Move) {
}

func (b *Board) setPieces(pieces []Piece) {
	for i := 0; i < len(pieces); i++ {
		p := pieces[i]
		sq := p.Square()
		b.Grid[sq.x][sq.y] = p
	}
}

func (b *Board) getPieces() []Piece {
	return []Piece{}
}

func (b *Board) getKing(c Color) *King {
	return &King{}
}

func (b *Board) possibleMoves() []*Move {
	return []*Move{}
}

func (b *Board) Print() {
	for i := Size - 1; i >= 0; i-- {
		for j := Size - Size; j < Size; j++ {
			piece := b.Grid[i][j]
			if piece == nil {
				fmt.Print(". ")
				continue
			}
			piece.Print()
		}
		fmt.Println()
	}
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

func (s *Square) Direction(color Color, directionName DirectionName) []*Square {
	v := DirVectors[color][directionName]
	squares := make([]*Square, 0, 8)
	sq := s.AddVector(&v)
	for sq.IsValid() {
		squares = append(squares, sq)
		sq = sq.AddVector(&v)
	}
	return squares
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

// Rook, Knight, Bishop, Queen, King or Pawn
type PieceBase struct {
	color Color
	square *Square
	board *Board
	moveCounter int
}

func (p *PieceBase) Color() Color {
	return p.color
}

func (p *PieceBase) Board() *Board {
	return p.board
}

func (p *PieceBase) Square() *Square {
	return p.square
}

func (p *PieceBase) Row() int8 {
	if p.color == White {
		return p.square.y
	} else {
		return Size - p.square.y
	}
}


// Rook, Bishop or Queen
type StraightGoer struct {
	PieceBase
}

func (sg *StraightGoer) CandidateCaptures(directions []DirectionName) []*Square {
	candidates := []*Square{}
	for i := 0; i < len(directions); i++ {
		d := directions[i]
		squares := sg.square.Direction(sg.Color(), d)
		for j := 0; j < len(squares); j++ {
			c := squares[j]
			if sg.board.GetPiece(squares[j]) != nil {
				candidates = append(candidates, c)
				break
			}
		}
	}
	return candidates
}

func (sg *StraightGoer) CandidateNonCaptures(directions []DirectionName) []*Square {
	candidates := []*Square{}
	for i := 0; i < len(directions); i++ {
		d := directions[i]
		squares := sg.square.Direction(sg.Color(), d)
		for j := 0; j < len(squares); j++ {
			c := squares[j]
			if sg.board.GetPiece(squares[j]) != nil {
				break
			}
			candidates = append(candidates, c)
		}
	}
	return candidates
}

type Piece interface {
	PossibleMoves() []*Move
	Print()
	Board() *Board
	Color() Color
	Square() *Square
}

func PossibleCaptures(p Piece, candidates []*Square) []*Move {
	captures := []*Move{}
	for i := 0; i < len(candidates); i++ {
		c := candidates[i]
		piece := p.Board().GetPiece(c)
		if piece == nil || piece.Color() == p.Color() {
			continue
		}
		m := Move {
			Piece: p,
			End: c,
			CapturedPiece: piece,
		}
		captures = append(captures, &m)
	}
	return captures
}

func PossibleNonCaptures(p Piece, candidates []*Square) []*Move {
	noncaptures := []*Move{}
	for i := 0; i < len(candidates); i++ {
		c := candidates[i]
		piece := p.Board().GetPiece(c)
		if piece != nil {
			continue
		}
		noncaptures = append(noncaptures, &Move{ Piece: p, End: c })
	}
	return noncaptures
}

type King struct {
	PieceBase
}

func (k *King) PossibleMoves() []*Move {
	moves := []*Move{}
	dirs := []DirectionName{Up, Down, Left, Right, UpLeft, UpRight, DownLeft, DownRight}
	for i := 0; i < len(dirs); i++ {
		vector := DirVectors[k.color][dirs[i]]
		end := k.square.AddVector(&vector)
		if !end.IsValid() {
			continue
		}
		piece := k.board.GetPiece(end)
		if piece != nil && piece.Color() == k.color {
			continue
		}
		m := &Move{ Piece: k, End: end }
		if piece == nil {
			moves = append(moves, m)
			continue
		}
		m.CapturedPiece = piece
		moves = append(moves, m)
	}
	//TODO castles
	return moves
}

func (k *King) Print() {
	if k.color == White {
		fmt.Print("k ")
	} else {
		fmt.Print("K ")
	}
}


type Knight struct {
	PieceBase
}

func (n *Knight) PossibleMoves() []*Move {
	moves := []*Move{}
	vectors := []Vector {
		Vector{x: 1, y: 2},
		Vector{x: -1, y: 2},
		Vector{x: 1, y: -2},
		Vector{x: -1, y: -2},
		Vector{x: 2, y: 1},
		Vector{x: -2, y: 1},
		Vector{x: 2, y: -1},
		Vector{x: -2, y: -1},
	}
	for i := 0; i < len(vectors); i++ {
		vector := vectors[i]
		end := n.square.AddVector(&vector)
		if !end.IsValid() {
			continue
		}
		piece := n.board.GetPiece(end)
		if piece != nil && piece.Color() == n.color {
			continue
		}
		m := &Move{ Piece: n, End: end }
		if piece == nil {
			moves = append(moves, m)
			continue
		}
		m.CapturedPiece = piece
		moves = append(moves, m)
	}
	return moves
}

func (n *Knight) Print() {
	if n.color == White {
		fmt.Print("n ")
	} else {
		fmt.Print("N ")
	}
}


type Pawn struct {
	PieceBase
}

func (p *Pawn) PossibleMoves() []*Move {
	captures := p.PossibleCaptures()
	noncaptures := p.PossibleNonCaptures()
	return append(captures, noncaptures...)
}

func (p *Pawn) PossibleNonCaptures() []*Move {
	noncaptures := []*Move{}
	vector := DirVectors[p.color][Up]
	end := p.square.AddVector(&vector)
	if !end.IsValid() {
		return noncaptures
	}
	if piece := p.board.GetPiece(end); piece != nil {
		return noncaptures
	}

	m := &Move{ Piece: p, End: end }
	if p.Row() == 1 {
		noncaptures = append(noncaptures, m)
		end = end.AddVector(&vector)
		if piece := p.board.GetPiece(end); piece != nil {
			return noncaptures
		}
		m = &Move{ Piece: p, End: end }
		return append(noncaptures, m)
	}
	if p.Row() == 6 {
		queen := &Queen{ StraightGoer{ PieceBase {color: p.color, square: end, board: p.board }}}
                m = &Move{
			Piece: p,
			End: end,
			PromoteTo: queen,
		}
		//TODO: other promotions
		return append(noncaptures, m)
	}
	return append(noncaptures, m)
}

func (p *Pawn) PossibleCaptures() []*Move {
	captures := []*Move{}
	dirs := []DirectionName{UpLeft, UpRight}
	for i := 0; i < len(dirs); i++ {
		vector := DirVectors[p.color][dirs[i]]
		end := p.square.AddVector(&vector)
		if !end.IsValid() {
			continue
		}
		//TODO: en-passant
		capturedPiece := p.board.GetPiece(end)
		if capturedPiece == nil || capturedPiece.Color() == p.color {
			continue
		}
		if p.Row() == 6 {
			queen := &Queen{ StraightGoer{ PieceBase {color: p.color, square: end, board: p.board }}}
			m := &Move{
				Piece: p,
				End: end,
				CapturedPiece: capturedPiece,
				PromoteTo: queen,
			}
			//TODO: other promotions
			captures = append(captures, m)
		} else {
			m := &Move{
				Piece: p,
				End: end,
				CapturedPiece: capturedPiece,
			}
			captures = append(captures, m)
		}
	}
	return captures
}

func (p *Pawn) Print() {
	if p.color == White {
		fmt.Print("p ")
	} else {
		fmt.Print("P ")
	}
}


type Rook struct {
	StraightGoer
}

func (r *Rook) PossibleMoves() []*Move {
	directionNames := []DirectionName{Up, Down, Left, Right}
	captures := PossibleCaptures(r, r.CandidateCaptures(directionNames))
	noncaptures := PossibleNonCaptures(r, r.CandidateNonCaptures(directionNames))
	return append(captures, noncaptures...)
}

func (r *Rook) Print() {
	if r.color == White {
		fmt.Print("r ")
	} else {
		fmt.Print("R ")
	}
}

type Bishop struct {
	StraightGoer
}

func (b *Bishop) PossibleMoves() []*Move {
	directionNames := []DirectionName{UpLeft, UpRight, DownLeft, DownRight}
	captures := PossibleCaptures(b, b.CandidateCaptures(directionNames))
	noncaptures := PossibleNonCaptures(b, b.CandidateNonCaptures(directionNames))
	moves := captures
	moves = append(moves, noncaptures...)
	return moves
}

func (b *Bishop) Print() {
	if b.color == White {
		fmt.Print("b ")
	} else {
		fmt.Print("B ")
	}
}

type Queen struct {
	StraightGoer
}

func (q *Queen) PossibleMoves() []*Move {
	directionNames := []DirectionName{Up, Down, Left, Right, UpLeft, UpRight, DownLeft, DownRight}
	captures := PossibleCaptures(q, q.CandidateCaptures(directionNames))
	noncaptures := PossibleNonCaptures(q, q.CandidateNonCaptures(directionNames))
	moves := captures
	moves = append(moves, noncaptures...)
	return moves
}

func (q *Queen) Print() {
	if q.color == White {
		fmt.Print("q ")
	} else {
		fmt.Print("Q ")
	}
}

type Move struct {
	Piece Piece
	End *Square
	CapturedPiece Piece
	PromoteTo Piece
}

func InitBoard() *Board {
	board := &Board{}
	pieces := []Piece{
		&Rook{ StraightGoer{ PieceBase {color: White, square: &Square{x: 0, y: 0}, board: board }}},
		&Rook{ StraightGoer{ PieceBase {color: White, square: &Square{x: 0, y: 7}, board: board }}},
		&Bishop{ StraightGoer{ PieceBase {color: White, square: &Square{x: 0, y: 2}, board: board }}},
		&Bishop{ StraightGoer{ PieceBase {color: White, square: &Square{x: 0, y: 5}, board: board }}},
		&Queen{ StraightGoer{ PieceBase {color: White, square: &Square{x: 0, y: 3}, board: board }}},
		&Knight{ PieceBase {color: White, square: &Square{x: 0, y: 1}, board: board }},
		&Knight{ PieceBase {color: White, square: &Square{x: 0, y: 6}, board: board }},
		&King{ PieceBase {color: White, square: &Square{x: 0, y: 4}, board: board }},
		&Pawn{ PieceBase {color: White, square: &Square{x: 1, y: 0}, board: board }},
		&Pawn{ PieceBase {color: White, square: &Square{x: 1, y: 1}, board: board }},
		&Pawn{ PieceBase {color: White, square: &Square{x: 1, y: 2}, board: board }},
		&Pawn{ PieceBase {color: White, square: &Square{x: 1, y: 3}, board: board }},
		&Pawn{ PieceBase {color: White, square: &Square{x: 1, y: 4}, board: board }},
		&Pawn{ PieceBase {color: White, square: &Square{x: 1, y: 5}, board: board }},
		&Pawn{ PieceBase {color: White, square: &Square{x: 1, y: 6}, board: board }},
		&Pawn{ PieceBase {color: White, square: &Square{x: 1, y: 7}, board: board }},

		&Rook{ StraightGoer{ PieceBase {color: Black, square: &Square{x: 7, y: 0}, board: board }}},
		&Rook{ StraightGoer{ PieceBase {color: Black, square: &Square{x: 7, y: 7}, board: board }}},
		&Bishop{ StraightGoer{ PieceBase {color: Black, square: &Square{x: 7, y: 2}, board: board }}},
		&Bishop{ StraightGoer{ PieceBase {color: Black, square: &Square{x: 7, y: 5}, board: board }}},
		&Queen{ StraightGoer{ PieceBase {color: Black, square: &Square{x: 7, y: 3}, board: board }}},
		&Knight{ PieceBase {color: Black, square: &Square{x: 7, y: 1}, board: board }},
		&Knight{ PieceBase {color: Black, square: &Square{x: 7, y: 6}, board: board }},
		&King{ PieceBase {color: Black, square: &Square{x: 7, y: 4}, board: board }},
		&Pawn{ PieceBase {color: Black, square: &Square{x: 6, y: 0}, board: board }},
		&Pawn{ PieceBase {color: Black, square: &Square{x: 6, y: 1}, board: board }},
		&Pawn{ PieceBase {color: Black, square: &Square{x: 6, y: 2}, board: board }},
		&Pawn{ PieceBase {color: Black, square: &Square{x: 6, y: 3}, board: board }},
		&Pawn{ PieceBase {color: Black, square: &Square{x: 6, y: 4}, board: board }},
		&Pawn{ PieceBase {color: Black, square: &Square{x: 6, y: 5}, board: board }},
		&Pawn{ PieceBase {color: Black, square: &Square{x: 6, y: 6}, board: board }},
		&Pawn{ PieceBase {color: Black, square: &Square{x: 6, y: 7}, board: board }},
	}
	board.setPieces(pieces)
	return board
}

func main() {
	board := InitBoard()
        board.Print()
}

package main

import (
	"fmt"
	"math/rand"
	"time"
)

const Size int8 = 8

type Color int8
const White Color = 1
const Black Color = -1

type Game struct {
	Board *Board
	OnTurn Color
}

func (g *Game) possibleMoves() []*Move {
	return g.Board.possibleMoves(g.OnTurn)
}

func (g *Game) doMove(move *Move) {
	g.Board.doMove(move)
	g.OnTurn = -g.OnTurn
}

func (g *Game) undoMove(move *Move) {
	g.Board.undoMove(move)
	g.OnTurn = -g.OnTurn
}

type Board struct {
	Grid [Size][Size]Piece
	EnpassantSquare *Square
}

func (b *Board) GetPiece(s *Square) Piece {
	return b.Grid[s.x][s.y]
}

func (b *Board) doMove(m *Move) {
	m.EnpassantSquareRemoved = b.EnpassantSquare
	b.EnpassantSquare = m.EnpassantSquareAdded
	if m.PromoteTo != nil {
		b.Grid[m.Start.x][m.Start.y] = nil
		b.Grid[m.End.x][m.End.y] = m.PromoteTo
		return
	}

	b.Grid[m.Start.x][m.Start.y] = nil
	m.Piece.doMove(m.End)
	if m.CapturedPiece != nil {
		b.Grid[m.CapturedPiece.Square().x][m.CapturedPiece.Square().y] = nil
	}
	b.Grid[m.End.x][m.End.y] = m.Piece
        if m.ShortCastle {
		sq := &Square{x: 7, y: m.Start.y}
		rook := b.GetPiece(sq).(*Rook)
		rook.square.x = 5
		b.Grid[7][m.Start.y] = nil
		b.Grid[5][m.Start.y] = rook
	}
        if m.LongCastle {
		sq := &Square{x: 0, y: m.Start.y}
		rook := b.GetPiece(sq).(*Rook)
		rook.square.x = 3
		b.Grid[0][m.Start.y] = nil
		b.Grid[3][m.Start.y] = rook
	}
}

func (b *Board) undoMove(m *Move) {
	b.EnpassantSquare = m.EnpassantSquareRemoved
	m.Piece.undoMove(m.Start)
	b.Grid[m.Start.x][m.Start.y] = m.Piece
	b.Grid[m.End.x][m.End.y] = nil

	if m.CapturedPiece != nil {
		b.Grid[m.CapturedPiece.Square().x][m.CapturedPiece.Square().y] = m.CapturedPiece
	}
        if m.ShortCastle {
		sq := &Square{x: 5, y: m.Start.y}
		rook := b.GetPiece(sq).(*Rook)
		rook.square.x = 7
		b.Grid[5][m.Start.y] = nil
		b.Grid[7][m.Start.y] = rook
	}
        if m.LongCastle {
		sq := &Square{x: 3, y: m.Start.y}
		rook := b.GetPiece(sq).(*Rook)
		rook.square.x = 0
		b.Grid[3][m.Start.y] = nil
		b.Grid[0][m.Start.y] = rook
	}
}

func (b *Board) setPieces(pieces []Piece) {
	for i := 0; i < len(pieces); i++ {
		p := pieces[i]
		sq := p.Square()
		b.Grid[sq.x][sq.y] = p
	}
}

func (b *Board) getPieces() []Piece {
	pieces := []Piece{}
	for i := Size - Size; i < Size; i++ {
		for j := Size - Size; j < Size; j++ {
			p := b.Grid[i][j];
			if p != nil {
				pieces = append(pieces, p)
			}
		}
	}
	return pieces
}

func (b *Board) getKing(c Color) *King {
	pieces := b.getPieces()
	var king *King
	for i := 0; i < len(pieces); i++ {
		piece := pieces[i]
		k, ok := piece.(*King)
		if !ok {
			continue
		}
		if k.Color() == c {
			king = k
			break
		}
	}
	if king == nil || king.Color() != c {
		panic("king not found")
	}
	return king
}

func (b *Board) possibleMoves(color Color) []*Move {
	moves := []*Move{}
	candidates := b.moveCandidates(color)
	for i := 0; i < len(candidates); i++ {
		m := candidates[i]
		b.doMove(m)
		king := b.getKing(color)
		if !king.IsInCheck() {
			moves = append(moves, m)
		}
		b.undoMove(m)
	}
	return moves
}

func (b *Board) moveCandidates(color Color) []*Move {
	moves := []*Move{}
	pieces := b.getPieces()
	for i := 0; i < len(pieces); i++ {
		piece := pieces[i]
		if piece.Color() != color {
			continue
		}
		possibleMoves := piece.PossibleMoves()
		moves = append(moves, possibleMoves...)
	}
	return moves
}

//TODO: tests
func (b *Board) IsAttacked(square *Square, color Color) bool {
	knight := &Knight{ PieceBase {color: color, square: square, board: b}}
	moves := knight.PossibleMoves()
	for i := 0; i < len(moves); i++ {
		m := moves[i]
		if _, ok := m.CapturedPiece.(*Knight); ok {
			return true
		}
	}
	bishop := &Bishop{ StraightGoer{ PieceBase {color: color, square: square, board: b}}}
	moves = bishop.PossibleMoves()
	for i := 0; i < len(moves); i++ {
		m := moves[i]
		if _, ok := m.CapturedPiece.(*Bishop); ok {
			return true
		}
	}
	rook := &Rook{ StraightGoer{ PieceBase {color: color, square: square, board: b}}}
	moves = rook.PossibleMoves()
	for i := 0; i < len(moves); i++ {
		m := moves[i]
		if _, ok := m.CapturedPiece.(*Rook); ok {
			return true
		}
	}
	queen := &Queen{ StraightGoer{ PieceBase {color: color, square: square, board: b}}}
	moves = queen.PossibleMoves()
	for i := 0; i < len(moves); i++ {
		m := moves[i]
		if _, ok := m.CapturedPiece.(*Queen); ok {
			return true
		}
	}
	pawn := &Pawn{ PieceBase {color: color, square: square, board: b}}
	moves = pawn.PossibleCaptures()
	for i := 0; i < len(moves); i++ {
		m := moves[i]
		if _, ok := m.CapturedPiece.(*Pawn); ok {
			return true
		}
	}
	return false
}

func (b *Board) Print() {
	for i := Size - 1; i >= 0; i-- {
		for j := Size - Size; j < Size; j++ {
			piece := b.Grid[j][i]
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

func (p *PieceBase) doMove(end *Square) {
	p.moveCounter++
	p.square = end
}

func (p *PieceBase) undoMove(start *Square) {
	p.moveCounter--
	p.square = start
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
	doMove(*Square)
	undoMove(*Square)
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
			Start: p.Square(),
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
		noncaptures = append(noncaptures, &Move{ Piece: p, Start: p.Square(), End: c })
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
		m := &Move{ Piece: k, Start: k.Square(), End: end }
		if piece == nil {
			moves = append(moves, m)
			continue
		}
		m.CapturedPiece = piece
		moves = append(moves, m)
	}
	moves = append(moves, k.ShortCastle()...)
	moves = append(moves, k.LongCastle()...)

	return moves
}

func (k *King) ShortCastle() []*Move {
	moves := []*Move{}
	if k.moveCounter > 0 {
		return moves
	}
	y := k.square.y
	rookPiece := k.board.GetPiece(&Square{x: 7, y: y})
	if rookPiece == nil {
		return moves
	}
	rook, ok := rookPiece.(*Rook)
	if !ok {
		return moves
	}
	if rook.moveCounter > 0 {
		return moves
	}

	for x := int8(5); x < 7; x++ {
		sq := &Square{x: x, y: y}
		if k.board.GetPiece(sq) != nil {
			return moves
		}
	}
	for x := int8(4); x < 7; x++ {
		sq := &Square{x: x, y: y}
		if k.board.IsAttacked(sq, k.color) {
			return moves
		}
	}
	end := &Square{x: 6, y: y}
	m := &Move{Piece: k, Start: k.Square(), End: end, ShortCastle: true}
	moves = append(moves, m)
	return moves
}

func (k *King) LongCastle() []*Move {
	moves := []*Move{}
	if k.moveCounter > 0 {
		return moves
	}
	y := k.square.y
	rookPiece := k.board.GetPiece(&Square{x: 0, y: y})
	if rookPiece == nil {
		return moves
	}
	rook, ok := rookPiece.(*Rook)
	if !ok {
		return moves
	}
	if rook.moveCounter > 0 {
		return moves
	}

	for x := int8(1); x < 4; x++ {
		sq := &Square{x: x, y: y}
		if k.board.GetPiece(sq) != nil {
			return moves
		}
	}
	for x := int8(2); x < 5; x++ {
		sq := &Square{x: x, y: y}
		if k.board.IsAttacked(sq, k.color) {
			return moves
		}
	}
	end := &Square{x: 2, y: y}
	m := &Move{Piece: k, Start: k.Square(), End: end, LongCastle: true}
	moves = append(moves, m)
	return moves
}

func (k *King) Print() {
	if k.color == White {
		fmt.Print("♚ ")
	} else {
		fmt.Print("♔ ")
	}
}

func (k *King) IsInCheck() bool {
	candidates := k.board.moveCandidates(-k.color)
	for i := 0; i < len(candidates); i++ {
		if candidates[i].CapturedPiece == k {
			return true
		}
	}
	return false
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
		m := &Move{ Piece: n, Start: n.Square(), End: end }
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
		fmt.Print("♞ ")
	} else {
		fmt.Print("♘ ")
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

	m := &Move{ Piece: p, Start: p.Square(), End: end }
	if p.Row() == 1 {
		noncaptures = append(noncaptures, m)
		newEnd := end.AddVector(&vector)
		if piece := p.board.GetPiece(newEnd); piece != nil {
			return noncaptures
		}
		m = &Move{ Piece: p, Start: p.Square(), End: newEnd, EnpassantSquareAdded: end }
		return append(noncaptures, m)
	}
	if p.Row() == 6 {
		queen := &Queen{ StraightGoer{ PieceBase {color: p.color, square: end, board: p.board }}}
		rook := &Rook{ StraightGoer{ PieceBase {color: p.color, square: end, board: p.board }}}
		bishop := &Bishop{ StraightGoer{ PieceBase {color: p.color, square: end, board: p.board }}}
		knight := &Knight{ PieceBase {color: p.color, square: end, board: p.board }}
		m1 := &Move{
			Piece: p,
			Start: p.Square(),
			End: end,
			PromoteTo: queen,
		}
		m2 := &Move{
			Piece: p,
			Start: p.Square(),
			End: end,
			PromoteTo: rook,
		}
		m3 := &Move{
			Piece: p,
			Start: p.Square(),
			End: end,
			PromoteTo: bishop,
		}
		m4 := &Move{
			Piece: p,
			Start: p.Square(),
			End: end,
			PromoteTo: knight,
		}
		return append(noncaptures, m1, m2, m3, m4)
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
		if p.board.EnpassantSquare != nil && *end == *p.board.EnpassantSquare {
			vector := DirVectors[p.color][Down]
			capturedPiece := p.board.GetPiece(end.AddVector(&vector))
			m := &Move{
				Piece: p,
				Start: p.Square(),
				End: end,
				CapturedPiece: capturedPiece,
			}
			captures = append(captures, m)
			continue
		}
		capturedPiece := p.board.GetPiece(end)
		if capturedPiece == nil || capturedPiece.Color() == p.color {
			continue
		}
		if p.Row() == 6 {
			queen := &Queen{ StraightGoer{ PieceBase {color: p.color, square: end, board: p.board }}}
			rook := &Rook{ StraightGoer{ PieceBase {color: p.color, square: end, board: p.board }}}
			bishop := &Bishop{ StraightGoer{ PieceBase {color: p.color, square: end, board: p.board }}}
			knight := &Knight{ PieceBase {color: p.color, square: end, board: p.board }}
			m1 := &Move{
				Piece: p,
				Start: p.Square(),
				End: end,
				CapturedPiece: capturedPiece,
				PromoteTo: queen,
			}
			m2 := &Move{
				Piece: p,
				Start: p.Square(),
				End: end,
				CapturedPiece: capturedPiece,
				PromoteTo: rook,
			}
			m3 := &Move{
				Piece: p,
				Start: p.Square(),
				End: end,
				CapturedPiece: capturedPiece,
				PromoteTo: bishop,
			}
			m4 := &Move{
				Piece: p,
				Start: p.Square(),
				End: end,
				CapturedPiece: capturedPiece,
				PromoteTo: knight,
			}
			captures = append(captures, m1, m2, m3, m4)
		} else {
			m := &Move{
				Piece: p,
				Start: p.Square(),
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
		fmt.Print("♟ ")
	} else {
		fmt.Print("♙ ")
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
		fmt.Print("♜ ")
	} else {
		fmt.Print("♖ ")
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
		fmt.Print("♝ ")
	} else {
		fmt.Print("♗ ")
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
		fmt.Print("♛ ")
	} else {
		fmt.Print("♕ ")
	}
}

type Move struct {
	Piece Piece
	Start *Square
	End *Square
	CapturedPiece Piece
	PromoteTo Piece
	LongCastle bool
	ShortCastle bool
	EnpassantSquareAdded *Square
	EnpassantSquareRemoved *Square
}

func InitBoard() *Board {
	board := &Board{}
	pieces := []Piece{
		&Rook{ StraightGoer{ PieceBase {color: White, square: &Square{x: 0, y: 0}, board: board }}},
		&Rook{ StraightGoer{ PieceBase {color: White, square: &Square{x: 7, y: 0}, board: board }}},
		&Bishop{ StraightGoer{ PieceBase {color: White, square: &Square{x: 2, y: 0}, board: board }}},
		&Bishop{ StraightGoer{ PieceBase {color: White, square: &Square{x: 5, y: 0}, board: board }}},
		&Queen{ StraightGoer{ PieceBase {color: White, square: &Square{x: 3, y: 0}, board: board }}},
		&Knight{ PieceBase {color: White, square: &Square{x: 1, y: 0}, board: board }},
		&Knight{ PieceBase {color: White, square: &Square{x: 6, y: 0}, board: board }},
		&King{ PieceBase {color: White, square: &Square{x: 4, y: 0}, board: board }},
		&Pawn{ PieceBase {color: White, square: &Square{x: 0, y: 1}, board: board }},
		&Pawn{ PieceBase {color: White, square: &Square{x: 1, y: 1}, board: board }},
		&Pawn{ PieceBase {color: White, square: &Square{x: 2, y: 1}, board: board }},
		&Pawn{ PieceBase {color: White, square: &Square{x: 3, y: 1}, board: board }},
		&Pawn{ PieceBase {color: White, square: &Square{x: 4, y: 1}, board: board }},
		&Pawn{ PieceBase {color: White, square: &Square{x: 5, y: 1}, board: board }},
		&Pawn{ PieceBase {color: White, square: &Square{x: 6, y: 1}, board: board }},
		&Pawn{ PieceBase {color: White, square: &Square{x: 7, y: 1}, board: board }},


		&Rook{ StraightGoer{ PieceBase {color: Black, square: &Square{x: 0, y: 7}, board: board }}},
		&Rook{ StraightGoer{ PieceBase {color: Black, square: &Square{x: 7, y: 7}, board: board }}},
		&Bishop{ StraightGoer{ PieceBase {color: Black, square: &Square{x: 2, y: 7}, board: board }}},
		&Bishop{ StraightGoer{ PieceBase {color: Black, square: &Square{x: 5, y: 7}, board: board }}},
		&Queen{ StraightGoer{ PieceBase {color: Black, square: &Square{x: 3, y: 7}, board: board }}},
		&Knight{ PieceBase {color: Black, square: &Square{x: 1, y: 7}, board: board }},
		&Knight{ PieceBase {color: Black, square: &Square{x: 6, y: 7}, board: board }},
		&King{ PieceBase {color: Black, square: &Square{x: 4, y: 7}, board: board }},
		&Pawn{ PieceBase {color: Black, square: &Square{x: 0, y: 6}, board: board }},
		&Pawn{ PieceBase {color: Black, square: &Square{x: 1, y: 6}, board: board }},
		&Pawn{ PieceBase {color: Black, square: &Square{x: 2, y: 6}, board: board }},
		&Pawn{ PieceBase {color: Black, square: &Square{x: 3, y: 6}, board: board }},
		&Pawn{ PieceBase {color: Black, square: &Square{x: 4, y: 6}, board: board }},
		&Pawn{ PieceBase {color: Black, square: &Square{x: 5, y: 6}, board: board }},
		&Pawn{ PieceBase {color: Black, square: &Square{x: 6, y: 6}, board: board }},
		&Pawn{ PieceBase {color: Black, square: &Square{x: 7, y: 6}, board: board }},
	}
	board.setPieces(pieces)
	return board
}

func main() {
	rand.Seed(time.Now().Unix())
	board := InitBoard()
	game := Game {
		Board: board,
		OnTurn: White,
	}
	for i:=0; i<1000; i++ {
		board.Print()
		fmt.Println("------")
		moves := game.possibleMoves()
		if len(moves) == 0 {
			fmt.Println("game over")
			break
		}
		which := rand.Intn(len(moves))

		// do castle whenever possible
		for j:=0; j<len(moves); j++ {
			m := moves[j]
			if m.CapturedPiece != nil {
				if board.EnpassantSquare != nil && *board.EnpassantSquare == *m.End {
					which = j
					fmt.Println("pick: en passant")
					break
				}
			}
			// if m.EnpassantSquareAdded != nil {
			// 	which = j
			// 	fmt.Println("pick: pawn by two")
			// 	break
			// }
			// if m.ShortCastle {
			// 	which = j
			// 	fmt.Println("pick: short castle")
			// 	break
			// }
			// if m.LongCastle {
			// 	which = j
			// 	fmt.Println("pick: long castle")
			// 	break
			// }
		}

		move := moves[which]
		game.doMove(move)
	}
}

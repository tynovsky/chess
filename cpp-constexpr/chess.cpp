// This is forces the game to be played on compile time and results
// Must be compiled with -std=c++17 -O3 -fconstexpr-steps=351843720
#include <stdio.h>

enum
{
    Pawn = 1 << 1,
    Knight = 1 << 2,
    Bishop = 1 << 3,
    Rook = 1 << 4,
    Queen = 1 << 5,
    King = 1 << 6,

    NotMoved = 1 << 7,
    Enpassant = 1 << 8,
    White = 1 << 9,
    Black = 1 << 10,
};

enum
{
    ResultProgress = 0,
    ResultNoMoves = 1,
    ResultCheckmate = 2,
    ResultStalemate = 3,
    ResultNotEnoughMaterial = 4,
};

typedef unsigned short Tile;
typedef unsigned short TileIndex;

static constexpr TileIndex RowTileCount = 8;
static constexpr TileIndex BoardTileCount = RowTileCount * RowTileCount;
static constexpr Tile rowMajors[] = {Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook};
static constexpr Tile rowPawns[] = {Pawn, Pawn, Pawn, Pawn, Pawn, Pawn, Pawn, Pawn};

static constexpr char MaxPiecesPerColor = RowTileCount * 2;
static constexpr unsigned short MaxTurns = 1000;

static constexpr TileIndex index(TileIndex x, TileIndex y) { return x + (y * RowTileCount); }
static constexpr TileIndex index(TileIndex who, TileIndex x, TileIndex y) { return (who * BoardTileCount) + x + (y * RowTileCount); }

struct RandomGenerator
{
    unsigned long int next = 1;

    constexpr RandomGenerator(const unsigned long int seed) : next(seed) {}

    constexpr int random(const int max)
    {
        next = next * 1103515245 + 12345;
        return (unsigned int)(next / 65536) % max;
    }
};

struct Checker
{
    Tile tiles[BoardTileCount];
    Tile currentPlayerMask;
    Tile moves[BoardTileCount * MaxPiecesPerColor];
    char movedPieces[MaxPiecesPerColor];
    char movedPiecesCount;

    constexpr Checker(const Tile *currentTiles, const Tile player) : tiles(), currentPlayerMask(player), moves(), movedPieces(), movedPiecesCount(0)
    {
        init(currentTiles, player);
    }

    constexpr void init(const Tile *t, const Tile player)
    {
        currentPlayerMask = player;

        for (TileIndex i = 0; i < BoardTileCount; i++)
            tiles[i] = t[i];
    }

    constexpr void reset()
    {
        movedPiecesCount = 0;

        for (char i = 0; i < MaxPiecesPerColor; i++)
            movedPieces[i] = 0;

        for (TileIndex i = 0; i < BoardTileCount * MaxPiecesPerColor; i++)
            moves[i] = 0;
    }

    constexpr bool hasEnoughMaterial()
    {
        unsigned char whiteKnights = 0, whiteBishops = 0, blackKnights = 0, blackBishops = 0;
        for (TileIndex i = 0; i < BoardTileCount; i++)
        {
            if (tiles[i] & (Pawn | Rook | Queen))
                return true;
            else if (tiles[i] & Knight && tiles[i] & White)
                whiteKnights++;
            else if (tiles[i] & Bishop && tiles[i] & White)
                whiteBishops++;
            else if (tiles[i] & Knight && tiles[i] & Black)
                blackKnights++;
            else if (tiles[i] & Bishop && tiles[i] & Black)
                blackBishops++;
        }

        return ((whiteBishops >= 2 || blackBishops >= 2) ||
                (whiteBishops == 1 && whiteKnights > 0) ||
                (blackBishops == 1 && blackKnights > 0) ||
                (whiteKnights > 2 || blackKnights > 2));
    }

    constexpr bool isPositionUnderAttack(const TileIndex x, const TileIndex y)
    {
        for (char f = 0; f < movedPiecesCount; f++)
            for (TileIndex i = f * BoardTileCount; i < (f + 1) * BoardTileCount; i++)
            {
                const TileIndex ii = i - (f * BoardTileCount);
                if (moves[i] != 0 && (ii % RowTileCount) == x && (ii / RowTileCount) == y)
                    return true;
            }

        return false;
    }

    constexpr int genMove(const TileIndex who, const TileIndex x, const TileIndex y, const bool noCapture, const bool mustCapture, const TileIndex mask)
    {
        const TileIndex target = index(x, y);

        if ((x < 0 || x >= RowTileCount || y < 0 || y >= RowTileCount) ||             // OOB check
            (tiles[target] != 0 && tiles[target] & currentPlayerMask) ||              // Attack own figures check
            (noCapture && tiles[target] != 0) || (mustCapture && tiles[target] == 0)) // no/must capture enforcement
            return 0;

        // Enpassant situation
        // if (tiles[who] & Bishop && tiles[target] & Enpassant)
        // {
        //     // TODO: Capture dat?
        // }

        if (tiles[who] & Pawn && (y == 0 || y == RowTileCount - 1))
            moves[index(movedPiecesCount, x, y)] = Queen | currentPlayerMask | mask; // Pawn promotion
        else
            moves[index(movedPiecesCount, x, y)] = (tiles[who] & ~(NotMoved | Enpassant)) | mask;
        return 1;
    }

    constexpr int genMoveLine(const TileIndex who, const TileIndex dx, const TileIndex dy)
    {
        int cnt = 0;
        TileIndex x = who % RowTileCount, y = who / RowTileCount;
        for (TileIndex i = 0; i < RowTileCount; i++)
        {
            x += dx;
            y += dy;

            if (x < 0 || x >= RowTileCount || y < 0 || y >= RowTileCount)
                break;

            cnt += genMove(who, x, y, false, false, 0);

            if (tiles[index(x, y)] != 0)
                break;
        }
        return cnt;
    }

    constexpr int genMoveOffset(const TileIndex who, const TileIndex ox, const TileIndex oy)
    {
        return genMove(who, (who % RowTileCount) + ox, (who / RowTileCount) + oy, false, false, 0);
    }

    constexpr int genPawnMoves(const TileIndex who)
    {
        const TileIndex x = who % RowTileCount, y = who / RowTileCount, axis = currentPlayerMask == Black ? -1 : +1;

        int cnt = genMove(who, x - 1, y + axis, false, true, 0) +
                  genMove(who, x + 1, y + axis, false, true, 0) +
                  genMove(who, x, y + axis, true, false, 0);

        if (tiles[who] & NotMoved)
            cnt += genMove(who, x, y + (axis * 2), true, false, Enpassant);

        return cnt;
    }

    constexpr int genKnightMoves(const TileIndex who)
    {
        return genMoveOffset(who, -1, -2) +
               genMoveOffset(who, -2, -1) +
               genMoveOffset(who, -2, +1) +
               genMoveOffset(who, -1, +2);
    }

    constexpr int genBishopMoves(const TileIndex who)
    {
        return genMoveLine(who, -1, -1) +
               genMoveLine(who, +1, -1) +
               genMoveLine(who, -1, +1) +
               genMoveLine(who, +1, +1);
    }

    constexpr int genRookMoves(const TileIndex who)
    {
        return genMoveLine(who, +1, 0) +
               genMoveLine(who, -1, 0) +
               genMoveLine(who, 0, -1) +
               genMoveLine(who, 0, +1);
    }

    constexpr int genQueenMoves(const TileIndex who)
    {
        return genBishopMoves(who) +
               genRookMoves(who);
    }

    constexpr int genKingMoves(const TileIndex who)
    {
        return genMoveOffset(who, -1, -1) +
               genMoveOffset(who, -1, 0) +
               genMoveOffset(who, -1, +1) +
               genMoveOffset(who, 0, -1) +
               genMoveOffset(who, 0, +1) +
               genMoveOffset(who, +1, -1) +
               genMoveOffset(who, +1, 0) +
               genMoveOffset(who, +1, +1);
    }

    constexpr int genPossibleMoves()
    {
        int totalMoves = 0;
        for (TileIndex i = 0; i < BoardTileCount; i++)
        {
            int moveCount = 0;

            if (!(tiles[i] & currentPlayerMask))
                continue;
            else if (tiles[i] & Pawn)
                moveCount = genPawnMoves(i);
            else if (tiles[i] & Knight)
                moveCount = genKnightMoves(i);
            else if (tiles[i] & Bishop)
                moveCount = genBishopMoves(i);
            else if (tiles[i] & Rook)
                moveCount = genRookMoves(i);
            else if (tiles[i] & Queen)
                moveCount = genQueenMoves(i);
            else if (tiles[i] & King)
                moveCount = genKingMoves(i);

            if (moveCount > 0)
            {
                movedPieces[movedPiecesCount] = i;
                movedPiecesCount++;
            }

            totalMoves += moveCount;
        }

        return totalMoves;
    }
};

struct Board
{
    Tile tiles[BoardTileCount];
    Tile currentPlayerMask;
    Checker checker, checker2;
    unsigned short turnsTotal;
    unsigned char state;
    TileIndex lastMoveFrom, lastMoveTo;
    RandomGenerator rgen;

    constexpr Board(const int seed, const bool runIt) : checker(tiles, Black), checker2(tiles, Black), rgen(seed), tiles(), currentPlayerMask(Black), turnsTotal(0), state(ResultProgress), lastMoveFrom(0), lastMoveTo(0)
    {
        copyRow(0, rowMajors, NotMoved | White);
        copyRow(1, rowPawns, NotMoved | White);
        copyRow(6, rowPawns, NotMoved | Black);
        copyRow(7, rowMajors, NotMoved | Black);

        if (runIt)
            for (int i = 0; i < MaxTurns; i++)
                if (next() != ResultProgress)
                    break;
    }

    constexpr int next()
    {
        const int nextPlayer = currentPlayerMask == Black ? White : Black;

        turnsTotal++;

        checker.init(tiles, currentPlayerMask);
        checker.reset();
        if (!checker.hasEnoughMaterial())
            return state = ResultNotEnoughMaterial;

        int kingX = 0, kingY = 0;
        for (int i = 0; i < BoardTileCount; i++)
            if (tiles[i] & King && tiles[i] & currentPlayerMask)
            {
                kingX = i % RowTileCount;
                kingY = i / RowTileCount;
                break;
            }

        int cnt = checker.genPossibleMoves();
        for (char f = 0; f < checker.movedPiecesCount; f++)
            for (TileIndex i = f * BoardTileCount; i < (f + 1) * BoardTileCount; i++)
                if (checker.moves[i] != 0)
                {
                    const TileIndex who = checker.movedPieces[f];
                    const TileIndex where = i - (f * BoardTileCount);

                    TileIndex kX = kingX, kY = kingY;
                    if (checker.tiles[who] & King)
                    {
                        kX = where % RowTileCount;
                        kY = where / RowTileCount;
                    }

                    checker2.init(tiles, nextPlayer);
                    checker2.tiles[where] = checker.moves[i];
                    checker2.tiles[who] = 0;
                    checker2.reset();
                    checker2.genPossibleMoves();
                    if (checker2.isPositionUnderAttack(kX, kY))
                    {
                        checker.moves[i] = 0;
                        cnt--;
                    }
                }

        checker2.init(tiles, nextPlayer);
        checker2.reset();
        checker2.genPossibleMoves();

        if (cnt == 0)
            return state = (checker2.isPositionUnderAttack(kingX, kingY) ? ResultCheckmate : ResultStalemate);

        const int wanted = rgen.random(cnt);
        for (char f = 0; f < checker.movedPiecesCount; f++)
            for (TileIndex i = f * BoardTileCount; i < (f + 1) * BoardTileCount; i++)
                if (checker.moves[i] != 0 && --cnt == wanted)
                {
                    for (TileIndex e = 0; e < BoardTileCount; e++)
                        tiles[e] &= ~Enpassant;

                    const TileIndex who = checker.movedPieces[f];
                    tiles[i % BoardTileCount] = checker.moves[i];
                    tiles[who] = 0;
                    if (checker.moves[i] & Enpassant)
                        tiles[index(who % RowTileCount, (who / RowTileCount) + (currentPlayerMask == Black ? -1 : +1))] = Enpassant;

                    currentPlayerMask = nextPlayer;
                    lastMoveFrom = who;
                    lastMoveTo = i % BoardTileCount;

                    return state = ResultProgress;
                }

        return state = ResultProgress;
    }

    constexpr void copyRow(const TileIndex row, const Tile *src, const Tile mask)
    {
        for (TileIndex i = 0; i < RowTileCount; i++)
            tiles[index(0, row) + i] = src[i] | mask;
    }
};

namespace
{
    constexpr const char *pieceString(const Tile tile)
    {
        if (tile & Pawn)
            return (tile & Black ? "♙" : "♟");
        else if (tile & Knight)
            return (tile & Black ? "♘" : "♞");
        else if (tile & Bishop)
            return (tile & Black ? "♗" : "♝");
        else if (tile & Rook)
            return (tile & Black ? "♖" : "♜");
        else if (tile & Queen)
            return (tile & Black ? "♕" : "♛");
        else if (tile & King)
            return (tile & Black ? "♔" : "♚");
        return ".";
    }

    // Print individual board
    void printBoard(const Board board)
    {
        for (int y = 0; y < RowTileCount; y++)
        {
            printf("%d", y + 1);
            for (int x = 0; x < RowTileCount; x++)
            {
                const TileIndex pos = index(x, y);
                if (pos == board.lastMoveFrom)
                    printf(" ?");
                else
                    printf("%s%s", board.lastMoveTo == pos ? ">" : " ", pieceString(board.tiles[pos]));
            }
            printf("\n");
        }
        printf("  ᵃ ᵇ ᶜ ᵈ ᵉ ᶠ ᵍ ʰ\n");
    }

    // Print resulting string
    constexpr void printResult(const int res)
    {
        if (res == ResultNoMoves)
            printf("No moves!\n");
        else if (res == ResultCheckmate)
            printf("Checkmate!\n");
        else if (res == ResultStalemate)
            printf("Stalemate!\n");
        else if (res == ResultNotEnoughMaterial)
            printf("Not enough material!\n");
        else
            printf("Unknown: %d\n", res);
    }

    // Helper struct that allows running multiple boards at compile time
    template <size_t N>
    struct CompiledBoards
    {
        int results[N];

        constexpr CompiledBoards() : results()
        {
            for (int i = 0; i < N; i++)
            {
                Board b(i, true);
                results[i] = b.state;
            }
        }
    };
} // namespace

int main()
{
    constexpr Board b(1, true);
    printResult(b.state);

    // static constexpr int N = 5;
    // constexpr CompiledBoards<N> boards;
    // for (int i = 0; i < N; i++)
    // {
    //     printf("%d => ", i);
    //     printResult(boards.results[i]);
    // }
}

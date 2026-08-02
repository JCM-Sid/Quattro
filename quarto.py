from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Sequence, Tuple

Piece = Tuple[int, int, int, int]
Board = List[Optional[Piece]]


def make_piece_set() -> List[Piece]:
    pieces: List[Piece] = []
    for color in (0, 1):
        for shape in (0, 1):
            for size in (0, 1):
                for fill in (0, 1):
                    pieces.append((color, shape, size, fill))
    return pieces


def is_winning_board(board: Sequence[Optional[Piece]]) -> bool:
    lines = [
        [0, 1, 2, 3],
        [4, 5, 6, 7],
        [8, 9, 10, 11],
        [12, 13, 14, 15],
        [0, 4, 8, 12],
        [1, 5, 9, 13],
        [2, 6, 10, 14],
        [3, 7, 11, 15],
        [0, 5, 10, 15],
        [3, 6, 9, 12],
    ]
    for line in lines:
        values = [board[idx] for idx in line]
        if not all(value is not None for value in values):
            continue
        if any(all(piece[attr] == values[0][attr] for piece in values[1:]) for attr in range(4)):
            return True
    return False


def apply_move(board: Board, piece: Piece, position: int) -> Board:
    updated_board = list(board)
    if position < 0 or position >= len(updated_board) or updated_board[position] is not None:
        raise ValueError("invalid position")
    updated_board[position] = piece
    return updated_board


def format_board(board: Sequence[Optional[Piece]]) -> str:
    rows = []
    for row in range(4):
        cells = []
        for col in range(4):
            idx = row * 4 + col
            value = board[idx]
            if value is None:
                cells.append("·")
            else:
                cells.append("X")
        rows.append(" | ".join(cells))
    return "\n".join(rows)


def parse_piece(token: str) -> Piece:
    if len(token) != 4 or any(ch not in "01" for ch in token):
        raise ValueError("piece must be a 4-digit binary string")
    return tuple(int(ch) for ch in token)


def describe_piece(piece: Piece) -> str:
    color = "light" if piece[0] else "dark"
    shape = "square" if piece[1] else "round"
    size = "large" if piece[2] else "small"
    fill = "filled" if piece[3] else "empty"
    return f"{color} {shape} {size} {fill} piece"


def parse_position(token: str) -> int:
    value = int(token)
    if value < 0 or value > 15:
        raise ValueError("position must be between 0 and 15")
    return value


def play_game() -> None:
    pieces = make_piece_set()
    board: Board = [None] * 16
    available = list(pieces)
    current_player = 1

    print("Quarto")
    print("Enter a 4-digit binary piece code (e.g. 1010) and a board position 0-15.")
    print("Legend: 0=dark/round/small/empty, 1=light/square/large/filled")

    while True:
        print(f"\nPlayer {current_player}'s turn")
        print(format_board(board))
        print("Available pieces:", len(available))
        try:
            piece_token = input("Choose a piece (binary code): ").strip()
            piece = parse_piece(piece_token)
            if piece not in available:
                raise ValueError("piece already used")
            available.remove(piece)
            pos_token = input(f"Place the {describe_piece(piece)} at position (0-15): ").strip()
            position = parse_position(pos_token)
            board = apply_move(board, piece, position)
        except ValueError as exc:
            print(f"Invalid input: {exc}")
            continue

        if is_winning_board(board):
            print(format_board(board))
            print(f"Player {current_player} wins!")
            return

        if not available:
            print("Draw")
            return

        current_player = 3 - current_player


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Play a local Quarto game")
    parser.add_argument("--demo", action="store_true", help="print a short demo and exit")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.demo:
        print("Quarto is a 2-player abstract strategy game on a 4x4 board.")
        print("Each turn, choose one of the remaining pieces and place it on the board.")
        print("The first player to complete a line with shared attributes wins.")
        return 0

    play_game()
    return 0


if __name__ == "__main__":
    sys.exit(main())

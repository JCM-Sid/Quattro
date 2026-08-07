from __future__ import annotations

import argparse
import random
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


def get_all_possible_moves(board: Board, available: List[Piece]) -> List[Tuple[Piece, int]]:
    moves: List[Tuple[Piece, int]] = []
    empty_positions = [i for i, cell in enumerate(board) if cell is None]
    for piece in available:
        for pos in empty_positions:
            moves.append((piece, pos))
    return moves


def find_winning_move(board: Board, available: List[Piece]) -> Optional[Tuple[Piece, int]]:
    empty_positions = [i for i, cell in enumerate(board) if cell is None]
    for piece in available:
        for pos in empty_positions:
            new_board = apply_move(board, piece, pos)
            if is_winning_board(new_board):
                return (piece, pos)
    return None


def get_computer_move(board: Board, available: List[Piece], level: str) -> Tuple[Piece, int]:
    moves = get_all_possible_moves(board, available)
    if not moves:
        raise ValueError("no moves available")

    # 1. Victoire immédiate (tous niveaux hors débutant)
    if level != "DEBUTANT":
        winning = find_winning_move(board, available)
        if winning is not None:
            return winning

    if level == "DEBUTANT" :
        return random.choice(moves)

    # 2. Niveau MOYEN (1 tour de profondeur)
    if level == "MOYEN":
        safe_moves: List[Tuple[Piece, int]] = []
        for piece, pos in moves:
            new_board = apply_move(board, piece, pos)
            new_available = [p for p in available if p != piece]
            if find_winning_move(new_board, new_available) is None:
                safe_moves.append((piece, pos))

        if safe_moves:
            return random.choice(safe_moves)
        return random.choice(moves)

    # 3. Niveau DIFFICILE (2 tours de profondeur / Minimax à 2 coups)
    if level == "DIFFICILE":
        best_moves: List[Tuple[Piece, int]] = []
        best_score = -float('inf')

        for piece, pos in moves:
            # Tour 1 : Simulation du coup de l'IA
            board_1 = apply_move(board, piece, pos)
            avail_1 = [p for p in available if p != piece]

            # Tour 2 : Analyse des réponses possibles de l'adversaire
            opp_winning_move = find_winning_move(board_1, avail_1)
            
            if opp_winning_move is not None:
                # Si l'adversaire peut gagner au tour suivant, coup très défavorable
                score = -100
            else:
                # Évaluation de la sécurité : combien de répliques sûres l'adversaire aurait-il ?
                # Plus le coup restreint les options de l'adversaire, meilleur est le score.
                opp_moves = get_all_possible_moves(board_1, avail_1)
                safe_opp_moves_count = 0
                
                for opp_piece, opp_pos in opp_moves:
                    board_2 = apply_move(board_1, opp_piece, opp_pos)
                    avail_2 = [p for p in avail_1 if p != opp_piece]
                    
                    # Si la réplique de l'adversaire ne nous donne pas de victoire au tour d'après
                    if find_winning_move(board_2, avail_2) is None:
                        safe_opp_moves_count += 1

                # Un score plus élevé signifie que l'adversaire a moins de contre-attaques faciles
                score = -safe_opp_moves_count

            # Sélection des meilleurs coups selon le score évalué
            if score > best_score:
                best_score = score
                best_moves = [(piece, pos)]
            elif score == best_score:
                best_moves.append((piece, pos))

        if best_moves:
            return random.choice(best_moves)

    return random.choice(moves)


def play_game(mode: str, level: Optional[str] = None) -> None:
    pieces = make_piece_set()
    board: Board = [None] * 16
    available = list(pieces)
    current_player = 1

    print("Quarto")
    print("Enter a 4-digit binary piece code (e.g. 1010) and a board position 0-15.")
    print("Legend: 0=dark/round/small/empty, 1=light/square/large/filled")

    while True:
        is_computer = (mode == "seul" and current_player == 2)

        if is_computer:
            print(f"\nComputer ({level})'s turn")
        else:
            print(f"\nPlayer {current_player}'s turn")

        print(format_board(board))
        print("Available pieces:", len(available))

        try:
            if is_computer:
                piece, position = get_computer_move(board, available, level or "DEBUTANT")
                print(f"Computer chooses piece {''.join(str(b) for b in piece)}")
                print(f"Computer places it at position {position}")
                available.remove(piece)
                board = apply_move(board, piece, position)
            else:
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
            if is_computer:
                print("Computer wins!")
            else:
                print(f"Player {current_player} wins!")
            return

        if not available:
            print("Draw")
            return

        current_player = 3 - current_player


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Play a local Quarto game")
    parser.add_argument("mode", choices=["2", "seul"], help="game mode: '2' for two players, 'seul' for solo against computer")
    parser.add_argument("level", nargs="?", choices=["DEBUTANT", "MOYEN", "DIFFICILE"], help="computer level (required for 'seul' mode)")
    parser.add_argument("--demo", action="store_true", help="print a short demo and exit")
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.demo:
        print("Quarto is a 2-player abstract strategy game on a 4x4 board.")
        print("Each turn, choose one of the remaining pieces and place it on the board.")
        print("The first player to complete a line with shared attributes wins.")
        return 0

    if args.mode == "seul" and args.level is None:
        parser.error("the 'level' argument is required when mode is 'seul'")

    play_game(args.mode, args.level)
    return 0


if __name__ == "__main__":
    sys.exit(main())

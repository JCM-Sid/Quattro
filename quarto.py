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


def get_computer_move(
    board: Board, 
    piece_to_place: Piece, 
    available: List[Piece], 
    level: str
) -> Tuple[int, Optional[Piece]]:
    """
    Retourne un tuple (position_où_placer_la_pièce, pièce_à_donner_à_l_adversaire).
    """
    empty_positions = [i for i, p in enumerate(board) if p is None]
    if not empty_positions:
        raise ValueError("no moves available")

    # Si le plateau est totalement vide (premier coup de la partie)
    if all(p is None for p in board):
        chosen_pos = random.choice(empty_positions)
        chosen_next = random.choice(available) if available else None
        return chosen_pos, chosen_next

    # 1. Gagnant en 1 placement (Placement en cours)
    for pos in empty_positions:
        test_board = apply_move(board, piece_to_place, pos)
        if is_winning_board(test_board):
            # On gagne direct : peu importe la pièce donnée après
            next_p = random.choice(available) if available else None
            return pos, next_p

    if level == "DEBUTANT":
        pos = random.choice(empty_positions)
        next_p = random.choice(available) if available else None
        return pos, next_p

    # S'il ne reste plus de pièces à distribuer (16e placement)
    if not available:
        return random.choice(empty_positions), None

    # Génération de tous les coups complets possibles de l'IA (Case, Pièce donnée)
    possible_actions: List[Tuple[int, Piece]] = [
        (pos, piece) for pos in empty_positions for piece in available
    ]

    # 2. Sécurisation : filtrer les pièces qui font gagner l'adversaire au coup 2
    safe_actions: List[Tuple[int, Piece]] = []
    
    for pos, given_piece in possible_actions:
        board_1 = apply_move(board, piece_to_place, pos)
        avail_1 = [p for p in available if p != given_piece]
        rem_positions_1 = [i for i in empty_positions if i != pos]

        # L'adversaire peut-il gagner immédiatement avec la pièce qu'on lui donne ?
        opp_can_win = False
        for opp_pos in rem_positions_1:
            board_opp = apply_move(board_1, given_piece, opp_pos)
            if is_winning_board(board_opp):
                opp_can_win = True
                break

        if not opp_can_win:
            safe_actions.append((pos, given_piece))

    # Si tous les coups donnent la victoire à l'adversaire, on prend un coup au hasard pour survivre
    valid_actions = safe_actions if safe_actions else possible_actions

    if level == "MOYEN":
        return random.choice(valid_actions)

    # 3. Niveau EXPERT / DIFFICILE : Recherche de la victoire au 3ème placement
    best_score = -float('inf')
    best_actions: List[Tuple[int, Piece]] = []

    for pos, given_piece in valid_actions:
        board_1 = apply_move(board, piece_to_place, pos)
        avail_1 = [p for p in available if p != given_piece]
        rem_positions_1 = [i for i in empty_positions if i != pos]

        # Évaluation sur le Tour 2 (Adversaire) -> Tour 3 (IA)
        # On cherche à maximiser le nombre de réponses défavorables pour l'adversaire
        wins_at_round_3 = 0
        total_opp_responses = 0

        for opp_pos in rem_positions_1:
            board_2 = apply_move(board_1, given_piece, opp_pos)
            rem_positions_2 = [i for i in rem_positions_1 if i != opp_pos]

            for opp_given_piece in avail_1:
                total_opp_responses += 1
                avail_2 = [p for p in avail_1 if p != opp_given_piece]

                # Tour 3 : L'IA place la pièce reçue `opp_given_piece`
                can_win_round_3 = False
                for my_pos_r3 in rem_positions_2:
                    board_3 = apply_move(board_2, opp_given_piece, my_pos_r3)
                    if is_winning_board(board_3):
                        can_win_round_3 = True
                        break

                if can_win_round_3:
                    wins_at_round_3 += 1

        # Score : plus la proportion d'opportunités de gagner au Tour 3 est élevée, meilleur est le coup
        score = (wins_at_round_3 / total_opp_responses) if total_opp_responses > 0 else 0

        if score > best_score:
            best_score = score
            best_actions = [(pos, given_piece)]
        elif score == best_score:
            best_actions.append((pos, given_piece))

    return random.choice(best_actions)


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

#!/usr/bin/env python3
"""Quarto — Interface graphique Pygame.

Usage:
    source .env/bin/activate
    python quarto_gui.py

Commandes:
    Clic gauche    — sélectionner une pièce / placer une pièce
    R              — redémarrer la partie
    Échap / Q      — quitter
"""

from __future__ import annotations

import sys
from typing import List, Optional, Tuple

import pygame

from quarto import apply_move, is_winning_board, make_piece_set, Piece

# ── Constantes visuelles ─────────────────────────────────────────────────────
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 850
FPS = 60

# Couleurs
COLOR_BG = (245, 245, 220)
COLOR_BOARD_CELL = (210, 180, 140)
COLOR_BOARD_BORDER = (139, 69, 19)
COLOR_PIECE_DARK = (101, 67, 33)
COLOR_PIECE_LIGHT = (222, 184, 135)
COLOR_HIGHLIGHT = (50, 205, 50)
COLOR_TEXT = (60, 40, 20)
COLOR_STATUS_BG = (230, 220, 190)

# Plateau
BOARD_COLS = 4
BOARD_ROWS = 4
CELL_SIZE = 100
CELL_GAP = 10
BOARD_ORIGIN_X = (WINDOW_WIDTH - (BOARD_COLS * CELL_SIZE + (BOARD_COLS - 1) * CELL_GAP)) // 2
BOARD_ORIGIN_Y = 80

# Pièces disponibles
POOL_CELL_SIZE = 70
POOL_GAP = 8
POOL_ORIGIN_X = (WINDOW_WIDTH - (BOARD_COLS * POOL_CELL_SIZE + (BOARD_COLS - 1) * POOL_GAP)) // 2
POOL_ORIGIN_Y = 600

# Police
pygame.font.init()
FONT_TITLE = pygame.font.SysFont("liberationsans", 32, bold=True)
FONT_STATUS = pygame.font.SysFont("liberationsans", 22)
FONT_SMALL = pygame.font.SysFont("liberationsans", 18)


# ── Helpers géométriques ─────────────────────────────────────────────────────


def board_rect(row: int, col: int) -> pygame.Rect:
    x = BOARD_ORIGIN_X + col * (CELL_SIZE + CELL_GAP)
    y = BOARD_ORIGIN_Y + row * (CELL_SIZE + CELL_GAP)
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)


def pool_rect(index: int) -> pygame.Rect:
    """Rectangle de la pièce disponible n°index (0..15)."""
    row = index // BOARD_COLS
    col = index % BOARD_COLS
    x = POOL_ORIGIN_X + col * (POOL_CELL_SIZE + POOL_GAP)
    y = POOL_ORIGIN_Y + row * (POOL_CELL_SIZE + POOL_GAP)
    return pygame.Rect(x, y, POOL_CELL_SIZE, POOL_CELL_SIZE)


def draw_piece(
    surface: pygame.Surface,
    piece: Piece,
    center: Tuple[int, int],
    base_size: int,
) -> None:
    """Dessine une pièce centrée en *center* avec taille de référence *base_size*."""
    color = COLOR_PIECE_LIGHT if piece[0] else COLOR_PIECE_DARK
    is_square = piece[1]
    is_large = piece[2]
    is_filled = piece[3]

    size = int(base_size * 0.85) if is_large else int(base_size * 0.55)
    line_width = 0 if is_filled else max(3, size // 10)

    if is_square:
        half = size // 2
        rect = pygame.Rect(center[0] - half, center[1] - half, size, size)
        if is_filled:
            pygame.draw.rect(surface, color, rect, border_radius=size // 8)
        else:
            pygame.draw.rect(surface, color, rect, width=line_width, border_radius=size // 8)
    else:
        radius = size // 2
        if is_filled:
            pygame.draw.circle(surface, color, center, radius)
        else:
            pygame.draw.circle(surface, color, center, radius, width=line_width)


# ── Classe principale ────────────────────────────────────────────────────────


class QuartoGUI:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Quarto")
        self.clock = pygame.time.Clock()

        self.reset_game()

    def reset_game(self) -> None:
        self.board: List[Optional[Piece]] = [None] * 16
        self.available: List[Piece] = make_piece_set()
        self.current_player = 1
        self.selected_piece: Optional[Piece] = None
        self.game_over = False
        self.winner: Optional[int] = None
        self.status_message = "Joueur 1 : sélectionnez une pièce"

    def run(self) -> None:
        while True:
            self._handle_events()
            self._draw()
            self.clock.tick(FPS)

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset_game()
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    pygame.quit()
                    sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.game_over:
                    continue
                self._on_click(event.pos)

    def _on_click(self, pos: Tuple[int, int]) -> None:
        if self.selected_piece is None:
            # Phase 1 : sélection d'une pièce dans les disponibles
            for idx, piece in enumerate(self.available):
                if pool_rect(idx).collidepoint(pos):
                    self.selected_piece = piece
                    self.status_message = (
                        f"Joueur {self.current_player} : placez la pièce sur le plateau"
                    )
                    return
        else:
            # Phase 2 : placement sur le plateau
            for row in range(BOARD_ROWS):
                for col in range(BOARD_COLS):
                    idx = row * BOARD_COLS + col
                    if board_rect(row, col).collidepoint(pos):
                        if self.board[idx] is not None:
                            return  # case occupée
                        self.board[idx] = self.selected_piece
                        self.available.remove(self.selected_piece)
                        self.selected_piece = None

                        if is_winning_board(self.board):
                            self.game_over = True
                            self.winner = self.current_player
                            self.status_message = (
                                f"🎉 Joueur {self.current_player} a gagné ! Appuyez sur R"
                            )
                            return

                        if not self.available:
                            self.game_over = True
                            self.status_message = "🤝 Match nul ! Appuyez sur R"
                            return

                        self.current_player = 3 - self.current_player
                        self.status_message = (
                            f"Joueur {self.current_player} : sélectionnez une pièce"
                        )
                        return

    def _draw(self) -> None:
        self.screen.fill(COLOR_BG)

        # Titre
        title = FONT_TITLE.render("Quarto", True, COLOR_TEXT)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 20))

        # Sous-titre joueur
        subtitle = FONT_STATUS.render(
            f"Tour du joueur {self.current_player}", True, COLOR_TEXT
        )
        self.screen.blit(subtitle, (WINDOW_WIDTH // 2 - subtitle.get_width() // 2, 55))

        # Plateau
        self._draw_board()

        # Séparateur
        pygame.draw.line(
            self.screen,
            COLOR_BOARD_BORDER,
            (50, POOL_ORIGIN_Y - 30),
            (WINDOW_WIDTH - 50, POOL_ORIGIN_Y - 30),
            2,
        )

        # Label pièces disponibles
        label = FONT_STATUS.render("Pièces disponibles", True, COLOR_TEXT)
        self.screen.blit(label, (WINDOW_WIDTH // 2 - label.get_width() // 2, POOL_ORIGIN_Y - 28))

        # Pièces disponibles
        self._draw_pool()

        # Barre de statut
        self._draw_status_bar()

        pygame.display.flip()

    def _draw_board(self) -> None:
        for row in range(BOARD_ROWS):
            for col in range(BOARD_COLS):
                idx = row * BOARD_COLS + col
                rect = board_rect(row, col)

                # Fond cellule
                pygame.draw.rect(self.screen, COLOR_BOARD_CELL, rect, border_radius=6)
                pygame.draw.rect(self.screen, COLOR_BOARD_BORDER, rect, width=2, border_radius=6)

                # Pièce présente ?
                piece = self.board[idx]
                if piece is not None:
                    center = rect.center
                    draw_piece(self.screen, piece, center, CELL_SIZE)

    def _draw_pool(self) -> None:
        for idx, piece in enumerate(self.available):
            rect = pool_rect(idx)

            # Fond
            bg_color = COLOR_HIGHLIGHT if piece == self.selected_piece else COLOR_BOARD_CELL
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=4)
            pygame.draw.rect(self.screen, COLOR_BOARD_BORDER, rect, width=2, border_radius=4)

            # Dessin pièce
            center = rect.center
            draw_piece(self.screen, piece, center, POOL_CELL_SIZE)

    def _draw_status_bar(self) -> None:
        bar_rect = pygame.Rect(0, WINDOW_HEIGHT - 50, WINDOW_WIDTH, 50)
        pygame.draw.rect(self.screen, COLOR_STATUS_BG, bar_rect)
        pygame.draw.line(
            self.screen, COLOR_BOARD_BORDER, (0, WINDOW_HEIGHT - 50), (WINDOW_WIDTH, WINDOW_HEIGHT - 50), 2
        )

        status = FONT_STATUS.render(self.status_message, True, COLOR_TEXT)
        self.screen.blit(
            status,
            (WINDOW_WIDTH // 2 - status.get_width() // 2, WINDOW_HEIGHT - 35),
        )


# ── Point d'entrée ───────────────────────────────────────────────────────────


def main() -> int:
    gui = QuartoGUI()
    gui.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())

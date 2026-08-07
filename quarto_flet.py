#!/usr/bin/env python3
"""Quarto — Application web avec Flet (Flutter).

Usage:
    source .env/bin/activate
    python quarto_flet.py
    python quarto_flet.py --port 8080

L'application démarre un serveur web sur le port indiqué.
Configurez nginx en reverse proxy (WebSocket support requis) et pm2
pour la gestion du processus en production.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import uuid
from typing import Dict, List, Optional

import flet as ft
from flet import PageResizeEvent, run

from quarto import get_computer_move, is_winning_board, make_piece_set, Piece

# ── État global pour les parties multijoueur ─────────────────────────────────
GAMES: Dict[str, dict] = {}
_SERVER_INFO = {"host": "127.0.0.1", "port": 8080}

# ── Couleurs ─────────────────────────────────────────────────────────────────
_COLOR_DARK = "#654321"
_COLOR_LIGHT = "#DEB887"
_COLOR_CELL_BG = "#F5F9F5"
_COLOR_CELL_BORDER = "#8B4513"
_COLOR_HIGHLIGHT_BG = "#8C8C2D"
_COLOR_HIGHLIGHT_BORDER = "#228B22"
_COLOR_PAGE_BG = "#FFFDF4"



# ── Helpers visuels ──────────────────────────────────────────────────────────


def _border_all(width: int, color: str) -> ft.Border:
    """Crée une bordure uniforme (compatibilité Flet)."""
    side = ft.BorderSide(width, color)
    return ft.Border(top=side, right=side, bottom=side, left=side)


# ── Application principale ───────────────────────────────────────────────────


class QuartoApp:
    def __init__(self, page: ft.Page) -> None:
        self.page = page
        self.page.title = "Quarto"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.bgcolor = _COLOR_PAGE_BG
        self.page.padding = 20
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

        self.mode: Optional[str] = None
        self.computer_level: Optional[str] = "DEBUTANT"
        self.current_user: Optional[str] = None
        self.player2_user: Optional[str] = None
        self.users: Dict[str, dict] = self._load_users()

        # Remote game state
        self.game_id: Optional[str] = None
        self.player_role: Optional[int] = None
        self._game_id_from_url = self._extract_game_id()

        # Tailles dynamiques
        self.cell_size = 90
        self.pool_cell_size = 70
        self.piece_to_place_size = 80
        self.board_piece_size = 60
        self.pool_piece_size = 50
        self.pool_cols = 4

        self.page.on_resize = self._on_resize
        self.page.pubsub.subscribe(self._on_pubsub_message)
        self._show_login_screen()

    # ── Redimensionnement ──────────────────────────────────────────────────

    def _update_sizes(self) -> None:
        """Calcule les tailles et le layout compact si nécessaire."""
        viewport_w = self.page.width or 800
        is_compact = viewport_w < 500

        # Padding réduit sur mobile
        self.page.padding = 10 if is_compact else 20

        # Masquer / afficher les éléments optionnels
        if hasattr(self, "subtitle_text"):
            self.subtitle_text.visible = not is_compact
        if hasattr(self, "board_label"):
            self.board_label.visible = not is_compact
        if hasattr(self, "pool_label"):
            self.pool_label.visible = not is_compact
        if hasattr(self, "rules_text"):
            self.rules_text.visible = not is_compact

        if is_compact:
            available_w = max(300, viewport_w - 20)  # padding 10 de chaque côté
            self.cell_size = max(48, min(55, (available_w - 30) // 4))
            self.pool_cols = 6  # plus de colonnes = moins de hauteur
        else:
            available_w = max(300, viewport_w - 40)  # padding 20 de chaque côté
            self.cell_size = max(50, min(90, (available_w - 30) // 4))
            self.pool_cols = 4

        self.pool_cell_size = max(35, min(70, int(self.cell_size * 0.75)))
        self.piece_to_place_size = max(40, min(80, self.cell_size))
        self.board_piece_size = int(self.cell_size * 0.65)
        self.pool_piece_size = int(self.pool_cell_size * 0.65)

    def _on_resize(self, e: ft.PageResizeEvent) -> None:
        self._update_sizes()
        self._refresh()

    # ── Widgets visuels ────────────────────────────────────────────────────

    def _piece_widget(self, piece: Piece, base_size: int) -> ft.Container:
        color = _COLOR_LIGHT if piece[0] else _COLOR_DARK
        is_square = piece[1]
        is_large = piece[2]
        is_filled = piece[3]

        size = int(base_size * 0.8) if is_large else int(base_size * 0.5)
        line_width = max(2, size // 12)

        return ft.Container(
            width=size,
            height=size,
            bgcolor=color if is_filled else None,
            border=None if is_filled else _border_all(line_width, color),
            border_radius=4 if is_square else size // 2,
        )

    def _board_cell(self, idx: int) -> ft.Container:
        piece = self.board[idx]
        return ft.Container(
            width=self.cell_size,
            height=self.cell_size,
            bgcolor=_COLOR_CELL_BG,
            border=_border_all(2, _COLOR_CELL_BORDER),
            border_radius=8,
            alignment=ft.alignment.Alignment(0, 0),
            content=self._piece_widget(piece, self.board_piece_size) if piece else None,
            on_click=lambda e: self._on_cell_click(idx),
        )

    def _pool_cell(self, piece: Piece) -> ft.Container:
        return ft.Container(
            width=self.pool_cell_size,
            height=self.pool_cell_size,
            bgcolor=_COLOR_CELL_BG,
            border=_border_all(2, _COLOR_CELL_BORDER),
            border_radius=8,
            alignment=ft.alignment.Alignment(0, 0),
            content=self._piece_widget(piece, self.pool_piece_size),
            on_click=lambda e: self._on_piece_click(piece),
        )

    # ── Authentification ───────────────────────────────────────────────────

    def _load_users(self) -> Dict[str, dict]:
        """Charge les utilisateurs et stats depuis users.json."""
        path = os.path.join(os.path.dirname(__file__), "users.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_users(self) -> None:
        """Persiste les utilisateurs et stats dans users.json."""
        path = os.path.join(os.path.dirname(__file__), "users.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.users, f, indent=2)

    def _record_game_result(self, winner: str, loser: str) -> None:
        """Incrémente les compteurs victoire/défaite et sauvegarde."""
        if winner in self.users:
            self.users[winner]["wins"] = self.users[winner].get("wins", 0) + 1
        if loser in self.users:
            self.users[loser]["losses"] = self.users[loser].get("losses", 0) + 1
        self._save_users()

    def _build_stats_view(self) -> List[ft.Control]:
        """Construit la liste des widgets du classement."""
        rows: List[ft.Control] = [
            ft.Divider(color=_COLOR_CELL_BORDER, thickness=1),
            ft.Text(
                "Classement",
                size=18,
                weight=ft.FontWeight.BOLD,
                color=_COLOR_DARK,
            ),
        ]
        for name, data in sorted(
            self.users.items(),
            key=lambda x: x[1].get("wins", 0),
            reverse=True,
        ):
            wins = data.get("wins", 0)
            losses = data.get("losses", 0)
            rows.append(
                ft.Text(
                    f"{name:<12} : {wins} victoire(s) - {losses} défaite(s)",
                    size=14,
                    color=_COLOR_CELL_BORDER,
                )
            )
        return rows

    def _show_end_game_stats(self) -> None:
        """Affiche le classement à la fin d'une partie."""
        self.stats_container.controls = self._build_stats_view()
        self.stats_container.visible = True

    def _show_login_screen(self) -> None:
        self._clear()

        self.username_field = ft.TextField(
            label="Nom d'utilisateur",
            width=250,
            text_align=ft.TextAlign.CENTER,
        )
        self.password_field = ft.TextField(
            label="Mot de passe",
            password=True,
            can_reveal_password=True,
            width=250,
            text_align=ft.TextAlign.CENTER,
        )
        self.login_error = ft.Text(
            "", size=14, color="red", weight=ft.FontWeight.BOLD
        )

        self.page.add(
            ft.Text("Quarto", size=36, weight=ft.FontWeight.BOLD, color=_COLOR_DARK),
            ft.Text("Connexion", size=20, color=_COLOR_CELL_BORDER),
            ft.Container(height=20),
            self.username_field,
            ft.Container(height=10),
            self.password_field,
            ft.Container(height=10),
            ft.Button(
                "Se connecter",
                on_click=lambda _: self._on_login(),
                bgcolor=_COLOR_CELL_BORDER,
                color="white",
                width=250,
            ),
            ft.Container(height=10),
            self.login_error,
        )

    def _on_login(self) -> None:
        username = self.username_field.value.strip()
        password = self.password_field.value.strip()

        user = self.users.get(username)
        if user and user.get("password") == password:
            self.current_user = username
            if self._game_id_from_url:
                self._try_join_remote_game(self._game_id_from_url)
            else:
                self._show_start_screen()
        else:
            self.login_error.value = "Nom d'utilisateur ou mot de passe incorrect."
            self.page.update()

    def _logout(self) -> None:
        self.current_user = None
        self.player2_user = None
        self.game_id = None
        self.player_role = None
        self._show_login_screen()

    def _show_player2_login(self) -> None:
        """Demande les identifiants du joueur 2 avant de démarrer une partie à 2."""
        self._clear()

        self.p2_username_field = ft.TextField(
            label="Nom du joueur 2",
            width=250,
            text_align=ft.TextAlign.CENTER,
        )
        self.p2_password_field = ft.TextField(
            label="Mot de passe du joueur 2",
            password=True,
            can_reveal_password=True,
            width=250,
            text_align=ft.TextAlign.CENTER,
        )
        self.p2_login_error = ft.Text(
            "", size=14, color="red", weight=ft.FontWeight.BOLD
        )

        self.page.add(
            ft.Text("Quarto", size=36, weight=ft.FontWeight.BOLD, color=_COLOR_DARK),
            ft.Text(
                "Connexion du joueur 2", size=20, color=_COLOR_CELL_BORDER
            ),
            ft.Container(height=20),
            self.p2_username_field,
            ft.Container(height=10),
            self.p2_password_field,
            ft.Container(height=10),
            ft.Button(
                "Commencer la partie",
                on_click=lambda _: self._on_player2_login(),
                bgcolor=_COLOR_CELL_BORDER,
                color="white",
                width=250,
            ),
            ft.Container(height=10),
            ft.Button(
                "Retour",
                on_click=lambda _: self._show_start_screen(),
                bgcolor="#8B4513",
                color="white",
                width=250,
            ),
            ft.Container(height=10),
            self.p2_login_error,
        )

    def _on_player2_login(self) -> None:
        username = self.p2_username_field.value.strip()
        password = self.p2_password_field.value.strip()

        if not username:
            self.p2_login_error.value = "Veuillez saisir un nom d'utilisateur."
            self.page.update()
            return

        if username == self.current_user:
            self.p2_login_error.value = "Le joueur 2 doit être différent du joueur 1."
            self.page.update()
            return

        user = self.users.get(username)
        if not user or user.get("password") != password:
            self.p2_login_error.value = "Nom d'utilisateur ou mot de passe incorrect."
            self.page.update()
            return

        self.player2_user = username
        self._start_game("2players", None)

    # ── Navigation écrans ──────────────────────────────────────────────────

    def _clear(self) -> None:
        self.page.controls.clear()
        self.page.update()

    def _show_start_screen(self) -> None:
        self.player2_user = None
        self.game_id = None
        self.player_role = None
        self._clear()
        self.page.add(
            ft.Text("Quarto", size=36, weight=ft.FontWeight.BOLD, color=_COLOR_DARK),
            ft.Text(
                f"Bienvenue, {self.current_user} !",
                size=16,
                color=_COLOR_CELL_BORDER,
                weight=ft.FontWeight.W_600,
            ),
            ft.Container(height=10),
            ft.Text("Choisissez votre mode de jeu", size=18, color=_COLOR_CELL_BORDER),
            ft.Container(height=20),
            ft.Button(
                "Solo vs Ordinateur",
                on_click=lambda _: self._choose_level(),
                bgcolor=_COLOR_CELL_BORDER,
                color="white",
                width=250,
            ),
            ft.Container(height=10),
            ft.Button(
                "2 Joueurs",
                on_click=lambda _: self._show_player2_login(),
                bgcolor=_COLOR_CELL_BORDER,
                color="white",
                width=250,
            ),
            ft.Container(height=10),
            ft.Button(
                "Connexion avec partenaire distant",
                on_click=lambda _: self._create_remote_game(),
                bgcolor="#2196F3",
                color="white",
                width=250,
            ),
            ft.Container(height=20),
            ft.Button(
                "Se déconnecter",
                on_click=lambda _: self._logout(),
                bgcolor="#8B4513",
                color="white",
                width=250,
            ),
        )

    def _choose_level(self) -> None:
        self._clear()
        self.page.add(
            ft.Text("Quarto", size=36, weight=ft.FontWeight.BOLD, color=_COLOR_DARK),
            ft.Text(
                "Choisissez le niveau de l'ordinateur",
                size=18,
                color=_COLOR_CELL_BORDER,
            ),
            ft.Container(height=20),
            ft.Button(
                "DEBUTANT",
                on_click=lambda _: self._start_game("solo", "DEBUTANT"),
                bgcolor="#4CAF50",
                color="white",
                width=250,
            ),
            ft.Container(height=10),
            ft.Button(
                "MOYEN",
                on_click=lambda _: self._start_game("solo", "MOYEN"),
                bgcolor="#FF9800",
                color="white",
                width=250,
            ),
            ft.Container(height=10),
            ft.Button(
                "EXPERT - CHLOE",
                on_click=lambda _: self._start_game("solo", "DIFFICILE"),
                bgcolor="#F44336",
                color="white",
                width=250,
            ),
            ft.Container(height=10),
            ft.Button(
                "Retour",
                on_click=lambda _: self._show_start_screen(),
                bgcolor=_COLOR_CELL_BORDER,
                color="white",
                width=250,
            ),
        )

    # ── Jeu ────────────────────────────────────────────────────────────────

    def _start_game(self, mode: str, level: Optional[str]) -> None:
        self.mode = mode
        self.computer_level = level

        self.board: List[Optional[Piece]] = [None] * 16
        self.available: List[Piece] = make_piece_set()
        self.current_player = 1
        self.piece_to_place: Optional[Piece] = None
        self.game_over = False

        self.status_text = ft.Text(
            "", size=20, weight=ft.FontWeight.BOLD, color=_COLOR_DARK
        )
        self.subtitle_text = ft.Text(
            "Jeu de stratégie 4×4", size=16, color=_COLOR_CELL_BORDER
        )
        self.piece_to_place_widget = ft.Container(
            width=self.piece_to_place_size,
            height=self.piece_to_place_size,
            bgcolor=_COLOR_CELL_BG,
            border=_border_all(2, _COLOR_HIGHLIGHT_BORDER),
            border_radius=8,
            alignment=ft.alignment.Alignment(0, 0),
        )
        self.piece_to_place_container = ft.Column(
            [
                ft.Text("Pièce à placer :", size=14, color=_COLOR_CELL_BORDER),
                self.piece_to_place_widget,
            ],
            spacing=5,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            visible=False,
        )
        self.board_label = ft.Text(
            "Plateau", size=18, weight=ft.FontWeight.W_600, color=_COLOR_DARK
        )
        self.board_column = ft.Column(spacing=10)
        self.pool_label = ft.Text(
            "Pièces disponibles",
            size=18,
            weight=ft.FontWeight.W_600,
            color=_COLOR_DARK,
        )
        self.pool_column = ft.Column(spacing=8)
        self.restart_button = ft.Button(
            "🔄 Recommencer",
            on_click=lambda _: self._reset(),
            bgcolor=_COLOR_CELL_BORDER,
            color="white",
        )
        self.menu_button = ft.Button(
            "🏠 Menu principal",
            on_click=lambda _: self._show_start_screen(),
            bgcolor=_COLOR_CELL_BORDER,
            color="white",
        )
        self.rules_text = ft.Text(
            "Règles : choisissez une pièce pour l'adversaire, qui doit la placer, "
            "puis choisit une pièce pour vous.",
            size=12,
            color=_COLOR_CELL_BORDER,
            italic=True,
        )
        self.stats_container = ft.Column(
            self._build_stats_view(),
            spacing=5,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            visible=False,
        )

        self._clear()
        self._update_sizes()
        self._build_game_layout()
        self._update_status()
        self._refresh()

    def _build_game_layout(self) -> None:
        self.page.add(
            ft.Text("Quarto", size=36, weight=ft.FontWeight.BOLD, color=_COLOR_DARK),
            self.subtitle_text,
            ft.Container(height=10),
            self.status_text,
            ft.Container(height=5),
            self.stats_container,
            ft.Container(height=5),
            self.piece_to_place_container,
            ft.Container(height=10),
            self.board_label,
            self.board_column,
            ft.Container(height=10),
            ft.Divider(color=_COLOR_CELL_BORDER, thickness=2),
            self.pool_label,
            self.pool_column,
            ft.Container(height=15),
            ft.Row(
                [self.restart_button, self.menu_button],
                spacing=10,
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            ft.Container(height=10),
            self.rules_text,
        )

    def _refresh(self) -> None:
        self.board_column.controls = self._build_board_rows()
        self.pool_column.controls = self._build_pool_rows()
        if self.piece_to_place is not None:
            self.piece_to_place_widget.width = self.piece_to_place_size
            self.piece_to_place_widget.height = self.piece_to_place_size
            self.piece_to_place_widget.content = self._piece_widget(
                self.piece_to_place, int(self.piece_to_place_size * 0.65)
            )
            self.piece_to_place_container.visible = True
        else:
            self.piece_to_place_container.visible = False
        self.page.update()

    def _build_board_rows(self) -> List[ft.Row]:
        rows: List[ft.Row] = []
        for r in range(4):
            cells: List[ft.Container] = []
            for c in range(4):
                idx = r * 4 + c
                cells.append(self._board_cell(idx))
            rows.append(
                ft.Row(cells, spacing=10, alignment=ft.MainAxisAlignment.CENTER)
            )
        return rows

    def _build_pool_rows(self) -> List[ft.Row]:
        """Retourne uniquement les pièces encore disponibles (grille dynamique)."""
        rows: List[ft.Row] = []
        cells: List[ft.Container] = []
        for piece in self.available:
            cells.append(self._pool_cell(piece))
            if len(cells) == self.pool_cols:
                rows.append(
                    ft.Row(cells, spacing=8, alignment=ft.MainAxisAlignment.CENTER)
                )
                cells = []
        if cells:
            rows.append(
                ft.Row(cells, spacing=8, alignment=ft.MainAxisAlignment.CENTER)
            )
        return rows

    def _player_label(self, player: int) -> str:
        """Retourne le nom d'affichage du joueur."""
        if self.mode == "remote" and self.game_id and self.game_id in GAMES:
            game = GAMES[self.game_id]
            if player == 1:
                return game["player1"]
            if player == 2:
                return game["player2"]
        if player == 1:
            return self.current_user
        if player == 2 and self.player2_user:
            return self.player2_user
        return f"Joueur {player}"

    def _update_status(self) -> None:
        """Met à jour le texte de statut selon la phase et le mode."""
        if self.game_over:
            return
        p = self._player_label
        if self.mode == "solo":
            if self.current_player == 1:
                if self.piece_to_place is None:
                    self.status_text.value = (
                        f"{p(1)} : choisissez une pièce pour l'ordinateur"
                    )
                else:
                    self.status_text.value = (
                        f"{p(1)} : placez la pièce choisie par l'ordinateur"
                    )
            else:
                self.status_text.value = "L'ordinateur réfléchit..."
        else:
            other = 3 - self.current_player
            if self.piece_to_place is None:
                self.status_text.value = (
                    f"{p(self.current_player)} : choisissez une pièce "
                    f"pour {p(other)}"
                )
            else:
                self.status_text.value = (
                    f"{p(self.current_player)} : placez la pièce "
                    f"choisie par {p(other)}"
                )

    # ── Partie à distance ──────────────────────────────────────────────────

    def _extract_game_id(self) -> Optional[str]:
        """Extrait l'identifiant de partie depuis l'URL."""
        try:
            query = getattr(self.page, "query", None)
            if query:
                return query.get("game")
        except Exception:
            pass
        route = getattr(self.page, "route", "") or ""
        if "?" in route:
            qs = route.split("?", 1)[1]
            params = urllib.parse.parse_qs(qs)
            ids = params.get("game", [])
            if ids:
                return ids[0]
        try:
            url = getattr(self.page, "url", "") or ""
            if "?" in url:
                parsed = urllib.parse.urlparse(url)
                params = urllib.parse.parse_qs(parsed.query)
                ids = params.get("game", [])
                if ids:
                    return ids[0]
        except Exception:
            pass
        return None

    def _create_remote_game(self) -> None:
        """Crée une nouvelle partie distante et affiche le lien à partager."""
        game_id = str(uuid.uuid4())[:8]
        self.game_id = game_id
        self.player_role = 1

        GAMES[game_id] = {
            "player1": self.current_user,
            "player2": None,
            "board": [None] * 16,
            "available": make_piece_set(),
            "current_player": 1,
            "piece_to_place": None,
            "game_over": False,
        }

        self._show_waiting_screen(game_id)

    def _show_waiting_screen(self, game_id: str) -> None:
        """Affiche l'écran d'attente avec l'URL à partager."""
        self._clear()
        host = (
            "127.0.0.1"
            if _SERVER_INFO["host"] in ("0.0.0.0", "127.0.0.1")
            else _SERVER_INFO["host"]
        )
        url = f"http://{host}:{_SERVER_INFO['port']}/?game={game_id}"

        self.page.add(
            ft.Text("Quarto", size=36, weight=ft.FontWeight.BOLD, color=_COLOR_DARK),
            ft.Text("Partie créée !", size=24, color=_COLOR_CELL_BORDER),
            ft.Container(height=10),
            ft.Text("En attente du joueur 2...", size=18, color=_COLOR_CELL_BORDER),
            ft.Container(height=20),
            ft.Text(
                "Partagez ce lien avec votre partenaire :",
                size=14,
                color=_COLOR_CELL_BORDER,
            ),
            ft.Container(height=5),
            ft.Text(
                url,
                size=14,
                color=_COLOR_DARK,
                weight=ft.FontWeight.BOLD,
                selectable=True,
            ),
            ft.Container(height=20),
            ft.Button(
                "Annuler",
                on_click=lambda _: self._show_start_screen(),
                bgcolor="#8B4513",
                color="white",
                width=250,
            ),
        )

    def _try_join_remote_game(self, game_id: str) -> None:
        """Tente de rejoindre une partie existante en tant que joueur 2."""
        if game_id not in GAMES:
            self._show_login_error("Partie introuvable.")
            return

        game = GAMES[game_id]
        if game.get("player2"):
            self._show_login_error("Cette partie est déjà complète.")
            return
        if game["player1"] == self.current_user:
            self._show_login_error(
                "Vous ne pouvez pas jouer contre vous-même."
            )
            return

        self.game_id = game_id
        self.player_role = 2
        game["player2"] = self.current_user

        # Notifie le joueur 1 que le joueur 2 a rejoint
        self.page.pubsub.send_all(
            {"game_id": game_id, "action": "player_joined"}
        )

        self._start_remote_game()

    def _show_login_error(self, message: str) -> None:
        """Affiche un message d'erreur sur l'écran de login."""
        self.login_error.value = message
        self.page.update()

    def _start_remote_game(self) -> None:
        """Démarre l'interface de jeu pour une partie distante."""
        self._start_game("remote", None)
        self._sync_remote_state()

    def _sync_remote_state(self) -> None:
        """Synchronise l'état local depuis le state global GAMES."""
        if not self.game_id or self.game_id not in GAMES:
            return
        game = GAMES[self.game_id]
        self.board = game["board"]
        self.available = game["available"]
        self.current_player = game["current_player"]
        self.piece_to_place = game["piece_to_place"]
        self.game_over = game["game_over"]
        self._update_status()
        self._refresh()

    def _publish_remote_update(self, action: str = "update") -> None:
        """Publie un message pubsub pour synchroniser les joueurs distants."""
        if self.game_id:
            self.page.pubsub.send_all(
                {"game_id": self.game_id, "action": action}
            )

    def _on_pubsub_message(self, message) -> None:
        """Gère les messages pubsub entrants."""
        if not isinstance(message, dict):
            return
        if message.get("game_id") != self.game_id:
            return

        action = message.get("action")
        if action == "player_joined" and self.player_role == 1:
            self._start_remote_game()
        elif action in ("update", "reset"):
            self._sync_remote_state()

    def _on_piece_click_remote(self, piece: Piece) -> None:
        """Gère le choix d'une pièce en mode distant."""
        if self.game_over or self.piece_to_place is not None:
            return
        if self.current_player != self.player_role:
            return
        if piece not in self.available:
            return

        game = GAMES[self.game_id]
        game["piece_to_place"] = piece
        game["available"].remove(piece)
        game["current_player"] = 3 - game["current_player"]

        self._publish_remote_update()
        self._sync_remote_state()

    def _on_cell_click_remote(self, idx: int) -> None:
        """Gère le placement d'une pièce en mode distant."""
        if self.game_over or self.piece_to_place is None:
            return
        if self.current_player != self.player_role:
            return
        if self.board[idx] is not None:
            return

        game = GAMES[self.game_id]
        game["board"][idx] = game["piece_to_place"]
        game["piece_to_place"] = None

        if is_winning_board(game["board"]):
            game["game_over"] = True
            winner_name = (
                game["player1"] if game["current_player"] == 1 else game["player2"]
            )
            loser_name = (
                game["player2"] if game["current_player"] == 1 else game["player1"]
            )
            self._record_game_result(winner_name, loser_name)
            self._publish_remote_update()
            self._sync_remote_state()
            self._show_end_game_stats()
            return

        if not game["available"]:
            game["game_over"] = True
            self._publish_remote_update()
            self._sync_remote_state()
            self._show_end_game_stats()
            return

        self._publish_remote_update()
        self._sync_remote_state()

    def _on_piece_click(self, piece: Piece) -> None:
        if self.mode == "remote":
            self._on_piece_click_remote(piece)
            return
        if self.game_over or self.piece_to_place is not None:
            return
        if piece not in self.available:
            return

        self.piece_to_place = piece
        self.available.remove(piece)
        self.current_player = 3 - self.current_player
        self.status_text.value = "Réflexion en cours ..."
        self._update_status()
        self._refresh()

        if self.mode == "solo" and self.current_player == 2:
            self.status_text.value = "Réflexion en cours ..."
            self._play_computer_turn()

    def _on_cell_click(self, idx: int) -> None:
        if self.mode == "remote":
            self._on_cell_click_remote(idx)
            return
        if self.game_over or self.piece_to_place is None:
            return
        if self.board[idx] is not None:
            return

        self.board[idx] = self.piece_to_place
        self.piece_to_place = None

        if is_winning_board(self.board):
            self.game_over = True
            winner = (
                "L'ordinateur"
                if (self.mode == "solo" and self.current_player == 2)
                else self._player_label(self.current_player)
            )
            self.status_text.value = f"🎉 {winner} a gagné !"
            if self.mode == "2players":
                winner_name = (
                    self.current_user if self.current_player == 1 else self.player2_user
                )
                loser_name = (
                    self.player2_user if self.current_player == 1 else self.current_user
                )
                self._record_game_result(winner_name, loser_name)
                self._show_end_game_stats()
            self._refresh()
            return

        if not self.available:
            self.game_over = True
            self.status_text.value = "🤝 Match nul !"
            if self.mode == "2players":
                self._show_end_game_stats()
            self._refresh()
            return

        self._update_status()
        self._refresh()

    def _play_computer_turn(self) -> None:
        """Tour de l'ordinateur (placement + choix automatiques)."""
        if self.game_over or self.piece_to_place is None:
            return

        # L'ordinateur joue : il place la pièce reçue ET choisit la pièce suivante pour le joueur
        try:
            pos, next_piece = get_computer_move(
                self.board, 
                self.piece_to_place, 
                self.available, 
                self.computer_level
            )
        except ValueError:
            self.game_over = True
            self.status_text.value = "🤝 Match nul !"
            self._refresh()
            return

        # 1. Placement de la pièce reçue par l'ordinateur
        self.board[pos] = self.piece_to_place
        self.piece_to_place = None

        if is_winning_board(self.board):
            self.game_over = True
            self.status_text.value = "🎉 L'ordinateur a gagné !"
            self._refresh()
            return

        if not self.available:
            self.game_over = True
            self.status_text.value = "🤝 Match nul !"
            self._refresh()
            return

        # 2. Assignation de la pièce choisie par l'ordinateur pour le Joueur 1
        if next_piece in self.available:
            self.piece_to_place = next_piece
            self.available.remove(next_piece)

        self.current_player = 1
        self.status_text.value = (
            f"{self._player_label(1)} : placez la pièce choisie par l'ordinateur"
        )
        self._refresh()

    def _reset(self) -> None:
        if self.mode == "remote" and self.game_id and self.game_id in GAMES:
            game = GAMES[self.game_id]
            game["board"] = [None] * 16
            game["available"] = make_piece_set()
            game["current_player"] = 1
            game["piece_to_place"] = None
            game["game_over"] = False
            self.page.pubsub.send_all(
                {"game_id": self.game_id, "action": "reset"}
            )
            self._sync_remote_state()
            return
        self.board = [None] * 16
        self.available = make_piece_set()
        self.current_player = 1
        self.piece_to_place = None
        self.game_over = False
        self.stats_container.visible = False
        self._update_status()
        self._refresh()


# ── Point d'entrée ───────────────────────────────────────────────────────────


def main(page: ft.Page) -> None:
    QuartoApp(page)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Quarto Web — Serveur Flet")
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port du serveur web (défaut: 8080)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Hôte sur lequel écouter (défaut: 127.0.0.1 pour local, utiliser 0.0.0.0 pour PM2/Production)",
    )
    args = parser.parse_args()
    _SERVER_INFO["host"] = args.host
    _SERVER_INFO["port"] = args.port
    ft.run(
        main=main,
        port=args.port,
        host=args.host,
        view=ft.AppView.WEB_BROWSER  # Force Flet à ouvrir/servir le site web
    )
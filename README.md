# Quarto local game

This repository now includes a small local Quarto implementation for playing on this PC.

## What it is

Quarto is a two-player abstract strategy game played on a 4x4 board. Each turn, the current player chooses one of the remaining pieces and places it on the board. The first player to complete a line where all four pieces share at least one attribute wins.

## How to run

### Console mode

From the project root:

```bash
./run_quattro.sh
```

Or with Python directly:

```bash
python3 quarto.py
```

### Graphical mode (Pygame)

Requires a virtual environment with Pygame:

```bash
uv venv .env
source .env/bin/activate
uv pip install pygame
python3 quarto_gui.py
```

**Controls:**
- **Clic gauche** — sélectionner une pièce dans les disponibles, puis cliquer sur une case du plateau pour la placer.
- **R** — redémarrer la partie.
- **Échap / Q** — quitter.

### Web mode (Flet)

Accessible depuis un navigateur. Nécessite Flet dans le venv :

```bash
source .env/bin/activate
uv pip install flet
python quarto_flet.py --port 8080
```

Puis ouvrez `http://localhost:8080`.

**Pour le déploiement internet** (nginx + pm2) :
- Flet expose un serveur web + WebSocket sur le port choisi.
- Configurez nginx en reverse proxy avec support WebSocket (`proxy_http_version 1.1`, `Upgrade` et `Connection` headers).
- Utilisez pm2 pour garder le processus Python actif.

## Parameters (console)

- `--demo`: prints a short description of the game and exits.
- `--help`: shows the available command-line options.

## Gameplay (console)

- Enter a 4-digit binary piece code such as `1010`.
- Enter a board position from `0` to `15`.
- The board is displayed as a 4x4 grid of positions.

## Validation

The implementation is verified with the built-in unit tests:

```bash
python3 -m unittest -q
```

# Software engineering:
```
python3 ai-coding-playbook/scripts/generate_rules.py --tool kimi --clean --config playbook.yaml --project-status in_progress
```

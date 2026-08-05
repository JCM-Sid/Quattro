# Project Overlay — Quattro

## Identity

- **Product name:** Quattro (local Quarto board game)
- **Domain:** Two-player abstract strategy game with optional solo mode vs. computer
- **Stack:** Python 3, standard library only (no external dependencies)
- **Language:** French UI labels and CLI feedback; code comments and identifiers in English

## File map

| File | Role |
|------|------|
| `quarto.py` | main script: 2 players or solo mode + 3 computer levels (DEBUTANT, MOYEN, DIFFICILE) |
| `run_quattro.sh` | Launcher entry-point (`python3 quarto.py`) |
| `tests/test_quarto.py` | Unit tests for core game logic (piece set, win detection, move application) |
| `playbook.yaml` | ai-coding-playbook local config |
| `./ai-coding-playbook/scripts/generate_rules.py` | Derived-rule generator (Cursor / Claude / Kimi) |

## CLI

```bash
# Run the game (two players or solo)
./run_quattro.sh
python3 quarto.py

# Run tests
python3 -m unittest -q
python3 -m unittest discover -s tests -v

# Regenerate derived rules (KIMI.md, .cursor/rules, .claude/rules, etc.)
python3 scripts/generate_rules.py --tool all --clean
```

## Game rules (domain invariants)

- 4×4 board (positions 0–15).
- 16 unique pieces, each defined by 4 binary attributes: `(color, shape, size, fill)`.
- A line of four sharing **at least one** attribute wins.
- In `quarto.py` solo mode, the computer picks a piece **and** a position for the player, then places it.

## Architecture notes
- No external dependencies → no `requirements.txt`, `pyproject.toml`, or lockfile.

## Conventions

- Branches: `feature/<name>`, `fix/<name>`, `release/<version>` (see `git-worktrees` pack).
- Keep French UI strings; keep code identifiers in English.
- Test-first for game-logic changes; manual play-test for UX changes.

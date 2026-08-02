# Quarto local game

This repository now includes a small local Quarto implementation for playing on this PC.

## What it is

Quarto is a two-player abstract strategy game played on a 4x4 board. Each turn, the current player chooses one of the remaining pieces and places it on the board. The first player to complete a line where all four pieces share at least one attribute wins.

## How to run

From the project root:

```bash
./run_quarto.sh
```

Or with Python directly:

```bash
python3 quarto.py
```

## Parameters

- `--demo`: prints a short description of the game and exits.
- `--help`: shows the available command-line options.

## Gameplay

- Enter a 4-digit binary piece code such as `1010`.
- Enter a board position from `0` to `15`.
- The board is displayed as a 4x4 grid of positions.

## Validation

The implementation is verified with the built-in unit tests:

```bash
python3 -m unittest -q
```

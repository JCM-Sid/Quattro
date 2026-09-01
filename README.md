# Quarto local game

This repository now includes a small local Quarto implementation for playing on this PC.

## What it is

Quarto is a two-player abstract strategy game played on a 4x4 board. Each turn, the current player chooses one of the remaining pieces and places it on the board. The first player to complete a line where all four pieces share at least one attribute wins.

## How to run

via url:
[https://quarto.apps.ddcm.fr/]

pm2:
```bash
pm2 start /home/jch_m/Proj/Quattro/.env/bin/python --name "Quattro" -- /home/jch_m/Proj/Quattro/quarto_flet.py --host 0.0.0.0 --port 8082
```


### Web mode (Flet)

Accessible depuis un navigateur. Nécessite Flet dans le venv :

```bash
source .env/bin/activate
uv pip install flet
python quarto_flet.py --port 8080
```

Puis ouvrez `http://localhost:8080`.

L'écran de jeu affiche les boutons *Recommencer*, *Menu principal* et *Règles du jeu* sous le titre, au-dessus du plateau et du pool de pièces. Le bouton *Règles du jeu* ouvre une fenêtre pop-up avec les règles complètes du Quarto.

Au démarrage, un écran de connexion permet de se connecter avec un compte existant ou d'en créer un nouveau (vérification de l'unicité du nom et confirmation du mot de passe). Les comptes et les statistiques sont stockés dans `users.json`.

**Pour le déploiement internet** (nginx + pm2) :
- Flet expose un serveur web + WebSocket sur le port choisi.
- Configurez nginx en reverse proxy avec support WebSocket (`proxy_http_version 1.1`, `Upgrade` et `Connection` headers).
- Utilisez pm2 pour garder le processus Python actif.

Puis ouvrez `https://quarto.apps.ddcm.fr`.


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
./project-overlay.md
```

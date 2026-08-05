## 2026-08-05 — Règles du Quarto corrigées (vrai Quarto)
- **Decision:** Inverser le flow de jeu dans `quarto_flet.py` pour respecter les vraies règles du Quarto : le joueur choisit une pièce pour son adversaire, qui doit la placer, puis choisit une pièce en retour.
- **Context:** L'ancienne implémentation faisait sélectionner ET placer une pièce par le même joueur au même tour. L'utilisateur souhaite la règle officielle où la sélection et le placement sont séparés entre les deux joueurs.
- **Consequences:**
  - Nouvel état `piece_to_place` : la pièce choisie par l'adversaire, affichée visuellement dans un encadré dédié sous le statut.
  - `available` ne contient que les pièces réellement disponibles ; la pièce à placer est retirée dès la sélection.
  - En mode solo, l'ordinateur exécute deux phases consécutives : placement de la pièce reçue, puis choix d'une nouvelle pièce pour le joueur.
  - Le pool ne permet plus de clic quand une pièce est en attente de placement (`piece_to_place is not None`).
  - Le match nul est détecté après le dernier placement (quand `available` est vide et `piece_to_place` est `None`).
  - Token consumption : non mesuré.

## 2026-08-03 — Interface web Flet pour Quarto (mode solo + pool dynamique)
- **Decision:** Créer `quarto_flet.py` avec Flet (Flutter web) pour jouer dans un navigateur, avec écran de démarrage proposant mode Solo (3 niveaux) ou 2 Joueurs, et corriger le rendu du pool de pièces.
- **Context:** L'utilisateur souhaite une version web accessible via nginx/pm2. Flet 0.86.5 est installé dans le venv existant. Deux bugs bloquaient l'expérience : le pool de pièces disparaissait prématurément (grille 4×4 fixe avec cases vides) et le mode solo manquait.
- **Consequences:**
  - `quarto_flet.py` remplace la logique console par une UI web complète.
  - Écran de démarrage : choix "Solo vs Ordinateur" (DEBUTANT/MOYEN/DIFFICILE) ou "2 Joueurs".
  - Le pool utilise `ft.Wrap` dynamique : seules les pièces réellement disponibles sont affichées, éliminant le bug de cases vides qui masquaient les pièces restantes.
  - Compatibilité Flet 0.86.5 : pas de `ft.border.all` ni `ft.alignment.center` ; utilisation de `ft.Border` avec `ft.BorderSide` et `ft.alignment.Alignment(0, 0)`.
  - L'ordinateur joue automatiquement après le joueur humain en mode solo via `get_computer_move()` existant.
  - Token consumption : non mesuré.

## 2026-08-03 — Interface graphique Pygame pour Quarto
- **Decision:** Créer `quarto_gui.py` avec Pygame pour jouer visuellement : plateau 4×4, pièces disponibles cliquables, sélection et placement à la souris.
- **Context:** L'utilisateur souhaite une version graphique du jeu existant en console. Pygame est choisi pour un rendu 2D simple sans dépendance lourde.
- **Consequences:**
  - Nouveau fichier `quarto_gui.py` réutilisant la logique métier de `quarto.py`.
  - Environnement virtuel `.env` créé via `uv venv .env` pour isoler Pygame.
  - README mis à jour avec instructions d'installation et lancement GUI.
  - Même logique de jeu (sélection pièce → placement → vérification victoire) mais avec interaction souris au lieu de saisie console.

## 2026-08-03 — Génération unifiée des règles agents (Kimi + Cursor + Claude)
- **Decision:** Intégrer le support Kimi directement dans `ai-coding-playbook/scripts/generate_rules.py` pour émettre `KIMI.md`, `.kimi/agents/*.md` et `.kimi-code/local.toml` au même titre que les règles Cursor/Claude.
- **Context:** Les règles Kimi étaient maintenues à la main dans `KIMI.md` et `AGENTS.md`, ce qui créait une divergence avec le catalogue `ai-coding-playbook`. L'objectif est un flux de génération unique déclenché par `--tool all --clean`.
- **Consequences:**
  - `KIMI.md` devient un fichier dérivé regénéré automatiquement (mode posture + core rules + pack rules + overlay projet).
  - `AGENTS.md` et `SYSTEM.md` supprimés : `KIMI.md` est le seul point d'entrée pour Kimi Code CLI.
  - `project-overlay.md` créé pour stocker le contexte produit spécifique à Quattro (nom, stack, conventions).
  - Le générateur extrait automatiquement le nom du projet depuis `project-overlay.md` pour `.kimi-code/local.toml`.

## 2026-08-03 — Gestion des règles différées dans KIMI.md
- **Decision:** Corriger le générateur Kimi pour qu'il affiche correctement la section "Deferred Rules" dans `KIMI.md` même quand les règles différées proviennent du `project_status` par défaut (ex. `in_progress` → `architecture-principles` + `configuration-boundaries` différées).
- **Context:** Le générateur lisait `config.get("deferred_rules")` dans `playbook.yaml`, mais cette clé est absente quand les valeurs par défaut sont déduites du manifeste via `project_status`.
- **Consequences:** `KIMI.md` affiche désormais explicitement les règles temporairement différées, ce qui informe l'agent de ne les appliquer que sur le code nouveau ou modifié.

## 2026-08-02 — Mode solo et niveaux d'IA pour Quarto
- **Decision:** Ajouter un mode de jeu solo contre l'ordinateur avec trois niveaux de difficulté (DEBUTANT, MOYEN, DIFFICILE) via les arguments CLI.
- **Context:** Le prototype ne supportait que le mode 2 joueurs humains. L'utilisateur souhaite pouvoir jouer seul avec une IA paramétrable.
- **Consequences:** Le parser d'arguments accepte désormais `quarto 2` et `quarto seul <niveau>`. La logique IA reste simple (random / coup gagnant / look-ahead d'un tour) pour rester proportionnée à un prototype.

## 2026-08-02 — Stratégie IA par niveau
- **Decision:** Définir trois stratégies distinctes sans dépendance externe.
  - DEBUTANT : choix aléatoire pur de la pièce et de la position.
  - MOYEN : joue un coup gagnant immédiat s'il existe, sinon aléatoire.
  - DIFFICILE : coup gagnant immédiat, sinon évite de donner un coup gagnant à l'adversaire au tour suivant (défense par look-ahead d'un tour).
- **Context:** L'utilisateur a précisé que le débutant "ne choisit pas toujours la meilleure option". Le minimax complet était jugé trop lourd pour un prototype.
- **Consequences:** Le code reste dans un seul fichier, sans bibliothèque externe. La distinction entre les niveaux est claire et testable manuellement.

## 2026-08-02 — Branches main et develop
- **Decision:** Merger la feature `feature/quarto-local` dans `main` à la demande explicite de l'utilisateur, puis créer `develop` à partir de `main` pour les futures intégrations.
- **Context:** Le playbook du projet stipule que `develop` est la cible d'intégration et `main` est release-only. Le repo n'avait initialement ni `main` ni `develop`.
- **Consequences:** `main` contient désormais le code fonctionnel. `develop` est disponible pour les prochaines branches de feature/fix. Il faudra baser les futurs travaux sur `develop`.

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

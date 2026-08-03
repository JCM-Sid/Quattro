---
name: "git-workflow-automation"
description: "Deterministic publish and finish of feature/fix into develop"
tools: ["read_file", "edit_file", "bash"]
---

# git-workflow-automation

**Tier:** pack  
**Pack:** git-workflow-automation  
**Modes:** all

# Git workflow automation

## Applicability

Optional pack for projects that already use `git-workflow` and want a
**deterministic** path to publish a finished `feature/*` or `fix/*` branch,
then integrate it into `develop`. Disable it if merges stay fully manual or
PR-based.

Requires the `git-workflow` pack (declared via `requires:` in the manifest;
selecting this pack expands to include it).

## Finish feature / fix

Do **not** hand-roll `checkout` / `merge` / `push develop` for a change branch.
Use the generated scripts under `scripts/git-workflow/`:

1. **Publish the change branch** (optional intermediate step): after the work
   is committed, `scripts/git-workflow/publish.sh feature/<name>` (or
   `fix/<name>`). Refuses a dirty dedicated worktree. Use this to share the
   branch without integrating yet.
2. **Integrate into develop**:
   `scripts/git-workflow/finish.sh feature <name>` (or `fix <name>`).
   Runs `check_command` from `playbook.yaml` when set, **pushes the change
   branch**, merges `--no-ff` into `develop`, pushes `develop`, removes the
   worktree and local branch, and deletes the remote branch.

`finish` always publishes the change branch before merging, so local cleanup
is not blocked by an outdated remote-tracking ref. A prior `publish` remains
optional when you only want to share the branch early.

## Agent consent

- An explicit request to **validate / publish the change branch** (e.g.
  « validé ») is consent to commit if needed, then run `publish.sh`.
- An explicit request to **finish / integrate to develop** (e.g. « go dev »)
  is consent to commit the current change if needed, then run `finish.sh`
  (includes push of the change branch, push of `develop`, and remote branch
  delete via that script). Stage only files belonging to the feature / fix;
  `finish.sh` still refuses a dirty worktree.

Those phrases are examples of consent wording, not the only accepted forms.
Push outside these scripts remains gated by `agent-permissions`.

## Checks

Optional `check_command:` in `playbook.yaml` is injected into `finish.sh`
at generate time (same pattern as `format_command` for the pre-commit hook).
When unset, the script continues with a clear message — projects without a
suite must still honour any documented manual checks from `git-worktrees`.

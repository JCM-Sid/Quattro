---
name: "git-worktrees"
description: "Git workflow, branches, and worktrees"
tools: ["read_file", "edit_file", "bash"]
---

# git-worktrees

**Tier:** pack  
**Pack:** git-workflow  
**Modes:** all

# Git workflow

## Applicability

Rule for projects that adopt the classic Gitflow `main` / `develop` /
`release/*` workflow with one branch and one worktree per change. Disable it if
the project uses a different Git workflow.

## Branch roles

| Branch | Role |
|--------|------|
| `main` | Released version |
| `develop` | Integration branch |
| `release/<version>` | Release preparation (last-mile only) |

- `main` only evolves via intentional merge from a `release/*` branch, then tag
  `v<version>` (e.g. `release/1.2.0` → tag `v1.2.0`).
- `develop` is modified by merging a change classified as a feature or fix
  (normally a `feature/*` or `fix/*` branch), and by merging a finished
  `release/*` back into `develop`.
- Do not merge `develop` directly into `main`.

## Choosing the branch type

| Prefix | When |
|--------|------|
| `feature/<name>` | New capability, improvement, intentional behavior change |
| `fix/<name>` | Bug fix, regression, incorrect behavior |
| `release/<version>` | Freeze a release from `develop` (version, changelog, release-only fixes) |

Choose the prefix based on the nature of the request — **do not put everything under `feature/`**. No `hotfix/` from `main`.

## Execution environment constraints

Execution environments may impose mechanics such as branch names, checkout
locations, worktree models, or pull-request flows. Treat those constraints as
adapters, not as project workflow decisions.

Preserve the project invariants:

- Start changes from `develop` and integrate them back into `develop`.
- Keep `main` reserved for intentional releases.
- Classify every change semantically as a feature, fix, or release, even when
  the environment mandates a different physical branch name.
- Run the required checks before integration.
- Use the project's generated workflow automation when it is available.

Prefer explicit project configuration over environment defaults whenever the
environment permits it. Adapt routine, reversible mechanics automatically; do
not ask the user to restate the established workflow. If a mandatory constraint
makes an invariant impossible, report the conflict before changing project
files.

## Worktree discipline

**1 change = 1 branch = 1 dedicated worktree** (including a release). Never reuse
a worktree for another change or switch branches inside a dedicated worktree.

Use the generated Git workflow scripts to create worktrees, finish releases,
clean merged branches, and check releases. Do not reproduce their mechanics
manually. After merge into `develop` (or after finishing a release), clean up
the worktree and branch immediately.

Optional pack `git-workflow-automation` adds deterministic scripts to publish a
`feature/*` or `fix/*` branch and finish it into `develop` (`publish`,
`finish`). Enable it separately when that automation is wanted.

Enabling this pack also emits **tool permission** artefacts for the host IDE/CLI.
Today that means a managed `.cursor/permissions.json` (Cursor Auto-review
adapter — first tool adapter; other tools may follow). It steers automatic
approval for routine worktree/merge commands; it does not replace the
tests-before-merge gate below.

## Tests before merge

**Blocking**: never merge a `feature/*` or `fix/*` branch into `develop` until the project checks have been run **and are green** in the change's worktree. The exact test command is project-specific (documented in the overlay / README, e.g. `poetry run pytest`).

If the project has no automated test suite yet: say so explicitly, and do not invent a command. Documented manual checks remain blocking if they exist. Refuse the merge if a required check fails — do not merely offer to run it afterward.

## Release

1. Run `scripts/git-workflow/check_release.sh` and resolve any unmerged
   `feature/` / `fix/` branch first.
2. Create the release worktree:
   `scripts/git-workflow/new_worktree.sh release <version>`.
3. On `release/<version>`, do last-mile work only (version bump, changelog,
   release-only fixes).
4. Finish with `scripts/git-workflow/release.sh <version>`: merge into
   `main`, tag `v<version>`, merge back into `develop`, then clean up the
   worktree and branch.

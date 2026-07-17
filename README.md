# Learning OS v3 — Repository

Plain-file knowledge repository for deep technical learning. Fresh Git repository, scaffolded 2026-07-16 (Stage 1, Phase 2 of the migration).

## Quick start

The **operator** is whoever drives this repository through its rules — normally
Claude reading `CLAUDE.md`, but a person with a text editor and Git can operate
it by hand. The repository is the source of truth; the operator only files,
links, and rebuilds views. Everything under `generated/` is a disposable view —
never edit it.

1. **With Claude:** open this folder in a chat and say what you're working on.
   The operator reads `CLAUDE.md`, then `work/COORDINATION.md` +
   `records/modules.yaml`, then your active workspace. That's the whole interface.
2. **By hand:** exam facts live in `records/modules.yaml`; "what should I do
   next?" is `generated/coordination-view.md` (run `make views` to refresh);
   your knowledge is under `knowledge/notes/`; capture anything into `work/inbox/`.
3. **After editing:** run `make check`. The pre-commit hook blocks commits while
   the validator reports errors.

The rest of this file is the full manual; the four commands are under
[Commands](#commands).

- **What this is / how it works:** `system/SPEC-README.md` → `system/PHILOSOPHY.md` → `system/ARCHITECTURE.md`
- **How the operator behaves:** `system/CLAUDE.md` — the single canonical contract; root `CLAUDE.md` (and the `LearningOS/` project-root entry) are symlinks to it
- **Migration state:** **COMPLETE — cutover 2026-07-17.** Pilot approved (5/5 frozen criteria, `migration/pilot-report.md`); Stage 2 full migration executed same day (`migration/final-report.md`). This repository is the operational root; the legacy `semestercontext/` tree is frozen history (banners point here).
- **Legacy:** the frozen pre-v3 tree is `semestercontext/` (tag `pre-v3-baseline`); this folder is designed to be moved beside it after cutover.
- **Roots:** materials → `../materials/` (`material://<source-id>/…` resolves there), code projects → `../projects/` — both outside the authored tree by design (materials move in Stage 2, Step 8).

## How to use it (the whole manual)

**Start a session:** open this folder in a chat. The operator reads `CLAUDE.md`,
then `work/COORDINATION.md` + `records/modules.yaml`, then your active
workspace. You just say what you're working on.

**"What should I do next?"** → the operator rebuilds and reads the coordination
view (exam spine + every workspace's next action). Recommendations are computed
fresh, never read from stored plans.

**Study something:** name the concept — German works ("Kettenregel",
"Hypothesentest"). You get: your notes on it, its prerequisites (dependency
report), and the best source for the purpose — first learning, review,
derivation, drill (selector views).

**Capture anything:** drop it in `work/inbox/` or your workspace `scratch/` —
photos of handwritten pages included. No naming, no filing; say what it is and
the operator routes it. If you ever catch yourself making a filing decision,
stop — that's the operator's job.

**Something becomes worth keeping:** it turns into a note under `knowledge/`
(your reasoning preserved verbatim; the operator asks before any semantic
rewrite, split, or merge).

**A fact changes** ("I registered for X", "deferring Y"): say it once. Exam
events land ONLY in `records/modules.yaml`, decisions in `COORDINATION.md` —
never in prose copies.

**An effort ends:** its workspace is archived whole; the durable notes stay.

**Trust but verify:** `python tools/validate.py` after any batch of edits
(session-end habit). Never edit anything under the generated output tree —
it's a disposable view; delete it freely.

## Without the operator (human fallback — no Claude needed)

Everything is plain text; nothing requires any tool to read. The four questions:

- **Exam dates, registrations, grades?** Open `records/modules.yaml` — it is
  commented and readable raw. This file is the only truth for those facts.
- **What should I do next?** Run `make views` (or `python tools/generate.py`),
  then open `generated/coordination-view.md` — exam spine, every workspace's
  next action, neglect signals. Check its `Generated:` timestamp; if views feel
  stale, rebuild (the post-commit hook does this automatically after commits).
- **Where is my knowledge on X?** Browse `knowledge/notes/<domain>/` —
  filenames say what they are — or ctrl-F `generated/concept-index.md`
  (German terms work; aliases are indexed). The prerequisite graph is drawn in
  `generated/concept-map.md`.
- **Where do I put this?** `work/inbox/` — no naming, no filing, ever.

If something looks broken: `make check` names every problem; `git log` is the
history; `generated/` can always be deleted and rebuilt. No proprietary
anything — a text editor and Git are enough to operate this repository forever.

## Commands

```bash
make setup      # once per clone/move: create .venv, install deps, install both Git hooks
make check      # validate (schemas + VALIDATION.md rules)
make views      # rebuild everything under the gitignored output tree
make test       # test suite
make            # list the one-word commands
```

`make setup` creates a project-local virtual environment at `.venv/` (gitignored)
from `requirements-dev.txt`, so the tooling never touches your system Python —
this sidesteps the PEP 668 / Homebrew "externally-managed-environment" error you
hit on a clean macOS install. Every later `make` target and both Git hooks use
`.venv/bin/python` automatically when it exists, and fall back to the system
`python3` otherwise. Build with a specific interpreter via
`make setup PYTHON=python3.12`.

(Equivalent direct calls once the venv exists: `.venv/bin/python tools/validate.py`
[`--online` adds the URL audit], `.venv/bin/python tools/generate.py`,
`.venv/bin/python -m pytest`.) Requires Python 3.10+, `pyyaml`, `jsonschema>=4`,
`pytest` — the tools fail fast with the exact fix if a dependency is missing or
too old.

Two Git hooks (canonical copies in `tools/hooks/`, installed by `make setup`):
**pre-commit** blocks any commit while the validator reports errors (warnings
print but never block); **post-commit** rebuilds `generated/` so the local
dashboards are never stale.

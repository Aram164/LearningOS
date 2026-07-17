# Learning OS v3 — Repository

Plain-file knowledge repository for deep technical learning. Fresh Git repository, scaffolded 2026-07-16 (Stage 1, Phase 2 of the migration).

- **What this is / how it works:** `system/SPEC-README.md` → `system/PHILOSOPHY.md` → `system/ARCHITECTURE.md`
- **How the operator behaves:** `system/CLAUDE.md` (copied to root `CLAUDE.md`)
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

## Commands

```bash
python tools/validate.py            # full offline validation (schemas + VALIDATION.md rules)
python tools/validate.py --online   # + external URL audit
python tools/generate.py            # rebuild everything under the gitignored output tree
python -m pytest                    # test suite
```

Requires Python 3.10+, `pyyaml`, `jsonschema>=4`, `pytest`.

A pre-commit hook (canonical copy `tools/hooks/pre-commit`, installed in
`.git/hooks/`) blocks any commit while the validator reports errors; warnings
print but never block. After a fresh clone/move, reinstall with
`cp tools/hooks/pre-commit .git/hooks/ && chmod +x .git/hooks/pre-commit`.

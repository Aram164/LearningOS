# Learning OS v3 — Repository

Plain-file knowledge repository for deep technical learning. Fresh Git repository, scaffolded 2026-07-16 (Stage 1, Phase 2 of the migration).

- **What this is / how it works:** `system/SPEC-README.md` → `system/PHILOSOPHY.md` → `system/ARCHITECTURE.md`
- **How the operator behaves:** `system/CLAUDE.md` (copied to root `CLAUDE.md`)
- **Migration state:** **COMPLETE — cutover 2026-07-17.** Pilot approved (5/5 frozen criteria, `migration/pilot-report.md`); Stage 2 full migration executed same day (`migration/final-report.md`). This repository is the operational root; the legacy `semestercontext/` tree is frozen history (banners point here).
- **Legacy:** the frozen pre-v3 tree is `semestercontext/` (tag `pre-v3-baseline`); this folder is designed to be moved beside it after cutover.
- **Roots:** materials → `../materials/` (`material://<source-id>/…` resolves there), code projects → `../projects/` — both outside the authored tree by design (materials move in Stage 2, Step 8).

## Commands

```bash
python tools/validate.py            # full offline validation (schemas + VALIDATION.md rules)
python tools/validate.py --online   # + external URL audit
python tools/generate.py            # rebuild everything under the gitignored output tree
python -m pytest                    # test suite
```

Requires Python 3.10+, `pyyaml`, `jsonschema>=4`, `pytest`.

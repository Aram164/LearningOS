# Learning OS v3 — Consolidated Specification (v3.1)

> **Status:** frozen implementation contract
> **Consolidated:** 2026-07-16
> **Supersedes:** `LearningOS_v3_Rebuild_Package.zip` (original spec) **and** `LearningOS_v3_Architecture_Revisions.md` (amendments). Both are historical from this date. There is exactly one authoritative specification: this package.

## Reading order

1. `PHILOSOPHY.md` — why the system exists. Read first. Every future ambiguity ("should this be a note?", "is this metadata useful or burden?") is resolved against its principle 10.1: *reduce organizational burden rather than create it.*
2. `WHY-REDESIGN.md`
3. `ARCHITECTURE.md`
4. `schema/*.schema.json` + `VALIDATION.md`
5. `CLAUDE.md`
6. `WORKFLOWS.md`
7. `MIGRATION.md`
8. `ACCEPTANCE-TESTS.md`
9. `BUILD-SPEC.md`

## What changed vs. the original package

- **Coordination layer** — `work/COORDINATION.md` owns commitments, explicit priorities, cross-workspace dependencies, and deferrals — and nothing else. The dashboard is a *generated* view (`generated/coordination-view.md`). Exam dates and workspace statuses are never restated in it.
- **Module records** — `records/modules.yaml` owns administrative facts: module identity, credits, examination attempts (including withdrawals and second sittings), Kombimodul components, grades. Dashboards over it are generated.
- **Note roles** — optional `role` field (default `synthesis`): exercise banks, mock exams, and crosswalks stay durable, retrievable notes instead of being archived.
- **Crosswalk ownership resolved** — contextual source judgments are canonical only in source records; crosswalk notes keep narrative; generated views reproduce the per-lecture/per-concept selector tables.
- **Machine-validatable schemas** — `schema/*.schema.json` replace the informal SCHEMA.yaml for structure; cross-file semantic rules live in `VALIDATION.md`.
- **Relations tightened** — `related-to` removed; eight relation types remain.
- **IDs** — numeric suffixes are collision-only (`note-cross-entropy`, `note-cross-entropy-02`).
- **Generated directory** — gitignored, fully rebuildable.
- **One validator** — `tools/validate.py` replaces `check_links.py`, `check_system.py`, and routine offline lychee runs; external URLs are checked only via an explicit `--online` mode.
- **Physical layout** — `LearningOS/{repository, materials, projects, legacy}`; active code repositories get an owned home.
- **Standing workspaces** — continuous efforts (degree planning, job) are legal, marked `standing: true`.
- **Migration** — two stages with a hard gate after the pilot; the pilot must include the AML–SaD Master Wiring; SESSION-LOG, module cards, and degree-planning files have explicit mappings; created-date policy defined.
- **Philosophy adopted as normative intent** — `PHILOSOPHY.md` (the user's own document) heads the reading order; the operating principle "reduce organizational burden rather than create it" is the tiebreaker for future decisions.
- **File-saving conventions** — concrete physical rules (ARCHITECTURE §3.3): note filename = `<note-id>.md`; handwritten originals under `knowledge/attachments/<note-id>/`; materials organized by source ID; `work/inbox/` as the zero-friction capture point that Claude routes.
- **Scope triage** — workspaces carry a `Deferred` section and triage labels (*required now / helpful now / defer / reference only*) so a deliberate "not now" is a recorded decision, not a thought to re-have.
- **Evidence, not mastery** — the system never claims understanding, but can show evidence for it: derive / explain / apply map onto `derivation` / `exercise` / `implementation` evidence entries.

## Scope

Learning OS v3 replaces the existing Masters-Planning architecture and the SoSe-2026 semester system. Operational information survives through `records/modules.yaml`, `work/COORDINATION.md`, active workspaces, and archived workspaces. No previous operational file remains a parallel canonical system.

## Contract

Claude must not invent new entity types, workflows, or schemas during the rebuild unless a documented migration blocker makes this specification impossible. Any such blocker must be reported before the architecture is changed.

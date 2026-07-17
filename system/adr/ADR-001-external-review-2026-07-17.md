# ADR-001 — Disposition of the external review (2026-07-17)

**Status:** accepted · **Context:** after Stage-2 cutover, Aram supplied a
12-point external critique of the v3 design. This ADR records what was adopted,
what was already covered by the frozen spec, and what was rejected with
reasons. The frozen architecture (entity families, ownership rules, invariants)
is unchanged; adopted items extend the *generated* layer and its documentation
only.

## Adopted

- **(4) Manifest as the complete machine-readable projection.** Contract now
  stated in `build_manifest`'s docstring; manifest extended to carry note
  attachments/evidence/contexts/supersedes, full module facts (attempts,
  examination, components), workspace links, and the COORDINATION sections.
  A consumer needing repository state reads `manifest.json`, not the tree.
- **(5) Generated Markdown = views.** Already architecturally true
  (ARCHITECTURE §2.5/§14, gitignored, never inputs); the generated-file header
  now says so explicitly ("a disposable VIEW over the canonical records").
- **(6) Dependency report.** New deterministic output
  `dependency-report.md`: direct + transitive prerequisites per concept
  (`requires` + `builds-on` closure), a layered study order (Kahn levels,
  cycle-guarded), and the module → workspace → concept graph. Directly serves
  the scope-explosion use case in PHILOSOPHY.
- **(8) Retrieval-based evaluation.** This is the system's own standard (the
  pilot gate WAS five frozen retrieval questions). Practice going forward:
  after any batch migration or large registry change, run fresh retrieval
  spot-checks against the regenerated views, not just the rule validator.
  Stage-2 spot-checks were run post-cutover (AMLS per-lecture selector;
  Taylor drill via concept selector) — both answer without legacy files.

## Already covered by the frozen spec (no change needed)

- **(1)** `knowledge/notes/algorithms/` exists since the 2026-07-16 scaffold
  (Aram's seven-bucket decision); empty until Algo-2 study produces notes.
- **(7)** Health report (`reports/health.md`, generator) and validation report
  (`reports/validation-report.md`, validator) are separate artifacts.
- **(9)** LFS already rejected by Aram; nothing uses it. Revisit only if the
  attachment policy (commit whole PDFs) makes the repo unwieldy.
- **(10)** Note-identity protection: ARCHITECTURE §5.5, invariant 18,
  CLAUDE.md §5 — split/merge/replace are explicit, approved events with a
  `supersedes` trail.
- **(11)** Tool-agnosticism: ARCHITECTURE §1 "Operator independence" +
  invariant 19; operator behavior lives only in CLAUDE.md.
- **(12)** The canonical / deterministically-generated / agent-computed triad:
  ARCHITECTURE §2 + §14; enforced by the validator (GEN-UNKNOWN, GEN-INPUT,
  GEN-TRACKED).

## Rejected (for this repository)

- **(2) In-place rebuild** and **(3) history preservation via migration
  branch.** Right defaults for a repository with substantial history; here the
  legacy Git history was six days old (initialized 2026-07-11) and survives
  intact in the frozen legacy tree (tag `pre-v3-baseline` + post-cutover
  commit). The fresh repository bought: clean reversibility, a hard acceptance
  gate, no 45k-file/8 GB trees in the knowledge repo's history, and no period
  where one tree serves two architectures. Provenance is preserved through
  `migration/path-map.csv`, `material-moves.csv`, and the archived legacy
  brain. The residual wart — `LearningOS/` physically inside
  `semestercontext/` — is resolved by moving the folder out (it is
  location-independent), not by merging histories.

# Point-3 prototype: replay + gains record

Side-by-side manifest contract compiler. No production behavior changed:
no stamped field, no enforced gate, no release artifact, no consumer path.
All evidence below is reproducible from the frozen baseline.

- Freeze: Core `96c9873553561b871dd43cb3293beaba51e829ec`,
  UI `fa07053926e0f757c726eff69b54721f238b17d1` (both trees clean).
- Replays ran 2026-09-20 on `prototype/contract-gen` in both repos.
- Toolchain: python 3.14.4, jsonschema 4.26.0, referencing 0.37.0,
  node v26.6.0, ajv 8.20.0, ajv-formats 3.0.1, json-schema-to-typescript 16.0.0
  (experiment only; not retained as a dependency).

## Phase 0 baseline

- UI contract layer: 1,890 lines (`manifest.ts` 943 + `manifest-records.ts` 947).
- M1 function validators: 8 + 71 = 79; M2 const validators: 2;
  M3 exported: 23; M4 `exact(` sites: 71.
- Mirrored-literal drift: schema title says "manifest v9" in the v11 file;
  22 UI error strings say "closed v8 projection" at v11.
- Historical v11 bump, contract-path-filtered: Core `d9e510f`
  (`manifest-contract.yaml` 8+/3−, new versioned `manifest-v11.schema.json`
  copy, 3 resource schemas +5/+1/±12); UI `bf9f7da` (lock + fixture +
  `manifest.ts`, 3 files, +32/−26). Whole-commit totals
  (35 files Core, 29 files UI) are feature work, reported as context only.
- Track-2 boundary inventory: manifest (this prototype) → `operations.ts`
  (193 lines, next candidate) → `gateway-v2.ts` (429 lines, structural
  portion only, later) → `tools/learning_os/diagnostics/` causal rules
  (behavioral, NEVER generated).
- Baseline `make system-check`: green before any prototype file existed.

## Phase 1 — bundle + closure digest (Core)

- Closure for v11: root + exactly 9 documents (7 reached directly, plus
  `learning-plan` via declared-$id alias `…/learning-plan-v1` and
  `material-comparison-defs` via `unit-material-synthesis`).
- Closure digest at freeze: `sha256:dbeb567651ca9d7c5b122c14953252d…`.
- `tests/test_contract_bundle.py` (8 tests): determinism, whitespace
  invariance, JSON-value sensitivity, exact 9-path inventory, alias
  fail-closed, registry parity (every admitted identity resolves identically
  through the live `schema_registry()`), root-hash-blindness control,
  meta shape. `tools/contract_bundle.py build`/`check` verified byte-stable.

## Phase 2 — Ajv validator + differential tests

- Generated `manifest.validator.cjs`: 805,166 bytes, 9 resources, CJS (Ajv's
  default; an ESM attempt emitted `require()` via the ajv-formats snippet and
  was abandoned — module format is irrelevant to the experiment).
- Strictness alignment: `strictSchema: false` for the single custom keyword
  `x-governs` (9×, annotation-only — Python's plain validator ignores it);
  all other strict checks stay on. Ajv logs 3 strictTypes notes (untyped
  `minItems`/`required` applicators); semantics unaffected.
- `tests/test_contract_differential.py` (5 tests): 2 seeds valid under both
  validators; 11 mutation classes agree (invalid under both); per-format
  subschema checks; full-scale 16 MB manifest valid under both
  (python 1.1s vs ajv subprocess 0.2s, informational only).
- FINDING (pinned, not hidden): Core's `FormatChecker()` ships without
  `date-time`/`uri` checkers, so the producer silently ignores those formats
  while Ajv enforces them. `date` agrees both directions. A production
  cutover must extend Core's checker set (a strictness change, out of scope);
  aligning Ajv down would hide the gap.

## Phase 3 — TypeScript generation: verdict FAIL (allowed)

json-schema-to-typescript@16.0.0 cannot consume this schema graph. Attempted:
single-file relative-ref staging, same with `$defs`→`definitions`
normalization, experimental `--imports` directory mode — all abort with
"Refs should have been resolved by the resolver!" on the
`unit-material-synthesis` root node (a 2020-12 root-level `$ref` with sibling
keywords plus cross-file back-edges); full `$RefParser.dereference` yields a
circular structure that is not even serializable. Reproduce without
installing anything:

    node scripts/stage-contract-types.mjs --bundle <bundle> --meta <meta> --out /tmp/st
    npx --package=json-schema-to-typescript json2ts -i /tmp/st/root.json

Consequence: handwritten UI types stay authoritative for wire shapes; the
generated Ajv validator stays authoritative for validation. No fallback
emitter was built (declared out of scope for this prototype).

## Phase 4 — metadata + regenerate-and-diff

- `manifest.meta.ts` (version + root hash + closure digest) and
  `manifest.prototype.lock.json` render purely from bundle metadata; a pytest
  asserts every overlapping scalar equals `contracts/manifest-v11.lock.json`.
- `npm run contract:diff-prototype`: exit 0 on match, exit 1 naming drifted
  files (verified both directions). Generated headers carry no invocation
  paths, so the gate passes from any checkout or temp dir.

## Phase 5 replays (scratch worktrees, since removed)

### 5A — v11 introduction → current main (the blind-spot proof)

- `contract_version` 11 → 11; root schema byte-identical; stamped
  `schema_sha256` identical; **closure `786a51f1…` → `dbeb5676…` (changed)**.
- Bundle diff: exactly two added optional properties —
  `learning-plan#/$defs/resource/.../node_scaffold_note` and
  `study-map#/$defs/legacyResource/.../node_scaffold_note`.
- Fragment analysis: both additions sit outside every fragment the manifest
  closure evaluates (the three referenced study-map fragments are ref-free
  leaves; `learning-plan` itself is reached only via an edge the manifest
  never evaluates). Validation semantics are unchanged — yet the digest
  flips. Conservative by design, demonstrated on a live case.
- Safety property this establishes: the closure digest can false-positive
  (flip on an unevaluated change) but never false-negative (miss an
  evaluated change — any evaluated change is also a document change). That
  is the fail-closed direction.

### 5B — v10 → v11 (clean single bump, `d9e510f^` → `d9e510f`)

- Version 10 → 11; stamped hash and closure both change, as they should.
- Root diff is exactly the documented v11 change: version const,
  freshness-reasons enum 7 → 6 (`unit_revision` dropped), `$id` bump.
- Resource diffs are `d9e510f` companions: documented (`scope_of_absence` +
  required 7 → 8) and undocumented-but-covered
  (`knowledge_node_id` × 2, policy const `tiered-v1` → `tiered-v2` — the v11
  history note under-describes its own commit; the bump still covers them).
- Generator path: zero structural hand-edits (bundle → emit → diff).

### 5C — v9 → v10 (clean single bump, `921ce70^` → `921ce70`)

- Version 9 → 10; stamped hash and closure both change.
- Root diff is exactly the documented v10 change: version const,
  `+requires_assets`, `+exposes_solutions_for`, `$id` bump. Nothing else.
- Resource diffs are the commit's companions (`independentEvidenceReview`
  machinery, matching the "Repair learner evidence" commit; likewise
  undocumented in the v10 history note, likewise covered by the bump).
- Generator path: zero structural hand-edits.

### Control — v10 lifetime stability (`921ce70` → `d9e510f^`)

- Version 10 → 10; stamped hash same; **closure identical**
  (`478fc3b5…` both ends). No false positives across v10's whole lifetime,
  and identical bytes from two independent checkouts (determinism).

## Gains table

| Metric | Before (hand-mirrored) | Prototype (generated) |
|---|---|---|
| Structural UI validators | 79 fn + 2 const + 71 `exact(` hand-written | Ajv standalone, 0 hand-written; differential suite proves Python≡Ajv |
| Mirrored version/hash/key literals | lock + constants + fixture, copied by hand | rendered from bundle meta; pytest asserts equality with production lock |
| Hash coverage | root file bytes only | 10-document closure (`sha256:dbeb5676…` at freeze) |
| Missed semantic drift (5A class) | invisible by construction | closure flips; 5A caught live drift |
| Bump hand-edits (contract paths) | Core yaml+schema+resources; UI 3 files +32/−26 | 0 structural (review generated diff only) |
| Wire types | handwritten interfaces | STILL handwritten (json2ts FAIL, Phase 3) |
| Validator implementations | Python + handwritten TS (two specs) | Python + Ajv over one spec + differential CI |

## Cutover considerations (for a future decision, not this prototype)

1. Extend Core's `FormatChecker` set (`date-time`, `uri`) before trusting
   Ajv verdicts at the boundary — else the consumer is stricter than the
   producer in a way no test would catch post-cutover.
2. Wire types need a different strategy: newer json2ts, another generator,
   or a conservative hand-rolled structural emitter. Do not hand-patch
   generated files.
3. `contract:generate` + `contract:diff-prototype` are manual today; a
   cutover wires regeneration into the release path and moves types into
   `src/` (the source-graph gate forbids unimported files there).
4. A fragment-precise digest is possible but was deliberately not built;
   whole-document errs toward over-flipping, which is the safe direction.
5. History notes under-describe companion schema changes twice (v10, v11);
   generated bundle diffs make that visible for free — consider attaching
   them to future bump reviews.

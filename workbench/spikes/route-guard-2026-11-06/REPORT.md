# SPIKE REPORT — route-guard unification (2026-11-06)

Labelled spike (Gate 2 authorization: "Spike 2 = optional narrow route-guard
unification only (references.py:118–138, 316–337, 441–456, routes.py:64–88), no
spec-registry apparatus; throwaway, no production edits, measured ledger").

## 1. What was built

`spike_references.py` — a full copy of production `references.py` (672 → 734
wc-l) whose ONLY change is the guard unification, verifiable by diff:
one shared comparison helper `route_guard_mismatches(route_ref, *, unit_id,
source_id, locator)` (sentinel semantics: a provided value is compared
**strictly**, exactly as the authored ifs — a record whose field is absent
reads as None and mismatches a real route value; an omitted attribute is not
compared — that is family policy, expressed by the caller), and the three
guard blocks (F2 synthesis trio, F6 selection trio, F8 resource pair) plus the
legacy-matcher call site rewritten onto it. Per-family message emission stays
in the family branches — byte-exact message parity requires it.

Scope correction discovered during the spike: `routes.py:64-88`
`exact_selection_matches` has a **second caller**
(`derive/projection/projection/records_curriculum.py:141`), so it is shared
machinery, not a dead 4th copy; the spike unifies the references.py call site
onto the helper's comparison (the matcher's `route_id` clause is dead at that
call site — the legacy branch runs only when the selection has no route_id)
and leaves the filter function itself in place for the projection caller.

## 2. Parity evidence

Baseline (production): **98 passed** over `tests/test_manifest_routes.py`,
`tests/test_validation.py`, `tests/test_route_identity_migration.py`, and
`tests/test_scenarios.py` — the last being the recorded-sequence oracle that
pins exact diagnostic codes, texts, paths and order, including guard codes.
With the spike swapped in (pytest `-p spike_guard_swap`, sys.modules swap
before `core.py` binds the mixin): **98 passed, zero failures**.

Targeted semantics checks (run, output recorded in the spike commit):
triple simultaneous drift emits in authored order `(unit, source, locator)`;
strict-None behavior preserved (missing-field records still fire the guard);
F8 family policy preserved (no locator comparison; falsy `sid` skips the
source guard). The simultaneous-drift emission order — the obligation the
post-review briefing added to arm (c) as `emission_rank` — is carried here by
the helper's fixed return order matching the authored if-order.

## 3. Measured ledger — and what it corrects

| Quantity | Value |
|---|---|
| Lines removed / added (diff vs production) | 65 removed, 127 added |
| Net | **+62 wc-l (672 → 734)** |
| Comparison implementations for the route-guard invariant | 4 (3 blocks + matcher call site) → **1 helper** |
| Parity | 98/98 including recorded sequences |

**Measured correction to Deliverable 2 §3/§8:** the pilot estimated the guard
collapse at ≈ −19 L net within `references.py` (−25 more in `routes.py`).
Measurement says the opposite sign: with byte-exact message parity, the loop
scaffolding and helper cost more than the bare `if` conditions they replace —
**the unification is a ≈ +62 L net increase, justified only by dimension 2**
(one implementation of the drift-prone invariant) **and nothing else**. Under
the brief's §9 rule (a line increase counts only against a named dimensions-2–4
win), this stands or falls on whether the reviewer values single-implementation
of this invariant at +62 L. It is an ordinary refactor decision, not a SQL one.

## 4. Reproduction

```
PYTHONPATH=tools .venv/bin/pytest tests/test_manifest_routes.py \
  tests/test_validation.py tests/test_route_identity_migration.py \
  tests/test_scenarios.py -q                                          # 98 passed
PYTHONPATH="tools:workbench/spikes/route-guard-2026-11-06" \
  .venv/bin/pytest -p spike_guard_swap <same files> -q                # 98 passed
diff tools/learning_os/derive/validation/references.py \
     workbench/spikes/route-guard-2026-11-06/spike_references.py      # 65< / 127>
```

Production files untouched; the swap lives only in the pytest process.

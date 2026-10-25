# Finding: `MANIFEST-CONTRACT-DRIFT` is documented but never emitted by any code

**Document claim:** `system/developer/changing-contracts.md:60` —
"When `MANIFEST-CONTRACT-DRIFT` fires:" — presented, like its sibling
`SCHEMA-CONTRACT-DRIFT` (line 17), as a named diagnostic the gate fires.

**Result: FALSE.** No code emits `MANIFEST-CONTRACT-DRIFT`. The only occurrence
outside documentation is a YAML comment (`system/contracts/manifest-contract.yaml:29`).

## Evidence

Exhaustive source search (excluding docs):

```
$ grep -rn "MANIFEST-CONTRACT-DRIFT" . --include="*.py" --include="*.yaml" \
    --include="*.yml" --include="*.json" --include="Makefile" --include="*.toml"
system/contracts/manifest-contract.yaml:29:# WHEN MANIFEST-CONTRACT-DRIFT FIRES
```

The actual gate lives in
`tools/learning_os/store/contracts/manifest_contract.py`. On drift it raises
`ManifestContractError` (class at line 45; message composed in `check()`,
lines 185-224) with a prose message that never contains the documented name:

```
the published manifest no longer matches system/contracts/manifest-contract.yaml
(declared v15).
  top_level_keys: added ['experimental_widgets'], missing none
  ...
```

The asymmetry is real: the schema gate genuinely emits its code
(`tools/learning_os/derive/validation/contract.py:70` —
`self.err("SCHEMA-CONTRACT-DRIFT", …)`), so the document's parallel construction
sets the expectation the manifest gate does not meet.

## Failing test on the pin

`tests/test_v1_manifest_drift_code.py` (registered in `tests/group_map.py`
"contracts" and `.github/shard-manifest.json`). It drives the real gate the way
`tests/test_manifest_contract.py` does — `build_manifest` on `mini_repo`, one
undeclared top-level key, then `check()` / `enforce()` — and asserts the
documented diagnostic:

```
$ .venv/bin/python -m pytest tests/test_v1_manifest_drift_code.py -q
…
FAILED tests/test_v1_manifest_drift_code.py::test_manifest_drift_message_carries_the_documented_code
FAILED tests/test_v1_manifest_drift_code.py::test_manifest_drift_exception_carries_the_documented_code
============================== 2 failed in 0.22s ===============================
```

Both failures show the actual refusal text; neither message contains
`MANIFEST-CONTRACT-DRIFT`.

## Assessment

- **Certainly wrong:** the document names a failure mode that does not exist in
  code. A developer grepping for `MANIFEST-CONTRACT-DRIFT` finds only the
  document, the contract comment, and no enforcement site — the opposite of
  what a named code is for.
- The gate itself works (the drift is refused, message actionable, bump
  instructions included); only the name in the document is unsupported.
- Severity: low. Doc-vs-code naming defect. Fixing it is out of scope (no fixes
  per campaign rules) — either the code should emit the code, or the document
  should quote the actual `ManifestContractError` phrasing.

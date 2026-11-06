# Contract-bundle check is environment-sensitive and blind to duplicate JSON keys (2026-11-06)

Task: agent-perspective hunt on branch `codex/review-shortcomings-20261105`. Workflow
step: development gates — contract bundle build/check.

Observation (verified, file:line): `tools/learning_os/store/contracts/bundle.py`
(`build_meta`, :119–166) embeds python/jsonschema/referencing versions, and
`tools/contract_bundle.py:97` byte-compares meta on `check` — so `check` fails across
environments or after a pip upgrade while the schema closure is unchanged. `check` is
also blind to *extra* stale files in the compare dir. `json.loads` normalizes duplicate
keys last-wins, so two schemas differing only in duplicate-key layout digest
identically.

Inference: the module self-describes as a prototype beside current behavior; the
failure modes are operational friction, not integrity holes.

Safety retained: fail-closed everywhere; `tests/test_contract_bundle.py` pins
whitespace-insensitivity and value-sensitivity of the digest.

Smallest improvement: compare the closure digest plus a semantic meta subset (schema
contract identity), surface an explicit warning on toolchain-version mismatch, reject
duplicate keys at load (`object_pairs_hook`), and fail on unexpected extra files in the
compare dir. Safeguards to retain: any mismatch still blocks; nothing becomes
auto-adopted.

Filing: GitHub issue not filed — `gh` CLI unavailable (blocked by tooling availability,
2026-11-06). Proposed issue title: "contract_bundle check fails on toolchain version
changes and ignores duplicate JSON keys".

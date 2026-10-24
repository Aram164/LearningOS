---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Process a lecture (WORKFLOWS §23)

Executable transcript of processing one lecture end to end: the as-taught
deck lands in the materials tree and its source is registered and attached
through workflow 6a's gateway; the scope pass reads the deck and separates
the new teaching from what an earlier unit already covers; the coverage
audit names the taught scope; the lecture unit and its scope-authority route
enter through one reviewed `module.plan.import` package, preflighted with
zero canonical writes; the learner's material choice is recorded through
`unit.source-selection.set`; and the tree validates, regenerates, and shows
its own write footprint. The deck and the plan are gated separately: this
transcript runs against a deck that exists in the materials tree — with no
as-taught deck, the operator stops and asks — and in production the import
applies only after Aram has seen the package and its check result
(OPERATOR.md boundary 18).
`tests/test_procedures.py` runs it with Scrut; `<REPO>` comes from the
`LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Materials in: the deck lands in the materials tree

Slides as taught land in the materials tree, never in the authored tree. In
production the deck is pulled in through workflow 6a's placement path and the
inventory is rebuilt with `make inventory`; the scenario fixture has no tools
tree, so this transcript places the same six-page deck and stages the same
manifest row the inventory writes.

```scrut
$ $LOS_REPO/.venv/bin/python - <<'PY'
> import hashlib
> import os
> import sys
> from pathlib import Path
>
> import yaml
>
> sys.path.insert(0, str(Path(os.environ["LOS_REPO"]) / "tests"))
> from repo_builders import write_minimal_pdf
>
> fx = Path(os.environ["LOS_FX"])
> deck = fx.parent / "materials/source-demo-lecture/lecture-03.pdf"
> write_minimal_pdf(deck, [
>     "Demo Lecture 3 - Linearity of expectation",
>     "Recall from Lecture 1: expectation weights every outcome value by its probability.",
>     "Linearity: E[X + Y] = E[X] + E[Y], with no independence required.",
>     "Worked example: the sum of two fair dice, by linearity.",
>     "Linearity turns double counting into a sum of simple expectations.",
>     "Exam note: state linearity before expanding any sum.",
> ])
> manifest_path = fx / "records/materials-manifest.yaml"
> manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
> manifest.setdefault("files", {})["source-demo-lecture/lecture-03.pdf"] = {
>     "size": deck.stat().st_size,
>     "sha256": hashlib.sha256(deck.read_bytes()).hexdigest(),
> }
> manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
> print("deck: " + str(deck.relative_to(fx.parent)))
> print("sha256: " + hashlib.sha256(deck.read_bytes()).hexdigest())
> PY
deck: materials/source-demo-lecture/lecture-03.pdf
sha256: bd0dbb3ba778d397c2afbe6cfb46e6c6697fd884fda3797cb565abffb1f2b30f
```

## The scope pass: new teaching versus re-coverage

The deck's subject is new to the repository, and its recall page is not.

```scrut
$ los search "linearity"
[]
```

```scrut
$ los search "expected value" | $LOS_REPO/.venv/bin/python -c 'import json,sys; print([r["id"] for r in json.load(sys.stdin)])'
['note-demo', 'note-demo-analysis', 'concept-expected-value', 'source-demo-book', 'workspace-demo', 'workspace-second', 'unit-demo-l01', 'unit-demo-l02', 'study-map-demo-l01', 'source-map-demo']
```

The recall is re-covered: `unit-demo-l01` already teaches it, so the new
unit's knowledge map carries the recall as a node that the new teaching
builds on, not as a second study path.

Read the deck itself; scope never comes from titles or keyword matches.

```scrut
$ $LOS_REPO/.venv/bin/python -c 'from pypdf import PdfReader; import os; r = PdfReader(os.path.join(os.environ["LOS_FX"], "..", "materials", "source-demo-lecture", "lecture-03.pdf")); [print(f"p.{i}: {p.extract_text().strip()}") for i, p in enumerate(r.pages, 1)]'
p.1: Demo Lecture 3 - Linearity of expectation
p.2: Recall from Lecture 1: expectation weights every outcome value by its probability.
p.3: Linearity: E[X + Y] = E[X] + E[Y], with no independence required.
p.4: Worked example: the sum of two fair dice, by linearity.
p.5: Linearity turns double counting into a sum of simple expectations.
p.6: Exam note: state linearity before expanding any sum.
```

## Register the deck's source (workflow 6a)

<!-- los:reference {"kind": "command", "text": "los source-intake"} -->
<!-- los:reference {"kind": "command", "text": "los source-revise --check"} -->
The deck's source is registered metadata-only with discovery provenance,
then its bytes attach with the live hash. Both writes go through the
gateway: check, bind the diff, seal with derived guards, submit once.

```scrut
$ los source-intake --record '{"records": [{"action": "create", "id": "source-demo-lecture", "partition": "sources.yaml", "title": "Demo Lecture 3 deck", "type": "lecture", "discovery": {"observed": "2026-10-01", "basis": [{"kind": "list-entry", "ref": "course/probe.md#L3"}], "possible_use": "Probe lecture deck."}}]}' --check
{"ok":true,"check":true,"records":1,"diff":[{"id":"source-demo-lecture","action":"create","partition":"sources.yaml","fields":{"title":{"before":null,"after":"Demo Lecture 3 deck"},"type":{"before":null,"after":"lecture"},"discovery":{"before":null,"after":{"observed":"2026-10-01","basis":[{"kind":"list-entry","ref":"course/probe.md#L3"}],"possible_use":"Probe lecture deck."}}}}],"diff_sha256":"sha256:7826dfd53e21cc52d89f3d082a2b9f1f44e41815e0e770efd2da5e5e47ca6c96","expected_revisions":{"source-demo-lecture":0},"artifact_ids":["source-demo-lecture"]}
```

```scrut
$ eval "$(los source-intake --record '{"records": [{"action": "create", "id": "source-demo-lecture", "partition": "sources.yaml", "title": "Demo Lecture 3 deck", "type": "lecture", "discovery": {"observed": "2026-10-01", "basis": [{"kind": "list-entry", "ref": "course/probe.md#L3"}], "possible_use": "Probe lecture deck."}}]}' --check | $H/los-bind INTAKE_DIFF '$.diff_sha256')" && echo "$INTAKE_DIFF"
sha256:7826dfd53e21cc52d89f3d082a2b9f1f44e41815e0e770efd2da5e5e47ca6c96
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.intake.record --payload "{\"record\": {\"records\": [{\"action\": \"create\", \"id\": \"source-demo-lecture\", \"partition\": \"sources.yaml\", \"title\": \"Demo Lecture 3 deck\", \"type\": \"lecture\", \"discovery\": {\"observed\": \"2026-10-01\", \"basis\": [{\"kind\": \"list-entry\", \"ref\": \"course/probe.md#L3\"}], \"possible_use\": \"Probe lecture deck.\"}}]}, \"expected_diff_sha256\": \"$INTAKE_DIFF\"}" --key s23-intake --request-id request-s23-intake --guards auto --out "$TMPDIR/s23-intake.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: source-demo-lecture=0
```

```scrut {interpolated: true}
$ los capability source.intake.record --payload-file "$TMPDIR/s23-intake.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{
  "schema_version": 2,
  "request_id": "request-s23-intake",
  "idempotency_key": "s23-intake",
  "capability": "source.intake.record",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-001",
  "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
  "snapshot_after": "$LOS_FIXTURE_SNAPSHOT_3",
  "result": {
    "ok": true,
    "transaction_id": "transaction-20261001-090000-001",
    "receipt_path": "operations/transactions/transaction-20261001-090000-001.yaml",
    "artifact_revisions": {
      "source-demo-lecture": 1
    },
    "snapshot_after": "$LOS_FIXTURE_SNAPSHOT_3",
    "replayed": false
  },
  "error": null
}
```

```scrut
$ $H/los-assert-receipt --last --capability source.intake.record
```

## Attach the deck bytes with the live hash

```scrut
$ MAT_SHA=$(sha256sum "$(dirname "$LOS_FX")/materials/source-demo-lecture/lecture-03.pdf" | cut -d' ' -f1) && echo "$MAT_SHA"
bd0dbb3ba778d397c2afbe6cfb46e6c6697fd884fda3797cb565abffb1f2b30f
```

```scrut
$ cat > "$TMPDIR/attach-record.yaml" <<EOF
> id: source-demo-lecture
> material: material://source-demo-lecture/lecture-03.pdf
> material_sha256: $MAT_SHA
> EOF
```

```scrut
$ eval "$(los source-revise --file "$TMPDIR/attach-record.yaml" --check | $H/los-bind ATTACH_DIFF '$.diff_sha256')" && echo "$ATTACH_DIFF"
sha256:38ab6dbd717878b6a05dba32f41a55c7b360e69dfc48dcb0dc0602d0ef203581
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.record.revise --payload "{\"record\": {\"id\": \"source-demo-lecture\", \"material\": \"material://source-demo-lecture/lecture-03.pdf\", \"material_sha256\": \"$MAT_SHA\"}, \"expected_diff_sha256\": \"$ATTACH_DIFF\"}" --key s23-attach --request-id request-s23-attach --guards auto --out "$TMPDIR/s23-attach.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: source-demo-lecture=1
```

```scrut {interpolated: true}
$ los capability source.record.revise --payload-file "$TMPDIR/s23-attach.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{
  "schema_version": 2,
  "request_id": "request-s23-attach",
  "idempotency_key": "s23-attach",
  "capability": "source.record.revise",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-002",
  "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
  "snapshot_after": "$LOS_FIXTURE_SNAPSHOT_4",
  "result": {
    "ok": true,
    "transaction_id": "transaction-20261001-090000-002",
    "receipt_path": "operations/transactions/transaction-20261001-090000-002.yaml",
    "artifact_revisions": {
      "source-demo-lecture": 2
    },
    "snapshot_after": "$LOS_FIXTURE_SNAPSHOT_4",
    "replayed": false
  },
  "error": null
}
```

```scrut
$ $H/los-assert-receipt --last --capability source.record.revise
```

## The coverage audit names the taught scope

The source-completeness gate's output is the audit itself: every local file
rowed, the recall's re-coverage named, the taught scope pinned to exact
pages.

```scrut
$ cat > work/active/workspace-demo/outputs/lecture-03-coverage-audit.md <<'EOF'
> # Lecture 03 coverage audit — 2026-10-01
>
> Plan package: `work/active/workspace-demo/outputs/lecture-03-package.yaml`
>
> Scope authority: Demo Lecture 3 deck, as taught.
>
> Review boundary: the module-demo materials root and the module's own
> bibliography; no preserved prior-year plan exists for this module.
>
> ## Local inventory
>
> | Locator | Version/year | Format | Opened/inspected evidence | Actual contents | Disposition | Unit route | Lecture-specific angle |
> |---|---|---|---|---|---|---|---|
> | `material://source-demo-lecture/lecture-03.pdf` | current | course-material | locator `lecture-03.pdf, PDF pp. 1-6` read | linearity recall, statement, dice example, exam note | current | `route-demo-l03-deck` | scope authority and lecturer notation |
> | `material://source-demo-book/lecture-01.pdf` | current | book | already routed | expected-value derivation | complementary | `route-b2f1f80014860a929a3af0bc` | prior lecture, recalled on deck p. 2 |
>
> ## Linked inventory
>
> None: the deck names no external reading.
>
> ## Current/prior and duplicate reconciliation
>
> No prior-year deck exists; nothing to reconcile.
>
> ## Explicit exclusions and unresolved gaps
>
> None: every file in the declared root has a row.
>
> ## Unit knowledge and material matrix
>
> | Unit | Knowledge nodes | Authoritative scope | Course material | Books | Coverage gap |
> |---|---|---|---|---|---|
> | `unit-demo-l03` | `knowledge-demo-l03-recall` then `knowledge-demo-l03-linearity` | deck pp. 1-6 | `route-demo-l03-deck` | existing book routes re-cover the recall only | none |
>
> ## Completeness sign-off
>
> - [x] Every file under the declared local root has an inventory row.
> - [x] Materials were opened; no scope decision came from filenames.
> - [x] Every ordinary lecture has an individual row.
> - [x] Learner choices stay separate from the complete menu.
> EOF
```

## Package and preflight the lecture unit

<!-- los:reference {"kind": "command", "text": "los module-plan-import module-demo --file lecture-03-package.yaml --check"} -->
The package drafts outside the repository, from the canonical template: the
new lecture unit with its knowledge map, the scope-authority route with its
exact locator and quoted evidence, the final workspace joins, and the
complete final source map — the existing book routes reproduced exactly. The
claim evidence quotes the deck's own pages, so the covers claim is anchored
to verified bytes.

```scrut
$ cat > "$TMPDIR/lecture-03-package.yaml" <<'EOF'
> module_id: module-demo
> plan_contract:
>   version: 2
>   plan_template_version: 1
>   coverage_audit: work/active/workspace-demo/outputs/lecture-03-coverage-audit.md
>   intentional_reorders: []
>   checks:
>     local_inventory_complete: true
>     linked_inventory_complete: true
>     materials_opened_and_content_checked: true
>     current_and_prior_scope_reconciled: true
>     duplicates_and_numbering_checked: true
>     exclusions_and_unresolved_gaps_recorded: true
> module_patch:
>   unit_order:
>     - unit-demo-l01
>     - unit-demo-l02
>     - unit-demo-l03
> source_map:
>   type: module-source-map
>   module_id: module-demo
>   sources:
>     - source_id: source-demo-book
>       role: spine
>       why: Scoped demo reading.
>       priority: 0
>       unit_routes:
>         - unit_id: unit-demo-l01
>           id: route-b2f1f80014860a929a3af0bc
>           title: Demo book — expected-value derivation
>           format: book
>           angle: Derives the weighted sum and works a discrete example.
>           covers:
>             - knowledge-demo-outcomes
>             - knowledge-demo-expectation
>           depth: derivation
>           scope: current
>           locator: lecture-01.pdf
>         - unit_id: unit-demo-l02
>           title: Demo book — variance derivation
>           format: book
>           angle: Derives variance and works a discrete example.
>           covers:
>             - knowledge-demo-variance
>           depth: derivation
>           scope: current
>           locator: lecture-02.pdf
>     - source_id: source-demo-lecture
>       role: course-material
>       why: Current taught material is the scope authority.
>       priority: 1
>       unit_routes:
>         - unit_id: unit-demo-l03
>           id: route-demo-l03-deck
>           title: Demo Lecture 3 deck — the scope authority
>           format: course-material
>           angle: Defines the taught scope in the lecturer's notation and works the linearity example.
>           angle_detail: 'Read pp. 2-4 as the chapter. The recall on p. 2 only restates Lecture 1;
>             the statement on p. 3 is the exam-form result; the dice example on p. 4 is the one
>             worked derivation. The exam note on p. 6 says the lecturer expects the result stated
>             before any expansion.'
>           covers:
>             - knowledge-demo-l03-linearity
>           depth: course-aligned
>           scope: current
>           locator: lecture-03.pdf, PDF pp. 1-6
>           vault_path: material://source-demo-lecture/lecture-03.pdf
> units:
>   - unit:
>       id: unit-demo-l03
>       type: unit
>       module_id: module-demo
>       kind: lecture
>       title: Linearity of expectation
>       order: 3
>       scope: "The third lecture as taught: linearity of expectation without independence."
>       status: active
>       scope_sources:
>         - source_id: source-demo-lecture
>           authority: slides
>           locator: lecture-03.pdf, PDF pp. 1-6
>       source_selections: []
>       artifacts: {}
>       workspace_ids:
>         - workspace-demo
>       knowledge_map:
>         summary: The lecture recalls the weighted-sum definition and derives linearity with a worked example.
>         nodes:
>           - id: knowledge-demo-l03-recall
>             title: The weighted-sum recall
>             summary: Lecture 1's expectation definition, restated in the lecturer's notation.
>           - id: knowledge-demo-l03-linearity
>             title: Linearity without independence
>             summary: Expectation of a sum is the sum of expectations, independence not required.
>             builds_on:
>               - knowledge-demo-l03-recall
>             concept_ids:
>               - concept-expected-value
> workspace_updates:
>   - id: workspace-demo
>     sources:
>       - source-demo-book
>       - source-demo-lecture
>     unit_ids:
>       - unit-demo-l01
>       - unit-demo-l02
>       - unit-demo-l03
>     sections:
>       Current Scope: unit-demo-l03 — linearity of expectation, deck as taught.
>       Next Action: Choose material for unit-demo-l03 from the complete menu.
> claim_evidence:
>   - claim_id: covers:route-demo-l03-deck
>     evidence:
>       - kind: route-locator
>         ref: lecture-03.pdf, PDF pp. 1-6
>       - kind: manifest
>         ref: source-demo-lecture/lecture-03.pdf
>       - kind: quote
>         ref: material://source-demo-lecture/lecture-03.pdf
>         page: 3
>         text: "Linearity: E[X + Y] = E[X] + E[Y], with no independence required."
>       - kind: quote
>         ref: material://source-demo-lecture/lecture-03.pdf
>         page: 6
>         text: "Exam note: state linearity before expanding any sum."
>         note: the deck's own exam framing closes the taught scope
> EOF
```

The preflight runs the contract, routing and shadow-repository validation and
writes nothing.

```scrut
$ los module-plan-import module-demo --file "$TMPDIR/lecture-03-package.yaml" --check | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"], d["mode"], d["canonical_files_written"]); print(d["package_sha256"]); print(d["routes_added"]); print(json.dumps(d["expected_revisions"], sort_keys=True))'
True check 0
sha256:96249d311994f07dd1d8e5fcf1cea19877634b99c1584e22f127c719a231f360
['route-demo-l03-deck']
{"file:operations/transactions/lineage.yaml": 0, "module-demo": 0, "unit-demo-l03": 0}
```

## Apply the package through the gateway

```scrut {output_stream: stderr}
$ PKG_SHA=$(sha256sum "$TMPDIR/lecture-03-package.yaml" | cut -d' ' -f1) && $H/los-seal --capability module.plan.import --payload "{\"module_id\": \"module-demo\", \"file\": \"$TMPDIR/lecture-03-package.yaml\", \"file_sha256\": \"sha256:$PKG_SHA\"}" --key s23-import --request-id request-s23-import --guards auto --out "$TMPDIR/s23-import.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: file:operations/transactions/lineage.yaml=0, module-demo=0, unit-demo-l03=0
```

```scrut {interpolated: true}
$ los capability module.plan.import --payload-file "$TMPDIR/s23-import.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{
  "schema_version": 2,
  "request_id": "request-s23-import",
  "idempotency_key": "s23-import",
  "capability": "module.plan.import",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-003",
  "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
  "snapshot_after": "$LOS_FIXTURE_SNAPSHOT_6",
  "result": {
    "ok": true,
    "mode": "apply",
    "module_id": "module-demo",
    "units_written": [
      "unit-demo-l03"
    ],
    "files_written": 5,
    "transaction_id": "transaction-20261001-090000-003",
    "receipt_path": "operations/transactions/transaction-20261001-090000-003.yaml",
    "artifact_revisions": {
      "file:operations/transactions/lineage.yaml": 1,
      "module-demo": 1,
      "unit-demo-l03": 1
    },
    "snapshot_after": "$LOS_FIXTURE_SNAPSHOT_6",
    "replayed": false
  },
  "error": null
}
```

```scrut
$ $H/los-assert-receipt --last --capability module.plan.import
```

## Record the learner's material choice

<!-- los:reference {"kind": "command", "text": "los unit-source-selection"} -->
The complete menu is the source map; the learner's choice is one recorded
selection on the new route, never a silent preselection.

```scrut {output_stream: stderr}
$ $H/los-seal --capability unit.source-selection.set --payload '{"unit_id": "unit-demo-l03", "action": "select", "source_id": "source-demo-lecture", "locator": "lecture-03.pdf, PDF pp. 1-6", "purpose": "Current lecture pass"}' --key s23-select --request-id request-s23-select --guards auto --out "$TMPDIR/s23-select.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: unit-demo-l03=1
```

```scrut {interpolated: true}
$ los capability unit.source-selection.set --payload-file "$TMPDIR/s23-select.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{
  "schema_version": 2,
  "request_id": "request-s23-select",
  "idempotency_key": "s23-select",
  "capability": "unit.source-selection.set",
  "ok": true,
  "replayed": false,
  "transaction_id": "transaction-20261001-090000-004",
  "receipt_path": "operations/transactions/transaction-20261001-090000-004.yaml",
  "snapshot_after": "$LOS_FIXTURE_SNAPSHOT_7",
  "result": {
    "ok": true,
    "unit_id": "unit-demo-l03",
    "source_id": "source-demo-lecture",
    "locator": "lecture-03.pdf, PDF pp. 1-6",
    "selected": true,
    "transaction_id": "transaction-20261001-090000-004",
    "receipt_path": "operations/transactions/transaction-20261001-090000-004.yaml",
    "artifact_revisions": {
      "unit-demo-l03": 2
    },
    "snapshot_after": "$LOS_FIXTURE_SNAPSHOT_7",
    "replayed": false
  },
  "error": null
}
```

```scrut
$ $H/los-assert-receipt --last --capability unit.source-selection.set
```

```scrut
$ grep -n -A4 "source_selections" curriculum/modules/module-demo/units/unit-demo-l03/unit.yaml
13:source_selections:
14-- route_id: route-demo-l03-deck
15-  source_id: source-demo-lecture
16-  locator: lecture-03.pdf, PDF pp. 1-6
17-  purpose: Current lecture pass
```

## Validate, regenerate, and read the footprint

An ordered study map is owed next (OPERATOR boundary 6) and is created only
when a path is chosen (WORKFLOWS §25a); processing the lecture ends with a
clean tree and a readable record of everything it touched.

```scrut
$ (set -o pipefail; los validate | tail -n 1)
0 error(s), 13 warning(s) — OK
```

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

```scrut
$ grep -n "unit-demo-l03" generated/reading-room.md | head -n 3
17:- `workspace-demo` (active) — next: Choose material for unit-demo-l03 from the complete menu.
```

```scrut
$ git status --short
 M curriculum/modules/module-demo/module.yaml
 M curriculum/modules/module-demo/source-map.yaml
 M operations/transactions/lineage.yaml
 M operations/transactions/revisions.yaml
 M records/materials-manifest.yaml
 M sources/sources.yaml
 M work/active/workspace-demo/CONTEXT.md
?? curriculum/modules/module-demo/units/unit-demo-l03/
?? operations/diagnostics/
?? operations/transactions/idempotency.yaml
?? operations/transactions/transaction-20261001-090000-001.yaml
?? operations/transactions/transaction-20261001-090000-002.yaml
?? operations/transactions/transaction-20261001-090000-003.yaml
?? operations/transactions/transaction-20261001-090000-004.yaml
?? work/active/workspace-demo/outputs/lecture-03-coverage-audit.md
```

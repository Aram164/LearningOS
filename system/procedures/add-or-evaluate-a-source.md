---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Add or evaluate a source (WORKFLOWS §6)

Executable transcript of taking one paper from find to curated list:
search the registry by title, author, identifier and URL; register it
metadata-only through the intake gateway with discovery provenance;
refuse an intake that smuggles in an evaluation; place its bytes and
attach them with the live hash after the inventory; record the
evaluation; create its curated collection through the reviewed-file,
snapshot-guarded `collection.create` capability; revise one entry `why`;
and rebuild.
`tests/test_procedures.py` runs it with Scrut; `<REPO>` comes from the
`LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Search the registry by title: the paper is new

1. search the registry by title, author, identifier, and URL;
2. reuse the existing record when found;
3. add identity metadata and `material://` or URL location;
4. record evaluation globally or per concept: strengths, weaknesses, level, audience, prerequisites, useful sections;
5. avoid universal quality scores;
6. rebuild the source index.

```scrut
$ los search "Bare Essay"
[]
```

```scrut {output_stream: stderr}
$ los search "Bare Essay"
los: no record matches all 2 terms; per-term record hits: bare=0 essay=0
```

## Search by author, identifier and URL before registering

```scrut
$ los search "A. Author" | $LOS_REPO/.venv/bin/python -c 'import json,sys; print([r["id"] for r in json.load(sys.stdin)])'
['source-demo-book']
```

```scrut
$ los inspect source-demo-book | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["id"], d["title"], d["material"])'
source-demo-book Demo Book material://source-demo-book/book.pdf
```

```scrut
$ los search "https://example.com/bare-essay"
[]
```

The paper shares no title, author, identifier or URL with the
registered Demo Book, so a new record is registered instead of reusing
one.

## Review the metadata-only intake

<!-- los:reference {"kind": "command", "text": "los source-intake"} -->
<!-- los:reference {"kind": "command", "text": "los source-revise --check"} -->
<!-- los:reference {"kind": "command", "text": "los collection-entry-revise --check"} -->
1. **Register** the source (steps 1–5 above) through its gateway, never by
   editing the registry file directly. One record per teaching object; the
   one-line "why it earns its place" goes into the evaluation, never into a
   note or plan file. A find shelved from a list or page before anything is
   examined registers metadata-only through `source.intake.record`
   (`los source-intake`), which requires `discovery` provenance and refuses
   evaluations; an examination that overturns the shelf corrects the record
   through the same capability.
2. **Place the material:**
   - web-native (ALL videos, courses, blogs, interactive): `url` on the record
     — videos are never downloaded;
   - free downloadable file that is exam- or thesis-critical: pull into the
     materials topic tree via the PLACEMENT map + `tools/build_materials_tree.py`,
     record `material://<source-id>/…`;
   - campus-license or paid: leave URL-only until Aram pulls/decides.
   - already registered but URL-only: once verified local bytes exist, attach
     them with `source.record.revise` (`los source-revise --check`, then the
     reviewed apply) — exact `material://` URI plus the live byte hash, after
     `make inventory`. The same call may replace a stale evaluation with its
     explicit final form. It never changes identity or intake-owned fields,
     never replaces a held different material, and never rewrites a curated
     collection's `why` (workflow 6b stays a separate edit). When the attach
     moves an approved dossier's material basis, the check names the affected
     units and the apply must carry their reviewed replacement dossiers —
     or, when every moved route is screened, evidence-free, analysis-free
     and outside every comparison, a reviewed `dossier_rebases` shortcut
     naming exactly the moved routes. Both the shortcut and a full
     replacement stamp the new basis with their own fresh
     request_id/delivery_id — reusing the live dossier's provenance
     unchanged is refused, since it would attest the old material.
     Both paths also record prospective freshness lineage in the same
     transaction, bound to the new dossier bytes and validated staged basis.
     Anything else (deep-reviewed routes, evidence, comparisons, an
     already-stale dossier) keeps the full replacement. The check also lists referring collection entries; when a
     listed `why` is now false, correct it afterwards with
     `collection.entry.revise` (`los collection-entry-revise --check`, then
     the reviewed apply), which revises one entry's one-line `why` and
     preserves source, group, order and all other entries.
3. **List it (optional):** if it belongs in a curated per-domain list, add an
   entry to the matching `sources/collections/<name>.yaml` (workflow 6b).
4. **Verify:** `.venv/bin/python tools/validate.py --compact` then `.venv/bin/python tools/generate.py`.

```scrut
$ los source-intake --record '{"records": [{"action": "create", "id": "source-scenario-bare", "partition": "sources.yaml", "title": "Bare Essay", "type": "paper", "discovery": {"observed": "2026-10-01", "basis": [{"kind": "list-entry", "ref": "shelf/probe.md#L3"}], "possible_use": "Probe shelf."}}]}' --check
{"ok":true,"check":true,"records":1,"diff":[{"id":"source-scenario-bare","action":"create","partition":"sources.yaml","fields":{"title":{"before":null,"after":"Bare Essay"},"type":{"before":null,"after":"paper"},"discovery":{"before":null,"after":{"observed":"2026-10-01","basis":[{"kind":"list-entry","ref":"shelf/probe.md#L3"}],"possible_use":"Probe shelf."}}}}],"diff_sha256":"sha256:a610c3e12a216350d6d776c556f03726e00a9cfc8fbe254039d12a6f6c77e0bd","expected_revisions":{"source-scenario-bare":0},"artifact_ids":["source-scenario-bare"]}
```

## Bind the intake diff

```scrut
$ eval "$(los source-intake --record '{"records": [{"action": "create", "id": "source-scenario-bare", "partition": "sources.yaml", "title": "Bare Essay", "type": "paper", "discovery": {"observed": "2026-10-01", "basis": [{"kind": "list-entry", "ref": "shelf/probe.md#L3"}], "possible_use": "Probe shelf."}}]}' --check | $H/los-bind INTAKE_DIFF '$.diff_sha256')" && echo "$INTAKE_DIFF"
sha256:a610c3e12a216350d6d776c556f03726e00a9cfc8fbe254039d12a6f6c77e0bd
```

## Seal the intake with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.intake.record --payload "{\"record\": {\"records\": [{\"action\": \"create\", \"id\": \"source-scenario-bare\", \"partition\": \"sources.yaml\", \"title\": \"Bare Essay\", \"type\": \"paper\", \"discovery\": {\"observed\": \"2026-10-01\", \"basis\": [{\"kind\": \"list-entry\", \"ref\": \"shelf/probe.md#L3\"}], \"possible_use\": \"Probe shelf.\"}}]}, \"expected_diff_sha256\": \"$INTAKE_DIFF\"}" --key s06-intake --request-id request-s06-intake --guards auto --out "$TMPDIR/s06-intake.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: source-scenario-bare=0
```

## Submit the intake

```scrut {interpolated: true}
$ los capability source.intake.record --payload-file "$TMPDIR/s06-intake.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{"schema_version":2,"request_id":"request-s06-intake","idempotency_key":"s06-intake","capability":"source.intake.record","ok":true,"replayed":false,"transaction_id":"transaction-20261001-090000-001","receipt_path":"operations/transactions/transaction-20261001-090000-001.yaml","snapshot_after":"$LOS_FIXTURE_SNAPSHOT_2","result":{"ok":true,"transaction_id":"transaction-20261001-090000-001","receipt_path":"operations/transactions/transaction-20261001-090000-001.yaml","artifact_revisions":{"source-scenario-bare":1},"snapshot_after":"$LOS_FIXTURE_SNAPSHOT_2","replayed":false},"error":null}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability source.intake.record
```

## An intake carrying an evaluation is refused

```scrut {output_stream: stderr}
$ los source-intake --record '{"records": [{"action": "create", "id": "source-scenario-eval", "partition": "sources.yaml", "title": "Eval Essay", "type": "paper", "evaluations": [{"level": "introductory"}], "discovery": {"observed": "2026-10-01", "basis": [], "possible_use": "x"}}]}' --check
los: INVALID_REQUEST: source-scenario-eval: field 'evaluations' is outside the intake allowlist (evaluations, topics, material, routes, selections, notes, feedback and observations are never written through intake)
[2]
```

## Observe the placed bytes and the fixture inventory

The essay PDF was pulled into the materials topic tree; the fixture
supplies it at `source-scenario-bare/attached.pdf` with its generated
manifest. The inventory entrypoint anchors to its own file location,
so the sections below run a byte-identical copy against copied
fixture materials in a disposable pair.

```scrut
$ MAT_SHA=$(sha256sum "$(dirname "$LOS_FX")/materials/source-scenario-bare/attached.pdf" | cut -d' ' -f1) && echo "$MAT_SHA"
61b4d4e33f928a4f6801ae74b3e940e0cfac1285aa4a958d46ce0ae142b49ed6
```

```scrut
$ $H/los-assert-file records/materials-manifest.yaml --exists
```

## The materials plan wants no moves

```scrut
$ $LOS_REPO/.venv/bin/python $LOS_REPO/tools/build_materials_tree.py --materials-root "$(dirname "$LOS_FX")/materials" | grep -E "moves \(|to \(re\)write"
  moves (0)
  SOURCES.md files to (re)write: 0
```

## Copy the inventory entrypoint into a disposable pair

`tools/materials_manifest.py --build` anchors the materials tree and
the manifest to its own file location, so a byte-identical copy binds
to wherever it is placed. The helper copies only the entrypoint, its
one leaf dependency, and the two repo files they read, and refuses
any destination outside the transcript `TMPDIR`.

```scrut
$ mkdir -p "$TMPDIR/inv-pair/repo" && export INV_PAIR="$(realpath "$TMPDIR/inv-pair")" INV_REPO="$(realpath "$TMPDIR/inv-pair/repo")" && $H/los-anchored-copy materials_manifest "$INV_REPO"
sha256:a0583ab05765120a52f688d88ed6cd03e56c1567d7183328d0c640424297b575 Makefile
sha256:6b5296af66bf7bfb1a03b3dbb6c8ee6778fa4e7ba121fac957d73d8502f14161 pyproject.toml
sha256:0c84a5cae52dc8aa786e0009eaaa38e9e2f202b5f140e8cb07d1b188bc338ba8 tools/learning_os/__init__.py
sha256:9f4511b38e35ff56efa15bc8b486a589d9dc42eed38ab331da85c7e7f6503c41 tools/learning_os/domain/material_inventory.py
sha256:8bdcc529afb1448f8856ba13e615b894989c70786024d702e839f62b52e96e3b tools/materials_manifest.py
```

## Stage the copied sibling materials

```scrut
$ mkdir -p "$INV_REPO/records" && cp -R "$(dirname "$LOS_FX")/materials" "$INV_PAIR/materials" && export LIVE_SHA=$(sha256sum "$LOS_REPO/records/materials-manifest.yaml" | cut -d' ' -f1) && find "$INV_PAIR/materials" -type f | sed "s|$INV_PAIR|<PAIR>|" | sort
<PAIR>/materials/source-demo-book/book.pdf
<PAIR>/materials/source-demo-book/lecture-01.pdf
<PAIR>/materials/source-scenario-bare/attached.pdf
```

## Rebuild the inventory from the copied materials

```scrut
$ (cd "$INV_REPO" && make --silent inventory PY="$LOS_REPO/.venv/bin/python")
wrote records/materials-manifest.yaml: 3 files, 0.00 GB
```

## Verify the copied tree against the rebuilt manifest

The date and the pair path are redacted; both vary per run.

```scrut
$ (cd "$INV_REPO" && make --silent verify-materials PY="$LOS_REPO/.venv/bin/python") | sed -e "s|$INV_PAIR|<PAIR>|g" -e "s/captured [0-9-]*/captured <today>/"
manifest captured <today> — 3 files
OK — <PAIR>/materials matches the manifest (sha256 verified)
```

## The isolated rebuild matches the fixture manifest

Only the `captured` day differs, so it is excluded from the compare.

```scrut
$ [ "$(grep -v '^captured:' records/materials-manifest.yaml | sha256sum)" = "$(grep -v '^captured:' "$INV_REPO/records/materials-manifest.yaml" | sha256sum)" ] && echo "isolated rebuild matches the fixture manifest"
isolated rebuild matches the fixture manifest
```

```scrut
$ grep -A2 'source-scenario-bare/attached.pdf' "$INV_REPO/records/materials-manifest.yaml"
  source-scenario-bare/attached.pdf:
    size: 608
    sha256: 61b4d4e33f928a4f6801ae74b3e940e0cfac1285aa4a958d46ce0ae142b49ed6
```

## The copy anchors to the pair, not the live tree

The tool path stays in a variable: quoting it would break the
doc-command lint, which requires tool mentions to parse as commands.

```scrut
$ [ "$(sha256sum "$LOS_REPO/records/materials-manifest.yaml" | cut -d' ' -f1)" = "$LIVE_SHA" ] && echo "live manifest untouched"
live manifest untouched
```

```scrut
$ ENTRY=$INV_REPO/tools/materials_manifest.py && $LOS_REPO/.venv/bin/python -c "import importlib.util,sys; sys.path.insert(0, '$INV_REPO/tools'); spec = importlib.util.spec_from_file_location('mm', '$ENTRY'); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); print(mod.ROOT); print(mod.MANIFEST); print(mod.materials_root())" | sed -e "s|$INV_REPO|<REPO>|g" -e "s|$INV_PAIR|<PAIR>|g"
<REPO>
<REPO>/records/materials-manifest.yaml
<PAIR>/materials
```

## Review the attach

```scrut
$ cat > "$TMPDIR/attach-record.yaml" <<EOF
> id: source-scenario-bare
> material: material://source-scenario-bare/attached.pdf
> material_sha256: $MAT_SHA
> EOF
```

```scrut
$ eval "$(los source-revise --file "$TMPDIR/attach-record.yaml" --check | $H/los-bind ATTACH_DIFF '$.diff_sha256')" && echo "$ATTACH_DIFF"
sha256:2f478959e6ecde768db3beffe4aa953f658c82c8a00714cc3704afde1cc9248a
```

## Seal the attach with derived guards

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.record.revise --payload "{\"record\": {\"id\": \"source-scenario-bare\", \"material\": \"material://source-scenario-bare/attached.pdf\", \"material_sha256\": \"$MAT_SHA\"}, \"expected_diff_sha256\": \"$ATTACH_DIFF\"}" --key s06-attach --request-id request-s06-attach --guards auto --out "$TMPDIR/s06-attach.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: source-scenario-bare=1
```

## Submit the attach

```scrut {interpolated: true}
$ los capability source.record.revise --payload-file "$TMPDIR/s06-attach.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{"schema_version":2,"request_id":"request-s06-attach","idempotency_key":"s06-attach","capability":"source.record.revise","ok":true,"replayed":false,"transaction_id":"transaction-20261001-090000-002","receipt_path":"operations/transactions/transaction-20261001-090000-002.yaml","snapshot_after":"$LOS_FIXTURE_SNAPSHOT_3","result":{"ok":true,"transaction_id":"transaction-20261001-090000-002","receipt_path":"operations/transactions/transaction-20261001-090000-002.yaml","artifact_revisions":{"source-scenario-bare":2},"snapshot_after":"$LOS_FIXTURE_SNAPSHOT_3","replayed":false},"error":null}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability source.record.revise
```

## Record the evaluation in its explicit final form

```scrut
$ eval "$(los source-revise --record '{"id": "source-scenario-bare", "evaluations": [{"level": "introductory", "roles": ["first-learning"], "strengths": ["short and exact"], "concepts": ["concept-expected-value"]}]}' --check | $H/los-bind EVAL_DIFF '$.diff_sha256')" && echo "$EVAL_DIFF"
sha256:875f78222b721f37e24ca30af4b597c88cfd562df9a283540bc0447df1ab38ec
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability source.record.revise --payload "{\"record\": {\"id\": \"source-scenario-bare\", \"evaluations\": [{\"level\": \"introductory\", \"roles\": [\"first-learning\"], \"strengths\": [\"short and exact\"], \"concepts\": [\"concept-expected-value\"]}]}, \"expected_diff_sha256\": \"$EVAL_DIFF\"}" --key s06-eval --request-id request-s06-eval --guards auto --out "$TMPDIR/s06-eval.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: source-scenario-bare=2
```

```scrut {interpolated: true}
$ los capability source.record.revise --payload-file "$TMPDIR/s06-eval.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{"schema_version":2,"request_id":"request-s06-eval","idempotency_key":"s06-eval","capability":"source.record.revise","ok":true,"replayed":false,"transaction_id":"transaction-20261001-090000-003","receipt_path":"operations/transactions/transaction-20261001-090000-003.yaml","snapshot_after":"$LOS_FIXTURE_SNAPSHOT_4","result":{"ok":true,"transaction_id":"transaction-20261001-090000-003","receipt_path":"operations/transactions/transaction-20261001-090000-003.yaml","artifact_revisions":{"source-scenario-bare":3},"snapshot_after":"$LOS_FIXTURE_SNAPSHOT_4","replayed":false},"error":null}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability source.record.revise
```

## Create the curated collection it belongs on

```scrut
$ cat > "$TMPDIR/probe-essays.yaml" <<'EOF'
> title: Probe essays
> entries:
> - source: source-scenario-bare
>   group: Probe
>   why: The bare essay under test.
> EOF
```

The draft stays outside the canonical destination. Bind its exact bytes,
check it, seal the current snapshot and revision, and retain the envelope
for an exact replay.

```scrut
$ export COLLECTION_SHA="sha256:$(shasum -a 256 "$TMPDIR/probe-essays.yaml" | cut -d ' ' -f 1)"; los collection-create --file "$TMPDIR/probe-essays.yaml" --file-sha256 "$COLLECTION_SHA" --check > "$TMPDIR/collection-check.json" && $H/los-bind COLLECTION_PAYLOAD '$' < "$TMPDIR/collection-check.json" > /dev/null
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability collection.create --payload "{\"file\":\"$TMPDIR/probe-essays.yaml\",\"file_sha256\":\"$COLLECTION_SHA\"}" --key source-collection --request-id request-source-collection --guards auto --out "$TMPDIR/collection.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: collection:probe-essays=0
```

```scrut
$ los capability collection.create --payload-file "$TMPDIR/collection.json" > "$TMPDIR/collection-created.json" && $H/los-assert-receipt --last --capability collection.create && eval "$(cat "$TMPDIR/collection-created.json" | $H/los-bind COLLECTION_REV '$.result.artifact_revisions.collection:probe-essays')" && echo "$COLLECTION_REV"
1
```

```scrut
$ los capability collection.create --payload-file "$TMPDIR/collection.json" > "$TMPDIR/collection-replayed.json" && eval "$(cat "$TMPDIR/collection-replayed.json" | $H/los-bind COLLECTION_REPLAY '$.replayed')" && echo "$COLLECTION_REPLAY"
true
```

```scrut {output_stream: stderr}
$ los collection-create --file "$TMPDIR/probe-essays.yaml" --file-sha256 "$COLLECTION_SHA" --check
los: INVALID_REQUEST: collection 'probe-essays' already exists at sources/collections/probe-essays.yaml; creation never overwrites
[2]
```

```scrut
$ printf '\n' >> "$TMPDIR/probe-essays.yaml"; los collection-create --file "$TMPDIR/probe-essays.yaml" --file-sha256 "$COLLECTION_SHA" --check > "$TMPDIR/changed-collection.txt" 2>&1; refusal_status=$?; test "$refusal_status" -eq 2 && grep -q "approved collection file changed before use" "$TMPDIR/changed-collection.txt" && echo "changed reviewed bytes refused"
changed reviewed bytes refused
```

## The collection validates clean

```scrut
$ (set -o pipefail; los validate | tail -n 1)
0 error(s), 13 warning(s) — OK
```

## Revise one entry why through its gateway

```scrut
$ eval "$(los collection-entry-revise --record '{"collection": "probe-essays", "source": "source-scenario-bare", "why": "The bare essay, examined."}' --check | $H/los-bind ENTRY_DIFF '$.diff_sha256')" && echo "$ENTRY_DIFF"
sha256:2282313ea24c7f43af808416941f8b45aee64af28ce53b58c25356ecad4f0c55
```

```scrut {output_stream: stderr}
$ $H/los-seal --capability collection.entry.revise --payload "{\"record\": {\"collection\": \"probe-essays\", \"source\": \"source-scenario-bare\", \"why\": \"The bare essay, examined.\"}, \"expected_diff_sha256\": \"$ENTRY_DIFF\"}" --key s06-entry --request-id request-s06-entry --guards auto --out "$TMPDIR/s06-entry.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
seal_envelope: guards auto: collection:probe-essays=1
```

```scrut {interpolated: true}
$ los capability collection.entry.revise --payload-file "$TMPDIR/s06-entry.json"
> los_snapshot_status=$?; eval "$(los_fixture_values)"; (exit "$los_snapshot_status")
{"schema_version":2,"request_id":"request-s06-entry","idempotency_key":"s06-entry","capability":"collection.entry.revise","ok":true,"replayed":false,"transaction_id":"transaction-20261001-090000-005","receipt_path":"operations/transactions/transaction-20261001-090000-005.yaml","snapshot_after":"$LOS_FIXTURE_SNAPSHOT_6","result":{"ok":true,"transaction_id":"transaction-20261001-090000-005","receipt_path":"operations/transactions/transaction-20261001-090000-005.yaml","artifact_revisions":{"collection:probe-essays":2},"snapshot_after":"$LOS_FIXTURE_SNAPSHOT_6","replayed":false},"error":null}
```

## The newest receipt names the capability

```scrut
$ $H/los-assert-receipt --last --capability collection.entry.revise
```

## Rebuild the source index

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

## The index and the rendered collection carry the paper

```scrut
$ grep -n "Bare Essay" generated/source-index.md | head -n 3
13:**B:** [Bare Essay](#bare-essay)
28:### Bare Essay
54:- **Bare Essay** (`source-scenario-bare`) — roles: first-learning — level: introductory — short and exact
```

```scrut
$ grep -n "examined" generated/collections/probe-essays.md
9:  - The bare essay, examined.
```

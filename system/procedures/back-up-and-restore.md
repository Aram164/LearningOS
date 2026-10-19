---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Back up and restore (WORKFLOWS §31)

Executable transcript of the backup drill: manifest the three
roots, copy them beside the manifest, and verify the restore both
ways. The fixture ships Core and materials siblings but no UI
sibling, so the drill copies the pair's UI checkout (minus its
`.git`, which the manifest never inventories) and completes its
declared plugin set with a labeled `build-info.json` stand-in —
the checkout itself lacks that declared asset, and the UI stays
untouched. A tampered restored byte fails the drill.
`tests/test_procedures.py` runs it with Scrut; `<REPO>` comes from
the `LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Stage the drill UI from the pair checkout

```scrut
$ mkdir -p "$TMPDIR/backup" && cp -a "$LOS_REPO/../obsidian-ui" "$TMPDIR/backup/ui-src" && rm -rf "$TMPDIR/backup/ui-src/.git" && cat > "$TMPDIR/backup/ui-src/plugin/build-info.json" <<'EOF'
> {"stand_in": true, "note": "S10 drill: the pair checkout lacks its declared build-info.json."}
> EOF
```

## Manifest the three roots outside every root

Take the backup:

1. run `los backup-manifest --out /path/outside/every/root/manifest.json`
   (`--ui-root` / `--materials-root` override the sibling defaults). The
   command refuses a path inside any backed-up root, writes atomically,
   and prints a short summary (roots, entry count, aggregate digest,
   path) instead of the megabyte of JSON — the full manifest stays
   available behind the explicit `--stdout` flag;
2. copy the three roots beside the manifest (`cp -a` each authority);
   recovery pairs the restored data with a Core checkout at the commit
   the manifest's `provenance` records;
3. after any restore — and as a drill before relying on one — run
   `los backup-verify --manifest manifest.json --restored-core … --restored-ui …
   --restored-materials …`. `--checksums-only` checks integrity without
   executing restored code; the full form additionally runs the restored
   installer in dry-run mode with projection, validation, and restored UI
   bundle smoke checks.

```scrut
$ los backup-manifest --ui-root "$TMPDIR/backup/ui-src" --out "$TMPDIR/backup/manifest.json" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"]); print(d["roots"]); print(d["entries"]); print(d["aggregate_sha256"])'
True
['core', 'materials', 'ui']
481
sha256:f08838e84311b432a1c44b3c581191e919d10db03cbb386d55f02720d084067b
```

## The manifest binds data to Core's commit

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import json,os; d = json.load(open(os.path.join(os.environ["TMPDIR"], "backup/manifest.json"))); print(len(d["entries"])); print(d["aggregate_sha256"]); print(d["provenance"]["data_contract_version"]); print(d["provenance"]["core"]["commit"] is not None, d["provenance"]["ui"]["commit"])'
481
sha256:f08838e84311b432a1c44b3c581191e919d10db03cbb386d55f02720d084067b
54
True None
```

## The full manifest stays behind the explicit flag

```scrut
$ los backup-manifest --ui-root "$TMPDIR/backup/ui-src" --stdout | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(len(d["entries"])); print(sorted({e["root"] for e in d["entries"]})); print(d["aggregate_sha256"])'
481
['core', 'materials', 'ui']
sha256:f08838e84311b432a1c44b3c581191e919d10db03cbb386d55f02720d084067b
```

## Capture the pre-refusal state

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-refuse-manifest.json", "w")); print("captured", len(st["rc"]))'
captured 1
```

## A manifest path inside a backed-up root is refused

```scrut {output_stream: stderr}
$ los backup-manifest --ui-root "$TMPDIR/backup/ui-src" --out manifest.json
los: INVALID_REQUEST: refusing to write the manifest inside the backed-up core root: manifest.json
[2]
```

## The refusal added no receipt and moved no canonical byte

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-refuse-manifest.json")); fp=canonical_fingerprint(Path(".")); rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); assert fp==st["fp"], (fp, st["fp"]); assert rc==st["rc"], (rc, st["rc"]); print("unchanged")'
unchanged
```

## Copy the three roots beside the manifest

```scrut
$ cp -a "$LOS_FX" "$TMPDIR/backup/restored-core" && cp -a "$(dirname "$LOS_FX")/materials" "$TMPDIR/backup/restored-materials" && cp -a "$TMPDIR/backup/ui-src" "$TMPDIR/backup/restored-ui"
```

## The copies match their authorities

```scrut
$ diff -r -q "$LOS_FX" "$TMPDIR/backup/restored-core" && diff -r -q "$(dirname "$LOS_FX")/materials" "$TMPDIR/backup/restored-materials" && diff -r -q "$TMPDIR/backup/ui-src" "$TMPDIR/backup/restored-ui" && echo "copies match"
copies match
```

## Verify the restore without executing restored code

```scrut
$ los backup-verify --manifest "$TMPDIR/backup/manifest.json" --restored-core "$TMPDIR/backup/restored-core" --restored-ui "$TMPDIR/backup/restored-ui" --restored-materials "$TMPDIR/backup/restored-materials" --checksums-only
{"ok":true,"checked":481,"issues":[]}
```

## Verify the restore in full

```scrut
$ los backup-verify --manifest "$TMPDIR/backup/manifest.json" --restored-core "$TMPDIR/backup/restored-core" --restored-ui "$TMPDIR/backup/restored-ui" --restored-materials "$TMPDIR/backup/restored-materials" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"]); [print(c["id"], c["ok"]) for c in d["checks"]]; print(d["manual_ui_open_required"])'
True
checksums True
restore-provenance True
materials-alias-layer True
canonical-validation True
projection-regeneration True
ui-contract-lock True
ui-asset-declaration True
ui-install-preflight True
ui-bundle-smoke True
True
```

## A tampered restored byte fails the drill

```scrut
$ printf 'tamper' >> "$TMPDIR/backup/restored-materials/source-demo-book/book.pdf" && los backup-verify --manifest "$TMPDIR/backup/manifest.json" --restored-core "$TMPDIR/backup/restored-core" --restored-ui "$TMPDIR/backup/restored-ui" --restored-materials "$TMPDIR/backup/restored-materials" --checksums-only >"$TMPDIR/backup/tamper-out.txt" 2>&1; echo "exit=$?"; cat "$TMPDIR/backup/tamper-out.txt"
exit=1
{"ok":false,"checked":481,"issues":[{"root":"materials","path":"source-demo-book/book.pdf","issue":"checksum-mismatch"}]}
```

## The fixture itself still validates

```scrut
$ los validate | tail -n 1
0 error(s), 10 warning(s) — OK
```

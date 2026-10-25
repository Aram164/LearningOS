#!/bin/bash
# V5 phase 1: run system/procedures/back-up-and-restore.md exactly as written
# on the rich_world fixture. Blocks are quoted verbatim from the transcript.
set -u
export TMPDIR="$HOME/los-glm-V5-2026-10/tmp"
export LOS_REPO="$HOME/los-glm-V5-2026-10/repository"
mkdir -p "$TMPDIR"

mark() { echo; echo "===== BLOCK: $1 ====="; }

mark "Build the fixture"
eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
echo "LOS_FX=$LOS_FX"

mark "Stage the drill UI from the pair checkout"
mkdir -p "$TMPDIR/backup" && cp -a "$LOS_REPO/../obsidian-ui" "$TMPDIR/backup/ui-src" && rm -rf "$TMPDIR/backup/ui-src/.git" && cat > "$TMPDIR/backup/ui-src/plugin/build-info.json" <<'EOF'
{"stand_in": true, "note": "S10 drill: the pair checkout lacks its declared build-info.json."}
EOF
echo "staged ui-src"

mark "Manifest the three roots outside every root (out + summary)"
los backup-manifest --ui-root "$TMPDIR/backup/ui-src" --out "$TMPDIR/backup/manifest.json" > "$TMPDIR/backup/summary.json" && eval "$(cat "$TMPDIR/backup/summary.json" | $H/los-bind BACKUP_AGGREGATE '$.aggregate_sha256')" && cat "$TMPDIR/backup/summary.json" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"]); print(d["roots"]); print(d["entries"]); print(d["aggregate_sha256"])'

mark "The manifest binds data to Core's commit"
$LOS_REPO/.venv/bin/python -c 'import json,os; d = json.load(open(os.path.join(os.environ["TMPDIR"], "backup/manifest.json"))); print(len(d["entries"])); print(d["aggregate_sha256"]); print(d["provenance"]["data_contract_version"]); print(d["provenance"]["core"]["commit"] is not None, d["provenance"]["ui"]["commit"])'

mark "The full manifest stays behind the explicit flag"
los backup-manifest --ui-root "$TMPDIR/backup/ui-src" --stdout | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(len(d["entries"])); print(sorted({e["root"] for e in d["entries"]})); print(d["aggregate_sha256"])'

mark "Capture the pre-refusal state"
$LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st={"fp": canonical_fingerprint(Path(".")), "rc": sorted(glob.glob("operations/transactions/transaction-*.yaml"))}; json.dump(st, open(os.environ["TMPDIR"]+"/fp-refuse-manifest.json", "w")); print("captured", len(st["rc"]))'

mark "A manifest path inside a backed-up root is refused"
los backup-manifest --ui-root "$TMPDIR/backup/ui-src" --out manifest.json
echo "refusal-exit=$?"

mark "The refusal added no receipt and moved no canonical byte"
$LOS_REPO/.venv/bin/python -c 'import glob,json,os,sys; sys.path.insert(0, os.environ["LOS_REPO"]+"/tools"); from learning_os.store.fingerprint import canonical_fingerprint; from pathlib import Path; st=json.load(open(os.environ["TMPDIR"]+"/fp-refuse-manifest.json")); fp=canonical_fingerprint(Path(".")); rc=sorted(glob.glob("operations/transactions/transaction-*.yaml")); assert fp==st["fp"], (fp, st["fp"]); assert rc==st["rc"], (rc, st["rc"]); print("unchanged")'

mark "Copy the three roots beside the manifest"
cp -a "$LOS_FX" "$TMPDIR/backup/restored-core" && cp -a "$(dirname "$LOS_FX")/materials" "$TMPDIR/backup/restored-materials" && cp -a "$TMPDIR/backup/ui-src" "$TMPDIR/backup/restored-ui"
echo "copied"

mark "The copies match their authorities"
diff -r -q "$LOS_FX" "$TMPDIR/backup/restored-core" && diff -r -q "$(dirname "$LOS_FX")/materials" "$TMPDIR/backup/restored-materials" && diff -r -q "$TMPDIR/backup/ui-src" "$TMPDIR/backup/restored-ui" && echo "copies match"

mark "Verify the restore without executing restored code"
los backup-verify --manifest "$TMPDIR/backup/manifest.json" --restored-core "$TMPDIR/backup/restored-core" --restored-ui "$TMPDIR/backup/restored-ui" --restored-materials "$TMPDIR/backup/restored-materials" --checksums-only

mark "Verify the restore in full"
los backup-verify --manifest "$TMPDIR/backup/manifest.json" --restored-core "$TMPDIR/backup/restored-core" --restored-ui "$TMPDIR/backup/restored-ui" --restored-materials "$TMPDIR/backup/restored-materials" | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["ok"]); [print(c["id"], c["ok"]) for c in d["checks"]]; print(d["manual_ui_open_required"])'

mark "A tampered restored byte fails the drill"
printf 'tamper' >> "$TMPDIR/backup/restored-materials/source-demo-book/book.pdf" && los backup-verify --manifest "$TMPDIR/backup/manifest.json" --restored-core "$TMPDIR/backup/restored-core" --restored-ui "$TMPDIR/backup/restored-ui" --restored-materials "$TMPDIR/backup/restored-materials" --checksums-only >"$TMPDIR/backup/tamper-out.txt" 2>&1; echo "exit=$?"; cat "$TMPDIR/backup/tamper-out.txt"

mark "The fixture itself still validates"
los validate | tail -n 1

mark "DONE"

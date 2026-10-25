#!/bin/bash
# V5 attack 6 (fixed): the fixture is data-only, so los runs from the clone's
# tools with --root aimed at the fixture copy.
set -u
HOMEROOT="$HOME/los-glm-V5-2026-10"
FXSRC="$HOMEROOT/tmp/los-fx-jwfyl23x/LearningOS"
PY="$HOMEROOT/repository/.venv/bin/python"
LOS="$PY $HOMEROOT/repository/tools/los.py"

mark() { echo; echo "===== ATTACK 6.$1 ====="; }
fullverify() {  # $1 = layout root with repository/, obsidian-ui/, materials/ ; $2 = manifest ; $3 = out json
  $LOS --root "$HOMEROOT/repository" backup-verify --manifest "$2" \
    --restored-core "$1/repository" --restored-ui "$1/obsidian-ui" \
    --restored-materials "$1/materials" > "$3" 2>&1
  echo "exit=$?"
  $PY -c 'import json,sys; d=json.load(open(sys.argv[1])); print("ok:",d["ok"]); [print(" ",c["id"],c["ok"], "" if c["ok"] else json.dumps(c.get("detail",{}))[:260]) for c in d["checks"]]' "$3"
}

mark "0: fresh fixture copy, intact control (case C)"
rm -rf "$HOMEROOT/scratch/attack6-fx"
mkdir -p "$HOMEROOT/scratch/attack6-fx"
cp -a "$FXSRC/repository" "$HOMEROOT/scratch/attack6-fx/repository"
cp -a "$FXSRC/materials" "$HOMEROOT/scratch/attack6-fx/materials"
cp -a "$HOMEROOT/tmp/backup/ui-src" "$HOMEROOT/scratch/attack6-fx/obsidian-ui"
$LOS --root "$HOMEROOT/scratch/attack6-fx/repository" validate 2>&1 | tail -1
$LOS --root "$HOMEROOT/scratch/attack6-fx/repository" backup-manifest --out "$HOMEROOT/scratch/attack6-manifest-c.json" > /dev/null
echo "control manifest taken"
rm -rf "$HOMEROOT/scratch/attack6-restore-c"; mkdir -p "$HOMEROOT/scratch/attack6-restore-c"
cp -a "$HOMEROOT/scratch/attack6-fx/repository" "$HOMEROOT/scratch/attack6-restore-c/repository"
cp -a "$HOMEROOT/scratch/attack6-fx/obsidian-ui" "$HOMEROOT/scratch/attack6-restore-c/obsidian-ui"
cp -a "$HOMEROOT/scratch/attack6-fx/materials" "$HOMEROOT/scratch/attack6-restore-c/materials"
fullverify "$HOMEROOT/scratch/attack6-restore-c" "$HOMEROOT/scratch/attack6-manifest-c.json" "$HOMEROOT/scratch/attack6-verify-c.json"

mark "A: referenced material file already absent when the backup is taken"
rm "$HOMEROOT/scratch/attack6-fx/materials/source-demo-book/book.pdf"
echo "deleted materials/source-demo-book/book.pdf (referenced by sources/sources.yaml)"
$LOS --root "$HOMEROOT/scratch/attack6-fx/repository" backup-manifest --out "$HOMEROOT/scratch/attack6-manifest-a.json" > "$HOMEROOT/scratch/attack6-summary-a.json"
echo "backup-manifest exit=$? (does the backup refuse a damaged materials tree?)"
$PY -c 'import json,sys; d=json.load(open(sys.argv[1])); print("ok:",d["ok"],"entries:",d["entries"])' "$HOMEROOT/scratch/attack6-summary-a.json"
rm -rf "$HOMEROOT/scratch/attack6-restore-a"; mkdir -p "$HOMEROOT/scratch/attack6-restore-a"
cp -a "$HOMEROOT/scratch/attack6-fx/repository" "$HOMEROOT/scratch/attack6-restore-a/repository"
cp -a "$HOMEROOT/scratch/attack6-fx/obsidian-ui" "$HOMEROOT/scratch/attack6-restore-a/obsidian-ui"
cp -a "$HOMEROOT/scratch/attack6-fx/materials" "$HOMEROOT/scratch/attack6-restore-a/materials"
fullverify "$HOMEROOT/scratch/attack6-restore-a" "$HOMEROOT/scratch/attack6-manifest-a.json" "$HOMEROOT/scratch/attack6-verify-a.json"

mark "B: recorded alias whose target folder is not in the restore"
cp -a "$FXSRC/materials/source-demo-book/book.pdf" "$HOMEROOT/scratch/attack6-fx/materials/source-demo-book/book.pdf"
mkdir -p "$HOMEROOT/scratch/attack6-fx/materials/source-empty"
printf 'ds' > "$HOMEROOT/scratch/attack6-fx/materials/source-empty/.DS_Store"
mkdir -p "$HOMEROOT/scratch/attack6-fx/materials/.flat"
ln -sfn ../source-demo-book "$HOMEROOT/scratch/attack6-fx/materials/.flat/source-demo-book"
ln -sfn ../source-empty "$HOMEROOT/scratch/attack6-fx/materials/.flat/source-empty"
echo "alias layer built: source-demo-book (real) + source-empty (only .DS_Store inside)"
$LOS --root "$HOMEROOT/scratch/attack6-fx/repository" backup-manifest --out "$HOMEROOT/scratch/attack6-manifest-b.json" > /dev/null
$PY - <<'EOF'
import json
d = json.load(open("/Users/aramaljanadi/los-glm-V5-2026-10/scratch/attack6-manifest-b.json"))
print("materials_aliases:", d["materials_aliases"])
print("materials entries:", [e["path"] for e in d["entries"] if e["root"] == "materials"])
EOF
rm -rf "$HOMEROOT/scratch/attack6-restore-b"; mkdir -p "$HOMEROOT/scratch/attack6-restore-b"
cp -a "$HOMEROOT/scratch/attack6-fx/repository" "$HOMEROOT/scratch/attack6-restore-b/repository"
cp -a "$HOMEROOT/scratch/attack6-fx/obsidian-ui" "$HOMEROOT/scratch/attack6-restore-b/obsidian-ui"
cp -a "$HOMEROOT/scratch/attack6-fx/materials" "$HOMEROOT/scratch/attack6-restore-b/materials"
rm -rf "$HOMEROOT/scratch/attack6-restore-b/materials/source-empty"
echo "deleted source-empty/ from the restore (alias target lost)"
fullverify "$HOMEROOT/scratch/attack6-restore-b" "$HOMEROOT/scratch/attack6-manifest-b.json" "$HOMEROOT/scratch/attack6-verify-b.json"

mark "DONE attack 6"

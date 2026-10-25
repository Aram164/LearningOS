#!/bin/bash
# V5 attacks 1-3: tampered byte, deleted file, non-empty restore target.
# Each works on a fresh copy of the clone restore; restore-1 stays pristine.
set -u
HOMEROOT="$HOME/los-glm-V5-2026-10"
LOS="$HOMEROOT/repository/.venv/bin/python $HOMEROOT/repository/tools/los.py"
PY="$HOMEROOT/repository/.venv/bin/python"
M="$HOMEROOT/scratch/manifest.json"

mark() { echo; echo "===== ATTACK $1 ====="; }
verify_co() {  # verify checksums-only against $1, print ok + first issues
  $LOS backup-verify --manifest "$M" \
    --restored-core "$1/repository" --restored-ui "$1/obsidian-ui" \
    --restored-materials "$1/materials" --checksums-only > "$2" 2>&1
  echo "exit=$?"
  $PY -c 'import json,sys; d=json.load(open(sys.argv[1])); print("ok:",d["ok"],"checked:",d["checked"]); [print("  issue:",i) for i in d["issues"][:6]]; print("  total issues:", len(d["issues"]))' "$2"
}

mark "1: one tampered byte in the backed-up core tree"
rm -rf "$HOMEROOT/scratch/attack1-restore"
cp -a "$HOMEROOT/scratch/restore-1" "$HOMEROOT/scratch/attack1-restore"
TARGET="$HOMEROOT/scratch/attack1-restore/repository/curriculum/resume.yaml"
$PY - <<EOF
from pathlib import Path
p = Path("$TARGET")
data = bytearray(p.read_bytes())
print("file:", p.name, "bytes:", len(data), "byte@100:", data[100])
data[100] ^= 1
p.write_bytes(bytes(data))
print("flipped one byte at offset 100")
EOF
verify_co "$HOMEROOT/scratch/attack1-restore" "$HOMEROOT/scratch/attack1-verify.json"

mark "1b: one tampered byte in the manifest itself"
rm -rf "$HOMEROOT/scratch/attack1b-restore"
cp -a "$HOMEROOT/scratch/restore-1" "$HOMEROOT/scratch/attack1b-restore"
$PY - <<'EOF'
import json
p = "/Users/aramaljanadi/los-glm-V5-2026-10/scratch/manifest-1b.json"
d = json.load(open("/Users/aramaljanadi/los-glm-V5-2026-10/scratch/manifest.json"))
d["entries"][0]["size"] += 1  # one byte of lie in one entry
json.dump(d, open(p, "w"))
print("manifest copy with one tampered entry size written")
EOF
$LOS backup-verify --manifest "$HOMEROOT/scratch/manifest-1b.json" \
  --restored-core "$HOMEROOT/scratch/attack1b-restore/repository" \
  --restored-ui "$HOMEROOT/scratch/attack1b-restore/obsidian-ui" \
  --restored-materials "$HOMEROOT/scratch/attack1b-restore/materials" \
  --checksums-only > "$HOMEROOT/scratch/attack1b-verify.json" 2>&1
echo "exit=$?"
$PY -c 'import json,sys; d=json.load(open(sys.argv[1])); print("ok:",d["ok"]); [print("  issue:",i) for i in d["issues"][:6]]' "$HOMEROOT/scratch/attack1b-verify.json"

mark "2: a deleted file in the restored core"
rm -rf "$HOMEROOT/scratch/attack2-restore"
cp -a "$HOMEROOT/scratch/restore-1" "$HOMEROOT/scratch/attack2-restore"
VICTIM="$HOMEROOT/scratch/attack2-restore/repository/curriculum/thematic-groups.yaml"
wc -c "$VICTIM"; rm "$VICTIM"; echo "deleted curriculum/thematic-groups.yaml"
verify_co "$HOMEROOT/scratch/attack2-restore" "$HOMEROOT/scratch/attack2-verify.json"

mark "2b: deleted file, full verify form"
$LOS backup-verify --manifest "$M" \
  --restored-core "$HOMEROOT/scratch/attack2-restore/repository" \
  --restored-ui "$HOMEROOT/scratch/attack2-restore/obsidian-ui" \
  --restored-materials "$HOMEROOT/scratch/attack2-restore/materials" \
  > "$HOMEROOT/scratch/attack2-verify-full.json" 2>&1
echo "exit=$?"
$PY -c 'import json,sys; d=json.load(open(sys.argv[1])); print("ok:",d["ok"]); [print("  check:",c["id"],c["ok"]) for c in d["checks"]]; [print("  issue:",i) for i in d["checks"][0]["detail"]["issues"][:4]]' "$HOMEROOT/scratch/attack2-verify-full.json"

mark "3: restore into a NON-EMPTY folder — extra canonical file"
rm -rf "$HOMEROOT/scratch/attack3-restore"
cp -a "$HOMEROOT/scratch/restore-1" "$HOMEROOT/scratch/attack3-restore"
printf -- "---\nid: note-sneaky\ntitle: Planted\n---\n\nAn extra canonical note an earlier partial restore left behind.\n" > "$HOMEROOT/scratch/attack3-restore/repository/knowledge/notes/note-sneaky.md"
echo "planted knowledge/notes/note-sneaky.md"
verify_co "$HOMEROOT/scratch/attack3-restore" "$HOMEROOT/scratch/attack3-verify.json"

mark "3b: extra file OUTSIDE the allowlist at core root (not admitted anywhere)"
printf 'stray\n' > "$HOMEROOT/scratch/attack3-restore/repository/stray-root-file.txt"
echo "planted stray-root-file.txt at core root"
verify_co "$HOMEROOT/scratch/attack3-restore" "$HOMEROOT/scratch/attack3b-verify.json"

mark "3c: extra file under an EXCLUDED name (generated/)"
mkdir -p "$HOMEROOT/scratch/attack3-restore/repository/generated"
printf 'stale\n' > "$HOMEROOT/scratch/attack3-restore/repository/generated/stale-report.md"
echo "planted generated/stale-report.md"
verify_co "$HOMEROOT/scratch/attack3-restore" "$HOMEROOT/scratch/attack3c-verify.json"

mark "DONE attacks 1-3"

#!/bin/bash
# V5 attack 5: local-only attachments (pinned in system/contracts/local-attachments.yaml)
# are absent from this clone. Three probes: absence warnings, present-and-different
# errors, and the backup/verify round trip with fabricated attachments.
set -u
HOMEROOT="$HOME/los-glm-V5-2026-10"
LOS="$HOMEROOT/repository/.venv/bin/python $HOMEROOT/repository/tools/los.py"
PY="$HOMEROOT/repository/.venv/bin/python"

mark() { echo; echo "===== ATTACK 5.$1 ====="; }

mark "1: the five pinned paths in this clone"
for f in \
  knowledge/attachments/note-sad-descriptive-probability-handwritten/teil-01-part1.pdf \
  knowledge/attachments/note-sad-descriptive-probability-handwritten/teil-01-part2.pdf \
  knowledge/attachments/note-sad-distributions-handwritten/teil-02-part1.pdf \
  knowledge/attachments/note-sad-distributions-handwritten/teil-02-part2.pdf \
  knowledge/attachments/note-sad-hypothesis-testing-handwritten/teil-03.pdf ; do
  [ -f "$HOMEROOT/repository/$f" ] && echo "PRESENT $f" || echo "ABSENT  $f"
done
echo "ATTACH-LOCAL warnings in the clone's validate (see phase2 log):"
grep -c "ATTACH-LOCAL-ABSENT" "$HOMEROOT/scratch/clone-validate.txt"

mark "2: fabricated attachments present-and-different -> error?"
rm -rf "$HOMEROOT/scratch/attach-clone"
cp -a "$HOMEROOT/repository" "$HOMEROOT/scratch/attach-clone"
mkdir -p "$HOMEROOT/scratch/attach-clone/knowledge/attachments/note-sad-descriptive-probability-handwritten" \
         "$HOMEROOT/scratch/attach-clone/knowledge/attachments/note-sad-distributions-handwritten"
printf 'fabricated bytes, not the real scan' > "$HOMEROOT/scratch/attach-clone/knowledge/attachments/note-sad-descriptive-probability-handwritten/teil-01-part1.pdf"
printf 'other fabricated bytes' > "$HOMEROOT/scratch/attach-clone/knowledge/attachments/note-sad-distributions-handwritten/teil-02-part1.pdf"
cd "$HOMEROOT/scratch/attach-clone"
$PY tools/los.py validate > "$HOMEROOT/scratch/attach-validate.txt" 2>&1
echo "validate exit=$?"
grep -n "ATTACH-LOCAL" "$HOMEROOT/scratch/attach-validate.txt"
tail -1 "$HOMEROOT/scratch/attach-validate.txt"

mark "3: backup walks disk, not the index -> fabricated files enter the manifest"
cd "$HOMEROOT/scratch/attach-clone"
$PY tools/los.py --root "$HOMEROOT/scratch/attach-clone" backup-manifest \
  --ui-root "$HOMEROOT/obsidian-ui" --materials-root "$HOMEROOT/materials" \
  --out "$HOMEROOT/scratch/attach-manifest.json" > "$HOMEROOT/scratch/attach-summary.json"
echo "backup exit=$?"
$PY - <<'EOF'
import json
d = json.load(open("/Users/aramaljanadi/los-glm-V5-2026-10/scratch/attach-manifest.json"))
hits = [e for e in d["entries"] if e["path"].startswith("knowledge/attachments/")]
for e in hits:
    print("manifest entry:", e["root"], e["path"], e["size"])
print("attachment entries:", len(hits))
EOF

mark "4: restore, then delete one fabricated attachment -> verify?"
rm -rf "$HOMEROOT/scratch/attach-restore"
mkdir -p "$HOMEROOT/scratch/attach-restore"
cp -a "$HOMEROOT/scratch/attach-clone" "$HOMEROOT/scratch/attach-restore/attach-clone"
cp -a "$HOMEROOT/obsidian-ui" "$HOMEROOT/scratch/attach-restore/obsidian-ui"
cp -a "$HOMEROOT/materials" "$HOMEROOT/scratch/attach-restore/materials"
rm "$HOMEROOT/scratch/attach-restore/attach-clone/knowledge/attachments/note-sad-distributions-handwritten/teil-02-part1.pdf"
echo "deleted the fabricated teil-02-part1.pdf from the restore"
$LOS backup-verify --manifest "$HOMEROOT/scratch/attach-manifest.json" \
  --restored-core "$HOMEROOT/scratch/attach-restore/attach-clone" \
  --restored-ui "$HOMEROOT/scratch/attach-restore/obsidian-ui" \
  --restored-materials "$HOMEROOT/scratch/attach-restore/materials" \
  --checksums-only > "$HOMEROOT/scratch/attach-verify.json" 2>&1
echo "exit=$?"
head -c 600 "$HOMEROOT/scratch/attach-verify.json"; echo

mark "DONE attack 5"

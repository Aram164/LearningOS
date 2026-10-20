#!/bin/sh
# Snapshot the final working state: every file that differs from the base.
#
# The rebuild takes the code from this snapshot and the churn from the
# digest-reverted one, so the snapshot must hold *every* file the seven
# commits touch, at its final content. "Every file that differs from
# 40d8afe" is exactly that set: the seven commits' work plus the F-05
# correction and the churn it forced.
#
# Usage: sh snapshot_total.sh <out dir>
set -e
cd "$(dirname "$0")/../../repository" || exit 1
OUT="$1"
mkdir -p "$OUT"

# Tracked files whose content differs from the base (staged or not).
git diff --name-only 40d8afe -z | while IFS= read -r -d '' f; do
  [ -f "$f" ] || continue
  mkdir -p "$OUT/$(dirname "$f")"
  cp "$f" "$OUT/$f"
done

# New files the base does not have.
git ls-files --others --exclude-standard -z | while IFS= read -r -d '' f; do
  mkdir -p "$OUT/$(dirname "$f")"
  cp "$f" "$OUT/$f"
done

echo "snapshot: $(find "$OUT" -type f | wc -l) file(s) in $OUT"

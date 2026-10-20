#!/bin/sh
# Verify the branch's commits one at a time, in the primary checkout.
#
# The primary checkout is the one that has ../materials and ../obsidian-ui
# mounted, so the whole gate runs here; a linked worktree was tried first
# and the procedure-transcript fixture hangs there, so the verification
# moves through the primary checkout instead.
#
# Serial on purpose: seven suites at once saturated the machine (load 14 on
# 12 cores) and made every run slower than it needed to be.
#
# Usage: sh verify_in_place.sh <out dir> <sha:mode> [<sha:mode> ...]
#   mode = full    — the whole suite
#   mode = focused — the suites the commit touches
set -e
REPO=/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository
OUT="$1"
shift
mkdir -p "$OUT"

cd "$REPO"
START_BRANCH=$(git rev-parse --abbrev-ref HEAD)
restore() {
  git checkout -q "$START_BRANCH" || true
}
trap restore EXIT

for spec in "$@"; do
  sha=${spec%%:*}
  mode=${spec##*:}
  name=$(git log -1 --format=%h "$sha")
  log="$OUT/$name.log"
  git checkout -q "$sha"
  (
    echo "### $name $mode $(git log -1 --format=%s)"
    if ! make check; then echo "CHECK FAILED at $name"; exit 1; fi
    if ! make warnings; then echo "WARNINGS FAILED at $name"; exit 1; fi
    if ! make lint; then echo "LINT FAILED at $name"; exit 1; fi
    if ! make typecheck; then echo "TYPECHECK FAILED at $name"; exit 1; fi
    if [ "$mode" = "full" ]; then
      if ! .venv/bin/python -m pytest -q --no-header -p no:randomly; then
        echo "PYTEST FAILED at $name"; exit 1
      fi
    else
      if ! .venv/bin/python -m pytest -q --no-header -p no:randomly $PYTEST_FILES; then
        echo "PYTEST FAILED at $name"; exit 1
      fi
    fi
    echo "### $name GREEN"
  ) > "$log" 2>&1 || true
  if grep -q "### $name GREEN" "$log"; then
    echo "### $name GREEN"
  else
    echo "### $name FAILED — see $log"
    tail -5 "$log"
  fi
done
restore
trap - EXIT
echo "--- back on $(git rev-parse --abbrev-ref HEAD) ---"

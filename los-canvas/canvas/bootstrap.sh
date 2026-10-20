#!/usr/bin/env bash
# Rebuild everything the canvas needs, from the operator's own checkouts.
#
#   ./bootstrap.sh [CORE_REPO] [UI_REPO]
#
# Defaults point at the live tree. Nothing in CORE_REPO or UI_REPO is
# written to: both are cloned, and the UI's node_modules is copied
# read-only (the paired Core/UI contract tests shell out to Node + Ajv).
set -euo pipefail

# The canvas root is the directory that holds canvas/ and reports/ — the
# harness resolves its clones relative to its own location, so the clones
# must sit beside canvas/, not inside it.
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CORE_REPO="${1:-/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository}"
UI_REPO="${2:-/Users/aramaljanadi/Desktop/semestercontext/LearningOS/obsidian-ui}"
PAIRS="$HERE/LearningOS"

say() { printf '%s\n' "$*"; }

if [ ! -d "$CORE_REPO/.git" ]; then
  say "bootstrap: no Core repository at $CORE_REPO"; exit 2
fi
if [ ! -d "$UI_REPO/.git" ]; then
  say "bootstrap: no UI repository at $UI_REPO"; exit 2
fi

mkdir -p "$PAIRS"

if [ ! -d "$PAIRS/repository/.git" ]; then
  say "bootstrap: cloning Core from $CORE_REPO"
  git clone "$CORE_REPO" "$PAIRS/repository"
else
  say "bootstrap: Core clone already present"
fi

if [ ! -d "$PAIRS/obsidian-ui/.git" ]; then
  say "bootstrap: cloning UI from $UI_REPO"
  git clone "$UI_REPO" "$PAIRS/obsidian-ui"
else
  say "bootstrap: UI clone already present"
fi

if [ ! -x "$PAIRS/repository/.venv/bin/python" ]; then
  say "bootstrap: building the Core venv (make setup; needs network once)"
  (cd "$PAIRS/repository" && make setup)
else
  say "bootstrap: Core venv already present"
fi

# The editable install records an absolute path to tools/. If the clone was
# moved, that path is stale and `import learning_os` fails. Re-point it.
if ! (cd "$PAIRS/repository" && .venv/bin/python -c "import learning_os" >/dev/null 2>&1); then
  say "bootstrap: re-pointing the editable install at this checkout"
  (cd "$PAIRS/repository" && .venv/bin/python -m pip install -e . >/dev/null)
fi

if [ ! -d "$PAIRS/obsidian-ui/node_modules" ] && [ -d "$UI_REPO/node_modules" ]; then
  say "bootstrap: copying the UI node_modules (read-only on the source)"
  cp -R "$UI_REPO/node_modules" "$PAIRS/obsidian-ui/node_modules"
else
  say "bootstrap: UI node_modules already present (or none to copy)"
fi

say "bootstrap: rebuilding the Core projections"
(cd "$PAIRS/repository" && .venv/bin/python tools/generate.py >/dev/null)

say ""
say "bootstrap: ready."
say "  run the suites:   $HERE/canvas/run-all.sh"
say "  the clone's own:  cd $PAIRS/repository && .venv/bin/python -m pytest -q"

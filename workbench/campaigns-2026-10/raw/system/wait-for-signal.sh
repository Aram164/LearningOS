#!/bin/sh
# Wait until a GLM finish signal appears in signals/, or until a timeout.
# Usage: sh wait-for-signal.sh [max-minutes, default 180]
# Prints "SIGNAL <item id>: <content>" for every pending signal, or
# "TIMEOUT after N minutes". Run it in the background; its exit wakes the
# orchestrator.
D=/Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/glm-campaigns-2026-10-24/signals
MAX=${1:-180}
i=0
while [ "$i" -lt "$MAX" ]; do
  found=0
  for f in "$D"/*.done; do
    [ -e "$f" ] || continue
    found=1
    echo "SIGNAL $(basename "$f" .done): $(cat "$f")"
  done
  [ "$found" -eq 1 ] && exit 0
  sleep 60
  i=$((i + 1))
done
echo "TIMEOUT after $MAX minutes"

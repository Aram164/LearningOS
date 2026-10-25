#!/bin/sh
# wait-for-signal.sh, plus: exit with "UNLOCKED" when the screen goes from
# locked to unlocked. Usage: sh wait-or-unlock.sh [max-minutes, default 180]
D=/Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/glm-campaigns-2026-10-24/signals
MAX=${1:-180}
locked() { ioreg -n Root -d1 -a 2>/dev/null | grep -A1 CGSSessionScreenIsLocked | grep -q '<true/>'; }
was_locked=0; locked && was_locked=1
i=0
while [ "$i" -lt "$MAX" ]; do
  found=0
  for f in "$D"/*.done; do
    [ -e "$f" ] || continue
    found=1
    echo "SIGNAL $(basename "$f" .done): $(cat "$f")"
  done
  [ "$found" -eq 1 ] && exit 0
  if [ "$was_locked" -eq 1 ] && ! locked; then echo "UNLOCKED at $(date +%H:%M)"; exit 0; fi
  locked && was_locked=1
  sleep 60
  i=$((i + 1))
done
echo "TIMEOUT after $MAX minutes"

"""`los semantic`: the query surface over the 23 semantic predicates.

A semantic layer exists to be queried — applications stop re-deriving
meaning from scattered YAML because they can ask. Each predicate already
carries its input names, authority, and prose; this command is the thin
dispatcher over ``evaluate()``. Read-only, JSON out.
"""

from __future__ import annotations

import json
import sys

from learning_os.semantics.predicates import PREDICATES, evaluate


def _coerce(raw: str) -> object:
    """One ``--input k=v`` value. JSON first (numbers, booleans, arrays,
    objects, quoted strings), falling back to the bare string — so
    ``--input scope=current`` and ``--input
    entries='[{"type":"derivation","ref":"note://x"}]'`` both work."""
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return raw


def cmd_semantic(args) -> int:
    """Evaluate one predicate, or list the registry."""
    if args.list:
        print(json.dumps(
            [{"name": name,
              "inputs": list(PREDICATES[name].authoritative_inputs),
              "authority": PREDICATES[name].authority,
              "description": PREDICATES[name].description}
             for name in sorted(PREDICATES)],
            indent=2, sort_keys=True, ensure_ascii=False))
        return 0
    name = args.predicate
    if name not in PREDICATES:
        print(f"los: unknown semantic predicate: {name}", file=sys.stderr)
        print(f"los: see `los semantic --list` for the {len(PREDICATES)} "
              "registered names", file=sys.stderr)
        return 2
    inputs: dict[str, object] = {}
    for item in args.input or []:
        key, separator, value = item.partition("=")
        if not separator or not key.strip():
            print(f"los: --input takes k=v, got {item!r}", file=sys.stderr)
            return 2
        inputs[key.strip()] = _coerce(value)
    try:
        verdict = evaluate(name, **inputs)
    except TypeError as exc:
        print(f"los: malformed inputs for {name}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"predicate": name, "verdict": verdict,
                      "inputs": inputs},
                     indent=2, sort_keys=True, ensure_ascii=False))
    return 0

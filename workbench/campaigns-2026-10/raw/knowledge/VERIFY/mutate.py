"""Plant one deliberate bug per invariant in a disposable campaign clone, run
the probe that claims to guard it, and restore the file with git checkout.

A probe that stays green under its mutation proves nothing; one that goes red
shows the HELD verdict rests on a test with teeth.
"""
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
K1 = HOME / "los-glm-K1-2026-10/repository"
K4 = HOME / "los-glm-K4-2026-10/repository"
UI = HOME / "los-glm-K3-2026-10/obsidian-ui"

MUTATIONS = [
    # (name, clone, file, old, new, test command)
    ("M1 strict-cycle check disabled", K1,
     "tools/learning_os/derive/validation/registries.py",
     'if str(rel.get("type")) not in PREREQUISITE_RELATIONS:', "if True:",
     [".venv/bin/python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
      "tests/test_k1_4_prereq_cycles.py"]),
    ("M2 canvas draws dependent -> prerequisite", K1,
     "tools/learning_os/derive/projection/canvas.py",
     '"fromNode": b if strict else a,\n        "fromSide": "right" if strict else "left",\n        "toNode": a if strict else b,',
     '"fromNode": a,\n        "fromSide": "right" if strict else "left",\n        "toNode": b,',
     [".venv/bin/python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
      "tests/test_k1_5_canvas_direction.py"]),
    ("M3 unlicensed node `concepts` field licenses an edge", K1,
     "tools/learning_os/derive/projection/projection/atlas.py",
     'for concept_id in node.get("concept_ids") or ():',
     'for concept_id in (node.get("concept_ids") or node.get("concepts") or ()):',
     [".venv/bin/python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
      "tests/test_k1_2_no_inferred_edges.py"]),
    ("M4 old row matched by `from` only (stale edit lands)", K4,
     "tools/learning_os/app/handlers/atlas.py",
     'for i, row in enumerate(data["relations"]) if row == operation["old"]]',
     'for i, row in enumerate(data["relations"]) if row["from"] == operation["old"]["from"]]',
     [".venv/bin/python", "-m", "pytest", "-q", "-p", "no:cacheprovider",
      "tests/test_k4_1_stale_old_row.py"]),
    ("M5 UI marks every question target present", UI,
     "src/features/atlas/questions.ts",
     "function present(graph: AtlasGraph, target: AtlasQuestionTarget): boolean {\n  return target.kind",
     "function present(graph: AtlasGraph, target: AtlasQuestionTarget): boolean {\n  return true || target.kind",
     ["node", "tests/k3-questions.js"]),
    ("M6 UI old row leaks a projection null", UI,
     "src/features/atlas/relation-editor.ts",
     "...(edge.context ? { context: edge.context } : {}),",
     "context: edge.context ?? null,",
     ["node", "tests/k3-authoring.js"]),
]


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


failures = 0
for name, clone, rel, old, new, test in MUTATIONS:
    path = clone / rel
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        print(f"{name}: SKIPPED, anchor found {text.count(old)} times")
        failures += 1
        continue
    try:
        path.write_text(text.replace(old, new), encoding="utf-8")
        result = run(test, clone)
        verdict = "RED (probe caught it)" if result.returncode != 0 else "GREEN (probe MISSED it)"
        if result.returncode == 0:
            failures += 1
        tail = (result.stdout + result.stderr).strip().splitlines()
        print(f"{name}: {verdict}")
        for line in [l for l in tail if "assert" in l.lower() or "failed" in l.lower()][:3]:
            print(f"    {line[:160]}")
    finally:
        run(["git", "checkout", "--", rel], clone)
        assert path.read_text(encoding="utf-8") == text, f"restore failed: {path}"

for clone in (K1, K4, UI):
    dirty = [l for l in run(["git", "status", "--porcelain"], clone).stdout.splitlines()
             if not l.startswith("??") and "shard-manifest" not in l and "group_map" not in l]
    print(f"restored {clone.name if clone != UI else 'obsidian-ui'} ({clone.parent.name}): "
          f"{'clean' if not dirty else dirty}")
sys.exit(1 if failures else 0)

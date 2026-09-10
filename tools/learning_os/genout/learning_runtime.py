import json

from ..learning_runtime import collect_requirements
from ..loader import Repo


def build_learning_requirements_json(repo: Repo, generated_at: str) -> str:
    requirements = _collect_requirements(repo)
    output = {
        "_generated": {
            "generated_at": generated_at,
            "warning": "GENERATED file - do not edit; rebuilt by python tools/generate.py"
        },
        "requirements": requirements
    }
    return json.dumps(output, separators=(",", ":"), sort_keys=True, ensure_ascii=False)

def build_learning_requirements_md(repo: Repo) -> str:
    requirements = _collect_requirements(repo)
    lines = ["# Learning Requirements (Runtime Projection)\n", "> **WARNING:** This file is GENERATED. Do not edit directly.\n"]
    lines.append("Each requirement is compiled from its canonical study-map stage; stages without a runtime_target contribute none.")
    if not requirements:
        lines.append("No learning requirements found.")
    for req in requirements:
        lines.append(f"## {req.get('id', 'Unknown')}")
        namespace = "unit knowledge-map entry" if req["concept"].startswith("knowledge-") else "global concept"
        lines.append(f"- **Target**: `{req['concept']}` ({namespace})")
        cap = req.get('capability', {})
        lines.append(f"- **Capability**: {cap.get('kind')} ({', '.join(cap.get('operands', []))})")
        lines.append(f"- **Conditions**: {', '.join(req.get('conditions', []))}")
        lines.append(f"- **Evidence Spec**: {', '.join(req.get('evidence_spec', []))}")
        source = req.get('source_stage', {})
        lines.append(f"- **Source**: {source.get('module_id')} > {source.get('unit_id')} > {source.get('stage_id')}")
        lines.append("\n---\n")
    return "\n".join(lines) + "\n"

def _collect_requirements(repo: Repo) -> list[dict]:
    return collect_requirements(repo)

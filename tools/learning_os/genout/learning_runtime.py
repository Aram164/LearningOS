import json

import yaml

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
    lines = ["# Learning Requirements (Phase 1 Projection)\n", "> **WARNING:** This file is GENERATED. Do not edit directly.\n"]
    if not requirements:
        lines.append("No learning requirements found.")
    for req in requirements:
        lines.append(f"## {req.get('id', 'Unknown')}")
        lines.append(f"- **Concept**: `{req.get('concept')}`")
        cap = req.get('capability', {})
        lines.append(f"- **Capability**: {cap.get('kind')} ({', '.join(cap.get('operands', []))})")
        lines.append(f"- **Conditions**: {', '.join(req.get('conditions', []))}")
        lines.append(f"- **Evidence Spec**: {', '.join(req.get('evidence_spec', []))}")
        source = req.get('source_stage', {})
        lines.append(f"- **Source**: {source.get('module_id')} > {source.get('unit_id')} > {source.get('stage_id')}")
        lines.append("\n---\n")
    return "\n".join(lines) + "\n"

def _collect_requirements(repo: Repo) -> list[dict]:
    requirements = []
    curriculum_dir = repo.root / "curriculum" / "modules"
    for req_file in curriculum_dir.rglob("stages/*/requirements.yaml"):
        try:
            with open(req_file) as f:
                data = yaml.safe_load(f)
                if isinstance(data, list):
                    requirements.extend(data)
                elif isinstance(data, dict):
                    requirements.append(data)
        except Exception:
            pass
    return sorted(requirements, key=lambda x: x.get("id", ""))

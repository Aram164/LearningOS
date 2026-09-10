import json
from datetime import datetime

from ..learning_runtime import collect_requirements, read_observations, requirement_fingerprint
from ..loader import Repo


def interpret_observations(observations: list[dict], requirement: dict | None = None) -> dict:
    """Credit only distinct unaided activities meeting the target's evidence contract."""
    ordered = sorted(observations, key=lambda obs: (datetime.fromisoformat(obs["timestamp"]), obs["id"]))
    evidence_ids = [obs["id"] for obs in ordered]
    conditions = set((requirement or {}).get("conditions", []))
    evidence_spec = set((requirement or {}).get("evidence_spec", []))
    requirement_hash = requirement_fingerprint(requirement) if requirement else None
    superseded = {obs["supersedes"] for obs in ordered if obs.get("supersedes")}
    successes = set()
    qualified = []
    had_success = False
    recent_failure = False
    for obs in ordered:
        if obs["id"] in superseded:
            continue
        matches = (bool(evidence_spec) and obs.get("requirement_sha256") == requirement_hash
                   and conditions <= set(obs.get("conditions", [])))
        unaided = obs.get("assistance", "").strip().lower() == "none"
        if matches and obs["result"] in {"incorrect", "partial"}:
            recent_failure = True
            successes.clear()
            qualified.clear()
        elif (matches and unaided and obs["result"] == "correct"
              and evidence_spec <= set(obs.get("evidence_tags", []))):
            successes.add(obs["activity"])
            qualified.append(obs["id"])
            had_success = True
            if len(successes) >= 2:
                recent_failure = False
    status = "unseen" if not ordered else "uncertain"
    if len(successes) >= 2 and not recent_failure:
        status = "demonstrated"
    elif recent_failure and had_success:
        status = "fragile"
    return {
        "status": status,
        "evidence_ids": evidence_ids,
        "evidence_basis": [{"id": obs["id"], **obs.get("origin", {})} for obs in ordered],
        "qualifying_evidence_ids": qualified,
        "superseded_evidence_ids": sorted(superseded),
        "requirement_sha256": requirement_hash,
        "last_observed_at": ordered[-1]["timestamp"] if ordered else None,
        "derivation": "target-conditions-and-evidence-v1",
        "reason": ("two distinct unaided activities meet the target conditions and evidence specification"
                   if status == "demonstrated" else "insufficient or conflicting target-specific evidence"),
    }

def build_learner_interpretations_json(repo: Repo, generated_at: str) -> str:
    interpretations = _collect_and_interpret(repo)
    output = {
        "_generated": {
            "generated_at": generated_at,
            "warning": "GENERATED file - do not edit; rebuilt by python tools/generate.py"
        },
        "interpretations": interpretations
    }
    return json.dumps(output, separators=(",", ":"), sort_keys=True, ensure_ascii=False)

def build_learner_interpretations_md(repo: Repo) -> str:
    interpretations = _collect_and_interpret(repo)
    lines = ["# Learner Interpretations (Phase 3 Projection)\n", "> **WARNING:** This file is GENERATED. Do not edit directly.\n"]
    if not interpretations:
        lines.append("No interpretations available.")
    
    for req_id, data in sorted(interpretations.items()):
        lines.append(f"## {req_id}")
        lines.append(f"- **Status**: `{data['status']}`")
        if "blockers" in data:
            lines.append(f"- **Blockers**: {', '.join(data['blockers'])}")
        lines.append(f"- **Reason**: {data['reason']}")
        lines.append(f"- **Requirement definition**: `{data['requirement_sha256']}`")
        qualified = set(data["qualifying_evidence_ids"])
        superseded = set(data["superseded_evidence_ids"])
        for basis in data["evidence_basis"]:
            label = "corrected" if basis["id"] in superseded else "qualifying" if basis["id"] in qualified else "not qualifying"
            lines.append(f"- **Evidence**: `{basis['id']}` — {label}; `{basis.get('path', '')}:{basis.get('line', '')}`")
        lines.append("\n---\n")
    return "\n".join(lines) + "\n"

def _collect_and_interpret(repo: Repo) -> dict[str, dict]:
    requirements = collect_requirements(repo)
    observations = read_observations(repo, requirements)
    return {
        req["id"]: interpret_observations(
            [obs for obs in observations if obs["requirement"] == req["id"]], req
        )
        for req in requirements
    }

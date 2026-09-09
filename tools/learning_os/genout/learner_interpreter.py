import json
from pathlib import Path
from ..loader import Repo

def interpret_observations(observations: list[dict]) -> dict:
    if not observations:
        return {"status": "unseen", "evidence_ids": []}
    
    # Sort chronologically
    sorted_obs = sorted(observations, key=lambda x: x.get("timestamp", ""))
    evidence_ids = [obs.get("timestamp") for obs in sorted_obs]
    
    # Evaluate rules
    correct_unaided = 0
    incorrect_recent = 0
    has_assisted = False
    has_incorrect = False
    
    for obs in sorted_obs:
        is_correct = (obs.get("result") == "correct")
        is_assisted = bool(obs.get("assistance"))
        
        if is_correct and not is_assisted:
            correct_unaided += 1
            incorrect_recent = 0
        elif is_correct and is_assisted:
            has_assisted = True
            incorrect_recent = 0
        elif not is_correct:
            has_incorrect = True
            incorrect_recent += 1

    status = "unseen"
    if correct_unaided >= 2 and incorrect_recent == 0:
        status = "demonstrated"
    elif incorrect_recent > 0 and correct_unaided > 0:
        status = "fragile"
    elif has_assisted or has_incorrect or correct_unaided == 1:
        status = "uncertain"

    # Optional blocker logic (placeholder for actual prerequisites checking)
    blockers = []
    
    result = {
        "status": status,
        "evidence_ids": evidence_ids
    }
    if blockers:
        result["blockers"] = blockers
    return result

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
        lines.append(f"- **Evidence Points**: {len(data['evidence_ids'])}")
        lines.append("\n---\n")
    return "\n".join(lines) + "\n"

def _collect_and_interpret(repo: Repo) -> dict[str, dict]:
    # Group observations by requirement
    req_observations = {}
    for ws_id, ws in repo.workspaces.items():
        obs_file = ws.path.parent / "observations.jsonl"
        if obs_file.exists():
            with open(obs_file, "r") as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        obs = json.loads(line)
                        req_id = obs.get("requirement")
                        if req_id:
                            req_observations.setdefault(req_id, []).append(obs)
                    except Exception:
                        pass
    
    interpretations = {}
    for req_id, obs_list in req_observations.items():
        interpretations[req_id] = interpret_observations(obs_list)
    
    return interpretations

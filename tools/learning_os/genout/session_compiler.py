import json
import logging
from ..loader import Repo

def _compile_sessions(repo: Repo) -> list[dict]:
    req_path = repo.root / "generated" / "learning-requirements.json"
    interp_path = repo.root / "generated" / "learner-interpretations.json"
    
    if not req_path.is_file() or not interp_path.is_file():
        return []
        
    reqs = json.loads(req_path.read_text())["requirements"]
    interps = json.loads(interp_path.read_text())["interpretations"]
    
    sessions = []
    
    for req in reqs:
        req_id = req["id"]
        status = interps.get(req_id, {}).get("status", "unseen")
        source = req.get("source_stage", {})
        
        unit_id = source.get("unit_id")
        stage_id = source.get("stage_id")
        
        study_map_id = unit_id.replace("unit-", "study-map-")
        study_map = repo.study_maps.get(study_map_id)
        if not study_map:
            continue
            
        stage_data = next((s for s in study_map.data.get("stages", []) if s["id"] == stage_id), None)
        if not stage_data:
            continue
            
        resources = stage_data.get("resources", [])
        
        # Build plan!
        steps = []
        rejected = []
        
        if status == "demonstrated":
            for r in resources:
                rid = r.get("id") or r.get("route_id") or r.get("material_ref", {}).get("route_id") or "unknown"
                rejected.append({"resource_id": rid, "reason": "target already demonstrated"})
        else:
            interventions = [r for r in resources if r.get("affordance") == "intervention"]
            evidences = [r for r in resources if r.get("affordance") == "evidence"]
            mixed = [r for r in resources if r.get("affordance") == "mixed"]
            
            # Simple strategy
            if status in ("unseen", "uncertain"):
                if interventions:
                    r = interventions[0]
                    rid = r.get("id") or r.get("route_id") or r.get("material_ref", {}).get("route_id") or "unknown"
                    steps.append({"resource_id": rid, "role": "explanation", "reason": "closes current evidence gap from unseen/uncertain"})
                if evidences:
                    r = evidences[0]
                    rid = r.get("id") or r.get("route_id") or r.get("material_ref", {}).get("route_id") or "unknown"
                    steps.append({"resource_id": rid, "role": "independent evidence", "reason": "ensures intervention is followed by evidence"})
                
                # reject rest
                for r in resources:
                    rid = r.get("id") or r.get("route_id") or r.get("material_ref", {}).get("route_id") or "unknown"
                    if not any(s["resource_id"] == rid for s in steps):
                        rejected.append({"resource_id": rid, "reason": "avoids same-role redundancy or simpler plan preferred"})
                        
            elif status == "fragile":
                if mixed:
                    r = mixed[0]
                    rid = r.get("id") or r.get("route_id") or r.get("material_ref", {}).get("route_id") or "unknown"
                    steps.append({"resource_id": rid, "role": "guided practice", "reason": "misconception contrast / guided practice for fragile"})
                if evidences:
                    r = evidences[0]
                    rid = r.get("id") or r.get("route_id") or r.get("material_ref", {}).get("route_id") or "unknown"
                    steps.append({"resource_id": rid, "role": "evidence task", "reason": "verify repair of fragile state"})
                
                # reject rest
                for r in resources:
                    rid = r.get("id") or r.get("route_id") or r.get("material_ref", {}).get("route_id") or "unknown"
                    if not any(s["resource_id"] == rid for s in steps):
                        rejected.append({"resource_id": rid, "reason": "avoids same-role redundancy or simpler plan preferred"})
        
        session = {
            "target_requirement_id": req_id,
            "current_status": status,
            "steps": steps,
            "rejected_alternatives": rejected,
            "assumptions": ["time budget is unconstrained for this prototype"],
            "replan_conditions": ["evidence fails to be demonstrated", "learner aborts intervention"]
        }
        sessions.append(session)
        
    return sessions

def build_compiled_sessions_json(repo: Repo, generated_at: str) -> str:
    sessions = _compile_sessions(repo)
    output = {
        "_generated": {
            "generated_at": generated_at,
            "warning": "GENERATED file - do not edit; rebuilt by python tools/generate.py"
        },
        "sessions": sessions
    }
    return json.dumps(output, separators=(",", ":"), sort_keys=True, ensure_ascii=False)

def build_compiled_sessions_md(repo: Repo) -> str:
    sessions = _compile_sessions(repo)
    lines = ["# Compiled Sessions (Phase 5 Projection)\n", "> **WARNING:** This file is GENERATED. Do not edit directly.\n"]
    if not sessions:
        lines.append("No sessions compiled.")
    for s in sessions:
        lines.append(f"## Target: `{s['target_requirement_id']}`")
        lines.append(f"**Current Status:** {s['current_status']}")
        lines.append("\n### Steps")
        if not s["steps"]:
            lines.append("*(No steps needed)*")
        for step in s["steps"]:
            lines.append(f"- Resource `{step['resource_id']}` (Role: *{step['role']}*) — {step['reason']}")
        
        lines.append("\n### Rejected Alternatives")
        if not s["rejected_alternatives"]:
            lines.append("*(None)*")
        for r in s["rejected_alternatives"]:
            lines.append(f"- `{r['resource_id']}`: {r['reason']}")
            
        lines.append("\n### Assumptions")
        for a in s["assumptions"]:
            lines.append(f"- {a}")
            
        lines.append("\n### Replan Conditions")
        for r in s["replan_conditions"]:
            lines.append(f"- {r}")
            
        lines.append("\n---\n")
    return "\n".join(lines) + "\n"

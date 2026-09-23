"""Evidence-bound ability map shared by Library, Session, and Atlas reads.

Ability identities and reviewed preparation/transfer live in knowledge. Attempts
remain append-only learner work. This module derives answers; it owns no cache or
second copy of either fact. Concept overlap is discovery only.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from .learning_runtime import RuntimeInputError, runtime_path
from .loader import Repo
from .material_refs import matching_routes, unit_routes


def ability_fingerprint(ability: dict) -> str:
    # Evidence is bound to what the learner was asked to show. Display labels,
    # review metadata, and preparation routes may change without changing that
    # claim. Condition and criterion order does not change their meaning.
    evidence_definition = {
        "id": ability["id"],
        "claim": ability["claim"],
        "conditions": sorted(ability["conditions"]),
        "evidence_spec": sorted(ability["evidence_spec"]),
    }
    payload = json.dumps(evidence_definition, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def bridge_source_freshness(repo: Repo, bridge: dict) -> dict:
    """Observe the exact reviewed source bytes before using a transfer edge."""
    if bridge.get("review", {}).get("state") != "reviewed":
        return {"status": "not-reviewed"}
    source = bridge.get("source")
    recorded = bridge.get("source_sha256")
    if not isinstance(source, str) or not isinstance(recorded, str):
        return {"status": "unavailable"}
    relative = Path(source.split("#", 1)[0])
    try:
        path = runtime_path(repo.root, repo.root / relative)
        if not path.is_file():
            return {"status": "unavailable"}
        observed = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except (OSError, RuntimeInputError):
        return {"status": "unavailable"}
    return {"status": "current" if observed == recorded else "stale",
            "observed_sha256": observed}


def validate_ability_registry(repo: Repo) -> list[str]:
    """Check semantic references as well as the registry's JSON shape."""
    issues: list[str] = []
    known = set(repo.abilities)
    for ability in repo.abilities.values():
        aid = ability["id"]
        for concept in ability.get("concept_ids", []):
            if concept not in repo.concepts:
                issues.append(f"{aid}: unknown concept {concept}")
        for module in ability.get("module_ids", []):
            if module not in repo.modules:
                issues.append(f"{aid}: unknown module {module}")
        review = ability.get("review", {})
        if review.get("state") == "reviewed" and not (review.get("reviewed_by") and review.get("reviewed_on")):
            issues.append(f"{aid}: reviewed ability needs reviewer and date")
        for route in ability.get("preparation_routes", []):
            for prerequisite in route.get("all_of", []):
                if prerequisite not in known or prerequisite == aid:
                    issues.append(f"{aid}: invalid prerequisite {prerequisite}")
    for bridge in repo.ability_bridges:
        if not isinstance(bridge, dict):
            issues.append("ability bridge must be an object")
            continue
        left, right = bridge.get("from"), bridge.get("to")
        if left not in known or right not in known or left == right:
            issues.append(f"invalid ability bridge {left} -> {right}")
            continue
        review = bridge.get("review", {})
        if review.get("state") == "reviewed" and not (review.get("reviewed_by") and review.get("reviewed_on")):
            issues.append(f"{left} -> {right}: reviewed bridge needs reviewer and date")
        if review.get("state") == "reviewed" and not bridge.get("source_sha256"):
            issues.append(f"{left} -> {right}: reviewed bridge needs a source digest")
        if bridge.get("kind") == "equivalence" and review.get("state") == "reviewed":
            required = set(repo.abilities[left]["conditions"]) | set(repo.abilities[right]["conditions"])
            if not required.issubset(bridge.get("conditions", [])):
                issues.append(f"{left} -> {right}: equivalence omits an ability condition")
    # A preparation cycle would make every ability in it unreachable from
    # direct evidence. Alternatives do not license cycles either.
    edges = {aid: {p for route in ability.get("preparation_routes", [])
                   for p in route.get("all_of", [])} for aid, ability in repo.abilities.items()}
    active: set[str] = set()
    done: set[str] = set()

    def visit(aid: str) -> None:
        if aid in active:
            issues.append(f"preparation cycle through {aid}")
            return
        if aid in done or aid not in edges:
            return
        active.add(aid)
        for item in edges[aid]:
            visit(item)
        active.remove(aid)
        done.add(aid)

    for aid in edges:
        visit(aid)
    for study_map in repo.study_maps.values():
        for stage in study_map.data.get("stages", []):
            for aid in stage.get("ability_ids", []):
                if aid not in known:
                    issues.append(f"{stage.get('id')}: unknown ability {aid}")
    return issues


def read_ability_observations(repo: Repo) -> list[dict]:
    """Read exact workspace-owned evidence, preserving corrections and history."""
    schema = json.loads((repo.root / "system/schema/ability-observation.schema.json").read_text())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    rows: list[dict] = []
    seen: set[str] = set()
    corrected: set[str] = set()
    for workspace in sorted(repo.workspaces.values(), key=lambda row: row.id):
        path = runtime_path(repo.root, workspace.path.parent / "ability-observations.jsonl")
        if not path.exists():
            continue
        rel = path.relative_to(repo.root).as_posix()
        for line_number, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeInputError(f"{rel}:{line_number}: invalid JSON: {exc}") from exc
            errors = sorted(validator.iter_errors(row), key=str)
            if errors:
                raise RuntimeInputError(f"{rel}:{line_number}: {errors[0].message}")
            aid = row["ability_id"]
            if aid not in repo.abilities:
                raise RuntimeInputError(f"{rel}:{line_number}: unknown ability {aid}")
            identity = row["id"]
            if identity in seen:
                raise RuntimeInputError(f"duplicate ability observation {identity}")
            if set(row.get("conditions", [])) & set(row.get("conditions_not_met", [])):
                raise RuntimeInputError(f"{rel}:{line_number}: contradictory condition flags")
            if row.get("supersedes"):
                prior = next((item for item in rows if item["id"] == row["supersedes"]), None)
                if (prior is None or prior["ability_id"] != aid or prior["origin"]["path"] != rel
                        or prior["id"] in corrected):
                    raise RuntimeInputError(f"{rel}:{line_number}: invalid correction target")
                corrected.add(prior["id"])
            seen.add(identity)
            rows.append({**row, "origin": {"path": rel, "line": line_number,
                                            "workspace_id": workspace.id}})
    return rows


def read_ability_candidates(repo: Repo) -> list[dict]:
    """Read tentative connections without promoting them to reviewed bridges."""
    path = runtime_path(repo.root, repo.root / "knowledge/ability-candidates.jsonl")
    if not path.exists():
        return []
    schema = json.loads((repo.root / "system/schema/ability-candidate.schema.json").read_text())
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    rows: list[dict] = []
    seen: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RuntimeInputError(f"knowledge/ability-candidates.jsonl:{line_number}: invalid JSON") from exc
        errors = sorted(validator.iter_errors(row), key=str)
        if errors:
            raise RuntimeInputError(f"knowledge/ability-candidates.jsonl:{line_number}: {errors[0].message}")
        if row["id"] in seen or row["from"] == row["to"]:
            raise RuntimeInputError(f"knowledge/ability-candidates.jsonl:{line_number}: invalid candidate identity")
        if row["from"] not in repo.abilities or row["to"] not in repo.abilities:
            raise RuntimeInputError(f"knowledge/ability-candidates.jsonl:{line_number}: unknown ability")
        seen.add(row["id"])
        rows.append({**row, "origin": {"path": "knowledge/ability-candidates.jsonl",
                                        "line": line_number}})
    return rows


def _direct_status(ability: dict, observations: list[dict]) -> tuple[str, list[dict], list[str]]:
    aid = ability["id"]
    current_hash = ability_fingerprint(ability)
    corrections = {row["supersedes"] for row in observations if row.get("supersedes")}
    history = [row for row in observations if row["ability_id"] == aid]
    active = [row for row in history if row["id"] not in corrections]
    comparable = [row for row in active if row["ability_sha256"] == current_hash
             and row["confirmed_by"] == "learner"
             and set(ability["conditions"]).issubset(row.get("conditions", []))
             and not set(ability["conditions"]) & set(row.get("conditions_not_met", []))]
    valid = [row for row in comparable if row["assistance"].strip().lower() == "none"
             and (row["result"] != "correct" or
                  set(ability["evidence_spec"]).issubset(row["evidence_tags"]))]
    reasons: list[str] = []
    if any(row["ability_sha256"] != current_hash for row in active):
        reasons.append("ability definition changed since recorded work")
    if any(row["confirmed_by"] != "learner" for row in active):
        reasons.append("unconfirmed work is excluded")
    if any(row["assistance"].strip().lower() != "none" for row in active):
        reasons.append("assisted work does not establish independent support")
    if any(row["result"] == "correct" and
           not set(ability["evidence_spec"]).issubset(row["evidence_tags"])
           for row in comparable):
        reasons.append("worked attempt does not cover every reviewed evidence criterion")
    if not valid:
        reasons.append("no current confirmed work under the stated conditions")
        return "uncertain", history, reasons
    latest = sorted(valid, key=lambda row: (row["timestamp"], row["id"]))[-1]
    if latest["result"] == "correct":
        if any(row["result"] in {"incorrect", "partial"} for row in comparable
               if (row["timestamp"], row["id"]) > (latest["timestamp"], latest["id"])):
            return "uncertain", history, ["conflicting later work"]
        return "supported", history, ["current confirmed worked attempt"]
    return "uncertain", history, ["latest comparable attempt is partial or incorrect"]


def ability_context(repo: Repo, *, focus: str | None = None, limit: int = 12) -> dict:
    """Small global horizon or one expanded ability, with explicit reasons."""
    observations = read_ability_observations(repo)
    candidates = read_ability_candidates(repo)
    bridge_freshness = {id(bridge): bridge_source_freshness(repo, bridge)
                        for bridge in repo.ability_bridges if isinstance(bridge, dict)}
    direct = {aid: _direct_status(ability, observations)
              for aid, ability in repo.abilities.items()}
    if focus is not None and focus not in repo.abilities:
        return {"state": "unmapped", "focus": focus,
                "reason": "no reviewed ability maps this identity"}

    resolved: dict[str, dict] = {}
    building: set[str] = set()

    def state(aid: str) -> dict:
        if aid in resolved:
            return resolved[aid]
        if aid in building:
            return {"state": "unmapped"}
        building.add(aid)
        ability = repo.abilities[aid]
        retired = ability.get("lifecycle") == "retired"
        reviewed = ability["review"]["state"] == "reviewed" and not retired
        status, history, reasons = direct[aid]
        if retired:
            status, reasons = "unmapped", ["ability identity retired; historical work retained"]
        elif not reviewed:
            status, reasons = "unmapped", ["ability is a tentative candidate"]
        transfer = []
        if reviewed and status != "supported" and not history:
            for bridge in repo.ability_bridges:
                if (not isinstance(bridge, dict) or bridge["kind"] != "equivalence"
                        or bridge["review"]["state"] != "reviewed"
                        or aid not in (bridge["from"], bridge["to"])):
                    continue
                if bridge_freshness[id(bridge)]["status"] != "current":
                    continue
                other = bridge["to"] if bridge["from"] == aid else bridge["from"]
                if (other not in direct or repo.abilities[other]["review"]["state"] != "reviewed"
                        or repo.abilities[other].get("lifecycle") == "retired"):
                    continue
                bridge_conditions = set(bridge["conditions"])
                if not (set(ability["conditions"]) | set(repo.abilities[other]["conditions"])) <= bridge_conditions:
                    continue
                if direct[other][0] != "supported":
                    continue
                corrections = {row["supersedes"] for row in direct[other][1]
                               if row.get("supersedes")}
                source_rows = [row for row in direct[other][1] if row["result"] == "correct"
                               and row["id"] not in corrections
                               and row["assistance"].strip().lower() == "none"
                               and row["confirmed_by"] == "learner"
                               and set(repo.abilities[other]["evidence_spec"]).issubset(row["evidence_tags"])
                               and row["ability_sha256"] == ability_fingerprint(repo.abilities[other])]
                if any(set(bridge["conditions"]).issubset(row.get("conditions", [])) for row in source_rows):
                    status = "supported"
                    transfer.append({"from": other, "source": bridge["source"],
                                     "carries": bridge["carries"], "changes": bridge["changes"]})
                    reasons = [f"reviewed equivalence from {other}"]
        routes = []
        if reviewed:
            for route in ability.get("preparation_routes", []):
                prerequisite_states = {p: state(p)["state"] for p in route["all_of"] if p in direct}
                missing = sorted(p for p, s in prerequisite_states.items() if s != "supported")
                routes.append({"reason": route["reason"], "source": route.get("source"),
                               "supported": sorted(p for p, s in prerequisite_states.items() if s == "supported"),
                               "missing_or_uncertain": missing,
                               "remaining_work": missing or [f"independent worked attempt for {aid}"]})
            if status == "uncertain" and not history and routes and any(route["supported"] for route in routes):
                status = "nearby"
                reasons.append("reviewed preparation route has named remaining work")
        result = {"id": aid, "title": ability["title"], "state": status,
                  "lifecycle": ability.get("lifecycle", "active"),
                  "reasons": reasons, "concept_ids": ability["concept_ids"],
                  "module_ids": ability.get("module_ids", []), "preparation_routes": routes,
                  "transfer": transfer,
                  "evidence": history if focus == aid else [{"id": row["id"], "result": row["result"],
                                                                "work_ref": row["work_ref"]} for row in history[-2:]]}
        building.remove(aid)
        resolved[aid] = result
        return result

    if focus:
        item = state(focus)
        related = [bridge for bridge in repo.ability_bridges
                   if isinstance(bridge, dict) and focus in (bridge.get("from"), bridge.get("to"))]
        encounters = []
        related_ids = {p for route in repo.abilities[focus].get("preparation_routes", [])
                       for p in route["all_of"]}
        related_ids.update(bridge["to"] if bridge["from"] == focus else bridge["from"]
                           for bridge in related)
        related_ids.discard(focus)
        related_encounters = []
        for study_map in repo.study_maps.values():
            for stage in study_map.data.get("stages", []):
                hit = focus in stage.get("ability_ids", [])
                related_hit = related_ids.intersection(stage.get("ability_ids", []))
                if not hit and not related_hit:
                    continue
                available_routes = unit_routes(
                    repo.module_source_maps.get(study_map.module_id, {}),
                    study_map.module_id, study_map.unit_id,
                )
                material_rows = []
                for resource in stage.get("resources", []):
                    if not isinstance(resource, dict):
                        continue
                    matches = matching_routes(resource, available_routes)
                    material_rows.append({
                        "route_id": matches[0]["id"] if len(matches) == 1 else None,
                        "source_id": resource.get("source_id"),
                        "locator": resource.get("locator"),
                        "match_state": "exact" if len(matches) == 1 else "unmapped",
                    })
                encounter = {"module_id": study_map.module_id,
                             "unit_id": study_map.unit_id,
                             "study_map_id": study_map.id,
                             "stage_id": stage["id"],
                             "title": stage.get("title"),
                             "objective": stage.get("objective"),
                             "status": stage.get("status"),
                             "materials": material_rows}
                if hit:
                    encounters.append(encounter)
                if related_hit:
                    route_ids = sorted({row["route_id"] for row in material_rows
                                        if row["route_id"]})
                    related_encounters.append({
                        "module_id": study_map.module_id,
                        "unit_id": study_map.unit_id,
                        "stage_id": stage["id"],
                        "title": stage.get("title"),
                        "objective": stage.get("objective"),
                        "ability_ids": sorted(related_hit),
                        "route_ids": route_ids[:12],
                        "route_total": len(route_ids),
                        "routes_truncated": len(route_ids) > 12,
                    })
        shared_tags = sorted(other_id for other_id, other in repo.abilities.items()
                             if other_id != focus and
                             set(other["concept_ids"]) & set(repo.abilities[focus]["concept_ids"]))
        return {"focus": focus, "ability": {**repo.abilities[focus], **item},
                "bridges": [{**bridge, "source_freshness": bridge_freshness[id(bridge)]}
                            for bridge in related], "encounters": encounters,
                "related_encounters": related_encounters[:20],
                "related_encounters_total": len(related_encounters),
                "candidate_connections": [row for row in candidates
                                          if focus in (row["from"], row["to"])][-20:],
                "shared_concept_candidates": shared_tags,
                "expand": {"material": "material-context QUERY",
                                               "stage": "inspect STAGE_ID"}}
    rows = [state(aid) for aid in sorted(repo.abilities)]
    priority = {"supported": 0, "nearby": 1, "uncertain": 2, "unmapped": 3}
    rows.sort(key=lambda row: (priority[row["state"]], row["id"]))
    listed = {row["id"] for row in rows[:limit]}
    # The horizon's own edges: every reviewed or candidate bridge, and every
    # tentative connection, whose two ends are both on the listed page. An
    # interface draws the map from this one read instead of expanding every
    # ability, and an edge to an ability beyond the page stays with that
    # ability's focused expansion rather than dangling here.
    horizon_bridges = [{**bridge, "source_freshness": bridge_freshness[id(bridge)]}
                       for bridge in repo.ability_bridges
                       if isinstance(bridge, dict)
                       and bridge.get("from") in listed and bridge.get("to") in listed]
    horizon_candidates = [row for row in candidates
                          if row["from"] in listed and row["to"] in listed]
    return {"abilities": rows[:limit], "total": len(rows),
            "bridges": horizon_bridges,
            "candidate_connections": horizon_candidates[-20:],
            "candidate_connection_count": len(candidates),
            "truncated": len(rows) > limit,
            "expand": "ability-context ABILITY_ID"}

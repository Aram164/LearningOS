"""Bounded agent-plan presentation and pure step expansion."""
from __future__ import annotations

import fnmatch
import json
import shlex
from typing import TypedDict, cast

from learning_os.domain.agent_plans import PlanIndex, PlanStep, PlanStepError, SummarySpec
from learning_os.domain.codes import INVALID_STEP_OUTPUT, SUMMARY_BUDGET_TOO_SMALL


def _json(value: object) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    except (ValueError, TypeError) as exc:
        raise PlanStepError("output must be finite JSON", INVALID_STEP_OUTPUT) from exc

def resolve_use(use: str, index: PlanIndex) -> str:
    """Map a task id, operation id, or verb to the canonical CLI verb."""
    if use in index.get("verbs", []):
        return use
    operation_to_verb = {op: verb for verb, op in index.get("verb_to_operation", {}).items()}
    if use in operation_to_verb:
        return operation_to_verb[use]
    if use in index.get("task_to_use", {}):
        return index["task_to_use"][use]
    raise PlanStepError(f"unknown task, capability, or verb: {use}")

def _extract(payload: object, dotted: str) -> tuple[object, bool]:
    node = payload
    for part in dotted.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        else:
            return None, False
    return node, True

def _place(target: dict[str, object], dotted: str, value: object) -> None:
    parts = dotted.split(".")
    node = target
    for part in parts[:-1]:
        existing = node.setdefault(part, {})
        if not isinstance(existing, dict):
            raise PlanStepError("summary fields must not overlap")
        node = existing
    node[parts[-1]] = value

def _cap(node: object, max_items: int) -> object:
    if isinstance(node, dict):
        return {key: _cap(value, max_items) for key, value in node.items()}
    if isinstance(node, list):
        capped = [_cap(value, max_items) for value in node[:max_items]]
        if len(node) > max_items:
            capped.append({"_omitted": len(node) - max_items})
        return capped
    if isinstance(node, str) and len(node) > 240:
        return node[:240] + "…"
    return node

def summarize(payload: object, *, fields: list[str] | None = None, max_items: int = 5, max_bytes: int = 2000) -> str:
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or max_bytes < 64:
        raise PlanStepError("summary.max_bytes must be an integer >= 64")
    if not isinstance(max_items, int) or isinstance(max_items, bool) or max_items < 1:
        raise PlanStepError("summary.max_items must be a positive integer")
    missing = []
    if fields:
        picked: dict[str, object] = {}
        for dotted in fields:
            value, found = _extract(payload, dotted)
            if found:
                _place(picked, dotted, value)
            else:
                missing.append(dotted)
        if missing:
            picked["_missing_fields"] = missing
        encoded = _json(picked)
    elif isinstance(payload, str):
        encoded = _json({"text": payload})
    else:
        encoded = _json(_cap(payload, max_items))
    size = len(encoded.encode("utf-8"))
    if size <= max_bytes:
        return encoded
    metadata = {"_truncated_bytes": size, **({"_missing_fields": missing} if missing else {})}
    if len(_json({**metadata, "preview": ""}).encode("utf-8")) > max_bytes:
        raise PlanStepError("budget cannot hold missing-field metadata; increase max_bytes", SUMMARY_BUDGET_TOO_SMALL)
    # Search the final escaped JSON bytes, not source character count.
    lo, hi = 0, min(len(encoded), max_bytes)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        candidate = _json({**metadata, "preview": encoded[:mid]})
        if len(candidate.encode("utf-8")) <= max_bytes:
            lo = mid
        else:
            hi = mid - 1
    return _json({**metadata, "preview": encoded[:lo]})

class ClusterGroup(TypedDict):
    cluster_id: object
    title: object
    member_count: int
    sample_goal_ids: list[str]
    omitted_members: int


class ClusterPreview(TypedDict):
    groups: list[ClusterGroup]
    total_groups: int
    total_goals: int
    omitted_groups: int
    omitted_goals: int
    full_result: str
    expand_argv: list[str]


def cluster_preview(scan: dict[str, object], *, argv: list[str] | None = None, sample: int = 3) -> ClusterPreview:
    """Preserve the public scan's bounds and route to complete membership."""
    if not isinstance(scan.get("groups"), list):
        raise PlanStepError("cluster preview requires the brief scan's groups")
    if argv is None:
        argv = shlex.split(cast(str, scan.get("full_result")) or "intelligence-scan --json")
    full_argv = [token for token in argv if token != "--brief"]
    if "--json" not in full_argv:
        full_argv.append("--json")
    groups: list[ClusterGroup] = []
    for group in cast(list[dict[str, object]], scan["groups"]):
        members = cast(list[str], group.get("sample_goal_ids", []))
        count = cast(int, group.get("member_count", len(members)))
        groups.append({"cluster_id": group.get("cluster_id"), "title": group.get("title"),
                       "member_count": count, "sample_goal_ids": members[:sample],
                       "omitted_members": max(0, count - len(members[:sample]))})
    return {"groups": groups, "total_groups": cast(int, scan.get("total_groups", len(groups))),
            "total_goals": cast(int, scan.get("total_goals", sum(g["member_count"] for g in groups))),
            "omitted_groups": cast(int, scan.get("omitted_groups", 0)),
            "omitted_goals": cast(int, scan.get("omitted_goals", 0)),
            "full_result": shlex.join(full_argv), "expand_argv": full_argv}

def _cluster_summary(scan: dict[str, object], argv: list[str], summary: SummarySpec) -> str:
    preview = cluster_preview(scan, argv=argv, sample=summary.get("max_items", 3))
    budget = summary.get("max_bytes", 2000)
    # Keep recovery metadata even when groups/samples need to be removed.
    while len(_json(preview).encode("utf-8")) > budget:
        sampled = next((g for g in reversed(preview["groups"]) if g["sample_goal_ids"]), None)
        if sampled:
            sampled["sample_goal_ids"].pop()
            sampled["omitted_members"] += 1
        elif preview["groups"]:
            removed = preview["groups"].pop()
            preview["omitted_groups"] += 1
            preview["omitted_goals"] += removed["member_count"]
        else:
            raise PlanStepError("cluster budget cannot hold counts and expansion; increase max_bytes")
    return _json(preview)

def classify_scope(errors: list[dict[str, object]], writes: list[str]) -> dict[str, object]:
    in_scope: list[dict[str, object]] = []
    unrelated: list[dict[str, object]] = []
    for error in errors:
        path = str(error.get("path", ""))
        (in_scope if path and any(fnmatch.fnmatch(path, glob) for glob in writes)
         else unrelated).append(error)
    return {"in_scope": in_scope, "unrelated": unrelated}

def _expand_log_step(step: PlanStep, session_id: str | None = None) -> list[str]:
    if step.get("stage_id"):
        capability = "stage.note.write"
        payload = {"unit_id": step["unit_id"], "stage_id": step["stage_id"], "text": step["text"]}
    else:
        capability, payload = "capture.create", {"text": step["text"]}
    return ["__seal_submit__", capability, _json(payload), step["key"],
            *(["--session-id=" + session_id] if session_id is not None else [])]

def _step_argv(step: PlanStep, index: PlanIndex, session_id: str | None = None) -> list[str]:
    if step.get("kind") == "log":
        argv = _expand_log_step(step, session_id)
    elif step.get("describe"):
        argv = ["capabilities", step["use"], "--json"]
    elif "argv" in step:
        argv = list(step["argv"])
    else:
        argv = [resolve_use(step["use"], index), *step.get("args", [])]
    if step.get("clusters"):
        if not argv or argv[0] != "intelligence-scan":
            raise PlanStepError("clusters requires intelligence-scan")
        for flag in ("--brief", "--json"):
            if flag not in argv:
                argv.append(flag)
    return argv


def _field(payload: object, name: str) -> object:
    if isinstance(payload, dict):
        if payload.get(name):
            return payload[name]
        nested = payload.get("result")
        if isinstance(nested, dict):
            return nested.get(name)
    return None

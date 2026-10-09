"""The module-plan gate, moved below its callers (SPEC (az) item 2, (bd) item 4).

The plan preflight (`_module_plan_validation_errors`), the in-apply gate
(`_plan_apply_gate`) and their exact dependency closure, moved
AST-identically from `commands/module.py` so the registered `route.patch`
handler can use them without an upward import.
"""

from __future__ import annotations

from pathlib import Path

from learning_os.loader import load_repo
from learning_os.material_synthesis import (
    MaterialSynthesisError,
    synthesis_destination,
    validate_unit_material_synthesis,
)
from learning_os.materials_resolution import evidential_route_projection
from learning_os.ops.check import _staged_shadow
from learning_os.rules import validate
from learning_os.warning_baseline import delta, load_baseline, signatures_from_issues


def _unit_route_rows(source_map: dict, unit_id: str) -> dict[str, dict]:
    """This unit's routes from a module source-map document, keyed by route ID."""
    rows: dict[str, dict] = {}
    for source in source_map.get("sources", []) or []:
        if not isinstance(source, dict):
            continue
        source_id = source.get("source_id")
        for route in source.get("unit_routes", []) or []:
            if not isinstance(route, dict) or route.get("unit_id") != unit_id:
                continue
            rid = route.get("id")
            if isinstance(rid, str) and rid not in rows:
                row = dict(route)
                row["source_id"] = source_id
                rows[rid] = row
    return rows


def _evidential_diff(live_rows: dict[str, dict],
                     staged_rows: dict[str, dict]) -> tuple[list[str], list[str], list[str]]:
    """(added, removed, evidentially-changed) route IDs between two route sets.

    Angle, title, depth and other exempt prose never appears here: those edits
    intentionally keep a dossier fresh. Anything in the evidential projection
    — identity, locator, material binding, coverage, scope — does.
    """
    added = sorted(set(staged_rows) - set(live_rows))
    removed = sorted(set(live_rows) - set(staged_rows))
    changed: list[str] = []
    for rid in sorted(set(live_rows) & set(staged_rows)):
        try:
            before = evidential_route_projection(live_rows[rid])
        except ValueError:
            before = {k: v for k, v in live_rows[rid].items() if k != "angle"
                      if k != "angle_detail"}
        try:
            after = evidential_route_projection(staged_rows[rid])
        except ValueError:
            after = {k: v for k, v in staged_rows[rid].items() if k != "angle"
                     if k != "angle_detail"}
        if before != after:
            changed.append(rid)
    return added, removed, changed


def _staged_synthesis_errors(root: Path, module_id: str, live_repo,
                             shadow: Path, shadow_repo,
                             entries: list[tuple[str, dict]]) -> list[str]:
    """Validate replacements against staged state and demand missing ones.

    Every replacement dossier is validated against the shadow post-change
    repository — never the live tree — so the new source map, study maps and
    dossier commit or roll back together. Units with an existing dossier whose
    routes change evidentially without a replacement get one actionable
    diagnostic instead of a stale commit.
    """
    errors: list[str] = []
    supplied = {unit_id for unit_id, _ in entries}
    live_map = (live_repo.module_source_maps or {}).get(module_id) or {}
    staged_map = (shadow_repo.module_source_maps or {}).get(module_id) or {}
    for unit_id, dossier in entries:
        unit = live_repo.units.get(unit_id)
        if unit is None or unit.module_id != module_id:
            errors.append(f"material_syntheses: unknown unit for {module_id}: {unit_id}")
            continue
        try:
            expected = synthesis_destination(live_repo.root, unit_id)
        except MaterialSynthesisError as exc:
            errors.append(f"material_syntheses {unit_id}: {exc}")
            continue
        try:
            rel = expected.resolve().relative_to(live_repo.root.resolve())
        except ValueError:
            errors.append(f"material_syntheses {unit_id}: destination escapes repository")
            continue
        if (shadow / rel).suffix != ".yaml":
            errors.append(f"material_syntheses {unit_id}: destination is not a YAML record")
        try:
            validate_unit_material_synthesis(shadow, unit_id, dossier, repo=shadow_repo)
        except MaterialSynthesisError as exc:
            errors.append(f"material_syntheses {unit_id}: replacement dossier invalid: {exc}")
    for unit_id, unit in sorted(live_repo.units.items()):
        if unit.module_id != module_id:
            continue
        try:
            destination = synthesis_destination(live_repo.root, unit_id)
        except MaterialSynthesisError:
            continue
        if not destination.exists():
            continue
        if unit_id in supplied:
            continue
        live_rows = _unit_route_rows(live_map, unit_id)
        staged_rows = _unit_route_rows(staged_map, unit_id)
        added, removed, changed = _evidential_diff(live_rows, staged_rows)
        if not (added or removed or changed):
            continue
        preservable = sorted(set(live_rows) & set(staged_rows) - set(changed))
        needs_review = sorted(set(added) | set(changed))
        errors.append(
            f"material_syntheses: {unit_id} routes change evidentially "
            f"(added={added}, removed={removed}, changed={changed}) but no "
            f"replacement dossier was supplied; assessments reusable unchanged={preservable}, "
            f"requiring fresh review={needs_review}"
        )
    return errors


#: Stage/resource fields that record learner state rather than plan content.
#: A revision that touches them must say so explicitly; silence corrupts
#: progress, notes, attachments, feedback and review attestations.
_LEARNER_STAGE_FIELDS = ("status", "working_note", "attachments",
                         "source_feedback", "runtime_review", "completed")


def _match_key(resource: dict) -> tuple:
    if isinstance(resource.get("route_id"), str):
        return ("route", resource["route_id"])
    if isinstance(resource.get("source_id"), str):
        return ("source", resource.get("source_id"), resource.get("locator"))
    return ("label", resource.get("label"))


def _stage_by_id(map_data: dict | None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for stage in (map_data or {}).get("stages", []) or []:
        if isinstance(stage, dict) and isinstance(stage.get("id"), str):
            out.setdefault(stage["id"], stage)
    return out


def _unit_semantic_diff(live_map: dict, staged_map: dict,
                        live_study: dict | None, staged_study: dict | None,
                        unit_id: str | None = None) -> dict:
    """Reviewable diff for one unit: routes, placements, triage, learner state.

    Callers pass ``unit_id``: a unit without a study map (on either side) still
    has routes, and deriving its id from the maps alone emptied its whole diff —
    both the review summary and the acknowledgment checks built on it.
    """
    unit_id = unit_id or (staged_study or {}).get("unit_id") \
        or (live_study or {}).get("unit_id") or ""
    live_rows = _unit_route_rows(live_map, unit_id)
    staged_rows = _unit_route_rows(staged_map, unit_id)
    added = sorted(set(staged_rows) - set(live_rows))
    removed = sorted(set(live_rows) - set(staged_rows))
    updated = sorted(rid for rid in set(live_rows) & set(staged_rows)
                     if live_rows[rid] != staged_rows[rid])
    _, _, evidential_changed = _evidential_diff(live_rows, staged_rows)
    demoted = sorted(rid for rid in set(live_rows)
                     if live_rows[rid].get("scope") in {"current", "prerequisite"}
                     and (rid in removed or staged_rows.get(rid, {}).get("scope")
                          not in {"current", "prerequisite"}))
    live_placements = [r for s in _stage_by_id(live_study).values()
                       for r in (s.get("resources", []) or []) if isinstance(r, dict)]
    staged_placements = [r for s in _stage_by_id(staged_study).values()
                         for r in (s.get("resources", []) or []) if isinstance(r, dict)]

    def triage(rows):
        counts: dict[str, int] = {}
        for row in rows:
            counts[row.get("scope_triage", "untriaged")] = \
                counts.get(row.get("scope_triage", "untriaged"), 0) + 1
        return counts

    # A route can appear in several stages. Never collapse those placements:
    # one reference-only placement must not hide another required placement.
    promoted_advanced = sorted(
        rid for rid, row in staged_rows.items()
        if row.get("depth") == "advanced-reference"
        and any(_match_key(p) in {("route", rid),
                                 ("source", row.get("source_id"), row.get("locator"))}
                and p.get("scope_triage") in {"required-now", "helpful-now"}
                for p in staged_placements)
        and (live_rows.get(rid, {}).get("depth") != "advanced-reference"
             or not any(_match_key(p) in {("route", rid),
                                         ("source", row.get("source_id"), row.get("locator"))}
                        and p.get("scope_triage") in {"required-now", "helpful-now"}
                        for p in live_placements)))
    placed_keys = {_match_key(r) for r in staged_placements}
    unplaced = sorted(
        rid for rid, row in staged_rows.items()
        if ("route", rid) not in placed_keys
        and ("source", row.get("source_id"), row.get("locator")) not in placed_keys)
    live_nodes = {n for r in live_rows.values() for n in (r.get("covers", []) or [])}
    staged_nodes = {n for r in staged_rows.values() for n in (r.get("covers", []) or [])}
    uncovered_nodes = sorted(live_nodes - staged_nodes)
    escalated = sorted(
        rid for rid in set(live_rows) & set(staged_rows)
        if live_rows[rid].get("scope") in {"out-of-scope", "prior-year", "optional", "complementary"}
        and staged_rows[rid].get("scope") in {"current", "prerequisite"})
    exact_to_unresolved = sorted(
        rid for rid in set(live_rows) & set(staged_rows)
        if (live_rows[rid].get("locator") or "").strip()
        and not (staged_rows[rid].get("locator") or "").strip())
    live_stages = _stage_by_id(live_study)
    staged_stages = _stage_by_id(staged_study)
    learner_changes: dict[str, list[str]] = {}
    learner_preserved: dict[str, list[str]] = {}
    for sid, old in live_stages.items():
        stage = staged_stages.get(sid, {})
        changed = [f for f in _LEARNER_STAGE_FIELDS if stage.get(f) != old.get(f)]
        kept = [f for f in _LEARNER_STAGE_FIELDS if f not in changed]
        if changed:
            learner_changes[sid] = changed
        if kept:
            learner_preserved[sid] = kept
    resource_learner_changes: list[str] = []
    destructive: list[str] = []
    for sid, old_stage in live_stages.items():
        stage = staged_stages.get(sid)
        if stage is None:
            destructive.append(f"stage {sid} removed (working note and learner state must remain reachable)")
        else:
            for field in ("attachments", "source_feedback"):
                if any(item not in (stage.get(field) or [])
                       for item in old_stage.get(field, []) or []):
                    destructive.append(f"{sid}.{field} loses recorded evidence")
            for field in ("completed", "working_note"):
                if old_stage.get(field) and stage.get(field) != old_stage[field]:
                    destructive.append(f"{sid}.{field} changes recorded evidence")
            if old_stage.get("status") not in {None, "pending"} \
                    and stage.get("status") != old_stage.get("status"):
                destructive.append(f"{sid}.status changes recorded progress")
        remaining = list((stage or {}).get("resources", []) or [])
        for old in old_stage.get("resources", []) or []:
            if not isinstance(old, dict) or not old.get("independent_evidence"):
                continue
            # Preserve each evidence-bearing placement, including duplicates.
            match = next((i for i, r in enumerate(remaining)
                          if isinstance(r, dict) and _match_key(r) == _match_key(old)
                          and r.get("independent_evidence") == old["independent_evidence"]), None)
            if match is None:
                resource_learner_changes.append(f"{sid}:{_match_key(old)}:independent_evidence")
                destructive.append(f"{sid}:{_match_key(old)} loses independent evidence")
            else:
                remaining.pop(match)
    map_state_changes = [f for f in ("status", "current_stage", "detours", "shelving")
                         if live_study and staged_study
                         and live_study.get(f) != staged_study.get(f)]
    for field in ("detours", "shelving"):
        if live_study and live_study.get(field) and field in map_state_changes:
            destructive.append(f"study-map.{field} changes recorded learner state")
    return {
        "unit_id": unit_id,
        "routes_before": len(live_rows),
        "routes_after": len(staged_rows),
        "added": added,
        "updated": updated,
        "removed": removed,
        "evidential_changed": evidential_changed,
        "demoted_current_or_prerequisite": demoted,
        "promoted_advanced_reference": promoted_advanced,
        "scope_escalations": escalated,
        "exact_to_unresolved": exact_to_unresolved,
        "uncovered_knowledge_nodes": uncovered_nodes,
        "placements_before": len(live_placements),
        "placements_after": len(staged_placements),
        "triage_before": triage(live_placements),
        "triage_after": triage(staged_placements),
        "unplaced_routes": unplaced,
        "learner_state_changes": learner_changes,
        "learner_state_preserved": learner_preserved,
        "resource_learner_changes": sorted(resource_learner_changes),
        "map_state_changes": map_state_changes,
        "destructive_learner_changes": destructive,
    }


def _route_changed_units(live_repo, staged_repo, module_id: str) -> set[str]:
    """Units whose routes differ evidentially between two repository states."""
    live_map = (live_repo.module_source_maps or {}).get(module_id) or {}
    staged_map = (staged_repo.module_source_maps or {}).get(module_id) or {}
    unit_ids = {uid for uid, unit in live_repo.units.items()
                if unit.module_id == module_id}
    unit_ids.update(uid for uid, unit in staged_repo.units.items()
                    if unit.module_id == module_id)
    changed: set[str] = set()
    for uid in unit_ids:
        added, removed, evidential = _evidential_diff(
            _unit_route_rows(live_map, uid), _unit_route_rows(staged_map, uid))
        if added or removed or evidential:
            changed.add(uid)
    return changed


def _semantic_ack_problems(module_id: str, live_repo, staged_repo,
                            touched_units: list[str],
                            acknowledgments: list[dict]) -> list[str]:
    """Context-dependent changes that need an explicit documented acknowledgment.

    Hard invariants stay errors elsewhere; these are suspicious-but-legitimate
    shapes (a demotion, a promotion, a reorder of meaning) that review must
    name. Each needs ``acknowledgments[]`` ``{kind, target, reason}``.
    """
    live_map = (live_repo.module_source_maps or {}).get(module_id) or {}
    staged_map = (staged_repo.module_source_maps or {}).get(module_id) or {}
    acked = {(str(a.get("kind")), str(a.get("target")))
             for a in acknowledgments if isinstance(a, dict)}
    missing_reason = {(str(a.get("kind")), str(a.get("target")))
                      for a in acknowledgments
                      if isinstance(a, dict) and not str(a.get("reason", "")).strip()}
    problems: list[str] = []

    def needs(kind: str, target: str, why: str):
        if (kind, target) in acked:
            if (kind, target) in missing_reason:
                problems.append(
                    f"semantic review: acknowledgment {kind} {target} needs a reason")
            return
        problems.append(f"semantic review required ({kind} {target}): {why}; "
                        f"add acknowledgments[] {{kind: {kind}, target: {target}, reason}}")

    live_unit_of = {}
    staged_unit_of = {}
    for source in live_map.get("sources", []) or []:
        for route in source.get("unit_routes", []) or []:
            if isinstance(route, dict) and route.get("id"):
                live_unit_of.setdefault(str(route["id"]), route.get("unit_id"))
    for source in staged_map.get("sources", []) or []:
        for route in source.get("unit_routes", []) or []:
            if isinstance(route, dict) and route.get("id"):
                staged_unit_of.setdefault(str(route["id"]), route.get("unit_id"))
    for rid in sorted(set(live_unit_of) & set(staged_unit_of)):
        if live_unit_of[rid] != staged_unit_of[rid]:
            needs("cross-unit-move", rid,
                  f"route moves from {live_unit_of[rid]} to {staged_unit_of[rid]}")
    scope = set(touched_units) | _route_changed_units(live_repo, staged_repo, module_id)
    for unit_id in sorted(scope):
        live_study = next((sm.data for sm in live_repo.study_maps.values()
                           if sm.unit_id == unit_id), None)
        staged_study = next((sm.data for sm in staged_repo.study_maps.values()
                             if sm.unit_id == unit_id), None)
        diff = _unit_semantic_diff(live_map, staged_map, live_study, staged_study, unit_id)
        problems.extend(f"learner-state preservation: {unit_id}: {p}"
                        for p in diff["destructive_learner_changes"])
        for rid in diff["demoted_current_or_prerequisite"]:
            needs("demotion", rid, f"{unit_id} demotes a current/prerequisite resource")
        for rid in diff["promoted_advanced_reference"]:
            needs("promotion", rid, f"{unit_id} places advanced-reference as required/helpful")
        for rid in diff["scope_escalations"]:
            needs("scope-escalation", rid, f"{unit_id} escalates peripheral scope to current")
        for rid in diff["exact_to_unresolved"]:
            needs("locator-regression", rid, f"{unit_id} replaces an exact locator with none")
        for node in diff["uncovered_knowledge_nodes"]:
            needs("coverage-loss", node, f"{unit_id} removes the last route covering this node")
        if diff["routes_after"] < diff["routes_before"]:
            needs("coverage-reduction", unit_id,
                  f"menu shrinks {diff['routes_before']} to {diff['routes_after']}")
        if diff["learner_state_changes"] or diff["resource_learner_changes"] \
                or diff["map_state_changes"]:
            needs("learner-state", unit_id, "learner-state fields change")
    return problems


def _real_perimeter_errors(root: Path) -> list[str]:
    """Environment errors from the real wrapper tree, in live format.

    Content validation runs in a shadow copy of ``repository/`` alone, where
    the perimeter checker is silent by design (no wrapper anchors exist there).
    The live transaction then validates the real tree and refuses on
    ``PERIMETER-*`` errors — so a preflight that omits this layer passes while
    the application fails. Run this layer against the real root before both
    ``--check`` and live application; synthetic repositories without a
    declaration stay silent, exactly as in live validation.
    """
    from learning_os.contracts import perimeter as _perimeter

    out: list[str] = []
    for issue in _perimeter.check(root):
        if issue.severity != "E":
            continue
        loc = f" [{issue.path}]" if issue.path else ""
        out.append(f"E PERIMETER-{issue.code}: {issue.message}{loc}")
    return out


#: Validator codes emitted by the perimeter checker share this namespace
#: (``check_perimeter`` prefixes every one of them). Both plan gates
#: partition staged issues on this structured namespace — never on message
#: prose — so a future perimeter code stays shadow-equivalent too.
_PERIMETER_CODE_PREFIX = "PERIMETER-"


def _compose_plan_gate_errors(
    root: Path,
    *,
    perimeter_errors: list[str],
    synthesis_errors: list[str],
    ack_errors: list[str],
    content_errors: list[str],
    signatures,
) -> list[str]:
    """One refusal list for plan gates, in shadow-preflight order.

    The ``--check`` shadow preflight and the in-transaction apply gate
    compose through here, so their refusal text cannot drift: the real-tree
    perimeter layer first, then staged synthesis and acknowledgment errors,
    then content errors, then one NEW-OR-GROWN-WARNING line per regressed
    baseline signature.
    """
    # The baseline is read from the real repository: the staged state is the
    # real tree plus the planned writes, so the baseline describes exactly
    # the "before".
    baseline, _ = load_baseline(root)
    regressions, _repairs = delta(baseline, signatures)
    return [
        *perimeter_errors,
        *synthesis_errors,
        *ack_errors,
        *content_errors,
        *(f"W NEW-OR-GROWN-WARNING: {line} (introduced by this plan; fix it, or "
           "adopt it deliberately with `.venv/bin/python tools/warning_baseline.py --update`)"
          for line in regressions),
    ]


def _plan_apply_gate(
    root: Path,
    *,
    live_repo=None,
    module_id: str | None = None,
    syntheses: list[tuple[str, dict]] | None = None,
    touched_units: list[str] | None = None,
    acknowledgments: list[dict] | None = None,
):
    """A ``_write_transaction`` gate enforcing the plan preflight in-apply.

    Returns ``(validate_extra, errors_out)``. The transaction calls
    ``validate_extra(staged_repo, staged_issues)`` once, on the staged state
    under the commit lock, from the same validation run that checks content;
    the full composed refusal list lands in ``errors_out`` for the caller to
    report with the preflight's exact text. The live pre-write repository is
    only needed — and only used — for the synthesis and acknowledgment
    diffs, which compare staged state against it; the caller's own
    already-loaded repo qualifies, because the operator lock held throughout
    means nothing changed between that load and this gate.
    """
    errors_out: list[str] = []

    def validate_extra(staged_repo, staged_issues):
        if module_id is not None and syntheses is not None and live_repo is None:
            raise AssertionError("plan gate needs the pre-write repository")
        perimeter_errors = [
            str(issue) for issue in staged_issues
            if issue.severity == "E"
            and issue.code.startswith(_PERIMETER_CODE_PREFIX)]
        content_issues = [
            issue for issue in staged_issues
            if not issue.code.startswith(_PERIMETER_CODE_PREFIX)]
        signatures, content_errors = signatures_from_issues(content_issues)
        synthesis_errors: list[str] = []
        ack_errors: list[str] = []
        if module_id is not None and syntheses is not None:
            try:
                synthesis_errors = _staged_synthesis_errors(
                    root, module_id, live_repo, root, staged_repo, syntheses)
            except MaterialSynthesisError as exc:
                synthesis_errors = [f"material_syntheses: staged state unreadable: {exc}"]
            if touched_units is not None and acknowledgments is not None:
                ack_errors = _semantic_ack_problems(
                    module_id, live_repo, staged_repo,
                    touched_units, acknowledgments)
        errors = _compose_plan_gate_errors(
            root,
            perimeter_errors=perimeter_errors,
            synthesis_errors=synthesis_errors,
            ack_errors=ack_errors,
            content_errors=content_errors,
            signatures=signatures)
        errors_out.extend(errors)
        return errors

    return validate_extra, errors_out


def _module_plan_validation_errors(
    root: Path,
    writes: dict[Path, str],
    *,
    module_id: str | None = None,
    syntheses: list[tuple[str, dict]] | None = None,
    touched_units: list[str] | None = None,
    acknowledgments: list[dict] | None = None,
) -> list[str]:
    """Validate planned files in a small shadow repository without canonical writes.

    The gate is the repository's one warning policy (CLAUDE.md hard rule 9,
    `learning_os.warning_baseline`): zero errors, and no warning signature that
    is new or grown relative to the recorded baseline. Until 2026-08-29 this
    function instead failed on every non-exempt warning anywhere in the shadow
    repository, which made it unsatisfiable — the baselined content debt of
    CRITIQUE-POINTS §1 lives in the source maps, so `module-plan-import` for one
    module failed on another module's deferred locators. A plan must still be
    refused when it *introduces* a warning; that is what the delta measures.

    The first layer is the real-tree perimeter: the shadow has no wrapper, so
    content validation there can never see an undeclared sibling. The live
    transaction refuses on it, so the preflight must too, with the identical
    string, before any canonical write begins.
    """
    perimeter_errors = _real_perimeter_errors(root)
    with _staged_shadow(root, writes) as shadow:
        signatures, errors = signatures_from_issues(
            validate(load_repo(shadow), online=False))
        synthesis_errors: list[str] = []
        ack_errors: list[str] = []
        if module_id is not None and syntheses is not None:
            live_repo = load_repo(root)
            staged_repo = load_repo(shadow)
            try:
                synthesis_errors = _staged_synthesis_errors(
                    root, module_id, live_repo, shadow, staged_repo, syntheses)
            except MaterialSynthesisError as exc:
                synthesis_errors = [f"material_syntheses: staged state unreadable: {exc}"]
            if touched_units is not None and acknowledgments is not None:
                ack_errors = _semantic_ack_problems(
                    module_id, live_repo, staged_repo,
                    touched_units, acknowledgments)
        content_errors = errors
    return _compose_plan_gate_errors(
        root,
        perimeter_errors=perimeter_errors,
        synthesis_errors=synthesis_errors,
        ack_errors=ack_errors,
        content_errors=content_errors,
        signatures=signatures)

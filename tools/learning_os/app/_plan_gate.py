"""The module-plan gate, moved below its callers (SPEC (az) item 2, (bd) item 4).

The plan preflight (`_module_plan_validation_errors`), the in-apply gate
(`_plan_apply_gate`) and their exact dependency closure, moved
AST-identically from `commands/module.py` so the registered `route.patch`
handler can use them without an upward import.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from learning_os.app.admin.masters_planning import MasterPromotionPlan
from learning_os.app.check import staged_shadow as _staged_shadow
from learning_os.derive.material_synthesis import (
    MaterialSynthesisError,
    synthesis_destination,
    validate_unit_material_synthesis,
)
from learning_os.derive.semantics.claim_status import claim_impacts, observe_claims
from learning_os.derive.validation import validate
from learning_os.domain.plan_import import INVENTORY_ROW_DISPOSITIONS as _INVENTORY_ROW_DISPOSITIONS
from learning_os.domain.plan_import import ack_shape_problems as _ack_shape_problems
from learning_os.domain.plan_import import inventory_block as _inventory_block
from learning_os.domain.plan_import import minimal_artifact_ids as _minimal_artifact_ids
from learning_os.domain.plan_import import (
    module_plan_routing_problems as _module_plan_routing_problems,
)
from learning_os.domain.plan_import import synthesis_entries as _synthesis_entries
from learning_os.domain.route_identity import route_with_identity
from learning_os.store.contracts import PLAN_TEMPLATE_VERSION, current_template_problems
from learning_os.store.fingerprint import canonical_fingerprint
from learning_os.store.loader import load_repo
from learning_os.store.material_analysis import observe_local_material
from learning_os.store.materials.resolution import evidential_route_projection, sha256_file
from learning_os.store.revisions import load_revisions
from learning_os.store.warning_baseline import delta, load_baseline, signatures_from_issues

_PLAN_COMPLETENESS_CHECKS = (
    "local_inventory_complete",
    "linked_inventory_complete",
    "materials_opened_and_content_checked",
    "current_and_prior_scope_reconciled",
    "duplicates_and_numbering_checked",
    "exclusions_and_unresolved_gaps_recorded",
)


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


def match_key(resource: dict) -> tuple:
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
        and any(match_key(p) in {("route", rid),
                                 ("source", row.get("source_id"), row.get("locator"))}
                and p.get("scope_triage") in {"required-now", "helpful-now"}
                for p in staged_placements)
        and (live_rows.get(rid, {}).get("depth") != "advanced-reference"
             or not any(match_key(p) in {("route", rid),
                                         ("source", row.get("source_id"), row.get("locator"))}
                        and p.get("scope_triage") in {"required-now", "helpful-now"}
                        for p in live_placements)))
    placed_keys = {match_key(r) for r in staged_placements}
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
                          if isinstance(r, dict) and match_key(r) == match_key(old)
                          and r.get("independent_evidence") == old["independent_evidence"]), None)
            if match is None:
                resource_learner_changes.append(f"{sid}:{match_key(old)}:independent_evidence")
                destructive.append(f"{sid}:{match_key(old)} loses independent evidence")
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


def real_perimeter_errors(root: Path) -> list[str]:
    """Environment errors from the real wrapper tree, in live format.

    Content validation runs in a shadow copy of ``repository/`` alone, where
    the perimeter checker is silent by design (no wrapper anchors exist there).
    The live transaction then validates the real tree and refuses on
    ``PERIMETER-*`` errors — so a preflight that omits this layer passes while
    the application fails. Run this layer against the real root before both
    ``--check`` and live application; synthetic repositories without a
    declaration stay silent, exactly as in live validation.
    """
    from learning_os.store.contracts import perimeter as _perimeter

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


def compose_plan_gate_errors(
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


def plan_apply_gate(
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
        errors = compose_plan_gate_errors(
            root,
            perimeter_errors=perimeter_errors,
            synthesis_errors=synthesis_errors,
            ack_errors=ack_errors,
            content_errors=content_errors,
            signatures=signatures)
        errors_out.extend(errors)
        return errors

    return validate_extra, errors_out


def module_plan_validation_errors(
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
    `learning_os.store.warning_baseline`): zero errors, and no warning signature that
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
    perimeter_errors = real_perimeter_errors(root)
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
    return compose_plan_gate_errors(
        root,
        perimeter_errors=perimeter_errors,
        synthesis_errors=synthesis_errors,
        ack_errors=ack_errors,
        content_errors=content_errors,
        signatures=signatures)


def coverage_audit_problems(root: Path, contract: dict) -> list[str]:
    """The audit-evidence rules shared by the module (v2) and unit (v1) contracts."""
    problems: list[str] = []
    if contract.get("plan_template_version") != PLAN_TEMPLATE_VERSION:
        problems.append(
            f"plan_contract.plan_template_version must be {PLAN_TEMPLATE_VERSION}"
        )
    audit_ref = contract.get("coverage_audit")
    if not isinstance(audit_ref, str) or not audit_ref.strip():
        problems.append("plan_contract.coverage_audit must name the completed audit")
    else:
        audit = (root / audit_ref).resolve()
        try:
            audit_relative = audit.relative_to(root.resolve())
        except ValueError:
            problems.append("plan_contract.coverage_audit must stay inside the repository")
        else:
            if audit_relative.parts[:2] != ("work", "active"):
                problems.append(
                    "plan_contract.coverage_audit must stay under snapshot-bound work/active/"
                )
            elif not audit.is_file():
                problems.append(f"coverage audit does not exist: {audit_ref}")
            else:
                audit_text = audit.read_text(encoding="utf-8")
                for marker in ("## Local", "## Linked", "## Completeness"):
                    if marker not in audit_text:
                        problems.append(
                            f"coverage audit lacks required section marker: {marker}"
                        )
    checks = contract.get("checks")
    if not isinstance(checks, dict):
        problems.append("plan_contract.checks must be a mapping")
    else:
        for key in _PLAN_COMPLETENESS_CHECKS:
            if checks.get(key) is not True:
                problems.append(f"plan_contract.checks.{key} must be true")
    if isinstance(audit_ref, str) and audit_ref.strip():
        problems.extend(_structured_inventory_problems(root, audit_ref))
    return problems

def enumerate_inventory_roots(materials: Path, roots: list) -> tuple[dict[str, str], list[str]]:
    """Live file set under explicitly scoped material roots: relpath -> sha256.

    Only the declared roots are walked; dotfiles and symlinks are skipped.
    A root that is not an observable directory fails the preflight instead
    of silently narrowing the scope the audit claims to cover.
    """
    observed: dict[str, str] = {}
    problems: list[str] = []
    try:
        boundary = materials.resolve()
    except OSError as exc:
        return {}, [f"material inventory cannot resolve the materials tree: {exc}"]
    cache: dict[Path, str] = {}
    for entry in roots:
        if not isinstance(entry, str) or not entry.strip():
            problems.append("material inventory roots must be nonempty strings")
            continue
        try:
            target = (materials / entry).resolve()
            target.relative_to(boundary)
        except (OSError, ValueError):
            problems.append(f"material inventory root escapes the materials tree: {entry}")
            continue
        if not target.is_dir():
            problems.append(f"material inventory root is not observable: {entry}")
            continue
        for path in sorted(target.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            if any(part.startswith(".") for part in path.relative_to(target).parts):
                continue
            rel = path.relative_to(boundary).as_posix()
            try:
                observed[rel] = sha256_file(path, cache).removeprefix("sha256:")
            except OSError:
                problems.append(f"material inventory cannot read observed file: {rel}")
    return observed, problems

def inventory_row_problems(block: dict, observed: dict[str, str],
                            materials: Path) -> list[str]:
    """Row shape, scope, digest, and duplicate-bytes rules for one inventory."""
    problems: list[str] = []
    rows = block.get("rows")
    if not isinstance(rows, list):
        return ["coverage audit inventory-v1 block needs a rows list"]
    roots = [r for r in (block.get("roots") or []) if isinstance(r, str)]
    seen: dict[str, dict] = {}
    local_rows: dict[str, dict] = {}
    for index, row in enumerate(rows):
        label = f"inventory row {index}"
        if not isinstance(row, dict):
            problems.append(f"{label} must be a mapping")
            continue
        kind = row.get("kind", "local")
        if kind not in ("local", "linked"):
            problems.append(f"{label} kind must be local or linked")
            continue
        disposition = row.get("disposition")
        if disposition not in _INVENTORY_ROW_DISPOSITIONS:
            problems.append(
                f"{label} disposition must be one of "
                f"{', '.join(_INVENTORY_ROW_DISPOSITIONS)}")
            continue
        if kind == "linked":
            for field in ("path", "sha256", "duplicate_of"):
                if row.get(field) is not None:
                    problems.append(
                        f"{label} is linked: {field} would impersonate observed bytes")
            if disposition not in ("linked", "out-of-scope"):
                problems.append(f"{label} is linked but disposed as {disposition}")
            if not isinstance(row.get("reference"), str) or not row["reference"].strip():
                problems.append(f"{label} is linked but names no reference")
            continue
        if disposition == "linked":
            problems.append(f"{label} observes local bytes but is disposed as linked")
            continue
        path = row.get("path")
        observation = observe_local_material(materials, path, "")
        if observation["status"] == "outside-boundary":
            problems.append(f"{label} path escapes the materials tree: {path}")
            continue
        if not any(path == root or path.startswith(root.rstrip("/") + "/")
                   for root in roots):
            problems.append(f"{label} path is outside the declared roots: {path}")
            continue
        if path in seen:
            problems.append(f"inventory row repeats path: {path}")
            continue
        seen[path] = row
        local_rows[path] = row
        recorded = row.get("sha256")
        if not isinstance(recorded, str) or len(recorded) != 64:
            problems.append(f"{label} needs the observed 64-hex sha256 for {path}")
            continue
        live = observed.get(path)
        if live is None:
            problems.append(f"inventory row names an unobserved file: {path}")
        elif live.lower() != recorded.lower():
            problems.append(f"inventory digest differs from observed bytes: {path}")
    for rel in sorted(observed):
        if rel not in seen:
            problems.append(f"material inventory lacks a row for observed file: {rel}")
    by_digest: dict[str, list[str]] = {}
    for path, row in local_rows.items():
        recorded = row.get("sha256")
        if isinstance(recorded, str) and len(recorded) == 64:
            by_digest.setdefault(recorded.lower(), []).append(path)
    for _digest, paths in sorted(by_digest.items()):
        if len(paths) < 2:
            continue
        canonical = [p for p in paths
                     if local_rows[p].get("disposition") != "duplicate"]
        if len(canonical) != 1:
            problems.append(
                "duplicate bytes need exactly one canonical row and "
                f"duplicate dispositions: {', '.join(sorted(paths))}")
            continue
        for path in sorted(paths):
            row = local_rows[path]
            if row.get("disposition") != "duplicate":
                continue
            target = row.get("duplicate_of")
            if target not in paths:
                problems.append(
                    f"inventory row {path} duplicate_of must name a row "
                    f"with equal bytes: {target}")
    return problems

def _structured_inventory_problems(root: Path, audit_ref: str) -> list[str]:
    """Reconcile the audit's structured inventory against observed bytes.

    Returns [] for a legacy audit without an inventory-v1 block. A present
    block must enumerate exactly the observed local set: missing rows,
    unobserved rows, digest drift, and undeclared duplicate bytes all fail.
    """
    audit = (root / audit_ref).resolve()
    try:
        audit.relative_to(root.resolve())
    except ValueError:
        return []
    if not audit.is_file():
        return []
    block, problems = _inventory_block(audit.read_text(encoding="utf-8"))
    if problems or block is None:
        return problems
    roots = block.get("roots")
    if not isinstance(roots, list) or not roots:
        return ["coverage audit inventory-v1 block needs a nonempty roots list"]
    materials = root.parent / "materials"
    observed, problems = enumerate_inventory_roots(materials, roots)
    if problems:
        return problems
    return inventory_row_problems(block, observed, materials)

def module_plan_contract_problems(root: Path, package: dict) -> list[str]:
    """Verify the human review evidence required before a plan is executable."""
    problems: list[str] = []
    contract = package.get("plan_contract")
    if not isinstance(contract, dict) or contract.get("version") != 2:
        return ["plan_contract.version must be 2 (see system/PLAN-CREATION-SOP.md)"]
    problems.extend(coverage_audit_problems(root, contract))
    problems.extend(_ack_shape_problems(package.get("acknowledgments", [])))
    intentional_reorders = contract.get("intentional_reorders", [])
    if not isinstance(intentional_reorders, list):
        problems.append("plan_contract.intentional_reorders must be a list")
    else:
        seen: set[tuple[str, str]] = set()
        for index, declaration in enumerate(intentional_reorders):
            if not isinstance(declaration, dict):
                problems.append(
                    f"plan_contract.intentional_reorders[{index}] must be a mapping"
                )
                continue
            target = declaration.get("target")
            record_id = declaration.get("id")
            reason = declaration.get("reason")
            if target not in {"module-unit-order", "study-map-stage-order"}:
                problems.append(
                    f"plan_contract.intentional_reorders[{index}].target must be "
                    "module-unit-order or study-map-stage-order"
                )
            if not isinstance(record_id, str) or not record_id.strip():
                problems.append(
                    f"plan_contract.intentional_reorders[{index}].id must name the reordered record"
                )
            if not isinstance(reason, str) or not reason.strip():
                problems.append(
                    f"plan_contract.intentional_reorders[{index}].reason must explain the pedagogical change"
                )
            key = (str(target), str(record_id))
            if key in seen:
                problems.append(
                    f"plan_contract.intentional_reorders repeats {key[0]} for {key[1]}"
                )
            seen.add(key)
    for unit_index, entry in enumerate(package.get("units", []) or []):
        if not isinstance(entry, dict) or entry.get("study_map") is None:
            continue
        for problem in current_template_problems(entry.get("study_map"), "curriculum"):
            problems.append(f"units[{unit_index}].study_map: {problem}")
    _, synthesis_problems = _synthesis_entries(
        package.get("module_id", ""), package)
    problems.extend(synthesis_problems)
    return problems

def module_plan_check_report(root: Path, module_id: str, package: dict,
                              writes: dict[Path, str],
                              entries: list[tuple[str, dict]],
                              package_sha: str,
                              seen_units: set[str]) -> dict:
    """The review artifact for a plan preflight: stable schema, no writes.

    Counts, diffs, freshness and learner-state preservation for exactly the
    touched units, computed from the live repository and one staged shadow.
    """
    from learning_os.derive.material_synthesis import (
        validate_unit_material_synthesis as _validate_dossier,
    )

    live_repo = load_repo(root)
    live_map = (live_repo.module_source_maps or {}).get(module_id) or {}
    acknowledgments = package.get("acknowledgments", []) or []
    supplied = {unit_id for unit_id, _ in entries}
    with _staged_shadow(root, writes) as shadow:
        staged_repo = load_repo(shadow)
        staged_map = (staged_repo.module_source_maps or {}).get(module_id) or {}

        def rows(source_map):
            out: dict[str, dict] = {}
            for source in source_map.get("sources", []) or []:
                if not isinstance(source, dict):
                    continue
                for route in source.get("unit_routes", []) or []:
                    if isinstance(route, dict):
                        identified = route_with_identity(module_id, str(source.get("source_id") or ""), route)
                        out.setdefault(str(identified["id"]), identified)
            return out

        live_rows, staged_rows = rows(live_map), rows(staged_map)
        changed_material_sources = {sid for sid, row in staged_repo.sources.items()
                                    if row.get("material") != live_repo.sources.get(sid, {}).get("material")}
        material_routes = {str(route_with_identity(module_id, str(source.get("source_id") or ""), row)["id"])
                           for source in staged_map.get("sources", [])
                           if source.get("source_id") in changed_material_sources
                           for row in source.get("unit_routes", []) if isinstance(row, dict)}
        touched_routes = {rid for rid, row in {**live_rows, **staged_rows}.items()
                          if row.get("unit_id") in seen_units or live_rows.get(rid) != staged_rows.get(rid)} | material_routes
        before_claims = observe_claims(root, repo=live_repo, route_ids=touched_routes)
        after_claims = observe_claims(shadow, repo=staged_repo, route_ids=touched_routes & set(staged_rows))
        rejudged = [row["claim_id"] for row in package.get("claim_evidence", []) or [] if isinstance(row, dict)]
        claims = claim_impacts(before_claims, after_claims, rejudged)

        units: dict[str, dict] = {}
        for uid in sorted(seen_units):
            live_study = next((sm.data for sm in live_repo.study_maps.values()
                               if sm.unit_id == uid), None)
            staged_study = next((sm.data for sm in staged_repo.study_maps.values()
                                 if sm.unit_id == uid), None)
            units[uid] = _unit_semantic_diff(live_map, staged_map, live_study, staged_study, uid)
        synthesis: dict[str, dict] = {}
        for uid in sorted(seen_units):
            try:
                destination = synthesis_destination(root, uid)
            except MaterialSynthesisError:
                continue
            exists = destination.exists()
            before: dict = {"present": exists, "fresh": False, "detail": None}
            if exists:
                try:
                    current = yaml.safe_load(destination.read_text(encoding="utf-8"))
                    validate_unit_material_synthesis(root, uid, current)
                    before["fresh"] = True
                except (MaterialSynthesisError, OSError, ValueError) as exc:
                    before["detail"] = str(exc)
            after: dict = {"replaced": uid in supplied, "fresh": False, "detail": None}
            if uid in supplied:
                dossier = dict(next(d for u, d in entries if u == uid))
                try:
                    _validate_dossier(shadow, uid, dossier, repo=staged_repo)
                    after["fresh"] = True
                except MaterialSynthesisError as exc:
                    after["detail"] = str(exc)
            elif exists and not before["fresh"]:
                after["detail"] = "live dossier already stale"
            elif exists:
                rows_live = _unit_route_rows(live_map, uid)
                rows_staged = _unit_route_rows(staged_map, uid)
                a, r, c = _evidential_diff(rows_live, rows_staged)
                if not (a or r or c):
                    after["fresh"] = True
                else:
                    after["detail"] = f"routes change without replacement: added={a} removed={r} changed={c}"
            synthesis[uid] = {"before": before, "after": after}
        ack_problems = _semantic_ack_problems(
            module_id, live_repo, staged_repo,
            sorted(set(seen_units)
                   | _route_changed_units(live_repo, staged_repo, module_id)),
            acknowledgments if isinstance(acknowledgments, list) else [])
    affected = sorted(str(p.resolve().relative_to(root.resolve())) for p in writes)
    changing: list[str] = []
    for path in writes:
        try:
            if (not path.exists()
                    or path.read_bytes() != writes[path].encode("utf-8")):
                changing.append(str(path.resolve().relative_to(root.resolve())))
        except OSError:
            changing.append(str(path.resolve().relative_to(root.resolve())))
    artifact_ids = [module_id, *sorted(seen_units),
                    *[d.get("id") for _, d in entries
                      if isinstance(d.get("id"), str)]]
    changing_writes = {}
    for path in writes:
        try:
            rel = str(path.resolve().relative_to(root.resolve()))
        except ValueError:
            continue
        if rel in changing:
            changing_writes[path] = writes[path]
    commit_artifact_ids = _minimal_artifact_ids(root, module_id, changing_writes, entries)
    revisions = load_revisions(root)
    live_sources = live_map.get("sources", []) or []
    staged_sources = staged_map.get("sources", []) or []
    return {
        "claims": claims,
        "ok": True,
        "mode": "check",
        "module_id": module_id,
        "package_sha256": package_sha,
        "expected_snapshot": f"sha256:{canonical_fingerprint(root)}",
        "expected_revisions": {aid: revisions.get(aid, 0) for aid in artifact_ids},
        "artifact_ids": artifact_ids,
        "affected_files": affected,
        "byte_changing_files": sorted(changing),
        "route_counts": {"before": len(live_rows), "after": len(staged_rows)},
        "source_records": {"before": len(live_sources), "after": len(staged_sources)},
        "units": units,
        "routes_added": sorted(set(staged_rows) - set(live_rows)),
        "routes_removed": sorted(set(live_rows) - set(staged_rows)),
        "routes_updated": sorted(rid for rid in set(live_rows) & set(staged_rows)
                                 if live_rows[rid] != staged_rows[rid]),
        "synthesis": synthesis,
        "semantic_ack_required": ack_problems,
        "commit_artifact_ids": commit_artifact_ids,
        "canonical_files_written": 0,
    }

def master_promotion_preflight(
    root: Path,
    module_id: str,
    plan: MasterPromotionPlan,
    package: dict,
    *,
    skip_validation: bool = False,
) -> list[str]:
    problems = module_plan_contract_problems(root, package)
    if problems:
        return [f"contract: {problem}" for problem in problems]
    repo = load_repo(root)
    problems = _module_plan_routing_problems(repo, module_id, package)
    if problems:
        return [f"routing: {problem}" for problem in problems]
    if skip_validation:
        # A gateway apply enforces the validation layer inside its
        # transaction instead; the package layers above still refuse here.
        return []
    try:
        errors = module_plan_validation_errors(root, plan.writes)
    except ValueError as exc:
        return [str(exc)]
    return [str(issue) for issue in errors]

def master_promotion_check_result(
    root: Path,
    module_id: str,
    plan: MasterPromotionPlan,
) -> dict:
    return {
        "ok": True,
        "mode": "check",
        "module_id": module_id,
        "candidate_module_id": plan.provenance["candidate_module_id"],
        "promotion_id": plan.provenance["id"],
        "package_sha256": plan.package_sha256,
        "expected_snapshot": f"sha256:{canonical_fingerprint(root)}",
        "expected_revisions": dict(plan.expected_revisions),
        "artifact_ids": list(plan.artifact_ids),
        "affected_files": list(plan.affected_paths),
        "provenance": plan.provenance,
        "diff": plan.diff,
        "canonical_files_written": 0,
    }

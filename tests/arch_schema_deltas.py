"""Shared request-schema delta strips for ratchet-context comparisons.

SPEC (bf) item 7 (the S13-context D16 test): the (ay) owner-metadata and
(bf) item 1 description strips, moved verbatim from
``tests/test_arch_ratchets.py`` so both the D4 conversion-purity check
and the D16 schema check apply exactly the same allowances.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from history_baselines import historical_text


def _c1_packet() -> dict:
    root = Path(__file__).resolve().parent.parent
    raw = (root / "workbench/architecture-hardening-2026-10-17/execution/C1-SURFACE-PACKET.json").read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "8e7781d6d10071e25eb0bc51cc0d068bbecffd51340946f1d82a7c107c31d2cf"
    return json.loads(raw)


def _before_approved_c1_cli(key: str, live: list) -> list:
    """Undo only the exact later approved additions for historical D16 comparisons.

    Besides the C1 packet's two rows, the A11-approved --report-out flag of
    2026-10-31 (workbench/system-fixes-2026-10-31/PLAN.md FX-4, approval line
    in tests/architecture/surface-approvals.yaml) is undone exactly.
    """
    if key in {"cli.goal", "cli.route-patch"}:
        change = _c1_packet()["changes"][key]
        assert live == change["after"], key
        return change["before"]
    if key == "cli.module-plan-import":
        unwound = [action for action in live if action.get("dest") != "report_out"]
        assert len(unwound) == len(live) - 1, key
        return unwound
    return live


def _before_approved_c1_schema(operation: str, raw: bytes) -> dict:
    """Require approved live bytes before comparing earlier schema migrations."""
    if operation == "module.plan.import":
        # The S13 proof predates the A11-approved --report-out field (FX-4,
        # approval recorded 2026-10-31); undo exactly that property.
        live = json.loads(raw)
        approved = live.get("properties", {}).pop("report_out", None)
        assert approved is not None, operation
        return live
    if operation not in {"goal.decide", "route.patch"}:
        return json.loads(raw)
    packet = _c1_packet()
    change = packet["changes"][f"request_schemas.{operation}.schema.json"]
    assert hashlib.sha256(raw).hexdigest() == change["after"], operation
    text = historical_text(
        packet["base_core"], f"system/schema/requests/{operation}.schema.json")
    assert text is not None, operation
    before = text.encode("utf-8")
    assert hashlib.sha256(before).hexdigest() == change["before"], operation
    return json.loads(before)

#: Exact SPEC (ay) owner metadata per primary request-schema file: node
#: pointer parts -> (owner, owner_shape). Alias files carry no metadata.
OWNER_METADATA_POINTERS: dict[str, dict[tuple[str, ...], tuple[str, str]]] = {
    "project.inspect": {
        ("properties", "id"): ("inspect-reference", "scalar"),
        ("properties", "more_ids", "items"): ("inspect-reference", "scalar"),
    },
    "ai-action.delivery.apply": {
        ("properties", "delivery_id"): ("ai-delivery-exchange", "scalar"),
        ("properties", "artifact_sha256"):
            ("ai-delivery-artifact-digests", "mapping-values"),
    },
}


def _strip_approved_owner_metadata(operation: str, old: dict, new: dict
                                   ) -> tuple[dict, dict]:
    """Strip exactly the approved SPEC (ay) metadata; fail on any deviation.

    Returns ``(old, new)`` copies with the approved ``x-los-id-owner`` /
    ``x-los-lookup`` pairs removed at exactly the approved pointers.
    Raises on a missing or mistyped pair, metadata the base already pins
    to a different value, a changed node type, or a missing node; every
    other difference stays for the exact recursive comparison.
    """
    approved = OWNER_METADATA_POINTERS.get(operation, {})
    old_copy = copy.deepcopy(old)
    new_copy = copy.deepcopy(new)
    for parts, (owner, owner_shape) in approved.items():
        old_node = old_copy
        new_node = new_copy
        try:
            for part in parts:
                old_node = old_node[part]
                new_node = new_node[part]
        except (KeyError, TypeError):
            raise AssertionError(
                f"owner pointer /{'/'.join(parts)} is missing") from None
        if not isinstance(new_node, dict):
            raise AssertionError(
                f"owner pointer /{'/'.join(parts)} is not an object")
        if not isinstance(new_node.get("x-los-id-owner"), str) \
                or new_node["x-los-id-owner"] != owner:
            raise AssertionError(
                f"owner pointer /{'/'.join(parts)} lacks "
                f"x-los-id-owner {owner!r}")
        if new_node.get("x-los-lookup") is not True:
            raise AssertionError(
                f"owner pointer /{'/'.join(parts)} lacks x-los-lookup true")
        if not isinstance(old_node, dict):
            raise AssertionError(
                f"owner pointer /{'/'.join(parts)} is not an object at base")
        if "x-los-id-owner" in old_node \
                and old_node["x-los-id-owner"] != owner:
            raise AssertionError(
                f"owner pointer /{'/'.join(parts)} changes its owner")
        if "x-los-lookup" in old_node and old_node["x-los-lookup"] is not True:
            raise AssertionError(
                f"owner pointer /{'/'.join(parts)} changes its lookup")
        if new_node.get("type") != old_node.get("type"):
            raise AssertionError(
                f"owner pointer /{'/'.join(parts)} changes its type")
        if owner_shape == "scalar" and new_node.get("type") != "string":
            raise AssertionError(
                f"owner pointer /{'/'.join(parts)} is not a scalar string")
        if owner_shape == "mapping-values" \
                and new_node.get("type") != "object":
            raise AssertionError(
                f"owner pointer /{'/'.join(parts)} is not a mapping object")
        for doc_node in (old_node, new_node):
            doc_node.pop("x-los-id-owner", None)
            doc_node.pop("x-los-lookup", None)
    for parts, (before, after, _was_present) in PHASE4_METADATA_CHANGES.get(operation, {}).items():
        old_node, new_node = old_copy, new_copy
        for part in parts[:-1]:
            old_node, new_node = old_node[part], new_node[part]
        key = parts[-1]
        if key not in old_node and key not in new_node:
            continue  # the earlier exact owner strip already removed this pair
        assert new_node.get(key) == after and type(new_node.get(key)) is type(after), (operation, parts)
        assert key not in old_node or old_node[key] in (before, after), (operation, parts)
        if key in old_node:
            new_node[key] = old_node[key]
        else:
            new_node.pop(key, None)
    return old_copy, new_copy


#: Exact SPEC (bf) item 1 pilot description pointers, plus the SPEC
#: (bi) item 6 wave 1 and final-wave authorized pointers: operation ->
#: property-node pointer parts. Only a ``description`` change from the
#: bootstrap placeholder to a real string is stripped, at exactly these
#: pairs (12 pilot + 83 wave 1 + 122 final wave). Alias files carry no
#: descriptions of their own.
BF_DESCRIPTION_POINTERS: dict[str, tuple[tuple[str, ...], ...]] = {
    "route.patch": (
        ("properties", "unit_id"),
        ("properties", "route_id"),
        ("properties", "changes"),
        ("properties", "check"),
        ("properties", "expected_snapshot"),
    ),
    "stage.progress.update": (
        ("properties", "unit_id"),
        ("properties", "stage_id"),
        ("properties", "status"),
        ("properties", "expected_snapshot"),
    ),
    "ai-action.delivery.apply": (
        ("properties", "delivery_id"),
        ("properties", "expected_snapshot"),
    ),
    "project.inspect": (
        ("properties", "id"),
    ),
    "ai-action.append-slices": (
        ("properties", "request_id"),
        ("properties", "route_id"),
        ("properties", "expected_snapshot"),
    ),
    "ai-action.delivery.import": (
        ("properties", "path"),
    ),
    "ai-action.prepare": (
        ("properties", "action_id"),
        ("properties", "target_kind"),
        ("properties", "target_id"),
        ("properties", "provider"),
        ("properties", "expected_snapshot"),
    ),
    "ai-action.status": (
        ("properties", "request_id"),
    ),
    "ai-action.delivery.validate": (
        ("properties", "delivery_id"),
    ),
    "detour.create": (
        ("properties", "unit_id"),
        ("properties", "stage_id"),
        ("properties", "title"),
        ("properties", "classification"),
        ("properties", "expected_snapshot"),
    ),
    "detour.resolve": (
        ("properties", "unit_id"),
        ("properties", "detour_id"),
        ("properties", "resolution"),
        ("properties", "expected_snapshot"),
    ),
    "learner.ability-observation.append": (
        ("properties", "workspace"),
        ("properties", "ability"),
        ("properties", "activity"),
        ("properties", "result"),
        ("properties", "assistance"),
        ("properties", "condition"),
        ("properties", "evidence_tag"),
        ("properties", "condition_not_met"),
        ("properties", "supersedes"),
        ("properties", "expected_snapshot"),
    ),
    "learner.observation.append": (
        ("properties", "workspace"),
        ("properties", "requirement"),
        ("properties", "activity"),
        ("properties", "result"),
        ("properties", "assistance"),
        ("properties", "tags"),
        ("properties", "context"),
        ("properties", "expected_snapshot"),
    ),
    "learner.stage-result.append": (
        ("properties", "workspace"),
        ("properties", "unit"),
        ("properties", "stage"),
        ("properties", "activity"),
        ("properties", "result"),
        ("properties", "assistance"),
        ("properties", "expected_snapshot"),
    ),
    "note.evidence.add": (
        ("properties", "note_id"),
        ("properties", "evidence_type"),
        ("properties", "expected_snapshot"),
    ),
    "note.revise": (
        ("properties", "note_id"),
        ("properties", "approve"),
        ("properties", "expected_snapshot"),
    ),
    "path.attachment.add": (
        ("properties", "path_id"),
        ("properties", "stage_id"),
        ("properties", "label"),
    ),
    "path.note.write": (
        ("properties", "path_id"),
        ("properties", "stage_id"),
    ),
    "path.progress.update": (
        ("properties", "path_id"),
        ("properties", "stage_id"),
        ("properties", "status"),
    ),
    "source.feedback.record": (
        ("properties", "unit_id"),
        ("properties", "stage_id"),
        ("properties", "source_id"),
        ("properties", "feedback"),
        ("properties", "note"),
        ("properties", "expected_snapshot"),
    ),
    "stage.attachment.add": (
        ("properties", "unit_id"),
        ("properties", "stage_id"),
        ("properties", "label"),
        ("properties", "expected_snapshot"),
    ),
    "stage.note.write": (
        ("properties", "unit_id"),
        ("properties", "stage_id"),
        ("properties", "text"),
        ("properties", "expected_snapshot"),
    ),
    "unit.note.append": (
        ("properties", "unit_id"),
        ("properties", "title"),
        ("properties", "text"),
        ("properties", "expected_snapshot"),
    ),
    "unit.source-selection.set": (
        ("properties", "unit_id"),
        ("properties", "source_id"),
        ("properties", "locator"),
        ("properties", "action"),
        ("properties", "purpose"),
        ("properties", "expected_snapshot"),
    ),
    "ability.candidate.append": (
        ("properties", "carries"),
        ("properties", "changes"),
        ("properties", "condition"),
        ("properties", "expected_snapshot"),
        ("properties", "from_ability"),
        ("properties", "kind"),
        ("properties", "source_ref"),
        ("properties", "to_ability"),
    ),
    "ability.context": (
        ("properties", "expected_snapshot"),
        ("properties", "limit"),
    ),
    "atlas.question.save": (
        ("properties", "expected_snapshot"),
        ("properties", "question"),
    ),
    "atlas.context": (
        ("properties", "concept_id"),
        ("properties", "expected_snapshot"),
    ),
    "backup.manifest": (
        ("properties", "materials_root"),
        ("properties", "ui_root"),
    ),
    "backup.verify": (
        ("properties", "manifest"),
        ("properties", "restored_core"),
        ("properties", "restored_materials"),
        ("properties", "restored_ui"),
    ),
    "operator.bootstrap": (
        ("properties", "expected_snapshot"),
        ("properties", "limit"),
        ("properties", "offset"),
    ),
    "goal.decide": (
        ("properties", "close"),
        ("properties", "defer"),
        ("properties", "reject"),
    ),
    "inbox.content": (
        ("properties", "expected_snapshot"),
    ),
    "legacy.archive.inspect": (
        ("properties", "allowlist"),
        ("properties", "archive_root"),
    ),
    "masters-planning.dashboard": (
        ("properties", "confirm_masters_planning"),
    ),
    "module.list": (
        ("properties", "program_id"),
        ("properties", "status"),
    ),
    "note.content": (
        ("properties", "expected_snapshot"),
        ("properties", "note_id"),
    ),
    "learner.observe": (
        ("properties", "activity"),
        ("properties", "assistance"),
        ("properties", "result"),
        ("properties", "tags"),
    ),
    "plan.edit-context": (
        ("properties", "expected_snapshot"),
        ("properties", "unit_id"),
    ),
    "plan.template": (
        ("properties", "module_id"),
        ("properties", "profile"),
        ("properties", "title"),
        ("properties", "unit_id"),
    ),
    "project.list": (
        ("properties", "status"),
    ),
    "related.read": (
        ("properties", "id"),
    ),
    "runtime.session": (
        ("properties", "context_json"),
        ("properties", "event"),
        ("properties", "expected_snapshot"),
        ("properties", "requirement"),
    ),
    "note.search": (
        ("properties", "expected_snapshot"),
        ("properties", "limit"),
        ("properties", "offset"),
    ),
    "unit.list": (
        ("properties", "component_id"),
        ("properties", "expected_snapshot"),
        ("properties", "limit"),
        ("properties", "module_id"),
        ("properties", "offset"),
        ("properties", "status"),
    ),
    "collection.entry.revise": (
        ("properties", "approve"),
        ("properties", "expected_snapshot"),
        ("properties", "record"),
    ),
    "concept.relations.change": (
        ("properties", "change"),
        ("properties", "expected_snapshot"),
    ),
    "coordination.section.revise": (
        ("properties", "expected_snapshot"),
        ("properties", "section"),
    ),
    "garden.seed.create": (
        ("properties", "expected_snapshot"),
    ),
    "inbox.resolve": (
        ("properties", "expected_snapshot"),
    ),
    "legacy.archive.lock.publish": (
        ("properties", "approve"),
        ("properties", "expected_snapshot"),
        ("properties", "record"),
    ),
    "masters-planning.catalog.update": (
        ("properties", "approve"),
        ("properties", "expected_snapshot"),
        ("properties", "record"),
    ),
    "masters-planning.comparison.publish": (
        ("properties", "approve"),
        ("properties", "candidate_module_id"),
        ("properties", "expected_snapshot"),
        ("properties", "record"),
    ),
    "material.context": (
        ("properties", "expected_snapshot"),
        ("properties", "limit"),
        ("properties", "offset"),
    ),
    "material.span": (
        ("properties", "expected_snapshot"),
        ("properties", "extract"),
        ("properties", "route_id"),
        ("properties", "unit_id"),
    ),
    "module.attempt.record": (
        ("properties", "expected_snapshot"),
        ("properties", "module_id"),
    ),
    "module.materials.compact": (
        ("properties", "check"),
        ("properties", "expected_snapshot"),
        ("properties", "module_id"),
    ),
    "module.sitting.update": (
        ("properties", "expected_snapshot"),
        ("properties", "module_id"),
    ),
    "note.analysis.save": (
        ("properties", "analysis"),
        ("properties", "expected_snapshot"),
    ),
    "note.analysis.save_batch": (
        ("properties", "expected_snapshot"),
    ),
    "note.create": (
        ("properties", "expected_snapshot"),
        ("properties", "note"),
    ),
    "project.create": (
        ("properties", "expected_snapshot"),
    ),
    "project.update": (
        ("properties", "expected_snapshot"),
        ("properties", "project_id"),
    ),
    "review.apply": (
        ("properties", "approve"),
        ("properties", "expected_snapshot"),
        ("properties", "selected"),
        ("properties", "unit_id"),
    ),
    "review.prepare": (
        ("properties", "expected_snapshot"),
        ("properties", "summary"),
        ("properties", "unit_id"),
    ),
    "source.intake.record": (
        ("properties", "approve"),
        ("properties", "expected_snapshot"),
        ("properties", "record"),
    ),
    "source.record.revise": (
        ("properties", "approve"),
        ("properties", "expected_snapshot"),
        ("properties", "record"),
    ),
    "unit.map.import": (
        ("properties", "expected_snapshot"),
        ("properties", "unit_id"),
    ),
    "unit.material-synthesis.publish": (
        ("properties", "approve"),
        ("properties", "check"),
        ("properties", "expected_snapshot"),
        ("properties", "record"),
        ("properties", "unit_id"),
    ),
    "workspace.next-action.update": (
        ("properties", "expected_snapshot"),
        ("properties", "workspace_id"),
    ),
}

_PLACEHOLDER_MARK = "(no description in the parser yet)"


def _strip_bf_description_updates(operation: str, old: dict, new: dict
                                  ) -> tuple[dict, dict]:
    """Strip exactly the approved SPEC (bf) description replacements.

    Returns ``(old, new)`` copies with the new description reset to the
    base one at each listed pointer whose base value contains the
    placeholder mark and whose new value is a non-empty string without
    it. Every other difference stays for the exact recursive comparison.
    """
    old_copy = copy.deepcopy(old)
    new_copy = copy.deepcopy(new)
    for parts in BF_DESCRIPTION_POINTERS.get(operation, ()):
        old_node = old_copy
        new_node = new_copy
        try:
            for part in parts:
                old_node = old_node[part]
                new_node = new_node[part]
        except (KeyError, TypeError):
            continue
        if not isinstance(old_node, dict) or not isinstance(new_node, dict):
            continue
        base = old_node.get("description")
        updated = new_node.get("description")
        if (isinstance(base, str) and _PLACEHOLDER_MARK in base
                and isinstance(updated, str) and updated
                and _PLACEHOLDER_MARK not in updated):
            new_node["description"] = base
    return old_copy, new_copy


# Exact SPEC (cx) D6-D9 metadata transitions; every other delta remains visible.
PHASE4_METADATA_CHANGES = {'ai-action.append-slices': {('properties', 'request_id', 'x-los-id-owner'): (None, 'ai-request-store', False), ('properties', 'request_id', 'x-los-lookup'): (None, True, False)}, 'ai-action.prepare': {('properties', 'action_id', 'x-los-id-owner'): (None, 'ai-action-registry', False), ('properties', 'action_id', 'x-los-lookup'): (None, True, False), ('properties', 'request_id', 'x-los-lookup'): (None, False, False), ('properties', 'target_id', 'x-los-id-owner'): (None, 'ai-action-target', False), ('properties', 'target_id', 'x-los-lookup'): (None, True, False)}, 'ai-action.status': {('properties', 'request_id', 'x-los-id-owner'): (None, 'ai-request-store', False), ('properties', 'request_id', 'x-los-lookup'): (None, True, False)}, 'ai-action.delivery.validate': {('properties', 'delivery_id', 'x-los-id-owner'): (None, 'ai-delivery-store', False), ('properties', 'delivery_id', 'x-los-lookup'): (None, True, False)}, 'operations.read': {('properties', 'request_id', 'x-los-id-owner'): (None, 'operations-trace-request', False), ('properties', 'request_id', 'x-los-lookup'): (None, True, False)}, 'related.read': {('properties', 'id', 'x-los-id-owner'): (None, 'related-record', False), ('properties', 'id', 'x-los-lookup'): (None, True, False)}, 'masters-planning.comparison.publish': {('properties', 'candidate_module_id', 'x-los-id-owner'): (None, 'masters-candidate-module', False), ('properties', 'candidate_module_id', 'x-los-lookup'): (None, True, False)}, 'session.end': {('properties', 'session_id', 'x-los-lookup'): (None, False, False)}, 'goal.decide': {('properties', 'session_id', 'x-los-lookup'): (None, False, False)}}


def _restore_phase6_descriptions(operation: str, old: dict, new: dict) -> dict:
    """Compare through the nine literal descriptions Aram approved on 17 October."""
    import json
    from pathlib import Path

    table = json.loads((Path(__file__).parent / "architecture" /
                        "phase6-description-updates.json").read_text())
    restored = copy.deepcopy(new)
    for change in table["changes"]:
        if change["schema"] != f"system/schema/requests/{operation}.schema.json":
            continue
        before, after = old, restored
        for part in change["pointer"].split("/")[1:-1]:
            before, after = before[part], after[part]
        assert before["description"] in (change["old"], change["new"])
        assert after["description"] == change["new"]
        after["description"] = before["description"]
    return restored

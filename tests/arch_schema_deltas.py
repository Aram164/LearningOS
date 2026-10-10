"""Shared request-schema delta strips for ratchet-context comparisons.

SPEC (bf) item 7 (the S13-context D16 test): the (ay) owner-metadata and
(bf) item 1 description strips, moved verbatim from
``tests/test_arch_ratchets.py`` so both the D4 conversion-purity check
and the D16 schema check apply exactly the same allowances.
"""

from __future__ import annotations

import copy

#: Exact SPEC (ay) owner metadata per primary request-schema file: node
#: pointer parts -> (owner, owner_shape). Alias files carry no metadata.
OWNER_METADATA_POINTERS: dict[str, dict[tuple[str, ...], tuple[str, str]]] = {
    "cli.inspect": {
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
    return old_copy, new_copy


#: Exact SPEC (bf) item 1 pilot description pointers, plus the SPEC
#: (bi) item 6 wave 1 authorized pointers: operation -> property-node
#: pointer parts. Only a ``description`` change from the bootstrap
#: placeholder to a real string is stripped, at exactly these pairs
#: (12 pilot + 83 wave 1). Alias files carry no descriptions of their
#: own.
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
    "cli.inspect": (
        ("properties", "id"),
    ),
    "cli.ai-action-append-slices": (
        ("properties", "request_id"),
        ("properties", "route_id"),
        ("properties", "expected_snapshot"),
    ),
    "cli.ai-action-import-delivery": (
        ("properties", "path"),
    ),
    "cli.ai-action-prepare": (
        ("properties", "action_id"),
        ("properties", "target_kind"),
        ("properties", "target_id"),
        ("properties", "provider"),
        ("properties", "expected_snapshot"),
    ),
    "cli.ai-action-status": (
        ("properties", "request_id"),
    ),
    "cli.ai-action-validate-delivery": (
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

"""The semantic contract holds for its first predicate (Phase 0 spike).

`NeedsStudyMap` is the derivation the producer already answers per unit row
as `needs_study_map`. These pin the evaluator's truth table, the registry
shape Phase 1 will grow, and the fact that the producer's wrapper and the
evaluator cannot disagree — so the spike proves the pattern rather than
adding a second opinion.
"""

from __future__ import annotations

import pytest

from learning_os.genout.projection.records_curriculum import _needs_study_map
from learning_os.semantics import (
    CONTRACT_VERSION,
    PREDICATES,
    evaluate,
    needs_study_map,
)


def test_the_contract_version_is_pinned():
    """Lineage (Phase 2) cites this; a bump must be a deliberate diff."""
    assert CONTRACT_VERSION == 2


EXPECTED_PREDICATES = {
    "NeedsStudyMap", "ScopeAuthority", "AllowedMutation", "ShelvingApproval",
    "CritiquePointActionable", "MasteryDeclared", "NoteChangeNeedsReview",
    "EvidenceComplete", "ClaimStale", "SourceComplete", "RouteValid",
    "RouteEvaluated", "StudyMapGrounded", "PlanTemplateCurrent", "RepoClean",
    "SnapshotFresh", "CanonicalWritePath", "WorkspaceMayCoordinate",
    "QuarantineExcluded", "ExternalSibling", "RelationMayApply",
    "DossierFresh", "AttemptConsistent",
}


def test_the_registry_holds_exactly_the_phase_1_set():
    """Cap: any addition needs a VOQ or a goal-detector motivating it."""
    assert set(PREDICATES) == EXPECTED_PREDICATES
    for predicate in PREDICATES.values():
        assert predicate.version == CONTRACT_VERSION
        assert predicate.authoritative_inputs
        assert predicate.authority
        assert predicate.description


def test_the_registry_names_the_spike_predicate():
    predicate = PREDICATES["NeedsStudyMap"]
    assert predicate.version == CONTRACT_VERSION
    assert predicate.authoritative_inputs == (
        "unit_status", "module_status", "has_study_map",
    )
    assert predicate.description


def test_unknown_predicates_fail_closed():
    with pytest.raises(KeyError):
        evaluate("DoesNotExist", unit_status="active")


@pytest.mark.parametrize(
    ("unit_status", "module_status", "has_map", "owed", "why"),
    [
        ("not-started", "enrolled", False, True,
         "an enrolled lecture with no map owes one"),
        ("active", "active", False, True, "so does an active one"),
        ("not-started", "enrolled", True, False,
         "a map discharges the obligation"),
        ("complete", "enrolled", False, False, "a finished unit owes nothing"),
        ("archived", "enrolled", False, False, "nor one set aside"),
        ("paused", "enrolled", False, False, "a paused unit is inactive"),
        ("ready-to-shelve", "active", False, False,
         "a unit leaving active study owes no new map"),
        ("not-started", "dropped", False, False,
         "a dropped module is history"),
        ("not-started", "archived", False, False, "nor is an archived one"),
        ("needs-map", "dropped", False, False,
         "an old label cannot oblige an inactive module"),
        ("not-started", None, False, False,
         "an unresolvable module accuses nobody"),
        (None, "enrolled", False, True,
         "a missing unit status still owes when the module is studied"),
    ],
)
def test_the_evaluator_answers_the_obligation(
    unit_status, module_status, has_map, owed, why,
):
    assert evaluate(
        "NeedsStudyMap",
        unit_status=unit_status,
        module_status=module_status,
        has_study_map=has_map,
    ) is owed, why


@pytest.mark.parametrize(
    ("name", "inputs", "verdict", "why"),
    [
        ("ScopeAuthority",
         {"fact_kind": "exam_date", "module_id": "module-hu-aml"},
         "curriculum/modules/module-hu-aml/module.yaml",
         "academic facts live in the owning module record"),
        ("ScopeAuthority", {"fact_kind": "exam_date"}, "unknown",
         "a module fact without its module has no owner"),
        ("ScopeAuthority", {"fact_kind": "records_mirror"}, "unknown",
         "compatibility mirrors are never authoritative"),
        ("ScopeAuthority",
         {"fact_kind": "workspace_status", "workspace_id": "workspace-aml-exam-prep"},
         "work/active/workspace-aml-exam-prep/CONTEXT.md",
         "workspace state lives in the workspace frontmatter"),
        ("AllowedMutation",
         {"capability": "route.patch",
          "target_path": "curriculum/modules/module-hu-aml/source-map.yaml",
          "scopes": ("curriculum/modules/*/source-map.yaml",)},
         True, "the capability contract admits its own scope"),
        ("AllowedMutation",
         {"capability": "route.patch",
          "target_path": "knowledge/notes/note-x.md",
          "scopes": ("curriculum/modules/*/source-map.yaml",)},
         False, "notes are outside route.patch authority"),
        ("AllowedMutation",
         {"capability": "route.patch",
          "target_path": "curriculum/modules/../x",
          "scopes": ("curriculum/**",)},
         False, "a traversal target denies rather than raises"),
        ("AllowedMutation",
         {"capability": "nope", "target_path": "x", "scopes": ()},
         False, "empty scopes deny"),
        ("ShelvingApproval",
         {"applied_items": ["a"], "approved_items": ["a", "b"]},
         True, "applied inside approval"),
        ("ShelvingApproval",
         {"applied_items": ["c"], "approved_items": ["a", "b"]},
         False, "unselected items never apply"),
        ("ShelvingApproval", {"applied_items": [], "approved_items": ["a"]},
         False, "an empty apply is refused, not waved through"),
        ("CritiquePointActionable",
         {"status": "open", "authorized_in_session": False},
         "deferred", "an open point is not a work item"),
        ("CritiquePointActionable",
         {"status": "open", "authorized_in_session": True},
         "actionable", "Aram's say-so in that session authorizes"),
        ("CritiquePointActionable",
         {"status": "resolved", "authorized_in_session": True},
         "closed", "closed points stay closed"),
        ("CritiquePointActionable",
         {"status": "mysterious", "authorized_in_session": True},
         "deferred", "unrecognized status defers"),
        ("MasteryDeclared", {"statement_kind": "resolved"},
         False, "a resolved question is still not mastery"),
        ("MasteryDeclared", {"statement_kind": "exam-passed"},
         True, "passing is a mastery claim and is refused"),
        ("MasteryDeclared", {"statement_kind": "vibes"},
         True, "unrecognized kinds are suspicion, not trust"),
        ("NoteChangeNeedsReview", {"change_kind": "semantic-rewrite"},
         True, "rewriting meaning needs eyes"),
        ("NoteChangeNeedsReview", {"change_kind": "evidence-append"},
         False, "appending trails never needs review"),
        ("NoteChangeNeedsReview", {"change_kind": "polish"},
         True, "unknown kinds require review"),
        ("EvidenceComplete",
         {"entries": [{"type": "derivation", "ref": "material://demo/x.pdf"}]},
         True, "one well-formed trail is the floor"),
        ("EvidenceComplete", {"entries": []},
         False, "absence is reported as absence"),
        ("EvidenceComplete",
         {"entries": [{"type": "derivation", "ref": "knowledge/attachments/x.md"}]},
         False, "a bare path breaks when the file moves"),
        ("EvidenceComplete",
         {"entries": [{"type": "derivation", "ref": "material://d/x.pdf"},
                      {"type": "derivation", "ref": "material://d/x.pdf"}]},
         False, "duplicates are not append-only"),
        ("ClaimStale",
         {"read_contract_version": 2, "current_contract_version": 2,
          "read_revisions": {"a": 3}, "current_revisions": {"a": 3}},
         False, "fresh reads are believed"),
        ("ClaimStale",
         {"read_contract_version": 1, "current_contract_version": 2,
          "read_revisions": {"a": 3}, "current_revisions": {"a": 3}},
         True, "a moved contract stales every claim"),
        ("ClaimStale",
         {"read_contract_version": 2, "current_contract_version": 2,
          "read_revisions": {"a": 3}, "current_revisions": {"a": 4}},
         True, "a newer read revision stales the claim"),
        ("ClaimStale",
         {"read_contract_version": 2, "current_contract_version": 2,
          "read_revisions": {"a": 3}, "current_revisions": {"a": 3, "b": 1}},
         False, "artifacts the claim never read cannot stale it"),
        ("SourceComplete",
         {"selection_state": "selected", "locator_ok": True},
         True, "selected with a working locator"),
        ("SourceComplete",
         {"selection_state": "selected", "locator_ok": False},
         False, "a dead locator is not accounted for"),
        ("SourceComplete",
         {"selection_state": "deferred", "locator_ok": False,
          "deferral_reason": "prior-year deck, superseded"},
         True, "deferred with a reason"),
        ("SourceComplete",
         {"selection_state": "deferred", "locator_ok": False,
          "deferral_reason": "  "},
         False, "a blank reason is silent omission"),
        ("SourceComplete",
         {"selection_state": "maybe", "locator_ok": True},
         False, "unrecognized states are incomplete"),
        ("RouteValid",
         {"route_id": "route-5ee4aec41221a1821604773c",
          "unit_id": "unit-aml-l01", "source_id": "source-aml-ss26-lectures",
          "locator": "lecture-slides/VL 01.pdf"},
         True, "a real route shape validates"),
        ("RouteValid",
         {"route_id": "VL 01 deck", "unit_id": "unit-aml-l01",
          "source_id": "source-aml-ss26-lectures", "locator": "x"},
         False, "titles are prose, never identity"),
        ("RouteEvaluated", {"scope": "optional"},
         True, "assessed skippable is still assessed"),
        ("RouteEvaluated", {"scope": "unevaluated"},
         False, "routed but never judged"),
        ("RouteEvaluated", {"scope": "someday"},
         False, "outside the vocabulary is not an assessment"),
        ("StudyMapGrounded",
         {"template_version": 1,
          "resource_pairs": [["source-a", "ch 1"]],
          "menu_pairs": [["source-a", "ch 1"], ["source-a", "ch 2"]]},
         True, "every row resolves against the menu"),
        ("StudyMapGrounded",
         {"template_version": 1,
          "resource_pairs": [["source-a", "ch 9"]],
          "menu_pairs": [["source-a", "ch 1"]]},
         False, "a row outside the menu ungrounds the map"),
        ("StudyMapGrounded",
         {"template_version": 0, "resource_pairs": [], "menu_pairs": []},
         False, "an old template is never grounded"),
        ("PlanTemplateCurrent", {"template_version": 1},
         True, "the shared contract"),
        ("PlanTemplateCurrent", {"template_version": True},
         False, "a bool is not a version"),
        ("RepoClean", {"error_count": 0, "new_or_grown_warnings": 0},
         True, "the definition of clean"),
        ("RepoClean", {"error_count": 0, "new_or_grown_warnings": 1},
         False, "one traded warning still fails"),
        ("SnapshotFresh",
         {"expected_snapshot": "sha256:abc", "current_snapshot": "sha256:abc"},
         True, "matching snapshots proceed"),
        ("SnapshotFresh",
         {"expected_snapshot": "sha256:abc", "current_snapshot": "sha256:def"},
         False, "on conflict, reload rather than overwrite"),
        ("SnapshotFresh", {"expected_snapshot": "", "current_snapshot": ""},
         False, "empty snapshots are never fresh"),
        ("CanonicalWritePath", {"channel": "route.patch"},
         True, "a declared gateway"),
        ("CanonicalWritePath", {"channel": "hand-edit"},
         False, "a hand edit is never a faster version"),
        ("WorkspaceMayCoordinate", {"claim_kind": "unit_ids"},
         True, "id lists coordinate"),
        ("WorkspaceMayCoordinate", {"claim_kind": "unit_order"},
         False, "ordering belongs to the module"),
        ("WorkspaceMayCoordinate", {"claim_kind": "whatever"},
         False, "unknown kinds do not coordinate"),
        ("QuarantineExcluded",
         {"path": "curriculum/quarantine/masters-planning/catalog.yaml"},
         True, "quarantine stays out of normal search"),
        ("QuarantineExcluded", {"path": "knowledge/notes/note-x.md"},
         False, "ordinary notes index normally"),
        ("QuarantineExcluded", {"path": "../escape"},
         True, "unreadable paths are never routinely indexed"),
        ("ExternalSibling", {"path": "Stratum/models/x.py"},
         True, "the sibling is never traversed automatically"),
        ("ExternalSibling", {"path": "knowledge/notes/note-x.md"},
         False, "in-repo paths are ordinary"),
        ("ExternalSibling", {"path": "/etc/passwd"},
         True, "absolute paths are outside by construction"),
        ("RelationMayApply",
         {"relation_type": "requires", "from_id": "concept-a",
          "to_id": "concept-b", "inferred": False},
         True, "a closed-vocabulary edge over canonical ids"),
        ("RelationMayApply",
         {"relation_type": "requires", "from_id": "concept-a",
          "to_id": "concept-b", "inferred": True},
         False, "nothing inferred lands without review"),
        ("RelationMayApply",
         {"relation_type": "related-to", "from_id": "concept-a",
          "to_id": "concept-b", "inferred": False},
         False, "there is no related-to"),
        ("DossierFresh",
         {"cached_hashes": {"unit": "h1"}, "current_hashes": {"unit": "h1"}},
         True, "unchanged inputs hit the cache"),
        ("DossierFresh",
         {"cached_hashes": {"unit": "h1"}, "current_hashes": {"unit": "h2"}},
         False, "one changed hash poisons the cache"),
        ("DossierFresh", {"cached_hashes": {}, "current_hashes": {}},
         False, "empty hash maps are never fresh"),
        ("AttemptConsistent",
         {"attempt_termins": [1], "sitting_termins": [1, 2]},
         True, "the attempt names a real sitting"),
        ("AttemptConsistent",
         {"attempt_termins": [3], "sitting_termins": [1, 2]},
         False, "a never-registered slot must not survive as real"),
    ],
)
def test_every_predicate_answers_and_fails_closed(name, inputs, verdict, why):
    assert evaluate(name, **inputs) == verdict, why


def test_the_producer_and_the_evaluator_cannot_disagree():
    """Sweep the input space: the wrapper must equal the predicate everywhere."""
    unit_statuses = [
        "not-started", "active", "complete", "archived", "paused",
        "ready-to-shelve", "needs-map", None,
    ]
    module_statuses = [
        "active", "enrolled", "dropped", "archived", "paused", None,
    ]
    for unit_status in unit_statuses:
        for module_status in module_statuses:
            for has_map in (False, True):
                assert _needs_study_map(
                    {"status": unit_status}, module_status, has_map,
                ) is needs_study_map(
                    unit_status=unit_status,
                    module_status=module_status,
                    has_study_map=has_map,
                )

"""Phase-1 semantic predicates: pure derived judgments over existing records.

The Intelligence Plane's semantic layer is interpretation, not stored truth.
Every predicate here is a pure function over already-loaded records or
projection rows. Predicates never write canonical data, never touch rebuilt
views, and never call gateway capabilities. The producer
(``genout.projection``) keeps answering derivations per row; this module owns
their *meaning* so agents read one declared layer instead of re-deriving it
from scattered YAML and rules.

Each predicate documents its authoritative inputs and its fallback rule: what
it answers when the inputs are incomplete or unknown. The fallback direction
is always fail-closed — an unknown input never produces a confident
permission. The full table lives in ``system/SEMANTIC-CONTRACT.md``; the
registry below is the machine-readable copy. Any addition needs a Verified
Operator Question (``tests/fixtures/verified_operator_questions/``) or a
goal-detector motivating it.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass

from ..contracts.write_scopes import WriteScopeError, scope_matches
from ..loading.vocabulary import EVIDENCE_SCHEMES, ID_RE, RELATION_TYPES, UNIT_ID_RE
from ..route_identity import ROUTE_ID_RE

#: Version of the predicate contract. Bumped when a predicate's inputs, truth
#: table, or registry membership changes. Lineage sidecars (Phase 2) cite this
#: so "what goes stale if the contract changes" stays answerable.
CONTRACT_VERSION = 2

#: A module whose units are still being studied. A dropped or archived module
#: keeps its records as history and is never asked for new plans.
STUDIED_MODULE_STATUSES = frozenset({"active", "enrolled"})

#: A unit that is finished, paused/inactive, or explicitly set aside is not
#: owed a plan either. `ready-to-shelve` is operationally inactive: asking it
#: to acquire a new study map while it is leaving active study would reverse
#: the user's lifecycle decision.
UNIT_STATUSES_WITHOUT_OBLIGATION = frozenset({
    "complete", "archived", "paused", "ready-to-shelve",
})

#: Route scopes the schema knows. `unevaluated` is assessed-nothing: the
#: source is routed but nobody has ever judged it — visibility debt, not a
#: verdict. Anything outside this set is not a scope at all.
ROUTE_SCOPE_VALUES = frozenset({
    "current", "prerequisite", "complementary", "optional",
    "prior-year", "out-of-scope", "unevaluated",
})

#: Evidence trails a note may carry (note.schema.json). A trail is a typed
#: claim that work exists; the body is never the evidence.
EVIDENCE_TYPES = frozenset({
    "derivation", "explanation", "implementation", "exercise", "exam", "external",
})

#: Statement kinds that declare mastery and are therefore refused
#: (OPERATOR.md rule 10; atlas.question.save invariant).
MASTERY_DECLARING_KINDS = frozenset({
    "mastered", "mastery", "complete", "task-complete", "exam-passed",
})

#: Statement kinds that describe work without claiming it.
NON_MASTERY_KINDS = frozenset({
    "open", "resolved", "evidence", "progress", "question",
})

#: Note changes that require visible review (OPERATOR.md rule 2).
REVIEW_REQUIRED_CHANGES = frozenset({
    "semantic-rewrite", "identity-change", "deletion",
    "inferred-relation", "pedagogical-judgment",
})

#: Note changes that never require review on their own.
REVIEW_FREE_CHANGES = frozenset({
    "typo", "formatting", "evidence-append", "measurement", "link-fix",
})

#: Channels through which a plan may be created or revised (OPERATOR.md
#: rule 16). Anything else is a hand edit, never a faster version of the path.
CANONICAL_WRITE_CHANNELS = frozenset({
    "module.plan.import", "unit.map.import", "route.patch", "migration",
})

#: What a workspace may coordinate (explicit id lists) versus what it never
#: owns (OPERATOR.md rule 6: workspaces do not own the curriculum hierarchy).
WORKSPACE_COORDINATION_KINDS = frozenset({
    "program_ids", "module_ids", "unit_ids",
})
WORKSPACE_OWNERSHIP_KINDS = frozenset({
    "unit_order", "module_status", "study_map", "note_body", "source_evaluation",
})

#: Source disposition states (OPERATOR.md rule 14: every named source is
#: selected, reference-only, or deferred with a reason — silent omission is
#: forbidden).
SELECTED_SOURCE_STATES = frozenset({"selected", "reference-only"})


def needs_study_map(
    *,
    unit_status: str | None,
    module_status: str | None,
    has_study_map: bool,
) -> bool:
    """Whether a unit still owes an ordered study map (OPERATOR.md rule 6).

    Derived, not declared. An authored label is a claim someone has to remember
    to set; one derivation ends the disagreement between counts, badges, and
    the Review queue. Fallback: an unresolvable module accuses nobody.
    """
    if has_study_map:
        return False
    if module_status not in STUDIED_MODULE_STATUSES:
        return False
    return unit_status not in UNIT_STATUSES_WITHOUT_OBLIGATION


#: Which record owns each fact kind: (location template, required id fields).
#: Compatibility mirrors (records/) never appear here; neither does anything
#: quarantined or boundary-only. A fact whose kind or ids are unknown has no
#: owner rather than a guessed one.
FACT_OWNERS: Mapping[str, tuple[str, tuple[str, ...]]] = {
    "exam_date": ("curriculum/modules/{module_id}/module.yaml", ("module_id",)),
    "exam_sitting": ("curriculum/modules/{module_id}/module.yaml", ("module_id",)),
    "exam_attempt": ("curriculum/modules/{module_id}/module.yaml", ("module_id",)),
    "registration_window": (
        "curriculum/modules/{module_id}/module.yaml", ("module_id",)),
    "module_status": ("curriculum/modules/{module_id}/module.yaml", ("module_id",)),
    "module_role": ("curriculum/modules/{module_id}/module.yaml", ("module_id",)),
    "workspace_status": ("work/active/{workspace_id}/CONTEXT.md", ("workspace_id",)),
    "coordination_decision": ("work/COORDINATION.md", ()),
    "priority": ("work/COORDINATION.md", ()),
    "deferral": ("work/COORDINATION.md", ()),
    "study_map_order": (
        "curriculum/modules/{module_id}/units/{unit_id}/study-map.yaml",
        ("module_id", "unit_id")),
    "stage_status": (
        "curriculum/modules/{module_id}/units/{unit_id}/study-map.yaml",
        ("module_id", "unit_id")),
    "stage_source_feedback": (
        "curriculum/modules/{module_id}/units/{unit_id}/study-map.yaml",
        ("module_id", "unit_id")),
    "source_selection": (
        "curriculum/modules/{module_id}/units/{unit_id}/unit.yaml",
        ("module_id", "unit_id")),
    "concept_definition": ("knowledge/notes/{note_id}.md", ("note_id",)),
    "note_body": ("knowledge/notes/{note_id}.md", ("note_id",)),
    "concept_relation": ("knowledge/concept-relations.yaml", ()),
    "source_record": ("sources/registry/ ({source_id})", ("source_id",)),
    "material_identity": ("sources/registry/ ({source_id})", ("source_id",)),
    "program_status": ("curriculum/programs/{program_id}.yaml", ("program_id",)),
    "transaction_receipt": ("operations/transactions/", ()),
}


def scope_authority(
    *,
    fact_kind: str,
    module_id: str = "",
    unit_id: str = "",
    workspace_id: str = "",
    note_id: str = "",
    program_id: str = "",
    source_id: str = "",
) -> str:
    """Which record authoritatively owns a fact (OPERATOR.md boundaries 4-5).

    Returns the owning location, or ``"unknown"`` when the kind is not in the
    table or a required id is missing. Fallback: never guess — a compatibility
    mirror or a quarantined record is never an acceptable answer.
    """
    entry = FACT_OWNERS.get(fact_kind)
    if entry is None:
        return "unknown"
    template, required = entry
    provided = {
        "module_id": module_id,
        "unit_id": unit_id,
        "workspace_id": workspace_id,
        "note_id": note_id,
        "program_id": program_id,
        "source_id": source_id,
    }
    if any(not provided[field] for field in required):
        return "unknown"
    return template.format(**{key: provided[key] for key in provided})


def allowed_mutation(
    *,
    capability: str,
    target_path: str,
    scopes: Sequence[str],
) -> bool:
    """Whether a capability's declared write scopes admit a target path.

    Authority is the capability contract's ``writes`` entry
    (system/contracts/capabilities.yaml); matching is exact segment logic,
    never a string prefix. Fallback: malformed capability, path, or scope —
    or an empty scope list — denies. Total: never raises.
    """
    if not isinstance(capability, str) or not capability:
        return False
    if not isinstance(target_path, str) or not isinstance(scopes, Sequence):
        return False
    try:
        return any(
            scope_matches(target_path, pattern)
            for pattern in scopes
            if isinstance(pattern, str)
        )
    except WriteScopeError:
        return False


def shelving_approval(
    *,
    applied_items: Sequence[str],
    approved_items: Sequence[str],
) -> bool:
    """Whether a shelving apply stays inside the explicit approval.

    OPERATOR.md rule 9: apply only explicitly selected proposal items.
    An empty apply carries nothing and is refused rather than waved through.
    """
    if not applied_items or not approved_items:
        return False
    try:
        return set(applied_items) <= set(approved_items)
    except TypeError:
        return False


def critique_point_actionable(
    *,
    status: str,
    authorized_in_session: bool,
) -> str:
    """Whether a critique point is actionable work, deferred, or closed.

    An open point is not a work item — it is recorded precisely so it can be
    deferred. Acting on one needs Aram's explicit say-so in that session;
    appending evidence never needs it. Fallback: an unrecognized status
    defers rather than authorizes.
    """
    if status == "open":
        return "actionable" if authorized_in_session else "deferred"
    if status in {"resolved", "withdrawn"}:
        return "closed"
    return "deferred"


def mastery_declared(*, statement_kind: str) -> bool:
    """Whether a statement kind declares mastery and must be refused.

    OPERATOR.md rule 10: report evidence or its absence, never mastery. A
    personal question recorded as resolved is still not mastery. Fallback:
    an unrecognized kind is treated as declaring — suspicion, not trust.
    """
    if statement_kind in MASTERY_DECLARING_KINDS:
        return True
    if statement_kind in NON_MASTERY_KINDS:
        return False
    return True


def note_change_needs_review(*, change_kind: str) -> bool:
    """Whether a note change requires visible review (OPERATOR.md rule 2).

    Semantic rewriting, identity changes, deletion, inferred relations, and
    pedagogical judgments never land silently. Fallback: unknown kinds
    require review.
    """
    if change_kind in REVIEW_REQUIRED_CHANGES:
        return True
    if change_kind in REVIEW_FREE_CHANGES:
        return False
    return True


def _evidence_entry_well_formed(entry: object) -> bool:
    """One trail is a known type addressed by a typed URI (note.schema.json)."""
    if not isinstance(entry, Mapping):
        return False
    kind, ref = entry.get("type"), entry.get("ref")
    return (
        kind in EVIDENCE_TYPES
        and isinstance(ref, str)
        and bool(ref)
        and ref.startswith(EVIDENCE_SCHEMES)
    )


def evidence_complete(*, entries: Sequence[Mapping[str, object]]) -> bool:
    """Whether a note's evidence trail counts as complete (Phase 1 bar).

    Complete means present, well-formed, and append-only: at least one trail,
    every trail a known type with a typed-URI ref, no exact duplicates. This
    is the floor — role-specific bars (a mock exam's difficulty, an exercise
    bank's solved/unsolved split) belong to lineage review, not to presence.
    Fallback: malformed input is incomplete, never an exception.
    """
    if not isinstance(entries, Sequence) or not entries:
        return False
    try:
        trails = [dict(entry) for entry in entries]
    except (TypeError, ValueError):
        return False
    if not all(_evidence_entry_well_formed(entry) for entry in trails):
        return False
    seen = {(entry.get("type"), entry.get("ref")) for entry in trails}
    return len(seen) == len(trails)


def claim_stale(
    *,
    read_contract_version: int,
    current_contract_version: int,
    read_revisions: Mapping[str, int],
    current_revisions: Mapping[str, int],
) -> bool:
    """Whether a derived claim must be re-examined before it is believed.

    A claim goes stale when the contract it was judged under moved, when an
    artifact it read has a newer revision, or when a read artifact is gone.
    Artifacts the claim never read cannot stale it — staleness is not
    completeness. Fallback: malformed revision maps are stale — a claim
    whose reads cannot be checked is not a claim to rely on.
    """
    if read_contract_version != current_contract_version:
        return True
    if not isinstance(read_revisions, Mapping) \
            or not isinstance(current_revisions, Mapping):
        return True
    try:
        return any(
            key not in current_revisions or current_revisions[key] != revision
            for key, revision in read_revisions.items()
        )
    except TypeError:
        return True


def source_complete(
    *,
    selection_state: str,
    locator_ok: bool,
    deferral_reason: str = "",
) -> bool:
    """Whether a learning source is fully accounted for (OPERATOR.md rule 14).

    Every source a plan names must be selected or reference-only with a
    working locator, or deferred with a reason. Registered-source counts
    never prove this; silent omission fails it. Fallback: an unrecognized
    state or a missing reason is incomplete.
    """
    if selection_state in SELECTED_SOURCE_STATES:
        return bool(locator_ok)
    if selection_state == "deferred":
        return isinstance(deferral_reason, str) and bool(deferral_reason.strip())
    return False


def route_valid(
    *,
    route_id: str,
    unit_id: str,
    source_id: str,
    locator: str,
) -> bool:
    """Whether a material route is structurally addressable.

    A valid route carries a well-formed route id and names its owning unit,
    source, and locator — titles are learner prose and never identity.
    Validity is not evaluation: an unevaluated route can be valid.
    Fallback: any missing or malformed field invalidates.
    """
    return (
        isinstance(route_id, str) and ROUTE_ID_RE.match(route_id) is not None
        and isinstance(unit_id, str) and UNIT_ID_RE.match(unit_id) is not None
        and isinstance(source_id, str) and ID_RE.match(source_id) is not None
        and isinstance(locator, str) and bool(locator.strip())
    )


def route_evaluated(*, scope: str) -> bool:
    """Whether a route's scope reflects a real assessment.

    `unevaluated` means routed but never judged — visibility debt, made
    visible so it can be chosen or dismissed deliberately. Anything outside
    the schema's scope vocabulary is not an assessment either.
    """
    return scope in ROUTE_SCOPE_VALUES and scope != "unevaluated"


def _pairs(rows: object) -> set[tuple[str, str]] | None:
    """Normalize (source_id, locator) rows, or None when they are malformed."""
    if not isinstance(rows, Sequence):
        return None
    pairs = set()
    for row in rows:
        if not isinstance(row, Sequence) or len(row) != 2:
            return None
        source_id, locator = row
        if not isinstance(source_id, str) or not isinstance(locator, str):
            return None
        pairs.add((source_id, locator))
    return pairs


def study_map_grounded(
    *,
    template_version: int,
    resource_pairs: Sequence[Sequence[str]],
    menu_pairs: Sequence[Sequence[str]],
) -> bool:
    """Whether every material stage row resolves against the complete menu.

    A study map is an ordered projection over the unit's complete material
    menu — never a replacement for it. Grounded means the current template
    contract and no row reaching outside the menu. Fallback: malformed rows
    unground the map; a map with no material rows is trivially grounded.
    """
    if type(template_version) is not int or template_version != 1:
        return False
    resources, menu = _pairs(resource_pairs), _pairs(menu_pairs)
    if resources is None or menu is None:
        return False
    return resources <= menu


def plan_template_current(*, template_version: int) -> bool:
    """Whether a plan uses the shared numbered-stage contract (rule 15)."""
    return type(template_version) is int and template_version == 1


def repo_clean(*, error_count: int, new_or_grown_warnings: int) -> bool:
    """Whether the repository counts as clean (OPERATOR.md: zero errors, and
    no new or grown warning signature — warnings stay visible, never block).
    """
    return error_count == 0 and new_or_grown_warnings == 0


def snapshot_fresh(*, expected_snapshot: str, current_snapshot: str) -> bool:
    """Whether a mutation still holds the snapshot it read (rule 12).

    On conflict the caller reloads rather than overwrites. Fallback: an
    empty snapshot on either side is never fresh.
    """
    return (
        isinstance(expected_snapshot, str)
        and isinstance(current_snapshot, str)
        and bool(expected_snapshot)
        and expected_snapshot == current_snapshot
    )


def canonical_write_path(*, channel: str) -> bool:
    """Whether a plan change travels a declared gateway (rule 16).

    `module.plan.import` for source maps and units, `unit.map.import` for one
    study map, `route.patch` for descriptive material fields — recorded
    migrations are the one exception. A hand edit is never a faster version
    of this path. Fallback: unknown channels are hand edits.
    """
    return channel in CANONICAL_WRITE_CHANNELS


def workspace_may_coordinate(*, claim_kind: str) -> bool:
    """Whether a workspace may touch a claim (OPERATOR.md rule 6).

    Workspaces coordinate efforts through explicit id lists; they do not own
    the curriculum hierarchy. Fallback: unknown kinds do not coordinate.
    """
    if claim_kind in WORKSPACE_COORDINATION_KINDS:
        return True
    if claim_kind in WORKSPACE_OWNERSHIP_KINDS:
        return False
    return False


def _normalized_path(path: object) -> str | None:
    """A clean relative path, or None when it is malformed or external."""
    if not isinstance(path, str) or not path or "\\" in path or "\x00" in path:
        return None
    if path.startswith("/") or path.startswith("Stratum/") or path == "Stratum":
        return None
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return None
    return "/".join(parts)


def quarantine_excluded(*, path: str) -> bool:
    """Whether a path is excluded from normal loading and search (rule 4).

    Master's Planning lives quarantined and is represented only by a boundary
    record. Fallback: a malformed or external path is treated as excluded —
    nothing unreadable is ever routinely indexed.
    """
    normalized = _normalized_path(path)
    if normalized is None:
        return True
    return normalized == "curriculum/quarantine" \
        or normalized.startswith("curriculum/quarantine/")


def external_sibling(*, path: str) -> bool:
    """Whether a path reaches outside the repository (rule 3).

    `semestercontext/Stratum/` is an external sibling repository: LearningOS
    never indexes, validates, migrates, or manages it, and no query, build,
    validator, or AI action traverses it automatically.
    """
    if not isinstance(path, str) or not path:
        return True
    if path.startswith("/") or path == "Stratum" or path.startswith("Stratum/"):
        return True
    return any(part in {".."} for part in path.split("/"))


def relation_may_apply(
    *,
    relation_type: str,
    from_id: str,
    to_id: str,
    inferred: bool,
) -> bool:
    """Whether a concept relation may land without review.

    Types come from the closed vocabulary; endpoints are canonical concept
    ids; and no concept is ever inferred (ADR-015) — an inferred edge needs
    visible review first (OPERATOR.md rule 2). Fallback: anything malformed
    or inferred does not apply.
    """
    if inferred:
        return False
    return (
        relation_type in RELATION_TYPES
        and isinstance(from_id, str) and ID_RE.match(from_id) is not None
        and isinstance(to_id, str) and ID_RE.match(to_id) is not None
    )


def dossier_fresh(
    *,
    cached_hashes: Mapping[str, str],
    current_hashes: Mapping[str, str],
) -> bool:
    """Whether a cached context dossier still matches its dependencies.

    A dossier is keyed on its inputs' hashes; any dependency change
    invalidates it. Serving a dossier after a dependency changed is cache
    poisoning. Fallback: empty or malformed hash maps are never fresh.
    """
    if not isinstance(cached_hashes, Mapping) or not cached_hashes:
        return False
    if not isinstance(current_hashes, Mapping) or not current_hashes:
        return False
    try:
        return dict(cached_hashes) == dict(current_hashes)
    except (TypeError, ValueError):
        return False


def attempt_consistent(
    *,
    attempt_termins: Sequence[int],
    sitting_termins: Sequence[int],
) -> bool:
    """Whether recorded attempts match the module's sittings (rule 5).

    Administrative facts live in the owning module record, and an attempt
    that names no sitting is how a never-registered slot survives as if it
    were real. Every attempt termin must occur among the sittings.
    Fallback: malformed termin lists are inconsistent.
    """
    try:
        return set(attempt_termins) <= set(sitting_termins)
    except TypeError:
        return False


@dataclass(frozen=True)
class Predicate:
    """One named semantic judgment plus the metadata a consumer needs."""

    name: str
    version: int
    function: Callable[..., object]
    authoritative_inputs: tuple[str, ...]
    authority: str
    description: str


def _predicate(
    name: str,
    function: Callable[..., object],
    authoritative_inputs: tuple[str, ...],
    authority: str,
    description: str,
) -> Predicate:
    return Predicate(
        name=name,
        version=CONTRACT_VERSION,
        function=function,
        authoritative_inputs=authoritative_inputs,
        authority=authority,
        description=description,
    )


PREDICATES: Mapping[str, Predicate] = {
    "NeedsStudyMap": _predicate(
        "NeedsStudyMap", needs_study_map,
        ("unit_status", "module_status", "has_study_map"),
        "OPERATOR.md rule 6",
        "Every unit of an active or enrolled module owes a study map unless "
        "complete, archived, paused, or leaving active study.",
    ),
    "ScopeAuthority": _predicate(
        "ScopeAuthority", scope_authority,
        ("fact_kind", "module_id", "unit_id", "workspace_id", "note_id",
         "program_id", "source_id"),
        "OPERATOR.md boundaries 4-5",
        "Each fact kind has exactly one owning record; mirrors and "
        "quarantine are never authoritative.",
    ),
    "AllowedMutation": _predicate(
        "AllowedMutation", allowed_mutation,
        ("capability", "target_path", "scopes"),
        "system/contracts/capabilities.yaml",
        "A capability may write only inside its declared write scopes.",
    ),
    "ShelvingApproval": _predicate(
        "ShelvingApproval", shelving_approval,
        ("applied_items", "approved_items"),
        "OPERATOR.md rule 9",
        "Shelving applies only explicitly selected proposal items.",
    ),
    "CritiquePointActionable": _predicate(
        "CritiquePointActionable", critique_point_actionable,
        ("status", "authorized_in_session"),
        "system/CRITIQUE-POINTS.md rules 2-4",
        "An open point is deferred work, actionable only with Aram's "
        "explicit say-so in that session.",
    ),
    "MasteryDeclared": _predicate(
        "MasteryDeclared", mastery_declared,
        ("statement_kind",),
        "OPERATOR.md rule 10",
        "Report evidence or its absence; mastery is never declared.",
    ),
    "NoteChangeNeedsReview": _predicate(
        "NoteChangeNeedsReview", note_change_needs_review,
        ("change_kind",),
        "OPERATOR.md rule 2",
        "Semantic rewriting, identity changes, deletion, inferred relations, "
        "and pedagogical judgments require visible review.",
    ),
    "EvidenceComplete": _predicate(
        "EvidenceComplete", evidence_complete,
        ("entries",),
        "system/schema/note.schema.json",
        "A complete trail is present, well-formed, and append-only.",
    ),
    "ClaimStale": _predicate(
        "ClaimStale", claim_stale,
        ("read_contract_version", "current_contract_version",
         "read_revisions", "current_revisions"),
        "operations/transactions/revisions.yaml",
        "A claim read under an older contract or older revisions is stale.",
    ),
    "SourceComplete": _predicate(
        "SourceComplete", source_complete,
        ("selection_state", "locator_ok", "deferral_reason"),
        "OPERATOR.md rule 14",
        "Every named source is selected, reference-only, or deferred with a "
        "reason; silent omission fails.",
    ),
    "RouteValid": _predicate(
        "RouteValid", route_valid,
        ("route_id", "unit_id", "source_id", "locator"),
        "tools/learning_os/route_identity.py",
        "A route is addressable by id plus owning unit, source, and locator.",
    ),
    "RouteEvaluated": _predicate(
        "RouteEvaluated", route_evaluated,
        ("scope",),
        "system/schema/module-source-map.schema.json",
        "Unevaluated scope is visibility debt, not a verdict.",
    ),
    "StudyMapGrounded": _predicate(
        "StudyMapGrounded", study_map_grounded,
        ("template_version", "resource_pairs", "menu_pairs"),
        "OPERATOR.md unit workflow",
        "A study map projects over the complete menu; no row reaches outside.",
    ),
    "PlanTemplateCurrent": _predicate(
        "PlanTemplateCurrent", plan_template_current,
        ("template_version",),
        "OPERATOR.md rule 15",
        "New plans use the shared numbered-stage contract, version 1.",
    ),
    "RepoClean": _predicate(
        "RepoClean", repo_clean,
        ("error_count", "new_or_grown_warnings"),
        "OPERATOR.md 'clean'",
        "Zero errors and no new or grown warning signature.",
    ),
    "SnapshotFresh": _predicate(
        "SnapshotFresh", snapshot_fresh,
        ("expected_snapshot", "current_snapshot"),
        "OPERATOR.md rule 12",
        "On conflict, reload rather than overwrite.",
    ),
    "CanonicalWritePath": _predicate(
        "CanonicalWritePath", canonical_write_path,
        ("channel",),
        "OPERATOR.md rule 16",
        "Plans change only through declared gateways, never by hand edit.",
    ),
    "WorkspaceMayCoordinate": _predicate(
        "WorkspaceMayCoordinate", workspace_may_coordinate,
        ("claim_kind",),
        "OPERATOR.md rule 6",
        "Workspaces coordinate through id lists; they own no hierarchy.",
    ),
    "QuarantineExcluded": _predicate(
        "QuarantineExcluded", quarantine_excluded,
        ("path",),
        "OPERATOR.md rule 4",
        "Quarantined content is excluded from normal loading and search.",
    ),
    "ExternalSibling": _predicate(
        "ExternalSibling", external_sibling,
        ("path",),
        "OPERATOR.md rule 3",
        "Stratum is external; nothing traverses it automatically.",
    ),
    "RelationMayApply": _predicate(
        "RelationMayApply", relation_may_apply,
        ("relation_type", "from_id", "to_id", "inferred"),
        "ADR-015; OPERATOR.md rule 2",
        "Relations use the closed vocabulary over canonical ids; nothing "
        "inferred lands without review.",
    ),
    "DossierFresh": _predicate(
        "DossierFresh", dossier_fresh,
        ("cached_hashes", "current_hashes"),
        "Phase 5 dossier contract",
        "A cached dossier serves only while every dependency hash matches.",
    ),
    "AttemptConsistent": _predicate(
        "AttemptConsistent", attempt_consistent,
        ("attempt_termins", "sitting_termins"),
        "OPERATOR.md rule 5",
        "Every recorded attempt names a real sitting of its module.",
    ),
}


def evaluate(name: str, **inputs: object) -> object:
    """Evaluate one registered predicate by name; unknown names fail closed.

    Returns the predicate's native verdict (bool or the documented enum).
    """
    try:
        predicate = PREDICATES[name]
    except KeyError:
        raise KeyError(f"unknown semantic predicate: {name!r}") from None
    return predicate.function(**inputs)

"""Pytest plugin to transparently swap in the SQLite predicate evaluator.

Use:
    PYTHONPATH="tools:workbench/spikes/predicates-sqlite-2026-11-07" \
        .venv/bin/pytest -p spike_predicates_swap tests/test_semantic_contract.py ...

Swaps `evaluate` and all registered predicate functions in-process. Production files remain untouched.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SPIKE_DIR = Path(__file__).resolve().parent
_REPO = _SPIKE_DIR.parents[2]
for _p in (str(_REPO / "tools"), str(_SPIKE_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import learning_os.derive.semantics as _semantics  # noqa: E402
import learning_os.derive.semantics.predicates as _predicates  # noqa: E402
import spike_predicates_adapter as _adapter  # noqa: E402
from learning_os.derive.semantics.predicates import Predicate  # noqa: E402

# Wrap each individual predicate so calling the function directly also goes to SQL
_PREDICATE_NAME_MAP = {
    "needs_study_map": "NeedsStudyMap",
    "needs_scope": "NeedsScope",
    "scope_authority": "ScopeAuthority",
    "allowed_mutation": "AllowedMutation",
    "shelving_approval": "ShelvingApproval",
    "critique_point_actionable": "CritiquePointActionable",
    "mastery_declared": "MasteryDeclared",
    "note_change_needs_review": "NoteChangeNeedsReview",
    "evidence_complete": "EvidenceComplete",
    "claim_stale": "ClaimStale",
    "source_complete": "SourceComplete",
    "route_valid": "RouteValid",
    "route_evaluated": "RouteEvaluated",
    "study_map_grounded": "StudyMapGrounded",
    "plan_template_current": "PlanTemplateCurrent",
    "repo_clean": "RepoClean",
    "snapshot_fresh": "SnapshotFresh",
    "canonical_write_path": "CanonicalWritePath",
    "workspace_may_coordinate": "WorkspaceMayCoordinate",
    "quarantine_excluded": "QuarantineExcluded",
    "external_sibling": "ExternalSibling",
    "relation_may_apply": "RelationMayApply",
    "dossier_fresh": "DossierFresh",
    "attempt_consistent": "AttemptConsistent",
    "needs_source_review": "NeedsSourceReview",
    "requires_human_judgment": "RequiresHumanJudgment",
    "current_scope_authority": "CurrentScopeAuthority",
}


def _make_wrapper(pred_name: str):
    def _wrapper(**kwargs):
        return _adapter.evaluate_sql(pred_name, **kwargs)
    return _wrapper


# Rebind individual functions in predicates module
for fn_name, pred_name in _PREDICATE_NAME_MAP.items():
    wrapper = _make_wrapper(pred_name)
    if hasattr(_predicates, fn_name):
        setattr(_predicates, fn_name, wrapper)
    if hasattr(_semantics, fn_name):
        setattr(_semantics, fn_name, wrapper)

# Rebind evaluate()
setattr(_predicates, "evaluate", _adapter.evaluate_sql)
setattr(_semantics, "evaluate", _adapter.evaluate_sql)

# Rebind functions inside PREDICATES dict
_new_predicates = {}
for name, p in _predicates.PREDICATES.items():
    _new_predicates[name] = Predicate(
        name=p.name,
        version=p.version,
        function=_make_wrapper(name),
        authoritative_inputs=p.authoritative_inputs,
        authority=p.authority,
        description=p.description,
    )

# Mutate existing dict in place
_predicates.PREDICATES.clear()
_predicates.PREDICATES.update(_new_predicates)

# Global module rebinding
for m in list(sys.modules.values()):
    if m is not None and hasattr(m, "__dict__"):
        if getattr(m, "evaluate", None) is not None and m.__name__.startswith("learning_os"):
            setattr(m, "evaluate", _adapter.evaluate_sql)

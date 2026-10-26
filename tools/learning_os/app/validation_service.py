"""Validation orchestration over a loaded snapshot.

The status read path and the warning-baseline collection both run the
Validator (derive) and hand its issues to a store-tier owner: the static
validation cache and the warning-baseline signatures. They therefore sit
above both tiers; store keeps the persistence and derive keeps the rules.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING

from learning_os.derive.validation import validate
from learning_os.derive.validation.advisories import advisory_issues
from learning_os.domain.failures import TransactionFailure
from learning_os.domain.validation import Issue
from learning_os.store.derived.engine import BuildContext, evaluate
from learning_os.store.derived.model import DerivedError
from learning_os.store.derived.store import invalidate
from learning_os.store.loader import load_repo
from learning_os.store.validation_cache import VALIDATION_NODE_ID, observe_pins, write_static_cache
from learning_os.store.validation_cache import freeze_static as _freeze_static
from learning_os.store.validation_cache import restore_static as _restore_static
from learning_os.store.validation_cache import valid_static_value as _valid_static_value
from learning_os.store.validation_cache import validation_inputs as _validation_inputs
from learning_os.store.validation_cache import validation_spec as _validation_spec
from learning_os.store.warning_baseline import signatures_from_issues

if TYPE_CHECKING:
    from typing import Any

    from learning_os.domain.snapshot import Repo


def status_issues(repo: Repo, pins: dict[str, str] | None = None) -> list[Issue]:
    """Validation issues for `status`: cached static plus live advisories.

    On a key match the static issues are served from the derived node and
    only the clock-derived advisories are recomputed; on any miss the full
    validator runs (once) and its static issues memoize the node
    best-effort, under pins observed before it ran. Pass ``pins`` observed
    before ``repo`` was loaded; None observes them now. Unobservable pins
    or any cache-layer failure validates uncached, exactly as today: a
    cache problem never becomes stale data or a new refusal.
    """
    if pins is None:
        pins = observe_pins(repo.root)
    if pins is None:
        return validate(repo, online=False)
    try:
        inputs = _validation_inputs(pins)
    except DerivedError:
        return validate(repo, online=False)
    captured: list[Any] = []

    def _build(_ctx: BuildContext) -> Any:
        frozen = _freeze_static(validate(repo, online=False))
        captured.append(frozen)
        return frozen

    try:
        evaluation = evaluate(
            repo.root, VALIDATION_NODE_ID,
            registry={VALIDATION_NODE_ID: (_validation_spec(), _build)},
            inputs=inputs)
    except OSError:
        # The build may have succeeded before the store failed: serve its
        # result (one validation, best-effort memoize, as before) rather
        # than validating twice. Nothing captured means the failure came
        # before or inside the build itself, so validate uncached.
        if captured and _valid_static_value(captured[0]):
            return _restore_static(captured[0]) + advisory_issues(repo)
        return validate(repo, online=False)
    except (DerivedError, TransactionFailure, ValueError):
        return validate(repo, online=False)
    if not _valid_static_value(evaluation.value):
        try:
            invalidate(repo.root, VALIDATION_NODE_ID)
        except (OSError, TransactionFailure):
            pass
        issues = validate(repo, online=False)
        try:
            write_static_cache(repo.root, issues, pins)
        except OSError:
            pass
        return issues
    return _restore_static(evaluation.value) + advisory_issues(repo)


def collect(root: Path) -> tuple[Counter, list[str]]:
    """(signature counter, error strings) for the repository at ``root``."""
    return signatures_from_issues(validate(load_repo(root), online=False))


def diagnostic_report(root: Path) -> dict:
    """Typed diagnostic issues for preflight (D11): never authorization.

    Reuses the cached-static + live-advisory split; a failure to obtain a
    trustworthy result is reported, never read as clean.
    """
    try:
        from learning_os.store.loader import load_repo

        issues = status_issues(load_repo(root))
    except Exception as exc:  # noqa: BLE001 - typed refusal, not clean
        return {"ok": False, "trustworthy": False,
                "error": {"code": "PREFLIGHT_FAILED", "message": str(exc)}}
    errors = [{"code": i.code, "path": i.path, "message": i.message}
              for i in issues if i.severity == "error"]
    return {"ok": not errors, "trustworthy": True, "errors": errors,
            "issues": [{"code": i.code, "path": i.path} for i in issues]}

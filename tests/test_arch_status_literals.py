"""Architecture guard: curriculum status sets and retirement checks live in domain/curriculum/."""

from __future__ import annotations

import ast
from pathlib import Path

from learning_os.domain.curriculum.lifecycle import (
    MODULE_STATUSES,
    UNIT_STATUSES,
    WORKSPACE_STATUSES,
)
from learning_os.domain.curriculum.stages import (
    STAGE_STATUSES,
    STUDY_MAP_STATUSES,
)

ROOT = Path(__file__).resolve().parent.parent
LEARNING_OS_ROOT = ROOT / "tools" / "learning_os"
DOMAIN_CURRICULUM_PREFIX = "tools/learning_os/domain/curriculum/"

ALL_CURRICULUM_STATUSES = (
    frozenset(MODULE_STATUSES)
    | UNIT_STATUSES
    | STUDY_MAP_STATUSES
    | STAGE_STATUSES
    | WORKSPACE_STATUSES
)

#: Explicit allowlist of non-classification status-set sites outside
#: ``domain/curriculum/`` with exact value sets and reasons.
ALLOWED_STATUS_SETS: dict[tuple[str, frozenset[str]], str] = {
    (
        "tools/learning_os/app/admin/masters_planning.py",
        frozenset({"needs-map", "not-started", "ready"}),
    ): "quarantine promotion admission rule",
    (
        "tools/learning_os/app/handlers/learner.py",
        frozenset({"complete", "skipped"}),
    ): "stage-action precondition requiring active stage",
    (
        "tools/learning_os/derive/validation/curriculum.py",
        frozenset({"ready", "active"}),
    ): "check_lifecycle_coherence blocked-workspace validator rule",
}

RETIRED_LITERALS = frozenset({"dropped", "archived"})


def _string_collection(node: ast.AST) -> frozenset[str] | None:
    if isinstance(node, (ast.Set, ast.List, ast.Tuple)):
        elts = node.elts
    elif (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "frozenset"
        and len(node.args) == 1
        and isinstance(node.args[0], (ast.Set, ast.List, ast.Tuple))
    ):
        elts = node.args[0].elts
    else:
        return None

    values: list[str] = []
    for elem in elts:
        if isinstance(elem, ast.Constant) and isinstance(elem.value, str):
            values.append(elem.value)
        else:
            return None
    unique = frozenset(values)
    if len(unique) >= 2 and unique <= ALL_CURRICULUM_STATUSES:
        return unique
    return None


def _is_status_access(node: ast.AST) -> bool:
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "get"
        and node.args
        and isinstance(node.args[0], ast.Constant)
        and node.args[0].value == "status"
    ):
        return True
    if (
        isinstance(node, ast.Subscript)
        and isinstance(node.slice, ast.Constant)
        and node.slice.value == "status"
    ):
        return True
    return False


def _retired_values(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return {node.value} if node.value in RETIRED_LITERALS else set()
    if isinstance(node, (ast.Set, ast.List, ast.Tuple)):
        found: set[str] = set()
        for elem in node.elts:
            if isinstance(elem, ast.Constant) and isinstance(elem.value, str):
                if elem.value in RETIRED_LITERALS:
                    found.add(elem.value)
        return found
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "frozenset"
        and len(node.args) == 1
    ):
        return _retired_values(node.args[0])
    return set()


def test_no_unallowlisted_curriculum_status_literals_outside_domain() -> None:
    violations: list[str] = []
    seen_allowlist: set[tuple[str, frozenset[str]]] = set()

    for path in sorted(LEARNING_OS_ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith(DOMAIN_CURRICULUM_PREFIX):
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
        # Track inner collection nodes inside frozenset(...) calls so one
        # expression is checked once rather than twice.
        frozenset_inners: set[int] = set()
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "frozenset"
                and len(node.args) == 1
                and isinstance(node.args[0], (ast.Set, ast.List, ast.Tuple))
            ):
                frozenset_inners.add(id(node.args[0]))

        for node in ast.walk(tree):
            if id(node) not in frozenset_inners:
                values = _string_collection(node)
                if values is not None:
                    key = (rel, values)
                    if key in ALLOWED_STATUS_SETS:
                        seen_allowlist.add(key)
                    else:
                        violations.append(
                            f"{rel}:{getattr(node, 'lineno', '?')}: "
                            f"ad-hoc curriculum status literal {sorted(values)} "
                            "(import from domain/curriculum/ instead)"
                        )

            if isinstance(node, ast.Compare):
                terms = [node.left, *node.comparators]
                if any(_is_status_access(term) for term in terms):
                    for term in terms:
                        retired = _retired_values(term)
                        if retired:
                            violations.append(
                                f"{rel}:{node.lineno}: "
                                f"status compared against retired literal {sorted(retired)} "
                                f"in `{ast.unparse(node)}` (use domain/curriculum/lifecycle.is_retired)"
                            )

    stale = sorted(
        (rel, sorted(values))
        for key in (set(ALLOWED_STATUS_SETS) - seen_allowlist)
        for rel, values in [key]
    )
    assert not violations, "\n".join(violations)
    assert not stale, f"stale allowlist entries: {stale}"

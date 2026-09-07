#!/usr/bin/env python3
"""Persist stable rich-route ids and exact selection references for v13.

The default is a no-write dry run.  The migration only inspects the canonical
curriculum paths named below, emits line-preserving insertions, and refuses the
entire apply when a learner selection has zero or multiple exact route matches.
It never guesses from a title, priority, or source alone.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from yaml.constructor import ConstructorError
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode
from yaml.resolver import BaseResolver

from learning_os.contracts.migration_lifecycle import (
    refuse_retired_apply,
    retired_migration,
)
from learning_os.fingerprint import canonical_fingerprint
from learning_os.routes import ROUTE_ID_RE, deterministic_route_id

REVIEW_SCHEMA_VERSION = 1
REVIEW_ACTIONS = frozenset({
    "add-route",
    "bind-route",
    "preserve-unresolved",
    "retire-selection",
    "revise-selection-guard",
    "split-selection",
})
EXECUTABLE_REVIEW_ACTIONS = frozenset({
    "bind-route",
    "retire-selection",
    "revise-selection-guard",
    "split-selection",
})


@dataclass(frozen=True)
class RouteRow:
    route_id: str
    module_id: str
    unit_id: str
    source_id: str
    locator: str
    path: Path


@dataclass(frozen=True)
class Problem:
    code: str
    path: Path
    detail: str


@dataclass(frozen=True)
class FileChange:
    path: Path
    before: str
    after: str


@dataclass(frozen=True)
class SelectionIssue:
    path: Path
    selection_index: int
    unit_id: str
    source_id: str
    locator: str
    code: str
    detail: str


@dataclass(frozen=True)
class ReviewResolution:
    action: str
    routes: tuple[RouteRow, ...]


try:
    # ⚡ Bolt: Use C-based loader for ~6x faster YAML parsing.
    from yaml import CSafeLoader as _SafeLoader
except ImportError:
    from yaml import SafeLoader as _SafeLoader

class _UniqueKeyLoader(_SafeLoader):
    """Load a review ledger without silently overwriting duplicate keys."""


def _construct_unique_mapping(
    loader: _UniqueKeyLoader,
    node: MappingNode,
    deep: bool = False,
) -> dict:
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as exc:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                "found an unhashable key",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(
    BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


@dataclass(frozen=True)
class MigrationPlan:
    root: Path
    routes: tuple[RouteRow, ...]
    changes: tuple[FileChange, ...]
    problems: tuple[Problem, ...]

    @property
    def ready(self) -> bool:
        return not self.problems

    def as_dict(self) -> dict:
        return {
            "migration": "route-identity-v13",
            "ready": self.ready,
            "routes": len(self.routes),
            "plan_sha256": plan_sha256(self),
            "changed_files": [
                change.path.relative_to(self.root).as_posix()
                for change in self.changes
            ],
            "problems": [
                {
                    "code": problem.code,
                    "path": problem.path.relative_to(self.root).as_posix(),
                    "detail": problem.detail,
                }
                for problem in self.problems
            ],
        }


def _mapping_value(node: Node | None, key: str) -> Node | None:
    if not isinstance(node, MappingNode):
        return None
    for key_node, value_node in node.value:
        if isinstance(key_node, ScalarNode) and key_node.value == key:
            return value_node
    return None


def _read_mapping(path: Path) -> tuple[str, dict, MappingNode | None, list[Problem]]:
    try:
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
        node = yaml.compose(text)
    except (OSError, yaml.YAMLError) as exc:
        return "", {}, None, [Problem("unreadable-yaml", path, str(exc))]
    if not isinstance(data, dict) or not isinstance(node, MappingNode):
        return text, {}, None, [
            Problem("invalid-document", path, "expected one YAML mapping")
        ]
    return text, data, node, []


def _mapping_insertion(
    text: str,
    node: MappingNode,
    key: str,
    value: str,
    *,
    path: Path,
) -> tuple[int, str] | Problem:
    if node.flow_style:
        return Problem(
            "unsupported-yaml-style",
            path,
            f"cannot line-preservingly add {key} to a flow-style mapping",
        )
    lines = text.splitlines(keepends=True)
    line_index = node.start_mark.line
    if line_index >= len(lines):
        return Problem("invalid-yaml-location", path, f"cannot locate {key} insertion")
    match = re.match(r"^(\s*)-\s+", lines[line_index])
    if match is None:
        return Problem(
            "unsupported-yaml-style",
            path,
            f"expected a block sequence item before {key}",
        )
    return line_index, f"{match.group(1)}  {key}: {value}\n"


def _apply_insertions(text: str, insertions: list[tuple[int, str]]) -> str:
    lines = text.splitlines(keepends=True)
    for line_index, addition in sorted(insertions, reverse=True):
        lines.insert(line_index + 1, addition)
    return "".join(lines)


def _item_bounds(text: str, node: MappingNode) -> tuple[int, int]:
    """Return the exact full-line span of one block sequence mapping."""

    lines = text.splitlines(keepends=True)
    start = sum(len(line) for line in lines[:node.start_mark.line])
    return start, node.end_mark.index


def _apply_text_edits(
    text: str,
    edits: list[tuple[int, int, str]],
    *,
    path: Path,
) -> tuple[str, list[Problem]]:
    """Apply non-overlapping, already-bounded edits from right to left."""

    out = text
    previous_start = len(text) + 1
    for start, end, replacement in sorted(edits, reverse=True):
        if start < 0 or end < start or end > len(text) or end > previous_start:
            return text, [Problem(
                "overlapping-review-edit",
                path,
                "review decisions did not resolve to disjoint YAML selection blocks",
            )]
        out = out[:start] + replacement + out[end:]
        previous_start = start
    return out, []


def _insertion_edit(
    text: str,
    node: MappingNode,
    key: str,
    value: str,
    *,
    path: Path,
) -> tuple[int, int, str] | Problem:
    insertion = _mapping_insertion(text, node, key, value, path=path)
    if isinstance(insertion, Problem):
        return insertion
    line_index, addition = insertion
    lines = text.splitlines(keepends=True)
    offset = sum(len(line) for line in lines[:line_index + 1])
    return offset, offset, addition


def _yaml_scalar(value: str) -> str:
    """Render one unambiguous YAML string without reformatting its mapping."""

    return json.dumps(value, ensure_ascii=False)


def _reviewed_selection_block(
    text: str,
    node: MappingNode,
    route: RouteRow,
    *,
    revise_guards: bool,
    path: Path,
) -> tuple[str, list[Problem]]:
    """Clone one exact selection block and bind it to one reviewed route."""

    start, end = _item_bounds(text, node)
    block = text[start:end]
    edits: list[tuple[int, int, str]] = []
    fields = {key.value: value for key, value in node.value
              if isinstance(key, ScalarNode)}
    if revise_guards:
        for key, value in (("source_id", route.source_id), ("locator", route.locator)):
            value_node = fields.get(key)
            if not isinstance(value_node, ScalarNode):
                return block, [Problem(
                    "review-selection-shape",
                    path,
                    f"cannot revise selection without scalar {key}",
                )]
            edits.append((
                value_node.start_mark.index - start,
                value_node.end_mark.index - start,
                _yaml_scalar(value),
            ))

    route_node = fields.get("route_id")
    if isinstance(route_node, ScalarNode):
        edits.append((
            route_node.start_mark.index - start,
            route_node.end_mark.index - start,
            route.route_id,
        ))
    elif route_node is not None:
        return block, [Problem(
            "review-selection-shape",
            path,
            "cannot replace a non-scalar selection route_id",
        )]
    else:
        first_line_end = block.find("\n")
        if first_line_end < 0:
            return block, [Problem(
                "unsupported-yaml-style",
                path,
                "cannot add route_id to a selection without a complete block line",
            )]
        first_line = block[:first_line_end + 1]
        match = re.match(r"^(\s*)-\s+", first_line)
        if match is None:
            return block, [Problem(
                "unsupported-yaml-style",
                path,
                "expected a block sequence item before route_id",
            )]
        edits.append((
            first_line_end + 1,
            first_line_end + 1,
            f"{match.group(1)}  route_id: {route.route_id}\n",
        ))
    return _apply_text_edits(block, edits, path=path)


def _plan_source_map(path: Path) -> tuple[list[RouteRow], FileChange | None, list[Problem]]:
    text, data, node, problems = _read_mapping(path)
    if problems or node is None:
        return [], None, problems
    module_id = data.get("module_id")
    sources = data.get("sources")
    source_nodes = _mapping_value(node, "sources")
    if not isinstance(module_id, str) or not isinstance(sources, list) \
            or not isinstance(source_nodes, SequenceNode):
        return [], None, [
            Problem("invalid-source-map", path, "module_id and sources are required")
        ]

    rows: list[RouteRow] = []
    insertions: list[tuple[int, str]] = []
    for entry, entry_node in zip(sources, source_nodes.value, strict=False):
        if not isinstance(entry, dict) or not isinstance(entry_node, MappingNode):
            continue
        source_id = entry.get("source_id")
        routes = entry.get("unit_routes", []) or []
        route_nodes = _mapping_value(entry_node, "unit_routes")
        if not isinstance(source_id, str) or not isinstance(routes, list):
            continue
        if not isinstance(route_nodes, SequenceNode):
            if routes:
                problems.append(
                    Problem("invalid-route-list", path, f"source '{source_id}' routes are not a sequence")
                )
            continue
        for route, route_node in zip(routes, route_nodes.value, strict=False):
            if not isinstance(route, dict) or not isinstance(route_node, MappingNode):
                # Legacy string routes intentionally remain readable and unchanged.
                continue
            route_id = route.get("id")
            if not isinstance(route_id, str) or not route_id:
                route_id = deterministic_route_id(module_id, source_id, route)
                insertion = _mapping_insertion(
                    text, route_node, "id", route_id, path=path
                )
                if isinstance(insertion, Problem):
                    problems.append(insertion)
                else:
                    insertions.append(insertion)
            elif ROUTE_ID_RE.fullmatch(route_id) is None:
                problems.append(
                    Problem("invalid-route-id", path, f"invalid route id '{route_id}'")
                )
            rows.append(RouteRow(
                route_id=route_id,
                module_id=module_id,
                unit_id=str(route.get("unit_id") or ""),
                source_id=source_id,
                locator=str(route.get("locator") or ""),
                path=path,
            ))
    after = _apply_insertions(text, insertions)
    change = FileChange(path, text, after) if after != text else None
    return rows, change, problems


def _plan_unit(
    path: Path,
    routes: list[RouteRow],
    resolutions: dict[int, ReviewResolution] | None = None,
) -> tuple[FileChange | None, list[Problem], list[SelectionIssue]]:
    text, data, node, problems = _read_mapping(path)
    if problems or node is None:
        return None, problems, []
    unit_id = data.get("id")
    selections = data.get("source_selections", []) or []
    selection_nodes = _mapping_value(node, "source_selections")
    if not isinstance(unit_id, str) or not isinstance(selections, list):
        return None, [Problem(
            "invalid-unit", path, "id and source_selections are required"
        )], []
    if not selections:
        return None, [], []
    if not isinstance(selection_nodes, SequenceNode):
        return None, [Problem(
            "invalid-selection-list", path, "source_selections is not a sequence"
        )], []

    edits: list[tuple[int, int, str]] = []
    issues: list[SelectionIssue] = []
    routes_by_id: dict[str, list[RouteRow]] = {}
    for route in routes:
        routes_by_id.setdefault(route.route_id, []).append(route)
    for selection_index, (selection, selection_node) in enumerate(zip(
        selections, selection_nodes.value, strict=False,
    )):
        if not isinstance(selection, dict) or not isinstance(
            selection_node, MappingNode
        ):
            problems.append(Problem(
                "invalid-selection", path, "selection must be a block mapping"
            ))
            continue
        route_id = selection.get("route_id")
        source_id = selection.get("source_id")
        locator = selection.get("locator")
        issue_code: str | None = None
        issue_detail = ""
        if isinstance(route_id, str) and route_id:
            candidates = routes_by_id.get(route_id, [])
            if len(candidates) != 1:
                issue_code = "selection-route-id-unresolved"
                issue_detail = (
                    f"selection route_id '{route_id}' resolves {len(candidates)} routes"
                )
            else:
                candidate = candidates[0]
                if (
                    candidate.unit_id != unit_id
                    or candidate.source_id != source_id
                    or candidate.locator != locator
                ):
                    issue_code = "selection-guard-mismatch"
                    issue_detail = (
                        f"selection route_id '{route_id}' disagrees with "
                        "unit/source/locator guards"
                    )
        else:
            candidates = [
                route for route in routes
                if route.unit_id == unit_id
                and route.source_id == source_id
                and route.locator == locator
            ]
            if len(candidates) != 1:
                issue_code = (
                    "selection-unmatched" if not candidates
                    else "selection-ambiguous"
                )
                issue_detail = (
                    f"selection {source_id!r} / {locator!r} resolves "
                    f"{len(candidates)} rich routes"
                )
            else:
                insertion = _insertion_edit(
                    text,
                    selection_node,
                    "route_id",
                    candidates[0].route_id,
                    path=path,
                )
                if isinstance(insertion, Problem):
                    problems.append(insertion)
                else:
                    edits.append(insertion)

        if issue_code is None:
            continue
        if not isinstance(source_id, str) or not isinstance(locator, str):
            problems.append(Problem(issue_code, path, issue_detail))
            problems.append(Problem(
                "review-selection-shape",
                path,
                f"selection {selection_index} needs scalar source_id and locator guards",
            ))
            continue
        issue = SelectionIssue(
            path=path,
            selection_index=selection_index,
            unit_id=unit_id,
            source_id=source_id,
            locator=locator,
            code=issue_code,
            detail=issue_detail,
        )
        issues.append(issue)
        resolution = (resolutions or {}).get(selection_index)
        if resolution is None:
            problems.append(Problem(issue.code, path, issue.detail))
            continue
        if resolution.action not in EXECUTABLE_REVIEW_ACTIONS:
            problems.append(Problem(
                "review-action-blocked",
                path,
                f"selection {selection_index} remains blocked by "
                f"'{resolution.action}'",
            ))
            continue

        start, end = _item_bounds(text, selection_node)
        if resolution.action == "retire-selection":
            edits.append((start, end, ""))
            continue

        blocks: list[str] = []
        block_failed = False
        revise_guards = resolution.action in {
            "revise-selection-guard", "split-selection",
        }
        for route in resolution.routes:
            block, block_problems = _reviewed_selection_block(
                text,
                selection_node,
                route,
                revise_guards=revise_guards,
                path=path,
            )
            problems.extend(block_problems)
            block_failed = block_failed or bool(block_problems)
            blocks.append(block)
        if not block_failed:
            edits.append((start, end, "".join(blocks)))

    after, edit_problems = _apply_text_edits(text, edits, path=path)
    problems.extend(edit_problems)
    return (
        FileChange(path, text, after) if after != text else None,
        problems,
        issues,
    )


def _migration_plan(
    root: Path,
    routes: list[RouteRow],
    changes: list[FileChange],
    problems: list[Problem],
) -> MigrationPlan:
    return MigrationPlan(
        root=root,
        routes=tuple(routes),
        changes=tuple(sorted(changes, key=lambda item: item.path.as_posix())),
        problems=tuple(sorted(
            problems,
            key=lambda item: (item.path.as_posix(), item.code, item.detail),
        )),
    )


def _baseline_plan(
    root: Path,
) -> tuple[
    MigrationPlan,
    list[RouteRow],
    list[FileChange],
    list[Problem],
    list[Path],
    list[SelectionIssue],
]:
    routes: list[RouteRow] = []
    source_changes: list[FileChange] = []
    source_map_paths, unit_paths, global_problems = _bounded_curriculum_files(root)
    for path in source_map_paths:
        found, change, found_problems = _plan_source_map(path)
        routes.extend(found)
        global_problems.extend(found_problems)
        if change:
            source_changes.append(change)

    by_id: dict[str, list[RouteRow]] = {}
    for route in routes:
        by_id.setdefault(route.route_id, []).append(route)
    for route_id, matches in sorted(by_id.items()):
        if len(matches) > 1:
            global_problems.append(Problem(
                "duplicate-route-id",
                matches[0].path,
                f"route id '{route_id}' resolves {len(matches)} rich routes",
            ))

    unit_changes: list[FileChange] = []
    unit_problems: list[Problem] = []
    issues: list[SelectionIssue] = []
    for path in unit_paths:
        change, found_problems, found_issues = _plan_unit(path, routes)
        unit_problems.extend(found_problems)
        issues.extend(found_issues)
        if change:
            unit_changes.append(change)
    baseline = _migration_plan(
        root,
        routes,
        [*source_changes, *unit_changes],
        [*global_problems, *unit_problems],
    )
    return (
        baseline,
        routes,
        source_changes,
        global_problems,
        unit_paths,
        issues,
    )


def _review_problem(
    root: Path,
    code: str,
    detail: str,
    *,
    path: Path | None = None,
) -> Problem:
    return Problem(code, path or root / "curriculum", detail)


def _valid_review_path(value: str) -> bool:
    return re.fullmatch(
        r"curriculum/modules/[^/.][^/]*/units/[^/.][^/]*/unit\.yaml",
        value,
    ) is not None and "\\" not in value


def _validate_review(
    root: Path,
    review: Any,
    baseline: MigrationPlan,
    routes: list[RouteRow],
    issues: list[SelectionIssue],
) -> tuple[dict[Path, dict[int, ReviewResolution]], list[Problem]]:
    problems: list[Problem] = []
    required_review_fields = {
        "schema_version",
        "basis_plan_sha256",
        "basis_snapshot_sha256",
        "decisions",
    }
    if not isinstance(review, dict) or set(review) != required_review_fields:
        return {}, [_review_problem(
            root,
            "review-malformed",
            "review must contain exactly schema_version, basis_plan_sha256, "
            "basis_snapshot_sha256, and decisions",
        )]
    if type(review.get("schema_version")) is not int \
            or review["schema_version"] != REVIEW_SCHEMA_VERSION:
        problems.append(_review_problem(
            root,
            "review-malformed",
            f"review schema_version must be {REVIEW_SCHEMA_VERSION}",
        ))

    expected_plan = plan_sha256(baseline)
    basis_plan = review.get("basis_plan_sha256")
    if not isinstance(basis_plan, str) \
            or re.fullmatch(r"sha256:[a-f0-9]{64}", basis_plan) is None:
        problems.append(_review_problem(
            root, "review-malformed", "basis_plan_sha256 must be one SHA-256 digest",
        ))
    elif basis_plan != expected_plan:
        problems.append(_review_problem(
            root,
            "review-basis-plan-drift",
            f"review was based on plan {basis_plan}, current baseline is {expected_plan}",
        ))

    expected_snapshot = f"sha256:{canonical_fingerprint(root)}"
    basis_snapshot = review.get("basis_snapshot_sha256")
    if not isinstance(basis_snapshot, str) \
            or re.fullmatch(r"sha256:[a-f0-9]{64}", basis_snapshot) is None:
        problems.append(_review_problem(
            root,
            "review-malformed",
            "basis_snapshot_sha256 must be one SHA-256 digest",
        ))
    elif basis_snapshot != expected_snapshot:
        problems.append(_review_problem(
            root,
            "review-basis-snapshot-drift",
            f"review was based on snapshot {basis_snapshot}, current snapshot is "
            f"{expected_snapshot}",
        ))

    decisions = review.get("decisions")
    if not isinstance(decisions, dict):
        problems.append(_review_problem(
            root,
            "review-malformed",
            "review decisions must be an object keyed by R### review id",
        ))
        return {}, problems

    issues_by_key = {
        (issue.path.relative_to(root).as_posix(), issue.selection_index): issue
        for issue in issues
    }
    routes_by_id: dict[str, list[RouteRow]] = {}
    for route in routes:
        routes_by_id.setdefault(route.route_id, []).append(route)

    required_decision_fields = {
        "unit_path",
        "selection_index",
        "expected_source_id",
        "expected_locator",
        "action",
        "route_ids",
        "rationale",
    }
    seen_keys: set[tuple[str, int]] = set()
    resolutions: dict[Path, dict[int, ReviewResolution]] = {}
    for review_id, decision in sorted(
        decisions.items(),
        key=lambda item: str(item[0]),
    ):
        label = f"decision {review_id}"
        if not isinstance(review_id, str) \
                or re.fullmatch(r"R[0-9]{3}", review_id) is None:
            problems.append(_review_problem(
                root,
                "review-malformed-decision",
                "review decision ids must use the R### form",
            ))
            continue
        if not isinstance(decision, dict) or set(decision) != required_decision_fields:
            problems.append(_review_problem(
                root,
                "review-malformed-decision",
                f"{label} must contain exactly the declared review decision fields",
            ))
            continue
        unit_path = decision.get("unit_path")
        selection_index = decision.get("selection_index")
        expected_source_id = decision.get("expected_source_id")
        expected_locator = decision.get("expected_locator")
        action = decision.get("action")
        route_ids = decision.get("route_ids")
        rationale = decision.get("rationale")
        if not isinstance(unit_path, str) or not _valid_review_path(unit_path) \
                or type(selection_index) is not int or selection_index < 0:
            problems.append(_review_problem(
                root,
                "review-malformed-decision",
                f"{label} needs a bounded canonical unit_path and nonnegative index",
            ))
            continue
        key = (unit_path, selection_index)
        issue = issues_by_key.get(key)
        problem_path = issue.path if issue else root / "curriculum"
        if key in seen_keys:
            problems.append(_review_problem(
                root,
                "review-duplicate-decision",
                f"multiple decisions target {unit_path} selection {selection_index}",
                path=problem_path,
            ))
            continue
        seen_keys.add(key)
        if issue is None:
            problems.append(_review_problem(
                root,
                "review-unused-decision",
                f"{unit_path} selection {selection_index} is not an unresolved baseline selection",
                path=problem_path,
            ))
            continue
        if not isinstance(expected_source_id, str) \
                or not isinstance(expected_locator, str) \
                or expected_source_id != issue.source_id \
                or expected_locator != issue.locator:
            problems.append(_review_problem(
                root,
                "review-selection-drift",
                f"{unit_path} selection {selection_index} no longer has the reviewed "
                "source_id/locator guards",
                path=issue.path,
            ))
            continue
        if not isinstance(rationale, str) or not rationale.strip():
            problems.append(_review_problem(
                root,
                "review-malformed-decision",
                f"{label} requires a nonempty rationale",
                path=issue.path,
            ))
            continue
        if not isinstance(action, str) or action not in REVIEW_ACTIONS:
            problems.append(_review_problem(
                root,
                "review-unknown-action",
                f"{label} has unsupported action {action!r}",
                path=issue.path,
            ))
            continue
        if not isinstance(route_ids, list) \
                or not all(isinstance(route_id, str) for route_id in route_ids):
            problems.append(_review_problem(
                root,
                "review-malformed-decision",
                f"{label} route_ids must be an array of route-id strings",
                path=issue.path,
            ))
            continue
        if len(set(route_ids)) != len(route_ids):
            problems.append(_review_problem(
                root,
                "review-duplicate-route",
                f"{label} repeats a selected route id",
                path=issue.path,
            ))
            continue

        cardinality_ok = (
            action in {"bind-route", "revise-selection-guard"}
            and len(route_ids) == 1
        ) or (action == "split-selection" and len(route_ids) >= 2) \
            or (action in {
                "add-route", "preserve-unresolved", "retire-selection",
            } and not route_ids)
        if not cardinality_ok:
            problems.append(_review_problem(
                root,
                "review-route-cardinality",
                f"{label} has invalid route count for action '{action}'",
                path=issue.path,
            ))
            continue

        chosen: list[RouteRow] = []
        route_failed = False
        for route_id in route_ids:
            matches = routes_by_id.get(route_id, [])
            if len(matches) != 1:
                problems.append(_review_problem(
                    root,
                    "review-route-unresolved",
                    f"{label} route_id '{route_id}' resolves {len(matches)} rich routes",
                    path=issue.path,
                ))
                route_failed = True
                continue
            route = matches[0]
            if route.unit_id != issue.unit_id:
                problems.append(_review_problem(
                    root,
                    "review-route-unit-mismatch",
                    f"{label} route_id '{route_id}' belongs to unit '{route.unit_id}'",
                    path=issue.path,
                ))
                route_failed = True
            if route.source_id != issue.source_id:
                problems.append(_review_problem(
                    root,
                    "review-route-source-mismatch",
                    f"{label} route_id '{route_id}' belongs to source "
                    f"'{route.source_id}'",
                    path=issue.path,
                ))
                route_failed = True
            if not route.locator:
                problems.append(_review_problem(
                    root,
                    "review-route-locator-missing",
                    f"{label} route_id '{route_id}' has no exact locator",
                    path=issue.path,
                ))
                route_failed = True
            chosen.append(route)
        if action == "bind-route" and chosen and chosen[0].locator != issue.locator:
            problems.append(_review_problem(
                root,
                "review-bind-guard-mismatch",
                f"{label} must use revise-selection-guard when the exact locator changes",
                path=issue.path,
            ))
            route_failed = True
        if route_failed:
            continue
        resolutions.setdefault(issue.path, {})[selection_index] = ReviewResolution(
            action=action,
            routes=tuple(chosen),
        )

    for key, issue in sorted(issues_by_key.items()):
        if key not in seen_keys:
            problems.append(_review_problem(
                root,
                "review-missing-decision",
                f"no decision covers {key[0]} selection {key[1]}",
                path=issue.path,
            ))
    return resolutions, problems


def plan_migration(root: Path, review: dict | None = None) -> MigrationPlan:
    root = root.resolve()
    (
        baseline,
        routes,
        source_changes,
        global_problems,
        unit_paths,
        issues,
    ) = _baseline_plan(root)
    if review is None:
        return baseline

    resolutions, review_problems = _validate_review(
        root, review, baseline, routes, issues,
    )
    if review_problems:
        return _migration_plan(
            root,
            routes,
            list(baseline.changes),
            [*baseline.problems, *review_problems],
        )

    changes = list(source_changes)
    problems = list(global_problems)
    for path in unit_paths:
        change, found_problems, _ = _plan_unit(
            path, routes, resolutions.get(path, {}),
        )
        problems.extend(found_problems)
        if change:
            changes.append(change)
    return _migration_plan(root, routes, changes, problems)


def render_diffs(plan: MigrationPlan) -> str:
    chunks = []
    for change in plan.changes:
        relative = change.path.relative_to(plan.root).as_posix()
        chunks.extend(difflib.unified_diff(
            change.before.splitlines(keepends=True),
            change.after.splitlines(keepends=True),
            fromfile=f"a/{relative}",
            tofile=f"b/{relative}",
        ))
    return "".join(chunks)


def plan_sha256(plan: MigrationPlan) -> str:
    """Hash the exact unified diff presented for approval."""

    return "sha256:" + hashlib.sha256(render_diffs(plan).encode("utf-8")).hexdigest()


def _bounded_curriculum_files(
    root: Path,
) -> tuple[list[Path], list[Path], list[Problem]]:
    """Enumerate only direct module/unit files without traversing symlinks."""
    problems: list[Problem] = []
    curriculum = root / "curriculum"
    modules = curriculum / "modules"
    for directory in (curriculum, modules):
        if directory.is_symlink():
            return [], [], [Problem(
                "unsafe-symlink-path",
                directory,
                "route migration refuses a symlinked curriculum authority",
            )]
        if not directory.is_dir():
            return [], [], problems

    source_maps: list[Path] = []
    units: list[Path] = []
    try:
        module_entries = sorted(modules.iterdir())
    except OSError as exc:
        return [], [], [Problem("unreadable-directory", modules, str(exc))]
    for module_dir in module_entries:
        if module_dir.is_symlink():
            problems.append(Problem(
                "unsafe-symlink-path",
                module_dir,
                "route migration refuses a symlinked module directory",
            ))
            continue
        if not module_dir.is_dir():
            continue
        source_map = module_dir / "source-map.yaml"
        if source_map.is_symlink():
            problems.append(Problem(
                "unsafe-symlink-path",
                source_map,
                "route migration refuses a symlinked source map",
            ))
        elif source_map.is_file():
            source_maps.append(source_map)

        unit_root = module_dir / "units"
        if unit_root.is_symlink():
            problems.append(Problem(
                "unsafe-symlink-path",
                unit_root,
                "route migration refuses a symlinked unit directory",
            ))
            continue
        if not unit_root.is_dir():
            continue
        try:
            unit_entries = sorted(unit_root.iterdir())
        except OSError as exc:
            problems.append(Problem("unreadable-directory", unit_root, str(exc)))
            continue
        for unit_dir in unit_entries:
            if unit_dir.is_symlink():
                problems.append(Problem(
                    "unsafe-symlink-path",
                    unit_dir,
                    "route migration refuses a symlinked unit directory",
                ))
                continue
            if not unit_dir.is_dir():
                continue
            unit_file = unit_dir / "unit.yaml"
            if unit_file.is_symlink():
                problems.append(Problem(
                    "unsafe-symlink-path",
                    unit_file,
                    "route migration refuses a symlinked unit record",
                ))
            elif unit_file.is_file():
                units.append(unit_file)
    return source_maps, units, problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--diff", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--review-file",
        type=Path,
        help="YAML or JSON review ledger to validate in this no-write plan",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    retired = retired_migration(
        root,
        "route-identity-v13",
        supported_through=13,
    )
    if refuse_retired_apply(retired, apply=args.apply):
        return 2 if args.apply else 0

    review = None
    if args.review_file is not None:
        try:
            review = yaml.load(
                args.review_file.read_text(encoding="utf-8"),
                Loader=_UniqueKeyLoader,
            )
        except (OSError, yaml.YAMLError) as exc:
            print(f"invalid route review file: {exc}")
            return 2
    plan = plan_migration(root, review=review)
    if args.json:
        print(json.dumps(plan.as_dict(), indent=2, sort_keys=True))
    else:
        status = "ready" if plan.ready else "blocked"
        print(
            f"route-identity-v13: {status}; {len(plan.routes)} rich routes; "
            f"{len(plan.changes)} changed files; {len(plan.problems)} problem(s); "
            f"plan {plan_sha256(plan)}"
        )
        for problem in plan.problems:
            relative = problem.path.relative_to(root).as_posix()
            print(f"{problem.code}: {relative}: {problem.detail}")
    if args.diff:
        print(render_diffs(plan), end="")
    if args.apply:
        print(
            "refusing direct --apply: use the approval-bound "
            "route.identity.migrate GatewayEnvelopeV2 capability"
        )
        return 2
    return 1 if plan.changes or plan.problems else 0


if __name__ == "__main__":
    raise SystemExit(main())

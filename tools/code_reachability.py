#!/usr/bin/env python3
"""Verify static reachability and dependency direction for Core tool modules.

This is a code-only architecture gate.  It parses imports without importing
LearningOS, loading canonical records, reading materials, or executing module
top-level code.  "Reachable" therefore means only "connected to a declared
Python entrypoint by syntax-visible imports"; it is not a runtime coverage or
lazy-import claim.
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parent

# Every supported top-level Python command is named here.  A new tools/*.py is
# deliberately a gate failure until its lifecycle is classified in this list
# and in tools/README.md.
ENTRYPOINTS = (
    "assemble_lecture_study_maps.py",
    "build_materials_index.py",
    "build_materials_tree.py",
    "code_reachability.py",
    "codex_obsidian.py",
    "generate.py",
    "generate_capability_schemas.py",
    "legacy_exit_review.py",
    "lift_angle_out_of_locator.py",
    "los.py",
    "manifest_contract.py",
    "material_toc.py",
    "materials_manifest.py",
    "normalise_material_uris.py",
    "plan_write_audit.py",
    "refresh_amls_fixture.py",
    "release_pair_receipt.py",
    "schema_contract.py",
    "stress_check.py",
    "validate.py",
    "warning_baseline.py",
)

# These are the code trees whose module reachability this gate owns.  Tests are
# consumers and are intentionally not roots: production code used only by a
# test remains visible as unreachable production code.
PACKAGE_ROOTS: Mapping[str, str] = {
    "learning_os": "learning_os",
    "materials_index": "materials_index",
    "migrations": "migrations",
}

# Completed migrations stay executable as historical evidence, but are not
# standing runtime dependencies.  Current data-contract v14 makes each listed
# migration's apply path fail closed through migration_lifecycle.py.
UNREACHABLE_ALLOWLIST: Mapping[str, str] = {
    "migrations.curriculum_v2": "retired module-first migration (through v0)",
    "migrations.library_taxonomy_v1": "retired taxonomy migration (through v1)",
    "migrations.projects_v1": "retired project migration (through v0)",
    "migrations.registry_partition_v1": "retired registry migration (through v1)",
    "migrations.standardize_job_plans_v1": "retired Job plan migration (through v10)",
    "migrations.standardize_plan_template_v10": (
        "retired plan-template migration (through v10)"
    ),
}


@dataclass(frozen=True)
class ReachabilityReport:
    scanned_modules: int
    reachable_modules: tuple[str, ...]
    allowed_unreachable: tuple[str, ...]
    unreachable_modules: tuple[str, ...]
    stale_allowlist: tuple[str, ...]
    unclassified_entrypoints: tuple[str, ...]
    configuration_errors: tuple[str, ...]
    syntax_errors: tuple[str, ...]
    dependency_cycles: tuple[tuple[str, ...], ...]
    package_entrypoint_imports: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not (
            self.unreachable_modules
            or self.stale_allowlist
            or self.unclassified_entrypoints
            or self.configuration_errors
            or self.syntax_errors
            or self.dependency_cycles
            or self.package_entrypoint_imports
        )

    def as_dict(self) -> dict:
        return {"ok": self.ok, **asdict(self)}


def _module_name(package: str, package_dir: Path, path: Path) -> str:
    relative = path.relative_to(package_dir)
    parts = list(relative.parts)
    if parts[-1] == "__init__.py":
        parts.pop()
    else:
        parts[-1] = path.stem
    return ".".join((package, *parts))


def _from_base(module: str, path: Path, node: ast.ImportFrom) -> str | None:
    if not node.level:
        return node.module
    package = module if path.name == "__init__.py" else module.rpartition(".")[0]
    parts = package.split(".") if package else []
    keep = len(parts) - node.level + 1
    if keep < 0:
        return None
    base = parts[:keep]
    if node.module:
        base.extend(node.module.split("."))
    return ".".join(base)


def _existing_with_parents(name: str | None, modules: Mapping[str, Path]) -> set[str]:
    if not name:
        return set()
    parts = name.split(".")
    return {
        candidate
        for end in range(1, len(parts) + 1)
        if (candidate := ".".join(parts[:end])) in modules
    }


def _imports(module: str, path: Path, tree: ast.AST, modules: Mapping[str, Path]) -> set[str]:
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                targets.update(_existing_with_parents(alias.name, modules))
        elif isinstance(node, ast.ImportFrom):
            base = _from_base(module, path, node)
            targets.update(_existing_with_parents(base, modules))
            for alias in node.names:
                if alias.name != "*":
                    targets.update(_existing_with_parents(f"{base}.{alias.name}", modules))
    return targets


def _direct_imports(
    module: str,
    path: Path,
    tree: ast.AST,
    modules: Mapping[str, Path],
) -> set[str]:
    """Resolve the most specific owned module for cycle/layer analysis.

    Reachability intentionally includes package parents. Treating those
    bookkeeping parents as real dependency edges would manufacture a cycle
    between every eager ``__init__`` and each child it exports.
    """
    targets: set[str] = set()

    def deepest(name: str | None) -> str | None:
        candidates = _existing_with_parents(name, modules)
        return max(candidates, key=lambda value: value.count("."), default=None)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if target := deepest(alias.name):
                    targets.add(target)
        elif isinstance(node, ast.ImportFrom):
            base = _from_base(module, path, node)
            base_target = deepest(base)
            resolved_alias = False
            for alias in node.names:
                if alias.name == "*":
                    continue
                candidate = f"{base}.{alias.name}" if base else alias.name
                if candidate in modules:
                    targets.add(candidate)
                    resolved_alias = True
            if base_target is not None and not resolved_alias:
                targets.add(base_target)
    return targets


def _dependency_cycles(graph: Mapping[str, set[str]]) -> tuple[tuple[str, ...], ...]:
    """Return strongly connected dependency components with more than one node."""
    next_index = 0
    indexes: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[tuple[str, ...]] = []

    def visit(module: str) -> None:
        nonlocal next_index
        indexes[module] = next_index
        lowlinks[module] = next_index
        next_index += 1
        stack.append(module)
        on_stack.add(module)

        for dependency in sorted(graph.get(module, set())):
            if dependency not in indexes:
                visit(dependency)
                lowlinks[module] = min(lowlinks[module], lowlinks[dependency])
            elif dependency in on_stack:
                lowlinks[module] = min(lowlinks[module], indexes[dependency])

        if lowlinks[module] != indexes[module]:
            return
        component: list[str] = []
        while stack:
            dependency = stack.pop()
            on_stack.remove(dependency)
            component.append(dependency)
            if dependency == module:
                break
        if len(component) > 1:
            components.append(tuple(sorted(component)))

    for module in sorted(graph):
        if module not in indexes:
            visit(module)
    return tuple(sorted(components))


def analyse(
    tools_root: Path = TOOLS_ROOT,
    *,
    entrypoints: Sequence[str] = ENTRYPOINTS,
    package_roots: Mapping[str, str] = PACKAGE_ROOTS,
    allowlist: Mapping[str, str] = UNREACHABLE_ALLOWLIST,
) -> ReachabilityReport:
    """Build the static import graph and classify every owned Python module."""
    tools_root = tools_root.resolve()
    modules: dict[str, Path] = {}
    configuration_errors: list[str] = []

    declared_entrypoints = set(entrypoints)
    actual_entrypoints = {path.name for path in tools_root.glob("*.py")}
    unclassified = sorted(actual_entrypoints - declared_entrypoints)

    root_modules: list[str] = []
    for relative in entrypoints:
        path = tools_root / relative
        if not path.is_file():
            configuration_errors.append(f"declared entrypoint is missing: {relative}")
            continue
        module = path.stem
        modules[module] = path
        root_modules.append(module)

    for package, relative in package_roots.items():
        package_dir = tools_root / relative
        if not package_dir.is_dir():
            configuration_errors.append(f"declared package root is missing: {relative}")
            continue
        for path in sorted(package_dir.rglob("*.py")):
            module = _module_name(package, package_dir, path)
            prior = modules.get(module)
            if prior is not None and prior != path:
                configuration_errors.append(
                    f"module {module} is declared by both {prior} and {path}"
                )
            modules[module] = path

    graph: dict[str, set[str]] = {}
    direct_graph: dict[str, set[str]] = {}
    syntax_errors: list[str] = []
    for module, path in sorted(modules.items()):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            syntax_errors.append(f"{path.relative_to(tools_root)}: {exc}")
            graph[module] = set()
            direct_graph[module] = set()
            continue
        graph[module] = _imports(module, path, tree, modules)
        direct_graph[module] = _direct_imports(module, path, tree, modules)

    reachable: set[str] = set()
    queue = deque(root_modules)
    while queue:
        module = queue.popleft()
        if module in reachable:
            continue
        reachable.add(module)
        queue.extend(sorted(graph.get(module, set()) - reachable))

    allowlisted = set(allowlist)
    stale_allowlist = sorted(
        module
        for module in allowlisted
        if module not in modules or module in reachable
    )
    allowed_unreachable = sorted((set(modules) - reachable) & allowlisted)
    unreachable = sorted(set(modules) - reachable - allowlisted)
    entrypoint_roots = set(root_modules)
    package_entrypoint_imports = sorted(
        f"{module} -> {dependency}"
        for module, dependencies in direct_graph.items()
        if module not in entrypoint_roots
        for dependency in dependencies
        if dependency in entrypoint_roots
    )

    return ReachabilityReport(
        scanned_modules=len(modules),
        reachable_modules=tuple(sorted(reachable)),
        allowed_unreachable=tuple(allowed_unreachable),
        unreachable_modules=tuple(unreachable),
        stale_allowlist=tuple(stale_allowlist),
        unclassified_entrypoints=tuple(unclassified),
        configuration_errors=tuple(configuration_errors),
        syntax_errors=tuple(syntax_errors),
        dependency_cycles=_dependency_cycles(direct_graph),
        package_entrypoint_imports=tuple(package_entrypoint_imports),
    )


def _print_report(report: ReachabilityReport) -> None:
    classified = len(report.reachable_modules) + len(report.allowed_unreachable)
    print(
        "code reachability: "
        f"{classified}/{report.scanned_modules} modules statically classified; "
        f"{len(report.allowed_unreachable)} historical allowlisted"
    )
    sections = (
        ("unreachable modules", report.unreachable_modules),
        ("stale allowlist entries", report.stale_allowlist),
        ("unclassified tools/*.py", report.unclassified_entrypoints),
        ("configuration errors", report.configuration_errors),
        ("syntax errors", report.syntax_errors),
        (
            "dependency cycles",
            tuple(" <-> ".join(component) for component in report.dependency_cycles),
        ),
        ("package imports executable entrypoints", report.package_entrypoint_imports),
    )
    for label, values in sections:
        if values:
            print(f"{label}:")
            for value in values:
                print(f"  - {value}")
    if report.ok:
        print("code architecture: PASS (static imports only; no runtime coverage claim)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the complete report as JSON")
    args = parser.parse_args()
    report = analyse()
    if args.json:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
    else:
        _print_report(report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

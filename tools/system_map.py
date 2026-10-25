#!/usr/bin/env python3
"""Check or regenerate the developer map from this checkout's source.

This development gate reads code and documentation only. It never loads learner
records or joins canonical validation. Static edges are imports, not call traces.
"""

from __future__ import annotations

import argparse
import ast
import fnmatch
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from code_reachability import _direct_imports, _module_name

HEADINGS = ("Purpose", "Owned paths", "Entry points", "Depends on and used by",
            "Invariants", "Pinning tests", "Binding ADRs")
BLOCK = re.compile(r"<!-- system-map:begin name=([\w-]+) -->\n(.*?)"
                   r"<!-- system-map:end -->", re.S)


@dataclass
class Component:
    identifier: str
    path: Path
    text: str
    sections: dict[str, str]


def sections(text: str) -> dict[str, str]:
    return {match[0]: match[1].strip() for match in re.findall(
        r"^## ([^\n]+)\n(.*?)(?=^## |\Z)", text, re.M | re.S)}


def spans(text: str) -> list[str]:
    return re.findall(r"`([^`\n]+)`", text)


def symbol_exists(root: Path, reference: str) -> bool:
    relative, _, symbol = reference.partition("::")
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()) or not path.is_file() or not symbol:
        return False
    try:
        nodes = ast.parse(path.read_text(encoding="utf-8")).body
        for name in symbol.split("."):
            node = next((n for n in nodes if isinstance(
                n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name), None)
            if node is None:
                return False
            nodes = node.body
        return True
    except (SyntaxError, UnicodeError):
        return False


def _page(root: Path, path: Path, errors: list[str]) -> Component:
    text = path.read_text(encoding="utf-8")
    parts = sections(text)
    if tuple(parts) != HEADINGS:
        errors.append(f"{path.relative_to(root)}: expected headings {HEADINGS}")
    if len(text.splitlines()) > 80:
        errors.append(f"{path.relative_to(root)}: exceeds 80 lines")
    for heading in HEADINGS:
        if not parts.get(heading):
            errors.append(f"{path.name}: empty {heading}")
    for reference in spans(parts.get("Entry points", "")):
        if not symbol_exists(root, reference):
            errors.append(f"{path.name}: missing entry point {reference}")
    for reference in spans(parts.get("Pinning tests", "")):
        relative = reference.partition("::")[0]
        if not relative.startswith("tests/") or not (root / relative).is_file() \
                or ("::" in reference and not symbol_exists(root, reference)):
            errors.append(f"{path.name}: missing pinning test {reference}")
    for reference in spans(parts.get("Binding ADRs", "")):
        if not reference.startswith("system/adr/ADR-") or not (root / reference).is_file():
            errors.append(f"{path.name}: missing ADR {reference}")
    for line in parts.get("Invariants", "").splitlines():
        if line.startswith("- ") and "unpinned" not in line \
                and not any(ref.startswith("tests/") for ref in spans(line)):
            errors.append(f"{path.name}: invariant needs a pinning test or explicit unpinned label")
    return Component(path.stem, path, text, parts)


def _rewrite(path: Path, expected: dict[str, str], *, write: bool,
             errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    blocks = list(BLOCK.finditer(text))
    names = [m[1] for m in blocks]
    if sorted(names) != sorted(expected):
        errors.append(f"{path.name}: generated block names {names}, expected {sorted(expected)}")
        return
    for match in reversed(blocks):
        body = expected[match[1]].rstrip() + "\n"
        if body != match[2]:
            if not write:
                errors.append(f"{path.name}: stale {match[1]}; run tools/system_map.py --write")
            text = text[:match.start(2)] + body + text[match.end(2):]
    if write and text != path.read_text(encoding="utf-8"):
        path.write_text(text, encoding="utf-8")


def check(root: Path, *, write: bool = False) -> list[str]:
    errors: list[str] = []
    base = root / "system/developer"
    pages = [_page(root, p, errors) for p in sorted((base / "components").glob("*.md"))]
    if not pages:
        return ["no component pages"]
    config = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    contracts = config["tool"]["importlinter"]["contracts"]
    layer_contract = next(c for c in contracts if c["type"] == "layers"
                          and c.get("containers") == ["learning_os"])
    layers = layer_contract["layers"]
    pkg = root / "tools/learning_os"
    modules = {_module_name("learning_os", pkg, p): p for p in pkg.rglob("*.py")}
    owners: dict[str, str] = {}
    component_layers: dict[str, str] = {}
    for name, path in sorted(modules.items()):
        relative = path.relative_to(root).as_posix()
        matches = [p for p in pages if any(
            fnmatch.fnmatchcase(relative, pattern)
            and relative.count("/") == pattern.count("/")
            for pattern in spans(p.sections.get("Owned paths", "")))]
        if len(matches) != 1:
            errors.append(f"{relative}: expected one owner, found {[p.identifier for p in matches]}")
            continue
        identifier = matches[0].identifier
        owners[name] = identifier
        layer = name.split(".")[1] if "." in name else "package-root"
        if layer not in layers and layer != "package-root":
            errors.append(f"{relative}: unclassified layer {layer}")
        if identifier in component_layers and component_layers[identifier] != layer:
            errors.append(f"{identifier}: spans layers")
        component_layers[identifier] = layer
    for page in pages:
        for pattern in spans(page.sections.get("Owned paths", "")):
            if not any(fnmatch.fnmatchcase(p.relative_to(root).as_posix(), pattern)
                       and p.relative_to(root).as_posix().count("/") == pattern.count("/")
                       for p in modules.values()):
                errors.append(f"{page.identifier}: owned path matches nothing: {pattern}")
    if errors:
        return errors
    edges: dict[str, set[str]] = {p.identifier: set() for p in pages}
    for name, path in sorted(modules.items()):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for dependency in _direct_imports(name, path, tree, modules):
            source, target = owners[name], owners[dependency]
            a, b = component_layers[source], component_layers[target]
            if a in layers and b in layers and layers.index(a) > layers.index(b):
                errors.append(f"layer violation: {name} -> {dependency}")
            if source != target:
                edges[source].add(target)
    for page in pages:
        dependencies = ", ".join(f"`{x}`" for x in sorted(edges[page.identifier])) or "none"
        users = ", ".join(f"`{x}`" for x in sorted(edges) if page.identifier in edges[x]) or "none"
        _rewrite(page.path, {"edges": f"Depends on: {dependencies}.\n\nUsed by: {users}."},
                 write=write, errors=errors)
    index = "\n".join(f"- `{p.identifier}` — {p.sections['Purpose']}" for p in pages)
    _rewrite(base / "CODEMAP.md", {"index": index}, write=write, errors=errors)
    diagrams = ["Layer order (from pyproject.toml): " + " → ".join(layers) + "."]
    for layer in layers:
        ids = sorted(p for p, value in component_layers.items() if value == layer)
        diagrams += [f"\n### {layer}\n", "```mermaid", "flowchart LR"]
        def node(value):
            return value.replace("-", "_")
        diagrams += [f'  {node(i)}["{i}"]' for i in ids]
        layer_edges = [(i, j) for i in ids for j in sorted(edges[i]) if j in ids]
        if len(layer_edges) <= 12:
            diagrams += [f"  {node(i)} --> {node(j)}" for i, j in layer_edges]
        diagrams += ["```"]
        if len(layer_edges) > 12:
            diagrams += [f"\nComponent roster: {len(layer_edges)} intra-layer imports omitted here "
                         "for readability. Each component page lists its complete dependencies."]
    _rewrite(base / "C4.md", {"components": "\n".join(diagrams)}, write=write, errors=errors)
    flows = (base / "FLOWS.md").read_text(encoding="utf-8")
    for reference in re.findall(r"<!-- system-map:symbol (\S+) -->", flows):
        if not symbol_exists(root, reference):
            errors.append(f"FLOWS.md: missing flow symbol {reference}")
    externals = set(re.findall(r"<!-- system-map:external (\S+) -->", flows))
    for heading, text in sections(flows).items():
        participants = set(re.findall(r"^\s*participant (\w+) as ", text, re.M))
        if not participants:
            continue
        declared = re.findall(r"<!-- system-map:participant (\w+) (\S+) -->", text)
        if len(declared) != len(participants) or {p for p, _ in declared} != participants:
            errors.append(f"FLOWS.md {heading}: each participant needs exactly one reference")
        for participant, reference in declared:
            if reference.startswith("component:"):
                valid = reference.removeprefix("component:") in edges
            elif reference.startswith("external:"):
                valid = reference.removeprefix("external:") in externals
            else:
                valid = symbol_exists(root, reference)
            if not valid:
                errors.append(f"FLOWS.md {heading}: invalid participant {participant}: {reference}")
    for path in [base / "CODEMAP.md", base / "C4.md", base / "FLOWS.md"]:
        for relative in spans(path.read_text(encoding="utf-8")):
            if relative.startswith(("tools/", "tests/", "system/", "pyproject.toml")) \
                    and not any(char in relative for char in " *<>:") \
                    and not (root / relative).exists():
                errors.append(f"{path.name}: missing named path {relative}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="regenerate code-derived blocks")
    mode.add_argument("--check", action="store_true", help="compare without writing (default)")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        errors = check(args.root.resolve(), write=args.write)
    except (OSError, ValueError, KeyError, StopIteration, SyntaxError) as exc:
        errors = [f"cannot read system map: {exc}"]
    for error in errors:
        print(error)
    if not errors:
        print("system map: ownership, references, layers and generated blocks agree")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())

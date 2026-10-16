"""Mechanical module moves (Phase 6 OD9, 6.0.2).

Applies a ``{old module -> new module}`` map to files, imports and
path-keyed text in one operation. Structure only: the tool refuses a
map whose text rewrites would touch a recording or canonical tree.

Usage:
  python tools/move_map.py --map MAP.yaml --check
  python tools/move_map.py --map MAP.yaml --apply
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

FORBIDDEN_PREFIXES = (
    "tests/scenarios/recorded/",
    "curriculum/",
    "sources/",
    "knowledge/",
    "records/",
    "work/",
    "operations/",
    "generated/",
)
TEXT_ROOTS = ("tools/", "tests/", "system/")
TEXT_FILES = ("pyproject.toml", "Makefile")


class MoveError(ValueError):
    """The map is invalid or the move is not mechanical."""


@dataclass(frozen=True)
class Move:
    """One map entry with normalized repo-relative paths."""

    from_raw: str
    to_raw: str
    from_norm: str
    to_norm: str
    is_dir: bool
    old_dotted: str | None
    new_dotted: str | None


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or f"exit {proc.returncode}"
        raise MoveError(f"git {' '.join(args)} failed: {detail}")
    return proc.stdout


def _repo_root() -> Path:
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or f"exit {proc.returncode}"
        raise MoveError(f"cannot find repository root: {detail}")
    return Path(proc.stdout.strip())


def _tracked_files(root: Path) -> list[str]:
    out = _git(root, "ls-files", "-z")
    return sorted(p for p in out.split("\0") if p)


def _dotted_for_path(rel: str) -> str | None:
    if not rel.endswith(".py"):
        return None
    if rel.startswith("tools/"):
        dotted = rel[len("tools/"):-len(".py")].replace("/", ".")
        if dotted.endswith(".__init__"):
            dotted = dotted[: -len(".__init__")]
        return dotted
    return None


def _is_direct_child(from_norm: str, is_dir: bool) -> bool:
    parent = from_norm.rsplit("/", 1)[0] if "/" in from_norm else ""
    return parent == "tools/learning_os"


def _load_moves(root: Path, map_path: Path) -> list[Move]:
    try:
        text = map_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise MoveError(f"cannot read map {map_path}: {exc}") from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise MoveError(f"invalid map YAML: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("moves"), list):
        raise MoveError("map must be a mapping with a 'moves' list")
    if not data["moves"]:
        raise MoveError("map has no moves")
    moves: list[Move] = []
    for index, entry in enumerate(data["moves"]):
        if not isinstance(entry, dict):
            raise MoveError(f"move {index}: not a mapping")
        from_raw = entry.get("from")
        to_raw = entry.get("to")
        if not isinstance(from_raw, str) or not isinstance(to_raw, str):
            raise MoveError(f"move {index}: 'from' and 'to' must be strings")
        is_dir = from_raw.endswith("/")
        from_norm = from_raw.rstrip("/")
        to_norm = to_raw.rstrip("/")
        if not from_norm or not to_norm:
            raise MoveError(f"move {index}: empty 'from' or 'to'")
        for label, value in (("from", from_norm), ("to", to_norm)):
            if value.startswith("/") or ".." in Path(value).parts:
                raise MoveError(
                    f"move {index}: {label} {value!r} is not repo-relative")
        moves.append(Move(
            from_raw=from_raw, to_raw=to_raw, from_norm=from_norm,
            to_norm=to_norm, is_dir=is_dir,
            old_dotted=_dotted_for_path(
                from_norm if not is_dir else from_norm + "/__init__.py"),
            new_dotted=_dotted_for_path(
                to_norm if not is_dir else to_norm + "/__init__.py"),
        ))
    return moves


def _is_package_move(move: Move) -> bool:
    return move.is_dir


def _mapped_dotted(moves: list[Move], dotted: str) -> str:
    for move in moves:
        if move.old_dotted is None or move.new_dotted is None:
            continue
        if _is_package_move(move):
            if dotted == move.old_dotted:
                return move.new_dotted
            prefix = move.old_dotted + "."
            if dotted.startswith(prefix):
                return move.new_dotted + dotted[len(move.old_dotted):]
        elif dotted == move.old_dotted:
            return move.new_dotted
    return dotted


def _mapped_path(moves: list[Move], rel: str) -> str:
    for move in moves:
        if move.is_dir:
            prefix = move.from_norm + "/"
            if rel.startswith(prefix):
                return move.to_norm + rel[len(move.from_norm):]
        elif rel == move.from_norm:
            return move.to_norm
    return rel


def _contains(ancestor: str, path: str) -> bool:
    return path == ancestor or path.startswith(ancestor + "/")


def _validate(root: Path, moves: list[Move],
              tracked: list[str]) -> None:
    tracked_set = set(tracked)
    for move in moves:
        for label, value in (("from", move.from_norm), ("to", move.to_norm)):
            if any(value == p.rstrip("/") or value.startswith(p)
                   for p in FORBIDDEN_PREFIXES):
                raise MoveError(
                    f"move {move.from_raw!r} -> {move.to_raw!r}: {label} "
                    f"{value!r} is under a forbidden tree")
        source = root / move.from_norm
        if move.is_dir:
            if not source.is_dir():
                raise MoveError(f"move source {move.from_raw!r} does not exist")
            if not any(p.startswith(move.from_norm + "/") for p in tracked):
                raise MoveError(
                    f"move source {move.from_raw!r} is not tracked by git")
        else:
            if not source.is_file():
                raise MoveError(f"move source {move.from_raw!r} does not exist")
            if move.from_norm not in tracked_set:
                raise MoveError(
                    f"move source {move.from_raw!r} is not tracked by git")
        dest = root / move.to_norm
        if dest.exists() or dest.is_symlink():
            raise MoveError(f"move destination {move.to_raw!r} already exists")
        if move.to_norm in tracked_set or any(
                p.startswith(move.to_norm + "/") for p in tracked):
            raise MoveError(f"move destination {move.to_raw!r} already exists")
        if move.from_norm == move.to_norm:
            raise MoveError(
                f"move {move.from_raw!r} -> {move.to_raw!r}: source and "
                "destination are the same")
    for move in moves:
        if move.is_dir and move.from_norm != move.to_norm and _contains(
                move.from_norm, move.to_norm):
            raise MoveError(
                f"move {move.from_raw!r} -> {move.to_raw!r}: destination "
                "is inside its source")
    for i, first in enumerate(moves):
        for j, second in enumerate(moves):
            if i == j:
                continue
            if first.from_norm == second.from_norm:
                raise MoveError(
                    f"moves overlap: duplicate source {first.from_norm!r}")
            if first.to_norm == second.to_norm and i < j:
                raise MoveError(
                    f"moves overlap: duplicate destination {first.to_norm!r}")
            if i < j and first.from_norm != second.from_norm and (
                    _contains(first.from_norm, second.from_norm)
                    or _contains(second.from_norm, first.from_norm)):
                raise MoveError(
                    f"moves overlap: sources {first.from_norm!r} and "
                    f"{second.from_norm!r} nest")
            if _contains(first.to_norm, second.from_norm):
                raise MoveError(
                    f"moves overlap: source {second.from_norm!r} is inside "
                    f"destination {first.to_norm!r}")
            if _contains(first.from_norm, second.to_norm):
                raise MoveError(
                    f"moves overlap: destination {second.to_norm!r} is "
                    f"inside source {first.from_norm!r}")
            if _contains(first.to_norm, second.to_norm) and i > j:
                raise MoveError(
                    f"moves overlap: destination {second.to_norm!r} is "
                    f"inside destination {first.to_norm!r} of a later move")
    created: set[str] = set()
    for move_index, move in enumerate(moves):
        parent = str(Path(move.to_norm).parent)
        if parent == ".":
            parent = ""
        if parent:
            on_disk = (root / parent).is_dir()
            in_created = parent in created or any(
                _contains(c, parent) for c in created)
            if not on_disk and not in_created:
                raise MoveError(
                    f"move destination {move.to_raw!r}: parent package "
                    f"{parent!r} does not exist and no earlier move creates it")
            if parent == "tools/learning_os" or parent.startswith(
                    "tools/learning_os/"):
                init_on_disk = (root / parent / "__init__.py").is_file()
                init_created = False
                if not init_on_disk:
                    for earlier in moves[:move_index]:
                        if not earlier.is_dir:
                            continue
                        if parent == earlier.to_norm:
                            init_created = (
                                root / earlier.from_norm / "__init__.py"
                            ).is_file()
                        elif parent.startswith(earlier.to_norm + "/"):
                            rel = parent[len(earlier.to_norm) + 1:]
                            init_created = (
                                root / earlier.from_norm / rel
                                / "__init__.py").is_file()
                if not init_on_disk and not init_created:
                    raise MoveError(
                        f"move destination {move.to_raw!r}: parent package "
                        f"{parent!r} has no __init__.py")
        if move.is_dir:
            created.add(move.to_norm)
            base = root / move.from_norm
            if base.is_dir():
                for sub in sorted(base.rglob("*")):
                    if sub.is_dir():
                        rel = sub.relative_to(root).as_posix()
                        created.add(_mapped_path([move], rel))


def _package_of(rel: str, dotted: str | None) -> str:
    if dotted is None:
        return ""
    if rel.rsplit("/", 1)[-1] == "__init__.py":
        return dotted
    return dotted.rpartition(".")[0]


def _resolve_base(module: str | None, level: int, package: str) -> str | None:
    if level == 0:
        return module or ""
    parts = package.split(".") if package else []
    if level - 1 > len(parts):
        return None
    base = parts[: len(parts) - (level - 1)] if level > 1 else list(parts)
    if module:
        base.extend(module.split("."))
    return ".".join(base)


def _collapse(text: str) -> str:
    return " ".join(text.split())


def _plan_imports(
    moves: list[Move], rel: str, text: str,
) -> tuple[str, list[tuple[str, str]]]:
    """Return (new text, [(old stmt, new stmt)]) for one Python file."""
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise MoveError(f"{rel}: cannot parse Python: {exc}") from exc
    dotted = _dotted_for_path(rel)
    if dotted is None and rel.startswith("tests/"):
        dotted = Path(rel).stem
    package = _package_of(rel, dotted)
    file_moved = _mapped_path(moves, rel) != rel
    lines = text.splitlines(keepends=True)
    starts: list[int] = []
    offset = 0
    for line in lines:
        starts.append(offset)
        offset += len(line)

    def absolute(lineno: int, col: int) -> int:
        return starts[lineno - 1] + col

    edits: list[tuple[int, int, str, str, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            base_old = _resolve_base(node.module, node.level, package)
            if base_old is None:
                continue
            base_mapped = _mapped_dotted(moves, base_old) if base_old else ""
            groups: dict[str, list[tuple[str, str | None]]] = {}
            order: list[str] = []
            changed = False
            for alias in node.names:
                if alias.name == "*":
                    new_base, new_name = base_mapped, "*"
                    if base_mapped != base_old:
                        changed = True
                else:
                    full_old = (
                        f"{base_old}.{alias.name}" if base_old else alias.name)
                    full_mapped = _mapped_dotted(moves, full_old)
                    if full_mapped != full_old:
                        changed = True
                        if "." in full_mapped:
                            new_base, new_name = full_mapped.rpartition(".")[0], (
                                full_mapped.rpartition(".")[2])
                        else:
                            new_base, new_name = "", full_mapped
                    else:
                        new_base, new_name = base_mapped, alias.name
                        if base_mapped != base_old:
                            changed = True
                if new_base not in groups:
                    groups[new_base] = []
                    order.append(new_base)
                groups[new_base].append((new_name, alias.asname))
            needs = changed or (file_moved and node.level > 0)
            if node.level > 0 and changed:
                needs = True
            if not needs:
                continue
            if any(base == "" for base in order):
                continue
            segment = ast.get_source_segment(text, node) or ""
            renamed = any(
                new_name != alias.name
                for alias, (new_name, _a) in zip(
                    node.names,
                    [item for base in order for item in groups[base]],
                    strict=False)
            ) if len(order) == 1 else True
            if len(order) == 1 and not renamed:
                new_base = order[0]
                new_segment, count = re.subn(
                    r"^from\s+(?:\.+[\w.]*|[\w.]+)",
                    f"from {new_base}", segment, count=1)
                if count == 0:
                    continue
            else:
                parts = []
                for base in order:
                    names = ", ".join(
                        f"{name} as {asname}" if asname else name
                        for name, asname in groups[base])
                    parts.append(f"from {base} import {names}")
                indent = " " * node.col_offset
                new_segment = ("\n" + indent).join(parts)
            start = absolute(node.lineno, node.col_offset)
            end = absolute(node.end_lineno or node.lineno,
                           node.end_col_offset or node.col_offset)
            edits.append((start, end, segment, new_segment, segment))
        elif isinstance(node, ast.Import):
            pairs: list[tuple[str, str | None]] = []
            changed = False
            for alias in node.names:
                mapped = _mapped_dotted(moves, alias.name)
                if mapped != alias.name:
                    changed = True
                pairs.append((mapped, alias.asname))
            if not changed:
                continue
            segment = ast.get_source_segment(text, node) or ""
            names = ", ".join(
                f"{name} as {asname}" if asname else name
                for name, asname in pairs)
            new_segment = f"import {names}"
            start = absolute(node.lineno, node.col_offset)
            end = absolute(node.end_lineno or node.lineno,
                           node.end_col_offset or node.col_offset)
            edits.append((start, end, segment, new_segment, segment))
    if not edits:
        return text, []
    edits.sort(key=lambda item: item[0], reverse=True)
    new_text = text
    report: list[tuple[str, str]] = []
    for start, end, segment, new_segment, _raw in edits:
        new_text = new_text[:start] + new_segment + new_text[end:]
        report.append((_collapse(segment), _collapse(new_segment)))
    report.reverse()
    return new_text, report


def _string_patterns(
    moves: list[Move],
) -> list[tuple[re.Pattern[str], str, str, str]]:
    patterns: list[tuple[re.Pattern[str], str, str, str]] = []
    for move in moves:
        old_path, new_path = move.from_norm, move.to_norm
        path_re = re.compile(
            r"(?<![A-Za-z0-9_./-])" + re.escape(old_path)
            + r"(?![A-Za-z0-9_-])")
        patterns.append((path_re, old_path, new_path, "path"))
        if move.old_dotted and move.new_dotted:
            dotted_re = re.compile(
                r"(?<![A-Za-z0-9_.])" + re.escape(move.old_dotted)
                + r"(?![A-Za-z0-9_])")
            patterns.append(
                (dotted_re, move.old_dotted, move.new_dotted, "dotted"))
    return patterns


def _layers_replacements(
    moves: list[Move],
) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for move in moves:
        if not _is_direct_child(move.from_norm, move.is_dir):
            continue
        if not move.old_dotted or not move.new_dotted:
            continue
        old_top = move.old_dotted.split(".")[1]
        new_top = move.new_dotted.split(".")[1]
        if old_top != new_top:
            pairs.append((old_top, new_top))
    return pairs


def _apply_strings(
    moves: list[Move], rel: str, text: str,
) -> tuple[str, list[tuple[str, str]], int]:
    report: list[tuple[str, str]] = []
    total = 0
    new_text = text
    for pattern, old, new, _kind in _string_patterns(moves):
        def repl(match: re.Match[str], _old: str = old, _new: str = new) -> str:
            report.append((_old, _new))
            return _new

        new_text, count = pattern.subn(repl, new_text)
        total += count
    if rel == "pyproject.toml":
        pairs = _layers_replacements(moves)
        if pairs:
            hits = 0
            layer_blocks = list(re.finditer(
                r"layers\s*=\s*\[.*?\]", new_text, flags=re.DOTALL))
            for block in reversed(layer_blocks):
                block_text = block.group(0)

                def fix_string(match: re.Match[str]) -> str:
                    nonlocal hits
                    quote, content = match.group(1), match.group(2)
                    parts = re.split(r"( : | \| )", content)
                    changed = False
                    for idx, token in enumerate(parts):
                        for old_top, new_top in pairs:
                            if token == old_top:
                                parts[idx] = new_top
                                report.append((old_top, new_top))
                                hits += 1
                                changed = True
                    if not changed:
                        return match.group(0)
                    return f"{quote}{''.join(parts)}{quote}"

                new_block = re.sub(
                    r"(['\"])((?:(?!\1).)*)\1", fix_string, block_text)
                new_text = (
                    new_text[: block.start()] + new_block
                    + new_text[block.end():])
            total += hits
    return new_text, report, total


def _read_text(root: Path, rel: str) -> str | None:
    try:
        data = (root / rel).read_bytes()
    except OSError:
        return None
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def _plan(
    root: Path, moves: list[Move], tracked: list[str],
) -> tuple[list[str], dict[str, str], int, int, int]:
    """Compute (report lines, post-path -> new text, moved, imports, strings)."""
    patterns = _string_patterns(moves)
    forbidden_hits: list[str] = []
    for rel in tracked:
        if not any(rel.startswith(p) for p in FORBIDDEN_PREFIXES):
            continue
        text = _read_text(root, rel)
        if text is None:
            continue
        if any(pattern.search(text) for pattern, _o, _n, _k in patterns):
            forbidden_hits.append(rel)
    if forbidden_hits:
        raise MoveError(
            "move would rewrite forbidden files: "
            + ", ".join(sorted(forbidden_hits)))
    py_files = [
        rel for rel in tracked
        if rel.endswith(".py")
        and (rel.startswith("tools/") or rel.startswith("tests/"))]
    contents: dict[str, str] = {}
    for rel in tracked:
        text = _read_text(root, rel)
        if text is not None:
            contents[rel] = text
    writes: dict[str, str] = {}
    import_lines: list[str] = []
    imports_rewritten = 0
    for rel in py_files:
        text = contents.get(rel)
        if text is None:
            continue
        new_text, report = _plan_imports(moves, rel, text)
        if report and any(rel.startswith(p) for p in FORBIDDEN_PREFIXES):
            raise MoveError(f"move would rewrite forbidden files: {rel}")
        post = _mapped_path(moves, rel)
        if report:
            imports_rewritten += len(report)
            for old, new in report:
                import_lines.append(f"{post}: {old} -> {new}")
        if new_text != text:
            writes[post] = new_text
            contents[rel] = new_text
    string_lines: list[str] = []
    strings_rewritten = 0
    text_files = [
        rel for rel in tracked
        if (any(rel.startswith(r) for r in TEXT_ROOTS) or rel in TEXT_FILES)
        and not any(rel.startswith(p) for p in FORBIDDEN_PREFIXES)]
    for rel in sorted(text_files):
        post = _mapped_path(moves, rel)
        text = writes.get(post, contents.get(rel))
        if text is None:
            continue
        new_text, report, count = _apply_strings(moves, rel, text)
        if count:
            strings_rewritten += count
            for old, new in report:
                string_lines.append(f"{post}: {old} -> {new}")
        if new_text != text:
            writes[post] = new_text
    move_lines: list[str] = []
    files_moved = 0
    for move in moves:
        if move.is_dir:
            members = sorted(
                p for p in tracked if p.startswith(move.from_norm + "/"))
            files_moved += len(members)
            for member in members:
                move_lines.append(
                    f"{member}: {member} -> {_mapped_path(moves, member)}")
        else:
            files_moved += 1
            move_lines.append(
                f"{move.from_norm}: {move.from_norm} -> {move.to_norm}")
    lines = move_lines + import_lines + string_lines
    return lines, writes, files_moved, imports_rewritten, strings_rewritten


def build_parser() -> argparse.ArgumentParser:
    """The tool's CLI surface (OD9, 6.0.2)."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", required=True, help="move map YAML file")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true",
                       help="print every planned edit; change nothing")
    group.add_argument("--apply", action="store_true",
                       help="perform the moves and edits")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        root = _repo_root()
        map_path = Path(args.map)
        if not map_path.is_absolute():
            map_path = Path.cwd() / map_path
        moves = _load_moves(root, map_path)
        tracked = _tracked_files(root)
        _validate(root, moves, tracked)
        lines, writes, files_moved, imports_rewritten, strings_rewritten = (
            _plan(root, moves, tracked))
    except MoveError as exc:
        print(f"move_map: {exc}", file=sys.stderr)
        return 2
    if args.check:
        for line in lines:
            print(line)
        print(f"files moved: {files_moved}")
        print(f"imports rewritten: {imports_rewritten}")
        print(f"strings rewritten: {strings_rewritten}")
        return 0
    try:
        for move in moves:
            _git(root, "mv", move.from_norm, move.to_norm)
        for post, new_text in sorted(writes.items()):
            (root / post).write_text(new_text, encoding="utf-8")
    except (MoveError, OSError) as exc:
        print(f"move_map: {exc}", file=sys.stderr)
        return 2
    for line in lines:
        print(line)
    print(f"files moved: {files_moved}")
    print(f"imports rewritten: {imports_rewritten}")
    print(f"strings rewritten: {strings_rewritten}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

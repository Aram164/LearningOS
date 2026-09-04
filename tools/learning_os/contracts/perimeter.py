"""The shape of the two levels above ``repository/``, checked against disk.

``system/contracts/perimeter.yaml`` declares what may exist at the wrapper and
umbrella levels. This module makes that declaration executable.

Two things make this checker unlike every other one in the tree, and both are
deliberate:

**It reads disk, never git.** The wrapper's ``.gitignore`` ignores
``LearningOS/`` wholly and ``*.pdf`` globally, so git is blind to exactly the
things this contract exists to see. A git-based check would report a clean tree
over three loose books.

**It refuses to run outside the real tree.** The synthetic mini-repos the test
suite builds live at ``<tmp>/LearningOS/repository`` — the same shape, none of
the content. Raising a perimeter error there would fail a third of the suite
and mean nothing. The discriminator is declared in the contract as
``applies_when_present`` rather than hardcoded here, so what counts as "the
real tree" is visible in the declaration instead of buried in a module.

Deny by default: a path at either level matching no entry is an error. That is
the point — an inspection list only ever catches what somebody thought of, and
``operations/`` and ``migration/`` are already on record as the trees that were
added after the list was written.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import yaml

PERIMETER_RELATIVE = "system/contracts/perimeter.yaml"

#: Read in 1 MiB blocks; the candidates are books, and the whole point of the
#: size pre-filter is that we hash almost nothing.
_HASH_BLOCK = 1024 * 1024


class PerimeterError(ValueError):
    """The declaration itself cannot be read."""


@dataclass(frozen=True)
class PerimeterIssue:
    code: str
    message: str
    path: str = ""
    #: "E" or "W". Structure is an error; a stray already declared in
    #: `pending_disposition` is a warning, because the umbrella level is in no
    #: git index and every disposition there is irreversible and operator-owned.
    #: The ratchet is the point: existing mess stays visible on every run, new
    #: mess is blocked the moment it appears.
    severity: str = "E"

    def __str__(self) -> str:
        location = f" [{self.path}]" if self.path else ""
        return f"PERIMETER-{self.code}: {self.message}{location}"


@dataclass(frozen=True)
class Perimeter:
    wrapper: str
    umbrella: str
    applies_when_present: tuple[str, ...]
    material_suffixes: frozenset[str]
    ephemera: frozenset[str]
    entries: tuple[dict, ...]
    pending: tuple[dict, ...]

    def declared_paths(self) -> set[str]:
        return {str(entry["path"]) for entry in self.entries}

    def pending_paths(self) -> set[str]:
        return {str(entry["path"]) for entry in self.pending}

    def managed_dirs(self) -> tuple[str, ...]:
        return tuple(
            str(entry["path"])
            for entry in self.entries
            if entry.get("file_policy") == "managed"
        )


def load(root: Path) -> Perimeter:
    """Read the declaration. Raises rather than guessing."""
    path = root / PERIMETER_RELATIVE
    if not path.is_file():
        raise PerimeterError(
            f"no {PERIMETER_RELATIVE} — nothing declares what may exist above "
            "the repository"
        )
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise PerimeterError(f"cannot read {PERIMETER_RELATIVE}: {exc}") from exc
    if not isinstance(raw, dict):
        raise PerimeterError(f"{PERIMETER_RELATIVE} is not a mapping")

    roots = raw.get("roots") or {}
    return Perimeter(
        wrapper=str(roots.get("wrapper", ".")),
        umbrella=str(roots.get("umbrella", "LearningOS")),
        applies_when_present=tuple(raw.get("applies_when_present") or ()),
        material_suffixes=frozenset(
            str(s).lower() for s in (raw.get("material_suffixes") or ())
        ),
        ephemera=frozenset(str(s) for s in (raw.get("ephemera") or ())),
        entries=tuple(raw.get("entries") or ()),
        pending=tuple(raw.get("pending_disposition") or ()),
    )


def wrapper_root(root: Path) -> Path:
    """``semestercontext/`` — two levels above the repository.

    Resolved first, always. ``Path(".").parent`` is ``Path(".")``, so a
    relative root would walk nowhere, ``applies()`` would find no anchors, and
    the check would silently disable itself — which is the exact class of
    invisible non-enforcement this contract exists to end.
    """
    return root.resolve().parent.parent


def applies(root: Path, perimeter: Perimeter) -> bool:
    """Whether this is the tree the declaration describes.

    Every declared anchor must be present. One missing anchor means a fixture,
    not a degraded system, and the honest response to a fixture is silence.
    """
    wrapper = wrapper_root(root)
    if not wrapper.is_dir():
        return False
    return all((wrapper / anchor).exists() for anchor in perimeter.applies_when_present)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(_HASH_BLOCK):
            digest.update(block)
    return digest.hexdigest()


def _observed(wrapper: Path, perimeter: Perimeter) -> list[tuple[str, Path]]:
    """Everything on disk at the two governed levels, ephemera excluded.

    Non-recursive by design. This contract governs what may *appear* at these
    two levels; what lives inside a declared directory is that directory
    owner's business, and the repository has its own tree contract for its own
    interior.
    """
    found: list[tuple[str, Path]] = []
    for base, prefix in ((wrapper, ""), (wrapper / perimeter.umbrella,
                                         f"{perimeter.umbrella}/")):
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir(), key=lambda p: p.name):
            if child.name in perimeter.ephemera:
                continue
            found.append((f"{prefix}{child.name}", child))
    return found


def _shadowed_by(candidate: Path, managed_roots: list[Path]) -> str | None:
    """The managed copy ``candidate`` duplicates, if one exists.

    Size first, hash second. The managed tree is ~1,155 files; hashing it whole
    to find three duplicates would be absurd, and a size collision is rare
    enough that the hash runs almost never.
    """
    try:
        size = candidate.stat().st_size
    except OSError:
        return None

    collisions = [
        path
        for managed in managed_roots
        if managed.is_dir()
        for path in managed.rglob("*")
        if path.is_file() and _size_or_none(path) == size
    ]
    if not collisions:
        return None

    digest = _sha256(candidate)
    for path in collisions:
        try:
            if _sha256(path) == digest:
                return path.as_posix()
        except OSError:
            continue
    return None


def _size_or_none(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError:
        return None


def check(root: Path) -> list[PerimeterIssue]:
    """Every way the perimeter and its declaration can disagree."""
    try:
        perimeter = load(root)
    except PerimeterError as exc:
        # A repository with no declaration is a fixture, not a violation. The
        # register test is what proves the real one has this contract.
        if not (root / PERIMETER_RELATIVE).exists():
            return []
        return [PerimeterIssue("UNREADABLE", str(exc), PERIMETER_RELATIVE)]

    if not applies(root, perimeter):
        return []

    wrapper = wrapper_root(root)
    issues: list[PerimeterIssue] = []
    declared = perimeter.declared_paths()
    pending = perimeter.pending_paths()
    by_path = {str(entry["path"]): entry for entry in perimeter.entries}

    observed = _observed(wrapper, perimeter)
    observed_paths = {relative for relative, _ in observed}

    managed_roots = [wrapper / name for name in perimeter.managed_dirs()]

    for relative, path in observed:
        if relative in declared:
            issues.extend(_check_kind(by_path[relative], relative, path))
            continue
        if relative in pending:
            # Declared as a known stray with a stated disposition. Visible in
            # the contract, not silently tolerated, and the test suite makes
            # the list shrink-only.
            continue
        issues.append(PerimeterIssue(
            "UNDECLARED",
            "not declared in the perimeter contract — give it a purpose and an "
            "owner, or file it where it belongs",
            relative,
        ))

    for relative in sorted(declared - observed_paths):
        issues.append(PerimeterIssue(
            "MISSING", f"declared but not on disk: '{relative}'",
            PERIMETER_RELATIVE))

    # Material and duplication rules apply to every file at these levels,
    # declared or pending — a declared stray is still a stray.
    for relative, path in observed:
        if not path.is_file() or path.is_symlink():
            continue
        if any(relative.startswith(f"{name}/") for name in perimeter.managed_dirs()):
            continue
        known = relative in pending
        severity = "W" if known else "E"
        awaiting = " (declared in pending_disposition)" if known else ""

        shadow = _shadowed_by(path, managed_roots)
        if shadow:
            issues.append(PerimeterIssue(
                "SHADOW",
                "byte-identical to the managed copy at "
                f"'{Path(shadow).relative_to(wrapper).as_posix()}' — a second "
                "copy nothing addresses, and nothing keeps in step" + awaiting,
                relative,
                severity,
            ))
        elif path.suffix.lower() in perimeter.material_suffixes:
            issues.append(PerimeterIssue(
                "UNMANAGED-MATERIAL",
                "course material outside the managed tree — it resolves as no "
                "material:// URI and no manifest records its checksum" + awaiting,
                relative,
                severity,
            ))

    if (root / ARCHITECTURE_RELATIVE).is_file():
        try:
            if not block_is_current(root, perimeter):
                issues.append(PerimeterIssue(
                    "STALE-BLOCK",
                    "the ARCHITECTURE root tree block is not the projection of "
                    "this contract — run `python tools/tree_contract.py --write`",
                    ARCHITECTURE_RELATIVE,
                ))
        except PerimeterError as exc:
            issues.append(PerimeterIssue(
                "STALE-BLOCK", str(exc), ARCHITECTURE_RELATIVE))

    return issues


def _check_kind(entry: dict, relative: str, path: Path) -> list[PerimeterIssue]:
    """The declared kind still describes what is there."""
    kind = str(entry.get("kind", ""))
    issues: list[PerimeterIssue] = []

    if kind == "symlink":
        if not path.is_symlink():
            issues.append(PerimeterIssue(
                "KIND", "declared a symlink but is not one", relative))
            return issues
        target = str(entry.get("target", ""))
        actual = path.readlink().as_posix()
        if target and actual != target:
            issues.append(PerimeterIssue(
                "KIND",
                f"symlink points at '{actual}', declared '{target}'",
                relative,
            ))
        return issues

    if kind in {"directory", "nested_repo"} and not path.is_dir():
        issues.append(PerimeterIssue(
            "KIND", f"declared a {kind} but is not a directory", relative))
    elif kind in {"file", "document"} and not path.is_file():
        issues.append(PerimeterIssue(
            "KIND", f"declared a {kind} but is not a file", relative))
    return issues


# ---- the ARCHITECTURE §3.1 projection ---------------------------------------
#
# §3.1 renders the wrapper root; §3.2 renders the repository. That is exactly
# the perimeter/tree split, so each block is a projection of the contract that
# owns it. Same rule as the tree block: the prose is derived, never authored.

ARCHITECTURE_RELATIVE = "system/ARCHITECTURE.md"
BEGIN = "<!-- root-tree:begin"
END = "<!-- root-tree:end -->"

_LABEL_GAP = 2


def render(perimeter: Perimeter) -> str:
    """The wrapper root as a tree block, in declared order.

    Only the two governed levels appear, and only entries that carry a purpose
    get an annotation — a row whose purpose is obvious from its name reads
    better without one.
    """
    umbrella = perimeter.umbrella

    def visible(entries):
        # Dotfiles are declared in the contract but stay out of the drawing:
        # a tree block is a map of where things live, and .env belongs in the
        # contract's prose rather than in a diagram of the workspace.
        return [e for e in entries if not Path(str(e["path"])).name.startswith(".")]

    top = visible([e for e in perimeter.entries if "/" not in str(e["path"])])
    nested = visible([e for e in perimeter.entries
                      if str(e["path"]).startswith(f"{umbrella}/")])

    def suffix(entry: dict) -> str:
        return "/" if entry.get("kind") in {"directory", "nested_repo"} else ""

    rows: list[tuple[str, str]] = []
    for index, entry in enumerate(top):
        name = str(entry["path"])
        last = index == len(top) - 1
        rows.append((("└── " if last else "├── ") + name + suffix(entry),
                     _annotation(entry)))
        if name != umbrella:
            continue
        for jndex, child in enumerate(nested):
            child_name = str(child["path"]).split("/", 1)[1]
            rows.append((
                ("    " if last else "│   ")
                + ("└── " if jndex == len(nested) - 1 else "├── ")
                + child_name + suffix(child),
                _annotation(child),
            ))

    width = max((len(line) for line, _ in rows), default=0) + _LABEL_GAP
    lines = ["semestercontext/"]
    for line, note in rows:
        lines.append(f"{line:<{width}}{note}".rstrip() if note else line)
    return "\n".join(lines)


def _annotation(entry: dict) -> str:
    """One short line per row. The full purpose lives in the contract.

    An entry may carry an explicit `annotation:` where its purpose is too long
    to draw. Truncating prose into a tree is how a diagram ends up saying
    something the contract does not.
    """
    explicit = " ".join(str(entry.get("annotation", "")).split())
    if explicit:
        return explicit
    purpose = " ".join(str(entry.get("purpose", "")).split())
    if not purpose:
        return ""
    first = purpose.split(". ")[0].rstrip(".")
    return first if len(first) <= 72 else first[:69].rstrip() + "…"


def _block_bounds(text: str) -> tuple[int, int]:
    start = text.find(BEGIN)
    if start == -1:
        raise PerimeterError(
            f"{ARCHITECTURE_RELATIVE} has no '{BEGIN}' marker — the generated "
            "root tree block is anchored on comment markers, never on heading "
            "numbers, which move"
        )
    open_end = text.find("-->", start)
    end = text.find(END, start)
    if open_end == -1 or end == -1:
        raise PerimeterError(
            f"{ARCHITECTURE_RELATIVE} has an unterminated root tree block")
    return open_end + len("-->"), end


def current_block(root: Path) -> str:
    text = (root / ARCHITECTURE_RELATIVE).read_text(encoding="utf-8")
    start, end = _block_bounds(text)
    return text[start:end]


def _expected_block(perimeter: Perimeter) -> str:
    return "\n\n```text\n" + render(perimeter) + "\n```\n\n"


def write_block(root: Path, perimeter: Perimeter) -> bool:
    path = root / ARCHITECTURE_RELATIVE
    text = path.read_text(encoding="utf-8")
    start, end = _block_bounds(text)
    replacement = _expected_block(perimeter)
    if text[start:end] == replacement:
        return False
    path.write_text(text[:start] + replacement + text[end:], encoding="utf-8")
    return True


def block_is_current(root: Path, perimeter: Perimeter) -> bool:
    return current_block(root) == _expected_block(perimeter)


def summary(root: Path) -> dict[str, int]:
    """Counts for a report. Never used to decide anything."""
    perimeter = load(root)
    return {
        "declared": len(perimeter.entries),
        "pending_disposition": len(perimeter.pending),
    }

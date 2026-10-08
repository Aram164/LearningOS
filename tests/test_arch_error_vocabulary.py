"""A14 one error vocabulary (PLAN D3): public codes are spelled once."""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import yaml

from learning_os.domain.codes import PUBLIC_CODES

ROOT = Path(__file__).resolve().parent.parent
RATCHETS_PATH = ROOT / "tests/architecture/ratchets.yaml"

FIX = "Import the code from learning_os.domain.codes."

CHECK_ID = "A14-vocabulary"

#: Tools files allowed to spell a public code (SPEC §3.3 A14).
ALLOWED_FILES: frozenset[str] = frozenset(
    {"tools/learning_os/domain/codes.py"})


@dataclass(frozen=True)
class Hit:
    signature: str
    path: str
    lineno: int


def load_public_codes() -> list[str]:
    """The public codes from domain.codes (SPEC §8.2 order)."""
    return list(PUBLIC_CODES)


def scan_file(path: Path, rel: str, codes: frozenset[str]) -> list[Hit]:
    """Public code literals in one file (exact string constants)."""
    if rel in ALLOWED_FILES:
        return []
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [Hit(f"{rel}::{node.value}", rel, node.lineno)
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and node.value in codes]


def scan_tree(root: Path, codes: frozenset[str]) -> list[Hit]:
    """Every public code literal under tools/**/*.py."""
    hits: list[Hit] = []
    for path in sorted((root / "tools").rglob("*.py")):
        hits.extend(scan_file(path, path.relative_to(root).as_posix(), codes))
    return hits


def test_public_codes_are_eleven():
    codes = load_public_codes()
    assert len(codes) == 11, (
        f"A14 domain.codes lists {len(codes)} public codes, SPEC §3.3 says 11 — {FIX}")
    assert all(isinstance(code, str) and code for code in codes)


def test_current_exceptions_are_recorded():
    codes = frozenset(load_public_codes())
    hits = scan_tree(ROOT, codes)
    current = Counter(hit.signature for hit in hits)
    first_seen = {hit.signature: hit for hit in hits}
    data = yaml.safe_load(RATCHETS_PATH.read_text(encoding="utf-8"))
    recorded = {entry["signature"]: entry["count"]
                for entry in data["checks"].get(CHECK_ID, [])}
    failures = []
    for signature, count in sorted(current.items()):
        if recorded.get(signature, 0) < count:
            seen = first_seen[signature]
            failures.append(
                f"A14 {signature}: current count {count} exceeds recorded "
                f"{recorded.get(signature, 0)} — "
                f"{seen.path}:{seen.lineno} — {FIX}")
    for signature in sorted(recorded):
        if signature not in current:
            failures.append(
                f"A14 {signature}: no longer occurs — "
                f"remove the fixed exception from ratchets.yaml")
    assert not failures, "\n".join(failures)

"""A6 ids round-trip (PLAN D6): stdout ids parse; schema patterns agree.

Part 1 (SPEC §8.1): every generic kind regex equals every occurrence of that
prefix's pattern in ``system/schema/*.schema.json``, apart from the listed
looser variants; the goal alternation equals the scan detectors ((q)).
Part 2 (SPEC §3.3 A6): every id-shaped stdout string parses; undecided
id-fields.yaml rows are recorded exceptions until the planner decides them.
"""

from __future__ import annotations

import argparse
import ast
import json
from collections import Counter
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

from learning_os.contracts.payloads import sha256_value
from learning_os.domain import ids
from learning_os.domain.failures import MalformedId
from learning_os.domain.ids import KINDS, Digest

ROOT = Path(__file__).resolve().parent.parent
RATCHETS_PATH = ROOT / "tests/architecture/ratchets.yaml"

FIX = "Print canonical ids via domain.ids (PLAN D6)."

CHECK_ID = "A6-idroundtrip"

#: (pattern, schema file) pairs looser than the kind regex (SPEC §8.1).
LOOSER_SCHEMA_PATTERNS: frozenset[tuple[str, str]] = frozenset({
    ("^ability-[a-z0-9-]+$", "ability-candidate.schema.json"),
    ("^ability-[a-z0-9-]+$", "ability-observation.schema.json"),
    ("^concept-[a-z0-9-]+$", "abilities.schema.json"),
    ("^module-[a-z0-9-]+$", "abilities.schema.json"),
})

#: Generic kinds in SPEC §8.1 order (kind and prefix coincide for all).
GENERIC_KINDS: tuple[str, ...] = (
    "module",
    "unit",
    "study-map",
    "stage",
    "route",
    "source",
    "concept",
    "note",
    "workspace",
    "program",
    "project",
    "ability",
    "detour",
    "component",
    "resource",
    "thematic-group",
    "proposal",
    "path",
    "knowledge",
)

SPECIAL_KINDS: tuple[str, ...] = (
    "transaction",
    "goal",
    "digest",
    "material-uri",
    "material-path",
)

#: Amendment (q)'s goal regex, exactly.
EXPECTED_GOAL_PATTERN = (
    r"^(?:lineage-stale|study-map-obligation|evidence-superseded):\S+$"
)


def test_kind_inventory_is_pinned():
    assert set(KINDS) == set(GENERIC_KINDS) | set(SPECIAL_KINDS)


def test_generic_patterns_are_canonical():
    for kind in GENERIC_KINDS:
        assert KINDS[kind].name == kind
        assert KINDS[kind].pattern.pattern == (
            f"^{kind}-[a-z0-9]+(?:-[a-z0-9]+)*$"), kind


def _schema_patterns():
    """Every (file, pattern) in system/schema/*.schema.json."""
    for path in sorted((ROOT / "system/schema").glob("*.schema.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        yield from _walk_patterns(data, path.name)


def _walk_patterns(node, name):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "pattern" and isinstance(value, str):
                yield name, value
            else:
                yield from _walk_patterns(value, name)
    elif isinstance(node, list):
        for value in node:
            yield from _walk_patterns(value, name)


def test_generic_patterns_match_schemas():
    # An occurrence of a prefix's pattern opens a character class right
    # after "^{prefix}-": other families anchored on the same stem
    # (^stage-result-, ^ability-observation-) and prefix guards (^route-)
    # are not occurrences of the kind pattern.
    seen_looser: set[tuple[str, str]] = set()
    failures = []
    for name, pattern in _schema_patterns():
        for kind in GENERIC_KINDS:
            if not pattern.startswith(f"^{kind}-["):
                continue
            canonical = KINDS[kind].pattern.pattern
            if pattern == canonical:
                break
            if (pattern, name) in LOOSER_SCHEMA_PATTERNS:
                seen_looser.add((pattern, name))
                break
            failures.append(
                f"A6 {name}: pattern {pattern!r} is neither the {kind} "
                f"kind regex nor a listed looser variant — {FIX}")
            break
    for pattern, name in sorted(set(LOOSER_SCHEMA_PATTERNS) - seen_looser):
        failures.append(
            f"A6 LOOSER_SCHEMA_PATTERNS entry {(pattern, name)!r} no longer "
            f"occurs — remove it")
    assert not failures, "\n".join(failures)


def test_goal_alternation_matches_scan_detectors():
    assert KINDS["goal"].pattern.pattern == EXPECTED_GOAL_PATTERN
    tree = ast.parse((ROOT / "tools/learning_os/semantics/scan.py").read_text(
        encoding="utf-8"))
    detectors = {
        node.args[1].value
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == "_emit" and len(node.args) >= 2
        and isinstance(node.args[1], ast.Constant)
        and isinstance(node.args[1].value, str)
    }
    assert detectors, "no _emit detectors found in semantics/scan.py"
    alternation = set(
        EXPECTED_GOAL_PATTERN.split("(?:")[1].split(")")[0].split("|"))
    assert alternation == detectors, (
        f"A6 goal alternation {sorted(alternation)} != scan detectors "
        f"{sorted(detectors)} — {FIX}")


def test_digest_spellings_round_trip():
    bare_value = "9f" * 32
    prefixed_value = f"sha256:{bare_value}"
    for value in (bare_value, prefixed_value):
        parsed = ids.parse("digest", value)
        assert isinstance(parsed, Digest)
        assert parsed.bare() == bare_value
        assert parsed.prefixed() == prefixed_value
    assert ids.is_valid("digest", bare_value) is True
    assert ids.is_valid("digest", prefixed_value) is True
    unit = ids.parse("unit", "unit-1")
    assert unit == "unit-1"
    assert isinstance(unit, str)


def test_digest_refuses_uppercase_and_malformed():
    bad = [
        "AB" * 32,
        f"sha256:{'AB' * 32}",
        "ab" * 31 + "AG",
        "ab" * 32 + "c",
        "ab" * 31,
        "",
        "sha256:",
        "sha256:xyz",
        "sha256:" + "ab" * 32 + " ",
        "SHA256:" + "ab" * 32,
        "ab" * 16 + " " + "ab" * 16,
    ]
    for value in bad:
        with pytest.raises(MalformedId):
            ids.parse("digest", value)
        assert ids.is_valid("digest", value) is False
    with pytest.raises(MalformedId):
        ids.parse("digest", None)
    assert ids.is_valid("digest", None) is False
    # Amendment (ad): production contracts are unchanged.
    with pytest.raises(argparse.ArgumentTypeError):
        sha256_value("ab" * 32)
    assert sha256_value("sha256:" + "ab" * 32) == "sha256:" + "ab" * 32
    note_schema = json.loads(
        (ROOT / "system/schema/note.schema.json").read_text(encoding="utf-8"))
    digest_field = note_schema["properties"]["material_analysis"][
        "properties"]["recorded_source_digest"]
    validator = Draft202012Validator(digest_field)
    assert validator.is_valid("ab" * 32) is True
    assert validator.is_valid("sha256:" + "ab" * 32) is False


def _navigate(doc: dict, pointer: str) -> dict | None:
    node: dict | None = doc
    for part in [p for p in pointer.split("/") if p]:
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, dict) else None


def test_inventory_digest_representations():
    """Amendment (ad) at every scalar digest inventory pointer."""
    import hashlib

    from learning_os.contracts.requests import request_schema

    rows = yaml.safe_load(
        (ROOT / "tests/architecture/id-fields.yaml").read_text(
            encoding="utf-8"))["fields"]
    digest_rows = [r for r in rows if r.get("kind") == "digest"]
    assert digest_rows, "no digest inventory rows"
    # Unaffected non-digest pointers are skipped silently.
    assert len(digest_rows) < len(rows)
    # Production contracts must stay byte-identical (read-only check).
    watched = [
        ROOT / "system/schema/note.schema.json",
        ROOT / "system/schema/capabilities/source.record.revise.schema.json",
    ]
    watched += sorted((ROOT / "system/schema/requests").glob("*.schema.json"))
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in watched if p.is_file()}
    # Plain-string digests (no argparse sha256_value, hence no pattern by
    # _json_type): payload schemas stay bare `string` for byte-identity, so
    # both spellings remain accepted at the schema boundary.
    PLAIN_STRING_DIGESTS = frozenset({
        ("ai-action.delivery.apply", "/properties/delivery_sha256"),
        ("coordination.section.revise",
         "/properties/expected_content_sha256"),
        ("module.plan.import", "/properties/package_sha256"),
    })
    checked = 0
    for row in sorted(digest_rows,
                      key=lambda r: (r["operation"], r["pointer"])):
        effective = request_schema(ROOT, row["operation"])
        node = _navigate(effective, row["pointer"])
        assert node is not None, f"{row['operation']} {row['pointer']} missing"
        key = (row["operation"], row["pointer"])
        validator = Draft202012Validator(node)
        if key in PLAIN_STRING_DIGESTS:
            assert "pattern" not in node, row
            assert validator.is_valid("sha256:" + "ab" * 32) is True, row
            assert validator.is_valid("ab" * 32) is True, row
        else:
            # No inventory pointer is the bare-only recorded_source_digest;
            # every other digest inventory pointer keeps prefixed.
            assert node.get("pattern") == "^sha256:[a-f0-9]{64}$", (
                f"{row['operation']} {row['pointer']}: want prefixed pattern")
            assert validator.is_valid("sha256:" + "ab" * 32) is True, row
            assert validator.is_valid("ab" * 32) is False, row
        checked += 1
    assert checked == len(digest_rows)
    # Negative control: a bare-only production pointer required as prefixed
    # must fail; an unaffected non-production pointer passes silently.
    note_schema = json.loads(
        (ROOT / "system/schema/note.schema.json").read_text(encoding="utf-8"))
    bare_node = note_schema["properties"]["material_analysis"][
        "properties"]["recorded_source_digest"]
    assert bare_node.get("pattern") != "^sha256:[a-f0-9]{64}$"
    bare_validator = Draft202012Validator(bare_node)
    assert bare_validator.is_valid("sha256:" + "ab" * 32) is False
    assert bare_validator.is_valid("ab" * 32) is True
    after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in watched if p.is_file()}
    assert after == before, "digest check changed a committed contract file"


def _stdout_strings():
    for path in sorted((ROOT / "tests/scenarios/recorded").rglob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        stdout = data.get("stdout")
        if not isinstance(stdout, str):
            continue
        try:
            payload = json.loads(stdout)
        except ValueError:
            continue
        yield from _walk_strings(payload)


def _walk_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from _walk_strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk_strings(value)


def test_stdout_ids_parse():
    checked = 0
    failures = []
    for value in _stdout_strings():
        for kind, id_kind in KINDS.items():
            if id_kind.pattern.fullmatch(value) is None:
                continue
            checked += 1
            try:
                parsed = ids.parse(kind, value)
            except MalformedId as exc:
                failures.append(
                    f"A6 {kind}::{value!r}: scanned but does not parse "
                    f"({exc}) — {FIX}")
                continue
            if kind == "digest":
                if value.startswith("sha256:"):
                    same = parsed.prefixed() == value
                else:
                    same = parsed.bare() == value
                if not same:
                    failures.append(
                        f"A6 digest spelling round trip failed for "
                        f"{value!r} — {FIX}")
            elif parsed != value:
                failures.append(
                    f"A6 {kind}::{value!r}: parse returned {parsed!r} — {FIX}")
    assert checked, "A6 scanned no id strings at all"
    assert not failures, "\n".join(failures[:20])


def _review_signatures() -> Counter[str]:
    """One exception per undecided id-fields.yaml row (SPEC 10.1)."""
    path = ROOT / "tests/architecture/id-fields.yaml"
    rows = yaml.safe_load(path.read_text(encoding="utf-8"))["fields"]
    current: Counter[str] = Counter()
    for row in rows:
        if "review" in row:
            current[f"{row['operation']}::{row['pointer']}::review"] += 1
    return current


def test_current_exceptions_are_recorded():
    current = _review_signatures()
    data = yaml.safe_load(RATCHETS_PATH.read_text(encoding="utf-8"))
    recorded = {entry["signature"]: entry["count"]
                for entry in data["checks"].get(CHECK_ID, [])}
    failures = []
    for signature, count in sorted(current.items()):
        if recorded.get(signature, 0) < count:
            failures.append(
                f"A6 {signature}: current count {count} exceeds recorded "
                f"{recorded.get(signature, 0)} — {FIX}")
    for signature in sorted(recorded):
        if signature not in current:
            failures.append(
                f"A6 {signature}: no longer occurs — "
                f"remove the fixed exception from ratchets.yaml")
    assert not failures, "\n".join(failures)

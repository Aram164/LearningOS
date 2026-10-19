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

from learning_os.app.handlers import platform as platform_handlers
from learning_os.domain import ids
from learning_os.domain.ai_errors import (
    DeliveryBindingError,
    DeliveryValidationError,
)
from learning_os.domain.failures import MalformedId
from learning_os.domain.ids import KINDS, Digest
from learning_os.store.ai_actions.binding import read_bound_delivery, validated_sha256
from learning_os.store.ai_actions.storage import FilesystemAIActionRepository
from learning_os.store.contracts.payloads import sha256_value

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
    r"^(?:lineage-stale|study-map-obligation|evidence-superseded|claims-needing-review|claims-audit|repeated-question-gap|inspection-without-dossier|reviewer-correction-pattern):\S+$"
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
    detectors = set()
    for name, argument in (("scan.py", 1), ("goals.py", 0)):
        tree = ast.parse((ROOT / "tools/learning_os/derive/semantics" / name).read_text())
        detectors.update(node.args[argument].value for node in ast.walk(tree)
                         if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                         and node.func.id == "_emit" and len(node.args) > argument
                         and isinstance(node.args[argument], ast.Constant)
                         and isinstance(node.args[argument].value, str))
    # Claim findings choose one of these literal detectors from shared status.
    detectors.update({"lineage-stale", "claims-needing-review"})
    assert detectors
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

    from learning_os.store.contracts.requests import request_schema

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


def _recorded_stdout_strings(data):
    stdout = data.get("stdout")
    if isinstance(stdout, str):
        try:
            payload = json.loads(stdout)
        except ValueError:
            pass
        else:
            yield from _walk_strings(payload)
    for step in data.get("steps", []):
        yield from _recorded_stdout_strings(step)


def _stdout_strings():
    for path in sorted((ROOT / "tests/scenarios/recorded").rglob("*.json")):
        yield from _recorded_stdout_strings(json.loads(path.read_text(encoding="utf-8")))


def _scalar_accepts(kind, value, subschema):
    parsed = ids.parse(kind, value)
    spellings = (parsed.prefixed(), parsed.bare()) if kind == "digest" else (value,)
    validator = Draft202012Validator(subschema)
    return any(validator.is_valid(spelling) for spelling in spellings)


def test_scalar_checker_preserves_digest_representation_and_refuses_wrong_type():
    value = "sha256:" + "ab" * 32
    prefixed = {"type": "string", "pattern": "^sha256:[a-f0-9]{64}$"}
    bare = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
    assert _scalar_accepts("digest", value, prefixed)
    assert _scalar_accepts("digest", value, bare)
    assert not _scalar_accepts("digest", value, {"type": "integer"})
    assert not _scalar_accepts("unit", "unit-1", {"type": "integer"})


def test_nested_sequence_stdout_is_scanned():
    data = {"steps": [{"stdout": '{"id":"unit-1"}'}, {"stdout": "plain text"}]}
    assert list(_recorded_stdout_strings(data)) == ["unit-1"]


def test_real_nested_sequence_stdout_is_scanned():
    """`note-demo-seq-1` appears only inside a sequence step's stdout."""
    assert "note-demo-seq-1" in set(_stdout_strings())


def test_decided_scalar_pointers_accept_their_values():
    from learning_os.store.contracts.requests import request_schema

    module_node = _navigate(
        request_schema(ROOT, "plan.template"), "/properties/module_id")
    assert _scalar_accepts("module", "module-1", module_node)
    concept_node = _navigate(
        request_schema(ROOT, "atlas.context"), "/properties/concept_id")
    assert _scalar_accepts("concept", "concept-1", concept_node)
    # Both digest spellings validate at the real prefixed-only pointer
    # and at the real bare-only production pointer alike.
    prefixed_node = _navigate(
        request_schema(ROOT, "source.record.revise"),
        "/properties/expected_diff_sha256")
    assert prefixed_node["pattern"] == "^sha256:[a-f0-9]{64}$"
    note_schema = json.loads(
        (ROOT / "system/schema/note.schema.json").read_text(encoding="utf-8"))
    bare_node = note_schema["properties"]["material_analysis"][
        "properties"]["recorded_source_digest"]
    assert bare_node["pattern"] == "^[0-9a-f]{64}$"
    for node in (prefixed_node, bare_node):
        assert _scalar_accepts("digest", "sha256:" + "ab" * 32, node)
        assert _scalar_accepts("digest", "ab" * 32, node)


def test_scalar_checker_refuses_wrong_type_and_containers():
    from learning_os.store.contracts.requests import request_schema

    assert not _scalar_accepts("module", "module-1", {"type": "integer"})
    object_node = _navigate(
        request_schema(ROOT, "unit.plan.revise"), "/properties/record")
    assert object_node["type"] == "object"
    assert not _scalar_accepts("unit", "unit-1", object_node)
    assert not _scalar_accepts("digest", "sha256:" + "ab" * 32, object_node)


def test_id_scan_changes_no_production_file():
    import hashlib

    watched = [
        ROOT / "tools/learning_os/adapters/cli_types.py",
        ROOT / "tools/learning_os/store/contracts/payloads.py",
        ROOT / "tests/architecture/id-fields.yaml",
        ROOT / "system/schema/note.schema.json",
    ]
    watched += sorted((ROOT / "system/schema/requests").glob("*.schema.json"))
    watched += sorted(
        (ROOT / "system/schema/capabilities").glob("*.schema.json"))
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in watched}
    assert len(list(_stdout_strings())) > 0
    # Builder Task 78 resolved the ten ::review rows below; only the
    # unrelated lineage claim review remains undecided.
    assert sum(_review_signatures().values()) == 1
    after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in watched}
    assert after == before


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
    from learning_os.store.contracts.requests import request_schema

    rows = yaml.safe_load((ROOT / "tests/architecture/id-fields.yaml").read_text())["fields"]
    pointers = {}
    for row in rows:
        if row.get("review") or row.get("kind") is None:
            continue
        node = _navigate(request_schema(ROOT, row["operation"]), row["pointer"])
        assert node is not None and node.get("type") == "string", row
        pointers.setdefault(row["kind"], []).append((row, node))
    checked = 0
    failures = []
    for value in set(_stdout_strings()):
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
            for row, node in pointers.get(kind, []):
                if not _scalar_accepts(kind, value, node):
                    failures.append(f"A6 {kind}::{value!r} fails scalar "
                                    f"{row['operation']}::{row['pointer']} — {FIX}")
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


# ---- SPEC (ay): the six executed validation owners (S15) --------------------
#
# Owner sources at accepted S14 (Core e437c278): storage.py 7506c022…,
# binding.py ced4c868… (both byte-identical in S15); the inspect helpers
# moved AST-identically from commands/reads.py (12542259…) to
# ops/handlers/platform.py in S15 B1 (cd6b5571). The checks below execute
# those real owners; the dispatch is shared by A6/A13/A5 (test-only).

#: The exact approved owner rows: (operation, pointer) -> (owner, shape).
#: The first six are SPEC (ay) items 1-2; human receipt
#: control/S15-Aram-six-field-approval-20261008.json. The remaining
#: eight are Builder Task 78 under SPEC (cx) D-6/D-7/D-8: each miss
#: suggests from the domain its handler already loads (or, for the
#: AI store, a bounded miss-only enumeration of that same store).
SUPPORTED_OWNER_ROWS: dict[tuple[str, str], tuple[str, str]] = {


    ("project.inspect", "/properties/id"): ("inspect-reference", "scalar"),
    ("project.inspect", "/properties/more_ids/items"): ("inspect-reference", "scalar"),
    ("ai-action.delivery.apply", "/properties/delivery_id"):
        ("ai-delivery-exchange", "scalar"),
    ("ai-action.delivery.apply", "/properties/artifact_sha256"):
        ("ai-delivery-artifact-digests", "mapping-values"),
    ("ai-action.append-slices", "/properties/request_id"):
        ("ai-request-store", "scalar"),
    ("ai-action.status", "/properties/request_id"):
        ("ai-request-store", "scalar"),
    ("ai-action.delivery.validate", "/properties/delivery_id"):
        ("ai-delivery-store", "scalar"),
    ("ai-action.prepare", "/properties/action_id"):
        ("ai-action-registry", "scalar"),
    ("ai-action.prepare", "/properties/target_id"):
        ("ai-action-target", "scalar"),
    ("operations.read", "/properties/request_id"):
        ("operations-trace-request", "scalar"),
    ("masters-planning.comparison.publish", "/properties/candidate_module_id"):
        ("masters-candidate-module", "scalar"),
    ("related.read", "/properties/id"): ("related-record", "scalar"),
}


def _escape_pointer_part(part: str) -> str:
    return part.replace("~", "~0").replace("/", "~1")


def owner_selected_values(operation: str, pointer: str,
                          request: dict) -> list[tuple[str, object]]:
    """Every governed scalar for a supported SPEC (ay) owner row.

    Returns ``(sub_pointer, value)`` pairs in request order: the scalar
    itself, every array item for an ``/items`` pointer, every actual map
    value for ``mapping-values``. Fails on an unsupported row, a missing
    pointer, or a wrong container shape; never invents a child pointer.
    """
    try:
        _, owner_shape = SUPPORTED_OWNER_ROWS[(operation, pointer)]
    except KeyError:
        raise AssertionError(
            f"A6 {operation}::{pointer}: no supported validation owner — {FIX}"
        ) from None
    parts = [part for part in pointer.split("/") if part]
    if len(parts) < 2 or parts[0] != "properties":
        raise AssertionError(
            f"A6 {operation}::{pointer}: not an inventory pointer — {FIX}")
    prop = parts[1]
    if prop not in request:
        raise AssertionError(
            f"A6 {operation}::{pointer}: pointer missing from the request — {FIX}")
    if pointer.endswith("/items"):
        items = request[prop]
        if not isinstance(items, list):
            raise AssertionError(
                f"A6 {operation}::{pointer}: want every array item, found "
                f"{type(items).__name__} — {FIX}")
        selected = []
        for index, item in enumerate(items):
            if not isinstance(item, str):
                raise AssertionError(
                    f"A6 {operation}::{pointer}/{index}: want a scalar id, found "
                    f"{type(item).__name__} — {FIX}")
            selected.append((f"{pointer}/{index}", item))
        return selected
    value = request[prop]
    if owner_shape == "scalar":
        if not isinstance(value, str):
            raise AssertionError(
                f"A6 {operation}::{pointer}: want a scalar id, found "
                f"{type(value).__name__} — {FIX}")
        return [(pointer, value)]
    if owner_shape == "mapping-values":
        if not isinstance(value, dict):
            raise AssertionError(
                f"A6 {operation}::{pointer}: want the digest map container, found "
                f"{type(value).__name__} — {FIX}")
        selected = []
        for key, item in value.items():
            if not isinstance(key, str):
                raise AssertionError(
                    f"A6 {operation}::{pointer}: want string map keys — {FIX}")
            selected.append(
                (f"{pointer}/{_escape_pointer_part(key)}", item))
        return selected
    raise AssertionError(
        f"A6 {operation}::{pointer}: unknown owner shape {owner_shape!r} — {FIX}")


def check_owner_value(owner: str, sub_pointer: str, value: object, *,
                      manifest=None, repo=None, candidates=(),
                      repository=None, delivery_dir=None,
                      delivery_sha256=None, artifact_map=None,
                      executed=None, service=None, registry=None,
                      root=None, target_kind="garden-note"):
    """Execute the real owner for one governed scalar (SPEC (ay)).

    Appends ``sub_pointer`` to ``executed`` (proving no governed scalar is
    skipped), then runs the existing owner. Only the three approved owner
    names dispatch; owner refusals propagate with their original class and
    message.
    """
    if executed is not None:
        executed.append(sub_pointer)
    if owner == "inspect-reference":
        payload = platform_handlers.record_payload(manifest, value)
        if payload is None:
            payload = platform_handlers.structural_payload(
                manifest, value, repo)
        if payload is None:
            return ("miss", platform_handlers.inspect_not_found(
                value, candidates))
        return ("resolved", payload)
    if owner == "ai-delivery-exchange":
        checked = FilesystemAIActionRepository._id(value)
        directory = repository.delivery_dir(checked)
        read_bound_delivery(
            directory, delivery_sha256=delivery_sha256,
            artifact_sha256=artifact_map)
        return ("bound", directory)
    if owner == "ai-delivery-artifact-digests":
        key = sub_pointer.rsplit("/", 1)[-1].replace("~1", "/").replace("~0", "~")
        validated = validated_sha256(
            value, label=f"artifact_sha256[{key}]")
        read_bound_delivery(
            delivery_dir, delivery_sha256=delivery_sha256,
            artifact_sha256=artifact_map)
        return ("bound-value", validated)
    # Builder Task 78 ((cx) D-6/D-7/D-8): each branch executes the
    # same getter its handler reaches; misses propagate with their
    # original class and message, carrying the loaded domain.
    if owner == "ai-request-store":
        return ("resolved", repository.get_request(value))
    if owner == "ai-delivery-store":
        delivery, _directory = repository.get_delivery(value)
        return ("resolved", delivery)
    if owner == "ai-action-registry":
        return ("resolved", registry.get(value))
    if owner == "ai-action-target":
        target, _path = service._target(value, target_kind)
        return ("resolved", target)
    if owner == "operations-trace-request":
        from learning_os.domain.failures import NotFound

        detail, domain = platform_handlers._describe_operation(root, value)
        if detail is None:
            raise NotFound("request", value, domain,
                           message="unknown request_id")
        return ("resolved", detail)
    if owner == "masters-candidate-module":
        from learning_os.app.admin import masters_planning
        from learning_os.derive import masters_catalog

        catalog = masters_catalog.load_master_catalog(root)
        assert catalog is not None, (
            f"A6 {owner}: no catalog at the fixture root — {FIX}")
        modules = {row["id"]: row for row in catalog["candidate_modules"]}
        if value not in modules:
            raise masters_planning.UnknownCandidateModule(
                "candidate module", value, list(modules),
                message=(f"comparison targets unknown candidate module: "
                         f"{value}"))
        return ("resolved", modules[value])
    if owner == "related-record":
        from learning_os.domain.suggest import not_found

        by_id = {row.get("id"): row for row in manifest["records"]}
        resolved_id = (manifest.get("project_aliases") or {}).get(value, value)
        if resolved_id not in by_id:
            return ("miss", not_found("record", value, by_id))
        return ("resolved", by_id[resolved_id])
    raise AssertionError(f"A6 unknown validation owner {owner!r} — {FIX}")


def _synthetic_manifest():
    """A manifest exercising every inspect resolution class (SPEC (ay)).

    Record ids, one old project alias, a curriculum stage, a detour, two
    project structure nodes (nested), a project milestone, and one id
    shared by two owners (ambiguity). Path stages come from the paired
    synthetic repo (they are not projected).
    """
    manifest = {
        "records": [
            {"id": "note-demo", "type": "note", "path": "knowledge/notes/note-demo.md"},
            {"id": "project-demo", "type": "project",
             "path": "work/projects/project-demo.yaml",
             "structure": {"nodes": [
                 {"id": "step-top", "children": [
                     {"id": "step-nested", "children": []}]},
                 {"id": "workstream-1", "children": []},
                 {"id": "shared-x", "children": []},
             ]},
             "milestone_ids": ["milestone-1"]},
        ],
        "project_aliases": {"module-old": "project-demo"},
        "stages": [
            {"id": "stage-l01", "unit_id": "unit-demo-l01",
             "study_map_id": "map-l01", "module_id": "module-demo"},
        ],
        "study_maps": [
            {"id": "map-l01", "unit_id": "unit-demo-l01",
             "module_id": "module-demo",
             "detours": [{"id": "detour-1"}, {"id": "shared-x"}]},
        ],
    }
    return manifest


def _synthetic_repo():
    """A repo stub carrying one learning-path stage (SPEC (ay))."""
    from types import SimpleNamespace

    return SimpleNamespace(learning_paths={
        "path-demo": SimpleNamespace(
            id="path-demo",
            data={"stages": [{"id": "stage-path-1"}]},
            workspace_id="workspace-demo",
            archived=False,
        ),
    })


def test_owner_table_matches_the_inventory_exactly():
    rows = yaml.safe_load(
        (ROOT / "tests/architecture/id-fields.yaml").read_text(
            encoding="utf-8"))["fields"]
    assert len(SUPPORTED_OWNER_ROWS) == 12
    tabled = set(SUPPORTED_OWNER_ROWS)
    inventory = {}
    for row in rows:
        if row.get("kind") is None and row.get("lookup") is True:
            key = (row["operation"], row["pointer"])
            assert key not in inventory, f"A6 duplicate owner row {key} — {FIX}"
            inventory[key] = (row.get("owner"), row.get("owner_shape"))
    assert set(inventory) == tabled, (
        "A6 owner inventory drift: "
        f"missing={sorted(tabled - set(inventory))} "
        f"extra={sorted(set(inventory) - tabled)} — {FIX}")
    for key, want in sorted(SUPPORTED_OWNER_ROWS.items()):
        assert inventory[key] == want, f"A6 {key}: {inventory[key]} != {want} — {FIX}"
        row = next(r for r in rows
                   if (r["operation"], r["pointer"]) == key)
        assert "review" not in row, f"A6 {key} still under review — {FIX}"
        assert isinstance(row.get("decision"), str) and row["decision"], (
            f"A6 {key} lacks dated conductor provenance — {FIX}")


#: Task 73 decision 4: ownership-identity rows that select or create a
#: window instead of looking up a known-ID inventory. (operation, pointer)
#: -> the decided reason. Only these exact rows may carry null kind with
#: lookup false, the schema marker and dated provenance, and no review;
#: every other null kind without a supported owner keeps its review.
NONLOOKUP_IDENTITY_ROWS: dict[tuple[str, str], str] = {
    ("session.end", "/properties/session_id"):
        "selects/creates the ownership window; never a known-ID lookup",
    # Builder Task 78 ((cx) D-6): the two further decided identities.
    # Creation and ownership ids have no typo lookup domain, so no
    # candidate inventory is ever enumerated for them.
    ("ai-action.prepare", "/properties/request_id"):
        "caller-supplied creation identity; never a known-ID lookup",
    ("goal.decide", "/properties/session_id"):
        "ownership-window identity; never a known-ID lookup",
}


def _assert_decided_nonlookup_identity(row: dict) -> None:
    """The exact decided nonlookup shape, row and schema marker (T73-4)."""
    from learning_os.store.contracts.requests import request_schema

    key = (row["operation"], row["pointer"])
    reason = NONLOOKUP_IDENTITY_ROWS[key]
    assert row.get("kind") is None, f"A6 {key}: nonlookup keeps null kind — {FIX}"
    assert row.get("lookup") is False, (
        f"A6 {key}: nonlookup sits at lookup false — {FIX}")
    assert "review" not in row, (
        f"A6 {key}: decided nonlookup carries no review — {FIX}")
    decision = row.get("decision")
    assert isinstance(decision, str) and reason in decision \
        and "2026-10-12" in decision, (
            f"A6 {key}: nonlookup lacks the dated decided reason — {FIX}")
    node = _navigate(request_schema(ROOT, row["operation"]), row["pointer"])
    assert isinstance(node, dict), (
        f"A6 {key}: inventory pointer missing from the schema — {FIX}")
    assert node.get("x-los-lookup") is False, (
        f"A6 {key}: schema marker is not lookup false — {FIX}")
    assert "x-los-id-kind" not in node and "x-los-id-owner" not in node, (
        f"A6 {key}: null kind carries no kind/owner marker — {FIX}")


def test_unresolved_null_kinds_keep_review_and_skip():
    """Null kinds without a supported owner stay failing/skipped, never pass."""
    rows = yaml.safe_load(
        (ROOT / "tests/architecture/id-fields.yaml").read_text(
            encoding="utf-8"))["fields"]
    for row in rows:
        key = (row["operation"], row["pointer"])
        if row.get("kind") is not None or key in SUPPORTED_OWNER_ROWS:
            continue
        if key in NONLOOKUP_IDENTITY_ROWS:
            _assert_decided_nonlookup_identity(row)
            continue
        assert "review" in row, (
            f"A6 {key}: null kind without an owner or review would pass "
            f"silently — {FIX}")


def test_nonlookup_allowance_covers_only_the_decided_row():
    """Any other unresolved row still fails; the decided shape is exact."""
    live = yaml.safe_load(
        (ROOT / "tests/architecture/id-fields.yaml").read_text(
            encoding="utf-8"))["fields"]
    decided = next(row for row in live
                   if (row["operation"], row["pointer"])
                   in NONLOOKUP_IDENTITY_ROWS)
    _assert_decided_nonlookup_identity(dict(decided))

    def rejects(mutator):
        mutant = dict(decided)
        mutator(mutant)
        with pytest.raises(AssertionError):
            _assert_decided_nonlookup_identity(mutant)

    rejects(lambda row: row.update(lookup=True))
    rejects(lambda row: row.update(lookup=None))
    rejects(lambda row: row.update(kind="session"))
    rejects(lambda row: row.update(review="unknown id prefix 'session'"))
    rejects(lambda row: row.update(decision="undated reason"))
    rejects(lambda row: row.pop("decision"))
    # An undecided row cannot borrow the allowance: it is not tabled.
    other = next(row for row in live
                 if row.get("kind") is None
                 and (row["operation"], row["pointer"])
                 not in NONLOOKUP_IDENTITY_ROWS
                 and (row["operation"], row["pointer"])
                 not in SUPPORTED_OWNER_ROWS)
    assert "review" in other
    assert (other["operation"], other["pointer"]) \
        not in NONLOOKUP_IDENTITY_ROWS


def test_owner_selection_covers_scalar_items_and_mapping_values():
    request = {"id": "note-demo", "more_ids": ["stage-l01", "detour-1"],
               "artifact_sha256": {"b.md": "sha256:" + "b" * 64,
                                   "a.md": "sha256:" + "a" * 64}}
    assert owner_selected_values(
        "project.inspect", "/properties/id", request) == [
            ("/properties/id", "note-demo")]
    assert owner_selected_values(
        "project.inspect", "/properties/more_ids/items", request) == [
            ("/properties/more_ids/items/0", "stage-l01"),
            ("/properties/more_ids/items/1", "detour-1")]
    assert owner_selected_values(
        "ai-action.delivery.apply", "/properties/artifact_sha256",
        request) == [
            ("/properties/artifact_sha256/b.md", "sha256:" + "b" * 64),
            ("/properties/artifact_sha256/a.md", "sha256:" + "a" * 64)]
    # The alias rows select through the same shapes as the primary.
    assert owner_selected_values(
        "project.inspect", "/properties/id", request) == [
            ("/properties/id", "note-demo")]
    assert owner_selected_values(
        "project.inspect", "/properties/more_ids/items", request) == [
            ("/properties/more_ids/items/0", "stage-l01"),
            ("/properties/more_ids/items/1", "detour-1")]


def test_owner_selection_fails_closed():
    request = {"id": "note-demo", "more_ids": ["stage-l01"],
               "artifact_sha256": {"a.md": "x"}}
    with pytest.raises(AssertionError):
        owner_selected_values("note.search", "/properties/id", request)
    with pytest.raises(AssertionError):
        owner_selected_values("project.inspect", "/properties/id", {})
    with pytest.raises(AssertionError):
        owner_selected_values(
            "project.inspect", "/properties/id", {"id": ["note-demo"]})
    with pytest.raises(AssertionError):
        owner_selected_values(
            "project.inspect", "/properties/more_ids/items",
            {"more_ids": "stage-l01"})
    with pytest.raises(AssertionError):
        owner_selected_values(
            "project.inspect", "/properties/more_ids/items",
            {"more_ids": ["ok", 7]})
    with pytest.raises(AssertionError):
        owner_selected_values(
            "ai-action.delivery.apply", "/properties/artifact_sha256",
            {"artifact_sha256": ["a.md"]})
    with pytest.raises(AssertionError):
        check_owner_value("invented-owner", "/properties/id", "x")


def test_inspect_owner_resolves_every_class_alias_and_order():
    import copy

    manifest = _synthetic_manifest()
    repo = _synthetic_repo()
    frozen = copy.deepcopy(manifest)
    candidates = platform_handlers._inspect_candidates(manifest, repo)
    assert candidates == [
        "note-demo", "project-demo", "stage-l01", "detour-1", "shared-x",
        "step-top", "step-nested", "workstream-1", "shared-x",
        "milestone-1", "stage-path-1",
    ]
    executed = []
    # Every candidate resolves through the real owner, in requested order.
    requested = ["note-demo", "stage-l01", "detour-1", "step-nested",
                 "workstream-1", "milestone-1", "stage-path-1", "shared-x"]
    payloads = [
        check_owner_value(
            "inspect-reference", f"/properties/more_ids/items/{i}", value,
            manifest=manifest, repo=repo, candidates=candidates,
            executed=executed)[1]
        for i, value in enumerate(requested)]
    assert [p["id"] for p in payloads] == requested
    assert payloads[0]["path"] == "knowledge/notes/note-demo.md"
    assert payloads[1]["structural_kind"] == "curriculum-stage"
    assert payloads[1]["edit_via"] == "plan-edit-context unit-demo-l01 --stage-id stage-l01"
    assert payloads[2]["structural_kind"] == "detour"
    assert payloads[3]["structural_kind"] == "project-node"
    assert payloads[3]["node_path"] == ["step-top", "step-nested"]
    assert payloads[4]["structural_kind"] == "project-node"
    assert payloads[5]["structural_kind"] == "project-milestone"
    assert payloads[5]["project_id"] == "project-demo"
    assert payloads[6]["structural_kind"] == "path-stage"
    assert payloads[6]["path_id"] == "path-demo"
    assert payloads[7]["structural_kind"] == "ambiguous"
    assert [c["structural_kind"] for c in payloads[7]["candidates"]] == [
        "detour", "project-node"]
    # Alias equivalence: the old alias resolves to the same record.
    status, aliased = check_owner_value(
        "inspect-reference", "/properties/id", "module-old",
        manifest=manifest, repo=repo, candidates=candidates,
        executed=executed)
    assert status == "resolved"
    assert aliased["id"] == "project-demo"
    assert aliased["resolved_from"] == "module-old"
    assert executed == [
        "/properties/more_ids/items/0", "/properties/more_ids/items/1",
        "/properties/more_ids/items/2", "/properties/more_ids/items/3",
        "/properties/more_ids/items/4", "/properties/more_ids/items/5",
        "/properties/more_ids/items/6", "/properties/more_ids/items/7",
        "/properties/id",
    ]
    assert manifest == frozen, f"A6 the inspect owner mutated its input — {FIX}"


def test_inspect_owner_miss_keeps_message_and_candidates():
    import copy

    manifest = _synthetic_manifest()
    repo = _synthetic_repo()
    frozen = copy.deepcopy(manifest)
    candidates = platform_handlers._inspect_candidates(manifest, repo)
    status, message = check_owner_value(
        "inspect-reference", "/properties/id", "note-demx",
        manifest=manifest, repo=repo, candidates=candidates)
    assert status == "miss"
    assert message.startswith("record not found: note-demx")
    assert "note-demo" in message
    status, structural = check_owner_value(
        "inspect-reference", "/properties/id", "stage-zzz",
        manifest=manifest, repo=repo, candidates=candidates)
    assert status == "miss"
    assert structural.startswith("record not found: stage-zzz (no curriculum stage")
    assert manifest == frozen, f"A6 the inspect owner mutated its input — {FIX}"


def _staged_delivery(directory, artifacts):
    """Stage a hash-bound delivery: delivery.yaml plus artifact bytes.

    Returns ``(delivery_sha256, artifact_sha256)`` for the staged bytes.
    """
    import hashlib

    directory.mkdir(parents=True, exist_ok=True)
    for ref, content in artifacts.items():
        target = directory / ref
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    blob = yaml.safe_dump(
        {"operations": [{"artifact_ref": ref} for ref in artifacts]},
        sort_keys=True).encode("utf-8")
    (directory / "delivery.yaml").write_bytes(blob)
    return ("sha256:" + hashlib.sha256(blob).hexdigest(),
            {ref: "sha256:" + hashlib.sha256(content).hexdigest()
             for ref, content in artifacts.items()})


def _delivery_exchange(tmp_path, delivery_id="demo-delivery"):
    """A repository root with one staged three-artifact delivery."""
    repository = FilesystemAIActionRepository(tmp_path / "repo")
    directory = repository.delivery_dir(delivery_id)
    delivery_sha256, artifact_map = _staged_delivery(directory, {
        "artifacts/first.md": b"first bytes",
        "artifacts/second.md": b"second bytes",
        "artifacts/last.md": b"last bytes",
    })
    return repository, directory, delivery_sha256, artifact_map


def _tree_inventory(root):
    """(relative path, kind, sha256-or-target) rows for every entry."""
    import hashlib

    rows = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_symlink():
            rows.append((rel, "symlink", str(path.readlink())))
        elif path.is_file():
            rows.append((rel, "file",
                         hashlib.sha256(path.read_bytes()).hexdigest()))
        elif path.is_dir():
            rows.append((rel, "dir", ""))
    return rows


def _mapped_refusal(exc):
    """The converted pipeline's (code, retryable, exit) for a delivery failure."""
    from learning_os.app.handlers import ai as ai_handler

    typed = ai_handler._refusal(exc, "ai-action.delivery.apply")
    return (typed.gateway_code, typed.gateway_retryable, typed.exit_code)


def test_exchange_owner_binds_grammar_lookup_and_binding(tmp_path):
    for delivery_id in ("demo-delivery", "abc", "d_1", "d.1"):
        repository, directory, delivery_sha256, artifact_map = _delivery_exchange(
            tmp_path / delivery_id, delivery_id)
        staged = _tree_inventory(tmp_path / delivery_id)
        status, bound = check_owner_value(
            "ai-delivery-exchange", "/properties/delivery_id", delivery_id,
            repository=repository, delivery_sha256=delivery_sha256,
            artifact_map=dict(artifact_map))
        assert status == "bound"
        assert bound == directory
        assert _tree_inventory(tmp_path / delivery_id) == staged, (
            f"A6 owner reads must not write — {FIX}")


def test_exchange_owner_negatives_keep_class_message_and_exit(tmp_path):
    repository, _, delivery_sha256, artifact_map = _delivery_exchange(tmp_path)
    before = _tree_inventory(tmp_path)
    # Malformed exchange identifiers keep the grammar refusal.
    for bad in ("", "ab", "AB", "has space", "../escape", "a" * 200,
                "note-demo!", "-lead"):
        with pytest.raises(DeliveryValidationError) as raised:
            check_owner_value(
                "ai-delivery-exchange", "/properties/delivery_id", bad,
                repository=repository, delivery_sha256=delivery_sha256,
                artifact_map=dict(artifact_map))
        assert str(raised.value) == f"unsafe exchange identifier: {bad}"
        assert _mapped_refusal(raised.value) == ("INVALID_REQUEST", False, 2)
    # A missing delivery record keeps the binding refusal, not NOT_FOUND.
    with pytest.raises(DeliveryBindingError) as raised:
        check_owner_value(
            "ai-delivery-exchange", "/properties/delivery_id", "demo-missing",
            repository=repository, delivery_sha256=delivery_sha256,
            artifact_map=dict(artifact_map))
    assert str(raised.value) == (
        "approved delivery record is missing or is not a regular file")
    assert _mapped_refusal(raised.value) == ("UNCONFIRMED", False, 2)
    # A symlinked delivery record is not a regular file either.
    link_dir = repository.delivery_dir("demo-link")
    link_dir.mkdir(parents=True)
    (link_dir / "real.yaml").write_text("operations: []\n", encoding="utf-8")
    (link_dir / "delivery.yaml").symlink_to(link_dir / "real.yaml")
    with pytest.raises(DeliveryBindingError) as raised:
        check_owner_value(
            "ai-delivery-exchange", "/properties/delivery_id", "demo-link",
            repository=repository, delivery_sha256=delivery_sha256,
            artifact_map=dict(artifact_map))
    assert str(raised.value) == (
        "approved delivery record is missing or is not a regular file")
    assert _mapped_refusal(raised.value) == ("UNCONFIRMED", False, 2)
    current = _tree_inventory(tmp_path)
    added = [row for row in current if row not in before]
    assert [row[0] for row in added] == [
        "repo/operations/ai-actions/deliveries/demo-link",
        "repo/operations/ai-actions/deliveries/demo-link/delivery.yaml",
        "repo/operations/ai-actions/deliveries/demo-link/real.yaml",
    ], f"A6 owner reads must not write beyond the test's own staging — {FIX}"


def test_digest_owner_binds_every_value_and_exact_keys(tmp_path):
    repository, directory, delivery_sha256, artifact_map = _delivery_exchange(
        tmp_path)
    before = _tree_inventory(tmp_path)
    selected = owner_selected_values(
        "ai-action.delivery.apply", "/properties/artifact_sha256",
        {"artifact_sha256": dict(artifact_map)})
    assert [pointer for pointer, _ in selected] == [
        "/properties/artifact_sha256/artifacts~1first.md",
        "/properties/artifact_sha256/artifacts~1second.md",
        "/properties/artifact_sha256/artifacts~1last.md",
    ]
    executed = []
    for sub_pointer, value in selected:
        status, validated = check_owner_value(
            "ai-delivery-artifact-digests", sub_pointer, value,
            repository=repository, delivery_dir=directory,
            delivery_sha256=delivery_sha256,
            artifact_map=dict(artifact_map), executed=executed)
        assert status == "bound-value"
        assert validated == value
    assert executed == [pointer for pointer, _ in selected]
    assert _tree_inventory(tmp_path) == before


def test_digest_owner_negatives_keep_class_message_and_exit(tmp_path):
    repository, directory, delivery_sha256, artifact_map = _delivery_exchange(
        tmp_path)
    before = _tree_inventory(tmp_path)
    refs = list(artifact_map)

    def run(mapping):
        return check_owner_value(
            "ai-delivery-artifact-digests",
            "/properties/artifact_sha256/artifacts~1first.md",
            mapping["artifacts/first.md"],
            repository=repository, delivery_dir=directory,
            delivery_sha256=delivery_sha256, artifact_map=mapping)

    # A missing key and an extra key break exact binding, each named.
    missing = dict(artifact_map)
    del missing[refs[1]]
    with pytest.raises(DeliveryBindingError) as raised:
        run(missing)
    assert "missing=['artifacts/second.md']" in str(raised.value)
    assert "unexpected=[]" in str(raised.value)
    assert _mapped_refusal(raised.value) == ("UNCONFIRMED", False, 2)
    extra = dict(artifact_map)
    extra["artifacts/extra.md"] = "sha256:" + "e" * 64
    with pytest.raises(DeliveryBindingError) as raised:
        run(extra)
    assert "unexpected=['artifacts/extra.md']" in str(raised.value)
    assert _mapped_refusal(raised.value) == ("UNCONFIRMED", False, 2)
    # Non-string values keep the opaque-admission typed refusal, per value.
    for bad in (7, {"sha256": "x"}, None, ["sha256:" + "a" * 64]):
        broken = dict(artifact_map)
        broken[refs[1]] = bad
        with pytest.raises(DeliveryValidationError) as raised:
            check_owner_value(
                "ai-delivery-artifact-digests",
                "/properties/artifact_sha256/artifacts~1second.md", bad,
                repository=repository, delivery_dir=directory,
                delivery_sha256=delivery_sha256, artifact_map=broken)
        assert str(raised.value) == (
            "artifact_sha256[artifacts/second.md] must be sha256 followed by "
            "64 lowercase hexadecimal digits")
        assert _mapped_refusal(raised.value) == ("INVALID_REQUEST", False, 2)
    # A wrong digest and wrong bytes each name their own artifact_ref,
    # at the second and last positions as well as the first.
    for position in (0, 1, 2):
        broken = dict(artifact_map)
        broken[refs[position]] = "sha256:" + "f" * 64
        with pytest.raises(DeliveryBindingError) as raised:
            check_owner_value(
                "ai-delivery-artifact-digests",
                f"/properties/artifact_sha256/artifacts~1{refs[position].split('/')[-1]}",
                broken[refs[position]],
                repository=repository, delivery_dir=directory,
                delivery_sha256=delivery_sha256, artifact_map=broken)
        assert refs[position] in str(raised.value)
        assert _mapped_refusal(raised.value) == ("UNCONFIRMED", False, 2)
    (directory / "artifacts/last.md").write_bytes(b"tampered bytes")
    with pytest.raises(DeliveryBindingError) as raised:
        run(dict(artifact_map))
    assert "artifacts/last.md" in str(raised.value)
    assert _mapped_refusal(raised.value) == ("UNCONFIRMED", False, 2)
    (directory / "artifacts/last.md").write_bytes(b"last bytes")
    assert _tree_inventory(tmp_path) == before


def test_six_owner_rows_resolved_and_eleven_reviews_retained():
    current = _review_signatures()
    # Builder Task 78 resolved ten further ::review rows; only the
    # unrelated lineage claim review remains undecided.
    assert sum(current.values()) == 1, (
        f"A6 want exactly the 1 retained review: {sorted(current)} — {FIX}")
    removed = {
        "ai-action.delivery.apply::/properties/artifact_sha256::review",
        "ai-action.delivery.apply::/properties/delivery_id::review",
        "project.inspect::/properties/id::review",
        "project.inspect::/properties/more_ids/items::review",

        # Task 73 decision 4: decided nonlookup, not under review.
        "session.end::/properties/session_id::review",
        # Builder Task 78 ((cx) D-6/D-7/D-8): decided lookups and
        # nonlookup identities, no longer under review.
        "ai-action.append-slices::/properties/request_id::review",
        "ai-action.prepare::/properties/action_id::review",
        "ai-action.prepare::/properties/request_id::review",
        "ai-action.prepare::/properties/target_id::review",
        "ai-action.status::/properties/request_id::review",
        "ai-action.delivery.validate::/properties/delivery_id::review",
        "cli.dual::/properties/session_id::review",
        "operations.read::/properties/request_id::review",
        "related.read::/properties/id::review",
        "masters-planning.comparison.publish::/properties/candidate_module_id::review",
    }
    assert not (removed & set(current)), (
        f"A6 resolved rows still under review: {sorted(removed & set(current))} — {FIX}")
    data = yaml.safe_load(RATCHETS_PATH.read_text(encoding="utf-8"))
    recorded = {entry["signature"]
                for entry in data["checks"].get(CHECK_ID, [])}
    assert set(current) == recorded - removed, (
        "A6 retained reviews must equal the recorded entries minus exactly "
        f"the six resolved rows — {FIX}")


def test_inspect_owner_on_a_real_fixture_keeps_handler_refusals(mini_repo):
    """The real inspect handler on a fixture: order, miss, no effects."""
    from scenario_fixtures import rich_world

    from learning_os.app.context import OpContext
    from learning_os.app.projection import fresh_manifest_and_repo as _fresh_manifest_and_repo
    from learning_os.domain.failures import WriteRefused
    from learning_os.store.fingerprint import canonical_fingerprint

    named = rich_world(mini_repo)
    assert named, f"A6 rich_world returned no named ids — {FIX}"
    manifest, repo = _fresh_manifest_and_repo(mini_repo)
    candidates = platform_handlers._inspect_candidates(manifest, repo)
    assert candidates, f"A6 fixture has no inspectable ids — {FIX}"
    before = canonical_fingerprint(mini_repo)
    # Every fixture candidate resolves through the dispatched owner.
    for value in candidates:
        status, _ = check_owner_value(
            "inspect-reference", "/properties/id", value,
            manifest=manifest, repo=repo, candidates=candidates)
        assert status == "resolved", f"A6 fixture id {value!r} misses — {FIX}"
    # Requested batch order and the unknown-id refusal through the handler.
    ctx = OpContext(root=mini_repo, operation="project.inspect",
                    channel="operator", invocation="query", gateway=None)
    first, second = candidates[0], candidates[-1]
    batch = platform_handlers.inspect(
        ctx, {"id": first, "more_ids": [second]})
    assert [row["id"] for row in batch.payload["records"]] == [first, second]
    assert batch.payload["requested_ids"] == [first, second]
    with pytest.raises(WriteRefused) as raised:
        platform_handlers.inspect(ctx, {"id": "note-no-such-record"})
    assert raised.value.site == "project.inspect.unknown-id"
    assert raised.value.exit_code == 2
    assert str(raised.value).startswith(
        "record not found: note-no-such-record")
    assert canonical_fingerprint(mini_repo) == before, (
        f"A6 inspect reads changed canonical bytes — {FIX}")

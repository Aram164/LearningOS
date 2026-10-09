"""Near-miss suggestions for registered operations (SPEC §3.3 A5).

(z) items 3-4, (af), (ay) item 4, (bf) items 3-6: every registered
operation's ``lookup: true``/``tolerant`` rows are probed with a
well-formed near-miss proven absent in the fresh fixture. Misses refuse
(or tolerate) exactly as specified, and the unmodified base succeeds
last. Unregistered operations are baselined ``operation::*`` exceptions.
"""

from __future__ import annotations

import copy
import io
import json
from contextlib import redirect_stderr
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

import learning_os.ops.handlers  # noqa: F401  (registration side effect)
from learning_os.ops.registry import REGISTRY

ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "tests/scenarios/cases"
INVENTORY_PATH = ROOT / "tests/architecture/id-fields.yaml"
RATCHETS_PATH = ROOT / "tests/architecture/ratchets.yaml"
REQUESTS_DIR = ROOT / "system/schema/requests"
RECORDED_DIR = ROOT / "tests/scenarios/recorded"

CHECK_ID = "A5-suggestions"
FIX = "Raise NotFound(kind, value, candidates) (PLAN D3)."


@pytest.fixture(autouse=True)
def _berlin_time(monkeypatch):
    """Pin TZ=Europe/Berlin in-process, restoring afterwards (SPEC §0)."""
    import time

    monkeypatch.setenv("TZ", "Europe/Berlin")
    time.tzset()


class _NoBase(Exception):
    """No marked base governs this pointer (SPEC (z) item 3, (af))."""


def _probe_rows() -> list[dict]:
    """Registered rows with ``lookup: true`` or ``lookup: tolerant``."""
    rows = yaml.safe_load(INVENTORY_PATH.read_text(encoding="utf-8"))["fields"]
    return [row for row in rows
            if row["operation"] in REGISTRY
            and row.get("lookup") in (True, "tolerant")]


def _a5_bases() -> dict[str, list[dict]]:
    """Every marked base case per operation, in case-file order."""
    import scenario_harness as harness

    bases: dict[str, list[dict]] = {}
    for path in sorted(CASES_DIR.glob("*.yaml")):
        doc = harness.load_case_file(path)
        for case in doc.get("cases", []):
            if case.get("a5_base") is True:
                bases.setdefault(path.stem, []).append(case)
    return bases


def _merged_case(operation: str, case: dict) -> dict:
    """The case with its file's fixture context, as the effects test builds it."""
    import scenario_harness as harness

    doc = harness.load_case_file(CASES_DIR / f"{operation}.yaml")
    return {"fixture": doc.get("fixture", "rich_world"),
            "observations": doc["observations"],
            "fixture_mtime": doc.get(
                "fixture_mtime", harness.FIXTURE_MTIME_DEFAULT),
            **case}


def _steps_with_ops(operation, case):
    if case.get("kind") == "sequence":
        return [
            (index, dict(step).get("operation", operation), step)
            for index, step in enumerate(case.get("steps", []))
        ]
    return [(0, operation, case)]


def _pointer_prop(pointer):
    parts = pointer.split("/")
    assert parts[1] == "properties", pointer
    return parts[2], pointer.endswith("/items")


_COMMAND_OPS: dict[str, set[str]] | None = None


def _command_served_ops(argv0: str) -> set[str]:
    """Operations served by one CLI command (aliases included)."""
    global _COMMAND_OPS
    if _COMMAND_OPS is None:
        served: dict[str, set[str]] = {}
        schemas = {
            path.name[: -len(".schema.json")]: path
            for path in REQUESTS_DIR.glob("*.schema.json")
        }
        for op in schemas:
            served.setdefault(op.replace(".", "-"), set()).add(op)
            if op.startswith("cli."):
                served.setdefault(op[len("cli."):], set()).add(op)
        for op, path in schemas.items():
            doc = json.loads(path.read_text(encoding="utf-8"))
            target = doc.get("$ref", "")
            stem = target[: -len(".schema.json")] if target else ""
            if stem in schemas:
                for _command, ops in served.items():
                    if stem in ops:
                        ops.add(op)
        _COMMAND_OPS = served
    return set(_COMMAND_OPS.get(argv0, ()))


def _los_parser(command):
    import los
    from learning_os.contracts.payloads import subparsers

    try:
        return subparsers(los.build_parser())[command]
    except KeyError:
        raise _NoBase(f"unknown CLI command {command!r}") from None


def _parse_cli_request(ctx, operation, step, argv):
    """The base request behind CLI argv, via the real parser."""
    import scenario_harness as harness

    if "request" in step:
        return harness._substitute(copy.deepcopy(step["request"]), ctx)
    words = [str(item) for item in harness._substitute(list(argv), ctx)]
    parser = _los_parser(words[0])
    try:
        namespace, _ = parser.parse_known_args(words[1:])
    except SystemExit as exc:
        raise AssertionError(
            f"A5 {operation}: the real parser crashed on {argv!r} — {FIX}"
        ) from exc
    return {key: value for key, value in vars(namespace).items()
            if not key.startswith("_")}


def _raw_cli_request(operation, step, argv):
    """The same parse without fixture substitution (selection only)."""
    words = [str(item) for item in argv]
    parser = _los_parser(words[0])
    try:
        namespace, _ = parser.parse_known_args(words[1:])
    except SystemExit as exc:
        raise AssertionError(
            f"A5 {operation}: the real parser crashed on {argv!r} — {FIX}"
        ) from exc
    return {key: value for key, value in vars(namespace).items()
            if not key.startswith("_")}


def _carries_value(request: dict, row: dict) -> bool:
    """The request carries a nonempty real value at the row's pointer."""
    prop, is_items = _pointer_prop(row["pointer"])
    if prop not in request:
        return False
    value = request[prop]
    if is_items:
        return (isinstance(value, list) and bool(value)
                and isinstance(value[0], str) and bool(value[0]))
    if row.get("owner_shape") == "mapping-values":
        if not isinstance(value, dict) or not value:
            return False
        first = next(iter(value.values()))
        return isinstance(first, str) and bool(first)
    return isinstance(value, str) and bool(value)


def _step_carries_raw(operation: str, step: dict, row: dict) -> bool:
    """The step carries a value at the pointer (no fixture needed)."""
    transport = step.get("transport")
    if transport == "gateway" or "request" in step:
        return _carries_value(step.get("request", {}), row)
    argv = step.get("argv", [])
    if not argv or operation not in _command_served_ops(str(argv[0])):
        return False
    try:
        request = _raw_cli_request(operation, step, argv)
    except _NoBase:
        return False
    return _carries_value(request, row)


def _select_base(operation: str, row: dict) -> tuple[dict, int, str]:
    """First marked base whose target step carries a value (SPEC (af)).

    The target step is ``a5_step`` when present, else the single step of
    the operation carrying the pointer. Raises _NoBase when no marked
    base qualifies; the base-last run later proves the target succeeds.
    """
    for case in _a5_bases().get(operation, []):
        if case.get("kind") == "sequence" and "a5_step" in case:
            index = case["a5_step"]
            steps = case.get("steps", [])
            if not isinstance(index, int) or not 0 <= index < len(steps):
                continue
            step = steps[index]
            if step.get("operation", operation) != operation:
                continue
            if "transport" not in step:
                continue
            if _step_carries_raw(operation, step, row):
                return case, index, step["transport"]
            continue
        found = []
        for index, eff_op, step in _steps_with_ops(operation, case):
            if eff_op != operation:
                continue
            if "transport" not in step:
                continue
            if _step_carries_raw(operation, step, row):
                found.append((index, step["transport"]))
        if len(found) == 1:
            return case, found[0][0], found[0][1]
    raise _NoBase(f"{operation}::{row['pointer']}::no-base")


def _derive_target(ctx, operation: str, row: dict, case: dict,
                   target_index: int) -> tuple[str, dict, list]:
    """The substituted target request and its probe positions."""
    import scenario_harness as harness

    steps = case.get("steps", []) if case.get("kind") == "sequence" else [case]
    step = steps[target_index]
    transport = step["transport"]
    if transport == "gateway" or "request" in step:
        request = harness._substitute(
            copy.deepcopy(step.get("request", {})), ctx)
    else:
        request = _parse_cli_request(ctx, operation, step, step["argv"])
    prop, is_items = _pointer_prop(row["pointer"])
    value = request.get(prop)
    if is_items:
        if not isinstance(value, list) or not value:
            raise _NoBase(f"{operation}::{row['pointer']}::no-base")
        positions = [("item", index, item)
                     for index, item in enumerate(value)]
    elif row.get("owner_shape") == "mapping-values":
        if not isinstance(value, dict) or not value:
            raise _NoBase(f"{operation}::{row['pointer']}::no-base")
        positions = [("value", key, item) for key, item in value.items()]
    else:
        if not isinstance(value, str) or not value:
            raise _NoBase(f"{operation}::{row['pointer']}::no-base")
        positions = [("scalar", None, value)]
    for _, _, item in positions:
        if not isinstance(item, str) or not item:
            raise _NoBase(f"{operation}::{row['pointer']}::no-base")
    return transport, request, positions


def _probe_positions(positions):
    """First/second/last probes (SPEC (bf) item 3; scalar: one)."""
    if len(positions) <= 2:
        return positions
    first, second, last = positions[0], positions[1], positions[-1]
    return [first, second, last]


def _mutated_step(step, transport, prop, position, miss):
    """The base step with one governed value replaced by its miss."""
    mutant = copy.deepcopy(step)
    if transport == "gateway" or "request" in mutant:
        request = mutant["request"]
        if position[0] == "item":
            request[prop][position[1]] = miss
        elif position[0] == "value":
            request[prop][position[1]] = miss
        else:
            request[prop] = miss
        return mutant
    argv = [str(item) for item in mutant["argv"]]
    base = position[2]
    hits = [i for i, word in enumerate(argv) if word == base]
    if len(hits) != 1:
        raise AssertionError(
            f"A5 argv location of {base!r} is not unique — {FIX}")
    argv[hits[0]] = miss
    mutant["argv"] = argv
    return mutant


# --- the (af) near-miss generator -------------------------------------------

#: The fixed cyclic alphabet (SPEC (af)).
_AF_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"


def _position_order(char: str) -> list[str]:
    """Every replacement for one position, in (af) trial order.

    The priority mutation first (digit +1 mod 10, a→b, b→a, else the
    next character in cyclic order), then the remaining alphabet in
    that same cyclic order starting just after the priority, without
    repeats and never the original character. A character outside the
    alphabet tries the whole alphabet from its first character.
    """
    if char not in _AF_ALPHABET:
        return list(_AF_ALPHABET)
    if char.isdigit():
        priority = str((int(char) + 1) % 10)
    elif char == "a":
        priority = "b"
    elif char == "b":
        priority = "a"
    else:
        priority = _AF_ALPHABET[
            (_AF_ALPHABET.index(char) + 1) % len(_AF_ALPHABET)]
    start = _AF_ALPHABET.index(priority)
    order = [priority]
    for step in range(1, len(_AF_ALPHABET)):
        candidate = _AF_ALPHABET[(start + step) % len(_AF_ALPHABET)]
        if candidate != char:
            order.append(candidate)
    return order


def _near_miss_candidate(value: str, *, parses, validates,
                         forbidden_texts, domain: set[str]) -> str:
    """First one-character mutation passing every (af) filter.

    Last position first, moving right to left; exactly one character
    changed. The candidate must parse, validate at the scalar schema
    pointer, occur in no path spelling or readable content, and be
    absent from the enumerated lookup domain.
    """
    for at in range(len(value) - 1, -1, -1):
        for replacement in _position_order(value[at]):
            candidate = value[:at] + replacement + value[at + 1:]
            if candidate == value:
                continue
            if not parses(candidate):
                continue
            if not validates(candidate):
                continue
            if any(candidate in text for text in forbidden_texts):
                continue
            if candidate in domain:
                continue
            return candidate
    raise AssertionError(
        f"A5 SPEC-GAP: no well-formed absent near-miss for {value!r} — {FIX}")


def _exclusion_texts(root: Path) -> list[str]:
    """Path spellings and readable UTF-8 contents (SPEC (af)).

    Every entry under the fixture's DATA_ROOTS and ``operations``,
    without following symlinks. A candidate occurring anywhere is
    excluded, even in authored prose.
    """
    from learning_os.fingerprint import DATA_ROOTS

    texts = []
    for top in (*DATA_ROOTS, "operations"):
        base = root / top
        if not base.is_dir() or base.is_symlink():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_symlink():
                continue
            texts.append(path.relative_to(root).as_posix())
            if path.is_file():
                try:
                    texts.append(path.read_bytes().decode("utf-8"))
                except (OSError, UnicodeDecodeError):
                    continue
    return texts


def _navigate(doc: dict, pointer: str) -> dict:
    """The subschema at an inventory pointer (the items node for /items)."""
    node = doc
    for part in [item for item in pointer.split("/") if item]:
        node = node[part]
    return node


def _schema_node(operation: str, pointer: str) -> dict:
    """The effective request-schema node at one inventory pointer."""
    from learning_os.contracts.requests import request_schema

    return _navigate(request_schema(ROOT, operation), pointer)


def _parses_for_row(row: dict):
    """The (af) parse filter: the kind grammar, or the owner's own."""
    from learning_os.domain import ids

    kind = row.get("kind")
    if kind is not None:
        return lambda candidate: ids.is_valid(kind, candidate)
    owner = row.get("owner")
    if owner == "ai-delivery-exchange":
        from learning_os.ai_actions.errors import DeliveryValidationError
        from learning_os.ai_actions.storage import (
            FilesystemAIActionRepository,
        )

        def exchange_grammar(candidate: str) -> bool:
            try:
                FilesystemAIActionRepository._id(candidate)
            except DeliveryValidationError:
                return False
            return True

        return exchange_grammar
    if owner == "ai-delivery-artifact-digests":
        from learning_os.ai_actions.binding import validated_sha256
        from learning_os.ai_actions.errors import DeliveryValidationError

        def digest_grammar(candidate: str) -> bool:
            try:
                validated_sha256(candidate, label="artifact_sha256[value]")
            except DeliveryValidationError:
                return False
            return True

        return digest_grammar
    if owner == "inspect-reference":
        return lambda candidate: True
    raise AssertionError(
        f"A5 {row['operation']}::{row['pointer']}: no grammar — {FIX}")


def _validates_for_row(operation: str, row: dict, request: dict,
                      position):
    """The (af) scalar-pointer validation filter.

    Scalars and array items validate the candidate at the pointer
    itself (both digest spellings, as A6 does). Mapping values have no
    value subschema, so the map with the probed value replaced
    validates at the container pointer while the owner grammar checks
    the value itself.
    """
    node = _schema_node(operation, row["pointer"])
    validator = Draft202012Validator(node)
    if row.get("owner_shape") == "mapping-values":
        prop, _ = _pointer_prop(row["pointer"])

        def validates_map(candidate: str) -> bool:
            return validator.is_valid(
                {**request[prop], position[1]: candidate})

        return validates_map
    kind = row.get("kind")

    def validates_scalar(candidate: str) -> bool:
        if kind == "digest":
            from learning_os.domain.ids import Digest

            parsed = Digest.parse(candidate)
            return validator.is_valid(parsed.prefixed()) or validator.is_valid(
                parsed.bare())
        return validator.is_valid(candidate)

    return validates_scalar


# --- lookup domains (SPEC (bf) item 3) --------------------------------------

_DELIVERIES_REL = Path("operations/ai-actions/deliveries")


def _inspect_membership(manifest: dict, ordered: list) -> set:
    """Absence membership: ordered ids plus resolving aliases (bg 2).

    The ordered complaint candidates are unchanged; only the set
    used to prove a proposed miss absent gains every alias that
    actually resolves to an existing inspect record, through the
    existing resolution owner.
    """
    from learning_os.ops.handlers import platform as platform_handlers

    membership = set(ordered)
    for alias in (manifest.get("project_aliases") or {}):
        if isinstance(alias, str) and platform_handlers.record_payload(
                manifest, alias) is not None:
            membership.add(alias)
    return membership


def _lookup_domain(ctx, operation: str, row: dict,
                   request: dict) -> tuple[list, set]:
    """The enumerated lookup domain: ordered ids plus a membership set.

    Each domain comes from the existing read-only loaders: units from
    ``repo.units``; stages from the unit's current study map as
    ``require_stage`` computes them; routes from ``unit_routes`` for the
    unit; inspect references from ``_inspect_candidates``; deliveries
    from the delivery directory entries; digests from the real bound
    digest. The ordered list feeds the complaint template in handler
    traversal order.
    """
    from learning_os.loader import load_repo

    kind = row.get("kind")
    owner = row.get("owner")
    if kind == "unit":
        repo = load_repo(ctx.root)
        ordered = list(repo.units)
        return ordered, set(ordered)
    if kind == "stage":
        repo = load_repo(ctx.root)
        unit = repo.units[request["unit_id"]]
        study_map = repo.study_maps[unit.data["current_study_map"]]
        ordered = [str(entry["id"])
                   for entry in study_map.data.get("stages", []) or []
                   if isinstance(entry, dict) and entry.get("id")]
        return ordered, set(ordered)
    if kind == "route":
        from learning_os.material_refs import unit_routes

        repo = load_repo(ctx.root)
        unit = repo.units[request["unit_id"]]
        source_map = repo.module_source_maps[unit.module_id]
        routes = unit_routes(source_map, unit.module_id, request["unit_id"])
        ordered = [entry["id"] for entry in routes]
        return ordered, set(ordered)
    if owner == "inspect-reference":
        from learning_os.ops._legacy_plumbing import _fresh_manifest_and_repo
        from learning_os.ops.handlers import platform as platform_handlers

        manifest, repo = _fresh_manifest_and_repo(ctx.root)
        ordered = platform_handlers._inspect_candidates(manifest, repo)
        return ordered, _inspect_membership(manifest, ordered)
    if owner == "ai-delivery-exchange":
        deliveries = ctx.root / _DELIVERIES_REL
        ordered = sorted(path.name for path in deliveries.iterdir()
                         ) if deliveries.is_dir() else []
        return ordered, set(ordered)
    if kind == "digest":
        ordered = [request["delivery_sha256"]]
        return ordered, set(ordered)
    if owner == "ai-delivery-artifact-digests":
        ordered = [request["delivery_sha256"],
                   *request["artifact_sha256"].values()]
        return ordered, set(ordered)
    raise AssertionError(
        f"A5 {operation}::{row['pointer']}: no lookup domain — {FIX}")


# --- oracles (SPEC (bf) item 4) ----------------------------------------------

def _gateway_error(result: dict) -> dict:
    stdout_json = result["stdout_json"]
    assert isinstance(stdout_json, dict), (
        f"A5 gateway miss has no JSON stdout — {FIX}")
    assert stdout_json.get("ok") is False, (
        f"A5 gateway miss ok is not false — {FIX}")
    error = stdout_json.get("error")
    assert isinstance(error, dict), (
        f"A5 gateway miss has no error object — {FIX}")
    return error


def _check_canonical_miss(result: dict, *, real_value: str, want_exit: int,
                          want_code: str, want_message: str) -> None:
    """The SPEC oracle for a canonical-kind miss (unit, stage, route)."""
    assert result["exit"] == want_exit, (
        f"A5 canonical miss exits {result['exit']}, want {want_exit} — {FIX}")
    error = _gateway_error(result)
    assert error.get("code") == want_code, (
        f"A5 canonical miss code {error.get('code')!r}, want "
        f"{want_code!r} — {FIX}")
    assert error.get("retryable") is False, (
        f"A5 canonical miss is retryable — {FIX}")
    details = error.get("details")
    assert isinstance(details, dict), (
        f"A5 canonical miss has no details object — {FIX}")
    assert details.get("reason") == "NOT_FOUND", (
        f"A5 canonical miss details.reason is {details.get('reason')!r} — "
        f"{FIX}")
    assert real_value in (details.get("suggestions") or []), (
        f"A5 canonical miss suggestions omit the real value {real_value!r}: "
        f"{details.get('suggestions')!r} — {FIX}")
    assert error.get("message") == want_message, (
        f"A5 canonical miss complaint differs — {FIX}")
    assert result["canonical_changed"] == {}, (
        f"A5 canonical miss changed canonical bytes "
        f"{sorted(result['canonical_changed'])} — {FIX}")
    assert result["receipts"] == [], (
        f"A5 canonical miss committed {result['receipts']} — {FIX}")


def _check_owner_inspect_miss(result: dict, *, miss: str, domain: list,
                              want_exit: int) -> None:
    """The (ay) inspect refusal: original class, code, complaint, exit.

    The D16 ``los: CODE:`` prefix is the reviewed rendering of the
    original ``WriteRefused``; the harness strips it for recording
    comparison (§5.3 item 4), so the oracle asserts the code from the
    refusal table and the complaint against the stripped line.
    """
    import scenario_harness as harness

    from learning_os.domain.failures import WriteRefused
    from learning_os.ops.handlers import platform as platform_handlers
    from learning_os.ops.pipeline import _cli_error_code

    assert result["exit"] == want_exit, (
        f"A5 inspect miss exits {result['exit']}, want {want_exit} — {FIX}")
    assert result["stdout"] == "", (
        f"A5 inspect miss printed stdout {result['stdout'][:200]!r} — {FIX}")
    want_code, _ = _cli_error_code(WriteRefused("x"))
    code_match = harness._D16_RE.match(result["stderr"])
    assert code_match is not None, (
        f"A5 inspect miss stderr lacks the D16 code: "
        f"{result['stderr']!r} — {FIX}")
    assert code_match.group(1) == want_code, (
        f"A5 inspect miss code {code_match.group(1)!r}, want "
        f"{want_code!r} — {FIX}")
    normalized = harness._D16_RE.sub("los: ", result["stderr"])
    want = platform_handlers.inspect_not_found(miss, domain)
    assert normalized == f"los: {want}\n", (
        f"A5 inspect miss complaint differs — {FIX}")
    assert result["outcome"] == "refused", (
        f"A5 inspect miss outcome is {result['outcome']} — {FIX}")
    assert result["canonical_changed"] == {}, (
        f"A5 inspect miss changed canonical bytes "
        f"{sorted(result['canonical_changed'])} — {FIX}")
    assert result["receipts"] == [], (
        f"A5 inspect miss committed {result['receipts']} — {FIX}")


def _check_owner_delivery_miss(result: dict, *, want_exit: int,
                               want_code: str, want_message: str,
                               want_retryable: bool) -> None:
    """An (ay)/digest delivery refusal: original typed failure, no relabel."""
    assert result["exit"] == want_exit, (
        f"A5 delivery miss exits {result['exit']}, want {want_exit} — {FIX}")
    error = _gateway_error(result)
    assert error.get("code") == want_code, (
        f"A5 delivery miss code {error.get('code')!r}, want "
        f"{want_code!r} — {FIX}")
    assert error.get("retryable") is want_retryable, (
        f"A5 delivery miss retryable is {error.get('retryable')} — {FIX}")
    assert error.get("details") == {}, (
        f"A5 delivery miss details are not the original empty object: "
        f"{error.get('details')!r} — {FIX}")
    assert error.get("message") == want_message, (
        f"A5 delivery miss complaint differs — {FIX}")
    assert result["canonical_changed"] == {}, (
        f"A5 delivery miss changed canonical bytes "
        f"{sorted(result['canonical_changed'])} — {FIX}")
    assert result["receipts"] == [], (
        f"A5 delivery miss committed {result['receipts']} — {FIX}")


def _check_tolerant_success(result: dict, *, real_value: str) -> None:
    """A tolerated miss: the characterized success ((z) item 4)."""
    assert result["exit"] == 0, (
        f"A5 tolerated miss exits {result['exit']} — {FIX}")
    assert result["outcome"] == "ok", (
        f"A5 tolerated miss outcome is {result['outcome']} — {FIX}")
    stdout_json = result["stdout_json"]
    assert isinstance(stdout_json, dict), (
        f"A5 tolerated miss has no JSON stdout — {FIX}")
    assert real_value in (stdout_json.get("suggestions") or []), (
        f"A5 tolerated miss suggestions omit the real value {real_value!r} "
        f"— {FIX}")
    assert result["canonical_changed"] == {}, (
        f"A5 tolerated miss changed canonical bytes "
        f"{sorted(result['canonical_changed'])} — {FIX}")


# --- recorded anchors ---------------------------------------------------------

#: The reviewed refusal site per canonical probe pointer: the refusal case
#: carrying that site supplies the expected exit and code. Cross-checked
#: against the case file's own ``expect.site`` at every run.
POINTER_SITE_CASE: dict[tuple[str, str], tuple[str, str]] = {
    ("route.patch", "/properties/unit_id"):
        ("route.patch.unknown-unit", "unknown-unit"),
    ("route.patch", "/properties/route_id"):
        ("route.patch.unknown-route", "unknown-route"),
    ("stage.progress.update", "/properties/unit_id"):
        ("stage.progress.update.unknown-unit", "unknown-unit"),
    ("stage.progress.update", "/properties/stage_id"):
        ("stage.progress.update.unknown-stage", "unknown-stage"),
}

#: The recorded CLI refusal per inspect probe pointer: the expected exit.
INSPECT_REFUSAL_CASE: dict[tuple[str, str], str] = {
    ("cli.inspect", "/properties/id"): "unknown-id",
    ("cli.inspect", "/properties/more_ids/items"): "batch-unknown-member",
    ("project.inspect", "/properties/id"): "unknown-id",
    ("project.inspect", "/properties/more_ids/items"): "batch-unknown-member",
}


def _recorded_exit_and_error(operation: str,
                             case_id: str) -> tuple[int, dict]:
    """Exit plus error object of one recorded refusal (never details)."""
    recorded = json.loads(
        (RECORDED_DIR / operation / f"{case_id}.json").read_text(
            encoding="utf-8"))
    return recorded["exit"], recorded["stdout_json"]["error"]


def _canonical_expectations(operation: str, pointer: str) -> tuple[int, str]:
    """Exit and code from the recorded refusal of the same site."""
    import scenario_harness as harness

    if (operation, pointer) not in POINTER_SITE_CASE:
        raise AssertionError(
            f"A5 {operation}::{pointer}: no reviewed site anchor — {FIX}")
    site, case_id = POINTER_SITE_CASE[(operation, pointer)]
    doc = harness.load_case_file(CASES_DIR / f"{operation}.yaml")
    anchored = [case for case in doc["cases"]
                if case.get("id") == case_id]
    assert len(anchored) == 1, (operation, case_id)
    assert (anchored[0].get("expect") or {}).get("site") == site, (
        f"A5 {operation}/{case_id} no longer carries site {site} — {FIX}")
    exit_code, error = _recorded_exit_and_error(operation, case_id)
    return exit_code, error["code"]


def _canonical_message(operation: str, row: dict, miss: str,
                       domain: list) -> str:
    """The expected complaint, built from the domain's template.

    ``route.patch`` raises the template as its message; the stage
    lookups transcribe it with the ``los: `` gateway prefix
    (``ops/handlers/_shared.py``), as the recordings show.
    """
    from learning_os.domain.suggest import not_found, with_suggestions

    kind = row["kind"]
    if operation == "route.patch" and row["pointer"].endswith("route_id"):
        return with_suggestions(
            f"route {miss} is missing or ambiguous in this unit",
            miss, domain)
    message = not_found(kind, miss, domain)
    if operation == "stage.progress.update":
        return f"los: {message}"
    return message


def _inspect_exit(operation: str, pointer: str) -> int:
    """The recorded exit of the same inspect refusal shape."""
    case_id = INSPECT_REFUSAL_CASE[(operation, pointer)]
    recorded = json.loads(
        (RECORDED_DIR / operation / f"{case_id}.json").read_text(
            encoding="utf-8"))
    return recorded["exit"]


#: Original delivery complaints (``ai_actions/binding.py`` templates,
#: reviewed in ``test_arch_idroundtrip.py`` and the recorded refusals).
_MISSING_RECORD = (
    "approved delivery record is missing or is not a regular file")
_HASH_MISMATCH = (
    "approved delivery content hash does not match the imported delivery record")
_ARTIFACT_MISMATCH = (
    "approved delivery artifact content hash does not match "
    "the imported bytes: {ref}")


def _delivery_expectations(operation: str, row: dict,
                           position) -> tuple[int, str, str, bool]:
    """Exit, code, complaint and retryability for a delivery probe.

    The exit, code and retryability come from the recorded refusal of
    the same binding site; the complaint is the reviewed template with
    the base request's own key. Never a probe's observed output.
    """
    if row["pointer"] == "/properties/delivery_sha256":
        recorded = json.loads(
            (RECORDED_DIR / operation / "sha-mismatch.json").read_text(
                encoding="utf-8"))
        refusal = recorded["steps"][2]
        error = refusal["stdout_json"]["error"]
        return (refusal["exit"], error["code"], _HASH_MISMATCH,
                error["retryable"])
    recorded = json.loads(
        (RECORDED_DIR / operation / "unknown-delivery.json").read_text(
            encoding="utf-8"))
    error = recorded["stdout_json"]["error"]
    if row["pointer"] == "/properties/delivery_id":
        return (recorded["exit"], error["code"], _MISSING_RECORD,
                error["retryable"])
    return (recorded["exit"], error["code"],
            _ARTIFACT_MISMATCH.format(ref=position[1]), error["retryable"])


# --- the sweep ------------------------------------------------------------------

def _sweep_params():
    return sorted((row["operation"], row["pointer"]) for row in _probe_rows())


def _recorded_signatures() -> set[str]:
    data = yaml.safe_load(RATCHETS_PATH.read_text(encoding="utf-8"))
    return {entry["signature"]
            for entry in data["checks"].get(CHECK_ID, [])}


def _assert_gap_recorded(signature: str) -> None:
    assert signature in _recorded_signatures(), (
        f"A5 {signature}: unrecorded gap — {FIX}")


@pytest.mark.parametrize(("operation", "pointer"), _sweep_params())
def test_pointer_misses(tmp_path, operation, pointer):
    import scenario_harness as harness

    rows = {row["pointer"]: row for row in _probe_rows()
            if row["operation"] == operation}
    row = rows[pointer]
    try:
        case, target_index, _ = _select_base(operation, row)
    except _NoBase as exc:
        _assert_gap_recorded(str(exc))
        return
    recorded = _recorded_signatures()
    assert f"{operation}::{pointer}::no-base" not in recorded, (
        f"A5 {operation}::{pointer} is governed but gap-recorded — {FIX}")
    workdir = tmp_path / "world"
    ctx = harness._prepare_world(
        _merged_case(operation, case), operation, workdir)
    try:
        transport, request, positions = _derive_target(
            ctx, operation, row, case, target_index)
    except _NoBase as exc:
        _assert_gap_recorded(str(exc))
        return
    steps = case.get("steps", []) if case.get("kind") == "sequence" else [case]
    for prereq in range(target_index):
        full = {"operation": operation, **steps[prereq]}
        result = harness._run_step(ctx, operation, full, prereq)
        assert result["exit"] == 0, (
            f"A5 {operation}::{pointer}: prerequisite step {prereq} exits "
            f"{result['exit']}: {result['stderr']!r} — {FIX}")
    base_step = dict(steps[target_index])
    if case.get("kind") == "sequence":
        base_step.setdefault("operation", operation)
    texts = _exclusion_texts(ctx.root)
    domain_list, domain_set = _lookup_domain(ctx, operation, row, request)
    prop, _ = _pointer_prop(pointer)
    parses = _parses_for_row(row)
    step_no = 1000
    for position in _probe_positions(positions):
        base_value = position[2]
        validates = _validates_for_row(operation, row, request, position)
        miss = _near_miss_candidate(
            base_value, parses=parses, validates=validates,
            forbidden_texts=texts, domain=domain_set)
        if (operation, pointer) == ("route.patch", "/properties/unit_id"):
            assert miss == "unit-demo-l03", (
                f"A5 route.patch unit probe uses {miss!r}, want the (af) "
                f"collision candidate unit-demo-l03 — {FIX}")
        mutant = _mutated_step(base_step, transport, prop, position, miss)
        if case.get("kind") == "sequence":
            mutant.setdefault("operation", operation)
        step_no += 1
        result = harness._run_step(ctx, operation, mutant, step_no)
        _check_probe(result, operation, row, position,
                     base_value, miss, domain_list)
    final = harness._run_step(ctx, operation, dict(base_step), 2000)
    assert final["exit"] == 0, (
        f"A5 {operation}::{pointer}: base {case['id']} step {target_index} "
        f"exits {final['exit']}: {final['stderr']!r} "
        f"{final['stdout'][:200]!r} — {FIX}")
    harness.check_witnesses(ctx)


def _check_probe(result: dict, operation: str, row: dict, position,
                 real_value: str, miss: str, domain_list: list) -> None:
    """Dispatch one probe result to its row-class oracle."""
    if row.get("lookup") == "tolerant":
        _check_tolerant_success(result, real_value=real_value)
        return
    owner = row.get("owner")
    if owner == "inspect-reference":
        _check_owner_inspect_miss(
            result, miss=miss, domain=domain_list,
            want_exit=_inspect_exit(operation, row["pointer"]))
        return
    if owner in ("ai-delivery-exchange", "ai-delivery-artifact-digests") or (
            row.get("kind") == "digest"
            and operation == "ai-action.delivery.apply"):
        want_exit, want_code, want_message, want_retryable = (
            _delivery_expectations(operation, row, position))
        _check_owner_delivery_miss(
            result, want_exit=want_exit, want_code=want_code,
            want_message=want_message, want_retryable=want_retryable)
        return
    want_exit, want_code = _canonical_expectations(
        operation, row["pointer"])
    _check_canonical_miss(
        result, real_value=real_value, want_exit=want_exit,
        want_code=want_code,
        want_message=_canonical_message(operation, row, miss, domain_list))


# --- the exception census -------------------------------------------------------

def _unregistered_universe() -> set[str]:
    """Every request-schema operation minus the registered names."""
    schemas = {path.name[: -len(".schema.json")]
               for path in REQUESTS_DIR.glob("*.schema.json")}
    return schemas - set(REGISTRY)


def _check_star_census(recorded_star: set[str]) -> None:
    """The recorded ``operation::*`` set equals the unregistered universe."""
    expected = {f"{operation}::*" for operation in _unregistered_universe()}
    assert recorded_star == expected, (
        "A5 star census drift: "
        f"new={sorted(recorded_star - expected)} "
        f"fixed={sorted(expected - recorded_star)} — {FIX}")


def test_star_exceptions_match_the_unregistered_universe():
    recorded = {signature for signature in _recorded_signatures()
                if signature.endswith("::*")}
    _check_star_census(recorded)
    for signature in _recorded_signatures():
        assert (signature.endswith("::*") or "::review" in signature
                or signature.endswith("::no-base")), (
                f"A5 {signature}: unknown exception shape — {FIX}")


def test_review_exceptions_match_registered_undecided_rows():
    rows = yaml.safe_load(INVENTORY_PATH.read_text(encoding="utf-8"))["fields"]
    expected = {f"{row['operation']}::{row['pointer']}::review"
                for row in rows
                if row["operation"] in REGISTRY and "review" in row}
    recorded = {signature for signature in _recorded_signatures()
                if "::review" in signature}
    assert recorded == expected, (
        "A5 review census drift: "
        f"new={sorted(recorded - expected)} "
        f"fixed={sorted(expected - recorded)} — {FIX}")


def test_star_census_rejects_extra_and_missing():
    expected = {f"{operation}::*" for operation in _unregistered_universe()}
    with pytest.raises(AssertionError, match="star census"):
        _check_star_census(expected | {"route.patch::*"})
    missing = set(expected)
    missing.pop()
    with pytest.raises(AssertionError, match="star census"):
        _check_star_census(missing)


def test_selection_without_eligible_base_fails_closed():
    row = {"operation": "route.patch",
           "pointer": "/properties/expected_snapshot"}
    with pytest.raises(_NoBase):
        _select_base("route.patch", row)
    with pytest.raises(AssertionError, match="unrecorded gap"):
        _assert_gap_recorded("route.patch::/properties/expected_snapshot::no-base")


# --- required controls (SPEC (z)/(af)/(bf)) ---------------------------------------

def test_l01_l02_collision_selects_l03():
    """The (af) collision: l02 excluded, l03 first absent (no fixture)."""
    from learning_os.domain import ids

    node = _schema_node("route.patch", "/properties/unit_id")
    validator = Draft202012Validator(node)
    miss = _near_miss_candidate(
        "unit-demo-l01",
        parses=lambda candidate: ids.is_valid("unit", candidate),
        validates=validator.is_valid,
        forbidden_texts=["unit-demo-l02"],
        domain={"unit-demo-l01", "unit-demo-l02"})
    assert miss == "unit-demo-l03", f"A5 collision miss is {miss!r} — {FIX}"


def test_mutually_exclusive_fields_select_separate_bases():
    """plan-edit-context's exclusive fields keep separate bases (SPEC (af))."""
    operation = "cli.plan-edit-context"
    route_id = {"operation": operation, "pointer": "/properties/route_id"}
    route_ids = {"operation": operation,
                 "pointer": "/properties/route_ids/items"}
    stage_id = {"operation": operation, "pointer": "/properties/stage_id"}
    unit_id = {"operation": operation, "pointer": "/properties/unit_id"}
    assert _select_base(operation, route_id)[0]["id"] == "route"
    assert _select_base(operation, route_ids)[0]["id"] == "batch"
    assert _select_base(operation, stage_id)[0]["id"] == "stage"
    assert _select_base(operation, unit_id)[0]["id"] == "full"
    bases = {_select_base(operation, row)[0]["id"]
             for row in (route_id, route_ids, stage_id)}
    assert bases == {"route", "batch", "stage"}


def test_real_parser_rejects_combined_exclusive_argv():
    """The real parser refuses --route-id with --stage-id (SPEC (af))."""
    import los

    parser = los.build_parser()
    argv = ["plan-edit-context", "unit-demo-l01",
           "--route-id", "route-b2f1f80014860a929a3af0bc",
           "--stage-id", "stage-demo"]
    with redirect_stderr(io.StringIO()):
        with pytest.raises(SystemExit) as rejected:
            parser.parse_args(argv)
    assert rejected.value.code == 2


def _passing_canonical_result():
    """A synthetic canonical refusal every oracle clause accepts."""
    from learning_os.domain.suggest import not_found, suggestions

    domain = ["unit-demo-l01", "unit-demo-l02", "unit-demo-l09"]
    miss = "unit-demo-l03"
    message = not_found("unit", miss, domain)
    return {
        "exit": 2,
        "stdout": json.dumps({"ok": False}),
        "stderr": "",
        "stdout_json": {
            "ok": False,
            "error": {"code": "INVALID_REQUEST", "message": message,
                      "retryable": False,
                      "details": {"reason": "NOT_FOUND",
                                  "suggestions": suggestions(miss, domain)}}},
        "outcome": "refused",
        "canonical_changed": {},
        "receipts": [],
    }, message


def test_canonical_oracle_accepts_a_clean_refusal():
    result, message = _passing_canonical_result()
    _check_canonical_miss(result, real_value="unit-demo-l01", want_exit=2,
                          want_code="INVALID_REQUEST", want_message=message)


def _check_passing_with(mutator):
    result, message = _passing_canonical_result()
    mutator(result)
    _check_canonical_miss(result, real_value="unit-demo-l01", want_exit=2,
                          want_code="INVALID_REQUEST", want_message=message)


def test_canonical_oracle_negatives_fail_for_the_intended_reason():
    _check_passing_with(lambda result: result)

    def empty_details(result):
        result["stdout_json"]["error"]["details"] = {}

    with pytest.raises(AssertionError, match="details.reason"):
        _check_passing_with(empty_details)

    def no_real_suggestion(result):
        result["stdout_json"]["error"]["details"]["suggestions"] = [
            "unit-demo-l02"]

    with pytest.raises(AssertionError, match="omit the real value"):
        _check_passing_with(no_real_suggestion)

    def changed_bytes(result):
        result["canonical_changed"] = {"records/x.yaml": "state"}

    with pytest.raises(AssertionError, match="changed canonical bytes"):
        _check_passing_with(changed_bytes)

    def committed(result):
        result["receipts"] = ["operations/transactions/TX1.yaml"]

    with pytest.raises(AssertionError, match="committed"):
        _check_passing_with(committed)


def _passing_tolerant_result():
    return {
        "exit": 0,
        "stdout": json.dumps({"ok": True}),
        "stderr": "",
        "stdout_json": {"ok": True, "known_identity": False,
                        "suggestions": ["ability-demo-derive"]},
        "outcome": "ok",
        "canonical_changed": {},
        "receipts": [],
    }


def test_tolerant_oracle_accepts_a_clean_success():
    _check_tolerant_success(_passing_tolerant_result(),
                            real_value="ability-demo-derive")


def test_tolerant_oracle_negative_fails_for_the_intended_reason():
    result = _passing_tolerant_result()
    result["stdout_json"]["suggestions"] = []
    with pytest.raises(AssertionError, match="omit the real value"):
        _check_tolerant_success(result, real_value="ability-demo-derive")


def _aliased_manifest():
    return {
        "records": [{"id": "aa", "type": "note"}],
        "project_aliases": {"ab": "aa"},
    }


def test_resolving_alias_expands_absence_membership():
    """A resolving alias joins the set, never the candidates (bg 2)."""
    from learning_os.ops.handlers import platform as platform_handlers

    manifest = _aliased_manifest()
    ordered = platform_handlers._inspect_candidates(manifest, None)
    assert ordered == ["aa"]
    membership = _inspect_membership(manifest, ordered)
    assert membership == {"aa", "ab"}


def test_resolving_alias_cannot_be_selected_as_a_miss():
    """The membership blocks a resolving alias from miss selection (bg 2)."""
    from learning_os.ops.handlers import platform as platform_handlers

    manifest = _aliased_manifest()
    membership = _inspect_membership(manifest, ["aa"])
    filters = {"parses": lambda candidate: True,
               "validates": lambda candidate: True,
               "forbidden_texts": []}
    assert _near_miss_candidate("aa", domain=set(), **filters) == "ab"
    assert _near_miss_candidate("aa", domain=membership, **filters) == "ac"
    direct = platform_handlers.record_payload(manifest, "aa")
    aliased = platform_handlers.record_payload(manifest, "ab")
    assert aliased is not None
    assert aliased["resolved_from"] == "ab"
    assert {key: aliased[key] for key in direct} == direct


def test_nonresolving_alias_does_not_expand_the_domain():
    """An alias to a missing record stays out of the set (bg 2)."""
    from learning_os.ops.handlers import platform as platform_handlers

    manifest = {"records": [{"id": "aa", "type": "note"}],
                "project_aliases": {"ab": "missing-id"}}
    assert platform_handlers.record_payload(manifest, "ab") is None
    assert _inspect_membership(manifest, ["aa"]) == {"aa"}

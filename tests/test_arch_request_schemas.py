"""A13 request schemas (PLAN D2): descriptions, id rows, CLI binding, success.

Also covers the (ai) alias loader: primary/alias equality, 91 bindings,
107-operation union, forbidden references, chains/cycles.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest
import yaml

from learning_os.contracts.requests import request_schema

ROOT = Path(__file__).resolve().parent.parent
REQUESTS_DIR = ROOT / "system/schema/requests"
ID_FIELDS_PATH = ROOT / "tests/architecture/id-fields.yaml"
RATCHETS_PATH = ROOT / "tests/architecture/ratchets.yaml"
CASES_DIR = ROOT / "tests/scenarios/cases"

CHECK_ID = "A13-request-schemas"
FIX = "Complete the request schema (PLAN D2)."

PLACEHOLDER_MARK = "(no description in the parser yet)"


def _primaries() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted(REQUESTS_DIR.glob("*.schema.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if "$ref" not in data:
            out[path.name[: -len(".schema.json")]] = data
    return out


def _aliases() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for path in sorted(REQUESTS_DIR.glob("*.schema.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if "$ref" in data:
            out[path.name[: -len(".schema.json")]] = data
    return out


def test_alias_documents_have_only_four_keys():
    for operation, data in sorted(_aliases().items()):
        assert set(data.keys()) == {"$schema", "$id", "x-governs", "$ref"}, operation
        assert data["$id"] == f"learningos/requests/{operation}", operation
        assert data["x-governs"] == "artifact", operation


def test_primary_alias_effective_equality_except_id():
    for alias, data in sorted(_aliases().items()):
        primary = data["$ref"][: -len(".schema.json")]
        primary_path = REQUESTS_DIR / f"{primary}.schema.json"
        assert primary_path.is_file(), f"{alias} -> {primary} missing"
        primary_data = json.loads(primary_path.read_text(encoding="utf-8"))
        assert "$ref" not in primary_data, f"{alias} targets {primary} with $ref"
        effective = request_schema(ROOT, alias)
        assert effective["$id"] == data["$id"], alias
        for key, value in primary_data.items():
            if key == "$id":
                continue
            assert effective[key] == value, f"{alias}::{key}"
        assert set(effective.keys()) == set(primary_data.keys()), alias


def test_required_and_defaults_preserved_through_alias():
    for alias in sorted(_aliases()):
        effective = request_schema(ROOT, alias)
        primary = _aliases()[alias]["$ref"][: -len(".schema.json")]
        primary_data = json.loads(
            (REQUESTS_DIR / f"{primary}.schema.json").read_text(encoding="utf-8"))
        assert effective["required"] == primary_data["required"], alias
        for prop, subschema in primary_data.get("properties", {}).items():
            assert effective["properties"][prop]["x-los-cli"]["default"] == \
                subschema["x-los-cli"]["default"], f"{alias}::{prop}"


def test_exactly_91_cli_bindings_and_107_union():
    primaries = _primaries()
    aliases = _aliases()
    with_cli = [op for op, data in primaries.items() if "x-los-cli-command" in data]
    assert len(with_cli) == 91, len(with_cli)
    assert len(primaries) == 91, len(primaries)
    assert len(aliases) == 16, len(aliases)
    union = set(primaries) | set(aliases)
    assert len(union) == 107, len(union)
    cases = {p.name[: -len(".yaml")] for p in CASES_DIR.glob("*.yaml")}
    assert union == cases, f"missing={sorted(cases - union)} extra={sorted(union - cases)}"


def test_no_duplicate_parser_from_aliases():
    for operation, data in sorted(_aliases().items()):
        assert "x-los-cli-command" not in data, operation
        assert "properties" not in data, operation


def test_forbidden_reference_forms_rejected(tmp_path: Path):
    import shutil

    work = tmp_path / "repo"
    shutil.copytree(REQUESTS_DIR, work / "system/schema/requests")
    base_primary = "cli.inspect"
    assert (work / "system/schema/requests" / f"{base_primary}.schema.json").is_file()
    bad_refs = [
        "sub/cli.inspect.schema.json",
        "sub\\cli.inspect.schema.json",
        "../cli.inspect.schema.json",
        "https://example.com/cli.inspect.schema.json",
        "cli.inspect.schema.json#/$defs/x",
        "cli.inspect.schema.json ",
    ]
    for index, ref in enumerate(bad_refs):
        alias = f"alias.bad{index}"
        (work / "system/schema/requests" / f"{alias}.schema.json").write_text(
            json.dumps({
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": f"learningos/requests/{alias}",
                "x-governs": "artifact",
                "$ref": ref,
            }), encoding="utf-8")
        with pytest.raises(ValueError):
            request_schema(work, alias)


def test_reference_chains_and_cycles_rejected(tmp_path: Path):
    import shutil

    work = tmp_path / "repo"
    shutil.copytree(REQUESTS_DIR, work / "system/schema/requests")
    directory = work / "system/schema/requests"
    # Chain: alias -> alias.
    (directory / "alias.chain.schema.json").write_text(json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "learningos/requests/alias.chain",
        "x-governs": "artifact",
        "$ref": "project.inspect.schema.json",
    }), encoding="utf-8")
    with pytest.raises(ValueError):
        request_schema(work, "alias.chain")
    # Cycle: two aliases pointing at each other (both have $ref, so chain).
    (directory / "alias.c1.schema.json").write_text(json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "learningos/requests/alias.c1",
        "x-governs": "artifact",
        "$ref": "alias.c2.schema.json",
    }), encoding="utf-8")
    (directory / "alias.c2.schema.json").write_text(json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "learningos/requests/alias.c2",
        "x-governs": "artifact",
        "$ref": "alias.c1.schema.json",
    }), encoding="utf-8")
    with pytest.raises(ValueError):
        request_schema(work, "alias.c1")


def test_canary_propagates_through_effective_alias(tmp_path: Path):
    import shutil

    work = tmp_path / "repo"
    shutil.copytree(REQUESTS_DIR, work / "system/schema/requests")
    primary_path = work / "system/schema/requests/cli.inspect.schema.json"
    primary = json.loads(primary_path.read_text(encoding="utf-8"))
    primary["properties"]["id"]["description"] = "CANARY-DESCRIPTION"
    primary["properties"]["id"]["x-los-cli"]["default"] = "CANARY-DEFAULT"
    primary_path.write_text(json.dumps(primary, indent=2), encoding="utf-8")
    effective = request_schema(work, "project.inspect")
    assert effective["properties"]["id"]["description"] == "CANARY-DESCRIPTION"
    assert effective["properties"]["id"]["x-los-cli"]["default"] == "CANARY-DEFAULT"
    assert effective["$id"] == "learningos/requests/project.inspect"


def _navigate(doc, pointer):
    node = doc
    for part in pointer.split("/")[1:]:
        part = part.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, dict) else None


def _has_success(operation, cli_name):
    case_path = CASES_DIR / f"{operation}.yaml"
    if not case_path.is_file():
        return False
    for case in yaml.safe_load(case_path.read_text()).get("cases", []):
        if case.get("kind") == "success":
            return True
        if case.get("kind") != "sequence":
            continue
        recorded_path = ROOT / "tests/scenarios/recorded" / operation / f"{case['id']}.json"
        if not recorded_path.is_file():
            continue
        records = json.loads(recorded_path.read_text()).get("steps", [])
        for declared, actual in zip(case.get("steps", []), records, strict=True):
            owns_step = (declared.get("transport") == "gateway"
                         and actual.get("operation") == operation) or (
                             declared.get("transport") == "cli"
                             and declared.get("argv", [None])[0] == cli_name)
            payload = actual.get("stdout_json")
            if owns_step and actual.get("exit") == 0 and not (
                    isinstance(payload, dict) and payload.get("ok") is False):
                return True
    return False


def _current_exceptions() -> Counter[str]:
    current: Counter[str] = Counter()
    rows_by_op: dict[str, list[dict]] = {}
    for row in yaml.safe_load(ID_FIELDS_PATH.read_text())["fields"]:
        rows_by_op.setdefault(row["operation"], []).append(row)
    for path in sorted(REQUESTS_DIR.glob("*.schema.json")):
        operation = path.name[: -len(".schema.json")]
        data = request_schema(ROOT, operation)
        properties = data.get("properties", {})
        for prop, subschema in sorted(properties.items()):
            desc = subschema.get("description", "")
            if not desc or PLACEHOLDER_MARK in desc:
                current[f"{operation}::{prop}::description"] += 1
            if "x-los-cli" not in subschema:
                current[f"{operation}::{prop}::cli"] += 1
        have_pointers = set()
        for row in rows_by_op.get(operation, []):
            parts = row["pointer"].split("/")
            if len(parts) >= 3 and parts[1] == "properties":
                have_pointers.add(parts[2].replace("~1", "/").replace("~0", "~"))
            if row.get("kind") is None:
                continue
            node = _navigate(data, row["pointer"])
            if not isinstance(node, dict) or node.get("type") != "string" or \
                    node.get("x-los-id-kind") != row["kind"] or \
                    node.get("x-los-lookup") != row.get("lookup"):
                current[f"{operation}::{row['pointer']}::id-annotation"] += 1
        for prop in sorted(properties):
            if prop in ("id", "ids") or prop.endswith(("_id", "_ids", "_sha256", "_digest")):
                if prop not in have_pointers:
                    current[f"{operation}::{prop}::id-row"] += 1
        if not _has_success(operation, data["x-los-cli-command"]["name"]):
            current[f"{operation}::*::success"] += 1
    return current


def test_current_exceptions_are_recorded():
    current = _current_exceptions()
    data = yaml.safe_load(RATCHETS_PATH.read_text(encoding="utf-8"))
    recorded = {entry["signature"]: entry["count"]
                for entry in data["checks"].get(CHECK_ID, [])}
    failures = []
    for signature, count in sorted(current.items()):
        if recorded.get(signature, 0) < count:
            failures.append(
                f"A13 {signature}: current count {count} exceeds recorded "
                f"{recorded.get(signature, 0)} — {FIX}")
    for signature in sorted(recorded):
        if signature not in current:
            failures.append(
                f"A13 {signature}: no longer occurs — "
                "remove the fixed exception from ratchets.yaml")
    assert not failures, "\n".join(failures)

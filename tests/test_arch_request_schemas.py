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
from test_arch_idroundtrip import SUPPORTED_OWNER_ROWS

from learning_os.store.contracts.requests import request_schema

ROOT = Path(__file__).resolve().parent.parent
REQUESTS_DIR = ROOT / "system/schema/requests"
ID_FIELDS_PATH = ROOT / "tests/architecture/id-fields.yaml"
RATCHETS_PATH = ROOT / "tests/architecture/ratchets.yaml"
CASES_DIR = ROOT / "tests/scenarios/cases"

CHECK_ID = "A13-request-schemas"
FIX = "Complete the request schema (PLAN D2)."

PLACEHOLDER_MARK = "(no description in the parser yet)"

#: SPEC (bu) 4 and (cq) 2: inventory rows that are not lookups.
#: (operation, pointer) -> reason. Both the id-fields row and the schema
#: annotation sit at ``false``; the D4 purity test tolerates the base
#: annotation flip for exactly these pairs, and nothing else.
BU4_FILTER_NOT_LOOKUP = {
    ("module.list", "/properties/program_id"):
        "SPEC (bu) 4: filter, not a lookup",


    ("plan.template", "/properties/module_id"):
        "SPEC (cq) 2: generated-template seed, not a lookup",
    ("plan.template", "/properties/unit_id"):
        "SPEC (cq) 2: generated-template seed, not a lookup",
}


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


def test_exactly_94_cli_bindings_and_union():
    primaries = _primaries()
    aliases = _aliases()
    with_cli = [op for op, data in primaries.items() if "x-los-cli-command" in data]
    assert len(with_cli) == 94, len(with_cli)
    assert len(primaries) == 94, len(primaries)
    assert len(aliases) == 0, len(aliases)
    union = set(primaries) | set(aliases)
    assert len(union) == 94, len(union)
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
    base_primary = "project.inspect"
    assert (work / "system/schema/requests" / f"{base_primary}.schema.json").is_file()
    bad_refs = [
        "sub/project.inspect.schema.json",
        "sub\\project.inspect.schema.json",
        "../project.inspect.schema.json",
        "https://example.com/project.inspect.schema.json",
        "project.inspect.schema.json#/$defs/x",
        "project.inspect.schema.json ",
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


def test_scheme_operations_rejected_despite_literal_file(tmp_path: Path):
    directory = tmp_path / "repo" / "system/schema/requests"
    directory.mkdir(parents=True)
    for operation in ("file:probe", "urn:probe"):
        literal = directory / f"{operation}.schema.json"
        literal.write_text(json.dumps({
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"learningos/requests/{operation}",
            "type": "object",
        }), encoding="utf-8")
        assert literal.is_file()
        with pytest.raises(ValueError):
            request_schema(tmp_path / "repo", operation)


def test_scheme_ref_targets_rejected_despite_literal_file(tmp_path: Path):
    import shutil

    work = tmp_path / "repo"
    shutil.copytree(REQUESTS_DIR, work / "system/schema/requests")
    directory = work / "system/schema/requests"
    for index, scheme in enumerate(("file", "urn")):
        target = f"{scheme}:project.inspect.schema.json"
        literal = directory / target
        literal.write_text(
            (directory / "project.inspect.schema.json").read_text(
                encoding="utf-8"),
            encoding="utf-8")
        assert literal.is_file()
        alias = f"alias.scheme{index}"
        (directory / f"{alias}.schema.json").write_text(json.dumps({
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": f"learningos/requests/{alias}",
            "x-governs": "artifact",
            "$ref": target,
        }), encoding="utf-8")
        with pytest.raises(ValueError):
            request_schema(work, alias)


def test_reference_chains_and_cycles_rejected(tmp_path: Path):
    import shutil

    work = tmp_path / "repo"
    shutil.copytree(REQUESTS_DIR, work / "system/schema/requests")
    directory = work / "system/schema/requests"
    # Chain: alias -> alias.
    (directory / "alias.inner.schema.json").write_text(json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "learningos/requests/alias.inner", "x-governs": "artifact",
        "$ref": "project.inspect.schema.json",
    }), encoding="utf-8")
    (directory / "alias.chain.schema.json").write_text(json.dumps({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "learningos/requests/alias.chain",
        "x-governs": "artifact",
        "$ref": "alias.inner.schema.json",
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
    primary_path = work / "system/schema/requests/project.inspect.schema.json"
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


def _owner_annotation_ok(row: dict, operation: str) -> bool:
    """Exact metadata/shape/coverage for one supported SPEC (ay) owner row.

    Returns True only when the inventory row carries the exact approved
    owner metadata and the effective schema node (resolved through the
    alias loader, so project.inspect rows cover the primary annotation)
    carries the exact ``x-los-id-owner``/``x-los-lookup`` pair with the
    approved scalar/container shape. Every other null kind stays skipped.
    """
    pointer = row["pointer"]
    try:
        owner, owner_shape = SUPPORTED_OWNER_ROWS[(operation, pointer)]
    except KeyError:
        return True
    if (row.get("owner") != owner
            or row.get("owner_shape") != owner_shape
            or row.get("lookup") is not True):
        return False
    try:
        effective_schema = request_schema(ROOT, operation)
    except (FileNotFoundError, ValueError):
        return False
    parts = pointer.split("/")
    node = effective_schema
    try:
        for part in parts[1:-1]:
            node = node[part]
    except (KeyError, TypeError):
        return False
    prop = parts[-1]
    if not isinstance(node, dict) or prop not in node:
        return False
    annotated = node[prop]
    if not isinstance(annotated, dict):
        return False
    if annotated.get("x-los-id-owner") != owner:
        return False
    if annotated.get("x-los-lookup") is not True:
        return False
    if owner_shape == "scalar":
        return annotated.get("type") == "string"
    if owner_shape == "mapping-values":
        return annotated.get("type") == "object"
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
                # Unresolved inventories are claimed by A6, not A13 —
                # except the six executed SPEC (ay) owners, whose exact
                # annotation A13 pins (alias included).
                if not _owner_annotation_ok(row, operation):
                    current[f"{operation}::{row['pointer']}::id-annotation"] += 1
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


def _a13_work_tree(tmp_path: Path) -> Path:
    import shutil

    work = tmp_path / "repo"
    shutil.copytree(REQUESTS_DIR, work / "system/schema/requests")
    id_fields = work / "tests/architecture/id-fields.yaml"
    id_fields.parent.mkdir(parents=True)
    shutil.copy(ID_FIELDS_PATH, id_fields)
    scenarios = work / "tests/scenarios"
    scenarios.mkdir(parents=True)
    (scenarios / "cases").symlink_to(CASES_DIR, target_is_directory=True)
    (scenarios / "recorded").symlink_to(
        ROOT / "tests/scenarios/recorded", target_is_directory=True)
    return work


def _point_a13_at(monkeypatch, work: Path):
    monkeypatch.setattr("test_arch_request_schemas.ROOT", work)
    monkeypatch.setattr("test_arch_request_schemas.REQUESTS_DIR",
                        work / "system/schema/requests")
    monkeypatch.setattr("test_arch_request_schemas.ID_FIELDS_PATH",
                        work / "tests/architecture/id-fields.yaml")
    monkeypatch.setattr("test_arch_request_schemas.CASES_DIR",
                        work / "tests/scenarios/cases")


def test_collector_is_faithful_on_an_unmodified_copy(tmp_path: Path,
                                                     monkeypatch):
    production = _current_exceptions()
    work = _a13_work_tree(tmp_path)
    _point_a13_at(monkeypatch, work)
    assert _current_exceptions() == production


def test_collector_detects_corruption_through_effective_aliases(
        tmp_path: Path, monkeypatch):
    production = _current_exceptions()
    work = _a13_work_tree(tmp_path)
    requests = work / "system/schema/requests"

    def rewrite(operation, mutate):
        path = requests / f"{operation}.schema.json"
        doc = json.loads(path.read_text(encoding="utf-8"))
        mutate(doc)
        path.write_text(json.dumps(doc), encoding="utf-8")

    # Corrupt primary annotation value (atlas.context backs
    # atlas.context).
    rewrite("atlas.context", lambda doc: doc["properties"][
        "concept_id"].update({"x-los-id-kind": "unit"}))
    # Corrupt scalar shape at a decided pointer.
    rewrite("source.record.revise", lambda doc: doc["properties"][
        "expected_diff_sha256"].update({"type": "integer"}))
    # Blank a real description in an alias primary (note.search backs
    # note.search) and drop sibling CLI metadata.
    rewrite("note.search", lambda doc: doc["properties"]["query"].update(
        {"description": ""}))
    rewrite("note.search",
            lambda doc: doc["properties"]["type"].pop("x-los-cli"))
    # Corrupt an annotation the alias inherits (plan.template backs
    # plan.template).
    rewrite("plan.template", lambda doc: doc["properties"][
        "module_id"].update({"x-los-id-kind": "unit"}))
    # Drop a required id row.
    id_fields = work / "tests/architecture/id-fields.yaml"
    rows = yaml.safe_load(id_fields.read_text(encoding="utf-8"))
    kept = [row for row in rows["fields"]
            if (row["operation"], row["pointer"])
            != ("ability.context", "/properties/ability_id")]
    assert len(kept) == len(rows["fields"]) - 1
    rows["fields"] = kept
    id_fields.write_text(yaml.safe_dump(rows), encoding="utf-8")

    _point_a13_at(monkeypatch, work)
    delta = set((_current_exceptions() - production).elements())
    assert delta == {
        "atlas.context::/properties/concept_id::id-annotation",
        "source.record.revise::/properties/expected_diff_sha256"
        "::id-annotation",
        "ability.context::ability_id::id-row",
        "note.search::query::description",
        "note.search::type::cli",
        "plan.template::/properties/module_id::id-annotation",
    }


def test_sequence_success_must_belong_to_the_target_binding(
        tmp_path: Path, monkeypatch):
    work = tmp_path / "repo"
    cases = work / "cases"
    cases.mkdir(parents=True)
    recorded = work / "tests/scenarios/recorded/synth.op"
    recorded.mkdir(parents=True)

    def add_case(case_id, actual):
        (recorded / f"{case_id}.json").write_text(
            json.dumps({"steps": actual}), encoding="utf-8")

    # A preparatory gateway step succeeds; the target step is refused.
    add_case("prep-ok-target-refused",
             [{"operation": "other.op", "exit": 0,
               "stdout_json": {"ok": True}},
              {"operation": "synth.op", "exit": 2,
               "stdout_json": {"ok": False}}])
    # Same shape over the CLI: the other binding succeeds, ours refuses.
    add_case("cli-prep-ok-target-refused",
             [{"exit": 0, "stdout_json": {"ok": True}},
              {"exit": 2, "stdout_json": {"ok": False}}])
    # A target step that exits 0 with ok:false is still a refusal.
    add_case("target-ok-false",
             [{"operation": "synth.op", "exit": 0,
               "stdout_json": {"ok": False}}])
    (cases / "synth.op.yaml").write_text(yaml.safe_dump({"cases": [
        {"id": "prep-ok-target-refused", "kind": "sequence", "steps": [
            {"transport": "gateway"}, {"transport": "gateway"}]},
        {"id": "cli-prep-ok-target-refused", "kind": "sequence", "steps": [
            {"transport": "cli", "argv": ["other-cmd"]},
            {"transport": "cli", "argv": ["synth-cmd", "x"]}]},
        {"id": "target-ok-false", "kind": "sequence", "steps": [
            {"transport": "gateway"}]},
    ]}), encoding="utf-8")
    monkeypatch.setattr("test_arch_request_schemas.CASES_DIR", cases)
    monkeypatch.setattr("test_arch_request_schemas.ROOT", work)
    assert _has_success("synth.op", "synth-cmd") is False
    # Positive control: the target step succeeding counts.
    (cases / "synth.ok.yaml").write_text(yaml.safe_dump({"cases": [
        {"id": "target-ok", "kind": "sequence", "steps": [
            {"transport": "gateway"}]}]}), encoding="utf-8")
    (work / "tests/scenarios/recorded/synth.ok").mkdir(parents=True)
    (work / "tests/scenarios/recorded/synth.ok/target-ok.json").write_text(
        json.dumps({"steps": [
            {"operation": "synth.ok", "exit": 0,
             "stdout_json": {"ok": True}}]}), encoding="utf-8")
    assert _has_success("synth.ok", "synth-cmd") is True


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


def _rewrite_schema_json(path, mutate):
    doc = json.loads(path.read_text(encoding="utf-8"))
    mutate(doc)
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")


def test_owner_rows_emit_no_annotation_on_the_valid_tree():
    current = _current_exceptions()
    for (operation, pointer) in SUPPORTED_OWNER_ROWS:
        assert current.get(f"{operation}::{pointer}::id-annotation", 0) == 0, (
            f"A13 {operation}::{pointer} fails its own annotation — {FIX}")


def test_owner_annotation_mutants_surface_id_annotation(tmp_path, monkeypatch):
    """Each owner-metadata corruption emits its rows' id-annotation."""
    AI = "ai-action.delivery.apply"

    counter = 0

    def delta(mutator):
        nonlocal counter
        counter += 1
        root = _a13_work_tree(tmp_path / f"mutant-{counter}")
        mutator(root)
        _point_a13_at(monkeypatch, root)
        with pytest.raises(AssertionError) as raised:
            test_current_exceptions_are_recorded()
        return str(raised.value)

    def strip_cli_id_owner(root):
        def edit(doc):
            del doc["properties"]["id"]["x-los-id-owner"]
        _rewrite_schema_json(
            root / "system/schema/requests/project.inspect.schema.json", edit)

    message = delta(strip_cli_id_owner)
    assert "project.inspect::/properties/id::id-annotation" in message
    assert "project.inspect::/properties/id::id-annotation" in message

    def truthy_lookup(root):
        def edit(doc):
            doc["properties"]["delivery_id"]["x-los-lookup"] = 1
        _rewrite_schema_json(
            root / f"system/schema/requests/{AI}.schema.json", edit)

    message = delta(truthy_lookup)
    assert f"{AI}::/properties/delivery_id::id-annotation" in message

    def wrong_owner(root):
        def edit(doc):
            doc["properties"]["more_ids"]["items"]["x-los-id-owner"] = (
                "invented-owner")
        _rewrite_schema_json(
            root / "system/schema/requests/project.inspect.schema.json", edit)

    message = delta(wrong_owner)
    assert "project.inspect::/properties/more_ids/items::id-annotation" in message
    assert "project.inspect::/properties/more_ids/items::id-annotation" in message

    def wrong_shape(root):
        def edit(doc):
            doc["properties"]["more_ids"]["items"]["type"] = "integer"
        _rewrite_schema_json(
            root / "system/schema/requests/project.inspect.schema.json", edit)

    message = delta(wrong_shape)
    assert "project.inspect::/properties/more_ids/items::id-annotation" in message

    def deleted_node(root):
        def edit(doc):
            del doc["properties"]["more_ids"]["items"]
        _rewrite_schema_json(
            root / "system/schema/requests/project.inspect.schema.json", edit)

    message = delta(deleted_node)
    assert "project.inspect::/properties/more_ids/items::id-annotation" in message

    def inventory_owner(root):
        path = root / "tests/architecture/id-fields.yaml"
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        for row in doc["fields"]:
            if (row["operation"] == AI
                    and row["pointer"] == "/properties/delivery_id"):
                row["owner"] = "invented-owner"
        path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    message = delta(inventory_owner)
    assert f"{AI}::/properties/delivery_id::id-annotation" in message

    def mapping_shape(root):
        def edit(doc):
            doc["properties"]["artifact_sha256"]["type"] = "string"
        _rewrite_schema_json(
            root / f"system/schema/requests/{AI}.schema.json", edit)

    message = delta(mapping_shape)
    assert f"{AI}::/properties/artifact_sha256::id-annotation" in message


def test_bu4_filter_rows_are_false_on_both_sides():
    """The enumerated (bu) 4 pairs sit at lookup false, row and schema."""
    rows = {(row["operation"], row["pointer"]): row
            for row in yaml.safe_load(ID_FIELDS_PATH.read_text())["fields"]}
    for (operation, pointer), reason in BU4_FILTER_NOT_LOOKUP.items():
        row = rows[(operation, pointer)]
        assert row.get("lookup") is False, (operation, pointer, reason)
        node = _navigate(request_schema(ROOT, operation), pointer)
        assert isinstance(node, dict), (operation, pointer, reason)
        assert node.get("x-los-lookup") is False, (operation, pointer, reason)


def test_bu4_allowance_covers_no_other_annotation(tmp_path, monkeypatch):
    """Any other annotation change still raises id-annotation."""
    counter = 0

    def delta(mutator):
        nonlocal counter
        counter += 1
        root = _a13_work_tree(tmp_path / f"bu4-{counter}")
        mutator(root)
        _point_a13_at(monkeypatch, root)
        with pytest.raises(AssertionError) as raised:
            test_current_exceptions_are_recorded()
        return str(raised.value)

    def other_operation_lookup(root):
        def edit(doc):
            doc["properties"]["note_id"]["x-los-lookup"] = False
        _rewrite_schema_json(
            root / "system/schema/requests/note.content.schema.json", edit)

    message = delta(other_operation_lookup)
    assert "note.content::/properties/note_id::id-annotation" in message
    assert "note.content::/properties/note_id::id-annotation" in message

    def other_annotation_same_pointer(root):
        def edit(doc):
            doc["properties"]["program_id"]["x-los-id-kind"] = "unit"
        _rewrite_schema_json(
            root / "system/schema/requests/module.list.schema.json", edit)

    message = delta(other_annotation_same_pointer)
    assert ("module.list::/properties/program_id::id-annotation"
            in message)

    def inventory_lookup_back(root):
        path = root / "tests/architecture/id-fields.yaml"
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        for row in doc["fields"]:
            if (row["operation"], row["pointer"]) in BU4_FILTER_NOT_LOOKUP:
                row["lookup"] = True
        path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    message = delta(inventory_lookup_back)
    assert ("module.list::/properties/program_id::id-annotation"
            in message)
    # SPEC (cq) 2: the flip-back above also restores the four
    # generation-input rows; each must raise again.
    for operation, pointer in (
            ("plan.template", "/properties/module_id"),
            ("plan.template", "/properties/unit_id"),
            ("plan.template", "/properties/module_id"),
            ("plan.template", "/properties/unit_id")):
        assert f"{operation}::{pointer}::id-annotation" in message

    def generation_seed_schema_lookup_back(root):
        # A retained true marker on the schema side (the inventory
        # stays false) raises on the primary and, through the
        # effective alias, on plan.template. The work trees nest, so
        # the earlier inventory flip-back is reset for these rows.
        def edit(doc):
            doc["properties"]["module_id"]["x-los-lookup"] = True
        _rewrite_schema_json(
            root / "system/schema/requests/plan.template.schema.json",
            edit)
        path = root / "tests/architecture/id-fields.yaml"
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        for row in doc["fields"]:
            if row["operation"] in ("plan.template", "plan.template"):
                row["lookup"] = False
        path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    message = delta(generation_seed_schema_lookup_back)
    assert ("plan.template::/properties/module_id::id-annotation"
            in message)
    assert ("plan.template::/properties/module_id::id-annotation"
            in message)

    def generation_seed_kind_drift(root):
        def edit(doc):
            doc["properties"]["module_id"]["x-los-id-kind"] = "unit"
        _rewrite_schema_json(
            root / "system/schema/requests/plan.template.schema.json",
            edit)

    message = delta(generation_seed_kind_drift)
    assert ("plan.template::/properties/module_id::id-annotation"
            in message)
    assert ("plan.template::/properties/module_id::id-annotation"
            in message)

    def generation_seed_type_drift(root):
        def edit(doc):
            doc["properties"]["unit_id"]["type"] = "integer"
        _rewrite_schema_json(
            root / "system/schema/requests/plan.template.schema.json",
            edit)

    message = delta(generation_seed_type_drift)
    assert ("plan.template::/properties/unit_id::id-annotation"
            in message)
    assert ("plan.template::/properties/unit_id::id-annotation"
            in message)

    def generation_seed_description_drift(root):
        def edit(doc):
            doc["properties"]["unit_id"]["description"] = ""
        _rewrite_schema_json(
            root / "system/schema/requests/plan.template.schema.json",
            edit)

    message = delta(generation_seed_description_drift)
    assert "plan.template::unit_id::description" in message
    assert "plan.template::unit_id::description" in message

    def generation_seed_inventory_lookup_back(root):
        # Flipping one generation-input inventory row back to true
        # raises exactly that operation's annotation.
        path = root / "tests/architecture/id-fields.yaml"
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        for row in doc["fields"]:
            if (row["operation"], row["pointer"]) == (
                    "plan.template", "/properties/unit_id"):
                row["lookup"] = True
        path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")

    message = delta(generation_seed_inventory_lookup_back)
    assert ("plan.template::/properties/unit_id::id-annotation"
            in message)

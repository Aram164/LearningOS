"""Prototype: Python jsonschema vs Ajv standalone differential agreement.

Paired-gate test: needs the sibling UI checkout (which carries the checked-in
Ajv validator), node, and the v15 bundle. Skips with an explicit reason when
the UI sibling or node is absent, so Core stays usable alone; a missing
checked-in validator is a failure, never a skip. Verdict booleans are
compared, not error sets (Ajv reports short; Python reports all).
"""

from __future__ import annotations

import copy
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from learning_os.contracts.bundle import build_bundle
from learning_os.contracts.json_schema import schema_registry

pytestmark = pytest.mark.full_repo

V15_REL = "system/contracts/manifest-v15.schema.json"
VALIDATOR_REL = "contract-prototype/generated/manifest.validator.cjs"
VERDICT_REL = "scripts/ajv-verdict.mjs"
FIXTURE_REL = "fixture-vault/generated/manifest.json"


class _NoTarget(Exception):
    """A mutation strategy found no suitable instance path in this seed."""


def _paired_ui(repo_root: Path) -> Path:
    ui = repo_root.parent / "obsidian-ui"
    if not ui.is_dir():
        pytest.skip("differential contract test needs the sibling obsidian-ui checkout")
    validator = ui / VALIDATOR_REL
    if not validator.is_file():
        pytest.fail(f"checked-in Ajv validator is missing: {validator}")
    if not (ui / VERDICT_REL).is_file():
        pytest.fail(f"Ajv verdict helper is missing: {ui / VERDICT_REL}")
    if shutil.which("node") is None:
        pytest.skip("differential contract test needs node")
    return ui


def _python_validator(repo_root: Path) -> Draft202012Validator:
    schema = json.loads((repo_root / V15_REL).read_text(encoding="utf-8"))
    return Draft202012Validator(
        schema,
        registry=schema_registry(repo_root / "system" / "schema"),
        format_checker=FormatChecker(),
    )


def _ajv_verdicts(ui: Path, tmp_path: Path, samples: dict[str, Any],
                  subschema: dict | None = None) -> dict[str, dict]:
    paths = []
    for name, value in samples.items():
        sample = tmp_path / f"{name}.json"
        sample.write_text(json.dumps(value), encoding="utf-8")
        paths.append(str(sample))
    command = ["node", str(ui / VERDICT_REL)]
    if subschema is not None:
        schema_path = tmp_path / "subschema.json"
        schema_path.write_text(json.dumps(subschema), encoding="utf-8")
        command += ["--subschema", str(schema_path)]
    else:
        command += [str(ui / VALIDATOR_REL)]
    try:
        completed = subprocess.run(
            command + paths, capture_output=True, text=True, timeout=300, check=False)
    except subprocess.TimeoutExpired as exc:
        pytest.fail(f"ajv-verdict timed out: {exc}")
    if completed.returncode != 0:
        pytest.fail(f"ajv-verdict failed: {completed.stderr.strip()}")
    return {entry["sample"]: entry for entry in json.loads(completed.stdout)}


# -- mutation strategies: each mutates one copy in place ---------------------
# Every strategy guards its path and raises _NoTarget when the seed lacks it.
# A mutation Python still accepts is discarded as non-discriminating.

def _s_drop_required_top(manifest: dict) -> None:
    if "programs" not in manifest:
        raise _NoTarget("no programs key")
    del manifest["programs"]


def _s_unknown_top(manifest: dict) -> None:
    manifest["__prototype_probe__"] = 1


def _s_mistype_version(manifest: dict) -> None:
    generated = manifest.get("_generated")
    if not isinstance(generated, dict) or not isinstance(generated.get("contract_version"), int):
        raise _NoTarget("no integer contract_version")
    generated["contract_version"] = "11"


def _s_unknown_generated_key(manifest: dict) -> None:
    generated = manifest.get("_generated")
    if not isinstance(generated, dict):
        raise _NoTarget("no _generated")
    generated["__probe__"] = 1


def _s_wrong_nested_type(manifest: dict) -> None:
    for key in ("programs", "units"):
        items = manifest.get(key)
        if isinstance(items, list) and items and isinstance(items[0].get("id"), str):
            items[0]["id"] = 123
            return
    raise _NoTarget("no string id under programs/units")


def _s_enum(manifest: dict) -> None:
    programs = manifest.get("programs")
    if isinstance(programs, list) and programs and "status" in programs[0]:
        programs[0]["status"] = "__invalid__"
        return
    modules = manifest.get("modules")
    if isinstance(modules, list) and modules and "kind" in modules[0]:
        modules[0]["kind"] = "__invalid__"
        return
    raise _NoTarget("no program status or module kind")


def _s_unique_items(manifest: dict) -> None:
    for key, field in (("modules", "thematic_group_ids"),
                       ("projects", "relationship_ids")):
        items = manifest.get(key)
        if (isinstance(items, list) and items
                and isinstance(items[0].get(field), list) and items[0][field]):
            items[0][field] = [*items[0][field], items[0][field][0]]
            return
    raise _NoTarget("no non-empty unique-items array")


def _s_allof_break(manifest: dict) -> None:
    """Break a nested requirement inside an allOf-governed record."""

    syntheses = manifest.get("unit_material_syntheses")
    if not (isinstance(syntheses, list) and syntheses):
        raise _NoTarget("no unit material synthesis")
    for field in ("freshness", "completeness"):
        if field in syntheses[0]:
            del syntheses[0][field]
            return
    raise _NoTarget("no freshness/completeness branch")


def _s_unevaluated_props(manifest: dict) -> None:
    syntheses = manifest.get("unit_material_syntheses")
    if not (isinstance(syntheses, list) and syntheses):
        raise _NoTarget("no unit material synthesis")
    syntheses[0]["__unevaluated_probe__"] = 1


def _s_ref_target(manifest: dict) -> None:
    """Corrupt a record validated through a cross-document $ref."""

    projects = manifest.get("projects")
    if isinstance(projects, list) and projects and "status" in projects[0]:
        projects[0]["status"] = 123
        return
    modules = manifest.get("modules")
    if isinstance(modules, list) and modules and isinstance(modules[0].get("id"), str):
        modules[0]["id"] = 123
        return
    raise _NoTarget("no project status or module id")


def _s_bad_format(manifest: dict) -> None:
    # Deliberately `date` only: it is the one format vocabulary both sides
    # enforce. date-time/uri divergence is pinned (not hidden) in
    # test_format_vocabulary_agreement.
    deadlines = manifest.get("academic_deadlines")
    if isinstance(deadlines, list) and deadlines and "start_date" in deadlines[0]:
        deadlines[0]["start_date"] = "not-a-date"
        return
    raise _NoTarget("no deadline start_date")

MUTATIONS = [
    ("drop-required-top", [_s_drop_required_top]),
    ("unknown-top", [_s_unknown_top]),
    ("mistype-version", [_s_mistype_version]),
    ("unknown-generated-key", [_s_unknown_generated_key]),
    ("wrong-nested-type", [_s_wrong_nested_type]),
    ("enum", [_s_enum]),
    ("unique-items", [_s_unique_items]),
    ("allof-break", [_s_allof_break]),
    ("unevaluated-props", [_s_unevaluated_props]),
    ("ref-target", [_s_ref_target]),
    ("bad-format", [_s_bad_format]),
]


def _seeds(ui: Path, repo_root: Path) -> dict[str, dict]:
    seeds: dict[str, dict] = {}
    fixture = ui / FIXTURE_REL
    if not fixture.is_file():
        pytest.fail(f"UI fixture manifest is missing: {fixture}")
    seeds["fixture"] = json.loads(fixture.read_text(encoding="utf-8"))
    core_manifest = repo_root / "generated" / "manifest.json"
    if core_manifest.is_file():
        seeds["core"] = json.loads(core_manifest.read_text(encoding="utf-8"))
    return seeds


def test_seeds_are_valid_under_python(repo_root: Path) -> None:
    ui = _paired_ui(repo_root)
    validator = _python_validator(repo_root)
    for name, seed in _seeds(ui, repo_root).items():
        errors = list(validator.iter_errors(seed))
        assert not errors, f"seed {name} is not Python-valid: {errors[0].message}"


def test_differential_agreement(repo_root: Path, tmp_path: Path) -> None:
    ui = _paired_ui(repo_root)
    validator = _python_validator(repo_root)
    seeds = _seeds(ui, repo_root)

    samples: dict[str, Any] = {}
    expected: dict[str, bool] = {}
    for seed_name, seed in seeds.items():
        samples[f"seed-{seed_name}"] = seed
        expected[f"seed-{seed_name}.json"] = True
    for class_id, strategies in MUTATIONS:
        survivors = 0
        notes = []
        for index, strategy in enumerate(strategies):
            mutant = copy.deepcopy(seeds["fixture"])
            try:
                strategy(mutant)
            except _NoTarget as exc:
                notes.append(f"{strategy.__name__}: no target ({exc})")
                continue
            python_errors = list(validator.iter_errors(mutant))
            if not python_errors:
                notes.append(f"{strategy.__name__}: non-discriminating")
                continue
            survivors += 1
            name = f"mutant-{class_id}-{index}"
            samples[name] = mutant
            expected[f"{name}.json"] = False
        assert survivors >= 1, f"mutation class {class_id} has no survivor: {notes}"

    verdicts = _ajv_verdicts(ui, tmp_path, samples)
    mismatches = []
    for name, want in sorted(expected.items()):
        got = verdicts[name]["valid"]
        if got != want:
            python_errors = [e.message for e in validator.iter_errors(samples[name.removesuffix(".json")])]
            mismatches.append(
                f"{name}: want valid={want}, Ajv says {got}; "
                f"python: {python_errors[:2]}; ajv: {verdicts[name]['errors'][:2]}")
    assert not mismatches, "Python/Ajv disagreement:\n" + "\n".join(mismatches)


def _format_subschemas(repo_root: Path, tmp_path: Path) -> dict[str, dict]:
    del tmp_path
    bundle = json.loads(build_bundle(repo_root / V15_REL, repo_root / "system" / "schema"))
    found: dict[str, dict] = {}

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            if (isinstance(node.get("format"), str) and node["format"] not in found
                    and node.get("type") == "string"):
                found[node["format"]] = node
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(bundle["root"])
    for resource in bundle["resources"]:
        visit(resource["schema"])
    return found


def test_format_vocabulary_agreement(repo_root: Path, tmp_path: Path) -> None:
    ui = _paired_ui(repo_root)
    subs = _format_subschemas(repo_root, tmp_path)
    cases = {
        "date": ("2026-01-01", "not-a-date"),
        "date-time": ("2026-01-01T00:00:00Z", "not-a-datetime"),
        "uri": ("https://example.com/x", "::::"),
    }
    assert set(cases) <= set(subs), f"missing format subschemas: {set(cases) - set(subs)}"
    registry = schema_registry(repo_root / "system" / "schema")
    for name, (good, bad) in cases.items():
        subschema = subs[name]
        python = Draft202012Validator(
            subschema, registry=registry, format_checker=FormatChecker())
        verdicts = _ajv_verdicts(ui, tmp_path, {f"{name}-good": good, f"{name}-bad": bad},
                                 subschema=subschema)
        assert not list(python.iter_errors(good)), f"{name}: Python rejects the valid value"
        assert verdicts[f"{name}-good.json"]["valid"] is True, f"{name}: Ajv rejects valid"
        if name == "date":
            assert list(python.iter_errors(bad)), "date: Python accepts the invalid value"
            assert verdicts["date-bad.json"]["valid"] is False, "date: Ajv accepts invalid"
            continue
        # PINNED DIVERGENCE (prototype finding, 2026-09-20): Core's
        # FormatChecker() ships without date-time/uri checkers, so the
        # producer silently ignores those formats today, while Ajv with
        # ajv-formats enforces them. A production cutover must extend Core's
        # checker set (a production strictness change, out of scope here) —
        # aligning Ajv down to the gap would hide it.
        assert not list(python.iter_errors(bad)), (
            f"{name}: Python now rejects invalid — the pinned divergence changed; "
            "revisit the cutover decision, do not just update this line")
        assert verdicts[f"{name}-bad.json"]["valid"] is False, (
            f"{name}: Ajv accepts invalid — ajv-formats behavior changed")


def test_prototype_lock_matches_production_lock(repo_root: Path) -> None:
    """Every scalar the generator emits must equal the hand-mirrored lock."""

    ui = _paired_ui(repo_root)
    production_file = ui / "contracts" / "manifest-v15.lock.json"
    if not production_file.is_file():
        pytest.skip("differential contract test needs the manifest-v15.lock.json in obsidian-ui")
    production = json.loads(production_file.read_text(encoding="utf-8"))
    prototype = json.loads((ui / "contract-prototype" / "generated"
                            / "manifest.prototype.lock.json").read_text(encoding="utf-8"))
    for key in ("contract_version", "mirrors", "schema_path", "schema_sha256",
                "top_level_keys", "generated_keys", "index_keys",
                "forbidden_top_level_keys"):
        assert prototype[key] == production[key], f"prototype lock drifts on {key}"
    assert prototype["closure_sha256"].startswith("sha256:")


def test_full_scale_core_manifest(repo_root: Path, tmp_path: Path) -> None:
    import time

    ui = _paired_ui(repo_root)
    core_manifest = repo_root / "generated" / "manifest.json"
    if not core_manifest.is_file():
        pytest.skip("full-scale check needs repository/generated/manifest.json")
    manifest = json.loads(core_manifest.read_text(encoding="utf-8"))
    started = time.perf_counter()
    python_errors = list(_python_validator(repo_root).iter_errors(manifest))
    python_seconds = time.perf_counter() - started
    assert not python_errors, f"core manifest is not Python-valid: {python_errors[0].message}"
    started = time.perf_counter()
    verdicts = _ajv_verdicts(ui, tmp_path, {"core-manifest": manifest})
    ajv_seconds = time.perf_counter() - started
    assert verdicts["core-manifest.json"]["valid"] is True
    print(f"\nfull-scale 16MB manifest: python {python_seconds:.1f}s, "
          f"ajv subprocess {ajv_seconds:.1f}s (informational only)")

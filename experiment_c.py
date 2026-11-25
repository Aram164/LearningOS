"""Collect focused baseline observations in a disposable Actions workspace."""

import contextlib
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

import yaml


WORKSPACE = Path.cwd()
CORE = WORKSPACE / "repository"
UI = WORKSPACE / "obsidian-ui"
EVIDENCE = WORKSPACE / "evidence"
PY = sys.executable
LIVE = "tests/test_ui_phase3_live_writes.py"
RECOVERY = "tests/test_ui_gateway_recovery.py"
OPERATIONS = "tests/test_operations_gate.py"
LIVE_MODULE = "tests.test_ui_phase3_live_writes"
REQUIRED_NAME = "test_source_selection_seven_scenarios_on_disk"
CHECK = [PY, "tools/check_shard_completeness.py"]


def save(name, value):
    (EVIDENCE / f"{name}.json").write_text(json.dumps(value, indent=2) + "\n")


def run(label, argv, cwd=CORE, env=None, timeout=150):
    result = subprocess.run(
        argv, cwd=cwd, env=env, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, timeout=timeout,
    )
    output = result.stdout.replace(str(WORKSPACE), "<workspace>").replace(
        os.environ["RUNNER_TEMP"], "<runner-temp>"
    )
    (EVIDENCE / f"{label}.log").write_text(
        f"exit: {result.returncode}\ncommand: {argv!r}\n{output}"
        .replace(str(WORKSPACE), "<workspace>").replace(os.environ["RUNNER_TEMP"], "<runner-temp>")
    )
    print(f"{label}: exit {result.returncode}", flush=True)
    return result


def pytest(label, temp, *files):
    return run(label, [
        PY, "-m", "pytest", "-q", "-ra", f"--basetemp={temp / label}",
        f"--junitxml={EVIDENCE / (label + '.xml')}", *files,
    ], timeout=1000)


@contextlib.contextmanager
def withhold(path, scratch):
    held = scratch / f"held-{path.name}"
    path.rename(held)
    try:
        yield
    finally:
        held.rename(path)


def receipt_rows(root):
    rows = []
    for file in sorted(root.glob("operations/transactions/transaction-*.yaml")):
        receipt = yaml.safe_load(file.read_text())
        rows.append({
            "id": receipt["id"],
            "capability": receipt["capability"],
            "channel": (receipt.get("request") or {}).get("channel"),
            "writes": [{"path": row["path"], "exists": (root / row["path"]).is_file()}
                       for row in receipt["writes"]],
        })
    return rows


def capture_effects(temp):
    out = {}
    worlds = sorted((temp / "c0-healthy").glob("ui-phase3-live-writes*/scenarios"))
    for world in worlds:
        for name in ("src-valid", "map-valid", "deliv-valid"):
            root = world / name / "repository"
            out[name] = {"receipts": receipt_rows(root)}
        unit = world / "src-valid/repository/curriculum/modules/module-demo/units/unit-demo-l02/unit.yaml"
        study_map = world / "map-valid/repository/curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml"
        delivery = world / "deliv-valid/repository"
        request = delivery / "operations/ai-actions/requests/ai-request-scenario-shelve/request.yaml"
        out["src-valid"]["selection_purposes"] = [
            row.get("purpose") for row in yaml.safe_load(unit.read_text())["source_selections"]
        ]
        out["map-valid"]["stages"] = [
            row["id"] for row in yaml.safe_load(study_map.read_text())["stages"]
        ]
        out["deliv-valid"]["transcription_exists"] = (
            delivery / "knowledge/garden/transcriptions/garden-note-seed.md"
        ).is_file()
        out["deliv-valid"]["request_status"] = yaml.safe_load(request.read_text())["status"]
    for ledger in sorted((temp / "c0-healthy").glob(
            "ui-recovery*/**/operations/transactions/idempotency.yaml")):
        root = ledger.parents[2]
        out["gateway-recovery"] = {
            "receipts": receipt_rows(root),
            "ledger_entries": len(yaml.safe_load(ledger.read_text())["entries"]),
        }
    save("c0-effects", out)


def make_guards(temp):
    source = (CORE / "Makefile").read_text().splitlines()
    start = next(i for i, line in enumerate(source) if line.startswith(
        '\t@test -f ../obsidian-ui/package.json ||'))
    end = source.index('\t$(PY) -m pytest -q', start)
    guard = temp / "guard.Makefile"
    guard.write_text("system-check-guards:\n" + "\n".join(source[start:end]) + "\n")
    shutil.copyfile(guard, EVIDENCE / "c1-extracted-guards.Makefile")
    return ["make", "-f", str(guard), "system-check-guards"]


def case_matches(node):
    return node.get("classname") == LIVE_MODULE and node.get("name") == REQUIRED_NAME


def capture_population(temp):
    historical = WORKSPACE / "historical-junit"
    frozen = run("c2-inventory", [PY, "-m", "pytest", "--collect-only", "-q"])
    assert frozen.returncode == 0
    ids = [line.strip() for line in frozen.stdout.splitlines() if "::" in line and not line.startswith(" ")]
    assert ids.count(f"{LIVE}::{REQUIRED_NAME}") == 1
    (EVIDENCE / "c2-frozen-node-ids.txt").write_text("\n".join(ids) + "\n")

    files = sorted(historical.glob("junit-*.xml"))
    assert len(files) == 9
    save("c2-input-digests", {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    matches = [(path, node) for path in files for node in ET.parse(path).iter("testcase")
               if case_matches(node)]
    assert len(matches) == 1 and len(matches[0][1]) == 0
    chosen = matches[0][0].name
    marked = [node for node in ET.parse(EVIDENCE / "c2-withheld-live.xml").iter("testcase")
              if case_matches(node)]
    assert len(marked) == 1 and marked[0].find("skipped") is not None

    run("c2-population-control", [*CHECK, "--junit-dir", str(historical)])
    for variant in ("absent", "skipped"):
        copy = temp / variant
        shutil.copytree(historical, copy)
        xml = copy / chosen
        tree = ET.parse(xml)
        parent = next(parent for parent in tree.iter() if any(map(case_matches, parent)))
        index = next(i for i, node in enumerate(parent) if case_matches(node))
        parent.remove(parent[index])
        if variant == "skipped":
            parent.insert(index, marked[0])
        tree.write(xml, encoding="utf-8", xml_declaration=True)
        run(f"c2-population-{variant}", [*CHECK, "--junit-dir", str(copy)])
    for variant, filename in (("healthy", "c0-healthy"), ("skipped", "c2-withheld-live")):
        run(f"c2-zero-skip-{variant}", [
            *CHECK, "--zero-skip-junit", str(EVIDENCE / f"{filename}.xml"),
        ])


def git_identity(temp):
    code = (
        "import sys; from pathlib import Path; sys.path.insert(0, 'tests'); "
        "from scenario_harness import _commit_fixture; "
        "_commit_fixture(Path(sys.argv[1]), '2026-01-15T12:00:00+00:00', None)"
    )
    identities = {
        "GIT_AUTHOR_NAME": "Experiment C Author",
        "GIT_AUTHOR_EMAIL": "experiment-c-author@example.invalid",
        "GIT_COMMITTER_NAME": "Experiment C Committer",
        "GIT_COMMITTER_EMAIL": "experiment-c-committer@example.invalid",
    }
    env = {key: val for key, val in os.environ.items() if not key.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null")
    fields = ["sha", "tree", "parent", "subject", "author", "author_email",
              "author_date", "committer", "committer_email", "committer_date"]
    result = {}
    for variant, overrides in (("normal", {}), ("ambient", identities)):
        root = temp / f"git-{variant}"
        root.mkdir()
        (root / "sample.txt").write_text("Identical Experiment C fixture\n")
        commit = run(f"c4-commit-{variant}", [PY, "-c", code, str(root)],
                     env={**env, **overrides})
        if commit.returncode == 0:
            shown = run(f"c4-identity-{variant}", [
                "git", "-C", str(root), "show", "-s", "--format=%H%n%T%n%P%n%s%n%an%n%ae%n%aI%n%cn%n%ce%n%cI",
            ], env=env)
            assert shown.returncode == 0
            result[variant] = dict(zip(fields, shown.stdout.splitlines(), strict=True))
    save("c4-identities", result)


def main():
    for key in ("LEARNINGOS_ALLOW_MISSING_CORE", "LEARNINGOS_ALLOW_FALLBACK",
                "LEARNINGOS_REQUIRE_CORE_MIRROR"):
        os.environ.pop(key, None)
    with tempfile.TemporaryDirectory(prefix="los-c-", dir=os.environ["RUNNER_TEMP"]) as scratch:
        temp = Path(scratch)
        git_identity(temp)
        guards = make_guards(temp)
        run("c1-healthy-guards", guards)
        with withhold(UI, temp):
            run("c1-no-ui-guards", guards)
            pytest("c1-no-ui", temp, LIVE, RECOVERY, OPERATIONS)
        with withhold(UI / "tests/gateway-recovery-harness.js", temp):
            run("c1-no-recovery-guards", guards)
            pytest("c1-no-recovery", temp, RECOVERY)

        parity = ["node", "scripts/check-gateway-parity.mjs", "--strict"]
        run("c3-paired-parity", parity, cwd=UI)
        healthy = pytest("c0-healthy", temp, LIVE, RECOVERY, OPERATIONS)
        if healthy.returncode == 0:
            capture_effects(temp)

        with withhold(UI / "tests/live-writes-harness.js", temp):
            run("c2-withheld-live-guards", guards)
            pytest("c2-withheld-live", temp, LIVE)

        atlas = ["sh", "-c", (
            'if [ -f "$LOS_REPO/../obsidian-ui/tests/test-atlas-boards.js" ]; then '
            'node "$LOS_REPO/../obsidian-ui/tests/test-atlas-boards.js"; else '
            "printf '%s\\n' 'Atlas board controller proof requires the sibling UI checkout.'; fi"
        )]
        atlas_env = {**os.environ, "LOS_REPO": str(CORE)}
        run("c3-atlas-paired", atlas, env=atlas_env)
        with withhold(UI, temp):
            run("c3-atlas-core-only", atlas, env=atlas_env)
        # Hide only the producer schema directory to take the same absent-Core
        # parity branch while leaving the installed Python environment untouched.
        with withhold(CORE / "system/schema/capabilities", temp):
            run("c3-parity-schema-absent-ci", parity, cwd=UI)
            local = {key: val for key, val in os.environ.items() if key != "CI"}
            run("c3-parity-schema-absent-local", parity, cwd=UI, env=local)
        schema = CORE / "system/schema/capabilities/capture.create.schema.json"
        original = schema.read_bytes()
        try:
            doc = json.loads(original)
            doc["description"] = "Experiment C annotation. Validation semantics are unchanged."
            schema.write_text(json.dumps(doc, indent=2) + "\n")
            run("c3-capability-mirror-mismatch", parity, cwd=UI)
        finally:
            schema.write_bytes(original)

        capture_population(temp)
        for repo in (CORE, UI):
            assert not subprocess.check_output(["git", "status", "--porcelain"], cwd=repo)


if __name__ == "__main__":
    main()

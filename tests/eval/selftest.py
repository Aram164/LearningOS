#!/usr/bin/env python3
"""Check the public campaign contract and disposable world builder."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

EVAL = Path(__file__).resolve().parent
REPO = EVAL.parents[1]
sys.path.insert(0, str(EVAL / "tools"))
from build_world import BuildError, build  # noqa: E402
from check_run import check_run  # noqa: E402
from oracle_vault import MANIFEST, SEALED, decrypt  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def check_public() -> list[str]:
    scenarios = yaml.safe_load((EVAL / "public/scenarios.yaml").read_text(encoding="utf-8"))
    rows = scenarios["scenarios"]
    ids = [row["id"] for row in rows]
    require(ids == [f"S{n:02d}" for n in range(28)], "expected S00-S27 in order")
    require(len(ids) == len(set(ids)), "duplicate scenario id")
    plans = {letter for row in rows for letter in row["plans"]}
    require(plans == {"B", "A", "E", "X", "U", "P", "R"}, f"plans {plans}")
    require(all(row.get("learner_says") or row.get("procedure") for row in rows),
            "scenario missing learner request or investigator procedure")
    for row in rows:
        require(row.get("world") in {"fresh", "continue"}, f"{row['id']}: world")
        require(bool(row.get("record")), f"{row['id']}: record list")
        for rel in row.get("inputs", []):
            require((EVAL / rel).is_file(), f"{row['id']}: missing input {rel}")
    for path in (EVAL / "public/schemas").glob("*.json"):
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))
    for path in (EVAL / "public/templates").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        schema = json.loads((EVAL / "public/schemas/scenario-result.schema.json").read_text())
        require(not list(Draft202012Validator(schema).iter_errors(data)), f"bad template {path}")
    curriculum = yaml.safe_load((EVAL / "corpus/curriculum.yaml").read_text(encoding="utf-8"))
    lab = next(m for m in curriculum["modules"] if m["id"] == "module-skill-query-lab")
    require([u["id"] for u in lab["units"]] ==
            ["unit-query-lab-plans", "unit-query-lab-lineage"], "query lab unit fixture")
    require(lab["units"][0]["study_map"]["stages"][0]["status"] == "complete",
            "completed stage fixture")
    require(lab["units"][1]["record"]["status"] == "needs-map", "needs-map fixture")
    require((EVAL / "corpus/materials/source-noor-lazy-lab/lab-notes.md").is_file(),
            "owned material missing")
    return ids


def check_oracle(ids: list[str]) -> None:
    require(SEALED.is_file() and MANIFEST.is_file(), "sealed oracle missing")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    require("expectations.yaml" in manifest["files"], "oracle expectations missing")
    require("JUDGE.md" in manifest["files"], "judge procedure missing")
    if os.getenv("LOS_EVAL_ORACLE_KEY"):
        import io
        import tarfile
        with tarfile.open(fileobj=io.BytesIO(decrypt()), mode="r:gz") as archive:
            data = yaml.safe_load(archive.extractfile("oracle/expectations.yaml").read())
        require(set(data["expectations"]) == set(ids), "oracle ID mismatch")
    public_bytes = b"".join(p.read_bytes() for p in (EVAL / "public").rglob("*") if p.is_file())
    require(b"global_hard_invariants:" not in public_bytes, "oracle plaintext leaked")


def check_builder() -> None:
    with tempfile.TemporaryDirectory(prefix="los-eval-selftest-") as temp:
        root = Path(temp)
        for name in ("a", "b"):
            world = build(root / name, "WORKTREE", 0, 20260924, False)
            require(world["notes"] >= 100, "world unexpectedly small")
            require((root / name / "LearningOS/repository/tools/los.py").is_file(),
                    "world lacks CLI")
        a = json.loads((root / "a/EVAL-WORLD.json").read_text(encoding="utf-8"))
        b = json.loads((root / "b/EVAL-WORLD.json").read_text(encoding="utf-8"))
        require(a["world_head"] == b["world_head"], "world HEAD is nondeterministic")
        require(a["corpus_sha256"] == b["corpus_sha256"], "corpus hashes differ")
        try:
            build(root / "a", "WORKTREE", 0, 20260924, False)
        except BuildError:
            pass
        else:
            raise AssertionError("builder accepted nonempty output")
        try:
            build(REPO / "tests/eval-forbidden-world", "WORKTREE", 0, 20260924, False)
        except BuildError:
            pass
        else:
            raise AssertionError("builder accepted output inside real repository")
        world_repo = root / "a/LearningOS/repository"
        before = subprocess.run(["git", "status", "--porcelain"], cwd=world_repo,
                                capture_output=True, text=True, check=True).stdout
        observer = subprocess.run([sys.executable, str(EVAL / "tools/observe.py"),
                                   "snapshot", str(world_repo), "--label", "selftest"],
                                  capture_output=True, text=True)
        require(observer.returncode == 0, f"observer failed: {observer.stderr}")
        after = subprocess.run(["git", "status", "--porcelain"], cwd=world_repo,
                               capture_output=True, text=True, check=True).stdout
        require(before == after, "observer changed the world")


def check_records() -> None:
    with tempfile.TemporaryDirectory(prefix="los-eval-records-") as temp:
        run = Path(temp) / "sample-run"
        (run / "results").mkdir(parents=True)
        (run / "observations").mkdir()
        (run / "SESSION_REPORT.md").write_text("# Selftest\n", encoding="utf-8")
        (run / "run.json").write_text(json.dumps({
            "run_id": run.name, "plan": "B", "session_role": "selftest",
            "started": "2026-09-27T00:00:00Z", "product_revision": "WORKTREE",
            "world_head": "abc", "blind": True, "scenarios": ["S00", "S01"],
        }), encoding="utf-8")
        for sid in ("S00", "S01"):
            before = f"observations/{sid}-before.json"
            after = f"observations/{sid}-after.json"
            diff = f"observations/{sid}-diff.json"
            for rel in (before, after, diff):
                (run / rel).write_text("{}\n", encoding="utf-8")
            (run / "results" / f"{sid}.json").write_text(json.dumps({
                "scenario": sid, "run_id": run.name, "classification": "NOT_RUN",
                "before": {"snapshot_file": before}, "after": {"snapshot_file": after},
                "consumer": {"goal": "selftest", "first_action": "none",
                             "commands": [], "outcome": "not run"},
                "internal": {"observe_diff_file": diff},
            }), encoding="utf-8")
        require(not check_run(run), "valid minimal run rejected")
        if os.getenv("LOS_EVAL_ORACLE_KEY"):
            sys.path.insert(0, str(EVAL / "metrics"))
            from score_workflows import score
            require(len(score(run)["worksheets"]) == 2, "judge scorer rejected valid run")
        (run / "results/S01.json").unlink()
        require(check_run(run), "missing scenario result accepted")


def main() -> int:
    ids = check_public()
    check_oracle(ids)
    check_builder()
    check_records()
    print(f"eval selftest: {len(ids)} scenarios, sealed oracle, deterministic world, safe observer OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

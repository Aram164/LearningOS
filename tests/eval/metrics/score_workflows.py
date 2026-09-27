#!/usr/bin/env python3
"""Judge worksheet for workflow runs; observer checks are evidence, not verdicts.

Requires LOS_EVAL_ORACLE_KEY. The decrypted oracle stays in memory. Blind
operators must never run this tool or receive its output.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import tarfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "tools"))
from check_run import check_run  # noqa: E402
from oracle_vault import decrypt  # noqa: E402


def oracle_expectations() -> dict:
    with tarfile.open(fileobj=io.BytesIO(decrypt()), mode="r:gz") as archive:
        member = archive.extractfile("oracle/expectations.yaml")
        if member is None:
            raise ValueError("sealed oracle lacks expectations.yaml")
        data = yaml.safe_load(member.read())
    if not isinstance(data, dict) or not isinstance(data.get("expectations"), dict):
        raise ValueError("invalid oracle expectations")
    return data


def score(run: Path) -> dict:
    problems = check_run(run)
    oracle = oracle_expectations()
    scenarios = yaml.safe_load((HERE / "public/scenarios.yaml").read_text(encoding="utf-8"))
    public_ids = {row["id"] for row in scenarios["scenarios"]}
    expected = oracle["expectations"]
    if set(expected) != public_ids:
        problems.append(f"oracle/public ID mismatch: {sorted(set(expected) ^ public_ids)}")
    if problems:
        return {"run_id": run.name, "record_problems": problems,
                "worksheets": [], "warning": "Fix run records before judging."}
    run_data = json.loads((run / "run.json").read_text(encoding="utf-8"))
    worksheets = []
    for sid in run_data.get("scenarios", []):
        path = run / "results" / f"{sid}.json"
        if not path.is_file():
            continue
        result = json.loads(path.read_text(encoding="utf-8"))
        internal = result.get("internal") or {}
        flags = []

        def load_diff(rel):
            path = (run / rel).resolve() if rel else None
            if path and path.is_relative_to(run.resolve()) and path.is_file():
                return json.loads(path.read_text(encoding="utf-8"))
            return None

        diff = load_diff(internal.get("observe_diff_file"))
        case_diffs = [(c.get("label", "?"), load_diff(c.get("observe_diff_file")))
                      for c in result.get("cases") or []]
        if diff is not None:
            flags.extend(diff.get("flags") or [])
            observed = set(diff.get("receipts_added") or [])
            for _, extra in case_diffs:
                observed |= set((extra or {}).get("receipts_added") or [])
            marker = "operations/transactions/transaction-"
            reported = {r[r.index(marker):] for r in internal.get("receipts") or []
                        if marker in r}
            if reported != observed:
                flags.append("reported-receipts-differ-from-observer")
            if internal.get("unexpected_writes"):
                flags.append("consumer-reported-unexpected-writes")
            authored = diff.get("authored") or diff.get("canonical") or {}
            if result.get("classification") == "PASS" and not any(authored.values()) \
                    and diff.get("receipts_added"):
                flags.append("pass-with-receipt-but-no-authored-diff")
        else:
            flags.append("missing-observer-diff")
        for label, extra in case_diffs:
            if extra is None:
                flags.append(f"case-{label}:missing-observer-diff")
            else:
                flags.extend(f"case-{label}:{flag}" for flag in extra.get("flags") or [])
        if result.get("classification") in {"PASS", "PASS_WITH_FRICTION"} \
                and result.get("failures"):
            flags.append("pass-with-recorded-failure")
        if run_data.get("blind") is False:
            flags.append("nonblind-run")
        worksheets.append({
            "scenario": sid,
            "consumer_classification": result.get("classification"),
            "consumer_reason": result.get("classification_reason", ""),
            "observer_flags": sorted(set(flags)),
            "must_check": expected.get(sid, {}).get("must", []),
            "reject_if": expected.get(sid, {}).get("reject", []),
            "judge_task_correctness_0_1_2": None,
            "judge_classification": None,
            "judge_evidence_paths": [],
            "judge_reason": "",
        })
    return {
        "run_id": run.name,
        "record_problems": problems,
        "global_hard_invariants": oracle.get("global_hard_invariants", []),
        "worksheets": worksheets,
        "warning": "Heuristics and consumer claims are not acceptance evidence; inspect primary artifacts.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--out", required=True, type=Path,
                        help="worksheet path outside the product repository")
    args = parser.parse_args(argv)
    if args.out.resolve().is_relative_to(HERE.parents[3]):
        parser.error("--out must be outside the real semestercontext tree")
    report = score(args.run)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"score_workflows: {len(report['worksheets'])} worksheets, "
          f"{len(report['record_problems'])} record problems → {args.out}")
    return int(bool(report["record_problems"]))


if __name__ == "__main__":
    sys.exit(main())

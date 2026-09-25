#!/usr/bin/env python3
"""Self-tests for the evaluation package (not part of the product test suite).

    .venv/bin/python tests/eval/selftest.py            # everything that needs no key
    LOS_EVAL_ORACLE_KEY=… .venv/bin/python tests/eval/selftest.py   # + oracle and leak checks
    .venv/bin/python tests/eval/selftest.py --quick    # skip the two world builds

Checks:
  public    corpus bundles parse; public YAML files are consistent (unique ids,
            probe queries exist, arrivals exist); every JSON schema is valid
  scorers   score_connections / score_retrieval arithmetic on toy data
  world     two builds from the same inputs have the same HEAD, validate with
            0 errors and publish views; observe/diff and determinism run
  blind     tests/eval/private holds only sealed files; plaintext oracle never
            tracked; with the key: the oracle decrypts, every oracle id exists
            in the world, and no distinctive oracle sentence appears in any
            public file, in any commit touching tests/eval, or in a built world
            (runs/ is consumer output: checked for the oracle's own sentences,
            not for the expected mentions a correct answer should contain)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

EVAL = Path(__file__).resolve().parent
REPO = EVAL.parents[1]
sys.path.insert(0, str(EVAL / "tools"))
sys.path.insert(0, str(EVAL / "metrics"))

import yaml  # noqa: E402
from bundle import read_bundle, read_bundles  # noqa: E402

RESULTS: list[tuple[str, str, str]] = []


def check(name):
    def wrap(fn):
        def run(*a, **k):
            try:
                note = fn(*a, **k) or ""
                RESULTS.append(("PASS", name, note))
            except SkipTest as exc:
                RESULTS.append(("SKIP", name, str(exc)))
            except Exception as exc:  # noqa: BLE001 — report every failure, keep going
                RESULTS.append(("FAIL", name, f"{exc}\n{traceback.format_exc(limit=3)}"))
        return run
    return wrap


class SkipTest(Exception):
    pass


def load(rel: str):
    return yaml.safe_load((EVAL / rel).read_text(encoding="utf-8"))


# ------------------------------------------------------------------ public
@check("public: corpus bundles parse")
def t_bundles():
    notes = read_bundles(EVAL / "corpus" / "notes")
    for name in ("stage-notes", "inbox", "garden", "arrivals", "workspaces", "coordination"):
        read_bundle(EVAL / "corpus" / f"{name}.md")
    for name in ("world", "registries", "curriculum", "projects"):
        load(f"corpus/{name}.yaml")
    return f"{len(notes)} notes"


@check("public: ids and cross-references")
def t_public_ids():
    notes = {i.key for i in read_bundles(EVAL / "corpus" / "notes")}
    arrivals = {i.key for i in read_bundle(EVAL / "corpus" / "arrivals.md")}
    probes = load("public/connection-probes.yaml")
    canon_ids = [p["id"] for p in probes["canon"]]
    assert len(canon_ids) == len(set(canon_ids)), "duplicate canon probe id"
    missing = [p["query"] for p in probes["canon"] if p["query"] not in notes]
    assert not missing, f"canon probe queries not in corpus: {missing}"
    assert set(probes["arrivals"]) == arrivals, "arrival probes differ from corpus arrivals"
    qs = [q["id"] for q in load("public/questions.yaml")["questions"]]
    assert qs == [f"Q{n:02d}" for n in range(1, len(qs) + 1)], "question ids not Q01..Qnn"
    sc = [s["id"] for s in load("public/scenarios.yaml")["scenarios"]]
    assert len(sc) == len(set(sc)), "duplicate scenario id"
    for s in load("public/scenarios.yaml")["scenarios"]:
        for rel in s.get("inputs") or []:
            if rel.startswith("eval-drop/"):
                assert Path(rel).stem in arrivals, f"{s['id']}: unknown input {rel}"
            else:
                assert (EVAL / rel).exists(), f"{s['id']}: missing input {rel}"
        assert set(s["plans"]) <= {"B", "N", "L", "R", "C", "X", "P", "F"}, f"{s['id']}: bad plan"
    return f"{len(canon_ids)} canon probes, {len(arrivals)} arrivals, {len(qs)} questions, {len(sc)} scenarios"


@check("public: JSON schemas are valid")
def t_schemas():
    from jsonschema import Draft202012Validator
    count = 0
    for path in sorted((EVAL / "public" / "schemas").glob("*.json")):
        Draft202012Validator.check_schema(json.loads(path.read_text(encoding="utf-8")))
        count += 1
    template = EVAL / "public" / "templates" / "result.example.json"
    if template.exists():
        schema = json.loads((EVAL / "public/schemas/scenario-result.schema.json").read_text())
        Draft202012Validator(schema).validate(json.loads(template.read_text()))
    return f"{count} schemas"


# ----------------------------------------------------------------- scorers
TOY_REL = {"P1": {"query": "note-q", "judgments": [
    {"t": "note-a", "c": "MUST_CONNECT", "s": 3, "cat": ["semantic-paraphrase"], "lex": "none",
     "path": "direct", "chron": "none", "m": ["alpha beta gamma"], "why": "toy"},
    {"t": "note-b", "c": "USEFUL_CONNECT", "s": 2, "cat": ["cross-domain"], "lex": "partial",
     "path": "direct", "chron": "none", "m": [], "why": "toy"},
    {"t": "note-old", "c": "AMBIGUOUS", "s": 0, "cat": ["chronology"], "lex": "none",
     "path": "direct", "chron": "superseded", "m": [], "why": "toy"},
    {"t": "note-x", "c": "MUST_NOT_CONNECT", "s": 0, "cat": ["keyword-decoy"], "lex": "partial",
     "path": "direct", "chron": "none", "m": [], "why": "toy"}]}}


@check("scorers: connection metrics on toy data")
def t_score_connections():
    from score_connections import aggregate, breakdowns, score_probe
    perfect = {"probe": "P1", "results": [
        {"rank": 1, "target": "note-a", "reason": "alpha beta gamma link"},
        {"rank": 2, "target": "knowledge/notes/x/note-b.md", "reason": "r"}]}
    r = score_probe("P1", TOY_REL["P1"], perfect, None, None)
    assert r["recall@5"] == 1.0 and r["mrr"] == 1.0, r
    assert r["relevant_recall@10"] == 1.0 and r["precision@5"] == 0.4, r
    assert r["explanation_coverage_HEURISTIC"] == 1.0, r
    assert r["must_not_rate@10"] == 0.0 and not r["decoy_hit@5"], r
    decoy = {"probe": "P1", "results": [
        {"rank": 1, "target": "note-x", "reason": "same word"},
        {"rank": 2, "target": "concept-y", "reason": "concept"},
        {"rank": 3, "target": "note-old", "reason": "looks related"},
        {"rank": 4, "target": "note-a", "reason": "nothing"}]}
    d = score_probe("P1", TOY_REL["P1"], decoy, None, None)
    assert d["decoy_hit@5"] and d["must_not_rate@10"] == 1.0, d
    assert d["non_material_dropped"] == 1 and d["mrr"] == 1 / 3, d
    assert d["outdated_uncaveated"] == ["note-old"], d
    assert d["judged_precision@5"] == 0.5, d
    missing = score_probe("P1", TOY_REL["P1"], None, None, None)
    agg = aggregate([r, missing])
    assert agg["macro_answered"]["recall@5"] == 1.0, agg
    assert agg["macro_all_missing_as_zero"]["recall@5"] == 0.5, agg
    b = breakdowns([d], TOY_REL)
    assert b["by_category"]["keyword-decoy"]["must_not_rate@10"] == 1.0, b


@check("scorers: retrieval metrics on toy data")
def t_score_retrieval():
    from score_retrieval import score_question
    oracle = {"cat": ["exact"], "evidence": {"all": ["note-a"], "any": ["note-b", "note-c"]},
              "points": [{"fact": "f1", "kw": [["0.1", "diverg"]]},
                         {"fact": "f2", "kw": [["scal"], ["standardiz"]]}],
              "forbidden": [{"claim": "c", "kw": [["2.3"]]}]}
    good = {"question": "Q", "answer": "0.1 diverged; standardizing fixed it",
            "evidence": [{"ref": "knowledge/notes/m/note-a.md"}, {"ref": "note-c"}]}
    g = score_question("Q", oracle, good, None, None)
    assert g["evidence_all"] and g["evidence_any"] and g["points_HEURISTIC"] == 1.0, g
    bad = {"question": "Q", "answer": "it was 2.3", "evidence": [{"ref": "note-b"}]}
    b = score_question("Q", oracle, bad, None, None)
    assert not b["evidence_all"] and b["forbidden_HEURISTIC"] == ["c"], b


# ------------------------------------------------------------------- world
def build(out: Path) -> dict:
    proc = subprocess.run([sys.executable, str(EVAL / "tools" / "build_world.py"),
                           "--out", str(out)], capture_output=True, text=True, timeout=1800)
    if proc.returncode != 0:
        raise AssertionError("build failed:\n" + proc.stderr[-3000:] + proc.stdout[-2000:])
    return json.loads((out / "EVAL-WORLD.json").read_text())


@check("world: deterministic build, validates, views publish")
def t_world(ctx):
    if ctx["quick"]:
        raise SkipTest("--quick")
    a = build(ctx["tmp"] / "a")
    b = build(ctx["tmp"] / "b")
    assert a["world_head"] == b["world_head"], (a["world_head"], b["world_head"])
    assert a["validate_exit"] == 0 and a["generate_exit"] == 0, a
    ctx["world"] = Path(a["paths"]["repository"])
    ctx["world_b"] = Path(b["paths"]["repository"])
    return f"HEAD {a['world_head'][:12]}, {a['notes']} notes, {a['commits']} commits"


@check("world: final curriculum state equals the corpus")
def t_final_state(ctx):
    if "world" not in ctx:
        raise SkipTest("no world built")
    cur = load("corpus/curriculum.yaml")
    checked = 0
    for mod in cur["modules"]:
        for unit in mod["units"]:
            smap = unit.get("study_map")
            if not smap:
                continue
            path = (ctx["world"] / "curriculum/modules" / mod["id"] / "units" / unit["id"]
                    / "study-map.yaml")
            built = yaml.safe_load(path.read_text(encoding="utf-8"))
            assert built["current_stage"] == smap["current_stage"], (smap["id"], built)
            want = {s["id"]: s["status"] for s in smap["stages"]}
            got = {s["id"]: s["status"] for s in built["stages"]}
            assert want == got, (smap["id"], want, got)
            checked += 1
    resume = yaml.safe_load((ctx["world"] / "curriculum/resume.yaml").read_text())
    assert resume["stage_id"] == cur["resume"]["stage_id"], resume
    return f"{checked} study maps"


@check("world: observe snapshot/diff is side-effect free")
def t_observe(ctx):
    if "world" not in ctx:
        raise SkipTest("no world built")
    from observe import diff, snapshot
    repo = ctx["world"]
    status = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True,
                            text=True).stdout
    s1 = snapshot(repo, "one")
    s2 = snapshot(repo, "two")
    d = diff(s1, s2)
    assert not any(d["canonical"].values()) and not d["flags"], d
    after = subprocess.run(["git", "status", "--porcelain"], cwd=repo, capture_output=True,
                           text=True).stdout
    assert status == after, "observer changed git status"
    return f"{s1['canonical']['count']} canonical files"


@check("world: determinism report (rebuild and two builds)")
def t_determinism(ctx):
    if "world" not in ctx:
        raise SkipTest("no world built")
    from determinism import pair, single
    s = single(ctx["world"])
    p = pair(ctx["world"], ctx["world_b"])
    ctx["determinism"] = {"single": s["timestamp_normalized"], "pair": {
        k: p[k] for k in ("heads_equal", "timestamp_and_root_normalized")}}
    # Recorded, not asserted: the harness must run; whether the product is
    # deterministic is for the evaluation sessions to report.
    return ("rebuild identical after TS normalization: "
            f"{s['timestamp_normalized']['identical']}; two builds identical after TS+root: "
            f"{p['timestamp_and_root_normalized']['identical']}")


# ------------------------------------------------------------------- blind
ALLOWED_PRIVATE = {"tests/eval/private/README.md", "tests/eval/private/oracle.tar.gz.enc",
                   "tests/eval/private/oracle.manifest.json"}


@check("blind: private/ holds only sealed material")
def t_private_tracked():
    listed = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard",
                             "tests/eval/private"], cwd=REPO, capture_output=True,
                            text=True).stdout.split()
    extra = sorted(set(listed) - ALLOWED_PRIVATE)
    assert not extra, f"unexpected files in tests/eval/private: {extra}"
    assert (EVAL / "private" / "oracle.tar.gz.enc").exists(), "sealed oracle missing"
    head = (EVAL / "private" / "oracle.tar.gz.enc").read_bytes()[:8]
    assert head == b"Salted__", "sealed oracle is not an openssl salted ciphertext"


def oracle_patterns(oracle_dir: Path, mentions: bool = True) -> list[str]:
    pats = set()
    rel = yaml.safe_load((oracle_dir / "relations.yaml").read_text())["probes"]
    for p in rel.values():
        for j in p["judgments"]:
            for s in [j.get("why", ""), *(j.get("m", []) if mentions else [])]:
                if len(s) >= 28:
                    pats.add(s)
    # Answer facts are left out on purpose: many quote the learner's own notes,
    # which are public by design. Judge notes, judgment reasons, expected
    # mentions and scenario expectations are the oracle's own words. Expected
    # mentions are also what a correct explanation should say (score_connections
    # rewards a reason that covers them), so mentions=False gives the patterns
    # for consumer output (H3).
    ans = yaml.safe_load((oracle_dir / "answers.yaml").read_text())["questions"]
    for q in ans.values():
        if len(q.get("judge", "")) >= 28:
            pats.add(q["judge"])
    exp = yaml.safe_load((oracle_dir / "scenario-expectations.yaml").read_text())["scenarios"]
    for sc in exp.values():
        for e in sc.get("expect", []):
            if len(e["what"]) >= 28:
                pats.add(e["what"])
    return sorted(pats)


def leak_hits(eval_dir: Path, pat_file: Path, run_pat_file: Path) -> list[str]:
    """Files under eval_dir holding oracle text. runs/ is consumer output and is
    checked against run_pat_file (the oracle's own sentences) only."""
    hits = subprocess.run(["grep", "-rlF", "-f", str(pat_file), "--exclude-dir=private",
                           "--exclude-dir=runs", str(eval_dir)],
                          capture_output=True, text=True).stdout.split()
    if (eval_dir / "runs").is_dir():
        hits += subprocess.run(["grep", "-rlF", "-f", str(run_pat_file),
                                str(eval_dir / "runs")],
                               capture_output=True, text=True).stdout.split()
    return hits


@check("blind: leak scan lets runs/ contain expected mentions (toy data)")
def t_leak_scan_toy(ctx):
    root = ctx["tmp"] / "leak-toy"
    mention = "a phrase a correct explanation is expected to say"
    own = "the oracle's own reason for judging this pair relevant"
    pat_file, run_pat_file = root / "patterns.txt", root / "run-patterns.txt"
    run_file = root / "eval" / "runs" / "r1" / "connections.jsonl"
    public_file = root / "eval" / "public" / "brief.md"
    run_file.parent.mkdir(parents=True)
    public_file.parent.mkdir(parents=True)
    pat_file.write_text(f"{mention}\n{own}\n", encoding="utf-8")
    run_pat_file.write_text(f"{own}\n", encoding="utf-8")
    run_file.write_text(json.dumps({"reason": mention}) + "\n", encoding="utf-8")
    assert leak_hits(root / "eval", pat_file, run_pat_file) == [], \
        "an expected mention in a run was reported as a leak"
    public_file.write_text(mention + "\n", encoding="utf-8")
    assert leak_hits(root / "eval", pat_file, run_pat_file) == [str(public_file)], \
        "an expected mention in a public file was not reported"
    public_file.unlink()
    run_file.write_text(json.dumps({"reason": own}) + "\n", encoding="utf-8")
    assert leak_hits(root / "eval", pat_file, run_pat_file) == [str(run_file)], \
        "the oracle's own sentence in a run was not reported"


@check("blind: oracle decrypts, ids resolve, nothing leaks")
def t_leaks(ctx):
    if not os.environ.get("LOS_EVAL_ORACLE_KEY"):
        raise SkipTest("LOS_EVAL_ORACLE_KEY not set")
    from common import world_ids
    from oracle_vault import open_to
    out = ctx["tmp"] / "opened"
    open_to(out)
    oracle_dir = out / "oracle"
    pats = oracle_patterns(oracle_dir)
    run_pats = oracle_patterns(oracle_dir, mentions=False)
    pat_file = ctx["tmp"] / "patterns.txt"
    pat_file.write_text("\n".join(pats) + "\n", encoding="utf-8")
    run_pat_file = ctx["tmp"] / "run-patterns.txt"
    run_pat_file.write_text("\n".join(run_pats) + "\n", encoding="utf-8")
    hits = leak_hits(EVAL, pat_file, run_pat_file)
    assert not hits, f"oracle text found in public files: {hits}"
    commits = subprocess.run(["git", "log", "--all", "--format=%H", "--", "tests/eval"],
                             cwd=REPO, capture_output=True, text=True).stdout.split()
    scopes = ((pat_file, ["tests/eval", ":!tests/eval/private", ":!tests/eval/runs"]),
              (run_pat_file, ["tests/eval/runs"]))
    for commit in commits:
        for patterns, pathspec in scopes:
            proc = subprocess.run(["git", "grep", "-lF", "-f", str(patterns), commit, "--",
                                   *pathspec], cwd=REPO, capture_output=True, text=True)
            assert not proc.stdout.strip(), f"oracle text in commit {commit[:12]}: {proc.stdout}"
    if "world" in ctx:
        world_root = ctx["world"].parent.parent
        hits = subprocess.run(["grep", "-rlF", "-f", str(pat_file), "--exclude-dir=.git",
                               str(world_root)], capture_output=True, text=True).stdout.split()
        assert not hits, f"oracle text inside a built world: {hits[:5]}"
        ids = world_ids(ctx["world"])
        rel = yaml.safe_load((oracle_dir / "relations.yaml").read_text())["probes"]
        bad = sorted({j["t"] for p in rel.values() for j in p["judgments"]} - ids)
        assert not bad, f"oracle targets missing from the world: {bad}"
    return f"{len(pats)} patterns ({len(run_pats)} for runs/), {len(commits)} commits scanned"


# -------------------------------------------------------------------- lint
@check("lint: ruff over tests/eval")
def t_ruff():
    ruff = REPO / ".venv" / "bin" / "ruff"
    if not ruff.exists():
        raise SkipTest("ruff not installed in .venv")
    proc = subprocess.run([str(ruff), "check", "tests/eval"], cwd=REPO, capture_output=True,
                          text=True)
    assert proc.returncode == 0, proc.stdout[-3000:]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--keep", action="store_true", help="keep the temporary worlds")
    args = parser.parse_args(argv)
    tmp = Path(tempfile.mkdtemp(prefix="los-eval-selftest-"))
    ctx = {"quick": args.quick, "tmp": tmp}
    t_bundles()
    t_public_ids()
    t_schemas()
    t_score_connections()
    t_score_retrieval()
    t_world(ctx)
    t_final_state(ctx)
    t_observe(ctx)
    t_determinism(ctx)
    t_private_tracked()
    t_leak_scan_toy(ctx)
    t_leaks(ctx)
    t_ruff()
    width = max(len(n) for _, n, _ in RESULTS)
    for status, name, note in RESULTS:
        print(f"{status:4}  {name:{width}}  {note.splitlines()[0] if note else ''}")
        if status == "FAIL":
            print("      " + note.replace("\n", "\n      "))
    if not args.keep:
        shutil.rmtree(tmp, ignore_errors=True)
    else:
        print(f"kept {tmp}")
    return 1 if any(s == "FAIL" for s, _, _ in RESULTS) else 0


if __name__ == "__main__":
    sys.exit(main())

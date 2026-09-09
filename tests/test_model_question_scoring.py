"""Per-model scoring for held-out operator questions, tested both ways.

Synthetic trials (fake ids, one trivial real predicate) prove the strict
contracts — key exclusion, refusals, verdict categories — without touching
the held-out set. One round trip runs the real held-out trials discovered
by split, never by name, so no held-out id appears in this file.
"""

import json
from pathlib import Path

import evaluate_operator_questions as evalq
import pytest
import yaml

REAL_TRIALS = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "verified_operator_questions"
)


def _write_trial(directory, stem, *, split="heldout",
                 predicate="RepoClean", inputs, expected):
    record = {
        "id": stem, "split": split, "class": "synthetic",
        "question": f"synthetic probe {stem}?",
        "procedure": {"predicate": predicate, "inputs": inputs},
        "expected": expected, "notes": f"synthetic record {stem}",
    }
    (directory / f"{stem}.yaml").write_text(
        yaml.safe_dump(record, sort_keys=True), encoding="utf-8")


def _synthetic_trials(tmp_path):
    """Two boolean trials over a pure predicate: one true, one false."""
    trials = tmp_path / "trials"
    trials.mkdir()
    _write_trial(
        trials, "trial-synth-true",
        inputs={"error_count": 0, "new_or_grown_warnings": 0},
        expected={"is_true": True},
    )
    _write_trial(
        trials, "trial-synth-false",
        inputs={"error_count": 2, "new_or_grown_warnings": 0},
        expected={"is_false": True},
    )
    return trials


def test_prepare_excludes_the_answer_key(tmp_path):
    trials = _synthetic_trials(tmp_path)
    records = evalq.load_trials(trials)
    assert [record["id"] for record in records] == [
        "trial-synth-false", "trial-synth-true"]
    package = evalq.prepare_package(records)
    assert package["trial_set_digest"] == evalq.trial_set_digest(records)
    assert len(package["trials"]) == 2
    assert "expected" not in json.dumps(package)
    for entry in package["trials"]:
        assert set(entry) == {"id", "class", "question", "procedure",
                              "notes"}


def test_prepare_refuses_non_heldout_and_malformed(tmp_path):
    trials = tmp_path / "trials"
    trials.mkdir()
    _write_trial(trials, "trial-ok",
                 inputs={"error_count": 0, "new_or_grown_warnings": 0},
                 expected={"is_true": True})
    with pytest.raises(evalq.EvalError):
        evalq.load_trials(tmp_path / "missing-dir")
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(evalq.EvalError, match="no held-out trials"):
        evalq.load_trials(empty)
    illustrated = tmp_path / "illustrated"
    illustrated.mkdir()
    _write_trial(illustrated, "trial-ok",
                 inputs={"error_count": 0, "new_or_grown_warnings": 0},
                 expected={"is_true": True}, split="example")
    with pytest.raises(evalq.EvalError, match="no held-out trials"):
        evalq.load_trials(illustrated)
    renamed = tmp_path / "renamed"
    renamed.mkdir()
    (renamed / "other-name.yaml").write_text(
        (trials / "trial-ok.yaml").read_text(encoding="utf-8"),
        encoding="utf-8")
    with pytest.raises(evalq.EvalError, match="does not match its filename"):
        evalq.load_trials(renamed)
    unknown = tmp_path / "unknown"
    unknown.mkdir()
    _write_trial(unknown, "trial-ok", predicate="NoSuchPredicate",
                 inputs={}, expected={"is_true": True})
    with pytest.raises(evalq.EvalError, match="unregistered predicate"):
        evalq.load_trials(unknown)
    doubled = tmp_path / "doubled"
    doubled.mkdir()
    _write_trial(doubled, "trial-ok",
                 inputs={"error_count": 0, "new_or_grown_warnings": 0},
                 expected={"is_true": True})
    other = {"id": "trial-ok", "split": "heldout", "class": "synthetic",
             "question": "dup?", "procedure": {"predicate": "RepoClean",
             "inputs": {"error_count": 0, "new_or_grown_warnings": 0}},
             "expected": {"is_true": True}, "notes": "dup"}
    (doubled / "zzz.yaml").write_text(
        yaml.safe_dump(other, sort_keys=True), encoding="utf-8")
    with pytest.raises(evalq.EvalError, match="duplicate trial ids"):
        evalq.load_trials(doubled)


def test_mixed_directory_admits_only_heldout(tmp_path):
    mixed = tmp_path / "mixed"
    mixed.mkdir()
    _write_trial(mixed, "trial-held",
                 inputs={"error_count": 0, "new_or_grown_warnings": 0},
                 expected={"is_true": True})
    _write_trial(mixed, "trial-shown",
                 inputs={"error_count": 0, "new_or_grown_warnings": 0},
                 expected={"is_true": True}, split="example")
    records = evalq.load_trials(mixed)
    assert [record["id"] for record in records] == ["trial-held"]


def test_score_pass_fail_unanswered_and_counts(tmp_path):
    trials = _synthetic_trials(tmp_path)
    records = evalq.load_trials(trials)
    report = evalq.score_trials(
        records, {"trial-synth-true": True, "trial-synth-false": True})
    assert report["trial_set_digest"] == evalq.trial_set_digest(records)
    assert report["addressed_voq_ids"] == [
        "trial-synth-false", "trial-synth-true"]
    assert {row["id"]: row["verdict"] for row in report["verdicts"]} == {
        "trial-synth-true": "pass", "trial-synth-false": "fail"}
    assert report["counts"] == {"pass": 1, "fail": 1, "unanswered": 0,
                                "fixture-rot": 0}
    assert "understands" not in json.dumps(report)
    report = evalq.score_trials(records, {"trial-synth-true": True})
    assert {row["id"]: row["verdict"] for row in report["verdicts"]} == {
        "trial-synth-true": "pass", "trial-synth-false": "unanswered"}
    assert report["counts"]["unanswered"] == 1
    repinned = evalq.score_trials(records, {"trial-synth-true": False})
    assert repinned["input_digest"] != report["input_digest"]


def test_score_refuses_unknown_ids_empty_strings_and_lists(tmp_path):
    trials = _synthetic_trials(tmp_path)
    records = evalq.load_trials(trials)
    with pytest.raises(evalq.EvalError, match="unknown trials"):
        evalq.score_trials(records, {"trial-ghost": True})
    with pytest.raises(evalq.EvalError, match="empty string"):
        evalq.score_trials(records, {"trial-synth-true": ""})
    with pytest.raises(evalq.EvalError, match="not a single stated verdict"):
        evalq.score_trials(records, {"trial-synth-true": [True, False]})
    with pytest.raises(evalq.EvalError, match="unreadable"):
        evalq.load_answers(tmp_path / "missing.json")
    not_object = tmp_path / "list.json"
    not_object.write_text("[true]", encoding="utf-8")
    with pytest.raises(evalq.EvalError, match="not a JSON object"):
        evalq.load_answers(not_object)


def test_score_marks_fixture_rot_not_model_failure(tmp_path):
    trials = tmp_path / "trials"
    trials.mkdir()
    _write_trial(trials, "trial-rot",
                 inputs={"error_count": 0, "new_or_grown_warnings": 0},
                 expected={"is_false": True})
    _write_trial(trials, "trial-broken",
                 inputs={"error_count": 0},
                 expected={"is_true": True})
    records = evalq.load_trials(trials)
    report = evalq.score_trials(
        records, {"trial-rot": False, "trial-broken": True})
    assert {row["id"]: row["verdict"] for row in report["verdicts"]} == {
        "trial-broken": "fixture-rot", "trial-rot": "fixture-rot"}
    assert report["counts"] == {"pass": 0, "fail": 0, "unanswered": 0,
                                "fixture-rot": 2}


def test_score_handles_equals_and_contains_ops(tmp_path, monkeypatch):
    import types

    from learning_os.semantics import PREDICATES

    fake = types.SimpleNamespace(
        function=lambda **inputs: "hello world")
    monkeypatch.setitem(PREDICATES, "FakePredicate", fake)
    trials = tmp_path / "trials"
    trials.mkdir()
    _write_trial(trials, "trial-equals", predicate="FakePredicate",
                 inputs={}, expected={"equals": "hello world"})
    _write_trial(trials, "trial-contains", predicate="FakePredicate",
                 inputs={}, expected={"contains": "hello"})
    records = evalq.load_trials(trials)
    report = evalq.score_trials(
        records, {"trial-equals": "hello world",
                  "trial-contains": "say hello kindly"})
    assert {row["id"]: row["verdict"] for row in report["verdicts"]} == {
        "trial-contains": "pass", "trial-equals": "pass"}
    report = evalq.score_trials(
        records, {"trial-equals": "goodbye", "trial-contains": 7})
    assert {row["id"]: row["verdict"] for row in report["verdicts"]} == {
        "trial-contains": "fail", "trial-equals": "fail"}


def test_real_heldout_set_scores_end_to_end(tmp_path):
    """The real set, discovered by split: a correct answer sheet passes,
    one flipped boolean fails exactly once. No held-out id is quoted."""
    import subprocess
    import sys

    from learning_os.semantics import evaluate

    records = evalq.load_trials(REAL_TRIALS)
    assert len(records) == 5
    package = evalq.prepare_package(records)
    assert "expected" not in json.dumps(package)
    truthful = {}
    for record in records:
        truth = evaluate(
            record["procedure"]["predicate"],
            **record["procedure"]["inputs"])
        op = next(iter(record["expected"]))
        truthful[record["id"]] = truth if op in ("equals", "contains") else bool(truth)
    report = evalq.score_trials(records, truthful)
    assert report["counts"]["pass"] == 5
    assert report["trial_set_digest"] == package["trial_set_digest"]
    flipped = dict(truthful)
    victim = next(trial_id for trial_id, answer in truthful.items()
                  if isinstance(answer, bool))
    flipped[victim] = not flipped[victim]
    report = evalq.score_trials(records, flipped)
    assert report["counts"] == {"pass": 4, "fail": 1, "unanswered": 0,
                                "fixture-rot": 0}
    tool = Path(__file__).resolve().parent.parent / "tools" / (
        "evaluate_operator_questions.py")
    package_file = tmp_path / "package.json"
    answers_file = tmp_path / "answers.json"
    report_file = tmp_path / "report.json"
    answers_file.write_text(json.dumps(truthful), encoding="utf-8")
    prep = subprocess.run(
        [sys.executable, str(tool), "prepare", "--trials", str(REAL_TRIALS),
         "--out", str(package_file)],
        capture_output=True, text=True, timeout=120)
    assert prep.returncode == 0, prep.stderr
    assert "digest" in prep.stdout
    scoring = subprocess.run(
        [sys.executable, str(tool), "score", "--trials", str(REAL_TRIALS),
         "--answers", str(answers_file), "--out", str(report_file)],
        capture_output=True, text=True, timeout=120)
    assert scoring.returncode == 0, scoring.stderr
    assert json.loads(report_file.read_text(
        encoding="utf-8"))["counts"]["pass"] == 5
    bad = dict(truthful)
    bad["voq-no-such-trial"] = True
    bad_file = tmp_path / "bad.json"
    bad_file.write_text(json.dumps(bad), encoding="utf-8")
    refused = subprocess.run(
        [sys.executable, str(tool), "score", "--trials", str(REAL_TRIALS),
         "--answers", str(bad_file), "--out", str(tmp_path / "x.json")],
        capture_output=True, text=True, timeout=120)
    assert refused.returncode == 2

"""Question-to-procedure scoring for held-out operator questions (format 2).

Synthetic trials (fake ids, one trivial real predicate) prove the strict
contracts — reference exclusion, hidden-key separation, refusals, verdict
categories — without touching the held-out set. One round trip runs the
real held-out trials discovered by split, never by name, so no held-out
id appears in this file.
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
                 predicate="RepoClean", inputs, expected, accepted=()):
    record = {
        "id": stem, "split": split, "class": "synthetic",
        "question": f"synthetic probe {stem}?",
        "notes": f"synthetic record {stem}",
        "reference": {
            "procedure": {"predicate": predicate, "inputs": inputs},
            "expected": expected,
            "accepted": list(accepted),
        },
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


def _submit(predicate="RepoClean", inputs=None, answer=True):
    return {"procedure": {"predicate": predicate, "inputs": inputs or {}},
            "answer": answer}


def test_prepare_excludes_reference_and_digests_public_only(tmp_path):
    trials = _synthetic_trials(tmp_path)
    records = evalq.load_trials(trials)
    assert [record["id"] for record in records] == [
        "trial-synth-false", "trial-synth-true"]
    package = evalq.prepare_package(records)
    assert package["package_format"] == 2
    assert package["package_digest"] == evalq.package_digest(
        package["trials"])
    assert len(package["trials"]) == 2
    dumped = json.dumps(package)
    for token in ("expected", "procedure", "accepted", "RepoClean"):
        assert token not in dumped
    for entry in package["trials"]:
        assert set(entry) == {"id", "class", "question", "notes"}


def test_hidden_key_change_leaves_the_public_package_identical(tmp_path):
    """Examination finding 1 (hidden-key separation gate): changing only
    the hidden answer key must not move the model-visible package. The
    evaluator-side key binding moves instead."""
    first = tmp_path / "first"
    first.mkdir()
    _write_trial(first, "trial-key",
                 inputs={"error_count": 0, "new_or_grown_warnings": 0},
                 expected={"is_true": True})
    second = tmp_path / "second"
    second.mkdir()
    _write_trial(second, "trial-key",
                 inputs={"error_count": 0, "new_or_grown_warnings": 0},
                 expected={"is_false": True})
    package_one = evalq.prepare_package(evalq.load_trials(first))
    package_two = evalq.prepare_package(evalq.load_trials(second))
    assert package_one["trials"] == package_two["trials"]
    assert package_one["package_digest"] == package_two["package_digest"]
    assert evalq.key_digest(
        evalq.load_trials(first)) != evalq.key_digest(
            evalq.load_trials(second))


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
             "question": "dup?",
             "notes": "dup",
             "reference": {
                 "procedure": {
                     "predicate": "RepoClean",
                     "inputs": {"error_count": 0,
                                "new_or_grown_warnings": 0}},
                 "expected": {"is_true": True},
                 "accepted": []}}
    (doubled / "zzz.yaml").write_text(
        yaml.safe_dump(other, sort_keys=True), encoding="utf-8")
    with pytest.raises(evalq.EvalError, match="duplicate trial ids"):
        evalq.load_trials(doubled)
    no_reference = tmp_path / "no-reference"
    no_reference.mkdir()
    bare = {"id": "trial-ok", "split": "heldout", "class": "synthetic",
            "question": "bare?", "notes": "bare",
            "procedure": {"predicate": "RepoClean", "inputs": {}},
            "expected": {"is_true": True}}
    (no_reference / "trial-ok.yaml").write_text(
        yaml.safe_dump(bare, sort_keys=True), encoding="utf-8")
    with pytest.raises(evalq.EvalError, match="unexpected keys"):
        evalq.load_trials(no_reference)


def test_repeated_trial_keys_refuse_before_decoding(tmp_path):
    trials = tmp_path / "trials"
    trials.mkdir()
    (trials / "trial-dup.yaml").write_text(
        "id: trial-dup\nid: trial-dup\nsplit: heldout\nclass: synthetic\n"
        "question: dup?\nnotes: dup\nreference:\n"
        "  procedure: {predicate: RepoClean, inputs: {}}\n"
        "  expected: {is_true: true}\n  accepted: []\n",
        encoding="utf-8")
    with pytest.raises(evalq.EvalError, match="repeated"):
        evalq.load_trials(trials)


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


def test_score_pass_fail_unanswered_unadjudicated_and_counts(tmp_path):
    trials = _synthetic_trials(tmp_path)
    records = evalq.load_trials(trials)
    report = evalq.score_trials(records, {
        "trial-synth-true": _submit(
            inputs={"error_count": 0, "new_or_grown_warnings": 0},
            answer=True),
        "trial-synth-false": _submit(
            inputs={"error_count": 2, "new_or_grown_warnings": 0},
            answer=True),
    })
    assert report["package_format"] == 2
    assert report["package_digest"] == evalq.prepare_package(
        records)["package_digest"]
    assert report["key_digest"] == evalq.key_digest(records)
    assert report["addressed_voq_ids"] == [
        "trial-synth-false", "trial-synth-true"]
    assert {row["id"]: (row["verdict"], row["procedure_accepted"])
            for row in report["verdicts"]} == {
        "trial-synth-true": ("pass", True),
        "trial-synth-false": ("fail", True)}
    assert report["counts"] == {"pass": 1, "fail": 1, "unanswered": 0,
                                "unadjudicated": 0, "fixture-rot": 0}
    assert "understands" not in json.dumps(report)
    report = evalq.score_trials(records, {
        "trial-synth-true": _submit(
            inputs={"error_count": 0, "new_or_grown_warnings": 0},
            answer=None)})
    assert {row["id"]: row["verdict"]
            for row in report["verdicts"]} == {
        "trial-synth-true": "unanswered", "trial-synth-false": "unanswered"}
    assert report["counts"]["unanswered"] == 2
    novel = evalq.score_trials(records, {
        "trial-synth-true": _submit(
            inputs={"error_count": 0, "new_or_grown_warnings": 0},
            answer=True),
        "trial-synth-false": _submit(
            inputs={"error_count": 99, "new_or_grown_warnings": 0},
            answer=False),
    })
    assert {row["id"]: row["verdict"]
            for row in novel["verdicts"]} == {
        "trial-synth-true": "pass", "trial-synth-false": "unadjudicated"}
    assert novel["counts"]["unadjudicated"] == 1
    repinned = evalq.score_trials(records, {
        "trial-synth-true": _submit(
            inputs={"error_count": 0, "new_or_grown_warnings": 0},
            answer=False)})
    assert repinned["input_digest"] != report["input_digest"]


def test_score_refuses_malformed_submissions(tmp_path):
    trials = _synthetic_trials(tmp_path)
    records = evalq.load_trials(trials)
    good_inputs = {"error_count": 0, "new_or_grown_warnings": 0}
    with pytest.raises(evalq.EvalError, match="unknown trials"):
        evalq.score_trials(records, {"trial-ghost": _submit()})
    with pytest.raises(evalq.EvalError, match="must hold exactly"):
        evalq.score_trials(records, {"trial-synth-true": True})
    with pytest.raises(evalq.EvalError, match="empty answer"):
        evalq.score_trials(records, {
            "trial-synth-true": _submit(inputs=good_inputs, answer="")})
    with pytest.raises(evalq.EvalError, match="no single stated answer"):
        evalq.score_trials(records, {
            "trial-synth-true": _submit(inputs=good_inputs,
                                        answer=[True, False])})
    with pytest.raises(evalq.EvalError, match="malformed procedure"):
        evalq.score_trials(records, {
            "trial-synth-true": {"procedure": {"predicate": "RepoClean"},
                                 "answer": True}})
    with pytest.raises(evalq.EvalError, match="not a JSON object"):
        evalq.score_trials(records, [True])
    with pytest.raises(evalq.EvalError, match="unreadable"):
        evalq.load_answers(tmp_path / "missing.json")
    not_object = tmp_path / "list.json"
    not_object.write_text("[true]", encoding="utf-8")
    with pytest.raises(evalq.EvalError, match="not a JSON object"):
        evalq.load_answers(not_object)


def test_repeated_answer_keys_refuse_before_decoding(tmp_path):
    """Examination finding 2: conflicting duplicates must refuse through
    the loader and through the actual CLI, not just in unit calls."""
    import subprocess
    import sys

    trials = _synthetic_trials(tmp_path)
    dupes = tmp_path / "dupes.json"
    dupes.write_text(
        '{"trial-synth-true": {"procedure": {"predicate": "RepoClean", '
        '"inputs": {}}, "answer": false}, '
        '"trial-synth-true": {"procedure": {"predicate": "RepoClean", '
        '"inputs": {}}, "answer": true}}',
        encoding="utf-8")
    with pytest.raises(evalq.EvalError, match="repeats key"):
        evalq.load_answers(dupes)
    tool = Path(__file__).resolve().parent.parent / "tools" / (
        "evaluate_operator_questions.py")
    refused = subprocess.run(
        [sys.executable, str(tool), "score", "--trials", str(trials),
         "--answers", str(dupes), "--out", str(tmp_path / "x.json")],
        capture_output=True, text=True, timeout=120)
    assert refused.returncode == 2
    assert "repeats key" in refused.stderr


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
    report = evalq.score_trials(records, {
        "trial-rot": _submit(
            inputs={"error_count": 0, "new_or_grown_warnings": 0},
            answer=False),
        "trial-broken": _submit(inputs={"error_count": 0}, answer=True),
    })
    assert {row["id"]: row["verdict"] for row in report["verdicts"]} == {
        "trial-broken": "fixture-rot", "trial-rot": "fixture-rot"}
    assert report["counts"] == {"pass": 0, "fail": 0, "unanswered": 0,
                                "unadjudicated": 0, "fixture-rot": 2}


@pytest.mark.parametrize("answer, verdict", [(False, "pass"), (True, "fail")])
def test_adjudicated_variant_procedure_scores(tmp_path, answer, verdict):
    """An accepted equivalent is creditable; the reference is not the
    only licit way to derive the answer."""
    trials = tmp_path / "trials"
    trials.mkdir()
    _write_trial(
        trials, "trial-variant",
        inputs={"error_count": 1, "new_or_grown_warnings": 0},
        expected={"is_false": True},
        accepted=[{"predicate": "RepoClean",
                   "inputs": {"error_count": 0,
                              "new_or_grown_warnings": 1}}],
    )
    records = evalq.load_trials(trials)
    report = evalq.score_trials(records, {
        "trial-variant": _submit(
            inputs={"error_count": 0, "new_or_grown_warnings": 1},
            answer=answer)})
    assert [row["verdict"] for row in report["verdicts"]] == [verdict]


@pytest.mark.parametrize("inputs", [
    {"error_count": 0, "new_or_grown_warnings": 1},
    {"error_count": 0},
], ids=["contradictory", "unexecutable"])
def test_unhealthy_accepted_variant_is_fixture_rot_through_cli(tmp_path, inputs):
    import subprocess
    import sys

    trials = tmp_path / "trials"
    trials.mkdir()
    _write_trial(
        trials, "trial-variant",
        inputs={"error_count": 0, "new_or_grown_warnings": 0},
        expected={"is_true": True},
        accepted=[{"predicate": "RepoClean", "inputs": inputs}],
    )
    answers = tmp_path / "answers.json"
    answers.write_text(json.dumps({
        "trial-variant": _submit(inputs=inputs, answer=True)}))
    output = tmp_path / "report.json"
    tool = Path(__file__).resolve().parent.parent / "tools" / (
        "evaluate_operator_questions.py")
    result = subprocess.run(
        [sys.executable, str(tool), "score", "--trials", str(trials),
         "--answers", str(answers), "--out", str(output)],
        capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text())
    assert report["verdicts"] == [{
        "id": "trial-variant", "verdict": "fixture-rot",
        "procedure_accepted": False}]
    assert report["counts"] == {
        "pass": 0, "fail": 0, "unanswered": 0,
        "unadjudicated": 0, "fixture-rot": 1}


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
    report = evalq.score_trials(records, {
        "trial-equals": _submit(
            predicate="FakePredicate", inputs={}, answer="hello world"),
        "trial-contains": _submit(
            predicate="FakePredicate", inputs={},
            answer="say hello kindly")})
    assert {row["id"]: row["verdict"] for row in report["verdicts"]} == {
        "trial-contains": "pass", "trial-equals": "pass"}
    report = evalq.score_trials(records, {
        "trial-equals": _submit(
            predicate="FakePredicate", inputs={}, answer="goodbye"),
        "trial-contains": _submit(
            predicate="FakePredicate", inputs={}, answer=7)})
    assert {row["id"]: row["verdict"] for row in report["verdicts"]} == {
        "trial-contains": "fail", "trial-equals": "fail"}


def test_real_heldout_set_scores_end_to_end(tmp_path):
    """The real set, discovered by split: correct procedures and answers
    pass, one flipped boolean fails exactly once, one novel procedure is
    unadjudicated rather than passed. No held-out id is quoted."""
    import subprocess
    import sys

    from learning_os.semantics import evaluate

    records = evalq.load_trials(REAL_TRIALS)
    assert len(records) == 5
    package = evalq.prepare_package(records)
    dumped = json.dumps(package)
    for token in ("expected", "procedure", "accepted"):
        assert token not in dumped
    truthful = {}
    for record in records:
        reference = record["reference"]["procedure"]
        truth = evaluate(reference["predicate"], **reference["inputs"])
        op = next(iter(record["reference"]["expected"]))
        truthful[record["id"]] = {
            "procedure": dict(reference),
            "answer": truth if op in ("equals", "contains") else bool(truth),
        }
    report = evalq.score_trials(records, truthful)
    assert report["counts"]["pass"] == 5
    assert report["package_digest"] == package["package_digest"]
    assert report["key_digest"] == evalq.key_digest(records)
    flipped = {trial_id: dict(submission)
               for trial_id, submission in truthful.items()}
    victim = next(trial_id for trial_id, submission in truthful.items()
                  if isinstance(submission["answer"], bool))
    flipped[victim] = dict(flipped[victim])
    flipped[victim]["answer"] = not flipped[victim]["answer"]
    report = evalq.score_trials(records, flipped)
    assert report["counts"] == {"pass": 4, "fail": 1, "unanswered": 0,
                                "unadjudicated": 0, "fixture-rot": 0}
    novel = {trial_id: dict(submission)
             for trial_id, submission in truthful.items()}
    novel[victim] = {"procedure": {"predicate": "RepoClean", "inputs": {}},
                     "answer": flipped[victim]["answer"]}
    report = evalq.score_trials(records, novel)
    assert report["counts"]["unadjudicated"] == 1
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
    package_text = package_file.read_text(encoding="utf-8")
    for token in ("expected", "procedure", "accepted"):
        assert token not in package_text
    scoring = subprocess.run(
        [sys.executable, str(tool), "score", "--trials", str(REAL_TRIALS),
         "--answers", str(answers_file), "--out", str(report_file)],
        capture_output=True, text=True, timeout=120)
    assert scoring.returncode == 0, scoring.stderr
    assert json.loads(report_file.read_text(
        encoding="utf-8"))["counts"]["pass"] == 5
    bad = dict(truthful)
    bad["voq-no-such-trial"] = _submit()
    bad_file = tmp_path / "bad.json"
    bad_file.write_text(json.dumps(bad), encoding="utf-8")
    refused = subprocess.run(
        [sys.executable, str(tool), "score", "--trials", str(REAL_TRIALS),
         "--answers", str(bad_file), "--out", str(tmp_path / "x.json")],
        capture_output=True, text=True, timeout=120)
    assert refused.returncode == 2

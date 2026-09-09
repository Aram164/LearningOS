"""Offline per-model scoring for held-out operator questions.

The suite proves predicates answer; this tool scores a *model* outside the
suite without leaking the answer key. ``prepare`` emits a model context
built from the held-out trial set — question text, procedure inputs, and
notes, but never the ``expected`` mapping, which is the key. ``score``
executes the same predicates over the same inputs (answers score from
evidence alone) and compares the model's stated verdicts against the
computed ones.

Reports carry per-question verdicts, counts, the exact input digest, and
the addressed VOQ ids. Counts are bookkeeping, not competence labels:
nothing here declares what a model understands.

Usage:
    python tools/evaluate_operator_questions.py prepare [--trials DIR] --out PACKAGE.json
    python tools/evaluate_operator_questions.py score [--trials DIR] --answers ANSWERS.json --out REPORT.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

from learning_os.semantics import PREDICATES, evaluate

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TRIALS = ROOT / "tests/fixtures/verified_operator_questions"

EXPECTED_OPS = ("equals", "is_true", "is_false", "contains")

VERDICTS = ("pass", "fail", "unanswered", "fixture-rot")


class EvalError(Exception):
    """A refused evaluation package: malformed trials or answers."""


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        _canonical(value).encode("utf-8")).hexdigest()


def load_trials(trials_dir: Path | str) -> list[dict]:
    """Load the directory and return its held-out trials. Refuses the rest.

    Every file must be a well-formed VOQ record: exact keys, a known
    split, an id matching its filename, a registered predicate, mapping
    inputs, and an answer key holding exactly one known op. Duplicate ids
    refuse before per-file detail checks so every documented refusal is
    reachable. Examples are validated like everything else but never
    admitted — illustrations are not eval material — and a directory with
    no held-out trials refuses.
    """
    root = Path(trials_dir)
    if not root.is_dir():
        raise EvalError(f"trial set is not a directory: {root}")
    parsed: list[tuple[str, dict]] = []
    for path in sorted(root.glob("*.yaml")):
        try:
            record = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise EvalError(f"trial {path.name} is not valid YAML: {exc}") from None
        if not isinstance(record, dict):
            raise EvalError(f"trial {path.name} is not a mapping")
        parsed.append((path.name, record))
    ids = [record.get("id") for _, record in parsed]
    if len(set(map(str, ids))) != len(ids):
        raise EvalError(f"duplicate trial ids in {root}")
    records = []
    for name, record in parsed:
        if set(record) != {"id", "split", "class", "question", "procedure",
                           "expected", "notes"}:
            raise EvalError(f"trial {name} has unexpected keys")
        if record["split"] not in ("example", "heldout"):
            raise EvalError(f"trial {name} has an unknown split")
        if record["id"] != Path(name).stem:
            raise EvalError(
                f"trial {name} id {record['id']!r} does not match its filename")
        procedure = record["procedure"]
        if not isinstance(procedure, dict) or set(procedure) != {
                "predicate", "inputs"}:
            raise EvalError(f"trial {name} has a malformed procedure")
        if procedure["predicate"] not in PREDICATES:
            raise EvalError(
                f"trial {name} names an unregistered predicate")
        if not isinstance(procedure["inputs"], dict):
            raise EvalError(f"trial {name} has malformed inputs")
        expected = record["expected"]
        if not isinstance(expected, dict) or len(expected) != 1 \
                or next(iter(expected)) not in EXPECTED_OPS:
            raise EvalError(f"trial {name} has a malformed answer key")
        records.append(record)
    heldout = sorted(
        (record for record in records if record["split"] == "heldout"),
        key=lambda record: record["id"])
    if not heldout:
        raise EvalError(f"no held-out trials in {root}")
    return heldout


def trial_set_digest(records: list[dict]) -> str:
    """Digest over the full keyed records: binds a package to its keys."""
    return _digest(records)


def prepare_package(records: list[dict]) -> dict:
    """Model context for the trials: everything except the answer key.

    The ``expected`` mapping never leaves this function; ``split`` is
    answering-irrelevant metadata and stays out too.
    """
    return {
        "trial_set_digest": trial_set_digest(records),
        "trials": [
            {key: record[key] for key in (
                "id", "class", "question", "procedure", "notes")}
            for record in records
        ],
    }


def _check_answers(answers: object) -> dict[str, object]:
    """Shape-check stated verdicts: a mapping of single JSON scalars.

    A missing key or an explicit null means the trial goes unanswered;
    anything else malformed refuses — a score never silently advances on
    bad input, however the answers arrived.
    """
    if not isinstance(answers, dict):
        raise EvalError("answers are not a JSON object")
    for key, value in answers.items():
        if value is None:
            continue
        if isinstance(value, (str, int, float)):
            if isinstance(value, str) and not value:
                raise EvalError(f"answer for {key!r} is an empty string")
            continue
        raise EvalError(f"answer for {key!r} is not a single stated verdict")
    return answers


def load_answers(path: Path | str) -> dict[str, object]:
    """Load the model's stated verdicts keyed by trial id."""
    try:
        return _check_answers(
            json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:
        raise EvalError(f"answers file is unreadable: {exc}") from None


def _model_matches(op: str, wanted: object, model: object, truth: object) -> bool:
    if op == "equals":
        return model == truth
    if op == "is_true":
        return model is True
    if op == "is_false":
        return model is False
    return isinstance(model, str) and wanted in model


def _fixture_holds(expected: dict, truth: object) -> bool:
    op, wanted = next(iter(expected.items()))
    if op == "equals":
        return truth == wanted
    if op == "is_true":
        return truth is True
    if op == "is_false":
        return truth is False
    return wanted in truth if isinstance(truth, (str, list, tuple)) else False


def score_trials(records: list[dict], answers: dict[str, object]) -> dict:
    """Score stated verdicts against executed predicates. Pure.

    Unknown answer ids refuse. A trial the predicates cannot execute, or
    whose computed verdict contradicts its own key, is ``fixture-rot`` —
    fixture debt, never model signal. Everything else is ``pass``,
    ``fail``, or ``unanswered``. The report pins the exact inputs it was
    computed from.
    """
    answers = _check_answers(answers)
    known = {record["id"] for record in records}
    strange = sorted(set(answers) - known)
    if strange:
        raise EvalError(f"answers address unknown trials: {', '.join(strange)}")
    verdicts = []
    for record in records:
        trial_id = record["id"]
        try:
            truth = evaluate(
                record["procedure"]["predicate"],
                **record["procedure"]["inputs"])
            healthy = _fixture_holds(record["expected"], truth)
        except Exception:
            healthy, truth = False, None
        if not healthy:
            verdicts.append({"id": trial_id, "verdict": "fixture-rot"})
            continue
        if trial_id not in answers or answers[trial_id] is None:
            verdicts.append({"id": trial_id, "verdict": "unanswered"})
            continue
        op, wanted = next(iter(record["expected"].items()))
        verdict = "pass" if _model_matches(
            op, wanted, answers[trial_id], truth) else "fail"
        verdicts.append({"id": trial_id, "verdict": verdict})
    counts = {verdict: sum(1 for row in verdicts if row["verdict"] == verdict)
              for verdict in VERDICTS}
    return {
        "trial_set_digest": trial_set_digest(records),
        "input_digest": _digest({"trials": records, "answers": answers}),
        "addressed_voq_ids": sorted(known),
        "verdicts": verdicts,
        "counts": counts,
    }


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True,
                               ensure_ascii=False) + "\n", encoding="utf-8")


def cmd_prepare(args: argparse.Namespace) -> int:
    records = load_trials(args.trials)
    package = prepare_package(records)
    _write_json(Path(args.out), package)
    print(f"prepared {len(package['trials'])} trials, "
          f"digest {package['trial_set_digest']}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    records = load_trials(args.trials)
    report = score_trials(records, load_answers(args.answers))
    _write_json(Path(args.out), report)
    counts = report["counts"]
    print(f"score {counts['pass']}/{len(report['verdicts'])} "
          f"({counts['unanswered']} unanswered, "
          f"{counts['fixture-rot']} fixture-rot)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Offline per-model scoring for held-out operator questions")
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="emit the model context package")
    prep.add_argument("--trials", default=str(DEFAULT_TRIALS))
    prep.add_argument("--out", required=True)
    prep.set_defaults(func=cmd_prepare)
    score = sub.add_parser("score", help="score stated verdicts from evidence")
    score.add_argument("--trials", default=str(DEFAULT_TRIALS))
    score.add_argument("--answers", required=True)
    score.add_argument("--out", required=True)
    score.set_defaults(func=cmd_score)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except EvalError as exc:
        print(f"evaluate-operator-questions: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

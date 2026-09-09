"""Offline question-to-procedure evaluation for held-out operator questions.

Replacement specification (research examination 2026-09-09, required
correction for the original model-conformance lesson): the model derives
HOW LearningOS answers a natural-language question — which predicate,
bound to which inputs — and states the answer. Format 1 published the
reference procedure in the model package, reducing the task to following
a supplied recipe; format 2 separates task facts from reference.

Trial record (authored, evaluator-side). Public task facts the model may
see: ``id``, ``split``, ``class``, ``question``, ``notes``. Reference
material the model must never see, under ``reference``: the ``procedure``
(``predicate`` + ``inputs``), the ``expected`` answer key (exactly one
known op), and ``accepted`` — additional adjudicated-equivalent
procedures (may be empty; the reference procedure is always accepted).

``notes`` is public task context. Anything the model must not see lives
under ``reference``; ``prepare`` physically cannot emit it (pinned by
test: the serialized package contains no ``procedure``, ``expected``,
or ``accepted`` token).

Model submission per trial id::

    {"procedure": {"predicate": name, "inputs": {...}}, "answer": scalar|null}

Scoring (evaluator-side, key in hand), per trial:

- submission malformed -> the whole batch refuses (shape violation,
  like an unknown trial id — fail closed, never a partial score);
- fixture unhealthy (reference predicate or submitted accepted alternative
  unexecutable, or its computed truth contradicts the key) -> ``fixture-rot``
  (fixture debt, never model signal);
- answer null or missing -> ``unanswered``;
- well-formed procedure outside the adjudicated set -> ``unadjudicated``
  (needs a human adjudication; never a pass, never a fail);
- accepted procedure + stated answer matches executed truth -> ``pass``;
- accepted procedure + mismatch -> ``fail``.

Digests: ``package_digest`` covers the public package alone — changing
only hidden key material leaves the model-visible package byte-identical
(pinned by test). ``key_digest`` binds the full keyed records and lives
only in the evaluator-side report, never in the package.

Decoding is strict on both sides: repeated keys refuse in answers JSON
and in trial YAML, before any conversion — shape validation after
decoding is too late (examination finding 2).

Reports carry per-trial verdicts, counts, both digests, and the
addressed VOQ ids. Counts are bookkeeping, not competence labels:
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

PACKAGE_FORMAT = 2

VERDICTS = ("pass", "fail", "unanswered", "unadjudicated", "fixture-rot")


class EvalError(Exception):
    """A refused evaluation package: malformed trials or submissions."""


def _canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(
        _canonical(value).encode("utf-8")).hexdigest()


class _NoDupLoader(yaml.SafeLoader):
    """YAML loader that refuses repeated mapping keys during decoding."""


def _no_dup_mapping(loader: _NoDupLoader, node: yaml.MappingNode,
                    deep: bool = False) -> dict:
    keys = [loader.construct_object(key_node, deep=True)
            for key_node, _ in node.value]
    repeated = sorted({str(key) for key in keys if keys.count(key) > 1})
    if repeated:
        raise EvalError(f"repeated mapping key(s): {', '.join(repeated)}")
    return loader.construct_mapping(node, deep=deep)


_NoDupLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_dup_mapping)


def _check_procedure(name: str, procedure: object, what: str) -> dict:
    if not isinstance(procedure, dict) or set(procedure) != {
            "predicate", "inputs"}:
        raise EvalError(f"trial {name} has a malformed {what}")
    if procedure["predicate"] not in PREDICATES:
        raise EvalError(f"trial {name} names an unregistered predicate")
    if not isinstance(procedure["inputs"], dict):
        raise EvalError(f"trial {name} has malformed {what} inputs")
    return procedure


def load_trials(trials_dir: Path | str) -> list[dict]:
    """Load the directory and return its held-out trials. Refuses the rest.

    Every file must be a well-formed trial record: exact keys, a known
    split, an id matching its filename, and a ``reference`` holding the
    procedure, the single-op answer key, and the adjudicated-equivalent
    procedures (possibly none). Duplicate ids refuse before per-file
    detail checks so every documented refusal is reachable. Examples are
    validated like everything else but never admitted — illustrations are
    not eval material — and a directory with no held-out trials refuses.
    """
    root = Path(trials_dir)
    if not root.is_dir():
        raise EvalError(f"trial set is not a directory: {root}")
    parsed: list[tuple[str, dict]] = []
    for path in sorted(root.glob("*.yaml")):
        try:
            record = yaml.load(
                path.read_text(encoding="utf-8"), Loader=_NoDupLoader)
        except yaml.YAMLError as exc:
            raise EvalError(
                f"trial {path.name} is not valid YAML: {exc}") from None
        except EvalError as exc:
            raise EvalError(f"trial {path.name} {exc}") from None
        if not isinstance(record, dict):
            raise EvalError(f"trial {path.name} is not a mapping")
        parsed.append((path.name, record))
    ids = [record.get("id") for _, record in parsed]
    if len(set(map(str, ids))) != len(ids):
        raise EvalError(f"duplicate trial ids in {root}")
    records = []
    for name, record in parsed:
        if set(record) != {"id", "split", "class", "question", "notes",
                           "reference"}:
            raise EvalError(f"trial {name} has unexpected keys")
        if record["split"] not in ("example", "heldout"):
            raise EvalError(f"trial {name} has an unknown split")
        if record["id"] != Path(name).stem:
            raise EvalError(
                f"trial {name} id {record['id']!r} does not match its filename")
        reference = record["reference"]
        if not isinstance(reference, dict) or set(reference) != {
                "procedure", "expected", "accepted"}:
            raise EvalError(f"trial {name} has a malformed reference")
        _check_procedure(name, reference["procedure"], "procedure")
        expected = reference["expected"]
        if not isinstance(expected, dict) or len(expected) != 1 \
                or next(iter(expected)) not in EXPECTED_OPS:
            raise EvalError(f"trial {name} has a malformed answer key")
        accepted = reference["accepted"]
        if not isinstance(accepted, list):
            raise EvalError(
                f"trial {name} has a malformed accepted-procedure list")
        for variant in accepted:
            _check_procedure(name, variant, "accepted procedure")
        records.append(record)
    heldout = sorted(
        (record for record in records if record["split"] == "heldout"),
        key=lambda record: record["id"])
    if not heldout:
        raise EvalError(f"no held-out trials in {root}")
    return heldout


def _public_entries(records: list[dict]) -> list[dict]:
    """The model-visible projection: task facts only, never reference."""
    return [{key: record[key] for key in ("id", "class", "question", "notes")}
            for record in records]


def package_digest(public_trials: list[dict]) -> str:
    """Digest over the public package alone: hidden key changes must not
    move it (examination finding 1 — hidden-key separation gate)."""
    return _digest(public_trials)


def key_digest(records: list[dict]) -> str:
    """Evaluator-side binding of a package to its full keyed records.

    Never ships in the model package; recorded in the score report so an
    audit can re-derive exactly which key scored which submission.
    """
    return _digest(records)


def prepare_package(records: list[dict]) -> dict:
    """Model context for the trials: public task facts, no reference.

    Neither ``procedure`` nor ``expected`` nor ``accepted`` can leave
    this function — the projection keys are enumerated, not subtracted.
    """
    public = _public_entries(records)
    return {
        "package_format": PACKAGE_FORMAT,
        "package_digest": package_digest(public),
        "trials": public,
    }


def _check_submission(trial_id: object, submission: object) -> dict:
    """Shape-check one structured submission: procedure plus answer.

    A missing key or an explicit null answer means the trial goes
    unanswered; anything else malformed refuses — a score never silently
    advances on bad input, however the submission arrived.
    """
    if not isinstance(submission, dict) or set(submission) != {
            "procedure", "answer"}:
        raise EvalError(
            f"submission for {trial_id!r} must hold exactly procedure "
            "and answer")
    procedure = submission["procedure"]
    if not isinstance(procedure, dict) or set(procedure) != {
            "predicate", "inputs"}:
        raise EvalError(
            f"submission for {trial_id!r} has a malformed procedure")
    if not isinstance(procedure["predicate"], str) \
            or not procedure["predicate"]:
        raise EvalError(
            f"submission for {trial_id!r} names no predicate")
    if not isinstance(procedure["inputs"], dict):
        raise EvalError(
            f"submission for {trial_id!r} has malformed procedure inputs")
    answer = submission["answer"]
    if answer is None:
        return submission
    if isinstance(answer, str) and not answer:
        raise EvalError(f"submission for {trial_id!r} has an empty answer")
    if not isinstance(answer, (str, int, float)):
        raise EvalError(
            f"submission for {trial_id!r} has no single stated answer")
    return submission


def _check_submissions(submissions: object) -> dict:
    if not isinstance(submissions, dict):
        raise EvalError("submissions are not a JSON object")
    return {trial_id: _check_submission(trial_id, submission)
            for trial_id, submission in submissions.items()}


def _no_dup_object(pairs: list[tuple[str, object]]) -> dict:
    for key, _ in pairs:
        if sum(1 for other, _ in pairs if other == key) > 1:
            raise EvalError(f"answers file repeats key {key!r}")
    return dict(pairs)


def load_answers(path: Path | str) -> dict[str, object]:
    """Load the model's structured submissions keyed by trial id.

    Repeated keys refuse during decoding, before any conversion — a
    decoded dictionary can no longer tell that a conflict existed.
    """
    try:
        parsed = json.loads(Path(path).read_text(encoding="utf-8"),
                            object_pairs_hook=_no_dup_object)
    except (OSError, ValueError) as exc:
        raise EvalError(f"answers file is unreadable: {exc}") from None
    return _check_submissions(parsed)


def _procedure_identity(procedure: dict) -> tuple[str, str]:
    return (procedure["predicate"], _canonical(procedure["inputs"]))


def _accepted_identities(record: dict) -> set[tuple[str, str]]:
    reference = record["reference"]["procedure"]
    accepted = {_procedure_identity(reference)}
    accepted.update(
        _procedure_identity(variant)
        for variant in record["reference"]["accepted"])
    return accepted


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


def score_trials(records: list[dict], submissions: dict) -> dict:
    """Score structured submissions against executed predicates. Pure.

    Unknown submission ids refuse. A reference or submitted accepted
    alternative that cannot execute or contradicts the key is
    ``fixture-rot`` — fixture debt, never model signal. Everything
    else is ``pass``, ``fail``, ``unanswered``, or ``unadjudicated``.
    The report pins the exact inputs it was computed from.
    """
    submissions = _check_submissions(submissions)
    known = {record["id"] for record in records}
    strange = sorted(set(submissions) - known)
    if strange:
        raise EvalError(
            f"submissions address unknown trials: {', '.join(strange)}")
    public = _public_entries(records)
    digest = package_digest(public)
    verdicts = []
    for record in records:
        trial_id = record["id"]
        reference = record["reference"]["procedure"]
        try:
            truth = evaluate(reference["predicate"],
                             **reference["inputs"])
            healthy = _fixture_holds(record["reference"]["expected"], truth)
        except Exception:
            healthy, truth = False, None
        if not healthy:
            verdicts.append({"id": trial_id, "verdict": "fixture-rot",
                             "procedure_accepted": False})
            continue
        submission = submissions.get(trial_id)
        if submission is None or submission["answer"] is None:
            verdicts.append({"id": trial_id, "verdict": "unanswered",
                             "procedure_accepted": False})
            continue
        accepted = _procedure_identity(
            submission["procedure"]) in _accepted_identities(record)
        if not accepted:
            verdicts.append({"id": trial_id, "verdict": "unadjudicated",
                             "procedure_accepted": False})
            continue
        procedure = submission["procedure"]
        if _procedure_identity(procedure) != _procedure_identity(reference):
            # Adjudication can rot too. Reuse the already executed reference
            # only for the same procedure; alternatives must prove their key.
            try:
                truth = evaluate(procedure["predicate"], **procedure["inputs"])
                healthy = _fixture_holds(record["reference"]["expected"], truth)
            except Exception:
                healthy = False
            if not healthy:
                verdicts.append({"id": trial_id, "verdict": "fixture-rot",
                                 "procedure_accepted": False})
                continue
        op, wanted = next(iter(record["reference"]["expected"].items()))
        verdict = "pass" if _model_matches(
            op, wanted, submission["answer"], truth) else "fail"
        verdicts.append({"id": trial_id, "verdict": verdict,
                         "procedure_accepted": True})
    counts = {verdict: sum(1 for row in verdicts if row["verdict"] == verdict)
              for verdict in VERDICTS}
    return {
        "package_format": PACKAGE_FORMAT,
        "package_digest": digest,
        "key_digest": key_digest(records),
        "input_digest": _digest({"package_digest": digest,
                                 "submissions": submissions}),
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
          f"digest {package['package_digest']}")
    return 0


def cmd_score(args: argparse.Namespace) -> int:
    records = load_trials(args.trials)
    report = score_trials(records, load_answers(args.answers))
    _write_json(Path(args.out), report)
    counts = report["counts"]
    print(f"score {counts['pass']}/{len(report['verdicts'])} "
          f"({counts['unanswered']} unanswered, "
          f"{counts['unadjudicated']} unadjudicated, "
          f"{counts['fixture-rot']} fixture-rot)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Offline question-to-procedure scoring for held-out "
                    "operator questions")
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="emit the model context package")
    prep.add_argument("--trials", default=str(DEFAULT_TRIALS))
    prep.add_argument("--out", required=True)
    prep.set_defaults(func=cmd_prepare)
    score = sub.add_parser("score", help="score submitted procedures "
                                        "and stated answers from evidence")
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

"""Verified Operator Questions: the fixture suite that measures understanding.

~20 trial records over the semantic contract: public task facts plus an
evaluator-side reference (procedure, answer key, adjudicated
equivalents). Examples prove the predicates answer; the held-out set is
eval only — scored here, never used as illustrations in docs, examples,
or other tests. A held-out question whose id leaks into any of those
places stops being held out, and `test_heldout_ids_stay_held_out` fails
the suite on exactly that.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from learning_os.semantics import PREDICATES, evaluate

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "verified_operator_questions"

EXPECTED_OPS = ("equals", "is_true", "is_false", "contains")

#: Every place a held-out id must never appear. This file itself is listed:
#: the eval below discovers held-out questions by split, never by name.
NO_LEAK_PATHS = (
    Path("tools/learning_os/semantics/predicates.py"),
    Path("tools/learning_os/semantics/__init__.py"),
    Path("system/SEMANTIC-CONTRACT.md"),
    Path("tests/test_semantic_contract.py"),
    Path(__file__).resolve().parent / "test_verified_operator_questions.py",
)


def _load_all() -> list[dict]:
    fixtures = []
    for path in sorted(FIXTURE_DIR.glob("voq-*.yaml")):
        with path.open(encoding="utf-8") as stream:
            fixtures.append(yaml.safe_load(stream))
    return fixtures


@pytest.fixture(scope="module")
def voqs() -> list[dict]:
    return _load_all()


def _check_shape(voq: dict) -> None:
    assert set(voq) == {
        "id", "split", "class", "question", "notes", "reference",
    }, f"unexpected keys in {voq.get('id')}"
    assert voq["split"] in {"example", "heldout"}
    assert voq["id"].startswith("voq-")
    reference = voq["reference"]
    assert set(reference) == {"procedure", "expected", "accepted"}
    procedure = reference["procedure"]
    assert set(procedure) == {"predicate", "inputs"}
    assert procedure["predicate"] in PREDICATES, (
        f"{voq['id']} names an unregistered predicate")
    assert isinstance(procedure["inputs"], dict)
    expected = reference["expected"]
    assert isinstance(expected, dict) and len(expected) == 1
    assert next(iter(expected)) in EXPECTED_OPS
    for variant in reference["accepted"]:
        assert set(variant) == {"predicate", "inputs"}
        assert variant["predicate"] in PREDICATES
        assert isinstance(variant["inputs"], dict)


def _apply(expected: dict, verdict: object, voq_id: str) -> None:
    op, wanted = next(iter(expected.items()))
    if op == "equals":
        assert verdict == wanted, voq_id
    elif op == "is_true":
        assert verdict is True, voq_id
    elif op == "is_false":
        assert verdict is False, voq_id
    elif op == "contains":
        assert wanted in verdict, voq_id


def test_the_split_is_fifteen_examples_and_five_held_out(voqs):
    for voq in voqs:
        _check_shape(voq)
    assert len(voqs) == 20
    assert len({voq["id"] for voq in voqs}) == 20
    examples = [voq for voq in voqs if voq["split"] == "example"]
    heldout = [voq for voq in voqs if voq["split"] == "heldout"]
    assert len(examples) == 15
    assert len(heldout) == 5
    assert len({voq["class"] for voq in heldout}) == 5


def test_examples_are_green(voqs):
    """Every example question evaluates to its expected property."""
    examples = [voq for voq in voqs if voq["split"] == "example"]
    assert len(examples) == 15
    for voq in examples:
        procedure = voq["reference"]["procedure"]
        verdict = evaluate(procedure["predicate"], **procedure["inputs"])
        _apply(voq["reference"]["expected"], verdict, voq["id"])


def test_heldout_eval_scores_five_of_five(voqs, capsys):
    """The held-out set runs as eval: scored and reported, never illustrated.

    Correctness of the fixtures themselves is still gated — a wrong expected
    value is fixture rot, not model signal. What stays ungated is any claim
    about a *model*; per-model scoring happens outside this suite.
    """
    heldout = [voq for voq in voqs if voq["split"] == "heldout"]
    assert len(heldout) == 5
    passed = 0
    for voq in heldout:
        procedure = voq["reference"]["procedure"]
        verdict = evaluate(procedure["predicate"], **procedure["inputs"])
        try:
            _apply(voq["reference"]["expected"], verdict, voq["id"])
        except AssertionError:
            print(f"HELDOUT FAIL {voq['id']}: {verdict!r}")
        else:
            passed += 1
            print(f"HELDOUT PASS {voq['id']}")
    print(f"HELDOUT SCORE {passed}/{len(heldout)}")
    assert passed == len(heldout)


def test_heldout_ids_stay_held_out(voqs):
    """A held-out id quoted anywhere illustrated stops being held out."""
    root = Path(__file__).resolve().parents[1]
    heldout_ids = [voq["id"] for voq in voqs if voq["split"] == "heldout"]
    example_text = "\n".join(
        Path(path).read_text(encoding="utf-8")
        for path in sorted(FIXTURE_DIR.glob("voq-*.yaml"))
        if yaml.safe_load(Path(path).read_text(encoding="utf-8"))["split"] == "example"
    )
    for voq_id in heldout_ids:
        assert voq_id not in example_text, f"{voq_id} leaks into an example"
        for relative in NO_LEAK_PATHS:
            text = (root / relative).read_text(encoding="utf-8")
            assert voq_id not in text, f"{voq_id} leaks into {relative}"


def test_recipe_output_for_every_class_contains_no_held_out_id(voqs):
    """The recipe surface serves examples only: no held-out id may appear
    in any class's recipe output, however the loader is asked."""
    import json

    from learning_os.semantics.recipes import recipe_classes, recipes_for

    heldout_ids = [voq["id"] for voq in voqs if voq["split"] == "heldout"]
    assert len(heldout_ids) == 5
    classes = recipe_classes()
    assert len(classes) == 6
    for class_name in classes:
        text = json.dumps(recipes_for(class_name), sort_keys=True)
        for voq_id in heldout_ids:
            assert voq_id not in text, f"{voq_id} leaks into recipe {class_name}"


def test_recipe_serves_worked_procedures_and_refuses_unknown_class():
    import pytest

    from learning_os.semantics.recipes import RecipeError, recipes_for

    rows = recipes_for("scope-authority")
    assert rows, "the scope-authority class must have an example recipe"
    for row in rows:
        assert set(row) == {"id", "question", "procedure", "notes"}
        assert set(row["procedure"]) == {"predicate", "inputs"}
        assert row["procedure"]["predicate"] in PREDICATES
    with pytest.raises(RecipeError, match="no example recipe"):
        recipes_for("class-that-does-not-exist")


def test_recipe_command_serves_examples_only(mini_repo):
    """`los semantic --recipe CLASS` prints worked example procedures and
    never a held-out id; an unknown class fails closed naming its options."""
    import json

    from repo_builders import run_los

    from learning_os.semantics.recipes import recipes_for

    proc = run_los(mini_repo, "semantic", "--recipe", "scope-authority")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload == {"class": "scope-authority", "recipes": recipes_for("scope-authority")}
    assert len(payload["recipes"]) >= 1
    missing = run_los(mini_repo, "semantic", "--recipe", "class-that-does-not-exist")
    assert missing.returncode == 2
    assert not missing.stdout
    assert "no example recipe" in missing.stderr

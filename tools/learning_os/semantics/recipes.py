"""Worked example procedures for recurring operator questions.

The verified-operator-question fixtures are a frozen benchmark: the held-out
split must stay invisible to every surface. The *example* split, however, is
public by construction — and it is the one artifact recording the right
procedure for a recurring question class. This module publishes exactly
those examples as recipes, keyed by class, emitted from the same fixture
files the suite reads so a recipe can never drift from its fixture and a
held-out id can never appear (the loader filters on ``split: example``).
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent.parent
FIXTURE_DIR = ROOT / "tests" / "fixtures" / "verified_operator_questions"


class RecipeError(ValueError):
    """No recipe can be served for this class."""


def _load_examples() -> list[dict]:
    """Every example-split fixture, or a refusal when none load."""
    try:
        paths = sorted(FIXTURE_DIR.glob("voq-*.yaml"))
    except OSError as exc:
        raise RecipeError(f"cannot read recipe fixtures: {exc}") from exc
    examples = []
    for path in paths:
        try:
            record = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise RecipeError(f"cannot read recipe fixture {path.name}: {exc}") from exc
        if isinstance(record, dict) and record.get("split") == "example":
            examples.append(record)
    return examples


def recipe_classes() -> tuple[str, ...]:
    """Every question class with at least one example recipe."""
    return tuple(sorted({str(item["class"]) for item in _load_examples()
                         if isinstance(item.get("class"), str) and item["class"]}))


def recipes_for(class_name: str) -> list[dict]:
    """Worked example procedures for one question class.

    Examples only, always: a class with no example returns an empty list
    rather than reaching for the held-out split. Raises RecipeError for a
    class with no recipes at all.
    """
    if not isinstance(class_name, str) or not class_name.strip():
        raise RecipeError("a recipe names a question class")
    rows = [{
        "id": item["id"],
        "question": item["question"],
        "procedure": item["reference"]["procedure"],
        "notes": item.get("notes", ""),
    } for item in _load_examples()
        if item.get("class") == class_name
        and isinstance(item.get("reference"), dict)
        and isinstance(item["reference"].get("procedure"), dict)]
    if not rows:
        known = ", ".join(recipe_classes())
        raise RecipeError(
            f"no example recipe for class {class_name!r}"
            + (f" (classes: {known})" if known else ""))
    return rows

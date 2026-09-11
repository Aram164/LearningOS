"""A prose locator that begins with a file path resolves to that file.

The authored house style is a path followed by prose — ``lecture-slides/
10_testing.pdf, PDF pp. 5-9,18-24`` — because the angle belongs next to the
locator. ``safe_material_locator`` asks the stricter question ("is this
locator *exactly* one path") and correctly answers None for those, which left
231 of 529 plan rows naming a locally held source with no local target: the
interface showed a link, or nothing, for a PDF sitting on disk.

Two derived steps close that, both after the strict check declines and neither
touching canonical data:

* ``leading_material_locator`` takes the path the locator *begins* with;
* ``single_file_material`` falls back to the source's own material when that
  material names one concrete file (a directory never stands in for a row —
  which file the row meant is exactly what the locator carries).

The property that must survive is the one `materials_resolution`'s own
docstring records: nothing is scanned or basename-matched, so a locator can
never be "verified" against a file nobody asked for. Ambiguity is refused, and
a derived path that does not exist is reported missing rather than replaced.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from learning_os.loader import load_repo
from learning_os.materials_resolution import (
    leading_material_locator,
    project_material_resource,
    safe_material_locator,
    single_file_material,
)

DIR_SOURCE = "material://source-demo-book/lecture-slides"
FILE_SOURCE = "material://source-demo-book/demo.pdf"


# ---- the permissive extractor ------------------------------------------------


@pytest.mark.parametrize("locator, expected", [
    ("lecture-slides/10_testing.pdf, PDF pp. 5-9,18-24,29-35",
     "lecture-slides/10_testing.pdf"),
    ("exercise-slides/Übung 08.pdf (48 pp.; dual-perceptron pages worked)",
     "exercise-slides/Übung 08.pdf"),
    ("blitzstein.pdf Ch 1 Probability and counting, from PDF p. 18",
     "blitzstein.pdf"),
    ("lecture-slides/VL 11-transformers.pdf slides 73–81", 
     "lecture-slides/VL 11-transformers.pdf"),
    ("02_basics.pdf", "02_basics.pdf"),
])
def test_leading_locator_takes_the_path_the_locator_begins_with(locator, expected):
    assert leading_material_locator(locator) == expected


@pytest.mark.parametrize("locator", [
    "lecture-slides/a.pdf through lecture-slides/b.pdf",   # two candidates
    "a.pdf + b.pdf",                                        # two candidates
    "/lecture-slides/10_testing.pdf",                       # absolute
    "../lecture-slides/10_testing.pdf",                     # escapes
    "lecture-slides\\10_testing.pdf",                       # backslash
    "lecture-slides/10_testing.pdf\nsecond line",           # newline
    "lecture-slides/10_testing.pdf/child",                  # not a file target
    "Full lecture scope",                                   # names no file
    "note-algo2-b-trees-viva-drill",                        # names a note
    "Lecture 13 pages 45–46",                               # prose only
    None,
    42,
])
def test_leading_locator_refuses_ambiguity_and_escapes(locator):
    assert leading_material_locator(locator) is None


def test_the_strict_locator_is_not_loosened():
    """The permissive step is additive; `safe_material_locator` is unchanged."""
    prose = "lecture-slides/10_testing.pdf, PDF pp. 5-9"
    assert safe_material_locator(prose) is None
    assert leading_material_locator(prose) == "lecture-slides/10_testing.pdf"
    exact = "lecture-slides/10_testing.pdf"
    assert safe_material_locator(exact) == exact


# ---- the single-file fallback ------------------------------------------------


def test_single_file_material_stands_in_only_for_a_file():
    assert single_file_material(FILE_SOURCE) == FILE_SOURCE
    assert single_file_material(DIR_SOURCE) is None
    assert single_file_material("material://source-demo-book") is None
    assert single_file_material("https://example.invalid/book.pdf") is None
    assert single_file_material(None) is None


# ---- end to end through the projection ---------------------------------------


def _repo_with(root: Path, material: str, *, files: tuple[str, ...] = ()):
    repo = load_repo(root)
    for relative in files:
        target = repo.materials_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("synthetic material", encoding="utf-8")
    repo.sources["source-demo-book"]["material"] = material
    return repo


def test_prose_locator_over_a_directory_source_opens_the_named_file(mini_repo: Path):
    repo = _repo_with(mini_repo, DIR_SOURCE,
                      files=("source-demo-book/lecture-slides/10_testing.pdf",))
    projected = project_material_resource(repo, {
        "source_id": "source-demo-book",
        "locator": "lecture-slides/10_testing.pdf, PDF pp. 5-9,18-24",
    })
    assert projected["material_uri"] == \
        "material://source-demo-book/lecture-slides/10_testing.pdf"
    assert projected["material_exists"] is True
    assert projected["material_path"].endswith("10_testing.pdf")


def test_prose_locator_over_a_single_file_source_opens_that_file(mini_repo: Path):
    repo = _repo_with(mini_repo, FILE_SOURCE, files=("source-demo-book/demo.pdf",))
    projected = project_material_resource(repo, {
        "source_id": "source-demo-book",
        "locator": "Ch 1 Probability and counting; Ch 2 Conditional probability",
    })
    assert projected["material_uri"] == FILE_SOURCE
    assert projected["material_exists"] is True


def test_a_directory_source_never_stands_in_for_a_fileless_locator(mini_repo: Path):
    """The row meant one of many files and did not say which. Refuse."""
    repo = _repo_with(mini_repo, DIR_SOURCE,
                      files=("source-demo-book/lecture-slides/10_testing.pdf",))
    projected = project_material_resource(repo, {
        "source_id": "source-demo-book",
        "locator": "Full lecture scope",
    })
    assert "material_uri" not in projected
    assert "material_path" not in projected


def test_a_derived_path_that_does_not_exist_publishes_nothing(mini_repo: Path):
    """A reading of prose that lands on no file offers no target.

    `Übung 02–11.pdf` is a range notation, not a filename. Two properties hold
    together here: the neighbour that *does* exist is never substituted (the
    anti-basename-match rule this module exists to enforce), and the wrong
    reading is not published as a broken target either — so the projection's
    invariant that every exposed `material_path` is a real file survives.
    """
    repo = _repo_with(mini_repo, DIR_SOURCE,
                      files=("source-demo-book/lecture-slides/10_testing.pdf",))
    projected = project_material_resource(repo, {
        "source_id": "source-demo-book",
        "locator": "exercise-slides/Übung 02–11.pdf, the whole range",
    })
    assert "material_uri" not in projected
    assert "material_path" not in projected


def test_an_authored_vault_path_still_surfaces_when_it_names_nothing(mini_repo: Path):
    """An assertion that names no file is a defect the interface must show.

    This is the asymmetry: a derivation stays silent when it cannot resolve,
    because it was only a reading. An authored `vault_path` is a claim, and a
    claim about a file that is not there has to be visible to be repaired.
    """
    repo = _repo_with(mini_repo, DIR_SOURCE,
                      files=("source-demo-book/lecture-slides/10_testing.pdf",))
    projected = project_material_resource(repo, {
        "source_id": "source-demo-book",
        "locator": "prose",
        "vault_path": "material://source-demo-book/lecture-slides/99_missing.pdf",
    })
    assert projected["material_uri"] == \
        "material://source-demo-book/lecture-slides/99_missing.pdf"
    assert projected["material_exists"] is False


def test_an_explicit_vault_path_still_wins(mini_repo: Path):
    """The 298 rows that already resolve are untouched by the fallbacks."""
    repo = _repo_with(mini_repo, DIR_SOURCE,
                      files=("source-demo-book/lecture-slides/10_testing.pdf",
                             "source-demo-book/demo.pdf"))
    projected = project_material_resource(repo, {
        "source_id": "source-demo-book",
        "locator": "Ch 1, prose that names no file",
        "vault_path": "material://source-demo-book/lecture-slides/10_testing.pdf",
    })
    assert projected["material_uri"] == \
        "material://source-demo-book/lecture-slides/10_testing.pdf"
    assert projected["material_exists"] is True


def test_a_non_material_vault_path_is_left_alone(mini_repo: Path):
    """A repository-relative vault_path (a notes folder) is not a material."""
    repo = _repo_with(mini_repo, FILE_SOURCE, files=("source-demo-book/demo.pdf",))
    projected = project_material_resource(repo, {
        "source_id": "source-demo-book",
        "locator": "prose",
        "vault_path": "knowledge/notes/mathematics/",
    })
    assert "material_uri" not in projected

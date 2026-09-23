"""Metadata-only discovery provenance on sources and link fields on candidates.

Data contract v39 (two-pass intake, step 3): a source shelved from a list or
page carries `discovery` instead of an evaluation, and prospective Master's
candidates carry link fields without a discovery object (option B).
"""

from __future__ import annotations

import pytest
import yaml

from learning_os.loader import load_repo
from learning_os.masters_planning import (
    MastersPlanningError,
    validate_master_catalog,
)
from learning_os.rules import validate


def codes(issues, severity=None):
    return [i.code for i in issues if severity is None or i.severity == severity]


def run(root):
    return validate(load_repo(root))


def _discovery(**changes):
    value = {
        "observed": "2026-09-23",
        "basis": [
            {"kind": "list-entry", "ref": "legacy/EXAMPLE-LIST.md#L10"},
            {"kind": "landing-page", "ref": "https://example.org/cs000/"},
        ],
        "origins": ["legacy/EXAMPLE-LIST.md#L10"],
        "possible_use": "Possibly a lecture spine for intro supervised learning.",
        "child_titles": {"lec-01": "Lecture 1 — Introduction"},
    }
    value.update(changes)
    return value


def _add_source(mini_repo, source):
    path = mini_repo / "sources" / "sources.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["sources"].append(source)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _catalog(candidates):
    return {
        "schema_version": 1,
        "id": "master-planning-catalog",
        "type": "master-planning-catalog",
        "revision": 0,
        "updated_at": "2026-09-23T10:00:00Z",
        "candidate_modules": [],
        "candidate_sources": candidates,
        "comparison_ids": [],
    }


def _candidate(cid="candidate-source-demo", **changes):
    value = {
        "id": cid,
        "title": "Demo Course",
        "planning_state": "longlist",
        "privacy_class": "academic-only",
        "provenance": ["workspace-degree-planning/inputs/MASTERS-ML-RESOURCES.md#L40"],
        "fact_state": {"status": "unverified", "as_of": None, "evidence": []},
    }
    value.update(changes)
    return value


# ------------------------------------------------------------------- sources
def test_metadata_only_source_validates_without_an_evaluation(mini_repo):
    _add_source(mini_repo, {
        "id": "source-example-course", "title": "Example Course", "type": "course",
        "url": "https://example.org/cs000/",
        "identifiers": {"lec-01": "https://example.org/cs000/lec01"},
        "thematic_group_ids": [],
        "discovery": _discovery(),
    })
    assert codes(run(mini_repo), "E") == []


def test_discovery_requires_observed_basis_and_possible_use(mini_repo):
    _add_source(mini_repo, {
        "id": "source-example-course", "title": "Example Course", "type": "course",
        "discovery": {"observed": "2026-09-23", "basis": []},
    })
    assert "SCHEMA" in codes(run(mini_repo), "E")


def test_discovery_basis_kind_is_closed(mini_repo):
    _add_source(mini_repo, {
        "id": "source-example-course", "title": "Example Course", "type": "course",
        "discovery": _discovery(basis=[{"kind": "read-the-book", "ref": "x#L1"}]),
    })
    assert "SCHEMA" in codes(run(mini_repo), "E")


def test_discovery_ref_must_be_a_url_or_a_path_line(mini_repo):
    _add_source(mini_repo, {
        "id": "source-example-course", "title": "Example Course", "type": "course",
        "discovery": _discovery(basis=[{"kind": "list-entry", "ref": "some prose"}]),
    })
    assert "SCHEMA" in codes(run(mini_repo), "E")


def test_possible_use_is_bounded_at_200_characters(mini_repo):
    _add_source(mini_repo, {
        "id": "source-example-course", "title": "Example Course", "type": "course",
        "discovery": _discovery(possible_use="x" * 201),
    })
    assert "SCHEMA" in codes(run(mini_repo), "E")


def test_discovery_holds_no_pedagogical_fields(mini_repo):
    _add_source(mini_repo, {
        "id": "source-example-course", "title": "Example Course", "type": "course",
        "discovery": _discovery(concepts=["concept-expected-value"]),
    })
    assert "SCHEMA" in codes(run(mini_repo), "E")


def test_child_title_without_an_identifier_label_is_an_error(mini_repo):
    _add_source(mini_repo, {
        "id": "source-example-course", "title": "Example Course", "type": "course",
        "url": "https://example.org/cs000/",
        "discovery": _discovery(),
    })
    assert "REF-CHILD-TITLE" in codes(run(mini_repo), "E")


def test_identifier_without_a_child_title_is_fine(mini_repo):
    _add_source(mini_repo, {
        "id": "source-example-course", "title": "Example Course", "type": "course",
        "url": "https://example.org/cs000/",
        "identifiers": {"playlist": "https://example.org/cs000/videos"},
        "discovery": _discovery(child_titles={}),
    })
    assert "REF-CHILD-TITLE" not in codes(run(mini_repo), "E")


# ----------------------------------------------------------------- catalogue
def test_candidate_link_fields_are_accepted(mini_repo):
    value = _catalog([_candidate(
        url="https://example.org/cs000/",
        identifiers={"lec-01": "https://example.org/cs000/lec01"},
        child_titles={"lec-01": "Lecture 1 — Introduction"},
        possible_use="Possibly the attention block of the NLP module.",
        type="course",
    )])
    assert validate_master_catalog(mini_repo, value) == value


def test_candidate_child_title_needs_its_label(mini_repo):
    value = _catalog([_candidate(child_titles={"lec-01": "Lecture 1"})])
    with pytest.raises(MastersPlanningError, match="no matching identifiers label"):
        validate_master_catalog(mini_repo, value)


@pytest.mark.parametrize("url", [
    "https://drive.google.com/file/d/abc123/view",
    "https://www.dropbox.com/s/abc123/notes.pdf",
    "https://onedrive.live.com/?cid=abc123",
    "mailto:reader@example.com",
    "file:///home/aram/notes.pdf",
    "http://localhost:8000/course",
    "http://127.0.0.1/course",
    "https://10.0.0.8/course",
])
def test_candidate_refuses_personal_links(mini_repo, url):
    value = _catalog([_candidate(url=url)])
    with pytest.raises(MastersPlanningError, match="not catalogue material|not a public web link"):
        validate_master_catalog(mini_repo, value)
    via_identifier = _catalog([_candidate(identifiers={"mirror": url})])
    with pytest.raises(MastersPlanningError, match="not catalogue material|not a public web link"):
        validate_master_catalog(mini_repo, via_identifier)

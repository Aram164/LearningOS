"""The bindingness index holds against the live corpus, and fails when it should.

Two halves, deliberately. The synthetic half proves each check fires against a
corpus built to break it — a check nobody has seen fail is a check nobody knows
works. The live half proves the real index is exhaustive today, which is the
claim CRITIQUE-POINTS §3 said nothing was making.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from learning_os.contracts import normative_corpus as nc

ROOT = Path(__file__).resolve().parents[1]

_SCHEMA = json.loads((ROOT / nc.SCHEMA_RELATIVE).read_text(encoding="utf-8"))


def _corpus(tmp_path: Path, documents: list[dict], *, entrypoint: str | None = None,
            files: dict[str, str] | None = None) -> Path:
    """A throwaway repository whose corpus is exactly ``documents``."""
    root = tmp_path
    (root / "system" / "adr").mkdir(parents=True, exist_ok=True)
    (root / "system" / "contracts").mkdir(parents=True, exist_ok=True)
    (root / nc.SCHEMA_RELATIVE).write_text(json.dumps(_SCHEMA), encoding="utf-8")

    written = files if files is not None else {
        doc["path"]: f"# {Path(doc['path']).stem}\n" for doc in documents
    }
    for relative, text in written.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    (root / nc.CORPUS_RELATIVE).write_text(
        yaml.safe_dump({
            "corpus_version": 1,
            "entrypoint": entrypoint or documents[0]["path"],
            "documents": documents,
        }, sort_keys=False),
        encoding="utf-8",
    )
    return root


def _entry(path: str, **overrides) -> dict:
    entry = {
        "path": path,
        "class": "contract",
        "status": "current",
        "authority": "binding",
        "owner": "test",
        "summary": "a document",
    }
    entry.update(overrides)
    return entry


def _codes(issues) -> set[str]:
    return {issue.code for issue in issues}


# ---- the synthetic half ----------------------------------------------------

def test_a_minimal_corpus_is_clean(tmp_path):
    root = _corpus(tmp_path, [_entry("system/OPERATOR.md")])
    assert nc.check(root) == []


def test_an_unindexed_document_is_an_error(tmp_path):
    root = _corpus(tmp_path, [_entry("system/OPERATOR.md")])
    (root / "system" / "NEW-RULES.md").write_text("# rules\n", encoding="utf-8")
    issues = nc.check(root)
    assert "MISSING" in _codes(issues)
    assert any("system/NEW-RULES.md" == issue.path for issue in issues)


def test_an_unindexed_adr_is_an_error(tmp_path):
    root = _corpus(tmp_path, [_entry("system/OPERATOR.md")])
    (root / "system" / "adr" / "ADR-099-x-2026-09-01.md").write_text("# x\n", encoding="utf-8")
    assert "MISSING" in _codes(nc.check(root))


def test_an_index_entry_with_no_file_is_an_error(tmp_path):
    root = _corpus(
        tmp_path,
        [_entry("system/OPERATOR.md"), _entry("system/GHOST.md")],
        files={"system/OPERATOR.md": "# op\n"},
    )
    assert "ORPHAN" in _codes(nc.check(root))


def test_a_duplicate_path_is_an_error(tmp_path):
    root = _corpus(tmp_path, [_entry("system/OPERATOR.md"), _entry("system/OPERATOR.md")])
    assert "DUPLICATE" in _codes(nc.check(root))


def test_an_edge_to_an_unindexed_path_is_an_error(tmp_path):
    root = _corpus(tmp_path, [
        _entry("system/OPERATOR.md", supersedes=["system/adr/ADR-001-gone-2026-01-01.md"]),
    ])
    assert "EDGE" in _codes(nc.check(root))


def test_a_supersession_cycle_is_an_error(tmp_path):
    root = _corpus(tmp_path, [
        _entry("system/OPERATOR.md"),
        _entry("system/A.md", supersedes=["system/B.md"],
               status="superseded", authority="historical"),
        _entry("system/B.md", supersedes=["system/A.md"],
               status="superseded", authority="historical"),
    ], files={
        "system/OPERATOR.md": "# op\n",
        "system/A.md": "# A — retired by B\n",
        "system/B.md": "# B — retired by A\n",
    })
    assert "CYCLE" in _codes(nc.check(root))


def test_a_retired_document_still_marked_current_is_an_error(tmp_path):
    root = _corpus(tmp_path, [
        _entry("system/OPERATOR.md", supersedes=["system/OLD.md"]),
        _entry("system/OLD.md", status="current", authority="binding"),
    ], files={
        "system/OPERATOR.md": "# op\n",
        "system/OLD.md": "# old — superseded by OPERATOR\n",
    })
    assert "STATUS" in _codes(nc.check(root))


def test_superseded_with_no_successor_is_an_error(tmp_path):
    root = _corpus(tmp_path, [
        _entry("system/OPERATOR.md"),
        _entry("system/OLD.md", status="superseded", authority="historical"),
    ])
    assert "STATUS" in _codes(nc.check(root))


def test_a_retired_document_cannot_be_binding(tmp_path):
    root = _corpus(tmp_path, [
        _entry("system/OPERATOR.md"),
        _entry("system/FROZEN.md", status="frozen", authority="binding"),
    ])
    assert "AUTHORITY" in _codes(nc.check(root))


def test_a_retired_document_must_say_so_in_its_own_text(tmp_path):
    """The audit CRITIQUE-POINTS §3 said the review owed, made executable."""
    root = _corpus(tmp_path, [
        _entry("system/adr/ADR-013-new-2026-08-26.md",
               supersedes=["system/adr/ADR-010-old-2026-08-14.md"]),
        _entry("system/adr/ADR-010-old-2026-08-14.md",
               status="superseded", authority="historical"),
        _entry("system/OPERATOR.md"),
    ], entrypoint="system/OPERATOR.md", files={
        "system/adr/ADR-013-new-2026-08-26.md": "# ADR-013\n\nSupersedes ADR-010.\n",
        "system/adr/ADR-010-old-2026-08-14.md": "# ADR-010\n\nNo notice here.\n",
        "system/OPERATOR.md": "# op\n",
    })
    issues = nc.check(root)
    assert "NO-NOTICE" in _codes(issues)
    assert any(issue.path.endswith("ADR-010-old-2026-08-14.md") for issue in issues)


def test_a_notice_naming_the_successor_clears_it(tmp_path):
    root = _corpus(tmp_path, [
        _entry("system/adr/ADR-013-new-2026-08-26.md",
               supersedes=["system/adr/ADR-010-old-2026-08-14.md"]),
        _entry("system/adr/ADR-010-old-2026-08-14.md",
               status="superseded", authority="historical"),
        _entry("system/OPERATOR.md"),
    ], entrypoint="system/OPERATOR.md", files={
        "system/adr/ADR-013-new-2026-08-26.md": "# ADR-013\n",
        "system/adr/ADR-010-old-2026-08-14.md":
            "# ADR-010\n\n**Status:** superseded by ADR-013 (2026-08-26)\n",
        "system/OPERATOR.md": "# op\n",
    })
    assert nc.check(root) == []


def test_an_amendment_also_requires_a_notice(tmp_path):
    root = _corpus(tmp_path, [
        _entry("system/adr/ADR-013-new-2026-08-26.md",
               amends=["system/adr/ADR-003-part-2026-08-03.md"]),
        _entry("system/adr/ADR-003-part-2026-08-03.md"),
        _entry("system/OPERATOR.md"),
    ], entrypoint="system/OPERATOR.md", files={
        "system/adr/ADR-013-new-2026-08-26.md": "# ADR-013\n",
        "system/adr/ADR-003-part-2026-08-03.md": "# ADR-003\n\nNothing about it.\n",
        "system/OPERATOR.md": "# op\n",
    })
    assert "NO-NOTICE" in _codes(nc.check(root))


def test_an_amended_document_may_stay_current_and_binding(tmp_path):
    """Partial retirement is not retirement — ADR-012 is the live example."""
    root = _corpus(tmp_path, [
        _entry("system/adr/ADR-013-new-2026-08-26.md",
               amends=["system/adr/ADR-012-part-2026-08-19.md"]),
        _entry("system/adr/ADR-012-part-2026-08-19.md"),
        _entry("system/OPERATOR.md"),
    ], entrypoint="system/OPERATOR.md", files={
        "system/adr/ADR-013-new-2026-08-26.md": "# ADR-013\n",
        "system/adr/ADR-012-part-2026-08-19.md":
            "# ADR-012\n\n> **Amended by ADR-013 (2026-08-26):** parts retired.\n",
        "system/OPERATOR.md": "# op\n",
    })
    assert nc.check(root) == []


def test_an_unindexed_entrypoint_is_an_error(tmp_path):
    root = _corpus(tmp_path, [_entry("system/OPERATOR.md")], entrypoint="system/NOPE.md")
    assert "ENTRYPOINT" in _codes(nc.check(root))


def test_a_non_binding_entrypoint_is_an_error(tmp_path):
    root = _corpus(tmp_path, [
        _entry("system/OPERATOR.md", authority="informative", **{"class": "rationale"}),
    ])
    assert "ENTRYPOINT" in _codes(nc.check(root))


def test_a_missing_index_is_an_error_not_a_pass(tmp_path):
    """Prose present, index absent: the one case that must not read as clean."""
    (tmp_path / "system" / "contracts").mkdir(parents=True)
    (tmp_path / "system" / "OPERATOR.md").write_text("# op\n", encoding="utf-8")
    issues = nc.check(tmp_path)
    assert _codes(issues) == {"UNREADABLE"}


def test_a_repository_with_no_prose_has_no_corpus_to_check(tmp_path):
    """A synthetic fixture is not the system; the real repository is pinned
    non-empty by test_every_system_document_on_disk_is_classified."""
    (tmp_path / "system" / "contracts").mkdir(parents=True)
    assert nc.check(tmp_path) == []


def test_an_index_violating_its_schema_is_an_error(tmp_path):
    root = _corpus(tmp_path, [_entry("system/OPERATOR.md", status="retired-ish")])
    assert "UNREADABLE" in _codes(nc.check(root))


# ---- the live half ---------------------------------------------------------

@pytest.mark.full_repo
def test_the_live_corpus_is_fully_indexed_and_coherent():
    issues = nc.check(ROOT)
    assert issues == [], "\n".join(str(issue) for issue in issues)


@pytest.mark.full_repo
def test_every_system_document_on_disk_is_classified():
    indexed = {doc.path for doc in nc.load(ROOT).documents}
    assert set(nc.corpus_files(ROOT)) == indexed


@pytest.mark.full_repo
def test_the_declared_entrypoint_is_the_operator_contract():
    corpus = nc.load(ROOT)
    assert corpus.entrypoint == "system/OPERATOR.md"
    entry = corpus.by_path()[corpus.entrypoint]
    assert (entry.status, entry.authority) == ("current", "binding")


@pytest.mark.full_repo
def test_reverse_edges_are_derived_and_not_stored():
    """ARCHITECTURE's rule for canonical notes, applied to the corpus itself."""
    raw = yaml.safe_load((ROOT / nc.CORPUS_RELATIVE).read_text(encoding="utf-8"))
    for entry in raw["documents"]:
        assert "superseded_by" not in entry
        assert "amended_by" not in entry

    corpus = nc.load(ROOT)
    adr_013 = "system/adr/ADR-013-job-learning-collapse-2026-08-26.md"
    adr_010 = "system/adr/ADR-010-job-surface-2026-08-14.md"
    assert corpus.superseded_by[adr_010] == (adr_013,)
    assert corpus.by_path()[adr_010].status == "superseded"


@pytest.mark.full_repo
def test_no_frozen_or_superseded_document_claims_to_bind():
    for doc in nc.load(ROOT).documents:
        if doc.status in nc.RETIRED_STATUSES:
            assert doc.authority != "binding", doc.path

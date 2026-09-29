"""The plain-text materials catalogue renders every local source exactly once.

Regression cover for the 2026-09-29 shelving complaint: the builder counted
96 local source nodes but rendered none, because current ADR-007 subject
folders (``mathematics/``, …) never matched the legacy display keys
(``Math``, …) the README loop iterates. These tests are hermetic: they
exercise the pure classify/render functions and synthetic collection files,
never the live materials tree.
"""

from __future__ import annotations

import yaml
from materials_index import registry
from materials_index.config import SOURCES_DOMAIN_ORDER
from materials_index.registry import domain_for_online, load_collection_domains
from materials_index.reports import build_readme
from materials_index.tree import classify_source_node


def _node(rel: str, title: str = "Grinstead and Snell"):
    return {
        "rel": rel, "name": rel.rsplit("/", 1)[-1], "title": title,
        "stype": "book", "url": "", "archived": False,
        "nfiles": 1, "nsupport": 0,
    }


def _readme(lib=None, onl=None, mis=None, nlocal=1, roots=None):
    return build_readme({}, lib or {}, onl or {}, mis or {}, roots or {},
                        nlocal, 0, 0, 1, 0, 1024)


def _root(name, files=(), dirs=()):
    return {"name": name, "rel": name, "title": None, "ctx": None,
            "source_id": None, "archived": False,
            "files": [{"name": f, "rel": f"{name}/{f}",
                       "ext": f.rsplit(".", 1)[-1].lower(), "size": 10,
                       "support": False, "archived": False} for f in files],
            "dirs": list(dirs), "nfiles": len(files), "nsupport": 0, "bytes": 0}


# ------------------------------------------------------- domain coherence
def test_current_taxonomy_folders_classify_into_rendered_domains():
    current = ["mathematics", "optimization", "machine-learning",
               "ml-systems", "data-systems", "algorithms", "software",
               "method-admin"]
    legacy = ["ML", "Math", "CS-Theory", "Programming", "Degree",
              "Foundations"]
    for top in current:
        dom, mod = classify_source_node({"rel": f"{top}/subject/item"})
        assert mod is None
        assert dom in SOURCES_DOMAIN_ORDER, f"{top} -> {dom} is never rendered"
    for top in legacy:
        # Legacy module tops keep their module-coursework grouping (mod set);
        # every legacy top still maps to a rendered display domain.
        dom, _ = classify_source_node({"rel": f"{top}/subject/item"})
        assert dom in SOURCES_DOMAIN_ORDER, f"{top} -> {dom} is never rendered"


def test_legacy_books_subfolders_still_rehome():
    assert classify_source_node({"rel": "Books/analysis/item"})[0] == "Math"
    assert classify_source_node({"rel": "Books/stats/item"})[0] == "Math"
    assert classify_source_node({"rel": "Books/ml/item"})[0] == "ML"
    assert classify_source_node({"rel": "Books/algorithms/item"})[0] == "CS-Theory"


def test_mathematics_node_renders_once_under_mathematics():
    dom, _ = classify_source_node(
        {"rel": "mathematics/probability-statistics/grinstead-snell"})
    assert dom == "Math"
    text = _readme(lib={dom: [_node("mathematics/probability-statistics/"
                                    "grinstead-snell")]})
    assert "\n## Mathematics" in text
    assert text.count("Grinstead and Snell") == 1


def test_unknown_top_renders_under_own_heading_rather_than_vanishing():
    text = _readme(lib={"_unsorted": [_node("_unsorted/stray")]})
    assert "\n## _unsorted" in text
    assert text.count("Grinstead and Snell") == 1


def test_loose_files_render_under_the_new_subject_headings():
    from materials_index.tree import group_roots_by_display
    roots = [_root("mathematics", files=["stray.pdf"]),
             _root("ML", files=["legacy-stray.pdf"])]
    grouped = group_roots_by_display(roots)
    assert set(grouped) == {"Math", "ML"}
    text = _readme(nlocal=0, roots=grouped)
    math = text.split("\n## Mathematics")[1].split("\n## ")[0]
    assert "Plus 1 loose/unregistered file(s)" in math
    assert "\n## Machine Learning" in text


def test_readme_has_no_retired_surface_references():
    text = _readme(lib={"Math": [_node("mathematics/item")]})
    assert "INDEX.html" not in text
    assert "Files view" not in text
    assert "FILES.txt" in text


# ------------------------------------------------- online grouping
def test_exam_collection_groups_map_to_subject_domains(tmp_path, monkeypatch):
    coll = tmp_path / "collections"
    coll.mkdir()
    (coll / "exam-practice-banks.yaml").write_text(
        yaml.safe_dump({"entries": [
            {"source": "source-sad-bank", "group": "sad"},
            {"source": "source-aml-bank", "group": "aml"},
            {"source": "source-algo-bank", "group": "algo2"},
            {"source": "source-analysis-bank", "group": "analysis"},
            {"source": "source-amls-bank", "group": "amls"},
        ]}), encoding="utf-8")
    monkeypatch.setattr(registry, "SOURCES", tmp_path)
    domains = load_collection_domains()
    assert domains["source-sad-bank"] == "Math"
    assert domains["source-analysis-bank"] == "Math"
    assert domains["source-aml-bank"] == "ML"
    assert domains["source-amls-bank"] == "ML"
    assert domains["source-algo-bank"] == "CS-Theory"
    for dom in domains.values():
        assert dom in SOURCES_DOMAIN_ORDER
    assert domain_for_online("source-sad-bank", domains) == "Math"
    assert domain_for_online("source-unlisted", domains) == "Online"

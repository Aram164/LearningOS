"""Acceptance scenario tests (ACCEPTANCE-TESTS.md §L) that are automatable."""

from __future__ import annotations

import pytest
import yaml

from learning_os.genout import generate_all
from learning_os.loader import load_repo
from learning_os.rules import validate


def test_scenario_7_exam_attempt_lifecycle(mini_repo):
    """registered -> withdrawn -> registered (2. Termin): representable, renders,
    and the dates appear canonically nowhere else."""
    f = mini_repo / "records" / "modules.yaml"
    data = yaml.safe_load(f.read_text())
    data["modules"][0]["attempts"] = [
        {"termin": 1, "date": "2026-07-22", "result": "withdrawn",
         "notes": "Ruecktritt via AGNES"},
        {"termin": 2, "date": "2026-09-30", "result": "registered"},
    ]
    f.write_text(yaml.safe_dump(data))
    repo = load_repo(mini_repo)
    issues = validate(repo)
    assert [i for i in issues if i.severity == "E"] == []
    outputs = generate_all(repo, generated_at="T1")
    view = outputs["module-view.md"]
    assert "withdrawn" in view and "registered" in view
    assert "2026-09-30" in outputs["coordination-view.md"]  # exam spine merged
    # dates appear canonically nowhere else
    for tree in ("knowledge", "work", "sources"):
        for path in (mini_repo / tree).rglob("*"):
            if path.is_file():
                text = path.read_text(encoding="utf-8", errors="replace")
                assert "2026-09-30" not in text, path


@pytest.mark.full_repo
def test_scenario_7_on_real_repo(repo_root):
    """The real modules.yaml exercises withdrawal + second sitting + Kombimodul."""
    repo = load_repo(repo_root)
    assert repo.modules, "modules.yaml is empty"
    has_withdrawal = any(
        any(a.get("result") == "withdrawn" for a in m.get("attempts", []) or [])
        for m in repo.modules.values())
    assert has_withdrawal, "no module with a withdrawal (Ruecktritt) recorded"
    has_kombimodul = any(m.get("components") for m in repo.modules.values())
    assert has_kombimodul, "no Kombimodul (components list) recorded"
    # exam dates appear canonically only in the owning module.yaml
    attempt_dates = {str(a["date"]) for m in repo.modules.values()
                     for a in m.get("attempts", []) or [] if a.get("date")}
    for tree in ("knowledge", "work", "sources"):
        base = repo_root / tree
        for path in base.rglob("*"):
            if path.is_file() and path.suffix in (".md", ".yaml"):
                text = path.read_text(encoding="utf-8", errors="replace")
                for d in attempt_dates:
                    assert d not in text, f"exam date {d} duplicated in {path}"


def _owned_admin_dates(repo_root):
    """Every administrative date the partitioned module records own.

    The older check above sees `attempts` only, so sitting dates and Anmeldung
    windows — the facts most likely to be restated in a plan — were never
    covered.
    """
    import yaml
    iso = set()
    for path in (repo_root / "curriculum" / "modules").glob("*/module.yaml"):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        exam = data.get("examination") or {}
        for sitting in exam.get("sittings") or []:
            for key in ("date", "end_date"):
                if sitting.get(key):
                    iso.add(str(sitting[key]))
        for window in exam.get("registration_windows") or []:
            for key in ("opens", "closes"):
                if window.get(key):
                    iso.add(str(window[key]))
        for attempt in data.get("attempts") or []:
            if attempt.get("date"):
                iso.add(str(attempt["date"]))
    forms = {}
    for value in iso:
        year, month, day = value.split("-")
        # Aram writes German dates; an ISO-only scan misses every one of them.
        forms[value] = {value, f"{day}.{month}.{year}", f"{day}.{month}."}
    return forms


@pytest.mark.full_repo
def test_admin_dates_are_not_restated_in_live_operational_prose(repo_root):
    """Hard rule #2 applies to prose that *directs current work*.

    Deliberately scoped. Two trees legitimately contain these dates and are NOT
    scanned:

    * `work/active/*/inputs/` — preserved pre-migration plans. CLAUDE.md §5
      forbids rewriting migration content; a preserved original that said
      "Klausur Mo 27.07" is evidence of what was planned, not a competing
      owner.
    * `knowledge/notes/` — durable notes. Hard rule #3 forbids rewriting a note
      body, and a note recording *"slide 39 said the exam is probably 27.7.26,
      later confirmed"* is provenance, not a restatement.

    What IS scanned is everything that tells you what to do now: coordination,
    workspace CONTEXT files, and workspace outputs. Those must defer to the
    owning module record, because when a date moves they are what goes stale.
    """
    forms = _owned_admin_dates(repo_root)
    assert forms, "no owned admin dates found — the collector is broken"

    targets = [repo_root / "work" / "COORDINATION.md"]
    for workspace in (repo_root / "work" / "active").glob("*"):
        if not workspace.is_dir():
            continue
        targets.append(workspace / "CONTEXT.md")
        for path in (workspace / "outputs").rglob("*"):
            if path.is_file() and path.suffix in (".md", ".yaml"):
                targets.append(path)

    offences = []
    for path in targets:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for iso, variants in forms.items():
            for form in sorted(variants):
                if form in text:
                    line = text[:text.index(form)].count("\n") + 1
                    offences.append(
                        f"{path.relative_to(repo_root)}:{line} restates {iso} "
                        f"as '{form}'")
    assert not offences, (
        "administrative dates restated in live operational prose — they belong "
        "only in the owning curriculum/modules/<id>/module.yaml:\n  "
        + "\n  ".join(sorted(offences)))


def test_scenario_4_file_move_keeps_id(mini_repo):
    """Moving a note to another bucket keeps its ID and resolves after regeneration."""
    old = mini_repo / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    new_dir = mini_repo / "knowledge" / "notes" / "cross-domain"
    new_dir.mkdir()
    new = new_dir / "note-demo.md"
    old.rename(new)
    repo = load_repo(mini_repo)
    assert "note-demo" in repo.notes
    assert [i for i in validate(repo) if i.severity == "E"] == []
    manifest_path = generate_all(repo, generated_at="T1")["manifest.json"]
    assert "cross-domain/note-demo.md" in manifest_path


@pytest.mark.full_repo
def test_scenario_2_contextual_judgment_no_scalar_rating(repo_root):
    """Source evaluations are contextual; no universal scalar rating field exists."""
    repo = load_repo(repo_root)
    for source in repo.sources.values():
        assert "rating" not in source and "score" not in source
        for ev in source.get("evaluations", []) or []:
            assert "rating" not in ev and "score" not in ev


@pytest.mark.full_repo
def test_crosswalk_judgments_not_only_in_notes(repo_root):
    """Scenario 8 spot-check: crosswalk notes exist AND source records carry
    evaluations — the judgments do not live only in the narrative note."""
    repo = load_repo(repo_root)
    crosswalk_notes = [n for n in repo.notes.values() if n.meta.get("role") == "crosswalk"]
    if not crosswalk_notes:
        return  # nothing to check yet
    n_evals = sum(len(s.get("evaluations", []) or []) for s in repo.sources.values())
    assert n_evals > 0, "crosswalk notes present but no source evaluations recorded"
    for note in crosswalk_notes:
        for sid in note.meta.get("sources", []) or []:
            src = repo.sources.get(sid)
            assert src is not None, f"{note.id} cites unknown source {sid}"

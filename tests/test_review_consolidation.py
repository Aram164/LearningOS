"""Register completeness: every finding has owner/callers/tests/disposition."""
from __future__ import annotations

import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def test_register_complete():
    data = yaml.safe_load((ROOT / "system/contracts/review-consolidation.yaml").read_text())
    schema = yaml.safe_load((ROOT / "system/contracts/review-consolidation.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(data)
    ids = [f["id"] for f in data["findings"]]
    assert len(ids) == len(set(ids)) == 42
    assert set(ids) == set((
        "G30 G31 G32 G33 G34 G35 G36 O37 O38 O39 O40 O41 O42 O43 O44 O45 O46 O47 "
        "I49 R50 R51 R52 R53 R54 R55 R56 R57 R58 R59 R60 "
        "E01 E02 E03 E04 E05 E06 E07 E08 E09 E10 E11 E12"
    ).split())
    for f in data["findings"]:
        # Owner/caller paths describe recorded_revision, not the current tree.
        # Evidence itself must remain available without an external workbench.
        for evidence in f["measured_evidence"]:
            if evidence.startswith("https://"):
                assert re.fullmatch(r"https://github\.com/Aram164/LearningOS/actions/runs/[0-9]+", evidence), f["id"]
            else:
                path = (ROOT / evidence).resolve()
                assert path.is_relative_to(ROOT) and path.is_file(), (f["id"], evidence)
    # Distinct inherited defects must link their actual owning suites rather
    # than an unrelated runner test whose existence alone would pass.
    by_id = {f["id"]: f for f in data["findings"]}
    assert by_id["G31"]["regression_tests"] == "tests/test_claim_status_audits.py"
    assert by_id["O41"]["regression_tests"] == "tests/test_note_evidence.py"
    assert "../obsidian-ui/src/main.ts" in by_id["R51"]["caller_paths"]


def test_completed_register_is_historical():
    corpus = yaml.safe_load((ROOT / "system/contracts/normative-corpus.yaml").read_text())
    page = next(row for row in corpus["documents"] if row["path"] == "system/developer/review-consolidation.md")
    assert (page["status"], page["authority"]) == ("frozen", "historical")

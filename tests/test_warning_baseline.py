"""The warning policy is executable, and it cannot be gamed by an equal total.

The gate this replaces was prose: "0 errors, 0 warnings" in one document,
"warnings never block" in another, 535 warnings on disk. These tests pin the
policy that resolved the disagreement — zero errors, warnings visible, no NEW
signature — and in particular pin the one property a count does not have.
"""

from __future__ import annotations

import importlib.util
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "warning_baseline", ROOT / "tools" / "warning_baseline.py")
wb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wb)

_SCHEMA = json.loads(
    (ROOT / "system" / "contracts" / "validation-warning-baseline.schema.json")
    .read_text(encoding="utf-8"))


def _write(root: Path, signatures: dict[tuple[str, str], int]) -> None:
    wb.write_baseline(root, Counter(signatures), "test fixture")


# ---- the delta -------------------------------------------------------------

def test_an_unchanged_set_has_no_delta():
    same = Counter({("LOCATOR-VAGUE", "a.yaml"): 3})
    assert wb.delta(same, same) == ([], [])


def test_a_new_signature_is_a_regression():
    before = Counter({("LOCATOR-VAGUE", "a.yaml"): 3})
    after = Counter({("LOCATOR-VAGUE", "a.yaml"): 3, ("ROUTE-ANGLE-DETAIL-MISSING", "b.yaml"): 1})
    regressions, repairs = wb.delta(before, after)
    assert len(regressions) == 1 and "ROUTE-ANGLE-DETAIL-MISSING" in regressions[0]
    assert repairs == []


def test_a_grown_signature_is_a_regression():
    before = Counter({("LOCATOR-VAGUE", "a.yaml"): 3})
    after = Counter({("LOCATOR-VAGUE", "a.yaml"): 4})
    regressions, _ = wb.delta(before, after)
    assert len(regressions) == 1 and "3 → 4" in regressions[0]


def test_a_shrunk_signature_is_a_repair_not_a_failure():
    before = Counter({("LOCATOR-VAGUE", "a.yaml"): 3})
    after = Counter({("LOCATOR-VAGUE", "a.yaml"): 1})
    regressions, repairs = wb.delta(before, after)
    assert regressions == []
    assert len(repairs) == 1


def test_an_equal_total_does_not_hide_a_trade():
    """The property a count does not have, and the reason for the signature."""
    before = Counter({("LOCATOR-VAGUE", "a.yaml"): 2, ("LOCATOR-VAGUE", "b.yaml"): 2})
    after = Counter({("LOCATOR-VAGUE", "a.yaml"): 1, ("LOCATOR-VAGUE", "b.yaml"): 3})
    assert sum(before.values()) == sum(after.values())
    regressions, repairs = wb.delta(before, after)
    assert len(regressions) == 1
    assert len(repairs) == 1


# ---- the file --------------------------------------------------------------

def test_a_written_baseline_round_trips(tmp_path):
    signatures = {("LOCATOR-VAGUE", "a.yaml"): 3, ("HYGIENE-UNFILED", ""): 1}
    _write(tmp_path, signatures)
    loaded, meta = wb.load_baseline(tmp_path)
    assert loaded == Counter(signatures)
    assert meta["total"] == 4
    assert meta["distinct_signatures"] == 2
    assert meta["note"]


def test_a_written_baseline_satisfies_its_schema(tmp_path):
    from jsonschema import Draft202012Validator

    _write(tmp_path, {("LOCATOR-VAGUE", "a.yaml"): 3})
    data = yaml.safe_load(
        (tmp_path / wb.BASELINE_RELATIVE).read_text(encoding="utf-8"))
    Draft202012Validator(_SCHEMA).validate(data)


def test_a_missing_baseline_reads_as_empty_not_as_a_pass(tmp_path):
    loaded, meta = wb.load_baseline(tmp_path)
    assert loaded == Counter() and meta == {}
    # With an empty baseline every current warning is new, so the gate fires.
    regressions, _ = wb.delta(loaded, Counter({("LOCATOR-VAGUE", "a.yaml"): 1}))
    assert regressions


@pytest.mark.parametrize("counts", [(3, 1), (1, 3)])
def test_duplicate_signature_is_refused(tmp_path, counts):
    path = tmp_path / wb.BASELINE_RELATIVE
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump({"signatures": [
        {"code": "LOCATOR-VAGUE", "path": "a.md", "count": count} for count in counts
    ]}), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate signature LOCATOR-VAGUE at a.md") as exc:
        wb.load_baseline(tmp_path)
    assert str(path) in str(exc.value)


@pytest.mark.parametrize("row, message", [
    ({"code": "W"}, "missing count"),
    ({"count": 1}, "missing or invalid code"),
    *[({"code": "W", "count": count}, "non-integer count")
      for count in ("many", "3", 1.5, True, None, float("inf"))],
    ({"code": "W", "count": 0}, "count must be positive"),
    ({"code": ["W"], "count": 1}, "missing or invalid code"),
    ({"code": "W", "path": [], "count": 1}, "invalid path"),
    ("row", "expected a mapping"),
])
def test_malformed_row_is_refused(tmp_path, row, message):
    path = tmp_path / wb.BASELINE_RELATIVE
    path.parent.mkdir(parents=True)
    path.write_text(yaml.safe_dump({"signatures": [row]}), encoding="utf-8")
    with pytest.raises(ValueError, match=message) as exc:
        wb.load_baseline(tmp_path)
    assert str(path) in str(exc.value)


@pytest.mark.parametrize("content", ["[", "[]", "signatures: false", "signatures: {}"])
def test_malformed_document_is_named(tmp_path, content):
    path = tmp_path / wb.BASELINE_RELATIVE
    path.parent.mkdir(parents=True)
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError) as exc:
        wb.load_baseline(tmp_path)
    assert str(path) in str(exc.value)


@pytest.mark.parametrize("mode", ["--check", "--show"])
@pytest.mark.parametrize("rows", [
    [{"code": "W", "count": 3}, {"code": "W", "count": 1}],
    [{"code": "W", "count": 1.5}],
])
def test_cli_and_plan_preflight_report_same_refusal(mini_repo, monkeypatch, capsys, mode, rows):
    import sys

    from learning_os.commands.module import _module_plan_validation_errors

    path = mini_repo / wb.BASELINE_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump({"signatures": rows}), encoding="utf-8")
    with pytest.raises(ValueError) as exc:
        _module_plan_validation_errors(mini_repo, {})
    assert str(path) in str(exc.value)
    monkeypatch.setattr(sys, "argv", ["warning_baseline.py", "--root", str(mini_repo), mode])
    assert wb.main() == 2
    output = capsys.readouterr()
    assert str(exc.value) in output.err
    assert "Traceback" not in output.err


def test_checked_in_baseline_loads_unchanged():
    path = ROOT / wb.BASELINE_RELATIVE
    before = path.read_bytes()
    counts, meta = wb.load_baseline(ROOT)
    assert sum(counts.values()) == meta["total"]
    assert len(counts) == meta["distinct_signatures"]
    assert path.read_bytes() == before


def test_environmental_warnings_are_excluded_by_name():
    """They describe the machine, not the content, and differ per checkout."""
    from learning_os.rules.common import ENVIRONMENTAL_WARNINGS

    for code in ("MATERIALS-OFFLINE", "MATERIALS-DRIFT", "HYGIENE-VIEWS", "HYGIENE-LOCK",
                 "ANGLE-REVIEW-UNVERIFIED"):
        assert code in ENVIRONMENTAL_WARNINGS


def test_baseline_exempt_union_is_exactly_the_two_named_sets():
    """No prefix, severity band, or path heuristic — an exact code union only."""
    from learning_os.rules.common import (
        BASELINE_EXEMPT_WARNINGS,
        DYNAMIC_ADVISORY_WARNINGS,
        ENVIRONMENTAL_WARNINGS,
    )

    assert BASELINE_EXEMPT_WARNINGS == ENVIRONMENTAL_WARNINGS | DYNAMIC_ADVISORY_WARNINGS
    assert ENVIRONMENTAL_WARNINGS.isdisjoint(DYNAMIC_ADVISORY_WARNINGS)
    for code in ("WS-NEGLECT", "INBOX-STALE"):
        assert code in DYNAMIC_ADVISORY_WARNINGS
        assert code not in ENVIRONMENTAL_WARNINGS
    # Deliberate split (issue #86): "the bytes are not here" is environmental
    # and baseline-exempt, while "the bytes changed" stays baseline-managed.
    assert "ANGLE-REVIEW-UNVERIFIED" in ENVIRONMENTAL_WARNINGS
    assert "ANGLE-REVIEW-UNVERIFIED" in BASELINE_EXEMPT_WARNINGS
    assert "ANGLE-REVIEW-STALE" not in BASELINE_EXEMPT_WARNINGS


def test_an_unknown_future_warning_code_is_not_exempt_by_accident():
    from learning_os.rules.common import BASELINE_EXEMPT_WARNINGS

    assert "TOTALLY-MADE-UP-WARNING-CODE" not in BASELINE_EXEMPT_WARNINGS
    before = Counter()
    after = Counter({("TOTALLY-MADE-UP-WARNING-CODE", "x.yaml"): 1})
    regressions, _ = wb.delta(before, after)
    assert regressions, "a novel non-exempt code must still fail the gate"


def test_angle_review_unverified_is_dropped_but_stale_is_managed():
    """The #86 split at the gate: only "the bytes changed" can regress."""
    from learning_os.rules.common import Issue

    issues = [Issue("W", "ANGLE-REVIEW-UNVERIFIED", "evidence not on this machine", "sm.yaml"),
              Issue("W", "ANGLE-REVIEW-STALE", "review no longer matches", "sm.yaml")]
    signatures, errors = wb.signatures_from_issues(issues)
    assert errors == []
    assert ("ANGLE-REVIEW-UNVERIFIED", "sm.yaml") not in signatures
    assert signatures[("ANGLE-REVIEW-STALE", "sm.yaml")] == 1


# ---- exact-code exemption against the real emitting rules -------------------
# These reproduce the same fixture conditions as test_hygiene.py and
# test_improvements.py, then assert the resulting signature is present in
# normal validator output (proving visibility is unchanged) but absent from
# the baseline-managed counter `wb.collect()` produces (proving the exemption
# applies to the gate only, never to what an operator or `make check` sees).

def test_hygiene_lock_is_visible_but_baseline_exempt(mini_repo):
    import os
    import time

    lockdir = mini_repo / ".git"
    subprocess.run(["git", "init", "-q"], cwd=mini_repo, check=True, capture_output=True)
    lock = lockdir / "index.lock"
    lock.write_text("", encoding="utf-8")
    old = time.time() - 3600
    os.utime(lock, (old, old))

    from learning_os.loader import load_repo
    from learning_os.rules import validate

    issues = validate(load_repo(mini_repo))
    assert any(i.code == "HYGIENE-LOCK" for i in issues), "must remain visible"

    signatures, errors = wb.collect(mini_repo)
    assert errors == []
    assert not any(code == "HYGIENE-LOCK" for code, _path in signatures)


def test_inbox_stale_is_visible_but_baseline_exempt(mini_repo):
    import os
    import time

    item = mini_repo / "work" / "inbox" / "old-capture.md"
    item.write_text("unrouted capture\n", encoding="utf-8")
    old = time.time() - 20 * 86400
    os.utime(item, (old, old))

    from learning_os.loader import load_repo
    from learning_os.rules import validate

    issues = validate(load_repo(mini_repo))
    assert any(i.code == "INBOX-STALE" for i in issues), "must remain visible"

    signatures, errors = wb.collect(mini_repo)
    assert errors == []
    assert not any(code == "INBOX-STALE" for code, _path in signatures)


def test_ws_neglect_is_visible_but_baseline_exempt(mini_repo):
    import datetime
    import os
    import subprocess

    old = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@e",
        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@e",
        "GIT_AUTHOR_DATE": old, "GIT_COMMITTER_DATE": old,
    }
    subprocess.run(["git", "init", "-q"], cwd=mini_repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=mini_repo, check=True, env=env)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=mini_repo,
                   check=True, env=env)

    from learning_os.loader import load_repo
    from learning_os.rules import validate

    issues = validate(load_repo(mini_repo))
    assert any(i.code == "WS-NEGLECT" for i in issues), "must remain visible"

    signatures, errors = wb.collect(mini_repo)
    assert errors == []
    assert not any(code == "WS-NEGLECT" for code, _path in signatures)


# ---- the ratchet ------------------------------------------------------------
# The baseline is a ceiling the repository repaired below: 485 warnings
# recorded, 0 carried. A stale ceiling lets repaired warnings return
# unnoticed, so --update --ratchet lowers only repaired signatures and
# --check collapses repairs to one summary line.

def _run_cli(monkeypatch, capsys, *argv):
    import sys

    monkeypatch.setattr(sys, "argv", ["warning_baseline.py", *argv])
    return wb.main(), capsys.readouterr()


def test_ratchet_lowers_repairs_and_drops_zeros():
    baseline = Counter({("A", "a.yaml"): 3, ("B", "b.yaml"): 1, ("C", "c.yaml"): 2})
    current = Counter({("A", "a.yaml"): 1, ("C", "c.yaml"): 2})
    assert wb.ratchet(baseline, current) == Counter({("A", "a.yaml"): 1,
                                                     ("C", "c.yaml"): 2})


def test_ratchet_never_raises_a_count_or_adopts_a_new_signature():
    baseline = Counter({("A", "a.yaml"): 3})
    with pytest.raises(ValueError, match=r"NEW +B at b\.yaml"):
        wb.ratchet(baseline, Counter({("A", "a.yaml"): 3, ("B", "b.yaml"): 1}))
    with pytest.raises(ValueError, match=r"3 → 4"):
        wb.ratchet(baseline, Counter({("A", "a.yaml"): 4}))


def test_ratcheted_empty_baseline_writes_schema_valid_file(tmp_path):
    from jsonschema import Draft202012Validator

    assert wb.ratchet(Counter({("A", "a.yaml"): 3}), Counter()) == Counter()
    wb.write_baseline(tmp_path, Counter(), "ratchet to zero")
    text = (tmp_path / wb.BASELINE_RELATIVE).read_text(encoding="utf-8")
    Draft202012Validator(_SCHEMA).validate(yaml.safe_load(text))
    loaded, meta = wb.load_baseline(tmp_path)
    assert loaded == Counter() and meta["total"] == 0
    assert ".venv/bin/python tools/warning_baseline.py --check" in text
    assert not re.findall(r"(?<!/)python tools/warning_baseline\.py", text)


def test_check_collapses_repairs_to_one_summary_line(mini_repo, monkeypatch, capsys):
    _write(mini_repo, {("LOCATOR-VAGUE", "a.yaml"): 3, ("ROUTE-ANGLE-MISSING", "b.yaml"): 1})
    code, out = _run_cli(monkeypatch, capsys, "--check", "--root", str(mini_repo))
    assert code == 0, out.err
    lines = out.out.strip().splitlines()
    assert len(lines) == 3, out.out
    assert "2 signature(s) repaired below baseline (4 → 0)" in lines[1]
    assert "--update --ratchet --note" in lines[1]
    assert "  repaired  " not in out.out


def test_check_on_a_clean_tree_prints_two_lines(mini_repo, monkeypatch, capsys):
    current, _ = wb.collect(mini_repo)
    wb.write_baseline(mini_repo, current, "clean fixture")
    code, out = _run_cli(monkeypatch, capsys, "--check", "--root", str(mini_repo))
    assert code == 0, out.err
    assert len(out.out.splitlines()) == 2, out.out
    assert out.out.splitlines()[1].endswith("OK — zero errors, no new warning signature.")


def test_check_shows_summary_and_new_lines_together(mini_repo, monkeypatch, capsys):
    _write(mini_repo, {("LOCATOR-VAGUE", "a.yaml"): 3})
    (mini_repo / "stray.md").write_text("x", encoding="utf-8")
    code, out = _run_cli(monkeypatch, capsys, "--check", "--root", str(mini_repo))
    assert code == 1
    assert "1 signature(s) repaired below baseline (3 → 1)" in out.out
    assert "NEW       HYGIENE-UNFILED at stray.md" in out.out


def test_show_still_lists_every_repair(mini_repo, monkeypatch, capsys):
    _write(mini_repo, {("LOCATOR-VAGUE", "a.yaml"): 3, ("ROUTE-ANGLE-MISSING", "b.yaml"): 1})
    code, out = _run_cli(monkeypatch, capsys, "--show", "--root", str(mini_repo))
    assert code == 0
    assert out.out.count("  repaired  ") == 2


def test_update_ratchet_adopts_repairs_and_a_returning_warning_fails(
        mini_repo, monkeypatch, capsys):
    _write(mini_repo, {("LOCATOR-VAGUE", "a.yaml"): 3})
    code, out = _run_cli(monkeypatch, capsys, "--update", "--ratchet",
                          "--note", "ratchet fixture", "--root", str(mini_repo))
    assert code == 0, out.err
    assert "ratcheted 3 → 0" in out.out
    loaded, _ = wb.load_baseline(mini_repo)
    assert loaded == Counter()
    # A second run is a no-op that touches nothing.
    before = (mini_repo / wb.BASELINE_RELATIVE).read_bytes()
    code, out = _run_cli(monkeypatch, capsys, "--update", "--ratchet",
                          "--note", "ratchet fixture", "--root", str(mini_repo))
    assert code == 0
    assert "already ratcheted" in out.out
    assert (mini_repo / wb.BASELINE_RELATIVE).read_bytes() == before
    # The ratcheted tree checks clean in two lines …
    code, out = _run_cli(monkeypatch, capsys, "--check", "--root", str(mini_repo))
    assert code == 0
    assert len(out.out.splitlines()) == 2
    # … and a re-introduced warning fails the gate as NEW.
    (mini_repo / "stray.md").write_text("x", encoding="utf-8")
    code, out = _run_cli(monkeypatch, capsys, "--check", "--root", str(mini_repo))
    assert code == 1
    assert "ERROR" not in out.err
    assert "NEW       HYGIENE-UNFILED at stray.md" in out.out


def test_update_ratchet_refuses_a_new_signature(mini_repo, monkeypatch, capsys):
    wb.write_baseline(mini_repo, Counter(), "empty fixture")
    (mini_repo / "stray.md").write_text("x", encoding="utf-8")
    before = (mini_repo / wb.BASELINE_RELATIVE).read_bytes()
    code, out = _run_cli(monkeypatch, capsys, "--update", "--ratchet",
                          "--note", "must refuse", "--root", str(mini_repo))
    assert code == 1
    assert "HYGIENE-UNFILED" in out.err
    assert (mini_repo / wb.BASELINE_RELATIVE).read_bytes() == before


def test_ratchet_without_update_is_refused(mini_repo, monkeypatch, capsys):
    code, out = _run_cli(monkeypatch, capsys, "--ratchet", "--root", str(mini_repo))
    assert code == 2
    assert "--ratchet needs --update" in out.err


def test_update_ratchet_without_note_is_refused(mini_repo, monkeypatch, capsys):
    code, out = _run_cli(monkeypatch, capsys, "--update", "--ratchet",
                          "--root", str(mini_repo))
    assert code == 2
    assert "--update needs --note" in out.err


def test_cli_docstring_uses_the_project_interpreter():
    doc = wb.__doc__ or ""
    assert ".venv/bin/python tools/warning_baseline.py --check" in doc
    assert not re.findall(r"(?<!/)python tools/warning_baseline\.py", doc)


# ---- the live repository ---------------------------------------------------

@pytest.mark.full_repo
def test_the_recorded_baseline_still_matches_this_repository(real_issues):
    # wb.collect() is wired load->validate->signatures and is covered on
    # synthetic repos above; here only the signatures of the live tree matter,
    # so reuse the shared session validation instead of re-running it.
    current, errors = wb.signatures_from_issues(real_issues)
    baseline, meta = wb.load_baseline(ROOT)
    assert meta, "no baseline recorded"
    assert errors == [], "\n".join(errors)
    regressions, _ = wb.delta(baseline, current)
    assert regressions == [], "\n".join(regressions)


@pytest.mark.full_repo
def test_no_baseline_exempt_warning_reached_the_recorded_baseline():
    from learning_os.rules.common import BASELINE_EXEMPT_WARNINGS

    baseline, _ = wb.load_baseline(ROOT)
    for code, _path in baseline:
        assert code not in BASELINE_EXEMPT_WARNINGS, code

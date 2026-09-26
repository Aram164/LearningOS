"""Empty literal-AND searches disclose per-term hit counts.

Both record search and content search conjoin terms; an empty answer
used to print [] with no indication which term eliminated the result.
The stdout shapes stay untouched — the hint goes to stderr.
"""

from __future__ import annotations

import json

from repo_builders import run_los

from learning_os.commands.reads import empty_search_hint


def test_record_search_names_the_eliminating_term(mini_repo):
    result = run_los(mini_repo, "search", "demo zephyr")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == []
    assert "no record matches all 2 terms" in result.stderr
    assert "zephyr=0" in result.stderr
    assert "demo=" in result.stderr and "demo=0" not in result.stderr


def test_record_search_single_term_hint(mini_repo):
    result = run_los(mini_repo, "search", "zephyr")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == []
    assert "no record matches all 1 term;" in result.stderr


def test_record_search_with_hits_stays_silent(mini_repo):
    result = run_los(mini_repo, "search", "demo")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) != []
    assert result.stderr == ""


def test_content_search_names_the_eliminating_term(mini_repo):
    result = run_los(mini_repo, "search", "prose zephyr", "--content")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["total"] == 0
    assert "no note matches all 2 terms" in result.stderr
    assert "prose=1" in result.stderr and "zephyr=0" in result.stderr


def test_content_search_with_hits_stays_silent(mini_repo):
    result = run_los(mini_repo, "search", "prose", "--content")
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["total"] >= 1
    assert result.stderr == ""


def test_hint_truncates_pathological_queries():
    terms = [f"t{n}" for n in range(25)]
    hint = empty_search_hint("record", terms, [1] * 25)
    assert hint.startswith("no record matches all 25 terms;")
    assert "+5 more" in hint
    assert "t24=" not in hint

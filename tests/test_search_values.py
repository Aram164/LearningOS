"""Search matches values, never keys — and says when the array is cut.

F14: metadata search used to serialize each record with ``json.dumps`` and
substring-match terms against keys, punctuation and nulls alike, so ``status``
matched every unit, module, study map, workspace and program. The haystack is
now the record's values only. Content search applies the same rule to note
frontmatter: values match, keys do not, bodies are unchanged.

F15: the plain array response applies ``--limit`` (default 50) silently. When
the array is cut it now prints one stderr line naming the shown/total counts
and the continuation; a complete result stays silent on stderr.
"""

from __future__ import annotations

import json

from repo_builders import run_los


def _page_total(proc):
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)["total"]


# ------------------------------------------------- F14: metadata values only
def test_metadata_search_matches_values_not_keys(mini_repo):
    # "concepts" is a KEY on the note and workspace rows, but no value holds
    # it — except the concept rows' own path value. Base answered 5.
    proc = run_los(mini_repo, "search", "concepts", "--page", "--limit", "1")
    assert _page_total(proc) == 2
    proc = run_los(mini_repo, "search", "concepts")
    assert proc.returncode == 0, proc.stderr
    assert {row["id"] for row in json.loads(proc.stdout)} == {
        "concept-expected-value", "concept-variance"}


def test_metadata_key_only_terms_match_nothing(mini_repo):
    # "title" and "status" are keys on nearly every row; no mini-repo value
    # contains either word. Base answered 6 and 2.
    for term in ("title", "status"):
        proc = run_los(mini_repo, "search", term)
        assert proc.returncode == 0, proc.stderr
        assert json.loads(proc.stdout) == []
        assert f"{term}=0" in proc.stderr


def test_metadata_value_search_still_finds_rows(mini_repo):
    # Guard against over-narrowing: ids, titles and paths are values.
    proc = run_los(mini_repo, "search", "demo", "--page", "--limit", "1")
    assert _page_total(proc) == 5


def test_value_flattening_covers_scalars_and_skips_keys():
    from learning_os.commands.reads import flatten_search_values

    values = flatten_search_values(
        {"status": "ready", "count": 42, "standing": True,
         "nothing": None, "nested": {"deep": [1, False, "x"]}})
    assert "ready" in values and "42" in values and "x" in values
    assert "true" in values and "false" in values and "1" in values
    joined = "\n".join(values)
    for key in ("status", "count", "standing", "nothing", "nested", "deep"):
        assert key not in joined
    assert "null" not in joined
    assert "{" not in joined and '"' not in joined


# --------------------------------------- F14: content frontmatter values only
def test_content_search_ignores_frontmatter_keys(mini_repo):
    # "created" is a frontmatter key on the demo note; no value holds it.
    # Base matched the note.
    proc = run_los(mini_repo, "search", "created", "--content")
    assert proc.returncode == 0, proc.stderr
    assert json.loads(proc.stdout)["total"] == 0


def test_content_search_still_matches_frontmatter_values_and_body(mini_repo):
    # role value "synthesis", title value "Demo note", body word "prose".
    for term in ("synthesis", "Demo", "prose"):
        proc = run_los(mini_repo, "search", term, "--content")
        assert proc.returncode == 0, proc.stderr
        assert json.loads(proc.stdout)["total"] == 1, term


def test_content_body_snippets_keep_true_file_lines(mini_repo):
    proc = run_los(mini_repo, "search", "prose", "--content")
    assert proc.returncode == 0, proc.stderr
    [item] = json.loads(proc.stdout)["items"]
    text = (mini_repo / item["path"]).read_text(encoding="utf-8")
    expected = next(n for n, line in enumerate(text.splitlines(), 1)
                    if "prose" in line)
    assert item["snippets"][0]["line"] == expected


# --------------------------------------------- F15: the array says it is cut
def test_cut_array_names_shown_total_and_continuation(mini_repo):
    proc = run_los(mini_repo, "search", "demo", "--limit", "1")
    assert proc.returncode == 0, proc.stderr
    assert len(json.loads(proc.stdout)) == 1
    assert "showing 1 of 5 matches" in proc.stderr
    assert "--offset 1" in proc.stderr
    assert "--page" in proc.stderr


def test_cut_array_suggests_the_next_offset(mini_repo):
    proc = run_los(mini_repo, "search", "demo", "--limit", "1", "--offset", "1")
    assert proc.returncode == 0, proc.stderr
    assert len(json.loads(proc.stdout)) == 1
    assert "showing 1 of 5 matches" in proc.stderr
    assert "--offset 2" in proc.stderr


def test_complete_array_stays_silent(mini_repo):
    proc = run_los(mini_repo, "search", "demo")
    assert proc.returncode == 0, proc.stderr
    assert len(json.loads(proc.stdout)) == 5
    assert proc.stderr == ""
    exact = run_los(mini_repo, "search", "demo", "--limit", "5")
    assert exact.returncode == 0, exact.stderr
    assert exact.stderr == ""

"""Complete note retrieval and compact startup without hidden truncation."""
import json

from test_cli import run_los

from learning_os.loader import load_repo


def test_note_segments_reconstruct_exact_bytes_and_refuse_stale_continuation(mini_repo):
    note = next(iter(load_repo(mini_repo).notes.values()))
    original = note.path.read_bytes().decode("utf-8")
    response = run_los(mini_repo, "note-read", note.id, "--limit", "60")
    assert response.returncode == 0, response.stderr
    row = json.loads(response.stdout)
    pieces = [row["content"]]
    while row["next_offset"] is not None:
        response = run_los(mini_repo, "note-read", note.id, "--limit", "60",
                           "--offset", str(row["next_offset"]),
                           "--expected-snapshot", row["snapshot_id"])
        assert response.returncode == 0, response.stderr
        row = json.loads(response.stdout)
        pieces.append(row["content"])
    assert "".join(pieces) == original
    note.path.write_text(original + "\nA changed explanation.\n")
    stale = run_los(mini_repo, "note-read", note.id, "--offset", "60",
                    "--expected-snapshot", row["snapshot_id"])
    assert stale.returncode == 3
    assert not stale.stdout


def test_content_search_finds_reasoning_beyond_summary(mini_repo):
    note = next(iter(load_repo(mini_repo).notes.values()))
    with note.path.open("a") as handle:
        handle.write("\n" + "Details. " * 100 + "\n## Same heading\nFehlversuch über Unicode.\n")
    response = run_los(mini_repo, "search", "Fehlversuch", "--type", "note", "--content")
    assert response.returncode == 0, response.stderr
    payload = json.loads(response.stdout)
    assert payload["total"] == 1
    hit = payload["items"][0]
    assert hit["id"] == note.id
    snippet = hit["snippets"][0]
    assert "Fehlversuch" in snippet["text"]
    assert "Fehlversuch" in note.path.read_text().splitlines()[snippet["line"] - 1]
    assert json.loads(run_los(mini_repo, "search", "Fehlversuch", "--type", "note").stdout) == []


def test_compact_startup_has_explicit_totals_and_keeps_details(mini_repo):
    compact = run_los(mini_repo, "bootstrap", "--compact", "--limit", "1")
    assert compact.returncode == 0, compact.stderr
    data = json.loads(compact.stdout)
    full = json.loads(run_los(mini_repo, "bootstrap").stdout)
    for name in ("programs", "modules", "projects", "units"):
        assert data["collections"][name]["total"] == len(full[name])
        for row in data["collections"][name]["items"]:
            detail = run_los(mini_repo, "inspect", row["id"])
            assert detail.returncode == 0
            assert json.loads(detail.stdout)["id"] == row["id"]
    assert len(compact.stdout.encode()) < 65536


def test_bounded_reads_reject_bad_windows_and_unknown_ids(mini_repo):
    for args in (("note-read", "../../private"),
                 ("bootstrap", "--compact", "--limit", "0"),
                 ("bootstrap", "--compact", "--offset", "1"),
                 ("search", "word", "--content", "--limit", "101")):
        result = run_los(mini_repo, *args)
        assert result.returncode != 0
        assert not result.stdout


def test_search_refuses_malformed_note_and_returns_after_repair(mini_repo):
    note = next(iter(load_repo(mini_repo).notes.values()))
    original_text = note.path.read_text(encoding="utf-8")
    with note.path.open("a", encoding="utf-8") as f:
        f.write("\nNeedleUnfindable explanation.\n")

    response = run_los(mini_repo, "search", "NeedleUnfindable", "--type", "note", "--content")
    assert response.returncode == 0

    broken_text = note.path.read_text(encoding="utf-8").replace("id: ", "id: [broken", 1)
    note.path.write_text(broken_text, encoding="utf-8")

    broken_response = run_los(mini_repo, "search", "NeedleUnfindable", "--type", "note", "--content")
    assert broken_response.returncode != 0
    assert "cannot search" in broken_response.stderr
    # Naming the unreadable file is the point: the operator has to find it.
    assert "note-demo.md" in broken_response.stderr

    note.path.write_text(original_text + "\nNeedleUnfindable explanation.\n", encoding="utf-8")
    repaired_response = run_los(mini_repo, "search", "NeedleUnfindable", "--type", "note", "--content")
    assert repaired_response.returncode == 0

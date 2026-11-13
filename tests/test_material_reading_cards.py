"""Private reading memory: the study read, its gate, settlement and adoption (Plan C, ADR-021).

Every case runs the real gateway (``los`` in a child process) against a
synthetic world, with the clock pinned through ``LOS_OBSERVATIONS``. Together
with ``tests/test_study_hooks.py`` these are Plan C's step-5 proofs: no model
is involved, and each case is one check.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from repo_builders import LOS, add_curriculum, write_minimal_pdf

from learning_os.store.contracts.json_schema import validate_contract
from learning_os.store.materials.reading_cards import (
    ADOPT_IDLE,
    MAX_OPEN_ENTRIES,
    Read,
    ReadingStore,
    admit_card,
    store_root,
)

A = "aaaaaaaa-1111-4111-8111-111111111111"
B = "bbbbbbbb-2222-4222-8222-222222222222"
BOOK = "_unsorted/review/book.pdf"
NOW = "2026-11-12T10:00:00+01:00"
LATER = "2026-11-12T12:01:00+01:00"  # two hours and a minute after NOW


def _los(root: Path, *args: str, now: str = NOW) -> subprocess.CompletedProcess:
    observations = root.parent / f".obs-{hashlib.sha256(now.encode()).hexdigest()[:8]}.json"
    observations.write_text(json.dumps({"now": now}), encoding="utf-8")
    env = dict(os.environ, LOS_OBSERVATIONS=str(observations))
    return subprocess.run([sys.executable, str(LOS), "--root", str(root), *args],
                          capture_output=True, text=True, env=env, timeout=120)


def _ok(result: subprocess.CompletedProcess) -> dict:
    assert result.returncode == 0, result.stdout + result.stderr
    return json.loads(result.stdout)


def _refused(result: subprocess.CompletedProcess, needle: str) -> str:
    assert result.returncode != 0, result.stdout
    assert result.stdout == "", "a refused study read returns no text"
    assert needle in result.stderr, result.stderr
    return result.stderr


@pytest.fixture
def world(mini_repo: Path) -> Path:
    add_curriculum(mini_repo)
    write_minimal_pdf(mini_repo.parent / "materials" / BOOK,
                      [f"page {n} on Bayes and evidence" for n in range(1, 13)])
    return mini_repo


def _read(root: Path, session: str, pages: str, *, now: str = NOW, material: str = BOOK):
    return _los(root, "material-study-span", "--material", material, "--pages", pages,
                "--extract", "--session", session, now=now)


def _card(start: int, end: int, kind: str = "statement") -> str:
    return json.dumps({"paraphrase": f"Restates the result of pages {start} to {end} in plain words.",
                       "kinds": [kind],
                       "pointers": [{"page": start, "kind": kind, "label": "the main claim"}],
                       "concepts": ["concept-variance", "concept-not-registered"]})


def _settle(root: Path, session: str, *args: str, now: str = NOW):
    return _los(root, "material-card-settle", *args, "--session", session, now=now)


def _entry(study: dict, index: int = 0) -> str:
    return study["study"]["reads"][index]["entry"]


def _store(root: Path) -> ReadingStore:
    return ReadingStore(root)


def _validate_study(payload: dict, root: Path) -> None:
    validate_contract(Path(__file__).resolve().parents[1], "material-study-span.schema.json", payload)


# ---- capture -------------------------------------------------------------------------


def test_capture_persists_the_entry_before_text_and_refuses_when_it_cannot(world):
    first = _ok(_read(world, A, "pdf pp. 2-3"))
    _validate_study(first, world)
    assert "page 2 on Bayes" in first["span"]["spans"][0]["excerpt"]
    read = first["study"]["reads"][0]
    assert read["state"] == "opened" and read["pages"] == "pdf pp. 2-3"
    pending = store_root(world) / "pending" / f"{read['entry']}.json"
    assert pending.is_file(), "the entry exists by the time the text is returned"
    record = json.loads(pending.read_text())
    assert record["state"] == "open" and record["session"] == A
    assert record["inspected_range"] == {"start": 2, "end": 3}
    assert oct(store_root(world).stat().st_mode & 0o777) == "0o700"
    assert oct(pending.stat().st_mode & 0o777) == "0o600"
    # Fail closed: a store that cannot be written refuses the read and returns no text.
    shutil.rmtree(store_root(world))
    store_root(world).write_text("not a directory", encoding="utf-8")
    message = _refused(_read(world, A, "pdf p. 5"), "cannot record this read")
    assert "must be a real directory" in message


def test_failed_and_clipped_extractions_open_no_entry_and_return_no_text(world):
    long_pages = world.parent / "materials" / "_unsorted/review/long.pdf"
    write_minimal_pdf(long_pages, ["Bayes " * 700 for _ in range(3)])
    message = _refused(_read(world, A, "pdf pp. 1-3", material="_unsorted/review/long.pdf"),
                       "does not fit one excerpt")
    assert '--pages "pdf p. 1"' in message
    assert _store(world).entries() == []
    out_of_range = _los(world, "material-study-span", "--material", BOOK, "--pages", "pdf p. 99",
                        "--extract", "--session", A)
    assert out_of_range.returncode == 0, out_of_range.stderr
    data = json.loads(out_of_range.stdout)
    assert data["span"]["spans"][0]["extraction"] == "unreadable"
    assert data["study"]["reads"] == [] and data["study"]["open_entries"] == []


def test_the_study_read_nests_the_unchanged_material_span_answer(world):
    plain = _ok(_los(world, "material-span", "--material", BOOK, "--pages", "pdf p. 4", "--extract"))
    study = _ok(_read(world, A, "pdf p. 4"))
    assert study["span"] == plain
    assert plain["contract"] == "material-span-v1" and "study" not in plain


def test_a_discontiguous_selection_refuses_one_read_per_contiguous_range(world):
    message = _refused(_read(world, A, "pdf pp. 2 and 4"), "discontiguous")
    assert '--pages "pdf p. 2"' in message and '--pages "pdf p. 4"' in message
    assert _store(world).entries() == []


# ---- the turn cap -------------------------------------------------------------------


def test_a_fifth_span_refuses_while_four_pending_spans_stay_readable(world):
    entries = [_entry(_ok(_read(world, A, f"pdf p. {page}"))) for page in (1, 2, 3, 4)]
    assert len(set(entries)) == MAX_OPEN_ENTRIES == 4
    message = _refused(_read(world, A, "pdf p. 5"), "more than 4 open reading entries")
    assert all(entry in message for entry in entries)
    assert "material-card-settle " + entries[0] in message
    again = _ok(_read(world, A, "pdf p. 2"))
    assert again["study"]["reads"][0] == {**again["study"]["reads"][0], "state": "pending",
                                          "entry": entries[1]}
    assert "page 2 on Bayes" in again["span"]["spans"][0]["excerpt"]
    assert len(list((store_root(world) / "pending").glob("rd-*.json"))) == 4
    # Search, context and settlement stay available at the cap.
    _ok(_los(world, "material-context", "Bayes", "--session", A))
    _ok(_settle(world, A, entries[0], "--dismiss", "irrelevant", "--reason", "only a cover page"))
    _ok(_read(world, A, "pdf p. 5"))


# ---- overdue, Stop and adoption -----------------------------------------------------


def test_stop_marks_open_entries_overdue_and_new_spans_refuse_afterwards(world):
    entry = _entry(_ok(_read(world, A, "pdf p. 6")))
    store = _store(world)
    asks = [store.stop(A, continuing=index > 0) for index in range(3)]
    assert [decision.block for decision in asks] == [True, True, False]
    assert [decision.asked for decision in asks[:2]] == [1, 2]
    assert [row["entry"] for row in asks[2].overdue] == [entry]
    message = _refused(_read(world, A, "pdf p. 7", now=NOW), "overdue reading entries")
    assert entry in message and "material-card-settle " + entry in message
    reread = _ok(_read(world, A, "pdf p. 6"))
    assert reread["study"]["reads"][0]["state"] == "pending"
    _ok(_settle(world, A, entry, "--card", _card(6, 6)))
    _ok(_read(world, A, "pdf p. 7"))


def test_adoption_refuses_a_live_session_and_takes_an_idle_or_ended_one(world):
    entry = _entry(_ok(_read(world, A, "pdf p. 8")))
    live = _settle(world, B, "--adopt", A)
    assert live.returncode != 0 and "still live" in live.stderr
    # A live concurrent session never blocks another one.
    _ok(_read(world, B, "pdf p. 9"))
    # Two hours without a gateway call make A adoptable, which blocks every other session's new spans.
    blocked = _refused(_read(world, B, "pdf p. 10", now=LATER), "adopt and settle them")
    assert entry in blocked and f".venv/bin/python tools/los.py material-card-settle --adopt {A}" in blocked
    adopted = _ok(_settle(world, B, "--adopt", A, now=LATER))
    assert adopted["outcome"] == "adopted" and [row["entry"] for row in adopted["entries"]] == [entry]
    assert adopted["entries"][0]["state"] == "overdue"
    # Adopted debts are B's overdue debts: settle before any new span (G2).
    _refused(_read(world, B, "pdf p. 10", now=LATER), "overdue reading entries")
    _ok(_settle(world, B, entry, "--card", _card(8, 8), now=LATER))
    # B retrying its exact card settlement replays idempotently; A can no longer settle or mask a conflict.
    exact = _ok(_settle(world, B, entry, "--card", _card(8, 8), now=LATER))
    assert exact["replayed"] is True and exact["outcome"] == "saved"
    _refused(_settle(world, A, entry, "--dismiss", "irrelevant", "--reason", "late duplicate", now=LATER),
             "already settled")
    retry = _ok(_settle(world, B, "--adopt", A, now=LATER))
    assert retry["replayed"] is True
    log = (store_root(world) / "log" / f"{B}.jsonl").read_text().splitlines()
    assert [json.loads(line)["outcome"] for line in log] == ["adopted", "saved"]


def test_a_recorded_end_makes_a_session_adoptable_at_once(world):
    entry = _entry(_ok(_read(world, A, "pdf p. 11")))
    store = _store(world)
    for index in range(3):
        store.stop(A, continuing=index > 0)
    # Stop asks and marks overdue but never records an end (ADR-021 decision 5):
    # the session can still resume, so its entries are not adoptable yet.
    still_live = _settle(world, B, "--adopt", A)
    assert still_live.returncode != 0 and "still live" in still_live.stderr
    now = dt.datetime.fromisoformat(NOW)
    store.session_end(A, now=now)
    assert A in store.adoptable(B, now)
    store.touch(A, start=True, now=now)
    still_live = _settle(world, B, "--adopt", A)
    assert still_live.returncode != 0 and "still live" in still_live.stderr
    store.session_end(A, now=now)
    adopted = _ok(_settle(world, B, "--adopt", A))
    assert adopted["replayed"] is False
    assert [row["entry"] for row in adopted["entries"]] == [entry]


def test_adopting_the_same_entry_back_logs_each_transfer(tmp_path):
    store = ReadingStore(Path(__file__).resolve().parents[1], root=tmp_path / "store")
    now = dt.datetime.fromisoformat(NOW)
    read = Read(digest="a" * 64, material=BOOK, start=1, end=1, text_sha256="b" * 64)
    entry = store.admit(A, [read], now=now).opened[0]["entry"]

    for owner, adopter in ((A, B), (B, A), (A, B)):
        store.session_end(owner, now=now)
        result = store.adopt(adopter, owner, now=now)
        assert not result.replayed and result.entries[0]["entry"] == entry

    assert store.adopt(B, A, now=now).replayed
    log = (store.root / "log" / f"{B}.jsonl").read_text().splitlines()
    assert len(log) == 2
    assert all(json.loads(line)["entry"] == entry for line in log)


# ---- settlement ---------------------------------------------------------------------


def test_save_is_idempotent_and_a_failed_save_keeps_the_entry(world):
    entry = _entry(_ok(_read(world, A, "pdf pp. 2-4")))
    pending = store_root(world) / "pending" / f"{entry}.json"
    before = pending.read_bytes()
    outside = json.dumps({"paraphrase": "A card whose pointer leaves the range it describes.",
                          "kinds": ["proof"], "pointers": [{"page": 9, "kind": "proof", "label": "x"}]})
    bad = _settle(world, A, entry, "--card", outside)
    assert bad.returncode != 0 and "outside the recorded range" in bad.stderr
    unbacked = json.dumps({"paraphrase": "Names a kind that no pointer backs at all here.",
                           "kinds": ["proof", "statement"],
                           "pointers": [{"page": 2, "kind": "statement", "label": "x"}]})
    assert "no page pointer" in _settle(world, A, entry, "--card", unbacked).stderr
    assert pending.read_bytes() == before, "a refused save leaves the entry open and unchanged"
    saved = _ok(_settle(world, A, entry, "--card", _card(2, 4)))
    validate_contract(Path(__file__).resolve().parents[1], "material-card-settle.schema.json", saved)
    assert saved["replayed"] is False and saved["card"]["version"] == 1
    assert saved["card"]["review"] == "unreviewed" and saved["card"]["coverage_evidence"] is False
    assert saved["card"]["dangling_concepts"] == ["concept-not-registered"]
    again = _ok(_settle(world, A, entry, "--card", _card(2, 4)))
    assert again["replayed"] is True and again["card"]["version"] == 1
    other = _settle(world, A, entry, "--dismiss", "irrelevant", "--reason", "changed my mind")
    assert other.returncode != 0 and "already settled" in other.stderr
    versions = list((store_root(world) / "cards").rglob("v*.json"))
    assert len(versions) == 1
    assert len((store_root(world) / "log" / f"{A}.jsonl").read_text().splitlines()) == 1


def test_a_re_save_writes_a_new_version_and_keeps_the_old(world):
    first = _entry(_ok(_read(world, A, "pdf p. 12")))
    second = _entry(_ok(_read(world, B, "pdf p. 12")))
    _ok(_settle(world, A, first, "--card", _card(12, 12)))
    resaved = _ok(_settle(world, B, second, "--card", _card(12, 12, "overview")))
    assert resaved["card"]["version"] == 2
    directory = next((store_root(world) / "cards").rglob("p12-12"))
    assert sorted(path.name for path in directory.iterdir()) == ["v1.json", "v2.json"]
    covered = _ok(_read(world, A, "pdf p. 12"))
    assert covered["study"]["memory"][0]["version"] == 2


def test_source_changed_and_source_gone_are_checked_by_the_gateway(world):
    gone = world.parent / "materials" / "_unsorted/review/gone.pdf"
    write_minimal_pdf(gone, ["a page that will vanish", "and another"])
    changed_entry = _entry(_ok(_read(world, A, "pdf p. 1")))
    gone_entry = _entry(_ok(_read(world, A, "pdf p. 1", material="_unsorted/review/gone.pdf")))
    unchanged = _settle(world, A, changed_entry, "--source-changed", "--observed-sha256",
                        "sha256:" + "0" * 64)
    assert unchanged.returncode != 0 and "still hashes to the recorded digest" in unchanged.stderr
    book = world.parent / "materials" / BOOK
    write_minimal_pdf(book, [f"edition two page {n}" for n in range(1, 13)])
    live = "sha256:" + hashlib.sha256(book.read_bytes()).hexdigest()
    wrong = _settle(world, A, changed_entry, "--source-changed", "--observed-sha256", "sha256:" + "1" * 64)
    assert wrong.returncode != 0 and live in wrong.stderr
    closed = _ok(_settle(world, A, changed_entry, "--source-changed", "--observed-sha256", live))
    assert closed["outcome"] == "source-changed"
    present = _settle(world, A, gone_entry, "--source-gone")
    assert present.returncode != 0 and "still there" in present.stderr
    outside = world.parent / "outside.pdf"
    gone.rename(outside)
    gone.symlink_to(outside)
    _refused(_settle(world, A, gone_entry, "--source-gone"), "outside the materials boundary")
    gone.unlink()
    gone.symlink_to(gone.with_name("missing-target.pdf"))
    _refused(_settle(world, A, gone_entry, "--source-gone"), "still exists")
    gone.unlink()
    assert _ok(_settle(world, A, gone_entry, "--source-gone"))["outcome"] == "source-gone"
    assert _store(world).entries(session=A) == []


# ---- coverage ------------------------------------------------------------------------


def test_coverage_is_page_containment_and_redundant_needs_a_containing_card(world):
    narrow = _entry(_ok(_read(world, A, "pdf p. 3")))
    wide = _entry(_ok(_read(world, A, "pdf pp. 2-4")))  # not inside the narrow entry: a new one
    assert wide != narrow
    _ok(_settle(world, A, wide, "--card", _card(2, 4)))
    card = _store(world).all_cards()[0]["card"]
    inside = _ok(_read(world, A, "pdf p. 3"))
    assert inside["study"]["reads"][0]["state"] == "covered"  # the card wins; narrow stays owed
    assert narrow in {row["entry"] for row in inside["study"]["open_entries"]}
    redundant = _ok(_settle(world, A, narrow, "--dismiss", "redundant", "--covering-card", card))
    assert redundant["outcome"] == "dismissed-redundant"
    contained = _ok(_read(world, B, "pdf p. 3"))
    # The card covers every caller; A's own dismissal of the narrow entry does
    # not cover B (ADR-021 decision 4), so only the card is coverage here.
    assert contained["study"]["reads"][0] == {**contained["study"]["reads"][0], "state": "covered",
                                              "entry": None, "covered_by": [card]}
    straddle = _ok(_read(world, B, "pdf pp. 3-5"))
    assert straddle["study"]["reads"][0]["state"] == "opened"
    refused = _settle(world, B, _entry(straddle), "--dismiss", "redundant", "--covering-card", card)
    assert refused.returncode != 0 and "does not hold pdf pp. 3-5" in refused.stderr
    _ok(_settle(world, B, _entry(straddle), "--dismiss", "irrelevant", "--reason", "a worked aside"))
    straddle_entry = _entry(straddle)
    # A dismissal closes the obligation only for the dismissing session (ADR-021
    # decision 4): A's later read of the dismissed page still opens, and B's
    # dismissal is surfaced as prior-dismissal memory, never as coverage.
    later = _ok(_read(world, A, "pdf p. 5"))
    assert later["study"]["reads"][0]["state"] == "opened"
    assert [row["kind"] for row in later["study"]["memory"]] == ["prior-dismissal"]
    assert later["study"]["memory"][0]["entry"] == straddle_entry
    assert later["study"]["memory"][0]["outcome"] == "dismissed-irrelevant"
    assert later["study"]["memory"][0]["reason"] == "a worked aside"
    # B's own re-read of the dismissed range stays covered by its dismissal.
    own = _ok(_read(world, B, "pdf p. 5"))
    assert own["study"]["reads"][0] == {**own["study"]["reads"][0], "state": "covered",
                                        "entry": None, "covered_by": [straddle_entry]}


def test_cards_follow_the_bytes_not_the_path(world):
    entry = _entry(_ok(_read(world, A, "pdf p. 2")))
    _ok(_settle(world, A, entry, "--card", _card(2, 2)))
    moved = world.parent / "materials" / "mathematics" / "book.pdf"
    moved.parent.mkdir(parents=True)
    shutil.copy2(world.parent / "materials" / BOOK, moved)
    read = _ok(_read(world, B, "pdf p. 2", material="mathematics/book.pdf"))
    assert read["study"]["reads"][0]["state"] == "covered"
    assert read["study"]["memory"][0]["material"] == BOOK  # last seen, not the key


# ---- sessions --------------------------------------------------------------------------


@pytest.mark.parametrize("session", [None, "", "abc", A.upper(), A + "x", "../../etc/passwd"])
def test_missing_and_invalid_sessions_refuse(world, session):
    args = ["material-study-span", "--material", BOOK, "--pages", "pdf p. 1", "--extract"]
    if session is not None:
        args += ["--session", session]
    _refused(_los(world, *args), "study session is missing or malformed")
    settle = ["material-card-settle", "--adopt", B]
    if session is not None:
        settle += ["--session", session]
    assert _los(world, *settle).returncode != 0
    search = _los(world, "material-search", "Bayes", *(["--session", session] if session else []))
    if session:
        assert search.returncode != 0 and "malformed" in search.stderr
    assert not store_root(world).exists(), "a refused session never creates the store"


def test_entries_of_another_session_refuse_until_adopted(world):
    entry = _entry(_ok(_read(world, A, "pdf p. 4")))
    stolen = _settle(world, B, entry, "--dismiss", "irrelevant", "--reason", "not mine to say")
    assert stolen.returncode != 0 and f"belongs to session {A}" in stolen.stderr


# ---- privacy, inventory, backup --------------------------------------------------------


def test_the_store_stays_out_of_git_the_inventory_and_the_manifest(world, tmp_path):
    entry = _entry(_ok(_read(world, A, "pdf p. 2")))
    _ok(_settle(world, A, entry, "--card", _card(2, 2)))
    subprocess.run(["git", "init", "-q"], cwd=world, check=True)
    status = subprocess.run(["git", "status", "--porcelain", "--ignored"], cwd=world,
                            capture_output=True, text=True, check=True).stdout
    assert "reading-memory" not in status
    with pytest.raises(ValueError):
        store_root(world).relative_to(world)
    generated = _los(world, "generate")
    assert generated.returncode == 0, generated.stderr
    published = (world / "generated" / "manifest.json").read_text()
    assert "reading-memory" not in published and entry not in published and "card-" not in published
    # The inventory walker never sees the store: it is not under materials/.
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import materials_manifest

    listed = [rel for rel, _ in materials_manifest.iter_material_files(world.parent / "materials")]
    assert listed and not any("reading-memory" in rel or "rd-" in rel for rel in listed)


def _build_ui(workspace: Path) -> Path:
    """A synthetic UI authority beside the repository (never the live checkout)."""
    ui = workspace / "obsidian-ui"
    (ui / "plugin").mkdir(parents=True, exist_ok=True)
    for name in ("main.js", "styles.css", "manifest.json"):
        (ui / "plugin" / name).write_text("void 0;\n", encoding="utf-8")
    (ui / "plugin-assets.json").write_text(json.dumps({
        "schema_version": 1, "type": "learningos-ui-plugin-assets",
        "shipped": ["main.js", "styles.css", "manifest.json"], "vault_owned": ["data.json"],
    }), encoding="utf-8")
    return ui


def test_the_store_is_backed_up_and_restores_with_its_open_entries(world, tmp_path):
    from learning_os.app.backup_manifest import build_backup_manifest, verify_backup_manifest

    ui = _build_ui(world.parent)
    open_entry = _entry(_ok(_read(world, A, "pdf p. 2")))
    saved = _entry(_ok(_read(world, A, "pdf p. 3")))
    _ok(_settle(world, A, saved, "--card", _card(3, 3)))
    manifest = build_backup_manifest(world)
    assert manifest["roots"] == ["core", "materials", "reading-memory", "ui"]
    listed = {row["path"] for row in manifest["entries"] if row["root"] == "reading-memory"}
    assert f"pending/{open_entry}.json" in listed and f"settled/{saved}.json" in listed
    assert any(path.startswith("cards/") for path in listed)
    assert not any(path.startswith((".journal", ".lock")) for path in listed)
    restore = tmp_path / "restore" / "LearningOS"
    shutil.copytree(world, restore / "repository", symlinks=True)
    shutil.copytree(world.parent / "materials", restore / "materials", symlinks=True)
    shutil.copytree(store_root(world), restore / "reading-memory", symlinks=True)
    shutil.copytree(ui, restore / "obsidian-ui", symlinks=True)
    kwargs = {"restored_core": restore / "repository", "restored_ui": restore / "obsidian-ui",
              "restored_materials": restore / "materials"}
    result = verify_backup_manifest(world, manifest, **kwargs)
    assert result["ok"], result["issues"]
    restored = ReadingStore(restore / "repository")
    assert [row["entry"] for row in restored.entries(session=A)] == [open_entry]
    pending_read = _ok(_read(restore / "repository", A, "pdf p. 2"))
    assert pending_read["study"]["reads"][0] == {**pending_read["study"]["reads"][0],
                                                 "state": "pending", "entry": open_entry}
    (restore / "reading-memory" / "pending" / "rd-0000000000000000.json").write_text("{}")
    planted = verify_backup_manifest(world, manifest, **kwargs)
    assert {"root": "reading-memory", "path": "pending/rd-0000000000000000.json",
            "issue": "unaccounted"} in planted["issues"]


def test_an_absent_store_is_no_backup_root(world):
    from learning_os.app.backup_manifest import build_backup_manifest

    _build_ui(world.parent)
    manifest = build_backup_manifest(world)
    assert manifest["roots"] == ["core", "materials", "ui"]


# ---- search and context ----------------------------------------------------------------


def test_study_scope_serves_compact_cards_and_plain_calls_do_not(world):
    entry = _entry(_ok(_read(world, A, "pdf pp. 2-3")))
    _ok(_settle(world, A, entry, "--card", _card(2, 3)))
    context = _ok(_los(world, "material-context", "result", "--session", B))
    assert context["study_cards"]["total"] == 1
    served = context["study_cards"]["items"][0]
    assert served["review"] == "unreviewed" and "pointers" not in served
    assert "study_cards" not in _ok(_los(world, "material-context", "result"))


# ---- durability ------------------------------------------------------------------------


def test_a_torn_log_tail_is_truncated_before_the_next_append(tmp_path):
    store = ReadingStore(Path(__file__).resolve().parents[1], root=tmp_path / "store")
    read = Read(digest="a" * 64, material=BOOK, start=1, end=1, text_sha256="b" * 64)
    entry = store.admit(A, [read]).opened[0]["entry"]
    log = store.root / "log" / f"{A}.jsonl"
    with log.open("a", encoding="utf-8") as handle:
        handle.write('{"record":"log","torn":')  # a crash mid-append leaves partial bytes
    saved = store.save(A, entry, json.loads(_card(1, 1)))
    assert saved.outcome == "saved"
    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["outcome"] == "saved"


def test_a_crash_mid_commit_is_completed_by_the_journal_replay(tmp_path, monkeypatch):
    store = ReadingStore(Path(__file__).resolve().parents[1], root=tmp_path / "store")
    read = Read(digest="a" * 64, material=BOOK, start=1, end=1, text_sha256="b" * 64)
    entry = store.admit(A, [read]).opened[0]["entry"]

    def crash(self, operations):
        raise RuntimeError("crash mid-commit")

    monkeypatch.setattr(ReadingStore, "_apply", crash)
    with pytest.raises(RuntimeError):
        store.save(A, entry, json.loads(_card(1, 1)))
    monkeypatch.undo()
    assert list((store.root / ".journal").glob("*.json")), "the journal outlives the crash"
    replayed = store.save(A, entry, json.loads(_card(1, 1)))
    assert replayed.replayed is True and replayed.outcome == "saved"
    assert replayed.card is not None and replayed.card["version"] == 1
    assert store.entries(session=A) == []
    assert not list((store.root / ".journal").glob("*.json"))
    lines = (store.root / "log" / f"{A}.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1 and json.loads(lines[0])["outcome"] == "saved"


# ---- admission unit checks ----------------------------------------------------------------


def test_card_admission_names_the_first_structural_defect():
    rng = {"start": 2, "end": 4}
    good = json.loads(_card(2, 4))
    assert admit_card(good, rng)["kinds"] == ["statement"]
    for change, needle in [
        ({"paraphrase": "short"}, "paraphrase"),
        ({"kinds": ["essay"]}, "kinds"),
        ({"pointers": []}, "pointers"),
        ({"concepts": ["Concept X"]}, "concepts"),
        ({"extra": 1}, "unknown fields"),
    ]:
        from learning_os.store.materials.reading_cards import SettleRefusal

        with pytest.raises(SettleRefusal, match=needle):
            admit_card({**good, **change}, rng)


def test_idle_window_is_two_hours():
    assert ADOPT_IDLE.total_seconds() == 7200


def test_cross_session_settled_card_permutations_fail_closed(world):
    from learning_os.store.materials.reading_cards import ReadingStoreError, SettleRefusal

    store = _store(world)
    rd = Read(digest="a" * 64, material=BOOK, start=2, end=3, text_sha256="b" * 64)
    c = "cccccccc-3333-4333-8333-333333333333"

    # Case 1: A opens -> ends -> B adopts -> B saves card1.
    t0 = dt.datetime.fromisoformat(NOW)
    e1 = store.admit(A, [rd], now=t0).opened[0]["entry"]
    store.session_end(A, now=t0)
    store.adopt(B, A, now=t0)
    c1 = json.loads(_card(2, 3))
    c2 = json.loads(_card(1, 5))
    first = store.save(B, e1, c1, now=t0)
    assert first.outcome == "saved" and not first.replayed

    # Exact retry by settler B replays idempotently.
    assert store.save(B, e1, c1, now=t0).replayed is True
    # Conflicting settle by settler B, any settle by original A, or identical settle by C must fail closed.
    for _caller, fn in [
        ("B diff card", lambda: store.save(B, e1, c2, now=t0)),
        ("B dismiss", lambda: store.dismiss(B, e1, "irrelevant", reason="changed mind", now=t0)),
        ("A identical save", lambda: store.save(A, e1, c1, now=t0)),
        ("A dismiss", lambda: store.dismiss(A, e1, "irrelevant", reason="late", now=t0)),
        ("C identical save", lambda: store.save(c, e1, c1, now=t0)),
    ]:
        with pytest.raises((SettleRefusal, ReadingStoreError)):
            fn()

    # Case 2: B adopts -> B dismisses -> A trying to save/dismiss (even identical) must fail closed.
    rd2 = Read(digest="d" * 64, material=BOOK, start=4, end=5, text_sha256="e" * 64)
    e2 = store.admit(A, [rd2], now=t0).opened[0]["entry"]
    store.session_end(A, now=t0)
    store.adopt(B, A, now=t0)
    d1 = store.dismiss(B, e2, "irrelevant", reason="boilerplate", now=t0)
    assert d1.outcome == "dismissed-irrelevant"
    assert store.dismiss(B, e2, "irrelevant", reason="boilerplate", now=t0).replayed is True
    with pytest.raises(SettleRefusal, match="already settled"):
        store.save(A, e2, json.loads(_card(4, 5)), now=t0)
    with pytest.raises(SettleRefusal, match="already settled"):
        store.dismiss(A, e2, "irrelevant", reason="boilerplate", now=t0)
    with pytest.raises((SettleRefusal, ReadingStoreError)):
        store.dismiss(c, e2, "irrelevant", reason="boilerplate", now=t0)


def test_crash_temp_files_stay_in_journal_and_are_cleaned_on_recovery(world, tmp_path):
    from learning_os.app.backup_manifest import build_backup_manifest

    store = _store(world)
    rd = Read(digest="a" * 64, material=BOOK, start=1, end=2, text_sha256="b" * 64)
    entry = store.admit(A, [rd]).opened[0]["entry"]

    # Simulate legacy and in-journal interrupted temp files across store trees.
    stale_pending = store.root / "pending" / f".{entry}.json.tmp-999999"
    stale_pending.write_text("{", encoding="utf-8")
    stale_journal = store.root / ".journal" / ".card.json.tmp-999999"
    stale_journal.parent.mkdir(parents=True, exist_ok=True)
    stale_journal.write_text("{", encoding="utf-8")
    stale_card = store.root / "cards" / ("a" * 64) / ".v0001.json.tmp-999999"
    stale_card.parent.mkdir(parents=True, exist_ok=True)
    stale_card.write_text("{", encoding="utf-8")

    # Failed write unlinks its own temp file cleanly via BaseException cleanup.
    observed_temps: list[Path] = []
    real_replace = os.replace

    def fail_once(src, dst):
        if "reading-memory" in str(dst) and str(dst).endswith(f"{entry}.json"):
            observed_temps.append(Path(src))
            raise RuntimeError("injected replace failure")
        return real_replace(src, dst)

    mp = pytest.MonkeyPatch()
    try:
        mp.setattr(os, "replace", fail_once)
        with pytest.raises(RuntimeError, match="injected replace failure"):
            store.save(A, entry, json.loads(_card(1, 2)))
    finally:
        mp.undo()
    assert observed_temps and observed_temps[0].parent == store.root / ".journal"
    assert not observed_temps[0].exists()

    # build_backup_manifest takes the store lock (triggering recovery) and excludes temp files.
    ui = _build_ui(world.parent)
    manifest = build_backup_manifest(world, ui_root=ui)
    rm_paths = [row["path"] for row in manifest["entries"] if row["root"] == "reading-memory"]
    assert not any(".tmp-" in p for p in rm_paths), rm_paths
    assert not stale_pending.exists()
    assert not stale_journal.exists()
    assert not stale_card.exists()


def test_backup_manifest_serializes_with_concurrent_reading_card_settle(world):
    import threading

    from learning_os.app.backup_manifest import build_backup_manifest

    store = _store(world)
    rd = Read(digest="a" * 64, material=BOOK, start=6, end=7, text_sha256="b" * 64)
    entry = store.admit(A, [rd]).opened[0]["entry"]
    ui = _build_ui(world.parent)

    started = threading.Event()
    proceed = threading.Event()
    errors: list[BaseException] = []
    manifests: list[dict] = []

    real_replace = os.replace

    def barrier_replace(src, dst):
        if Path(dst).name == f"{entry}.json" and "settled" in str(dst):
            started.set()
            proceed.wait(timeout=10)
        return real_replace(src, dst)

    def run_backup():
        try:
            manifests.append(build_backup_manifest(world, ui_root=ui))
        except BaseException as exc:  # pragma: no cover - captured for assertion
            errors.append(exc)

    mp = pytest.MonkeyPatch()
    mp.setattr(os, "replace", barrier_replace)
    backup_thread = None
    try:
        save_thread = threading.Thread(
            target=lambda: store.save(A, entry, json.loads(_card(6, 7))),
        )
        save_thread.start()
        assert started.wait(timeout=10)
        backup_thread = threading.Thread(target=run_backup)
        backup_thread.start()
        proceed.set()
        save_thread.join(timeout=10)
        backup_thread.join(timeout=10)
    finally:
        proceed.set()
        if backup_thread is not None and backup_thread.is_alive():
            backup_thread.join(timeout=2)
        mp.undo()

    assert not errors, errors
    assert len(manifests) == 1
    rm_paths = {row["path"] for row in manifests[0]["entries"] if row["root"] == "reading-memory"}
    assert f"settled/{entry}.json" in rm_paths
    assert f"pending/{entry}.json" not in rm_paths


def test_passive_touch_preserves_ended_at_while_explicit_start_reactivates(world):
    entry = _entry(_ok(_read(world, A, "pdf p. 11")))
    store = _store(world)
    now = dt.datetime.fromisoformat(NOW)
    store.session_end(A, now=now)
    assert store.ended(A, now) is True

    store.touch(A, start=False, now=now)
    session = store.session(A)
    assert session is not None and session["ended_at"] is not None
    assert store.ended(A, now) is True
    assert [row["entry"] for row in store.adoptable(B, now).get(A, [])] == [entry]

    store.touch(A, start=True, now=now)
    session = store.session(A)
    assert session is not None and session["ended_at"] is None
    assert store.ended(A, now) is False


def test_study_context_and_search_lock_without_creating_absent_store_and_recover_journal(world, monkeypatch):
    from learning_os.app.context import OpContext
    from learning_os.app.handlers.materials import _study_context_cards, _study_hit_cards
    from learning_os.store.loading import load_repo

    repo = load_repo(world)
    ctx_search = OpContext(root=world, operation="material.search", channel="operator",
                           invocation="query", gateway=None)
    ctx_context = OpContext(root=world, operation="material.context", channel="operator",
                            invocation="query", gateway=None)

    assert _study_context_cards(ctx_context, repo, raw_terms=["Bayes"],
                                concept_id=None, material=None)["items"] == []
    absent_payload: dict = {"hits": [{"sha256": "sha256:" + "a" * 64, "span_pages": "pdf p. 1"}]}
    _study_hit_cards(ctx_search, repo, B, absent_payload)
    assert absent_payload["hits"][0]["cards"] == []
    assert absent_payload["study"]["cards"] == 0
    assert not store_root(world).exists(), "read paths never create an absent reading store"

    store = _store(world)
    book_bytes = (world.parent / "materials" / BOOK).read_bytes()
    digest = hashlib.sha256(book_bytes).hexdigest()
    read = Read(digest=digest, material=BOOK, start=1, end=1, text_sha256="b" * 64)
    entry = store.admit(A, [read]).opened[0]["entry"]

    def crash(self, operations):
        raise RuntimeError("crash mid-commit")

    monkeypatch.setattr(ReadingStore, "_apply", crash)
    with pytest.raises(RuntimeError, match="crash mid-commit"):
        store.save(A, entry, json.loads(_card(1, 1)))
    monkeypatch.undo()
    assert list((store.root / ".journal").glob("*.json"))

    ctx_result = _study_context_cards(ctx_context, repo, raw_terms=["Restates"],
                                      concept_id=None, material=None)
    assert ctx_result["total"] == 1
    assert not list((store.root / ".journal").glob("*.json"))

    # Simulate a second mid-commit crash recovered by _study_hit_cards under store.locked(create=False).
    entry2 = store.admit(A, [Read(digest=digest, material=BOOK, start=2, end=2, text_sha256="c" * 64)]).opened[0]["entry"]
    monkeypatch.setattr(ReadingStore, "_apply", crash)
    with pytest.raises(RuntimeError, match="crash mid-commit"):
        store.save(A, entry2, json.loads(_card(2, 2)))
    monkeypatch.undo()
    assert list((store.root / ".journal").glob("*.json"))

    hit_payload: dict = {"hits": [{"sha256": f"sha256:{digest}", "span_pages": "pdf pp. 1-2"}]}
    _study_hit_cards(ctx_search, repo, B, hit_payload)
    assert len(hit_payload["hits"][0]["cards"]) == 2
    assert hit_payload["study"]["cards"] == 2
    assert not list((store.root / ".journal").glob("*.json"))


def test_reading_store_lock_order_follows_operator_lock(world, monkeypatch):
    """Whenever operator_lock and ReadingStore.locked() are both held, operator_lock comes first."""
    import argparse
    import contextlib

    from learning_os.app import lock as app_lock
    from learning_os.app import pipeline as pipeline_module
    from learning_os.app.registry import REGISTRY
    from learning_os.store.materials import search_index

    assert REGISTRY["material.study-span"].lock == "shared"
    assert REGISTRY["material.card.settle"].lock == "shared"

    events: list[tuple[str, str, bool | None]] = []
    real_op_lock = app_lock.operator_lock
    real_rs_locked = ReadingStore.locked

    @contextlib.contextmanager
    def recording_op_lock(root, *, shared=False):
        events.append(("operator", "enter", shared))
        try:
            with real_op_lock(root, shared=shared):
                yield
        finally:
            events.append(("operator", "exit", shared))

    @contextlib.contextmanager
    def recording_rs_locked(self, *, create=True):
        events.append(("reading_store", "enter", create))
        try:
            with real_rs_locked(self, create=create) as present:
                yield present
        finally:
            events.append(("reading_store", "exit", create))

    monkeypatch.setattr(pipeline_module, "_operator_lock", recording_op_lock)
    monkeypatch.setattr(ReadingStore, "locked", recording_rs_locked)

    span_args = argparse.Namespace(
        root=str(world), _operation="material.study-span", json=True,
        material=BOOK, pages="pdf p. 5", extract=True, session=A,
    )
    span_outcome = pipeline_module.run_cli(world, "material.study-span", span_args)
    assert span_outcome.exit_code == 0, span_outcome.stderr
    assert events[0] == ("operator", "enter", True)
    assert events[-1] == ("operator", "exit", True)
    assert ("reading_store", "enter", True) in events
    assert events.index(("operator", "enter", True)) < events.index(("reading_store", "enter", True))
    assert events.index(("reading_store", "exit", True)) < events.index(("operator", "exit", True))
    entry_id = json.loads(span_outcome.stdout)["study"]["reads"][0]["entry"]

    events.clear()
    settle_args = argparse.Namespace(
        root=str(world), _operation="material.card.settle", _operation_kind="tool",
        json=True, entry=entry_id, card=json.loads(_card(5, 5)), session=A,
    )
    settle_outcome = pipeline_module.run_cli(world, "material.card.settle", settle_args)
    assert settle_outcome.exit_code == 0, settle_outcome.stderr
    assert events == [
        ("operator", "enter", True),
        ("reading_store", "enter", True),
        ("reading_store", "exit", True),
        ("operator", "exit", True),
    ]

    events.clear()
    ctx_args = argparse.Namespace(
        root=str(world), _operation="material.context", json=True,
        query="Restates", session=B,
    )
    ctx_outcome = pipeline_module.run_cli(world, "material.context", ctx_args)
    assert ctx_outcome.exit_code == 0, ctx_outcome.stderr
    assert events == [
        ("operator", "enter", True),
        ("reading_store", "enter", False),
        ("reading_store", "exit", False),
        ("operator", "exit", True),
    ]

    from types import SimpleNamespace

    events.clear()
    digest = hashlib.sha256((world.parent / "materials" / BOOK).read_bytes()).hexdigest()
    monkeypatch.setattr(search_index, "execute_search", lambda *a, **kw: SimpleNamespace(
        to_dict=lambda: {
            "schema_version": 1, "query": "Restates",
            "hits": [{"sha256": f"sha256:{digest}", "span_pages": "pdf p. 5", "score": 1.0}],
        },
    ))
    search_args = argparse.Namespace(
        root=str(world), _operation="material.search", json=True,
        query="Restates", session=B, limit=5, offset=0,
    )
    search_outcome = pipeline_module.run_cli(world, "material.search", search_args)
    assert search_outcome.exit_code == 0, search_outcome.stderr
    assert events == [
        ("operator", "enter", True),
        ("reading_store", "enter", False),
        ("reading_store", "exit", False),
        ("operator", "exit", True),
    ]


def test_reading_store_never_imports_or_acquires_operator_lock():
    """The store layer (and ReadingStore) structurally never imports operator_lock."""
    import ast

    store_dir = Path(__file__).resolve().parents[1] / "tools" / "learning_os" / "store"
    for py_path in sorted(store_dir.rglob("*.py")):
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                assert not node.module.startswith("learning_os.app"), (py_path, node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith("learning_os.app"), (py_path, alias.name)
            elif isinstance(node, ast.Name):
                assert node.id not in {"operator_lock", "_operator_lock", "escalate_operator_lock"}, py_path


def test_omit_covered_text_strips_only_covered_excerpts(world):
    first = _ok(_read(world, A, "pdf p. 2"))
    entry = _entry(first)
    assert "excerpt" in first["span"]["spans"][0]
    _ok(_settle(world, A, entry, "--card", _card(2, 2)))

    # On an already-covered span, --omit-covered-text omits raw excerpt text while serving the card.
    covered = _ok(_los(
        world, "material-study-span", "--material", BOOK, "--pages", "pdf p. 2",
        "--extract", "--omit-covered-text", "--session", B,
    ))
    assert covered["study"]["reads"][0]["state"] == "covered"
    span = covered["span"]["spans"][0]
    assert "excerpt" not in span
    assert span["excerpt_omitted"] == "covered"
    assert [item["kind"] for item in covered["study"]["memory"]] == ["card"]

    # On an uncovered span, --omit-covered-text still returns the excerpt needed to write a card.
    uncovered = _ok(_los(
        world, "material-study-span", "--material", BOOK, "--pages", "pdf p. 4",
        "--extract", "--omit-covered-text", "--session", B,
    ))
    assert uncovered["study"]["reads"][0]["state"] == "opened"
    assert "excerpt" in uncovered["span"]["spans"][0]
    assert "excerpt_omitted" not in uncovered["span"]["spans"][0]


def test_comma_separated_discontiguous_pages_refuse_fail_closed_in_study(world):
    refused = _los(
        world, "material-study-span", "--material", BOOK, "--pages", "pdf p. 1,4",
        "--extract", "--session", A,
    )
    assert refused.returncode == 2
    assert refused.stdout == ""
    assert "discontiguous" in refused.stderr
    assert _store(world).entries(session=A) == []


def test_settle_hints_and_cli_help_advertise_treatment_kinds(world):
    from learning_os.store.materials.reading_cards import (
        LOS_COMMAND,
        TREATMENT_KINDS,
        adopt_command,
        settle_command,
        treatment_kinds_hint,
    )

    cmd = settle_command("rd-0123456789abcdef")
    adopt = adopt_command(A)
    kinds_prose = treatment_kinds_hint()
    assert cmd.startswith(f"{LOS_COMMAND} material-card-settle rd-0123456789abcdef ")
    assert adopt == f"{LOS_COMMAND} material-card-settle --adopt {A}"
    assert "(kinds:" not in cmd
    for sep in (" | ", " || ", "; ", " && "):
        assert sep not in cmd
    payload = _ok(_read(world, A, "pdf p. 2"))
    next_action = payload["study"]["next_action"]
    assert f"Commands:\n{LOS_COMMAND} material-card-settle " in next_action
    for sep in (" | ", " || ", "; ", " && "):
        assert sep not in next_action
    help_out = _los(world, "material-card-settle", "--help")
    assert help_out.returncode == 0
    for kind in TREATMENT_KINDS:
        assert kind in kinds_prose
        assert kind in next_action
        assert kind in help_out.stdout


def test_generated_commands_separate_alternatives_and_preserve_covered_source_extract(world):
    from learning_os.store.materials.reading_cards import (
        LOS_COMMAND,
        join_adopt_commands,
        join_settle_commands,
    )

    joined_settle = join_settle_commands(["rd-1111111111111111", "rd-2222222222222222"])
    joined_adopt = join_adopt_commands([A, B])
    for text in (joined_settle, joined_adopt):
        for sep in (" | ", " || ", "; ", " && "):
            assert sep not in text
    cmd_lines = [line for line in joined_settle.splitlines() if LOS_COMMAND in line]
    assert len(cmd_lines) == 4
    assert all(line.startswith(f"{LOS_COMMAND} material-card-settle rd-") for line in cmd_lines)
    adopt_lines = [line for line in joined_adopt.splitlines() if line]
    assert adopt_lines == [
        f"{LOS_COMMAND} material-card-settle --adopt {A}",
        f"{LOS_COMMAND} material-card-settle --adopt {B}",
    ]

    # Multi-entry next_action and cap refusal omit shell pipelines and operators.
    first = _ok(_read(world, A, "pdf p. 1"))
    entry1 = _entry(first)
    second = _ok(_read(world, A, "pdf p. 2"))
    entry2 = _entry(second)
    for sep in (" | ", " || ", "; ", " && "):
        assert sep not in second["study"]["next_action"]
    assert f"Entry {entry1}:" in second["study"]["next_action"]
    assert f"Entry {entry2}:" in second["study"]["next_action"]

    _ok(_read(world, A, "pdf p. 3"))
    fourth = _ok(_read(world, A, "pdf p. 4"))
    entry4 = _entry(fourth)
    limit_err = _refused(_read(world, A, "pdf p. 5"), "more than 4 open reading entries")
    limit_next = limit_err.split("  next: ", 1)[1]
    for sep in (" | ", " || ", "; ", " && "):
        assert sep not in limit_next
    assert f"\n{LOS_COMMAND} material-card-settle {entry4} --card " in limit_next

    # Adoptable refusal across ended sessions separates --adopt commands without || or ;.
    _ok(_read(world, B, "pdf p. 6"))
    store = _store(world)
    store.session_end(A)
    store.session_end(B)
    C = "cccccccc-3333-4333-8333-333333333333"
    adopt_err = _refused(_read(world, C, "pdf p. 7"), "adopt and settle them")
    adopt_next = adopt_err.split("  next: ", 1)[1]
    for sep in (" | ", " || ", "; ", " && "):
        assert sep not in adopt_next
    assert f"{LOS_COMMAND} material-card-settle --adopt {A}" in adopt_next
    assert f"{LOS_COMMAND} material-card-settle --adopt {B}" in adopt_next

    # Source fidelity baseline (Option B): default covered study reads preserve raw excerpt
    # and unreviewed/non-evidence card metadata; --omit-covered-text remains explicit opt-in.
    assert _settle(world, C, "--adopt", A).returncode == 0
    assert _settle(world, C, entry4, "--card", _card(4, 4)).returncode == 0
    default_covered = _ok(_read(world, C, "pdf p. 4"))
    assert "page 4 on Bayes and evidence" in default_covered["span"]["spans"][0]["excerpt"]
    assert "excerpt_omitted" not in default_covered["span"]["spans"][0]
    assert default_covered["study"]["reads"][0]["state"] == "covered"
    assert default_covered["study"]["memory"][0]["review"] == "unreviewed"
    assert default_covered["study"]["memory"][0]["coverage_evidence"] is False

    omitted = _ok(_los(
        world, "material-study-span", "--material", BOOK, "--pages", "pdf p. 4",
        "--extract", "--omit-covered-text", "--session", C,
    ))
    assert omitted["span"]["spans"][0]["excerpt_omitted"] == "covered"
    assert "excerpt" not in omitted["span"]["spans"][0]
    assert omitted["study"]["memory"][0]["review"] == "unreviewed"
    assert omitted["study"]["memory"][0]["coverage_evidence"] is False

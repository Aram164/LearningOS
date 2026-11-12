"""Private reading memory: the study read, its gate, settlement and adoption (Plan C, ADR-021).

Every case runs the real gateway (``los`` in a child process) against a
synthetic world, with the clock pinned through ``LOS_OBSERVATIONS``. Together
with ``tests/test_study_hooks.py`` these are Plan C's step-5 proofs: no model
is involved, and each case is one check.
"""

from __future__ import annotations

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
    assert entry in blocked and f"los material-card-settle --adopt {A}" in blocked
    adopted = _ok(_settle(world, B, "--adopt", A, now=LATER))
    assert adopted["outcome"] == "adopted" and [row["entry"] for row in adopted["entries"]] == [entry]
    assert adopted["entries"][0]["state"] == "overdue"
    # Adopted debts are B's overdue debts: settle before any new span (G2).
    _refused(_read(world, B, "pdf p. 10", now=LATER), "overdue reading entries")
    _ok(_settle(world, B, entry, "--card", _card(8, 8), now=LATER))
    # The original session's later settle replays idempotently.
    replay = _ok(_settle(world, A, entry, "--dismiss", "irrelevant", "--reason", "late duplicate", now=LATER))
    assert replay["replayed"] is True and replay["outcome"] == "saved"
    retry = _ok(_settle(world, B, "--adopt", A, now=LATER))
    assert retry["replayed"] is True
    log = (store_root(world) / "log" / f"{B}.jsonl").read_text().splitlines()
    assert [json.loads(line)["outcome"] for line in log] == ["adopted", "saved"]


def test_a_recorded_end_makes_a_session_adoptable_at_once(world):
    entry = _entry(_ok(_read(world, A, "pdf p. 11")))
    store = _store(world)
    for index in range(3):
        store.stop(A, continuing=index > 0)
    adopted = _ok(_settle(world, B, "--adopt", A))
    assert [row["entry"] for row in adopted["entries"]] == [entry]


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
    assert contained["study"]["reads"][0] == {**contained["study"]["reads"][0], "state": "covered",
                                              "entry": None, "covered_by": [card, narrow]}
    straddle = _ok(_read(world, B, "pdf pp. 3-5"))
    assert straddle["study"]["reads"][0]["state"] == "opened"
    refused = _settle(world, B, _entry(straddle), "--dismiss", "redundant", "--covering-card", card)
    assert refused.returncode != 0 and "does not hold pdf pp. 3-5" in refused.stderr
    _ok(_settle(world, B, _entry(straddle), "--dismiss", "irrelevant", "--reason", "a worked aside"))
    assert _ok(_read(world, A, "pdf p. 5"))["study"]["reads"][0]["state"] == "covered"


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

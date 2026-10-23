"""Automatic guard derivation for the sealing helper (#80).

`seal_envelope.py --guards auto` derives the exact transaction artifact
set with a gateway dry run and reads revisions under the same lock as
the snapshot, so the sealed envelope commits on the first submission.
A concurrent canonical change still refuses as `STALE_SNAPSHOT`, and
explicit `--revision` entries still win.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from gateway_helpers import file_sha256, run_v2_capability

from learning_os.store.fingerprint import canonical_fingerprint

SEAL = Path(__file__).resolve().parent.parent / "tools" / "seal_envelope.py"

FIRST_SUBMISSION_CASES = [
    ("stage.progress.update", "guards-auto-progress-001",
     {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
      "status": "active"}),
    ("stage.note.write", "guards-auto-note-001",
     {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
      "text": "auto-guard note line"}),
    ("stage.attachment.add", "guards-auto-attach-001", None),  # needs a file
    ("source.feedback.record", "guards-auto-feedback-001",
     {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
      "source_id": "source-demo-book", "feedback": "helpful"}),
    ("capture.create", "guards-auto-capture-001",
     {"text": "auto-guard capture"}),
    ("garden.seed.create", "guards-auto-garden-001",
     {"text": "auto-guard seed"}),
]


def _seal(root: Path, out: Path, *, capability: str, payload: dict,
          key: str, extra: list[str] | None = None):
    command = [sys.executable, str(SEAL), "--root", str(root),
               "--capability", capability, "--payload", json.dumps(payload),
               "--key", key, "--guards", "auto", "--out", str(out)]
    command.extend(extra or [])
    return subprocess.run(command, capture_output=True, text=True, timeout=120)


def _submit(root: Path, envelope_path: Path):
    return run_v2_capability(
        root, json.loads(envelope_path.read_text(encoding="utf-8")))


@pytest.mark.parametrize("capability,key,payload", FIRST_SUBMISSION_CASES,
                         ids=[case[0] for case in FIRST_SUBMISSION_CASES])
def test_guards_auto_commits_on_the_first_submission(
        mini_repo: Path, tmp_path: Path, capability: str, key: str,
        payload: dict | None):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    if payload is None:  # stage.attachment.add needs a real approved file
        source = tmp_path / "attachment.txt"
        source.write_text("auto-guard attachment bytes", encoding="utf-8")
        payload = {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                   "file": str(source), "file_sha256": file_sha256(source),
                   "label": "auto"}
    sealed = _seal(mini_repo, tmp_path / "sealed.json", capability=capability,
                   payload=payload, key=key)
    assert sealed.returncode == 0, sealed.stderr
    assert "guards auto:" in sealed.stderr
    applied = _submit(mini_repo, tmp_path / "sealed.json")
    assert applied.returncode == 0, applied.stdout + applied.stderr
    body = json.loads(applied.stdout)
    assert body["ok"] is True, body
    assert body["replayed"] is False


def test_concurrent_canonical_change_still_refuses_as_stale_snapshot(
        mini_repo: Path, tmp_path: Path):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    first = _seal(mini_repo, tmp_path / "first.json",
                  capability="garden.seed.create",
                  payload={"text": "sealed before the concurrent write"},
                  key="guards-auto-stale-001")
    assert first.returncode == 0, first.stderr
    concurrent = _seal(mini_repo, tmp_path / "concurrent.json",
                       capability="capture.create",
                       payload={"text": "concurrent write"},
                       key="guards-auto-stale-002")
    assert concurrent.returncode == 0, concurrent.stderr
    applied = _submit(mini_repo, tmp_path / "concurrent.json")
    assert applied.returncode == 0, applied.stdout
    assert json.loads(applied.stdout)["ok"] is True
    stale = _submit(mini_repo, tmp_path / "first.json")
    assert stale.returncode == 3, stale.stdout
    body = json.loads(stale.stdout)
    assert body["ok"] is False
    assert body["error"]["code"] == "STALE_SNAPSHOT"


def test_explicit_revision_wins_over_derived_guards(mini_repo: Path,
                                                   tmp_path: Path):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   capability="stage.progress.update",
                   payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                            "status": "active"},
                   key="guards-auto-override-001",
                   extra=["--revision", "unit-demo-l01=99"])
    assert sealed.returncode == 0, sealed.stderr
    envelope = json.loads((tmp_path / "sealed.json").read_text(encoding="utf-8"))
    assert envelope["expected_revisions"]["unit-demo-l01"] == 99
    assert envelope["expected_revisions"]["study-map-demo-l01"] == 0
    applied = _submit(mini_repo, tmp_path / "sealed.json")
    assert applied.returncode == 3, applied.stdout
    assert json.loads(applied.stdout)["error"]["code"] == "REVISION_CONFLICT"


def test_guard_derivation_writes_nothing(mini_repo: Path, tmp_path: Path):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    fingerprint_before = canonical_fingerprint(mini_repo)
    tree_before = {path for path in mini_repo.rglob("*")}
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   capability="source.feedback.record",
                   payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                            "source_id": "source-demo-book",
                            "feedback": "helpful"},
                   key="guards-auto-dry-001")
    assert sealed.returncode == 0, sealed.stderr
    assert canonical_fingerprint(mini_repo) == fingerprint_before
    assert {path for path in mini_repo.rglob("*")} == tree_before


def test_guard_derivation_refuses_an_invalid_payload_at_seal_time(
        mini_repo: Path, tmp_path: Path):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    sealed = _seal(mini_repo, tmp_path / "sealed.json",
                   capability="stage.progress.update",
                   payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                            "status": "done"},
                   key="guards-auto-invalid-001")
    assert sealed.returncode == 2
    assert "invalid payload" in sealed.stderr
    for allowed in ("active", "paused", "complete", "skipped", "revisit"):
        assert allowed in sealed.stderr


def test_envelope_without_schema_version_is_refused_before_dispatch(
        mini_repo: Path, tmp_path: Path):
    envelope = {"request_id": "req-no-version",
                "capability": "capture.create",
                "payload": {"text": "no version"}}
    payload_file = tmp_path / "envelope.json"
    payload_file.write_text(json.dumps(envelope), encoding="utf-8")
    result = subprocess.run(
        [sys.executable,
         str(Path(__file__).resolve().parent.parent / "tools" / "los.py"),
         "--root", str(mini_repo), "capability", "capture.create",
         "--payload-file", str(payload_file)],
        capture_output=True, text=True, timeout=120)
    assert result.returncode == 2
    assert result.stdout == "", "a refused envelope must print no response"
    assert ("invalid capability envelope: schema_version 2 required "
            "(WORKFLOWS §25c)") in result.stderr


def test_guard_derivation_intercepts_every_commit_path(mini_repo: Path,
                                                       monkeypatch):
    """A handler that commits through its own TransactionService import is
    still stopped at the boundary.

    The AI delivery path constructs ``TransactionService`` from its own
    import rather than through ``support._write_transaction``. Intercepting
    one module's name would let such a handler reach the real ``commit``
    with the dry run's placeholder approval; the class-level boundary must
    capture it like any other.
    """
    import seal_envelope

    import los
    from learning_os.store import transactions

    real_build_parser = los.build_parser
    real_commit = transactions.TransactionService.commit

    def direct_commit_handler(args):
        probe = Path(args.root) / "work/inbox/direct-commit-probe.md"
        transactions.TransactionService(Path(args.root)).commit(
            capability="stage.note.write",
            writes={probe: "direct-commit probe\n"},
            artifact_ids=["unit-demo-l01"])
        return 0

    def build_parser():
        parser = real_build_parser()
        from learning_os.store.contracts.payloads import subparsers
        subparsers(parser)["stage-note"].set_defaults(func=direct_commit_handler)
        return parser

    monkeypatch.setattr(los, "build_parser", build_parser)
    before = canonical_fingerprint(mini_repo)
    receipts = sorted((mini_repo / "operations/transactions").glob("transaction-*.yaml"))

    snapshot, derived = seal_envelope._derive_guards_auto(
        mini_repo, capability="stage.note.write",
        payload={"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                 "text": "direct-commit probe"},
        key="guards-auto-direct-001", request_id="request-guards-auto-direct-001",
        channel="operator", approval_kind="operator-approval", snapshot=None)

    assert derived == {"unit-demo-l01": 0}
    assert snapshot == f"sha256:{before}"
    assert canonical_fingerprint(mini_repo) == before
    assert sorted((mini_repo / "operations/transactions").glob(
        "transaction-*.yaml")) == receipts
    assert not (mini_repo / "work/inbox/direct-commit-probe.md").exists()
    assert transactions.TransactionService.commit is real_commit


def test_seal_session_id_lands_in_the_approved_envelope(mini_repo: Path, tmp_path: Path):
    """#110: `--session-id` seals the session and still commits first try."""
    from repo_builders import add_curriculum

    from learning_os.store import session_ledger as plumbing_support
    from learning_os.store.contracts.gateway import intent_sha256

    add_curriculum(mini_repo)
    out = tmp_path / "sealed.json"
    sealed = _seal(mini_repo, out, capability="capture.create",
                   payload={"text": "sealed session capture"},
                   key="seal-session-001", extra=["--session-id", "sealed-agent"])
    assert sealed.returncode == 0, sealed.stderr
    envelope = json.loads(out.read_text(encoding="utf-8"))
    assert envelope["session_id"] == "sealed-agent"
    assert envelope["approval"]["subject_sha256"] == intent_sha256(envelope)

    submitted = _submit(mini_repo, out)
    assert submitted.returncode == 0, submitted.stderr or submitted.stdout
    captured = json.loads(submitted.stdout)["result"]["captured"]
    recorded = plumbing_support.load_session_paths(mini_repo, "sealed-agent")
    assert captured in recorded


def test_seal_blank_session_id_is_refused(mini_repo: Path, tmp_path: Path):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    out = tmp_path / "sealed-blank.json"
    sealed = _seal(mini_repo, out, capability="capture.create",
                   payload={"text": "blank session capture"},
                   key="seal-session-blank", extra=["--session-id", "   "])
    assert sealed.returncode == 2
    assert "must name a session" in sealed.stderr
    assert not out.exists()


def test_registered_guards_auto_pins_read_costs(
        mini_repo: Path, tmp_path: Path, monkeypatch, capsys):
    """F4 (registered path): the converted seal reads via the pipeline check.

    stage.note.write is registered, so the public selector
    (``seal_envelope.main --guards auto``) derives through
    ``_derive_registered_guards``: one live snapshot walk shared through
    the check context's cache (``ctx.snapshot_id()`` supplies both the
    seal token and the check record), the handler's single live load for
    its planner, one shadow load staging the proposal, and exactly one
    validation per the check contract (``check_proposal`` "Exactly one
    validate call" -> ``validate`` -> one ``Validator.run``).

    Legacy derivation is patched to fail: a selector regression routing
    this converted operation to ``_derive_guards_auto`` fails here.
    Unpatched, that routing crashes the seal with ``AttributeError:
    _operation`` (the stale-test failure this repair replaces), so the
    mutant cannot silently succeed.

    The one-walk pin is the SPEC (co) proof: a restored duplicate walk
    (the record re-walking instead of reusing the cached token) reads
    ``walks == 2`` and fails here. An explicit caller snapshot never
    seeds the cache, so the record keeps its independent walk on that
    path; this test covers the default read-live path.
    """
    import functools

    import seal_envelope
    from repo_builders import material_fixture

    import learning_os.store.fingerprint as fingerprint_module
    import learning_os.store.loader as loader_module
    from learning_os.derive.validation.core import Validator

    material_fixture(mini_repo)
    before = canonical_fingerprint(mini_repo)
    tree_before = {path for path in mini_repo.rglob("*")}
    live = mini_repo.resolve()
    counts = {"load_repo": 0, "live_loads": 0, "shadow_loads": 0,
              "walks": 0, "live_walks": 0, "validate": 0}
    original_load = loader_module.load_repo
    original_roots = fingerprint_module._fingerprint_roots
    original_cds = fingerprint_module.canonical_data_and_stat_fingerprints
    original_validate = Validator.run

    @functools.wraps(original_validate)
    def counted_validate(self, *args, **kwargs):
        counts["validate"] += 1
        return original_validate(self, *args, **kwargs)

    @functools.wraps(original_roots)
    def counted_roots(root, *args, **kwargs):
        counts["walks"] += 1
        if Path(root).resolve() == live:
            counts["live_walks"] += 1
        return original_roots(root, *args, **kwargs)

    @functools.wraps(original_cds)
    def counted_cds(root, *args, **kwargs):
        counts["walks"] += 1
        if Path(root).resolve() == live:
            counts["live_walks"] += 1
        return original_cds(root, *args, **kwargs)

    @functools.wraps(original_load)
    def counted_load(root, *args, **kwargs):
        counts["load_repo"] += 1
        if Path(root).resolve() == live:
            counts["live_loads"] += 1
        else:
            counts["shadow_loads"] += 1
        return original_load(root, *args, **kwargs)

    monkeypatch.setattr(Validator, "run", counted_validate)
    monkeypatch.setattr(fingerprint_module, "_fingerprint_roots",
                        counted_roots)
    monkeypatch.setattr(fingerprint_module,
                        "canonical_data_and_stat_fingerprints", counted_cds)
    # Every consumer binds load_repo by name at import; rebind each one.
    # An earlier counting test in this file may have left its own counter
    # bound in a module imported mid-test (monkeypatch restores only what
    # it patched), so reclaim one stale functools.wraps layer as well.
    for module in list(sys.modules.values()):
        current = getattr(module, "load_repo", None)
        if current is original_load or getattr(
                current, "__wrapped__", None) is original_load:
            monkeypatch.setattr(module, "load_repo", counted_load)

    def legacy_must_not_run(*args, **kwargs):
        raise AssertionError(
            "public selector routed a registered operation "
            "to legacy derivation")

    monkeypatch.setattr(seal_envelope, "_derive_guards_auto",
                        legacy_must_not_run)

    out = tmp_path / "sealed.json"
    code = seal_envelope.main([
        "--root", str(mini_repo), "--capability", "stage.note.write",
        "--payload", json.dumps({"unit_id": "unit-demo-l01",
                                 "stage_id": "stage-demo",
                                 "text": "A counted note"}),
        "--key", "guards-auto-once-001", "--guards", "auto",
        "--out", str(out)])
    captured = capsys.readouterr()
    assert code == 0, captured.err
    assert "guards auto:" in captured.err
    envelope = json.loads(out.read_text(encoding="utf-8"))
    assert envelope["expected_snapshot"] == f"sha256:{before}"
    assert envelope["expected_revisions"] == {"unit-demo-l01": 0}
    assert counts["live_loads"] == 1, counts
    assert counts["shadow_loads"] == 1, counts
    assert counts["load_repo"] == 2, counts
    assert counts["walks"] == 1, counts
    assert counts["live_walks"] == 1, counts
    assert counts["validate"] == 1, counts
    assert canonical_fingerprint(mini_repo) == before
    assert {path for path in mini_repo.rglob("*")} == tree_before


def test_public_selector_routes_converted_stage_note_write(
        mini_repo: Path, tmp_path: Path, monkeypatch, capsys):
    """A converted seal succeeds through the public selector, never legacy.

    stage.note.write is registered: ``seal_envelope.main --guards auto``
    must derive through ``_derive_registered_guards`` and the sealed
    envelope must commit on the first submission. Legacy derivation is
    patched to fail, so any routing regression fails this test.
    """
    import seal_envelope
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)

    def legacy_must_not_run(*args, **kwargs):
        raise AssertionError(
            "public selector routed a registered operation "
            "to legacy derivation")

    monkeypatch.setattr(seal_envelope, "_derive_guards_auto",
                        legacy_must_not_run)

    out = tmp_path / "sealed.json"
    code = seal_envelope.main([
        "--root", str(mini_repo), "--capability", "stage.note.write",
        "--payload", json.dumps({"unit_id": "unit-demo-l01",
                                 "stage_id": "stage-demo",
                                 "text": "selector probe note"}),
        "--key", "guards-auto-selector-001", "--guards", "auto",
        "--out", str(out)])
    assert code == 0, capsys.readouterr().err
    applied = _submit(mini_repo, out)
    assert applied.returncode == 0, applied.stdout + applied.stderr
    body = json.loads(applied.stdout)
    assert body["ok"] is True, body
    assert body["replayed"] is False


def test_public_module_plan_guards_auto_preserves_guard_derivation(
        mini_repo: Path, tmp_path: Path, monkeypatch, capsys):
    """The Phase 4 module-plan seal uses the registered public selector.

    The proposal check walks once and validates its shadow once. The
    live planner load and synthesis-destination resolution stay bounded,
    and guard derivation changes no canonical file.
    Calling the retired legacy derivation for this converted operation
    would test an unreachable Phase 3 route instead of current behavior.
    """
    import functools
    import sys

    import seal_envelope
    import yaml
    from repo_builders import add_curriculum

    import learning_os.store.fingerprint as fingerprint_module
    import learning_os.store.loader as loader_module
    from learning_os.derive.validation.core import Validator

    add_curriculum(mini_repo)
    audit_rel = "work/active/workspace-demo/outputs/demo-coverage-audit.md"
    audit = mini_repo / audit_rel
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text(
        "# Complete demo coverage audit\n\n## Local inventory\n\nDone.\n\n"
        "## Linked inventory\n\nDone.\n\n## Completeness sign-off\n\nDone.\n",
        encoding="utf-8",
    )
    package = tmp_path / "module-plan.yaml"
    package.write_text(
        yaml.safe_dump(
            {
                "module_id": "module-demo",
                "plan_contract": {
                    "version": 2,
                    "plan_template_version": 1,
                    "coverage_audit": audit_rel,
                    "checks": {
                        "local_inventory_complete": True,
                        "linked_inventory_complete": True,
                        "materials_opened_and_content_checked": True,
                        "current_and_prior_scope_reconciled": True,
                        "duplicates_and_numbering_checked": True,
                        "exclusions_and_unresolved_gaps_recorded": True,
                    },
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    before = canonical_fingerprint(mini_repo)
    tree_before = {path for path in mini_repo.rglob("*")}
    counts = {"load_repo": 0, "live_loads": 0, "shadow_loads": 0, "walks": 0, "validate": 0}

    def counted(key, function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            counts[key] += 1
            if key == "load_repo":
                side = ("live_loads" if Path(args[0]).resolve() == mini_repo.resolve()
                        else "shadow_loads")
                counts[side] += 1
            return function(*args, **kwargs)

        return wrapper

    monkeypatch.setattr(Validator, "run", counted("validate", Validator.run))
    monkeypatch.setattr(fingerprint_module, "_fingerprint_roots",
                        counted("walks", fingerprint_module._fingerprint_roots))
    monkeypatch.setattr(fingerprint_module, "canonical_data_and_stat_fingerprints",
                        counted("walks", fingerprint_module.canonical_data_and_stat_fingerprints))
    # Every consumer binds load_repo by name at import; rebind each one.
    # An earlier counting test in this file may have left its own counter
    # bound in a module imported mid-test (monkeypatch restores only what
    # it patched), so reclaim one stale functools.wraps layer as well.
    original_load = loader_module.load_repo
    load_counter = counted("load_repo", original_load)
    for module in list(sys.modules.values()):
        current = getattr(module, "load_repo", None)
        if current is original_load or getattr(
                current, "__wrapped__", None) is original_load:
            monkeypatch.setattr(module, "load_repo", load_counter)

    def legacy_must_not_run(*args, **kwargs):
        raise AssertionError("converted module.plan.import reached legacy sealing")

    monkeypatch.setattr(seal_envelope, "_derive_guards_auto", legacy_must_not_run)
    out = tmp_path / "sealed.json"
    code = seal_envelope.main([
        "--root", str(mini_repo), "--capability", "module.plan.import",
        "--payload", json.dumps({"module_id": "module-demo", "file": str(package),
                                 "file_sha256": file_sha256(package)}),
        "--key", "guards-auto-module-plan-once-001", "--guards", "auto",
        "--out", str(out)])
    captured = capsys.readouterr()
    assert code == 0, captured.err
    assert "guards auto:" in captured.err
    envelope = json.loads(out.read_text(encoding="utf-8"))
    assert envelope["expected_snapshot"] == f"sha256:{before}"
    assert envelope["expected_revisions"] == {"module-demo": 0}
    # The second live load resolves the synthesis destination of the unit.
    assert counts["live_loads"] == 2, counts
    assert counts["shadow_loads"] == 1, counts
    assert counts["load_repo"] == 3, counts
    assert counts["walks"] == 1, counts
    assert counts["validate"] == 1, counts
    assert canonical_fingerprint(mini_repo) == before
    assert {path for path in mini_repo.rglob("*")} == tree_before


# ---------------------------------------------------------------------------
# File-guard sealing (SPEC (cr)): inbox.resolve declares no artifact ids,
# so the registered seal must derive its file: guards. Before this repair
# the sealed envelope carried an empty revision map and the first
# submission refused with the exact-coverage INVALID_REQUEST (Task62's
# process-inbox evidence). The seal/check itself writes nothing.
# ---------------------------------------------------------------------------

def _inbox_drop_payload(mini_repo: Path, name: str = "note-drop.md"):
    """A real routed drop plus its seal payload, year, and raw bytes."""
    import datetime

    drop = mini_repo / "work/inbox" / name
    data = b"# Drop\n\nRouted.\n"
    drop.write_bytes(data)
    year = str(datetime.date.today().year)
    payload = {"name": name, "drop_sha256": file_sha256(drop),
               "routed_to": ["note-demo"]}
    return payload, data, year


def test_inbox_resolve_seal_derives_file_guards_and_first_submit_commits(
        mini_repo: Path, tmp_path: Path, monkeypatch, capsys):
    """Registered inbox.resolve: exact file guards seal, first submit lands."""
    import seal_envelope
    import yaml

    payload, data, year = _inbox_drop_payload(mini_repo)
    inbox_guard = f"file:work/inbox/{payload['name']}"
    archive_guard = f"file:archive/inbox/{year}/{payload['name']}"
    before = canonical_fingerprint(mini_repo)
    tree_before = {path for path in mini_repo.rglob("*")}

    def legacy_must_not_run(*args, **kwargs):
        raise AssertionError(
            "public selector routed a registered operation "
            "to legacy derivation")

    monkeypatch.setattr(seal_envelope, "_derive_guards_auto",
                        legacy_must_not_run)
    out = tmp_path / "sealed.json"
    code = seal_envelope.main([
        "--root", str(mini_repo), "--capability", "inbox.resolve",
        "--payload", json.dumps(payload), "--key", "guards-auto-inbox-001",
        "--guards", "auto", "--out", str(out)])
    captured = capsys.readouterr()
    assert code == 0, captured.err
    assert "guards auto:" in captured.err
    envelope = json.loads(out.read_text(encoding="utf-8"))
    assert envelope["expected_snapshot"] == f"sha256:{before}"
    assert envelope["expected_revisions"] == {inbox_guard: 0,
                                              archive_guard: 0}
    assert canonical_fingerprint(mini_repo) == before
    assert {path for path in mini_repo.rglob("*")} == tree_before
    assert not list(
        (mini_repo / "operations/transactions").glob("transaction-*.yaml"))

    applied = _submit(mini_repo, out)
    assert applied.returncode == 0, applied.stdout + applied.stderr
    body = json.loads(applied.stdout)
    assert body["ok"] is True, body
    assert body["replayed"] is False
    assert body["transaction_id"] is not None
    assert body["result"]["resolved"] == payload["name"]
    assert body["result"]["archived"] == [
        f"archive/inbox/{year}/{payload['name']}"]
    assert not (mini_repo / "work/inbox" / payload["name"]).exists()
    archived = mini_repo / f"archive/inbox/{year}/{payload['name']}"
    assert archived.read_bytes() == data
    receipt = yaml.safe_load(
        (mini_repo / body["receipt_path"]).read_text(encoding="utf-8"))
    assert sorted(row["path"] for row in receipt["writes"]) == sorted([
        f"archive/inbox/{year}/{payload['name']}",
        f"work/inbox/{payload['name']}"])
    assert receipt["expected_revisions"] == {inbox_guard: 0,
                                             archive_guard: 0}
    assert receipt["artifact_revisions"] == {
        inbox_guard: {"before": 0, "after": 1},
        archive_guard: {"before": 0, "after": 1},
    }
    assert receipt["metadata"]["routed_to"] == ["note-demo"]


def test_inbox_resolve_explicit_revision_wins_over_a_derived_file_guard(
        mini_repo: Path, tmp_path: Path):
    """An explicit --revision overrides one derived file guard, keeps cover."""
    payload, _, year = _inbox_drop_payload(mini_repo)
    inbox_guard = f"file:work/inbox/{payload['name']}"
    archive_guard = f"file:archive/inbox/{year}/{payload['name']}"
    out = tmp_path / "sealed.json"
    sealed = _seal(mini_repo, out, capability="inbox.resolve",
                   payload=payload, key="guards-auto-inbox-002",
                   extra=["--revision", f"{inbox_guard}=99"])
    assert sealed.returncode == 0, sealed.stderr
    envelope = json.loads(out.read_text(encoding="utf-8"))
    assert envelope["expected_revisions"][inbox_guard] == 99
    assert envelope["expected_revisions"][archive_guard] == 0
    applied = _submit(mini_repo, out)
    assert applied.returncode == 3, applied.stdout
    assert json.loads(applied.stdout)["error"]["code"] == "REVISION_CONFLICT"
    assert (mini_repo / "work/inbox" / payload["name"]).is_file()


def test_inbox_resolve_sealed_envelope_still_refuses_a_stale_snapshot(
        mini_repo: Path, tmp_path: Path):
    """A concurrent canonical write still stale-refuses the sealed envelope."""
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    payload, _, _ = _inbox_drop_payload(mini_repo)
    out = tmp_path / "first.json"
    sealed = _seal(mini_repo, out, capability="inbox.resolve",
                   payload=payload, key="guards-auto-inbox-003")
    assert sealed.returncode == 0, sealed.stderr
    concurrent = _seal(mini_repo, tmp_path / "concurrent.json",
                       capability="capture.create",
                       payload={"text": "concurrent write"},
                       key="guards-auto-inbox-004")
    assert concurrent.returncode == 0, concurrent.stderr
    applied = _submit(mini_repo, tmp_path / "concurrent.json")
    assert applied.returncode == 0, applied.stdout
    assert json.loads(applied.stdout)["ok"] is True
    stale = _submit(mini_repo, out)
    assert stale.returncode == 3, stale.stdout
    body = json.loads(stale.stdout)
    assert body["ok"] is False
    assert body["error"]["code"] == "STALE_SNAPSHOT"
    assert (mini_repo / "work/inbox" / payload["name"]).is_file()


def test_inbox_resolve_envelope_missing_a_file_guard_still_refuses(
        mini_repo: Path, tmp_path: Path):
    """Dropping one sealed file guard still trips the exact-coverage guard."""
    from learning_os.store.contracts.gateway import intent_sha256

    payload, _, year = _inbox_drop_payload(mini_repo)
    inbox_guard = f"file:work/inbox/{payload['name']}"
    archive_guard = f"file:archive/inbox/{year}/{payload['name']}"
    out = tmp_path / "sealed.json"
    sealed = _seal(mini_repo, out, capability="inbox.resolve",
                   payload=payload, key="guards-auto-inbox-005")
    assert sealed.returncode == 0, sealed.stderr
    envelope = json.loads(out.read_text(encoding="utf-8"))
    assert envelope["expected_revisions"] == {inbox_guard: 0,
                                              archive_guard: 0}
    del envelope["expected_revisions"][archive_guard]
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(envelope), encoding="utf-8")
    applied = _submit(mini_repo, tampered)
    assert applied.returncode == 2, applied.stdout
    body = json.loads(applied.stdout)
    assert body["ok"] is False
    assert body["error"]["code"] == "INVALID_REQUEST"
    assert "must cover exactly every transaction artifact" in body["error"]["message"]
    assert archive_guard in body["error"]["message"]
    assert (mini_repo / "work/inbox" / payload["name"]).is_file()


# One call per intent (agent-cost PLAN D1/B1): `seal_envelope.py --submit`
# seals through the same guard derivation as `--guards auto` and submits the
# envelope itself. The staged-shadow check is skipped, because the commit
# validates the real tree once.
def _one_call(root: Path, *, capability: str, payload: dict, key: str,
              extra: list[str] | None = None):
    command = [sys.executable, str(SEAL), "--root", str(root),
               "--capability", capability, "--payload", json.dumps(payload),
               "--key", key, "--submit"]
    command.extend(extra or [])
    return subprocess.run(command, capture_output=True, text=True, timeout=120)


def _receipts(root: Path) -> list[Path]:
    return sorted((root / "operations/transactions").glob("transaction-*.yaml"))


@pytest.mark.parametrize("capability,key,payload", FIRST_SUBMISSION_CASES,
                         ids=[case[0] for case in FIRST_SUBMISSION_CASES])
def test_one_call_write_commits_without_a_hand_built_envelope(
        mini_repo: Path, tmp_path: Path, capability: str, key: str,
        payload: dict | None):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    if payload is None:  # stage.attachment.add needs a real approved file
        source = tmp_path / "attachment.txt"
        source.write_text("one-call attachment bytes", encoding="utf-8")
        payload = {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
                   "file": str(source), "file_sha256": file_sha256(source),
                   "label": "auto"}
    applied = _one_call(mini_repo, capability=capability, payload=payload,
                        key=f"{key}-one-call")
    assert applied.returncode == 0, applied.stdout + applied.stderr
    body = json.loads(applied.stdout)
    assert body["ok"] is True, body
    assert body["replayed"] is False


def test_one_call_retry_replays_and_a_new_payload_under_the_key_conflicts(
        mini_repo: Path):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    payload = {"text": "captured once, retried after a lost response"}
    first = _one_call(mini_repo, capability="capture.create", payload=payload,
                      key="one-call-retry-001")
    assert first.returncode == 0, first.stdout + first.stderr
    receipts = _receipts(mini_repo)
    retry = _one_call(mini_repo, capability="capture.create", payload=payload,
                      key="one-call-retry-001")
    assert retry.returncode == 0, retry.stdout + retry.stderr
    first_body, retry_body = json.loads(first.stdout), json.loads(retry.stdout)
    assert retry_body["replayed"] is True
    assert retry_body["transaction_id"] == first_body["transaction_id"]
    assert _receipts(mini_repo) == receipts
    other = _one_call(mini_repo, capability="capture.create",
                      payload={"text": "a different capture"},
                      key="one-call-retry-001")
    assert other.returncode != 0, other.stdout
    assert json.loads(other.stdout)["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert _receipts(mini_repo) == receipts


def test_one_call_refusal_leaves_the_key_free_for_a_corrected_retry(
        mini_repo: Path):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    refused = _one_call(mini_repo, capability="stage.progress.update",
                        payload={"unit_id": "unit-demo-l01",
                                 "stage_id": "stage-demo", "status": "done"},
                        key="one-call-corrected-001")
    assert refused.returncode == 2
    assert "invalid payload" in refused.stderr
    corrected = _one_call(mini_repo, capability="stage.progress.update",
                          payload={"unit_id": "unit-demo-l01",
                                   "stage_id": "stage-demo", "status": "active"},
                          key="one-call-corrected-001")
    assert corrected.returncode == 0, corrected.stdout + corrected.stderr
    assert json.loads(corrected.stdout)["ok"] is True


@pytest.mark.parametrize("extra", [
    ["--revision", "unit-demo-l01=0"], ["--snapshot", "sha256:" + "0" * 64],
    ["--out", "/tmp/x.json"],
])
def test_one_call_refuses_a_second_source_for_a_derived_fact(
        mini_repo: Path, extra: list[str]):
    refused = _one_call(mini_repo, capability="capture.create",
                        payload={"text": "explicit guard"},
                        key="one-call-explicit-001", extra=extra)
    assert refused.returncode == 2
    assert "--submit derives its own guards" in refused.stderr
    assert _receipts(mini_repo) == []


# The seal fills the digest of every file a byte-bound field names
# (agent-cost D3), so an operator write needs no hand-run sha256sum, and a
# reviewed write is two calls: --check-out for the review, then --guards-from
# with --submit, which seals with the reviewed guards and the reviewed bytes.
def _attachment_payload(tmp_path: Path, text: str = "reviewed attachment bytes") -> dict:
    source = tmp_path / "attachment.txt"
    source.write_text(text, encoding="utf-8")
    return {"unit_id": "unit-demo-l01", "stage_id": "stage-demo",
            "file": str(source), "label": "reviewed"}


def test_one_call_binds_a_named_file_to_its_bytes(mini_repo: Path, tmp_path: Path):
    from repo_builders import add_curriculum

    from learning_os.store.session_ledger import sealed_request_path

    add_curriculum(mini_repo)
    payload = _attachment_payload(tmp_path)
    applied = _one_call(mini_repo, capability="stage.attachment.add",
                        payload=payload, key="one-call-digest-001")
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert "bound file_sha256 to the bytes of" in applied.stderr
    sealed = json.loads(sealed_request_path(mini_repo, "one-call-digest-001")
                        .read_text(encoding="utf-8"))
    assert sealed["payload"]["file_sha256"] == file_sha256(Path(payload["file"]))
    retry = _one_call(mini_repo, capability="stage.attachment.add",
                      payload=payload, key="one-call-digest-001")
    assert json.loads(retry.stdout)["replayed"] is True


def test_reviewed_write_is_two_calls_and_applies_the_reviewed_bytes(
        mini_repo: Path, tmp_path: Path):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    payload = _attachment_payload(tmp_path)
    record = tmp_path / "review.json"
    reviewed = _seal(mini_repo, tmp_path / "unused.json",
                     capability="stage.attachment.add", payload=payload,
                     key="reviewed-two-call-001", extra=["--check-out", str(record)])
    assert reviewed.returncode == 0, reviewed.stderr
    assert json.loads(record.read_text(encoding="utf-8"))["ok"] is True
    source = Path(payload["file"])
    source.write_text("bytes nobody reviewed", encoding="utf-8")
    changed = _one_call(mini_repo, capability="stage.attachment.add", payload=payload,
                        key="reviewed-two-call-001", extra=["--guards-from", str(record)])
    assert changed.returncode == 2
    assert "record payload differs from the sealing payload" in changed.stderr
    assert _receipts(mini_repo) == []
    source.write_text("reviewed attachment bytes", encoding="utf-8")
    applied = _one_call(mini_repo, capability="stage.attachment.add", payload=payload,
                        key="reviewed-two-call-001", extra=["--guards-from", str(record)])
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert json.loads(applied.stdout)["ok"] is True
    assert len(_receipts(mini_repo)) == 1


def test_reviewed_write_refuses_a_tree_that_moved_since_the_review(
        mini_repo: Path, tmp_path: Path):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    payload = _attachment_payload(tmp_path)
    record = tmp_path / "review.json"
    reviewed = _seal(mini_repo, tmp_path / "unused.json",
                     capability="stage.attachment.add", payload=payload,
                     key="reviewed-stale-001", extra=["--check-out", str(record)])
    assert reviewed.returncode == 0, reviewed.stderr
    moved = _one_call(mini_repo, capability="capture.create",
                      payload={"text": "lands after the review"}, key="reviewed-stale-move")
    assert moved.returncode == 0, moved.stdout + moved.stderr
    stale = _one_call(mini_repo, capability="stage.attachment.add", payload=payload,
                      key="reviewed-stale-001", extra=["--guards-from", str(record)])
    assert stale.returncode != 0
    assert json.loads(stale.stdout)["error"]["code"] == "STALE_SNAPSHOT"


# Two callers can use one key, by accident: agents copy documented example
# keys. Each attempt is sealed into a file of its own, and only the attempt
# that committed becomes the key's retry file, so neither a refused attempt
# nor a concurrent one can change what was, or is being, committed.
def _inbox_texts(root: Path) -> str:
    return "\n".join(path.read_text(encoding="utf-8")
                     for path in sorted((root / "work/inbox").glob("*.md")))


def test_a_conflicting_reuse_of_a_key_keeps_the_committed_retry(mini_repo: Path):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    first = {"text": "capture A, committed first"}
    committed = _one_call(mini_repo, capability="capture.create", payload=first,
                          key="one-call-reused-001")
    assert committed.returncode == 0, committed.stdout + committed.stderr
    reused = _one_call(mini_repo, capability="capture.create",
                       payload={"text": "capture B, same key by accident"},
                       key="one-call-reused-001")
    assert json.loads(reused.stdout)["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    retry = _one_call(mini_repo, capability="capture.create", payload=first,
                      key="one-call-reused-001")
    assert retry.returncode == 0, retry.stdout + retry.stderr
    body = json.loads(retry.stdout)
    assert body["replayed"] is True
    assert body["transaction_id"] == json.loads(committed.stdout)["transaction_id"]
    assert len(_receipts(mini_repo)) == 1


def test_a_concurrent_seal_under_the_key_cannot_change_what_commits(
        mini_repo: Path, monkeypatch, capsys):
    import seal_envelope
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    original_seal = seal_envelope._seal_with_key
    other = {"text": "capture B, sealed while A was in flight"}

    def seal_then_another_caller_seals(root, **kwargs):
        sealed = original_seal(root, **kwargs)
        original_seal(root, **{**kwargs, "payload": other, "request_id": None})
        return sealed

    monkeypatch.setattr(seal_envelope, "_seal_with_key", seal_then_another_caller_seals)
    capsys.readouterr()
    assert seal_envelope.main([
        "--root", str(mini_repo), "--capability", "capture.create",
        "--payload", json.dumps({"text": "capture A, the one submitted"}),
        "--key", "one-call-concurrent-001", "--submit"]) == 0
    monkeypatch.setattr(seal_envelope, "_seal_with_key", original_seal)
    assert "capture A, the one submitted" in _inbox_texts(mini_repo)
    assert "capture B" not in _inbox_texts(mini_repo)
    late = _one_call(mini_repo, capability="capture.create", payload=other,
                     key="one-call-concurrent-001")
    assert json.loads(late.stdout)["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    assert len(_receipts(mini_repo)) == 1


def test_a_commit_whose_attempt_was_never_settled_still_replays(
        mini_repo: Path, monkeypatch, capsys):
    """A crash after the commit, before the attempt became the retry file."""
    import seal_envelope
    from repo_builders import add_curriculum

    from learning_os.store.session_ledger import sealed_request_path

    add_curriculum(mini_repo)
    payload = {"text": "committed, then the process died"}
    monkeypatch.setattr(seal_envelope, "_settle_attempt", lambda *args: None)
    capsys.readouterr()
    assert seal_envelope.main([
        "--root", str(mini_repo), "--capability", "capture.create",
        "--payload", json.dumps(payload), "--key", "one-call-crash-001", "--submit"]) == 0
    first = json.loads(capsys.readouterr().out)
    assert not sealed_request_path(mini_repo, "one-call-crash-001").exists()
    monkeypatch.undo()
    retry = _one_call(mini_repo, capability="capture.create", payload=payload,
                      key="one-call-crash-001")
    assert retry.returncode == 0, retry.stdout + retry.stderr
    body = json.loads(retry.stdout)
    assert body["replayed"] is True
    assert body["transaction_id"] == first["transaction_id"]
    assert sealed_request_path(mini_repo, "one-call-crash-001").is_file()


def test_one_call_write_validates_once_and_a_moved_snapshot_is_stale(
        mini_repo: Path, monkeypatch, capsys):
    """Seal plus commit run the validator once, not twice (PLAN D4/A5).

    The guards still bind the snapshot sealed in process: a canonical write
    that lands between the seal and the commit refuses as STALE_SNAPSHOT,
    and the same key then seals afresh, because nothing committed under it.
    """
    import functools

    import seal_envelope
    from repo_builders import add_curriculum

    from learning_os.derive.validation.core import Validator

    add_curriculum(mini_repo)
    calls = {"validate": 0}
    original_validate = Validator.run

    @functools.wraps(original_validate)
    def counted_validate(self, *args, **kwargs):
        calls["validate"] += 1
        return original_validate(self, *args, **kwargs)

    monkeypatch.setattr(Validator, "run", counted_validate)

    def invoke(key: str) -> int:
        return seal_envelope.main([
            "--root", str(mini_repo), "--capability", "capture.create",
            "--payload", json.dumps({"text": f"counted capture {key}"}),
            "--key", key, "--submit"])

    assert invoke("one-call-count-001") == 0
    assert calls["validate"] == 1, calls

    original_seal = seal_envelope._seal_with_key

    def seal_then_race(root, **kwargs):
        envelope = original_seal(root, **kwargs)
        raced = _one_call(mini_repo, capability="garden.seed.create",
                          payload={"text": "landed between seal and commit"},
                          key="one-call-race-001")
        assert raced.returncode == 0, raced.stdout + raced.stderr
        return envelope

    monkeypatch.setattr(seal_envelope, "_seal_with_key", seal_then_race)
    capsys.readouterr()
    assert invoke("one-call-stale-001") == 3
    assert json.loads(capsys.readouterr().out)["error"]["code"] == "STALE_SNAPSHOT"
    monkeypatch.setattr(seal_envelope, "_seal_with_key", original_seal)
    assert invoke("one-call-stale-001") == 0


def test_one_call_reports_what_the_commit_validated(mini_repo: Path):
    """The write's own validation is the acceptance check (PLAN D4).

    The JSON result is unchanged; one stderr line reports the commit's own
    validation, so the agent does not run validate.py and the baseline check
    on the same state again. A replay validated nothing and says so.
    """
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    payload = {"text": "a capture whose validation is reported"}
    first = _one_call(mini_repo, capability="capture.create", payload=payload,
                      key="one-call-report-001")
    assert first.returncode == 0, first.stdout + first.stderr
    assert "seal_envelope: validation: 0 error(s)" in first.stderr
    assert "no new warning signature" in first.stderr
    assert "validation" not in json.loads(first.stdout)["result"]
    replay = _one_call(mini_repo, capability="capture.create", payload=payload,
                       key="one-call-report-001")
    assert replay.returncode == 0, replay.stdout + replay.stderr
    assert "validation: none ran in this call" in replay.stderr


@pytest.mark.parametrize("proved,expected", [
    ({"errors": 0, "warnings": 3, "new_warning_signatures": []},
     "no new warning signature"),
    ({"errors": 0, "warnings": 4, "new_warning_signatures": ["W-CODE at a.md (+1)"]},
     "NEW warning signature(s): W-CODE at a.md (+1)"),
    ({"errors": 0, "warnings": 3, "new_warning_signatures": None},
     "the warning baseline is unreadable"),
    (None, "none ran in this call"),
])
def test_validation_line_names_every_outcome(proved, expected):
    import seal_envelope

    assert expected in seal_envelope._validation_line(proved)

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

from learning_os.fingerprint import canonical_fingerprint

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
    from learning_os import transactions

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
        from learning_os.contracts.payloads import subparsers
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

    from learning_os.contracts.gateway import intent_sha256
    from learning_os.ops import _legacy_plumbing as plumbing_support

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
    recorded = plumbing_support._load_session_paths(mini_repo, "sealed-agent")
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

    import learning_os.fingerprint as fingerprint_module
    import learning_os.loader as loader_module
    from learning_os.rules.core import Validator

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


def test_legacy_guards_auto_reads_the_live_tree_once(
        mini_repo: Path, tmp_path: Path, monkeypatch):
    """F4 (legacy branch): an unregistered seal loads once and walks once.

    module.plan.import is a permanent Phase3 deferral (SPEC (bs) item 5:
    it converts with the transport adapter in PLAN 4.1, unlike
    workspace.next-action.update, which the final wave converts), so it
    takes the legacy dry-run path: the seal's bare snapshot walk plus
    the handler's single load, with no validation (interception stops at
    the transaction boundary before any check). Preserves the original
    zero-validation invariant on a real capability and fixture.
    """
    import functools
    import sys

    import seal_envelope
    import yaml
    from repo_builders import add_curriculum

    import learning_os.fingerprint as fingerprint_module
    import learning_os.loader as loader_module
    from learning_os.rules.core import Validator

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
    counts = {"load_repo": 0, "walks": 0, "validate": 0}

    def counted(key, function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            counts[key] += 1
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

    snapshot, derived = seal_envelope._derive_guards_auto(
        mini_repo, capability="module.plan.import",
        payload={"module_id": "module-demo", "file": str(package),
                 "file_sha256": file_sha256(package)},
        key="guards-auto-legacy-once-001",
        request_id="request-guards-auto-legacy-once-001",
        channel="operator", approval_kind="operator-approval", snapshot=None)

    assert snapshot == f"sha256:{before}"
    assert derived == {"module-demo": 0}
    assert counts["load_repo"] == 1, counts
    assert counts["walks"] == 1, counts
    assert counts["validate"] == 0, counts
    assert canonical_fingerprint(mini_repo) == before
    assert {path for path in mini_repo.rglob("*")} == tree_before

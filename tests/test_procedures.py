"""The A8 procedure index and transcript runner (SPEC §7.4, PLAN D11).

S08 chose Scrut. ``INDEX.yaml`` lists every ``## `` heading of
``system/WORKFLOWS.md`` and ``system/OPERATOR.md`` plus the ``## `` headings
of ``system/CLAUDE.md`` sections 2 and 7; every ``procedure`` entry needs an
existing transcript. Each ``system/procedures/*.md`` transcript runs as
``scrut test`` with ``LOS_REPO`` set; the binary path is configured through
``LOS_SCRUT_BIN`` (default: ``.venv/bin/scrut``, where ``make setup``
installs it — see BAKEOFF.md).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from collections import Counter
from pathlib import Path

import arch_audit_hook
import pytest
import yaml
from arch_writes_fixtures import witness_failures
from scenario_harness import (
    ARCH_SITE,
    check_render_purity_error,
    prepare_transcript_fixture,
    render_violations,
)

ROOT = Path(__file__).resolve().parents[1]
PROCEDURES = ROOT / "system" / "procedures"
INDEX_PATH = PROCEDURES / "INDEX.yaml"
RATCHETS_PATH = ROOT / "tests" / "architecture" / "ratchets.yaml"

CHECK_ID = "A8-transcripts"
FIX = "Update the transcript, or fix the doc command (PLAN D11)."
PROBE_OP = "test-only.probe"

#: The indexed docs and, for CLAUDE.md, the indexed section numbers.
INDEXED_DOCS = ("system/OPERATOR.md", "system/WORKFLOWS.md", "system/CLAUDE.md")
CLAUDE_SECTIONS = ("2", "7")


def _headings(doc: str) -> list[tuple[str, int]]:
    """Every ``## `` heading of one doc, with its 1-based line number."""
    lines = (ROOT / doc).read_text(encoding="utf-8").splitlines()
    found = [(line, number) for number, line in enumerate(lines, 1)
             if line.startswith("## ")]
    if doc == "system/CLAUDE.md":
        found = [(line, number) for line, number in found
                 if re.match(r"## ([0-9]+)\. ", line)
                 and re.match(r"## ([0-9]+)\. ", line).group(1)
                 in CLAUDE_SECTIONS]
    return found


def _load_index() -> list[dict]:
    data = yaml.safe_load(INDEX_PATH.read_text(encoding="utf-8"))
    assert data.get("schema") == 1, (
        f"A8 {INDEX_PATH.relative_to(ROOT)}:1: want schema 1 — {FIX}")
    sections = data.get("sections")
    assert isinstance(sections, list), (
        f"A8 {INDEX_PATH.relative_to(ROOT)}:1: want a sections list — {FIX}")
    return sections


def test_index_lists_every_heading():
    sections = _load_index()
    indexed: dict[tuple[str, str], dict] = {}
    failures = []
    for position, entry in enumerate(sections):
        if not isinstance(entry, dict):
            failures.append(
                f"A8 {INDEX_PATH.relative_to(ROOT)}: want a mapping at "
                f"sections[{position}] — {FIX}")
            continue
        doc, heading, classed = (entry.get("doc"), entry.get("heading"),
                                 entry.get("class"))
        if not isinstance(doc, str) or not isinstance(heading, str):
            failures.append(
                f"A8 {INDEX_PATH.relative_to(ROOT)}: sections[{position}] "
                f"needs string doc and heading — {FIX}")
            continue
        if classed not in ("procedure", "rule"):
            failures.append(
                f"A8 {doc}::{heading}: want class procedure|rule — "
                f"{INDEX_PATH.relative_to(ROOT)} sections[{position}] — {FIX}")
            continue
        if (doc, heading) in indexed:
            failures.append(
                f"A8 {doc}::{heading}: indexed twice — "
                f"{INDEX_PATH.relative_to(ROOT)} — {FIX}")
            continue
        indexed[(doc, heading)] = entry
    for doc in INDEXED_DOCS:
        for heading, lineno in _headings(doc):
            if (doc, heading) not in indexed:
                failures.append(
                    f"A8 {doc}::{heading}: heading not indexed — "
                    f"{doc}:{lineno} — {FIX}")
    for (doc, heading) in sorted(indexed):
        if heading not in [line for line, _ in _headings(doc)]:
            failures.append(
                f"A8 {doc}::{heading}: no such heading in {doc} — "
                f"{INDEX_PATH.relative_to(ROOT)} — {FIX}")
    assert not failures, "\n".join(failures)


def _missing_transcripts(sections: list[dict]) -> Counter:
    """``doc::heading`` of every procedure without an existing transcript."""
    missing: Counter = Counter()
    for entry in sections:
        if not isinstance(entry, dict) or entry.get("class") != "procedure":
            continue
        transcript = entry.get("transcript")
        if (not isinstance(transcript, str)
                or not (ROOT / transcript).is_file()):
            missing[f"{entry['doc']}::{entry['heading']}"] += 1
    return missing


def test_every_procedure_has_a_transcript():
    sections = _load_index()
    current = _missing_transcripts(sections)
    data = yaml.safe_load(RATCHETS_PATH.read_text(encoding="utf-8"))
    recorded = {entry["signature"]: entry["count"]
                for entry in data["checks"].get(CHECK_ID, [])}
    failures = []
    for signature, count in sorted(current.items()):
        if recorded.get(signature, 0) < count:
            doc, _, heading = signature.partition("::")
            try:
                lineno = next(number for line, number in _headings(doc)
                              if line == heading)
                where = f"{doc}:{lineno}"
            except StopIteration:
                where = INDEX_PATH.relative_to(ROOT).as_posix()
            failures.append(
                f"A8 {signature}: current count {count} exceeds recorded "
                f"{recorded.get(signature, 0)} — {where} — {FIX}")
    for signature in sorted(recorded):
        if signature not in current:
            failures.append(
                f"A8 {signature}: no longer occurs — "
                f"remove the fixed exception from ratchets.yaml")
    assert not failures, "\n".join(failures)


def _scrut_bin() -> Path:
    configured = os.environ.get("LOS_SCRUT_BIN")
    if configured:
        return Path(configured)
    return ROOT / ".venv" / "bin" / "scrut"


def test_fixture_values_bind_exact_snapshots_after_contract_changes(mini_repo, tmp_path):
    from learning_os.store.fingerprint import snapshot

    env = dict(os.environ, LOS_REPO=str(ROOT), LOS_FX=str(mini_repo),
               LOS_OBSERVATIONS=str(tmp_path / 'observations.json'))
    helper = ROOT / 'tests/procedure_helpers/los-fixture-values'
    def exports():
        proc = subprocess.run([sys.executable, str(helper)], env=env,
                              capture_output=True, text=True, check=True)
        return proc.stdout
    initial = snapshot(mini_repo)
    assert f'LOS_FIXTURE_SNAPSHOT_1={initial}' in exports()
    declaration = mini_repo / 'system/contracts/capabilities.yaml'
    declaration.write_text(declaration.read_text() + '\n# Contract edit.\n')
    changed = snapshot(mini_repo)
    assert initial != changed
    output = exports()
    assert f'LOS_FIXTURE_SNAPSHOT_1={initial}' in output
    assert f'LOS_FIXTURE_SNAPSHOT_2={changed}' in output
    assert exports() == output


def _procedure_child_env(*, log_path: Path, token: str) -> dict:
    """The env procedure children inherit: audit hook plus render check.

    The scenario harness's own mechanism (SPEC §3.2c): ``arch_site`` on
    ``PYTHONPATH`` installs ``arch_audit_hook`` at interpreter startup in
    every Python child, writing to ``LOS_ARCH_AUDIT_LOG`` under
    ``LOS_ARCH_LAUNCH_TOKEN`` as the root token. Transcripts manage their
    own ``LOS_OBSERVATIONS`` through ``los-fixture``, so this sets none.
    ``.venv/bin`` leads ``PATH`` so the helpers' ``env python3`` shebang
    lands on the venv interpreter they re-exec onto today: every Python
    child then installs the same hook, with no install gap.
    """
    env = dict(os.environ)
    env["LOS_REPO"] = str(ROOT)
    env["LOS_ARCH_RENDER_CHECK"] = "1"
    env["LOS_ARCH_AUDIT_LOG"] = str(log_path)
    env["LOS_ARCH_LAUNCH_TOKEN"] = token
    env["PYTHONPATH"] = (
        str(ARCH_SITE) + os.pathsep + env.get("PYTHONPATH", ""))
    env["PATH"] = str(ROOT / ".venv" / "bin") + os.pathsep + env.get(
        "PATH", "")
    return env


def _check_procedure_audit(transcript: str, log_path: Path) -> None:
    """Fail on missing or incomplete audit evidence, or render-marked I/O.

    A missing log raises through ``read_log``; a log with no install
    witness, an install without its completion, or any render-marked
    record fails here (SPEC (az), S15 item 5).
    """
    records = arch_audit_hook.read_log(log_path)
    problems = []
    if not any(rec.get("event") == "installed" for rec in records):
        problems.append(f"{transcript}: audit log has no installed witness")
    problems.extend(witness_failures(records, allow_isolated=True))
    problems.extend(render_violations(records))
    assert not problems, (
        f"{transcript}: audit witness failure:\n" + "\n".join(problems))


def _persist_procedure_audit(stem: str, log_path: Path) -> None:
    """Append one transcript's audit log to the A19 population (§3.6)."""
    import json as _json
    import os as _os

    audit_dir = _os.environ.get("LOS_ARCH_AUDIT_DIR")
    if not audit_dir:
        return
    dest_dir = Path(audit_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = f"procedure__{stem}"
    dest = dest_dir / f"{name}--{uuid.uuid4().hex}.jsonl"
    # Each installed child supplies its actual world and same-command
    # receipt proof; a transcript can use more than one disposable world.
    header = {"event": "case", "operation": "procedure", "case": stem}
    with open(dest, "x", encoding="utf-8") as out:
        out.write(_json.dumps(header) + "\n")
        out.write(log_path.read_text(encoding="utf-8"))
    with open(dest_dir / "cases.txt", "a", encoding="utf-8") as cases:
        cases.write(name + "\n")


def test_every_transcript_passes(tmp_path):
    transcripts = sorted(
        path for path in PROCEDURES.glob("*.md") if path.is_file())
    assert transcripts, f"no transcripts in {PROCEDURES}"
    scrut = _scrut_bin()
    assert scrut.is_file(), (
        f"scrut binary not found: {scrut} — set LOS_SCRUT_BIN to the v0.5.0"
        " binary, or run the `make setup` addition BAKEOFF.md records")
    for transcript in transcripts:
        log_path = tmp_path / f"{transcript.stem}.audit.jsonl"
        token = f"procedure-{uuid.uuid4().hex}"
        env = _procedure_child_env(log_path=log_path, token=token)
        proc = subprocess.run(
            [str(scrut), "test", str(transcript)],
            capture_output=True, text=True, timeout=600, env=env, cwd=ROOT)
        check_render_purity_error(proc.stdout + proc.stderr)
        assert proc.returncode == 0, (
            f"{transcript.name} failed:\n{proc.stdout}\n{proc.stderr}")
        _check_procedure_audit(transcript.name, log_path)
        _persist_procedure_audit(transcript.stem, log_path)


#: A child driver that runs one renderer through the real run_cli path.
#: ``argv`` is ``<root> <probe> <read|pure>``: the read mode renders the
#: probe file's content (audited I/O under the marker), the pure mode
#: renders a constant.
_PROBE_DRIVER = '''"""Procedure-child render probe (SPEC (az), S15 item 5)."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, %r)

from learning_os.app.pipeline import run_cli
from learning_os.app.proposal import Result
from learning_os.app.registry import REGISTRY, register

OPERATION = %r


def _reading(probe: Path, payload: dict) -> str:
    with open(probe, encoding="utf-8") as handle:
        return "saw " + handle.read()


def _pure(probe: Path, payload: dict) -> str:
    return "saw nothing"


def main() -> int:
    root = Path(sys.argv[1])
    probe = Path(sys.argv[2])
    render = _reading if sys.argv[3] == "read" else _pure

    def handler(ctx, req):
        return Result({"echo": "x"})

    # The operation's human renderer runs under the render marker (OD4).
    register(OPERATION, kind="query",
             human=lambda payload: render(probe, payload))(handler)
    try:
        outcome = run_cli(
            root, OPERATION, argparse.Namespace(root=str(root), json=False))
    finally:
        REGISTRY.pop(OPERATION, None)
    sys.stdout.write(outcome.stdout)
    sys.stderr.write(outcome.stderr)
    return outcome.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _write_probe_schema(root: Path) -> None:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"test-only/{PROBE_OP}",
        "type": "object",
        "properties": {},
    }
    path = root / "system" / "schema" / "requests" / f"{PROBE_OP}.schema.json"
    path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")


def _run_probe_child(mini_repo: Path, tmp_path: Path,
                     mode: str) -> tuple:
    """Run the probe driver as a procedure child; return (proc, records)."""
    log_path = tmp_path / f"probe-{mode}.audit.jsonl"
    token = f"procedure-{uuid.uuid4().hex}"
    probe = tmp_path / "probe.txt"
    probe.write_text("sight\n", encoding="utf-8")
    _write_probe_schema(mini_repo)
    driver = tmp_path / f"probe-driver-{mode}.py"
    driver.write_text(
        _PROBE_DRIVER % (str(ROOT / "tools"), PROBE_OP), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(driver), str(mini_repo), str(probe), mode],
        capture_output=True, text=True, timeout=120,
        env=_procedure_child_env(log_path=log_path, token=token),
        cwd=mini_repo)
    assert proc.returncode == 0, f"probe child failed: {proc.stderr[-2000:]}"
    return proc, arch_audit_hook.read_log(log_path), token


def _assert_probe_witnesses(records: list, token: str) -> None:
    assert witness_failures(records) == [], witness_failures(records)
    installed = [rec for rec in records if rec.get("event") == "installed"]
    assert len(installed) == 1, installed
    assert installed[0]["token"] == token
    completed = [rec for rec in records if rec.get("event") == "completed"]
    assert len(completed) == 1, completed
    assert completed[0]["pid"] == installed[0]["pid"]
    assert completed[0]["token"] == token


def test_procedure_child_audit_marks_render_io(mini_repo, tmp_path):
    """A file-reading renderer in a procedure child fails as op::cb::open."""
    _proc, records, token = _run_probe_child(mini_repo, tmp_path, "read")
    _assert_probe_witnesses(records, token)
    assert render_violations(records) == [
        f"A18 {PROBE_OP}::human::open: renderer performed audited I/O",
        f"A18 {PROBE_OP}::human::open: renderer performed audited I/O",
    ]


def test_procedure_child_audit_passes_pure_renderer(mini_repo, tmp_path):
    """The same procedure child with a pure renderer is clean."""
    _proc, records, token = _run_probe_child(mini_repo, tmp_path, "pure")
    _assert_probe_witnesses(records, token)
    assert render_violations(records) == []


def _popen_record(argv: list, token: str) -> dict:
    return {"event": "subprocess.Popen", "argv": argv, "token": token,
            "expect_crash": False}


def test_isolated_launch_needs_no_installed_witness():
    """An isolated (-I) launch is excused only with allow_isolated."""
    records = [_popen_record(
        ["/repo/.venv/bin/python", "-I", "-B", "install.py"], "t1")]
    assert witness_failures(records, allow_isolated=True) == []
    assert witness_failures(records) != []


def test_program_position_dash_i_still_needs_a_witness():
    """A -I past the script name (or in -c) belongs to the program."""
    script_arg = [_popen_record(
        ["/repo/.venv/bin/python", "tool.py", "-I"], "t2")]
    assert witness_failures(script_arg, allow_isolated=True) != []
    inline = [_popen_record(
        ["/repo/.venv/bin/python", "-c", "print('-I')"], "t3")]
    assert witness_failures(inline, allow_isolated=True) != []


ANCHORED_COPY = ROOT / "tests" / "procedure_helpers" / "los-anchored-copy"


def _run_anchored_copy(stem: str, dest: Path, tmpdir: Path) -> subprocess.CompletedProcess:
    """Run los-anchored-copy as a bare child (no audit env needed)."""
    env = dict(os.environ, LOS_REPO=str(ROOT), TMPDIR=str(tmpdir))
    return subprocess.run(
        [sys.executable, str(ANCHORED_COPY), stem, str(dest)],
        capture_output=True, text=True, timeout=120, env=env, cwd=tmpdir)


def _assert_bundle_hashes(proc: subprocess.CompletedProcess, dest: Path) -> None:
    """Stdout hash lines match the repo files' bytes, sorted by path."""
    assert proc.returncode == 0, proc.stderr[-2000:]
    lines = proc.stdout.splitlines()
    assert len(lines) == len({line.split(" ", 1)[1] for line in lines}) > 0
    assert lines == sorted(lines, key=lambda line: line.split(" ", 1)[1])
    for line in lines:
        digest, _, rel = line.partition(" ")
        assert digest.startswith("sha256:"), line
        source = (ROOT / rel).read_bytes()
        assert (dest / rel).read_bytes() == source
        assert digest == f"sha256:{hashlib.sha256(source).hexdigest()}", line


def test_anchored_copy_materials_manifest_roundtrip(tmp_path):
    """The inventory bundle lands byte-identical with printed hashes."""
    dest = tmp_path / "pair" / "repo"
    dest.mkdir(parents=True)
    proc = _run_anchored_copy("materials_manifest", dest, tmp_path)
    _assert_bundle_hashes(proc, dest)
    assert proc.stdout.count("\n") == 5


def test_anchored_copy_plan_write_audit_roundtrip(tmp_path):
    """The audit bundle is the one entrypoint, byte-identical."""
    dest = tmp_path / "pair" / "repo"
    dest.mkdir(parents=True)
    proc = _run_anchored_copy("plan_write_audit", dest, tmp_path)
    _assert_bundle_hashes(proc, dest)
    assert proc.stdout.count("\n") == 1


def test_anchored_copy_refuses_destination_outside_tmpdir(tmp_path):
    """A destination outside TMPDIR is refused and left untouched."""
    jail = tmp_path / "jail"
    jail.mkdir()
    dest = tmp_path / "elsewhere" / "repo"
    dest.mkdir(parents=True)
    proc = _run_anchored_copy("plan_write_audit", dest, jail)
    assert proc.returncode == 2
    assert "outside TMPDIR" in proc.stderr
    assert list(dest.iterdir()) == []


def test_anchored_copy_refuses_unknown_stem(tmp_path):
    """Only the two allowlisted bundles copy; anything else exits 2."""
    dest = tmp_path / "pair" / "repo"
    dest.mkdir(parents=True)
    proc = _run_anchored_copy("los", dest, tmp_path)
    assert proc.returncode == 2
    assert "unknown bundle" in proc.stderr
    assert list(dest.iterdir()) == []


def test_anchored_copy_refuses_repo_interior(tmp_path):
    """A destination inside LOS_REPO is refused before anything is made."""
    dest = ROOT / "scratch-probe-anchored"
    assert not dest.exists()
    # TMPDIR at the repo so the interior rule, not the TMPDIR rule, fires.
    proc = _run_anchored_copy("plan_write_audit", dest, ROOT)
    assert proc.returncode == 2
    assert "inside LOS_REPO" in proc.stderr
    assert not dest.exists()


def test_anchored_copy_refuses_symlink_destination(tmp_path):
    """A symlink destination is refused even when its target is inside."""
    target = tmp_path / "real"
    target.mkdir()
    dest = tmp_path / "linked"
    dest.symlink_to(target, target_is_directory=True)
    proc = _run_anchored_copy("plan_write_audit", dest, tmp_path)
    assert proc.returncode == 2
    assert "symlink" in proc.stderr
    assert list(target.iterdir()) == []


def test_anchored_copy_refuses_destination_parent_symlink(tmp_path):
    jail = tmp_path / "jail"
    jail.mkdir()
    dest = jail / "repo"
    dest.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "plan_write_audit.py"
    target.write_text("untouched sentinel\n")
    (dest / "tools").symlink_to(outside, target_is_directory=True)
    proc = _run_anchored_copy("plan_write_audit", dest, jail)
    assert proc.returncode == 1
    assert "symlink destination" in proc.stderr
    assert target.read_text() == "untouched sentinel\n"


def test_anchored_copy_refuses_source_parent_symlink(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "plan_write_audit.py").write_text("outside source\n")
    (source / "tools").symlink_to(outside, target_is_directory=True)
    dest = tmp_path / "dest"
    dest.mkdir()
    env = dict(os.environ, LOS_REPO=str(source), TMPDIR=str(tmp_path))
    proc = subprocess.run(
        [sys.executable, str(ANCHORED_COPY), "plan_write_audit", str(dest)],
        capture_output=True, text=True, timeout=120, env=env, cwd=tmp_path)
    assert proc.returncode == 1
    assert "source is not a regular file" in proc.stderr
    assert list(dest.iterdir()) == []


#: Expected-mismatch arms (SPEC (ak)): M-id to (transcript file, case
#: title, documented claim verbatim from tests/architecture/mismatches.yaml).
#: Each check below holds the DOCUMENTED claim and xfails while the observed
#: behavior from its transcript differs. M-01..M-08 predate this module's
#: arms and are owned outside Task 69; only the M-ids this task pinned get
#: rows here.
MISMATCH_CHECKS = {
    "M-09": (
        "start-a-workspace.md",
        "An unspecified deadline fails validation (M-09)",
        "Unspecified workspace deadline validates clean",
    ),
    "M-10": (
        "carry-work-across-semesters.md",
        "A supersedes frontmatter field is refused (M-10)",
        "Successor workspace carries supersedes frontmatter",
    ),
}


def _mismatch_world(tmp_path: Path, tag: str) -> tuple[Path, Path]:
    """A fresh disposable rich_world plus its observations path."""
    container = tmp_path / tag
    container.mkdir(parents=True, exist_ok=False)
    built = prepare_transcript_fixture("rich_world", container, seed=tag)
    return Path(built["root"]), Path(built["observations"])


def _run_los_validate(root: Path, observations: Path) -> subprocess.CompletedProcess:
    env = dict(os.environ, LOS_OBSERVATIONS=str(observations),
               TZ="Europe/Berlin")
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "los.py"), "--root",
         str(root), "validate"],
        capture_output=True, text=True, timeout=300, env=env, cwd=root)


def _workspace_skeleton(ws_id: str, title: str, extra_frontmatter: str) -> str:
    return (
        "---\n"
        f"id: {ws_id}\n"
        "type: workspace\n"
        f"title: {title}\n"
        "created: 2026-10-12\n"
        "status: active\n"
        "standing: false\n"
        "concepts: []\n"
        "notes: []\n"
        "sources: []\n"
        f"{extra_frontmatter}"
        "---\n"
        "## Objective\n\nProbe.\n\n"
        "## Current Scope\n\nSmall.\n\n"
        "## Open Questions\n\nNone.\n\n"
        "## Next Action\n\nProbe.\n"
    )


def test_mismatch_M09_null_deadline_validates(tmp_path):
    """M-09 | start-a-workspace.md | An unspecified deadline fails validation (M-09) | Unspecified workspace deadline validates clean."""
    root, observations = _mismatch_world(tmp_path, "mismatch-m09")
    ws = root / "work" / "active" / "workspace-m09"
    for sub in ("scratch", "inputs", "outputs"):
        (ws / sub).mkdir(parents=True)
    (ws / "CONTEXT.md").write_text(
        _workspace_skeleton("workspace-m09", "M09 probe", "deadline:\n"),
        encoding="utf-8")
    proc = _run_los_validate(root, observations)
    try:
        assert proc.returncode == 0, (
            "documented: unspecified workspace deadline validates clean; "
            f"got exit {proc.returncode}: {(proc.stdout + proc.stderr)[-500:]}")
    except AssertionError as err:
        pytest.xfail(f"M-09 expected mismatch: {err}")
    pytest.fail("M-09 documented claim now holds; remove the xfail arm per (ak)")


def test_mismatch_M10_workspace_supersedes_accepted(tmp_path):
    """M-10 | carry-work-across-semesters.md | A supersedes frontmatter field is refused (M-10) | Successor workspace carries supersedes frontmatter."""
    root, observations = _mismatch_world(tmp_path, "mismatch-m10")
    ws = root / "work" / "active" / "workspace-m10"
    for sub in ("scratch", "inputs", "outputs"):
        (ws / sub).mkdir(parents=True)
    (ws / "CONTEXT.md").write_text(
        _workspace_skeleton("workspace-m10", "M10 probe",
                            "supersedes:\n- workspace-demo\n"),
        encoding="utf-8")
    proc = _run_los_validate(root, observations)
    try:
        assert proc.returncode == 0, (
            "documented: successor workspace carries supersedes frontmatter; "
            f"got exit {proc.returncode}: {(proc.stdout + proc.stderr)[-500:]}")
    except AssertionError as err:
        pytest.xfail(f"M-10 expected mismatch: {err}")
    pytest.fail("M-10 documented claim now holds; remove the xfail arm per (ak)")

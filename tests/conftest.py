"""Shared fixtures: the real repository root and a synthetic-minimal repo builder."""

from __future__ import annotations

import json
import os
import shutil
import textwrap
from pathlib import Path

import group_map
import pytest
import yaml
from arch_audit_hook import SITE_WITNESS_ENV
from repo_builders import copy_real_contracts

from learning_os.store.diagnostics.conventions import TRACE_STORE_DENY_ENV

REPO_ROOT = Path(__file__).resolve().parent.parent

# The test session must never persist spans to the repository under test. A
# few tests drive the real capability catalog through the real CLI without
# ``--root`` (they assert on the real catalog, so a tmp mini would change
# the assertions); those runs bind the trace store to the real root, and
# their best-effort spans used to land in the live
# ``operations/diagnostics/traces.jsonl`` (JF-03). Deny persistence for this
# repository for the whole session — child processes inherit this
# environment, so rootless CLI runs are covered too — instead of truncating
# the live store after the fact. Mini repositories under tmp dirs are
# unaffected. Never truncate, unlink, or otherwise modify the live store
# from the test session: a legitimate span written outside the test scope
# must survive the suite (see test_diagnostic_store.py).
os.environ[TRACE_STORE_DENY_ENV] = os.pathsep.join(
    [str(REPO_ROOT), os.environ.get(TRACE_STORE_DENY_ENV, "")]).rstrip(os.pathsep)

# Stamp embedded in the shared session snapshots below. No consumer asserts on
# its value (verified at introduction); it only needs to be stable so the
# snapshots are built once.
SHARED_GENERATED_AT = "shared-test-snapshot"


@pytest.fixture(autouse=True)
def _unbind_diagnostic_store_between_tests():
    """Unbind the process-global trace store after every test (JF-03).

    Binding is process-global, so without this an in-process emit in one
    test could persist into the previous test's mini. Persistence to the
    repository under test is denied session-wide (above); this fixture
    only resets the pointer.
    """
    yield
    try:
        from learning_os.store.diagnostics.store import bind_store
    except ImportError:
        pass
    else:
        try:
            bind_store(None)
        except Exception:
            pass


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session", autouse=True)
def _site_witness_file(tmp_path_factory):
    """The A9 witness file for the session (SPEC §3.3 A9).

    Under pytest's tmp base, never inside ``repository/``. Child
    processes inherit it through ``os.environ``: the scenario
    harness and the procedure runner both start their child env
    from ``dict(os.environ)``.

    In CI merge mode the merged witness file of the producer shards is
    used as-is, so A9's session population is the whole suite's.
    """
    premerged = os.environ.get(PREMERGED_WITNESS_ENV)
    if premerged:
        previous = os.environ.get(SITE_WITNESS_ENV)
        os.environ[SITE_WITNESS_ENV] = premerged
        _load_premerged_attribution(premerged)
        yield Path(premerged)
        if previous is None:
            os.environ.pop(SITE_WITNESS_ENV, None)
        else:
            os.environ[SITE_WITNESS_ENV] = previous
        return
    path = tmp_path_factory.mktemp("site-witness") / "sites.jsonl"
    path.touch()
    previous = os.environ.get(SITE_WITNESS_ENV)
    os.environ[SITE_WITNESS_ENV] = str(path)
    yield path
    _dump_attribution_sidecar(path)
    if previous is None:
        os.environ.pop(SITE_WITNESS_ENV, None)
    else:
        os.environ[SITE_WITNESS_ENV] = previous


def _dump_attribution_sidecar(witness_path: Path) -> None:
    """Persist A9 per-case attribution beside the witness file (C3).

    ``scenario_harness.CASE_SITE_WITNESSES`` is process-local memory; a
    CI merge job cannot see it. The sidecar is the same map serialized
    (keyed "<operation>:<case-id>", values as sorted [operation, site]
    pairs), so the zz job can rebuild attribution over the merged witness
    file. Local runs write it too — harmless, and identical to what CI
    shards upload.
    """
    try:
        import scenario_harness
    except ImportError:
        return
    # Keys are (witness file, "operation:case"); only the case id travels —
    # the loader re-keys every entry onto the merged witness file anyway.
    data = {
        key: sorted(list(pair) for pair in sites)
        for (_, key), sites in scenario_harness.CASE_SITE_WITNESSES.items()
        if sites
    }
    try:
        witness_path.with_suffix(".jsonl.attribution.json").write_text(
            json.dumps(data, sort_keys=True), encoding="utf-8")
    except OSError:
        pass


def _load_premerged_attribution(merged_witness: str) -> None:
    """Rebuild A9 attribution in this process from the producer sidecars.

    Every sidecar's entries are re-keyed onto the merged witness file —
    A9 looks attribution up by ``(os.environ[LOS_SITE_WITNESS_FILE],
    "<operation>:<case-id>")``, and in merge mode that env points at the
    merged file. Cases are disjoint across shards (each scenario case
    runs exactly once suite-wide), so re-keying cannot collide.
    """
    raw = os.environ.get(PREMERGED_ATTRIBUTION_ENV, "")
    sidecars = [part for part in raw.split() if part]
    if not sidecars:
        return
    import scenario_harness

    merged: dict[tuple[str, str], set[tuple[str, str]]] = {}
    for sidecar in sidecars:
        data = json.loads(Path(sidecar).read_text(encoding="utf-8"))
        for key, pairs in data.items():
            bucket = merged.setdefault((merged_witness, key), set())
            bucket.update((pair[0], pair[1]) for pair in pairs)
    scenario_harness.CASE_SITE_WITNESSES.update(merged)


#: The A19 audit directory (SPEC §3.6): every scenario and procedure
#: case appends its audit log here for the zz ownership population.
AUDIT_DIR_ENV = "LOS_ARCH_AUDIT_DIR"

#: CI shard merge mode (C3, 2026-10-24). The suite runs as parallel shard
#: jobs; the zz population files run in later jobs over the *merged*
#: witness artifacts of the producer shards. These three variables switch
#: the session fixtures below from "create fresh session files" to "use
#: the merged ones", so the population checks see the whole suite's
#: population, not one shard's. They are unset for every local run and
#: every producer shard.
PREMERGED_WITNESS_ENV = "LOS_PREMERGED_WITNESS"
PREMERGED_AUDIT_ENV = "LOS_PREMERGED_AUDIT_DIR"
#: Space-separated attribution sidecar files (see the sessionfinish hook
#: below) written by the producer shards; re-keyed onto the merged
#: witness file and loaded into scenario_harness.CASE_SITE_WITNESSES so
#: A9's per-case attribution check survives the process boundary.
PREMERGED_ATTRIBUTION_ENV = "LOS_PREMERGED_ATTRIBUTION"


@pytest.fixture(scope="session", autouse=True)
def _operational_audit_dir(tmp_path_factory):
    """The session-scoped A19 audit directory, outside the repository.

    In CI merge mode the merged population directory is used as-is: the
    zz population tests must assert over every producer shard's logs.
    """
    premerged = os.environ.get(PREMERGED_AUDIT_ENV)
    if premerged:
        previous = os.environ.get(AUDIT_DIR_ENV)
        os.environ[AUDIT_DIR_ENV] = premerged
        yield Path(premerged)
        if previous is None:
            os.environ.pop(AUDIT_DIR_ENV, None)
        else:
            os.environ[AUDIT_DIR_ENV] = previous
        return
    path = tmp_path_factory.mktemp("operational-audit")
    previous = os.environ.get(AUDIT_DIR_ENV)
    os.environ[AUDIT_DIR_ENV] = str(path)
    yield path
    if previous is None:
        os.environ.pop(AUDIT_DIR_ENV, None)
    else:
        os.environ[AUDIT_DIR_ENV] = previous


#: Node-level shard selection (C3): "tests/test_x.py=1/4 tests/test_y.py=0/2"
#: — for each named file, this session keeps only items whose stable node-id
#: hash lands on <index> of <count>. A mod-N split is a partition for every
#: N, so a file shared by N legs still runs each of its tests exactly once
#: across the legs; the CI gate's collection-vs-sum proof holds either way.
#: Unset locally and for every file-level leg.
NODE_SHARDS_ENV = "LOS_NODE_SHARDS"


def pytest_collection_modifyitems(items, config):
    """Apply the area-group marker from tests/group_map.py; fail on drift.

    Then apply node-level shard selection when LOS_NODE_SHARDS names files
    carried by this session (the CI zz legs): the named files' items are
    trimmed to this leg's hash slice and reported to pytest as deselected,
    so a leg's summary line shows exactly what it dropped.
    """
    errors = group_map.check_map(Path(__file__).resolve().parent)
    assert not errors, (
        "tests/group_map.py is out of step with tests/: "
        + "; ".join(errors))
    for item in items:
        name = Path(str(item.fspath)).name
        group = group_map.FILE_TO_GROUP.get(name)
        if group is not None:
            item.add_marker(getattr(pytest.mark, group))

    import zlib

    shards = {}
    for entry in os.environ.get(NODE_SHARDS_ENV, "").split():
        stem, _, spec = entry.partition("=")
        index, _, count = spec.partition("/")
        if stem and count.isdigit() and index.isdigit():
            shards[stem] = (int(index), int(count))
    if not shards:
        return
    kept, deselected = [], []
    for item in items:
        name = Path(str(item.fspath)).name
        spec = shards.get(name)
        if spec is not None:
            index, count = spec
            bucket = zlib.crc32(item.nodeid.encode("utf-8")) % count
            if bucket != index:
                deselected.append(item)
                continue
        kept.append(item)
    if deselected:
        items[:] = kept
        config.hook.pytest_deselected(items=deselected)


@pytest.fixture(scope="session")
def real_repo():
    """The checked-in repository, loaded once.

    The suite never mutates the real tree (audited 2026-09-21: every write
    goes to tmp copies), and ``validate``/``generate_all``/``build_manifest``
    do not mutate the loaded object apart from idempotent memo caches — so
    every ``full_repo`` test can share one loaded snapshot instead of each
    paying ``load_repo`` again. Same assertions, one load.
    """
    from learning_os.store.loader import load_repo

    return load_repo(REPO_ROOT)


@pytest.fixture(scope="session")
def real_issues(real_repo):
    """``validate()`` over the checked-in repository, computed once."""
    from learning_os.derive.validation import validate

    return validate(real_repo)


@pytest.fixture(scope="session")
def real_generated(real_repo):
    """``generate_all()`` over the checked-in repository, computed once."""
    from learning_os.derive.projection import generate_all

    return generate_all(real_repo, generated_at=SHARED_GENERATED_AT)


@pytest.fixture(scope="session")
def real_manifest(real_generated):
    """The checked-in manifest, parsed from the shared ``generate_all``.

    ``generate_all(repo, at)["manifest.json"]`` parses to the same keys and
    values as ``build_manifest(repo, at, build_backlinks(repo, at))``
    (verified 2026-09-21) — key order follows production's sorted
    serialization, which is what every consumer reads. Same content the
    direct builders produce, without rebuilding it per test.
    """
    return json.loads(real_generated["manifest.json"])


@pytest.fixture()
def mini_repo(tmp_path: Path) -> Path:
    """A minimal, valid synthetic repository (inside LearningOS-shaped parents)."""
    return build_mini_repo(tmp_path)


def build_mini_repo(tmp_path: Path) -> Path:
    """The builder behind the fixture.

    Exposed as a plain function because one test needs the same synthetic
    repository at module scope — a cross-process harness acts on a single
    repository across several scenarios. Reaching inside the fixture object to
    get at this was the alternative, and a second copy of the description was
    the worse one.
    """
    los = tmp_path / "LearningOS"
    root = los / "repository"
    for d in ("knowledge/notes/mathematics", "knowledge/attachments", "records",
              "sources/collections", "work/inbox", "work/active", "generated/reports",
              "archive/workspaces", "tools", "tests"):
        (root / d).mkdir(parents=True)
    (los / "materials").mkdir()
    shutil.copytree(REPO_ROOT / "system" / "schema", root / "system" / "schema")
    copy_real_contracts(REPO_ROOT, root)

    (root / "knowledge" / "concepts.yaml").write_text(yaml.safe_dump({
        "concepts": [
            {"id": "concept-expected-value", "label": "Expected value",
             "aliases": ["Erwartungswert"]},
            {"id": "concept-variance", "label": "Variance", "aliases": ["Varianz"]},
        ]}), encoding="utf-8")
    (root / "knowledge" / "concept-relations.yaml").write_text(yaml.safe_dump({
        "relations": [
            {"from": "concept-variance", "type": "builds-on", "to": "concept-expected-value"},
        ]}), encoding="utf-8")
    (root / "sources" / "sources.yaml").write_text(yaml.safe_dump({
        "sources": [
            {"id": "source-demo-book", "title": "Demo Book", "type": "book",
             "authors": ["A. Author"],
             "evaluations": [{"concepts": ["concept-expected-value"],
                              "roles": ["first-learning"], "level": "introductory",
                              "strengths": ["clear intuition"]}]},
        ]}), encoding="utf-8")
    (root / "records" / "modules.yaml").write_text(yaml.safe_dump({
        "modules": [
            {"id": "module-demo", "institution": "HU Berlin", "title": "Demo Module",
             "status": "enrolled", "attempts": [
                 {"termin": 1, "date": "2026-07-27", "result": "withdrawn"},
                 {"termin": 2, "date": "2026-10-09", "result": "registered"},
             ]},
        ]}), encoding="utf-8")
    (root / "knowledge" / "notes" / "mathematics" / "note-demo.md").write_text(
        textwrap.dedent("""\
        ---
        id: note-demo
        type: note
        title: Demo note
        created: 2026-07-16
        role: synthesis
        concepts: [concept-expected-value]
        sources: [source-demo-book]
        ---

        Body prose.
        """), encoding="utf-8")
    ws = root / "work" / "active" / "workspace-demo"
    (ws / "scratch").mkdir(parents=True)
    (ws / "CONTEXT.md").write_text(textwrap.dedent("""\
        ---
        id: workspace-demo
        type: workspace
        title: Demo workspace
        created: 2026-07-16
        status: active
        concepts: [concept-expected-value]
        notes: [note-demo]
        ---

        ## Objective

        Demo.

        ## Current Scope

        Small.

        ## Open Questions

        None.

        ## Next Action

        Do the demo thing.
        """), encoding="utf-8")
    (root / "work" / "COORDINATION.md").write_text(textwrap.dedent("""\
        ---
        id: coordination
        type: coordination
        ---

        # Coordination

        ## Commitments

        (none)

        ## Priorities

        (none)

        ## Dependencies

        (none)

        ## Deferrals

        - Demo module deferred to 2. Termin (date lives in records/modules.yaml)
        """), encoding="utf-8")
    (root / ".gitignore").write_text("generated/*\n!generated/.gitkeep\n", encoding="utf-8")
    return root

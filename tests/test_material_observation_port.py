"""Material observation port (S16; group `materials`).

On a material fixture: (a) both ported functions return identical results
with ``obs=None`` and with an explicit live port; (b) with an in-memory
dict-backed fake they perform no filesystem reads under the fixture root
or the materials root; (c) a fake revision change reports the stale-note
message. A cheating fake proves the read detector is not vacuous, and two
delegation controls prove the source-map existence check and the route
checksum both travel through the port. Complete comparisons use exact
type-and-value equality, so ``False`` differs from ``0``; further
regressions prove reads mode resets (including renderer capture) and
that a failed install activates no log or reads mode.
"""

from __future__ import annotations

import copy
import hashlib
import os
from pathlib import Path

import arch_audit_hook
import pytest
import yaml
from repo_builders import material_fixture, write_yaml

from learning_os.app.render import call_renderer
from learning_os.app.synthesis.material_synthesis import (
    MaterialSynthesisError,
    _analysis_ref_problem,
    current_unit_material_basis,
)
from learning_os.store.loader import load_repo
from learning_os.store.material_analysis import observe_local_material
from learning_os.store.material_observations import (
    LiveMaterialObservations,
    MaterialObservations,
)
from learning_os.store.revisions import artifact_revision

UNIT_ID = "unit-demo-l01"
NOTE_ID = "note-ref-density"
ANCHOR = {"topic": "Density", "purpose": "intuition",
          "locator": "lecture-01.pdf p.1"}
RANGE = {"start": 1, "end": 1}
MATERIAL = "source-demo-book/lecture-01.pdf"


def _plant_note(root: Path) -> Path:
    """A note carrying a resolved material-analysis binding (cf. the
    analysis-refs suite's planter: same binding shape, local copy so this
    module does not import another test module's privates)."""
    digest = hashlib.sha256(
        (root.parent / "materials" / MATERIAL).read_bytes()).hexdigest()
    body = "Density prose.\n"
    meta = {"id": NOTE_ID, "type": "note", "role": "reference",
            "title": "Density analysis", "created": "2026-09-21",
            "state": "rough", "authorship": "operator-drafted",
            "semantic_review": "user-reviewed",
            "material_analysis": {
                "resolution": "resolved",
                "material": MATERIAL,
                "source_id": "source-demo-book",
                "recorded_source_digest": digest,
                "live_source_digest": digest,
                "inspected_range": dict(RANGE),
                "anchors": [dict(ANCHOR)],
                "frozen_input_sha256": hashlib.sha256(body.encode()).hexdigest(),
                "frozen_input_bytes": len(body.encode()),
            }}
    path = root / "knowledge/notes/mathematics" / f"{NOTE_ID}.md"
    front = "---\n" + yaml.safe_dump(meta, sort_keys=False).rstrip() + "\n---\n\n"
    path.write_bytes(front.encode("utf-8") + body.encode("utf-8"))
    return path


class _DictObservations(MaterialObservations):
    """In-memory fake: every method answers from precomputed live values.

    Lookups are strict: an unexpected artifact, path, or material raises
    ``KeyError`` instead of silently standing in for a real read.
    """

    def __init__(self, values: dict):
        self._values = values

    def revision(self, artifact_id: str) -> int:
        return self._values["revisions"][artifact_id]

    def is_file(self, path: Path) -> bool:
        return self._values["files"][path]

    def read_bytes(self, path: Path) -> bytes:
        return self._values["contents"][path]

    def observe_material(self, material: str, recorded_digest: str) -> dict:
        return dict(self._values["observations"][(material, recorded_digest)])

    def route_checksum(self, repo, route: dict, cache: dict | None = None) -> str:
        return self._values["checksums"][route["id"]]


class _CheatingObservations(_DictObservations):
    """A fake whose ``read_bytes`` really reads a materials file.

    It returns the correct precomputed bytes, so the measured function is
    unaffected: only the audit window sees the extra read.
    """

    def __init__(self, values: dict, decoy: Path):
        super().__init__(values)
        self._decoy = decoy

    def read_bytes(self, path: Path) -> bytes:
        self._decoy.read_bytes()
        return super().read_bytes(path)


@pytest.fixture
def port_world(mini_repo: Path) -> dict:
    """Material fixture plus every live value the fake stands in for."""
    root = mini_repo
    _, route_id, _ = material_fixture(root)
    # Stamp the deterministic id the v13 migration stamps into live routes
    # (tools/migrations/route_identity_v13.py), so the basis sees stable
    # route IDs; then plant the analysis note and reload once.
    smap_path = root / "curriculum/modules/module-demo/source-map.yaml"
    smap = yaml.safe_load(smap_path.read_text(encoding="utf-8"))
    smap["sources"][0]["unit_routes"][0]["id"] = route_id
    write_yaml(smap_path, smap)
    _plant_note(root)
    repo = load_repo(root)
    materials_root = root.parent / "materials"
    unit = repo.units[UNIT_ID]
    note = repo.notes[NOTE_ID]
    expected_basis = current_unit_material_basis(
        root, UNIT_ID, repo=repo, cache={})
    live_note_revision = artifact_revision(root, NOTE_ID)
    note_bytes = note.path.read_bytes()
    ref = {"note_id": NOTE_ID, "note_revision": live_note_revision,
           "note_digest": f"sha256:{hashlib.sha256(note_bytes).hexdigest()}",
           "anchor": dict(ANCHOR), "material": MATERIAL,
           "inspected_range": dict(RANGE)}
    assert _analysis_ref_problem(root, repo, ref, cache={}) is None
    binding = note.meta["material_analysis"]
    observation = observe_local_material(
        materials_root, MATERIAL,
        str(binding["recorded_source_digest"]), cache={})
    source_map_path = repo.module_source_map_origins[unit.module_id]
    values = {
        "revisions": {
            UNIT_ID: artifact_revision(root, UNIT_ID),
            unit.module_id: artifact_revision(root, unit.module_id),
            NOTE_ID: live_note_revision,
        },
        "files": {source_map_path: True},
        "contents": {note.path: note_bytes},
        "observations": {
            (MATERIAL, str(binding["recorded_source_digest"])): observation,
        },
        "checksums": dict(expected_basis["material_checksums"]),
    }
    return {"root": root, "repo": repo, "materials_root": materials_root,
            "route_id": route_id, "ref": ref,
            "expected_basis": expected_basis, "values": values}


def _assert_typed_equal(actual, expected, path="$"):
    """Recursive exact-type-and-value equality (contract 6.3).

    Every pair must share its exact ``type`` first, so ``False``
    differs from ``0``; dicts must then share exact key sets and
    lists exact lengths before recursing into values and items.
    A failure names the nested ``path`` of the first mismatch.
    """
    assert type(actual) is type(expected), (
        f"{path}: type {type(actual).__name__} is not "
        f"{type(expected).__name__}: {actual!r} vs {expected!r}")
    if isinstance(actual, dict):
        actual_keys = set(actual.keys())
        expected_keys = set(expected.keys())
        assert actual_keys == expected_keys, (
            f"{path}: key sets differ: "
            f"actual-only={sorted(map(repr, actual_keys - expected_keys))} "
            f"expected-only={sorted(map(repr, expected_keys - actual_keys))}")
        for key in actual:
            _assert_typed_equal(actual[key], expected[key], f"{path}[{key!r}]")
    elif isinstance(actual, list):
        assert len(actual) == len(expected), (
            f"{path}: lengths differ: {len(actual)} != {len(expected)}")
        for index, (item, want) in enumerate(zip(actual, expected, strict=True)):
            _assert_typed_equal(item, want, f"{path}[{index}]")
    else:
        assert actual == expected, (
            f"{path}: values differ: {actual!r} != {expected!r}")


def _reads_under(records: list[dict], roots: set[Path]) -> list[dict]:
    """Audit records touching any root, in raw or resolved form."""
    hits = []
    for record in records:
        for raw in record.get("paths", []):
            if not isinstance(raw, str):
                continue
            candidate = Path(raw)
            if not candidate.is_absolute():
                candidate = Path(os.getcwd()) / candidate
            forms = {candidate, Path(os.path.realpath(candidate))}
            if any(form == root or root in form.parents for form in forms
                   for root in roots):
                hits.append(record)
                break
    return hits


def _world_roots(world: dict) -> set[Path]:
    roots = set()
    for key in ("root", "materials_root"):
        base = world[key]
        roots.add(base)
        roots.add(Path(os.path.realpath(base)))
    return roots


def test_typed_parity_assertion_rejects_coercible_values():
    """The parity assertion itself: nested False/0 fails in both
    directions, changed key sets and lengths fail, and a matching
    nested value passes. Each failure names its type/value issue."""
    good = {"flag": False, "count": 0, "name": "",
            "items": [1, False, {"k": [0, None]}], "nothing": None}
    _assert_typed_equal(copy.deepcopy(good), good)

    nested_zero = copy.deepcopy(good)
    nested_zero["items"][1] = 0
    with pytest.raises(AssertionError,
                       match=r"\$\['items'\]\[1\].*type int is not bool"):
        _assert_typed_equal(nested_zero, good)
    with pytest.raises(AssertionError, match="type bool is not int"):
        _assert_typed_equal(good, nested_zero)

    deep_false = copy.deepcopy(good)
    deep_false["items"][2]["k"][0] = False
    with pytest.raises(AssertionError, match="type bool is not int"):
        _assert_typed_equal(deep_false, good)

    missing = copy.deepcopy(good)
    del missing["name"]
    with pytest.raises(AssertionError, match="key sets differ"):
        _assert_typed_equal(missing, good)
    extra = copy.deepcopy(good)
    extra["added"] = 1
    with pytest.raises(AssertionError, match="key sets differ"):
        _assert_typed_equal(extra, good)

    longer = copy.deepcopy(good)
    longer["items"].append(9)
    with pytest.raises(AssertionError, match="lengths differ"):
        _assert_typed_equal(longer, good)

    changed = copy.deepcopy(good)
    changed["name"] = "x"
    with pytest.raises(AssertionError, match="values differ"):
        _assert_typed_equal(changed, good)


def test_explicit_live_matches_default(port_world: dict):
    """(a) `obs=None` and an explicit live port agree on both functions."""
    root = port_world["root"]
    repo = port_world["repo"]
    ref = port_world["ref"]
    stale_ref = {**ref, "note_revision": ref["note_revision"] + 1}

    default_basis = current_unit_material_basis(
        root, UNIT_ID, repo=repo, cache={})
    live_basis = current_unit_material_basis(
        root, UNIT_ID, repo=repo, cache={},
        obs=LiveMaterialObservations(root, {}))
    _assert_typed_equal(default_basis, port_world["expected_basis"])
    _assert_typed_equal(live_basis, port_world["expected_basis"])

    assert _analysis_ref_problem(root, repo, ref, cache={}) is None
    assert _analysis_ref_problem(
        root, repo, ref, cache={},
        obs=LiveMaterialObservations(root)) is None
    stale_default = _analysis_ref_problem(root, repo, stale_ref, cache={})
    stale_live = _analysis_ref_problem(
        root, repo, stale_ref, cache={},
        obs=LiveMaterialObservations(root, {}))
    assert stale_live == stale_default == "note was revised after approval"


def test_fake_performs_no_filesystem_reads(port_world: dict, tmp_path: Path):
    """(b) the dict-backed fake completes both calls with zero reads under
    the fixture root or the materials root."""
    root = port_world["root"]
    repo = port_world["repo"]
    log_path = tmp_path / "audit-reads.log"
    fake = _DictObservations(port_world["values"])
    arch_audit_hook.install(str(log_path), reads=True)
    try:
        basis = current_unit_material_basis(
            root, UNIT_ID, repo=repo, cache={}, obs=fake)
        problem = _analysis_ref_problem(
            root, repo, port_world["ref"], cache={}, obs=fake)
    finally:
        arch_audit_hook.uninstall()
    _assert_typed_equal(basis, port_world["expected_basis"])
    assert problem is None
    arch_audit_hook.assert_capture_ok()
    records = arch_audit_hook.read_log(log_path)
    assert _reads_under(records, _world_roots(port_world)) == []


def test_read_detector_catches_a_real_read(port_world: dict, tmp_path: Path):
    """Negative control: a fake whose `read_bytes` really reads a materials
    file trips the same no-reads assertion, on exactly the file it read."""
    root = port_world["root"]
    repo = port_world["repo"]
    log_path = tmp_path / "audit-reads-cheat.log"
    decoy = port_world["materials_root"] / MATERIAL
    arch_audit_hook.install(str(log_path), reads=True)
    try:
        problem = _analysis_ref_problem(
            root, repo, port_world["ref"], cache={},
            obs=_CheatingObservations(port_world["values"], decoy))
    finally:
        arch_audit_hook.uninstall()
    assert problem is None
    arch_audit_hook.assert_capture_ok()
    records = arch_audit_hook.read_log(log_path)
    hits = _reads_under(records, _world_roots(port_world))
    assert hits, "the detector missed a real read"
    assert any(str(decoy) in record.get("paths", []) for record in hits)
    with pytest.raises(AssertionError):
        assert _reads_under(records, _world_roots(port_world)) == []


def test_fake_revision_change_reports_stale_note(port_world: dict):
    """(c) a fake revision past the approval reports the stale-note message."""
    root = port_world["root"]
    repo = port_world["repo"]
    values = {**port_world["values"],
              "revisions": {**port_world["values"]["revisions"],
                            NOTE_ID: port_world["ref"]["note_revision"] + 1}}
    assert _analysis_ref_problem(
        root, repo, port_world["ref"], cache={},
        obs=_DictObservations(values)) == "note was revised after approval"


def test_port_owns_source_map_existence(port_world: dict):
    """The basis trusts the port's existence answer, not the live file.

    With the source map deleted after the snapshot load, the fake's True
    still yields the expected basis; the live port refuses exactly as
    before, proving the control setup is not vacuous."""
    root = port_world["root"]
    repo = port_world["repo"]
    unit = repo.units[UNIT_ID]
    source_map_path = repo.module_source_map_origins[unit.module_id]
    source_map_path.unlink()
    basis = current_unit_material_basis(
        root, UNIT_ID, repo=repo, cache={},
        obs=_DictObservations(port_world["values"]))
    _assert_typed_equal(basis, port_world["expected_basis"])
    with pytest.raises(MaterialSynthesisError,
                       match="unit has no module source map"):
        current_unit_material_basis(root, UNIT_ID, repo=repo, cache={})


def test_port_owns_route_checksum(port_world: dict):
    """The basis carries the port's checksum, not a live recomputation.

    A fake checksum the live tree could never produce must appear
    verbatim; every other field still matches the expected basis."""
    root = port_world["root"]
    repo = port_world["repo"]
    route_id = port_world["route_id"]
    invented = "sha256:" + "00" * 32
    assert invented != port_world["expected_basis"]["material_checksums"][route_id]
    values = {**port_world["values"], "checksums": {route_id: invented}}
    basis = current_unit_material_basis(
        root, UNIT_ID, repo=repo, cache={},
        obs=_DictObservations(values))
    _assert_typed_equal(basis["material_checksums"], {route_id: invented})
    rest = {key: basis[key] for key in basis if key != "material_checksums"}
    expected_rest = {key: port_world["expected_basis"][key]
                     for key in port_world["expected_basis"]
                     if key != "material_checksums"}
    _assert_typed_equal(rest, expected_rest)


def test_reads_mode_resets_to_ordinary_capture(tmp_path: Path):
    """reads=True sees a plain read; a default install afterwards does not,
    while write capture keeps working and a renderer read is captured
    with its renderer marker."""
    probe = tmp_path / "probe.txt"
    probe.write_text("probe", encoding="utf-8")
    reads_log = tmp_path / "audit-reads-mode.log"
    arch_audit_hook.install(str(reads_log), reads=True)
    try:
        probe.read_bytes()
    finally:
        arch_audit_hook.uninstall()
    arch_audit_hook.assert_capture_ok()
    assert any(str(probe) in record.get("paths", [])
               for record in arch_audit_hook.read_log(reads_log)), \
        "reads mode missed a plain read"

    plain_log = tmp_path / "audit-plain.log"
    arch_audit_hook.install(str(plain_log))
    try:
        probe.read_bytes()
        (tmp_path / "wrote.txt").write_text("x", encoding="utf-8")
    finally:
        arch_audit_hook.uninstall()
    arch_audit_hook.assert_capture_ok()
    records = arch_audit_hook.read_log(plain_log)
    assert all(str(probe) not in record.get("paths", []) for record in records)
    assert any("wrote.txt" in str(path)
               for record in records for path in record.get("paths", []))

    render_log = tmp_path / "audit-render.log"
    arch_audit_hook.install(str(render_log))
    try:
        probe.read_bytes()
        call_renderer("op.probe", "human", probe.read_bytes)
        (tmp_path / "wrote-render.txt").write_text("x", encoding="utf-8")
    finally:
        arch_audit_hook.uninstall()
    arch_audit_hook.assert_capture_ok()
    records = arch_audit_hook.read_log(render_log)
    probe_hits = [record for record in records
                  if str(probe) in record.get("paths", [])]
    assert probe_hits, "a renderer read was not captured"
    assert all(record.get("render") == ["op.probe", "human"]
               for record in probe_hits), \
        "an unmarked probe read was captured"
    assert any("wrote-render.txt" in str(path)
               for record in records for path in record.get("paths", []))


def test_failed_reads_install_activates_nothing(tmp_path: Path):
    """A failed install(..., reads=True) activates no log or reads mode.

    Idle, it raises and leaves no active log; while an ordinary window
    is active, it preserves that log and mode, so a plain read stays
    unrecorded while writes keep working."""
    probe = tmp_path / "probe-failed-install.txt"
    probe.write_text("probe", encoding="utf-8")
    arch_audit_hook.uninstall()
    with pytest.raises(arch_audit_hook.AuditCaptureError,
                       match="audit log path is a directory"):
        arch_audit_hook.install(str(tmp_path), reads=True)
    assert arch_audit_hook._ACTIVE_LOG is None
    assert arch_audit_hook._READS is False

    idle_log = tmp_path / "audit-after-idle-failure.log"
    arch_audit_hook.install(str(idle_log))
    try:
        probe.read_bytes()
    finally:
        arch_audit_hook.uninstall()
    arch_audit_hook.assert_capture_ok()
    assert all(str(probe) not in record.get("paths", [])
               for record in arch_audit_hook.read_log(idle_log))

    active_log = tmp_path / "audit-active.log"
    arch_audit_hook.install(str(active_log))
    try:
        with pytest.raises(arch_audit_hook.AuditCaptureError,
                           match="audit log path is a directory"):
            arch_audit_hook.install(str(tmp_path), reads=True)
        assert arch_audit_hook._ACTIVE_LOG == str(active_log)
        assert arch_audit_hook._READS is False
        probe.read_bytes()
        (tmp_path / "wrote-after-failed-install.txt").write_text(
            "x", encoding="utf-8")
    finally:
        arch_audit_hook.uninstall()
    arch_audit_hook.assert_capture_ok()
    records = arch_audit_hook.read_log(active_log)
    assert all(str(probe) not in record.get("paths", []) for record in records)
    assert any("wrote-after-failed-install.txt" in str(path)
               for record in records for path in record.get("paths", []))

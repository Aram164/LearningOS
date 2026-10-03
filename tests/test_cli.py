"""CLI gateway tests (ADR-006): los.py status/--json, capture, delegation,
and the reading-room / adoption additions to the generator."""

from __future__ import annotations

import datetime as _dt
import json

import pytest
import yaml
from gateway_helpers import approved_v2_call, file_sha256, request_artifact_id
from repo_builders import add_curriculum, run_los, write_yaml

from learning_os.genout import adoption_counts, generate_all
from learning_os.genout.modules_view import _academic_deadlines, _exam_spine_lines
from learning_os.loader import load_repo


# ----------------------------------------------------------------- status
def test_status_json_shape_and_counts(mini_repo):
    proc = run_los(mini_repo, "status", "--json")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert {"learning_os", "root", "counts", "adoption",
            "exam_spine", "validation"} <= set(payload)
    c = payload["counts"]
    assert c["notes"] == 1
    assert c["concepts"] == 2
    assert c["sources"] == 1
    assert c["active_workspaces"] == 1
    assert c["inbox_items"] == 0
    assert c["inbox_files"] == 0
    # the fixture registers a 2. Termin attempt — it must be on the spine
    assert payload["exam_spine"][0]["date"] == "2026-10-09"
    assert payload["exam_spine"][0]["termin"] == 2
    assert payload["adoption"] == {"notes_reviewed": 0, "notes_with_evidence": 0}


def test_status_counts_match_manifest_programs_and_modules(mini_repo):
    # F3: status counted repo.programs/repo.modules raw, so the quarantined
    # program and compatibility-only (project-migrated) modules inflated it
    # past bootstrap --brief, which reports the manifest's projected counts.
    add_curriculum(mini_repo)
    write_yaml(mini_repo / "curriculum/programs/program-quarantined.yaml", {
        "id": "program-quarantined", "type": "program", "title": "Quarantined",
        "kind": "quarantine", "status": "quarantined", "default": False,
        "semester_bound": False, "semesters": [],
    })
    compat_dir = mini_repo / "curriculum/modules/module-compat"
    write_yaml(compat_dir / "module.yaml", {
        "id": "module-compat", "type": "module", "kind": "project",
        "area_id": "program-bachelors", "title": "Migrated",
        "status": "active", "unit_order": [], "source_map": "source-map.yaml",
        "compatibility_only": True, "migrated_to": "project-compat",
    })
    write_yaml(compat_dir / "source-map.yaml", {
        "type": "module-source-map", "module_id": "module-compat",
        "sources": [],
    })
    status = run_los(mini_repo, "status", "--json")
    assert status.returncode == 0, status.stderr
    counts = json.loads(status.stdout)["counts"]
    assert counts["programs"] == 1
    assert counts["programs_quarantined"] == 1
    assert counts["modules"] == 1
    assert counts["modules_compatibility_only"] == 1
    brief = run_los(mini_repo, "bootstrap", "--brief")
    assert brief.returncode == 0, brief.stderr
    manifest_counts = json.loads(brief.stdout)["counts"]
    assert counts["programs"] == manifest_counts["programs"]
    assert counts["modules"] == manifest_counts["modules"]


def test_status_human_output_mentions_validation(mini_repo):
    proc = run_los(mini_repo, "status")
    assert proc.returncode == 0, proc.stderr
    assert "validation:" in proc.stdout
    assert "notes 1" in proc.stdout


def test_status_counts_a_folder_drop_once_and_its_files_recursively(mini_repo):
    # #114 item 2: `inbox_items` keeps its top-level meaning while
    # `inbox_files` agrees with `inbox-list` by construction.
    drop = mini_repo / "work/inbox/drop-001"
    drop.mkdir(parents=True)
    for name in ("a.md", "b.md", "c.md"):
        (drop / name).write_text("capture\n", encoding="utf-8")
    (mini_repo / "work/inbox/top.md").write_text("capture\n", encoding="utf-8")
    proc = run_los(mini_repo, "status", "--json")
    assert proc.returncode == 0, proc.stderr
    counts = json.loads(proc.stdout)["counts"]
    assert counts["inbox_items"] == 2
    assert counts["inbox_files"] == 4
    listed = run_los(mini_repo, "inbox-list")
    assert listed.returncode == 0, listed.stderr
    assert len(json.loads(listed.stdout)) == counts["inbox_files"]
    human = run_los(mini_repo, "status")
    assert human.returncode == 0, human.stderr
    assert "inbox 2 top-level · 4 files" in human.stdout


def test_status_exits_1_on_validation_errors_but_still_reports(mini_repo):
    note = mini_repo / "knowledge/notes/mathematics/note-demo.md"
    note.rename(note.with_name("renamed-demo.md"))
    proc = run_los(mini_repo, "status")
    assert proc.returncode == 1, proc.stderr
    assert "error(s)" in proc.stdout
    assert "notes 1" in proc.stdout
    json_proc = run_los(mini_repo, "status", "--json")
    assert json_proc.returncode == 1, json_proc.stderr
    assert json.loads(json_proc.stdout)["validation"]["ok"] is False


@pytest.mark.parametrize("flag", [[], ["--json"]])
def test_status_refuses_unreadable_canonical_file(mini_repo, flag):
    concepts = mini_repo / "knowledge/concepts.yaml"
    concepts.write_text(
        concepts.read_text(encoding="utf-8") + "\nbroken: [unclosed\n",
        encoding="utf-8")
    proc = run_los(mini_repo, "status", *flag)
    assert proc.returncode == 2, proc.stderr
    assert "knowledge/concepts.yaml" in proc.stderr
    assert not proc.stdout


def _strip_attempts(mini_repo):
    modules_path = mini_repo / "records/modules.yaml"
    data = yaml.safe_load(modules_path.read_text(encoding="utf-8"))
    for module in data["modules"]:
        module["attempts"] = []
    modules_path.write_text(yaml.safe_dump(data), encoding="utf-8")


def test_status_exam_line_names_module_files_not_frozen_snapshot(mini_repo):
    _strip_attempts(mini_repo)
    proc = run_los(mini_repo, "status")
    assert proc.returncode == 0, proc.stderr
    assert "no registered attempt in any module's module.yaml" in proc.stdout
    assert "records/modules.yaml" not in proc.stdout


def test_module_view_exam_line_names_module_files_not_frozen_snapshot(mini_repo):
    _strip_attempts(mini_repo)
    lines = _exam_spine_lines(load_repo(mini_repo))
    assert "(no registered attempt in any module's module.yaml)" in lines
    assert not any("records/modules.yaml" in line for line in lines)


def test_exam_spine_pending_lists_both_missing_fact_states(mini_repo):
    # #114 item 3: pending means no attempt recorded — an upcoming
    # sitting reads `registration not recorded` (the brief's phrase),
    # an elapsed one `unrecorded`. The manifest keeps `unregistered`.
    add_curriculum(mini_repo)
    module_path = mini_repo / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    future = (_dt.date.today() + _dt.timedelta(days=30)).isoformat()
    module["examination"]["sittings"][1]["date"] = future
    module["attempts"] = [att for att in module["attempts"]
                          if att.get("termin") != 2]
    write_yaml(module_path, module)
    repo = load_repo(mini_repo)
    rows = [row for row in _academic_deadlines(repo)
            if row.get("kind") == "exam" and row.get("termin") in (2, 3)]
    assert {row["registration_state"] for row in rows} == {
        "unregistered", "unrecorded"}
    lines = _exam_spine_lines(repo)
    assert "**Sittings with no registered attempt yet:**" in lines
    pending = [line for line in lines
               if "registration not recorded" in line or "unrecorded" in line]
    assert len(pending) == 2
    assert any("registration not recorded" in line for line in pending)
    assert any("— unrecorded" in line for line in pending)
    assert not any("not registered" in line for line in lines)


# ---------------------------------------------------------------- capture
def test_capture_text_lands_in_inbox_and_routing_stays_operator(mini_repo):
    key = "capture-half-formed-001"
    proc = approved_v2_call(
        mini_repo,
        capability="capture.create",
        payload={"text": "a half-formed thought", "title": "Half formed"},
        artifact_ids=[request_artifact_id("capture.create", key)],
        idempotency_key=key,
    )
    assert proc.returncode == 0, proc.stderr
    response = json.loads(proc.stdout)
    assert response["ok"] is True
    assert response["receipt_path"]
    inbox = mini_repo / "work" / "inbox"
    files = [f for f in inbox.iterdir() if f.suffix == ".md"]
    assert len(files) == 1
    body = files[0].read_text(encoding="utf-8")
    assert "a half-formed thought" in body
    assert "# Half formed" in body
    assert response["result"]["captured"] == files[0].relative_to(mini_repo).as_posix()


def test_capture_direct_cli_write_is_refused(mini_repo):
    proc = run_los(mini_repo, "capture", "--text", "must use the gateway")
    assert proc.returncode == 2
    assert "GatewayEnvelopeV2" in proc.stderr
    assert not list((mini_repo / "work" / "inbox").glob("*.md"))


def test_capture_empty_input_fails_cleanly(mini_repo):
    proc = run_los(mini_repo, "capture", "--text", "   ")
    assert proc.returncode == 2
    assert not list((mini_repo / "work" / "inbox").glob("*.md"))


def test_capture_file_copy(mini_repo, tmp_path):
    src = tmp_path / "photo-notes.txt"
    src.write_text("scanned scribbles", encoding="utf-8")
    key = "capture-photo-notes-001"
    proc = approved_v2_call(
        mini_repo,
        capability="capture.create",
        payload={"file": str(src), "file_sha256": file_sha256(src)},
        artifact_ids=[request_artifact_id("capture.create", key)],
        idempotency_key=key,
    )
    assert proc.returncode == 0, proc.stderr
    copied = mini_repo / "work" / "inbox" / "photo-notes.txt"
    assert copied.read_text(encoding="utf-8") == "scanned scribbles"
    assert src.exists()  # capture copies; it never destroys the original


# ------------------------------------------------------------- delegation
def test_validate_delegates_and_passes_on_clean_repo(mini_repo):
    proc = run_los(mini_repo, "validate")
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert "0 error(s)" in proc.stdout


def test_generate_delegates_and_writes_reading_room(mini_repo):
    proc = run_los(mini_repo, "generate")
    assert proc.returncode == 0, proc.stderr
    room = mini_repo / "generated" / "reading-room.md"
    assert room.exists()
    assert "GENERATED" in room.read_text(encoding="utf-8")[:400]


# ------------------------------------------- reading room & adoption view
def test_reading_room_composes_the_views(mini_repo):
    outputs = generate_all(load_repo(mini_repo), generated_at="T1")
    room = outputs["reading-room.md"]
    assert "2026-10-09" in room                      # exam spine (registered)
    assert "workspace-demo" in room                  # active workspace + next
    assert "Do the demo thing." in room
    assert "note-demo.md" in room                    # recently changed notes
    assert "coordination-view.md" in room            # links into deeper views
    assert "reports/health.md" in room
    assert "reviewed: 0/1" in room                   # adoption line


def test_health_carries_adoption_section(mini_repo):
    outputs = generate_all(load_repo(mini_repo), generated_at="T1")
    health = outputs["reports/health.md"]
    assert "Review & evidence adoption" in health
    assert "`reviewed` date: 0/1" in health
    assert "`evidence` entries: 0/1" in health


# ---------------------------------------------------------- concept canvas
def test_concept_canvas_is_valid_json_canvas(mini_repo):
    outputs = generate_all(load_repo(mini_repo), generated_at="T1")
    data = json.loads(outputs["concept-canvas.canvas"])
    assert "_generated" in data
    node_ids = {n["id"] for n in data["nodes"]}
    assert node_ids == {"concept-expected-value", "concept-variance"}
    for n in data["nodes"]:
        assert {"id", "type", "text", "x", "y", "width", "height"} <= set(n)
    # Study order, not the canonical sentence (ADR-016 decision 3). The
    # relation reads "variance builds on expected value"; the arrow has to point
    # at what you learn second.
    [edge] = data["edges"]
    assert edge["fromNode"] == "concept-expected-value"
    assert edge["fromSide"] == "right"
    assert edge["toNode"] == "concept-variance"
    assert edge["toSide"] == "left"
    assert edge["label"] == "prerequisite for (builds-on)"
    # Identity is canonical and unchanged, so this is a direction fix rather
    # than a rewrite of every edge in the file.
    assert edge["id"] == "concept-variance--builds-on--concept-expected-value"
    # prerequisite-depth layout: the dependent sits one layer right of its prereq
    xs = {n["id"]: n["x"] for n in data["nodes"]}
    assert xs["concept-variance"] > xs["concept-expected-value"]
    # note links rendered on the concept card
    ev = next(n for n in data["nodes"] if n["id"] == "concept-expected-value")
    assert "note-demo" in ev["text"]


def test_a_semantic_canvas_edge_keeps_its_canonical_direction(mini_repo):
    """Only the strict subgraph is a learning order, so only it is redrawn.

    A semantic arrow that flipped would assert an order the relation does not
    carry — the exact confusion ADR-016 decision 2 exists to prevent.
    """
    f = mini_repo / "knowledge" / "concept-relations.yaml"
    f.write_text(yaml.safe_dump({"relations": [
        {"from": "concept-variance", "type": "applies-in",
         "to": "concept-expected-value"},
    ]}))
    outputs = generate_all(load_repo(mini_repo), generated_at="T1")
    [edge] = json.loads(outputs["concept-canvas.canvas"])["edges"]
    assert edge["fromNode"] == "concept-variance"
    assert edge["fromSide"] == "left"
    assert edge["toNode"] == "concept-expected-value"
    assert edge["toSide"] == "right"
    assert edge["label"] == "applies-in"


def test_the_canvas_and_the_mermaid_map_agree_on_study_direction(mini_repo):
    """Both are generated from one relation set. A test that asserts one and
    not the other proves nothing — and until 2026-09-04 they disagreed."""
    outputs = generate_all(load_repo(mini_repo), generated_at="T1")
    [edge] = json.loads(outputs["concept-canvas.canvas"])["edges"]
    concept_map = outputs["concept-map.md"]

    # The map says so in its own header, and draws `requires` solid and
    # `builds-on` dotted. Either way the prerequisite is on the left.
    assert "Arrows point from prerequisite to dependent" in concept_map
    [arrow] = [ln for ln in concept_map.splitlines()
               if "-->" in ln or "-.->" in ln]
    left, right = arrow.split("->")
    assert "concept_expected_value" in left
    assert "concept_variance" in right

    # The canvas edge runs between the same two concepts in the same order.
    assert edge["fromNode"] == "concept-expected-value"
    assert edge["toNode"] == "concept-variance"


def test_adoption_counts_flag_drift_past_review(mini_repo):
    note = mini_repo / "knowledge" / "notes" / "mathematics" / "note-demo.md"
    text = note.read_text(encoding="utf-8")
    note.write_text(text.replace("created: 2026-07-16",
                                 "created: 2026-07-16\nreviewed: 2026-07-20"),
                    encoding="utf-8")
    ad = adoption_counts(load_repo(mini_repo))
    assert ad["notes_reviewed"] == 1
    # mini_repo has no Git history -> the note counts as changed-since-review
    assert ad["changed_since_review"] == ["note-demo"]


# ------------------------------------------------- F11: --json and usage
#: Every read command whose output is always JSON accepts --json as a no-op.
#: Each entry is (subcommand, argv tail satisfying its required arguments).
JSON_NOOP_COMMANDS = [
    ("ability-context", []),
    ("ai-action-list", []),
    ("ai-action-status", ["ai-request-demo"]),
    ("ai-action-validate-delivery", ["delivery-demo"]),
    ("atlas-context", ["concept-expected-value"]),
    ("backup-verify", ["--manifest", "M", "--restored-core", "C",
                       "--restored-ui", "U", "--restored-materials", "T"]),
    ("bootstrap", ["--brief"]),
    ("inbox-list", []),
    ("inbox-read", ["drop.md"]),
    ("inspect", ["note-demo"]),
    ("legacy-archive-inspect", ["--archive-root", "A", "--allowlist", "L"]),
    ("material-context", ["density"]),
    ("material-span", ["unit-demo-l01", "route-demo"]),
    ("module-list", []),
    ("note-read", ["note-demo"]),
    ("operations", []),
    ("plan-edit-context", ["unit-demo-l01"]),
    ("program-list", []),
    ("project-list", []),
    ("related", ["note-demo"]),
    ("runtime-session", ["--requirement", "req-demo"]),
    ("search", ["demo"]),
    ("semantic", ["--list"]),
    ("unit-list", []),
]


@pytest.mark.parametrize("command,tail", JSON_NOOP_COMMANDS)
def test_json_only_reads_accept_json_as_a_noop(command, tail):
    import los

    args = los.build_parser().parse_args([command, *tail, "--json"])
    assert args.json is True


def test_json_flag_keeps_read_bytes_identical(mini_repo):
    plain = run_los(mini_repo, "bootstrap", "--brief")
    assert plain.returncode == 0, plain.stderr
    flagged = run_los(mini_repo, "bootstrap", "--brief", "--json")
    assert flagged.returncode == 0, flagged.stderr
    assert flagged.stdout == plain.stdout

    plain = run_los(mini_repo, "inspect", "note-demo")
    assert plain.returncode == 0, plain.stderr
    flagged = run_los(mini_repo, "inspect", "note-demo", "--json")
    assert flagged.returncode == 0, flagged.stderr
    assert flagged.stdout == plain.stdout


def test_capability_backed_commands_take_no_added_json_flag(repo_root):
    """F11 never extends a command that backs a command capability.

    ``capture`` and ``garden-seed-create`` already shipped a functional
    --json before this round; every other backed parser takes none.
    """
    import los
    from learning_os.contracts.capability_catalog import command_definitions
    from learning_os.contracts.payloads import subparsers

    parsers = subparsers(los.build_parser())
    grandfathered = {"capture", "garden-seed-create"}
    for definition in command_definitions(repo_root).values():
        command = definition.cli_command or ""
        if command in grandfathered:
            continue
        parser = parsers[command]
        assert not any(action.dest == "json" for action in parser._actions), \
            command


def test_no_capability_schema_gains_a_json_property(repo_root):
    import los
    from learning_os.contracts.capability_catalog import command_definitions
    from learning_os.contracts.payload_records import resolve_all
    from learning_os.contracts.payloads import all_payload_schemas

    schemas = all_payload_schemas(
        los.build_parser(), command_definitions(repo_root),
        payload_records=resolve_all(repo_root))
    assert len(schemas) == 49
    for name, schema in schemas.items():
        assert "json" not in schema["properties"], name


@pytest.mark.parametrize("argv,usage,err", [
    (["inspect", "X", "--bogus"], "usage: los inspect",
     "unrecognized arguments: --bogus"),
    (["search", "demo", "--bogus"], "usage: los search",
     "unrecognized arguments: --bogus"),
    # A missing required positional still reports the subcommand's usage.
    (["inspect", "--bogus"], "usage: los inspect", "required: id"),
])
def test_unrecognized_argument_prints_subcommand_usage(mini_repo, argv, usage,
                                                      err):
    proc = run_los(mini_repo, *argv)
    assert proc.returncode == 2
    assert proc.stderr.startswith(usage), proc.stderr
    assert err in proc.stderr
    # Not the root listing of all ~93 subcommands.
    assert "ai-action-list" not in proc.stderr
    assert "workspace-next-action" not in proc.stderr


def test_root_error_still_prints_root_usage(mini_repo):
    proc = run_los(mini_repo, "--bogus")
    assert proc.returncode == 2
    assert proc.stderr.startswith("usage: los [-h]"), proc.stderr
    assert "los: error:" in proc.stderr

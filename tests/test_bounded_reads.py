"""Complete note retrieval and compact startup without hidden truncation."""
import json

import pytest
import yaml
from repo_builders import add_curriculum, run_los, write_yaml

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
    domains = {row["domain"]: row for row in data["domain_atlas"]}
    assert len(domains) >= 7
    repo = load_repo(mini_repo)
    assert sum(row["notes"] for row in domains.values()) == len(repo.notes)
    assert sum(row["shelves"] for row in domains.values()) == len(repo.collections)


def test_domain_glance_keeps_empty_future_and_unbucketed_domains():
    from learning_os.commands.reads import _domain_glance

    records = [
        {"type": "note", "domain": "future", "role": "crosswalk"},
        {"type": "note", "domain": ""},
        {"type": "collection", "domain": "cross-domain", "entries": [{}, {}]},
        {"type": "topic-pack", "domain": "cross-domain", "entries": [{}]},
        {"type": "note", "domain": "nested", "path": "knowledge/notes/data-systems/nested/note.md"},
        {"type": "source", "domain": "future"},
    ]
    glance = _domain_glance({"records": records})
    assert glance == _domain_glance({"records": records[::-1]})
    domains = {row["domain"]: row for row in glance}
    assert domains["mathematics"]["notes"] == 0
    assert domains["future"]["notes"] == domains["future"]["crosswalks"] == 1
    assert domains["data-systems"]["notes"] == 1
    assert "nested" not in domains
    assert domains["cross-domain"] == {"domain": "cross-domain", "notes": 1,
                                       "crosswalks": 0, "shelves": 2, "entries": 3}


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

def _two_route_context(mini_repo):
    """One unit with two resolvable routes, the first fully stage-wired."""
    import yaml
    from repo_builders import material_fixture, write_yaml

    from learning_os.material_refs import unit_routes

    repo, first_id, smid = material_fixture(mini_repo)
    unit_id = repo.study_maps[smid].unit_id
    smap_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    smap = yaml.safe_load(smap_path.read_text(encoding="utf-8"))
    base = dict(smap["sources"][0]["unit_routes"][0])
    base.pop("id", None)
    base.update(title="Second derivation", locator="lecture-02.pdf",
                covers=["knowledge-demo-outcomes"])
    smap["sources"][0]["unit_routes"].append(base)
    write_yaml(smap_path, smap)
    material = repo.materials_root / "source-demo-book/lecture-02.pdf"
    material.parent.mkdir(parents=True, exist_ok=True)
    material.write_text("synthetic lecture two", encoding="utf-8")
    fresh = load_repo(mini_repo)
    assert not fresh.parse_failures
    routes = unit_routes(
        fresh.module_source_maps["module-demo"], "module-demo", unit_id)
    ids = [row["id"] for row in routes]
    assert len(ids) == 2 and len(set(ids)) == 2
    assert first_id in ids
    return unit_id, ids


def test_route_batch_matches_scalar_per_item_in_requested_order(mini_repo):
    unit_id, (first, second) = _two_route_context(mini_repo)
    scalar = {}
    for rid in (first, second):
        proc = run_los(mini_repo, "plan-edit-context", unit_id,
                       "--route-id", rid)
        assert proc.returncode == 0, proc.stderr
        scalar[rid] = json.loads(proc.stdout)
    batch = run_los(mini_repo, "plan-edit-context", unit_id,
                    "--route-ids", second, first)
    assert batch.returncode == 0, batch.stderr
    payload = json.loads(batch.stdout)
    assert payload["contract"] == "plan-edit-context-batch"
    assert payload["requested_route_ids"] == [second, first]
    assert [entry["route"]["id"] for entry in payload["routes"]] == [
        second, first]
    for entry, rid in zip(payload["routes"], [second, first], strict=True):
        assert entry == {key: scalar[rid][key] for key in (
            "route", "uses", "patch_fields", "patch_capability")}
    for key in ("unit_id", "module_id", "snapshot_id", "artifact_revisions",
                "preflight"):
        assert payload[key] == scalar[first][key]
    assert payload["routes"][0]["uses"] or payload["routes"][1]["uses"]


def test_route_batch_refuses_bad_requests_without_partial_payload(mini_repo):
    unit_id, (first, _) = _two_route_context(mini_repo)
    missing = run_los(mini_repo, "plan-edit-context", unit_id,
                      "--route-ids", first, "route-missing")
    assert missing.returncode != 0
    assert not missing.stdout
    assert "missing or ambiguous" in missing.stderr
    duplicate = run_los(mini_repo, "plan-edit-context", unit_id,
                        "--route-ids", first, first)
    assert duplicate.returncode != 0
    assert not duplicate.stdout
    assert "distinct" in duplicate.stderr
    oversized = run_los(mini_repo, "plan-edit-context", unit_id,
                        "--route-ids", *(f"route-{n}" for n in range(21)))
    assert oversized.returncode != 0
    assert not oversized.stdout
    assert "at most 20" in oversized.stderr


def test_stage_scoped_read_returns_flags_without_the_map(mini_repo):
    """One stage's own flags and placements, not the 127 KB map inspect."""
    import yaml
    from repo_builders import add_curriculum, write_yaml

    add_curriculum(mini_repo)
    staged = yaml.safe_load(
        (mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml")
        .read_text(encoding="utf-8"))
    staged["stages"][0]["scope_triage"] = "required-now"
    staged["stages"][0]["exam_critical"] = True
    write_yaml(mini_repo / "curriculum/modules/module-demo/units/unit-demo-l01/study-map.yaml",
               staged)
    proc = run_los(mini_repo, "plan-edit-context", "unit-demo-l01",
                   "--stage-id", "stage-demo")
    assert proc.returncode == 0, proc.stderr
    payload = json.loads(proc.stdout)
    assert payload["contract"] == "plan-edit-context-stage"
    assert payload["requested_stage_id"] == "stage-demo"
    assert payload["stage"]["scope_triage"] == "required-now"
    assert payload["stage"]["exam_critical"] is True
    assert payload["stage"]["id"] == "stage-demo"
    assert "full unit context" in payload["scope"]
    assert len(proc.stdout.encode()) < 65536


def test_stage_scoped_read_refuses_missing_stage_and_mixed_selectors(mini_repo):
    from repo_builders import add_curriculum

    add_curriculum(mini_repo)
    missing = run_los(mini_repo, "plan-edit-context", "unit-demo-l01",
                      "--stage-id", "stage-missing")
    assert missing.returncode != 0
    assert not missing.stdout
    assert "missing or ambiguous" in missing.stderr
    unit_id, (first, _) = _two_route_context(mini_repo)
    mixed = run_los(mini_repo, "plan-edit-context", unit_id,
                    "--stage-id", "stage-demo", "--route-id", first)
    assert mixed.returncode == 2


def test_route_batch_cli_parsing_rejects_empty_and_mixed_selectors(mini_repo):
    unit_id, (first, _) = _two_route_context(mini_repo)
    bare = run_los(mini_repo, "plan-edit-context", unit_id, "--route-ids")
    assert bare.returncode == 2
    mixed = run_los(mini_repo, "plan-edit-context", unit_id,
                    "--route-id", first, "--route-ids", first)
    assert mixed.returncode == 2


def test_route_batch_uses_one_repository_load(mini_repo, monkeypatch):
    import los
    from learning_os.commands import material as material_commands

    unit_id, (first, second) = _two_route_context(mini_repo)
    loads = []
    real_load = material_commands.load_repo

    def counting(root):
        loads.append(root)
        return real_load(root)

    monkeypatch.setattr(material_commands, "load_repo", counting)
    args = los.build_parser().parse_args(
        ["--root", str(mini_repo), "plan-edit-context", unit_id,
         "--route-ids", first, second])
    assert material_commands.cmd_plan_edit_context(args) == 0
    assert len(loads) == 1


def test_route_batch_snapshot_conflict_refuses_whole_response(
    mini_repo, monkeypatch, capsys,
):
    import los
    from learning_os.commands import material as material_commands
    from learning_os.commands import reads as reads_commands
    from learning_os.commands.support import WriteRefused

    unit_id, (first, second) = _two_route_context(mini_repo)
    real_fingerprint = reads_commands.canonical_fingerprint

    def flipping(root):
        if flipping.calls:
            return "deadbeef-changed"
        flipping.calls.append(root)
        return real_fingerprint(root)

    flipping.calls = []
    monkeypatch.setattr(
        reads_commands, "canonical_fingerprint", flipping)
    args = los.build_parser().parse_args(
        ["--root", str(mini_repo), "plan-edit-context", unit_id,
         "--route-ids", first, second])
    with pytest.raises(WriteRefused, match="snapshot"):
        material_commands.cmd_plan_edit_context(args)
    assert capsys.readouterr().out == ""


def test_route_batch_refuses_a_cross_unit_route(mini_repo):
    """A route that exists in the module but under another unit is
    refused for this unit — per-unit scoping, same path as missing."""
    import yaml
    from repo_builders import material_fixture, write_yaml

    from learning_os.material_refs import unit_routes

    repo, _, smid = material_fixture(mini_repo)
    unit_id = repo.study_maps[smid].unit_id
    smap_path = mini_repo / "curriculum/modules/module-demo/source-map.yaml"
    smap = yaml.safe_load(smap_path.read_text(encoding="utf-8"))
    base = dict(smap["sources"][0]["unit_routes"][0])
    base.pop("id", None)
    base.update(title="Foreign derivation", locator="lecture-09.pdf",
                covers=["knowledge-demo-outcomes"], unit_id="unit-demo-l02")
    smap["sources"][0]["unit_routes"].append(base)
    write_yaml(smap_path, smap)
    fresh = load_repo(mini_repo)
    assert not fresh.parse_failures
    foreign = unit_routes(
        fresh.module_source_maps["module-demo"], "module-demo",
        "unit-demo-l02")
    assert len(foreign) == 1
    proc = run_los(mini_repo, "plan-edit-context", unit_id,
                   "--route-ids", foreign[0]["id"])
    assert proc.returncode != 0
    assert not proc.stdout
    assert "missing or ambiguous" in proc.stderr


def test_route_helper_refuses_unknown_and_ambiguous_ids():
    from learning_os.commands.material import _route
    from learning_os.commands.support import WriteRefused

    rows = [{"id": "route-a"}, {"id": "route-a"}, {"id": "route-b"}]
    with pytest.raises(WriteRefused, match="missing or ambiguous"):
        _route(rows, "route-missing")
    with pytest.raises(WriteRefused, match="missing or ambiguous"):
        _route(rows, "route-a")
    assert _route(rows, "route-b") == {"id": "route-b"}


def test_search_succeeds_despite_malformed_project(mini_repo):
    # A read refuses only when the failures actually affect the answer it is about to give.
    note = next(iter(load_repo(mini_repo).notes.values()))
    with note.path.open("a", encoding="utf-8") as f:
        f.write("\nNeedleUnfindable explanation.\n")
    
    # Break a non-note file (modules)
    module_path = mini_repo / "records" / "modules.yaml"
    original_module_text = module_path.read_text(encoding="utf-8")
    broken_module_text = original_module_text.replace("modules:", "modules: [broken")
    module_path.write_text(broken_module_text, encoding="utf-8")
    
    try:
        response = run_los(mini_repo, "search", "NeedleUnfindable", "--type", "note", "--content")
        assert response.returncode == 0, response.stderr
        payload = json.loads(response.stdout)
        assert len(payload.get("items", [])) > 0
    finally:
        module_path.write_text(original_module_text, encoding="utf-8")


def test_brief_startup_is_one_guarded_page_with_runnable_expands(mini_repo):
    add_curriculum(mini_repo)
    brief = run_los(mini_repo, "bootstrap", "--brief")
    assert brief.returncode == 0, brief.stderr
    data = json.loads(brief.stdout)
    assert data["contract"] == "bootstrap-brief"
    assert data["snapshot_id"].startswith("sha256:")
    assert "resume_pointer" in data and "counts" in data
    # The mapped demo unit owes nothing; its active map is resumable.
    assert data["owed_study_maps"] == []
    assert [row["id"] for row in data["active_study_maps"]] == ["study-map-demo-l01"]
    assert data["active_study_maps"][0]["current_stage"] == "stage-demo"
    assert data["deadline_count"] == len(data["academic_deadlines"]) > 0
    assert {row["module_id"] for row in data["academic_deadlines"]
            if row.get("module_id")} == {"module-demo"}
    expands = data["expand"]
    for key in ("full_compact", "continuation", "resume", "inspect",
                "note_read", "content_search", "material_context",
                "capability_detail"):
        assert expands[key], key
    assert expands["plan_brief"] == []
    assert len(brief.stdout.encode()) < 65536
    # A second unit without a map is owed, with its own prep command.
    module_path = mini_repo / "curriculum/modules/module-demo/module.yaml"
    module = yaml.safe_load(module_path.read_text(encoding="utf-8"))
    module["unit_order"].append("unit-demo-l02")
    write_yaml(module_path, module)
    write_yaml(mini_repo / "curriculum/modules/module-demo/units/unit-demo-l02/unit.yaml", {
        "id": "unit-demo-l02", "type": "unit", "module_id": "module-demo",
        "kind": "lecture", "title": "Variance", "order": 2,
        "scope": "The lecture as taught.", "status": "active",
        "scope_sources": [], "artifacts": {}, "workspace_ids": [],
    })
    again = run_los(mini_repo, "bootstrap", "--brief")
    assert again.returncode == 0, again.stderr
    owed = json.loads(again.stdout)
    assert owed["owed_study_maps"] == ["unit-demo-l02"]
    assert owed["expand"]["plan_brief"] == ["plan-edit-context unit-demo-l02 --brief"]


def test_brief_startup_refuses_paging_and_mixed_modes(mini_repo):
    for args in (("bootstrap", "--brief", "--offset", "1"),
                 ("bootstrap", "--brief", "--compact")):
        result = run_los(mini_repo, *args)
        assert result.returncode != 0
        assert not result.stdout


def test_brief_pointer_state_confirmed_when_the_pointer_resolves(mini_repo):
    add_curriculum(mini_repo)
    brief = run_los(mini_repo, "bootstrap", "--brief")
    assert brief.returncode == 0, brief.stderr
    data = json.loads(brief.stdout)
    assert data["pointer_state"] == "confirmed"
    assert data["pointer_state_note"].startswith("confirmed =")
    # A confirmed stop is not a priority choice: workspace options remain.
    assert [row["workspace_id"] for row in data["recorded_options"]] == ["workspace-demo"]
    assert "not current priorities" in data["recorded_options_note"]
    assert data["expand"]["coordination"] == "inspect coordination"
    assert data["expand"]["intelligence_scan"] == "intelligence-scan --brief --json"
    assert [row["id"] for row in data["active_study_maps"]] == ["study-map-demo-l01"]
    # The brief agrees with resume about what the pointer means.
    resumed = run_los(mini_repo, "resume", "--json")
    assert resumed.returncode == 0, resumed.stderr
    assert json.loads(resumed.stdout)["via"] == "resume pointer"


def test_brief_pointer_missing_shows_unranked_recorded_options(mini_repo):
    add_curriculum(mini_repo)
    (mini_repo / "curriculum/resume.yaml").unlink()
    # A second active track: the page must show both, never pick one.
    second = mini_repo / "work/active/workspace-second/CONTEXT.md"
    second.parent.mkdir(parents=True)
    second.write_text(
        "---\nid: workspace-second\ntype: workspace\ntitle: Second\n"
        "status: active\n---\n\n## Objective\n\nSecond.\n\n"
        "## Next Action\n\nDo the second thing.\n", encoding="utf-8")
    brief = run_los(mini_repo, "bootstrap", "--brief")
    assert brief.returncode == 0, brief.stderr
    data = json.loads(brief.stdout)
    assert data["pointer_state"] == "missing"
    assert data["recorded_options"] == [
        {"workspace_id": "workspace-demo",
         "next_action": "Do the demo thing.",
         "source": "work/active/workspace-demo/CONTEXT.md"},
        {"workspace_id": "workspace-second",
         "next_action": "Do the second thing.",
         "source": "work/active/workspace-second/CONTEXT.md"},
    ]
    for option in data["recorded_options"]:
        assert set(option) == {"workspace_id", "next_action", "source"}
    assert [row["id"] for row in data["active_study_maps"]] == ["study-map-demo-l01"]


def test_brief_pointer_invalid_matches_missing(mini_repo):
    add_curriculum(mini_repo)
    pointer_path = mini_repo / "curriculum/resume.yaml"
    pointer = yaml.safe_load(pointer_path.read_text(encoding="utf-8"))
    pointer["stage_id"] = "stage-no-such-stage"
    write_yaml(pointer_path, pointer)
    brief = run_los(mini_repo, "bootstrap", "--brief")
    assert brief.returncode == 0, brief.stderr
    data = json.loads(brief.stdout)
    assert data["pointer_state"] == "invalid"
    assert [opt["workspace_id"] for opt in data["recorded_options"]] == ["workspace-demo"]


def test_search_surfaces_garden_seeds_and_inbox_filenames(mini_repo):
    from learning_os.garden import garden_id

    garden = mini_repo / "knowledge/garden"
    garden.mkdir(parents=True, exist_ok=True)
    (garden / "zephyrquux-garden.md").write_text(
        "# Zephyrquux garden seed\n\nA seedling thought.\n", encoding="utf-8")
    (mini_repo / "work/inbox/20260910-tessera-todo.md").write_text(
        "tessera todo\n", encoding="utf-8")
    seed_id = garden_id(garden, garden / "zephyrquux-garden.md")
    rows = json.loads(run_los(mini_repo, "search", "Zephyrquux").stdout)
    seed = next((row for row in rows if row.get("id") == seed_id), None)
    assert seed is not None, rows
    assert seed["type"] == "garden-note"
    assert seed["state"] == "seed"
    assert set(seed) == {"id", "type", "title", "path", "status", "state", "deprecated"}
    rows = json.loads(run_los(mini_repo, "search", "tessera-todo").stdout)
    drop = next((row for row in rows if row.get("type") == "inbox-item"), None)
    assert drop is not None, rows
    assert drop["id"] == "20260910-tessera-todo.md"
    assert drop["path"] == "work/inbox/20260910-tessera-todo.md"
    assert json.loads(run_los(mini_repo, "search", "tessera-todo",
                              "--type", "note").stdout) == []


def test_note_read_resolves_a_garden_seed(mini_repo):
    from learning_os.garden import garden_id

    garden = mini_repo / "knowledge/garden"
    garden.mkdir(parents=True, exist_ok=True)
    (garden / "kernel-thought.md").write_text(
        "# Kernel thought\n\nThe third meaning of kernel.\n", encoding="utf-8")
    seed_id = garden_id(garden, garden / "kernel-thought.md")
    response = run_los(mini_repo, "note-read", seed_id)
    assert response.returncode == 0, response.stderr
    row = json.loads(response.stdout)
    assert row["contract"] == "note-content"
    assert row["note_id"] == seed_id
    assert "The third meaning of kernel." in row["content"]
    assert row["snapshot_id"].startswith("sha256:")


def test_inbox_read_serves_text_and_refuses_binary_escape_and_missing(mini_repo):
    inbox = mini_repo / "work/inbox"
    (inbox / "todo.md").write_text("hello inbox\n", encoding="utf-8")
    response = run_los(mini_repo, "inbox-read", "todo.md")
    assert response.returncode == 0, response.stderr
    row = json.loads(response.stdout)
    assert row["contract"] == "inbox-content"
    assert row["item"] == "todo.md"
    assert row["content"] == "hello inbox\n"
    assert row["snapshot_id"].startswith("sha256:")
    (inbox / "blob.bin").write_bytes(b"\x00\x01\x02\xff")
    refused = run_los(mini_repo, "inbox-read", "blob.bin")
    assert refused.returncode != 0
    assert "not UTF-8" in refused.stderr
    link = inbox / "link.md"
    link.symlink_to(inbox / "todo.md")
    linked = run_los(mini_repo, "inbox-read", "link.md")
    assert linked.returncode != 0
    assert "symlink" in linked.stderr
    assert run_los(mini_repo, "inbox-read", "../active/x").returncode != 0
    missing = run_los(mini_repo, "inbox-read", "nope.md")
    assert missing.returncode != 0
    assert "not found" in missing.stderr


def test_search_rows_carry_state_and_deprecated(mini_repo):
    concepts = json.loads(run_los(mini_repo, "search", "Expected",
                                  "--type", "concept").stdout)
    assert concepts, "mini concept must match"
    assert all("deprecated" in row for row in concepts)
    notes = json.loads(run_los(mini_repo, "search", "note-demo",
                               "--type", "note").stdout)
    assert notes, "mini note must match"
    assert all("state" in row for row in notes)


def test_inbox_list_lists_names_without_reading_bytes(mini_repo):
    listed = run_los(mini_repo, "inbox-list")
    assert listed.returncode == 0, listed.stderr
    assert json.loads(listed.stdout) == []
    inbox = mini_repo / "work/inbox"
    (inbox / "todo.md").write_text("hello inbox\n", encoding="utf-8")
    (inbox / "blob.bin").write_bytes(b"\x00\x01\x02\xff")
    (inbox / ".hidden.md").write_text("dot-file\n", encoding="utf-8")
    listed = run_los(mini_repo, "inbox-list")
    assert listed.returncode == 0, listed.stderr
    rows = json.loads(listed.stdout)
    assert [row["id"] for row in rows] == ["blob.bin", "todo.md"]
    assert all(row["type"] == "inbox-item" for row in rows)
    assert all(set(row) == {"id", "type", "title", "path", "status",
                            "state", "deprecated"} for row in rows)
    assert rows[0]["path"] == "work/inbox/blob.bin"

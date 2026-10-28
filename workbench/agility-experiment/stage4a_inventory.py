#!/usr/bin/env python3
"""Read-only thesis migration inventory; writes its report outside Core."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import yaml

BASE = Path(__file__).resolve().parent
ROOT = BASE / "repository"
PROJECT = "project-bachelor-thesis"
MODULE = "module-project-bachelor-thesis"
WORKSPACE = "workspace-thesis-mle-medical"
PROJECT_PATH = "projects/registry/project-bachelor-thesis.yaml"
MODULE_PATH = "curriculum/modules/module-project-bachelor-thesis/module.yaml"
WORKSPACE_PATH = "work/active/workspace-thesis-mle-medical/CONTEXT.md"


def digest(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def yaml_file(path: str):
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def leaves(value, pointer=""):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from leaves(child, pointer + "/" + str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from leaves(child, pointer + "/" + str(index))
    else:
        yield pointer, value


def structure_nodes(nodes):
    for node in nodes:
        yield node
        yield from structure_nodes(node.get("children", []))


def main() -> None:
    global ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ROOT = args.root.resolve()
    out = args.output.resolve()
    if out == ROOT or ROOT in out.parents:
        parser.error("the inventory report must stay outside the source checkout")
    assert not git("status", "--porcelain=v1"), "source checkout must be clean"
    project = yaml_file(PROJECT_PATH)
    module = yaml_file(MODULE_PATH)
    relations = yaml_file("projects/relations/project-relations.yaml")["relations"]
    aliases = yaml_file("projects/aliases.yaml")["aliases"]
    workspace_text = (ROOT / WORKSPACE_PATH).read_text(encoding="utf-8")
    workspace_meta = yaml.safe_load(workspace_text.split("---", 2)[1])
    assert project["id"] == PROJECT and module["id"] == MODULE
    assert module["compatibility_only"] is True
    assert project["unit_ids"] == module["unit_order"] == workspace_meta["unit_ids"]
    assert project["workspace_ids"] == [WORKSPACE]
    assert workspace_meta["project_id"] == PROJECT
    assert aliases[MODULE] == PROJECT

    active_content = WORKSPACE_PATH + "#Research context"
    history = "migration/backups/projects-to-modules-v62/ (original bytes and field map)"
    destinations = {
        "boundaries": WORKSPACE_PATH + "#Access boundaries",
        "decisions": WORKSPACE_PATH + "#Research decisions",
        "files": WORKSPACE_PATH + "#Materials and deliverables",
        "id": MODULE_PATH + ":id; old Project ID redirects to Module",
        "linked_module_ids": MODULE_PATH + ":related_module_ids; relationship explanations stay in workspace",
        "migrated_at": history, "migrated_from": history, "migration": history,
        "milestone_ids": WORKSPACE_PATH + "#Milestone identity map; existing Unit IDs remain unchanged",
        "objective": active_content + " (verbatim retained scope; existing Objective prose preserved)",
        "project_type": active_content + " (thesis classification; no new entity)",
        "revision": "Existing Project revision history/receipts remain literal; new Module revision remains its own token",
        "root_uri": WORKSPACE_PATH + "#Access boundaries",
        "schema_version": history, "source_sha256": history,
        "status": MODULE_PATH + ":status (active remains active; no completion inferred)",
        "structure": WORKSPACE_PATH + "#Research workstreams (parallel/nested structure and stable anchors)",
        "thematic_group_ids": MODULE_PATH + ":thematic_group_ids (preserve existing union, no inferred tags)",
        "title": MODULE_PATH + ":title",
        "type": "Module entity; original Project type retained in migration history",
        "unit_ids": MODULE_PATH + ":unit_order (identical existing IDs and order)",
        "workspace_ids": WORKSPACE_PATH + ":module_ids (existing owning workspace)",
    }
    assert set(destinations) == set(project), "unmapped or obsolete top-level field"
    field_map = [{"source_pointer": pointer,
                  "source_value_sha256": digest(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()),
                  "destination": destinations[pointer.split("/")[1]]}
                 for pointer, value in leaves(project)]
    relation_map = [{"source_pointer": pointer,
                     "source_value_sha256": digest(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()),
                     "destination": WORKSPACE_PATH + "#Materials and deliverables (verbatim reasons/contributions and stable IDs)"}
                    for pointer, value in leaves(relations)]

    nodes = list(structure_nodes(project["structure"]["nodes"]))
    legacy_targets = {PROJECT: MODULE}
    for row in [*nodes, *project["decisions"], *relations]:
        legacy_targets[row["id"]] = WORKSPACE
    for old, unit_id in zip(project["milestone_ids"], project["unit_ids"], strict=True):
        legacy_targets[old] = unit_id

    paths = {PROJECT_PATH, MODULE_PATH, WORKSPACE_PATH, "curriculum/resume.yaml",
             "system/contracts/data-contract.yaml",
             "projects/aliases.yaml", "projects/relations/project-relations.yaml",
             "operations/transactions/revisions.yaml", "operations/transactions/idempotency.yaml",
             "curriculum/programs/program-bachelors.yaml", "curriculum/programs/program-thesis-projects.yaml",
             "curriculum/modules/module-project-bachelor-thesis/source-map.yaml"}
    unit_paths = []
    map_paths = []
    for unit_id in project["unit_ids"]:
        unit_path = f"curriculum/modules/{MODULE}/units/{unit_id}/unit.yaml"
        paths.add(unit_path)
        unit_paths.append(unit_path)
        assert yaml_file(unit_path)["module_id"] == MODULE
        study_path = str(Path(unit_path).parent / "study-map.yaml")
        if (ROOT / study_path).is_file():
            paths.add(study_path)
            map_paths.append(study_path)
            for stage in yaml_file(study_path)["stages"]:
                if stage.get("working_note"):
                    paths.add(stage["working_note"])
    for row in project["files"]:
        candidate = (ROOT / row["path"]).resolve()
        candidate.relative_to(ROOT.resolve())
        assert candidate.is_file(), row["path"]
        paths.add(row["path"])
    optional_absent = {"curriculum/resume.yaml"}
    assert all((ROOT / path).is_file() or path in optional_absent for path in paths)
    source_hashes = {path: digest((ROOT / path).read_bytes()) if (ROOT / path).is_file() else None
                     for path in sorted(paths)}

    protected_academic_fields = ("institution", "semester", "code", "credits", "examination", "attempts", "grade")
    academic_facts = {key: module[key] for key in protected_academic_fields if key in module}
    revisions = yaml_file("operations/transactions/revisions.yaml")["revisions"]
    assert module["kind"] == "project"
    assert not academic_facts, "new academic facts require explicit preservation review"
    assert "No registration or deadline facts yet" in (ROOT / "work/COORDINATION.md").read_text()

    pattern = r"(?<![a-z0-9-])(?:" + "|".join(re.escape(k) for k in [MODULE, *legacy_targets]) + r")(?![a-z0-9-])"
    scan = subprocess.run(["rg", "--json", "--pcre2", "--no-ignore", "-n", "-e", pattern,
                           "--glob", "*.yaml", "--glob", "*.md", "--glob", "*.json",
                           "--glob", "!work/proposals/**", "--glob", "!operations/diagnostics/**",
                           "curriculum", "projects", "work", "knowledge", "sources", "records", "operations"],
                          cwd=ROOT, text=True, capture_output=True, check=False)
    assert scan.returncode in (0, 1), scan.stderr
    references = []
    for line in scan.stdout.splitlines():
        row = json.loads(line)
        if row["type"] != "match":
            continue
        data = row["data"]
        path = data["path"]["text"]
        references.append({"path": path, "line": data["line_number"],
                           "ids": sorted(set(re.findall(pattern, data["lines"]["text"]))),
                           "handling": "historical evidence; do not rewrite" if path.startswith("operations/")
                           else "inspect in bounded migration; preserve owned Units/maps and prose"})

    assert all((digest((ROOT / path).read_bytes()) if (ROOT / path).is_file() else None) == value
               for path, value in source_hashes.items())
    assert not git("status", "--porcelain=v1"), "inventory wrote into the source checkout"
    result = {
        "stage": "4A", "mode": "read-only inventory and dry-run specification",
        "source_commit": git("rev-parse", "HEAD"), "canonical_files_written": 0,
        "source_data_contract": yaml_file("system/contracts/data-contract.yaml")["contract_version"],
        "inventory_tool_sha256": digest(Path(__file__).read_bytes()),
        "counts": {"active_project_records": len(list((ROOT / "projects/registry").glob("*.yaml"))),
                   "top_level_fields": len(project), "mapped_leaf_values": len(field_map),
                   "workstream_nodes": len(nodes), "decisions": len(project["decisions"]),
                   "relationships": len(relations), "mapped_relationship_leaf_values": len(relation_map),
                   "file_references": len(project["files"]),
                   "units": len(unit_paths), "existing_study_maps": len(map_paths)},
        "source_sha256": source_hashes, "field_ownership": field_map,
        "relationship_field_ownership": relation_map,
        "expected_revisions": {key: revisions.get(key, 0) for key in (MODULE, PROJECT, WORKSPACE)},
        "legacy_owner_redirects": legacy_targets, "remove_reverse_alias": {MODULE: PROJECT},
        "academic_decision": {"module_kind": "project (unchanged in consolidation)",
                              "area_id": "program-bachelors", "existing_academic_facts": academic_facts,
                              "unknowns": ["registration", "institution", "semester", "credits", "grade"],
                              "rule": "No academic facts inferred; research progress is not awarded degree credit. Preserve future supplied facts on the same Module owner."},
        "proposed_record_edits": [MODULE_PATH, WORKSPACE_PATH, "projects/aliases.yaml", "projects/relations/project-relations.yaml"],
        "proposed_retirement": PROJECT_PATH,
        "required_code_before_apply": ["bounded alias schema/validation/projection owner targets",
                                       "guarded, receipt-producing migration in fixtures",
                                       "Core/UI ordinary-Module visibility and historical navigation",
                                       "Open workspace context action and active content access tests"],
        "preserve_verbatim": unit_paths + map_paths + ["curriculum/resume.yaml", "historical transaction receipts and revision identities", "existing workspace body"],
        "references": references,
        "acceptance_limit": "Not an applicable migration or approval; no schema/record/UI changes. 4B/4C remain gated.",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(out), "counts": result["counts"], "references": len(references), "canonical_files_written": 0}, indent=2))


if __name__ == "__main__":
    main()

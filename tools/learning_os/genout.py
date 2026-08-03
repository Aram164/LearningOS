"""Deterministic generation of all derived outputs (BUILD-SPEC Step 5).

Outputs (all under generated/, gitignored, rebuildable, never canonical):
  manifest.json, concept-index.md, source-index.md (incl. per-lecture and
  per-concept selector views), module-view.md, coordination-view.md,
  backlinks.json, nebula.md (the Garden index — §14), reports/health.md.

Fully deterministic for a given committed tree: all collections sorted by ID;
Git-derived neglect signals depend only on repository state; the generation
timestamp is the last-commit timestamp, so regeneration without new commits
is byte-for-byte reproducible.
"""

from __future__ import annotations

import datetime as _dt
import json
import hashlib
import os
import re
import subprocess
from pathlib import Path, PurePosixPath

from . import __version__
from .loader import Repo

LECTURE_KEY_RE = re.compile(r"^(?:VL\s*)?L?\d{1,2}\b")

SELECTOR_ROLES = ("first-learning", "review", "implementation")


def mermaid_node_ids(ids) -> dict[str, str]:
    """Map concept IDs to unique, Mermaid-safe node identifiers.

    Sanitizing an ID to Mermaid's allowed character set can map distinct IDs to
    the same token (e.g. 'concept-a-b' and 'concept-a.b' both collapse to
    'concept_a_b'). Emitting two nodes with an identical identifier silently
    merges them in the rendered graph. Assigning a disambiguating suffix on
    collision guarantees every input ID gets its own node. Deterministic:
    inputs are processed in sorted order.
    """
    mapping: dict[str, str] = {}
    used: set[str] = set()
    for cid in sorted(ids):
        base = re.sub(r"[^0-9A-Za-z_]", "_", cid)
        if not base or not (base[0].isalpha() or base[0] == "_"):
            base = "n_" + base
        name = base
        i = 2
        while name in used:
            name = f"{base}__{i}"
            i += 1
        used.add(name)
        mapping[cid] = name
    return mapping


def _md_header(title: str, generated_at: str) -> list[str]:
    return [
        f"# {title}",
        "",
        "> ⚠️ GENERATED file — a disposable VIEW over the canonical records, not "
        "part of the canonical architecture. Never edit; edit canonical inputs "
        f"instead. Rebuilt by `python tools/generate.py` (learning_os v{__version__}) "
        "from: knowledge/, sources/, curriculum/, records/, work/.",
        f"> Generated: {generated_at}",
        "",
    ]


def _json_header(generated_at: str) -> dict:
    return {
        "warning": "GENERATED file - do not edit; rebuilt by python tools/generate.py",
        "generator": f"learning_os v{__version__}",
        "generated_at": generated_at,
    }


def _slug(heading: str) -> str:
    """GitHub-style anchor for a Markdown heading."""
    s = heading.lower()
    s = "".join(ch for ch in s if ch.isalnum() or ch in " -")
    return s.replace(" ", "-")


def _letter_toc(entries: list[tuple[str, str]]) -> list[str]:
    """Compact letter-grouped table of contents.

    entries: (display text, heading text used for the anchor), pre-sorted.
    Returns one line per starting letter: 'A: [x](#x) · [y](#y)'.
    """
    lines: list[str] = []
    by_letter: dict[str, list[str]] = {}
    for display, heading in entries:
        letter = display[:1].upper() if display else "#"
        if not letter.isalpha():
            letter = "#"
        by_letter.setdefault(letter, []).append(f"[{display}](#{_slug(heading)})")
    for letter in sorted(by_letter):
        lines.append(f"**{letter}:** " + " · ".join(by_letter[letter]))
        lines.append("")
    return lines


def _git_last_commit(root: Path, rel: str) -> str:
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", rel],
                             cwd=root, capture_output=True, text=True, timeout=30)
        return out.stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def stable_generated_at(root: Path) -> str:
    """Reproducible generation timestamp: the repository's last-commit time.

    Regenerating without new commits yields byte-for-byte identical output
    (improvement: no wall-clock noise in generated files). Falls back to a
    fixed marker when Git is unavailable (e.g. synthetic test repos).
    """
    try:
        out = subprocess.run(["git", "log", "-1", "--format=%cI"],
                             cwd=root, capture_output=True, text=True, timeout=30)
        ts = out.stdout.strip()
        if out.returncode == 0 and ts:
            return f"{ts} (last commit)"
    except Exception:  # noqa: BLE001
        pass
    return "(no Git history available)"


# --------------------------------------------------------------------- build
def _material_location(repo: Repo, ref) -> dict:
    """Resolve a ``material://`` URI to a path relative to the LearningOS root
    (the vault's parent) plus an existence flag. Interfaces get a path they can
    hand to the OS file opener; the resolution rule stays here."""
    if not ref or not str(ref).startswith("material://"):
        return {"material_path": None, "material_exists": False}
    target = repo.materials_root / str(ref)[len("material://"):]
    try:
        rel = target.resolve().relative_to(repo.learningos_root.resolve())
    except (ValueError, OSError):
        try:
            rel = target.relative_to(repo.learningos_root)
        except ValueError:
            return {"material_path": None, "material_exists": False}
    return {"material_path": str(rel), "material_exists": target.exists()}


def _source_fingerprint(repo: Repo) -> str:
    """Content identity of every authored input used by the projection."""
    digest = hashlib.sha256()
    roots = ("knowledge", "sources", "records", "work", "curriculum", "system/schema")
    for rel_root in roots:
        base = repo.root / rel_root
        if not base.exists():
            continue
        files = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
        for path in files:
            rel = path.relative_to(repo.root).as_posix()
            if any(part.startswith(".") for part in path.relative_to(repo.root).parts):
                continue
            digest.update(rel.encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def _git_state(root: Path) -> tuple[str | None, bool]:
    try:
        rev = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root,
                             capture_output=True, text=True, timeout=30)
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all", "--",
             "knowledge", "sources", "records", "work", "curriculum", "system/schema"],
            cwd=root, capture_output=True, text=True, timeout=30)
        return (rev.stdout.strip() or None, bool(status.stdout.strip()))
    except Exception:  # noqa: BLE001
        return None, False


def build_manifest(repo: Repo, generated_at: str, backlinks: dict | None = None) -> dict:
    """The COMPLETE machine-readable projection of the repository (ADR-001):
    every canonical record (notes incl. attachments/evidence/contexts, concepts,
    sources, modules incl. attempts, workspaces, coordination) plus all
    relations. A consumer needing repository state should read this file, not
    parse the tree.

    ADR-006 addendum (2026-08-03, fourth): this is also the INTERFACE contract.
    Every field an interface would otherwise re-derive by parsing Markdown or
    YAML is projected here — workspace `next_action`/`objective`, source
    `url`/`material`/`evaluations`, note `domain`/`summary`, and structured
    `academic_deadlines`. Usability lives in the interface; deriving meaning
    stays here, once. If a UI needs to regex a canonical file, that is a
    manifest bug.

    One fact, one shape: where a projection could be expressed two ways the
    manifest carries exactly one. `academic_deadlines` replaced the narrower
    `exam_spine` key (2026-08-03), and `stages` is the flat by-id index for
    stage lookup while `study_maps[].stages` stays the ordering authority —
    an index plus an ordered list, never two copies of the same access path."""
    records = []
    for note in sorted(repo.notes.values(), key=lambda n: n.id):
        rel = note.path.relative_to(repo.root)
        records.append({
            "id": note.id, "type": "note",
            "title": note.meta.get("title", ""),
            "path": str(rel),
            "domain": rel.parent.name if rel.parent.name != "notes" else "",
            "summary": _first_para(_strip_headings(note.body))[:400],
            "role": note.meta.get("role", "synthesis"),
            "state": note.meta.get("state"),
            "authorship": note.meta.get("authorship"),
            "concepts": sorted(note.meta.get("concepts", []) or []),
            "sources": sorted(note.meta.get("sources", []) or []),
            "contexts": sorted(note.meta.get("contexts", []) or []),
            "attachments": list(note.meta.get("attachments", []) or []),
            "evidence": list(note.meta.get("evidence", []) or []),
            "supersedes": sorted(note.meta.get("supersedes", []) or []),
            "reviewed": note.meta.get("reviewed"),
        })
    for cid in sorted(repo.concepts):
        c = repo.concepts[cid]
        records.append({
            "id": cid, "type": "concept", "title": c.get("label", ""),
            "path": str(repo.concept_origins.get(cid, "").relative_to(repo.root))
            if repo.concept_origins.get(cid) else "knowledge/concepts.yaml",
            "aliases": sorted(c.get("aliases", []) or []),
            "deprecated": bool(c.get("deprecated", False)),
        })
    for sid in sorted(repo.sources):
        s = repo.sources[sid]
        records.append({
            "id": sid, "type": "source", "title": s.get("title", ""),
            "path": str(repo.source_origins.get(sid, "").relative_to(repo.root))
            if repo.source_origins.get(sid) else "sources/sources.yaml",
            "source_type": s.get("type", ""),
            # interface fields: everything needed to SHOW and OPEN a source.
            # `material_path` is resolved HERE (material:// → the .flat farm is
            # a business rule, loader.materials_root) so no interface has to
            # reimplement URI resolution. It is relative to the LearningOS
            # root, i.e. the vault's parent.
            "url": s.get("url"),
            "material": s.get("material"),
            **_material_location(repo, s.get("material")),
            "authors": list(s.get("authors", []) or []),
            "organization": s.get("organization"),
            "year": s.get("year"),
            "identifiers": dict(s.get("identifiers", {}) or {}),
            "roles": sorted({str(r) for ev in (s.get("evaluations") or [])
                             for r in (ev.get("roles") or [])}),
            # `useful_sections` is where the reading plan actually lives ("read
            # ch. 3 for X") — projected with its concept links so an interface
            # can turn a source into a navigable table of contents.
            "evaluations": [
                {"roles": list(ev.get("roles", []) or []),
                 "strengths": list(ev.get("strengths", []) or []),
                 "weaknesses": list(ev.get("weaknesses", []) or []),
                 "verdict": ev.get("verdict"),
                 "concepts": sorted(ev.get("concepts", []) or []),
                 "useful_sections": [
                     {"section": str(k), "note": str(v)}
                     for entry in (ev.get("useful_sections") or [])
                     if isinstance(entry, dict)
                     for k, v in entry.items()
                 ]}
                for ev in (s.get("evaluations") or []) if isinstance(ev, dict)
            ],
        })
    for mid in sorted(repo.modules):
        m = repo.modules[mid]
        origin = repo.module_origins.get(mid)
        records.append({
            "id": mid, "type": "module", "title": m.get("title", ""),
            "path": str(origin.relative_to(repo.root)) if origin else "records/modules.yaml",
            "kind": m.get("kind", "academic"), "area_id": m.get("area_id"),
            "status": m.get("status", ""),
            "institution": m.get("institution"), "code": m.get("code"),
            "credits": m.get("credits"), "semester": m.get("semester"),
            "components": list(m.get("components", []) or []),
            "examination": m.get("examination"),
            "attempts": list(m.get("attempts", []) or []),
            "grade": m.get("grade"),
            "unit_order": list(m.get("unit_order", []) or []),
            "source_map": m.get("source_map"),
        })
    for name in sorted(repo.collections):
        doc = repo.collections[name]
        entries = [e for e in doc.get("entries", []) or [] if isinstance(e, dict)]
        records.append({
            "id": name, "type": "collection",
            "title": doc.get("title", name),
            "path": f"sources/collections/{name}.yaml",
            "sources": [str(e.get("source", "")) for e in entries],
            # A shelf is curation, not a bag of ids: its rationale, its domain and
            # each entry's group + role are what make it browsable. Projected here
            # so no interface re-parses the collection YAML (ADR-006).
            "summary": " ".join(str(doc.get("description", "")).split()),
            "domain": ATLAS_COLLECTION_DOMAIN.get(name, "cross-domain"),
            "entries": [{"source": str(e.get("source", "")),
                         "group": str(e.get("group", "")) or None,
                         "why": " ".join(str(e.get("why", "")).split()) or None}
                        for e in entries],
        })
    for ws in sorted(repo.workspaces.values(), key=lambda w: w.id):
        records.append({
            "id": ws.id, "type": "workspace", "title": ws.meta.get("title", ""),
            "path": str(ws.path.relative_to(repo.root)),
            "status": ws.status, "standing": ws.standing, "archived": ws.archived,
            "deadline": ws.meta.get("deadline"),
            # interface fields: the two sections every surface wants to show.
            # Parsed HERE so no interface ever regexes CONTEXT.md again.
            "objective": _first_para(ws.section("Objective"))[:400],
            "next_action": _first_para(ws.section("Next Action"))[:400],
            "concepts": sorted(ws.meta.get("concepts", []) or []),
            "notes": sorted(ws.meta.get("notes", []) or []),
            "sources": sorted(ws.meta.get("sources", []) or []),
            "program_ids": sorted(ws.meta.get("program_ids", []) or []),
            "module_ids": sorted(ws.meta.get("module_ids", []) or []),
            "unit_ids": sorted(ws.meta.get("unit_ids", []) or []),
        })
    for learning_path in sorted(repo.learning_paths.values(), key=lambda p: p.id):
        data = learning_path.data
        projected_stages = []
        for stage in data.get("stages", []) or []:
            projected = dict(stage)
            note_ref = stage.get("notes_path") if isinstance(stage, dict) else None
            note_file = repo.root / str(note_ref) if note_ref else None
            if note_file and note_file.is_file():
                projected["notes_text"] = note_file.read_text(
                    encoding="utf-8", errors="replace")
                projected["notes_updated"] = _git_last_commit(
                    repo.root, note_file.relative_to(repo.root).as_posix())
            else:
                projected["notes_text"] = ""
                projected["notes_updated"] = None
            projected_stages.append(projected)
        records.append({
            "id": learning_path.id, "type": "learning-path",
            "title": data.get("title", ""),
            "path": str(learning_path.path.relative_to(repo.root)),
            "workspace_id": learning_path.workspace_id,
            "area": data.get("area", "university"),
            "module_id": data.get("module_id"),
            "status": data.get("status", ""),
            "current_stage": data.get("current_stage", ""),
            "created": data.get("created"), "updated": data.get("updated"),
            "objective": data.get("objective", ""),
            "source_plan": data.get("source_plan"),
            "stages": projected_stages,
            "shelving": dict(data.get("shelving", {}) or {}),
            "archived": learning_path.archived,
        })
    for program in sorted(repo.programs.values(), key=lambda p: p.id):
        records.append({
            **dict(program.data),
            "path": str(program.path.relative_to(repo.root)),
        })
    for unit in sorted(repo.units.values(), key=lambda u: u.id):
        data = unit.data
        records.append({
            **dict(data),
            "path": str(unit.path.relative_to(repo.root)),
        })
    for study_map in sorted(repo.study_maps.values(), key=lambda sm: sm.id):
        data = study_map.data
        projected_stages = []
        for stage in data.get("stages", []) or []:
            projected = dict(stage)
            note_ref = stage.get("working_note") if isinstance(stage, dict) else None
            note_file = repo.root / str(note_ref) if note_ref else None
            if note_file and note_file.is_file():
                projected["notes_text"] = note_file.read_text(
                    encoding="utf-8", errors="replace")
                projected["notes_updated"] = _git_last_commit(
                    repo.root, note_file.relative_to(repo.root).as_posix())
            else:
                projected["notes_text"] = ""
                projected["notes_updated"] = None
            projected_stages.append(projected)
        records.append({
            **{k: v for k, v in data.items() if k != "stages"},
            "module_id": study_map.module_id,
            "path": str(study_map.path.relative_to(repo.root)),
            "stages": projected_stages,
        })
    for mid in sorted(repo.module_source_maps):
        source_map = repo.module_source_maps[mid]
        records.append({
            "id": f"source-map-{mid.removeprefix('module-')}",
            **dict(source_map),
            "path": str(repo.module_source_map_origins[mid].relative_to(repo.root)),
        })
    if repo.coordination is not None:
        records.append({
            "id": "coordination", "type": "coordination",
            "path": "work/COORDINATION.md",
            "sections": {h: (repo.coordination.section(h) or "")
                         for h in ("Commitments", "Priorities", "Dependencies", "Deferrals")},
        })
    relations = [
        {"from": r.get("from"), "type": r.get("type"), "to": r.get("to"),
         "context": r.get("context"), "source": r.get("source")}
        for r in sorted(repo.relations,
                        key=lambda r: (str(r.get("from")), str(r.get("type")), str(r.get("to"))))
    ]
    ad = adoption_counts(repo)
    fingerprint = _source_fingerprint(repo)
    revision, dirty = _git_state(repo.root)
    generated_meta = _json_header(generated_at)
    generated_meta.update({
        "contract_version": 2,
        "snapshot_id": f"sha256:{fingerprint}",
        "source_fingerprint": fingerprint,
        "source_revision": revision,
        "source_dirty": dirty,
    })
    programs_v2 = [r for r in records if r.get("type") == "program"]
    modules_v2 = [r for r in records if r.get("type") == "module"]
    units_v2 = [r for r in records if r.get("type") == "unit"]
    study_maps_v2 = [r for r in records if r.get("type") == "study-map"]
    source_maps_v2 = [r for r in records if r.get("type") == "module-source-map"]
    stages_v2 = [
        {**stage, "study_map_id": study_map["id"],
         "unit_id": study_map["unit_id"], "module_id": study_map["module_id"]}
        for study_map in study_maps_v2 for stage in study_map.get("stages", [])
    ]
    module_to_units = {
        module["id"]: [uid for uid in module.get("unit_order", []) if uid]
        for module in modules_v2
    }
    unit_to_study_map = {
        unit["id"]: unit.get("current_study_map")
        for unit in units_v2 if unit.get("current_study_map")
    }
    component_to_units: dict[str, list[str]] = {}
    source_to_modules: dict[str, list[str]] = {}
    source_to_units: dict[str, list[str]] = {}
    workspace_to_modules: dict[str, list[str]] = {}
    workspace_to_units: dict[str, list[str]] = {}
    for unit in units_v2:
        if unit.get("component_id"):
            component_to_units.setdefault(unit["component_id"], []).append(unit["id"])
        for scoped in unit.get("scope_sources", []) or []:
            if scoped.get("source_id"):
                source_to_units.setdefault(scoped["source_id"], []).append(unit["id"])
        for selection in unit.get("source_selections", []) or []:
            if selection.get("source_id"):
                source_to_units.setdefault(selection["source_id"], []).append(unit["id"])
    for source_map in source_maps_v2:
        mid = source_map.get("module_id")
        for entry in source_map.get("sources", []) or []:
            sid = entry.get("source_id")
            if sid:
                source_to_modules.setdefault(sid, []).append(mid)
            for uid in entry.get("unit_routes", []) or []:
                source_to_units.setdefault(sid, []).append(uid)
    for study_map in study_maps_v2:
        for stage in study_map.get("stages", []) or []:
            for resource in stage.get("resources", []) or []:
                sid = resource.get("source_id")
                if sid:
                    source_to_units.setdefault(sid, []).append(study_map["unit_id"])
    for workspace in [r for r in records if r.get("type") == "workspace" and not r.get("archived")]:
        workspace_to_modules[workspace["id"]] = list(workspace.get("module_ids", []) or [])
        workspace_to_units[workspace["id"]] = list(workspace.get("unit_ids", []) or [])
    for table in (component_to_units, source_to_modules, source_to_units,
                  workspace_to_modules, workspace_to_units):
        for key in table:
            table[key] = sorted(set(table[key]))
    progress = {}
    study_map_by_unit = {sm["unit_id"]: sm for sm in study_maps_v2}
    unit_by_id = {u["id"]: u for u in units_v2}
    for module in modules_v2:
        module_units = [unit_by_id[uid] for uid in module.get("unit_order", [])
                        if uid in unit_by_id]
        stage_rows = [stage for unit in module_units
                      for stage in (study_map_by_unit.get(unit["id"], {}).get("stages", []) or [])]
        progress[module["id"]] = {
            "units_total": len(module_units),
            "units_complete": sum(1 for unit in module_units if unit.get("status") == "complete"),
            "units_needing_map": sum(1 for unit in module_units if unit.get("status") == "needs-map"),
            "stages_total": len(stage_rows),
            "stages_complete": sum(1 for stage in stage_rows if stage.get("status") == "complete"),
        }
    semesters_v2 = [
        {**semester, "program_id": program["id"]}
        for program in programs_v2 for semester in program.get("semesters", []) or []
    ]
    inbox_dir = repo.root / "work" / "inbox"
    inbox_items = len([
        item for item in inbox_dir.iterdir() if not item.name.startswith(".")
    ]) if inbox_dir.is_dir() else 0
    return {
        "_generated": generated_meta,
        "records": records,
        "relations": relations,
        # Backlinks are part of the SAME atomic manifest snapshot. The legacy
        # backlinks.json remains as a compatibility view, but interfaces never
        # need to race two separately-written files again.
        "backlinks": {k: v for k, v in (backlinks or {}).items() if k != "_generated"},
        # Interface convenience: every academic date an interface can render
        # with no Python running at all — registered attempts, available
        # sittings that have no attempt yet, and grouped registration windows,
        # already ordered. `_academic_deadlines` correlates attempts with
        # `examination.sittings` here so no interface repeats that rule.
        #
        # There is deliberately no separate `exam_spine` key: it was a strict
        # subset of this list (registered attempts only) and a second shape for
        # the same facts. `_exam_spine` survives as the internal helper behind
        # the Markdown views and `los.py status --json` (ADR-006, 2026-08-03).
        "academic_deadlines": _academic_deadlines(repo),
        "programs": programs_v2,
        "semesters": semesters_v2,
        "modules": modules_v2,
        "units": units_v2,
        "study_maps": study_maps_v2,
        "stages": stages_v2,
        "module_source_maps": source_maps_v2,
        "resume_pointer": dict(repo.resume_pointer or {}),
        "quarantine_boundaries": [
            {k: program.get(k) for k in
             ("id", "title", "kind", "status", "description", "boundary_action")}
            for program in programs_v2
            if program.get("status") in {"quarantined", "boundary-only"}
        ],
        "indexes": {
            "module_to_units": module_to_units,
            "unit_to_study_map": unit_to_study_map,
            "component_to_units": dict(sorted(component_to_units.items())),
            "source_to_modules": dict(sorted(source_to_modules.items())),
            "source_to_units": dict(sorted(source_to_units.items())),
            "workspace_to_modules": dict(sorted(workspace_to_modules.items())),
            "workspace_to_units": dict(sorted(workspace_to_units.items())),
        },
        "progress": progress,
        "counts": {
            "notes": len(repo.notes), "concepts": len(repo.concepts),
            "sources": len(repo.sources), "collections": len(repo.collections),
            "modules": len(repo.modules),
            "workspaces_active": len(repo.active_workspaces()),
            "workspaces_archived": len(repo.archived_workspaces()),
            "learning_paths": len(repo.learning_paths),
            "learning_paths_active": sum(
                1 for p in repo.active_learning_paths() if p.status == "active"),
            "programs": len(repo.programs),
            "units": len(repo.units),
            "study_maps": len(repo.study_maps),
            "stages": len(stages_v2),
            "stages_complete": sum(1 for stage in stages_v2 if stage.get("status") == "complete"),
            "source_feedback_records": sum(
                len(stage.get("source_feedback", []) or []) for stage in stages_v2),
            "units_needing_map": sum(1 for unit in units_v2 if unit.get("status") == "needs-map"),
            "inbox_items": inbox_items,
            "relations": len(repo.relations),
            "notes_reviewed": ad["notes_reviewed"],
            "notes_with_evidence": ad["notes_with_evidence"],
        },
    }


def build_backlinks(repo: Repo, generated_at: str) -> dict:
    concept_to_notes: dict[str, list] = {}
    source_to_notes: dict[str, list] = {}
    note_incoming: dict[str, list] = {}
    workspace_to_notes: dict[str, list] = {}
    concept_relations: dict[str, dict] = {}
    module_to_workspaces: dict[str, list] = {}
    unit_to_workspaces: dict[str, list] = {}
    module_to_units: dict[str, list] = {}
    source_to_units: dict[str, list] = {}

    for note in sorted(repo.notes.values(), key=lambda n: n.id):
        for cid in note.meta.get("concepts", []) or []:
            concept_to_notes.setdefault(cid, []).append(note.id)
        for sid in note.meta.get("sources", []) or []:
            source_to_notes.setdefault(sid, []).append(note.id)
        for wid in note.meta.get("contexts", []) or []:
            workspace_to_notes.setdefault(wid, []).append(note.id)
        for target in note.meta.get("supersedes", []) or []:
            note_incoming.setdefault(target, []).append(
                {"from": note.id, "kind": "superseded-by"})
        for m in re.finditer(r"note://(note-[a-z0-9-]+)", note.body):
            if m.group(1) != note.id:
                note_incoming.setdefault(m.group(1), []).append(
                    {"from": note.id, "kind": "mentions"})
    for ws in sorted(repo.workspaces.values(), key=lambda w: w.id):
        for nid in ws.meta.get("notes", []) or []:
            lst = workspace_to_notes.setdefault(ws.id, [])
            if nid not in lst:
                lst.append(nid)
        explicit_modules = ws.meta.get("module_ids", []) or []
        for mid in explicit_modules:
            module_to_workspaces.setdefault(mid, []).append(ws.id)
        for uid in ws.meta.get("unit_ids", []) or []:
            unit_to_workspaces.setdefault(uid, []).append(ws.id)
        # Compatibility only for pre-v2 workspaces. V2 relationships are
        # declared in frontmatter and never inferred from names or prose.
        if not explicit_modules:
            for m in re.finditer(r"\bmodule-[a-z0-9]+(?:-[a-z0-9]+)*\b", ws.body):
                module_to_workspaces.setdefault(m.group(0), []).append(ws.id)
    for mid, module in repo.modules.items():
        module_to_units[mid] = list(module.get("unit_order", []) or [])
    for unit in repo.units.values():
        for scoped in unit.data.get("scope_sources", []) or []:
            sid = scoped.get("source_id") if isinstance(scoped, dict) else None
            if sid:
                source_to_units.setdefault(sid, []).append(unit.id)
        for selection in unit.data.get("source_selections", []) or []:
            sid = selection.get("source_id") if isinstance(selection, dict) else None
            if sid:
                source_to_units.setdefault(sid, []).append(unit.id)
    for study_map in repo.study_maps.values():
        for stage in study_map.data.get("stages", []) or []:
            for resource in stage.get("resources", []) or []:
                sid = resource.get("source_id") if isinstance(resource, dict) else None
                if sid:
                    source_to_units.setdefault(sid, []).append(study_map.unit_id)
    for rel in repo.relations:
        frm, to, rtype = rel.get("from"), rel.get("to"), rel.get("type")
        concept_relations.setdefault(frm, {"outgoing": [], "incoming": []})
        concept_relations.setdefault(to, {"outgoing": [], "incoming": []})
        concept_relations[frm]["outgoing"].append({"type": rtype, "to": to})
        concept_relations[to]["incoming"].append({"type": rtype, "from": frm})
    for d in concept_relations.values():
        d["outgoing"].sort(key=lambda e: (e["type"], e["to"]))
        d["incoming"].sort(key=lambda e: (e["type"], e["from"]))
    for m in (concept_to_notes, source_to_notes, workspace_to_notes,
              module_to_workspaces, unit_to_workspaces, module_to_units, source_to_units):
        for k in m:
            m[k] = sorted(set(m[k])) if all(isinstance(x, str) for x in m[k]) else m[k]
    generated_meta = _json_header(generated_at)
    generated_meta.update({
        "contract_version": 2,
        "snapshot_id": f"sha256:{_source_fingerprint(repo)}",
    })
    return {
        "_generated": generated_meta,
        "concept_to_notes": dict(sorted(concept_to_notes.items())),
        "source_to_notes": dict(sorted(source_to_notes.items())),
        "note_incoming": dict(sorted(note_incoming.items())),
        "workspace_to_notes": dict(sorted(workspace_to_notes.items())),
        "concept_relations": dict(sorted(concept_relations.items())),
        "module_to_workspaces": dict(sorted(module_to_workspaces.items())),
        "unit_to_workspaces": dict(sorted(unit_to_workspaces.items())),
        "module_to_units": dict(sorted(module_to_units.items())),
        "source_to_units": dict(sorted(source_to_units.items())),
    }


def _evals_for_concept(repo: Repo, cid: str) -> list[tuple[str, dict, dict]]:
    """(source_id, source, evaluation) pairs whose evaluation targets cid."""
    out = []
    for sid in sorted(repo.sources):
        source = repo.sources[sid]
        for ev in source.get("evaluations", []) or []:
            if cid in (ev.get("concepts") or []):
                out.append((sid, source, ev))
    return out


def _eval_line(sid: str, source: dict, ev: dict) -> str:
    bits = []
    if ev.get("roles"):
        bits.append("roles: " + ", ".join(ev["roles"]))
    if ev.get("level"):
        bits.append(f"level: {ev['level']}")
    if ev.get("strengths"):
        bits.append(ev["strengths"][0])
    detail = " — ".join(bits)
    return f"**{source.get('title', sid)}** (`{sid}`)" + (f" — {detail}" if detail else "")


def build_concept_index(repo: Repo, backlinks: dict, generated_at: str) -> str:
    lines = _md_header("Concept index", generated_at)
    toc_entries = []
    for cid in sorted(repo.concepts):
        c = repo.concepts[cid]
        label = c.get("label", cid)
        heading = label + (" *(deprecated)*" if c.get("deprecated") else "")
        toc_entries.append((label, heading))
    toc_entries.sort(key=lambda e: e[0].lower())
    lines.append("## Contents")
    lines.append("")
    lines.extend(_letter_toc(toc_entries))
    for cid in sorted(repo.concepts):
        c = repo.concepts[cid]
        label = c.get("label", cid)
        dep = " *(deprecated)*" if c.get("deprecated") else ""
        lines.append(f"## {label}{dep}")
        lines.append("")
        lines.append(f"`{cid}`")
        if c.get("aliases"):
            lines.append("")
            lines.append("Aliases: " + " · ".join(sorted(c["aliases"])))
        if c.get("description"):
            lines.append("")
            lines.append(f"*{c['description']}*")
        if c.get("replaced_by"):
            lines.append("")
            lines.append(f"Replaced by: `{c['replaced_by']}`")
        note_ids = backlinks["concept_to_notes"].get(cid, [])
        if note_ids:
            lines.append("")
            lines.append("**Notes:**")
            lines.append("")
            for nid in note_ids:
                note = repo.notes.get(nid)
                role = note.meta.get("role", "synthesis") if note else "?"
                title = note.meta.get("title", nid) if note else nid
                lines.append(f"- `{nid}` — {title} *(role: {role})*")
        rels = backlinks["concept_relations"].get(cid)
        if rels and (rels["outgoing"] or rels["incoming"]):
            lines.append("")
            lines.append("**Related concepts:**")
            lines.append("")
            for e in rels["outgoing"]:
                lines.append(f"- {e['type']} → `{e['to']}`")
            for e in rels["incoming"]:
                lines.append(f"- ← {e['type']} from `{e['from']}`")
        evals = _evals_for_concept(repo, cid)
        if evals:
            lines.append("")
            lines.append("**Contextual sources:**")
            lines.append("")
            for sid, source, ev in evals:
                lines.append(f"- {_eval_line(sid, source, ev)}")
        lines.append("")
    return "\n".join(lines)


def _lecture_entries(repo: Repo) -> list[tuple[str, str, str, dict]]:
    """(lecture_label, source_id, section_note, evaluation) for lecture-series sources.

    A lecture entry is any evaluation on a type=lecture source whose
    useful_sections carry a lecture-shaped key (e.g. 'L05 — Logistic Regression').
    """
    entries = []
    for sid in sorted(repo.sources):
        source = repo.sources[sid]
        if source.get("type") != "lecture":
            continue
        for ev in source.get("evaluations", []) or []:
            for section in ev.get("useful_sections", []) or []:
                for key, desc in sorted(section.items()):
                    if LECTURE_KEY_RE.match(key):
                        entries.append((key, sid, desc, ev))
    entries.sort(key=lambda e: (e[1], e[0]))
    return entries


def build_collection_view(repo: Repo, name: str, doc: dict, generated_at: str) -> str:
    """Render one curated collection (sources/collections/<name>.yaml) as a
    readable list, grouped by first appearance of `group`."""
    lines = _md_header(doc.get("title", name), generated_at)
    if doc.get("description"):
        lines.append(str(doc["description"]).strip())
        lines.append("")
    current_group = object()  # sentinel: first entry always opens its section
    for entry in doc.get("entries", []) or []:
        if not isinstance(entry, dict):
            continue
        group = entry.get("group")
        if group != current_group:
            current_group = group
            if group:
                lines.append(f"## {group}")
                lines.append("")
        sid = str(entry.get("source", ""))
        s = repo.sources.get(sid, {})
        title = s.get("title", sid)
        url = s.get("url")
        head = f"**[{title}]({url})**" if url else f"**{title}**"
        ident = [s.get("type", ""),
                 ", ".join(s.get("authors", []) or []) or s.get("organization", ""),
                 str(s.get("year", "") or "")]
        ident_str = " · ".join(x for x in ident if x)
        lines.append(f"- {head}" + (f" ({ident_str})" if ident_str else "") + f" — `{sid}`")
        if entry.get("why"):
            lines.append(f"  - {entry['why']}")
        if s.get("material"):
            lines.append(f"  - local: `{s['material']}`")
        for key, val in (s.get("identifiers") or {}).items():
            lines.append(f"  - {key}: {val}")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"Canonical input: `sources/collections/{name}.yaml` — source judgments "
                 "live in the source records (see source-index.md), not here.")
    return "\n".join(lines)


def build_source_index(repo: Repo, generated_at: str) -> str:
    lines = _md_header("Source index", generated_at)

    if repo.collections:
        lines.append("## Collections (curated lists)")
        lines.append("")
        for name in sorted(repo.collections):
            doc = repo.collections[name]
            n = len(doc.get("entries", []) or [])
            lines.append(f"- [{doc.get('title', name)}](collections/{name}.md) — "
                         f"{n} entries (`sources/collections/{name}.yaml`)")
        lines.append("")

    lines.append("## Registry")
    lines.append("")
    toc_entries = sorted(
        ((str(repo.sources[sid].get("title", sid)), str(repo.sources[sid].get("title", sid)))
         for sid in repo.sources),
        key=lambda e: e[0].lower())
    lines.extend(_letter_toc(toc_entries))
    for sid in sorted(repo.sources):
        s = repo.sources[sid]
        lines.append(f"### {s.get('title', sid)}")
        lines.append("")
        ident = [f"`{sid}`", s.get("type", "")]
        if s.get("authors"):
            ident.append(", ".join(s["authors"]))
        if s.get("organization"):
            ident.append(s["organization"])
        if s.get("year"):
            ident.append(str(s["year"]))
        lines.append(" · ".join(str(x) for x in ident if x))
        loc = s.get("material") or s.get("url")
        if loc:
            lines.append("")
            lines.append(f"Location: `{loc}`")
        for ev in s.get("evaluations", []) or []:
            lines.append("")
            scope = ", ".join(f"`{c}`" for c in ev.get("concepts", []) or []) or "global"
            lines.append(f"- **Evaluation** ({scope})")
            if ev.get("roles"):
                lines.append(f"  - roles: {', '.join(ev['roles'])}")
            if ev.get("level"):
                lines.append(f"  - level: {ev['level']}")
            if ev.get("audience"):
                lines.append(f"  - audience: {', '.join(ev['audience'])}")
            if ev.get("prerequisites"):
                lines.append(f"  - prerequisites: {', '.join(ev['prerequisites'])}")
            for st in ev.get("strengths", []) or []:
                lines.append(f"  - strength: {st}")
            for wk in ev.get("weaknesses", []) or []:
                lines.append(f"  - weakness: {wk}")
            for section in ev.get("useful_sections", []) or []:
                for key, desc in sorted(section.items()):
                    lines.append(f"  - section — {key}: {desc}")
        lines.append("")

    # ---------------------------------------------------- per-lecture selector
    lines.append("---")
    lines.append("")
    lines.append("## Selector view — per lecture")
    lines.append("")
    lines.append("For each lecture of a registered lecture-series source: its concepts, and "
                 "for each concept the recommended sources for first learning / review / "
                 "implementation (from contextual source evaluations).")
    lines.append("")
    for key, sid, desc, ev in _lecture_entries(repo):
        lines.append(f"### {sid} — {key}")
        lines.append("")
        if desc:
            lines.append(f"*{desc}*")
            lines.append("")
        concepts = sorted(ev.get("concepts", []) or [])
        if not concepts:
            lines.append("(no concepts registered for this lecture)")
            lines.append("")
            continue
        for cid in concepts:
            label = repo.concepts.get(cid, {}).get("label", cid)
            lines.append(f"**{label}** (`{cid}`)")
            lines.append("")
            evals = [(s, src, e) for (s, src, e) in _evals_for_concept(repo, cid) if s != sid]
            self_evals = [(s, src, e) for (s, src, e) in _evals_for_concept(repo, cid) if s == sid]
            for role in SELECTOR_ROLES:
                picks = [(s, src, e) for (s, src, e) in evals if role in (e.get("roles") or [])]
                if picks:
                    lines.append(f"- *{role}:* " + " · ".join(_eval_line(s, src, e)
                                                              for s, src, e in picks))
            other = [(s, src, e) for (s, src, e) in evals
                     if not set(e.get("roles") or []) & set(SELECTOR_ROLES)]
            for s, src, e in other:
                roles = ", ".join(e.get("roles") or ["unspecified"])
                lines.append(f"- *{roles}:* {_eval_line(s, src, e)}")
            for s, src, e in self_evals:
                lines.append(f"- *lecture:* {_eval_line(s, src, e)}")
            note_ids = sorted(n.id for n in repo.notes.values()
                              if cid in (n.meta.get("concepts") or []))
            if note_ids:
                lines.append("- *notes:* " + " · ".join(f"`{n}`" for n in note_ids))
            lines.append("")
        lines.append("")

    # ---------------------------------------------------- per-concept selector
    lines.append("---")
    lines.append("")
    lines.append("## Selector view — per concept")
    lines.append("")
    for cid in sorted(repo.concepts):
        evals = _evals_for_concept(repo, cid)
        if not evals:
            continue
        label = repo.concepts.get(cid, {}).get("label", cid)
        lines.append(f"### {label} (`{cid}`)")
        lines.append("")
        for role, heading in (("first-learning", "Best for first learning"),
                              ("review", "Best for review"),
                              ("implementation", "Best for implementation")):
            picks = [(s, src, e) for (s, src, e) in evals if role in (e.get("roles") or [])]
            if picks:
                lines.append(f"**{heading}:**")
                lines.append("")
                for s, src, e in picks:
                    lines.append(f"- {_eval_line(s, src, e)}")
                lines.append("")
        other = [(s, src, e) for (s, src, e) in evals
                 if not set(e.get("roles") or []) & set(SELECTOR_ROLES)]
        if other:
            lines.append("**Other contexts:**")
            lines.append("")
            for s, src, e in other:
                roles = ", ".join(e.get("roles") or ["unspecified"])
                lines.append(f"- ({roles}) {_eval_line(s, src, e)}")
            lines.append("")
    return "\n".join(lines)


def _exam_spine(repo: Repo) -> list[tuple[str, str, dict, dict]]:
    """(date, module_id, module, attempt) for attempts with result=registered."""
    spine = []
    for mid in sorted(repo.modules):
        module = repo.modules[mid]
        for att in module.get("attempts", []) or []:
            if att.get("result") == "registered" and att.get("date"):
                spine.append((str(att["date"]), mid, module, att))
    spine.sort()
    return spine


def _academic_deadlines(repo: Repo) -> list[dict]:
    """Project structured exam sittings and registration windows for interfaces.

    Attempts remain the authority for what the learner actually registered,
    withdrew from, sat, or passed.  Examination sittings describe available
    dates even before an attempt exists; correlating the two here keeps that
    business rule out of every interface.
    """
    deadlines: list[dict] = []
    represented_attempts: set[tuple[str, int, str]] = set()
    grouped_windows: dict[tuple[str, str, str], dict] = {}

    for mid in sorted(repo.modules):
        module = repo.modules[mid]
        examination = module.get("examination") or {}
        attempts = module.get("attempts", []) or []

        for sitting in examination.get("sittings", []) or []:
            start = str(sitting.get("date", ""))
            if not start:
                continue
            end = str(sitting.get("end_date") or start)
            termin = int(sitting.get("termin", 1))
            matching = [
                attempt for attempt in attempts
                if int(attempt.get("termin", 0)) == termin
                and start <= str(attempt.get("date", "")) <= end
            ]
            state = "unregistered"
            for result in ("registered", "passed", "failed", "withdrawn"):
                if any(attempt.get("result") == result for attempt in matching):
                    state = result
                    break
            represented_attempts.update(
                (mid, termin, str(attempt.get("date")))
                for attempt in matching if attempt.get("date")
            )
            # Availability is actionable state, not historical inventory. Keep
            # past sittings when an attempt gives them administrative meaning,
            # but do not advertise an elapsed, never-chosen sitting as open.
            if state == "unregistered" and end < _dt.date.today().isoformat():
                continue
            deadlines.append({
                "kind": "exam",
                "start_date": start,
                "end_date": end,
                "module_id": mid,
                "title": module.get("title", mid),
                "termin": termin,
                "label": sitting.get("label") or f"Termin {termin}",
                "time": sitting.get("time"),
                "notes": sitting.get("notes"),
                "registration_state": state,
            })

        for window in examination.get("registration_windows", []) or []:
            opens = str(window.get("opens", ""))
            closes = str(window.get("closes", ""))
            label = str(window.get("label", "Registration window"))
            if not opens or not closes:
                continue
            key = (opens, closes, label)
            grouped = grouped_windows.setdefault(key, {
                "kind": "registration-window",
                "start_date": opens,
                "end_date": closes,
                "label": label,
                "modules": [],
            })
            grouped["modules"].append({
                "module_id": mid,
                "title": module.get("title", mid),
                "action": window.get("action"),
                "termins": list(window.get("termins", []) or []),
            })

    # A registered attempt remains visible even if its module has not yet been
    # backfilled with an available-sitting record.
    for date, mid, module, attempt in _exam_spine(repo):
        key = (mid, int(attempt.get("termin", 1)), date)
        if key in represented_attempts:
            continue
        deadlines.append({
            "kind": "exam",
            "start_date": date,
            "end_date": date,
            "module_id": mid,
            "title": module.get("title", mid),
            "termin": attempt.get("termin"),
            "label": f"Termin {attempt.get('termin', '')}".strip(),
            "time": None,
            "notes": attempt.get("notes"),
            "registration_state": "registered",
        })

    for grouped in grouped_windows.values():
        grouped["modules"].sort(key=lambda row: row["module_id"])
        deadlines.append(grouped)
    deadlines.sort(key=lambda row: (
        row.get("start_date", ""),
        0 if row.get("kind") == "registration-window" else 1,
        row.get("label", ""),
        row.get("module_id", ""),
    ))
    return deadlines


def _exam_spine_lines(repo: Repo) -> list[str]:
    lines = []
    spine = _exam_spine(repo)
    if spine:
        lines.append("| Date | Module | Termin | Notes |")
        lines.append("|---|---|---|---|")
        for date, mid, module, att in spine:
            lines.append(f"| {date} | {module.get('title', mid)} (`{mid}`) "
                         f"| {att.get('termin', '')} | {att.get('notes', '')} |")
    else:
        lines.append("(no registered attempts in records/modules.yaml)")
    deadlines = _academic_deadlines(repo)
    pending = [row for row in deadlines
               if row.get("kind") == "exam"
               and row.get("registration_state") == "unregistered"]
    if pending:
        lines.append("")
        lines.append("**Available sittings with no registered attempt yet:**")
        lines.append("")
        for row in pending:
            date = row["start_date"]
            if row.get("end_date") != date:
                date += f" to {row['end_date']}"
            lines.append(f"- **{date}** — {row['title']} (`{row['module_id']}`), "
                         f"{row['label']} — not registered"
                         + (f" · {row['notes']}" if row.get("notes") else ""))
    windows = [row for row in deadlines if row.get("kind") == "registration-window"]
    if windows:
        lines.append("")
        lines.append("**Registration windows:**")
        lines.append("")
        for row in windows:
            titles = ", ".join(module["title"] for module in row["modules"])
            lines.append(f"- **{row['start_date']} to {row['end_date']}** — "
                         f"{row['label']}: {titles}")
    return lines


def build_module_view(repo: Repo, generated_at: str) -> str:
    lines = _md_header("Module view", generated_at)
    lines.append("## Upcoming exam spine (registered attempts, sorted by date)")
    lines.append("")
    lines.extend(_exam_spine_lines(repo))
    lines.append("")
    for mid in sorted(repo.modules):
        m = repo.modules[mid]
        lines.append(f"## {m.get('title', mid)}")
        lines.append("")
        ident = [f"`{mid}`", m.get("institution", ""), m.get("code", "")]
        lines.append(" · ".join(str(x) for x in ident if x))
        lines.append("")
        facts = []
        if m.get("credits") is not None:
            facts.append(f"credits: {m['credits']}")
        if m.get("semester"):
            facts.append(f"semester: {m['semester']}")
        facts.append(f"status: {m.get('status', '')}")
        if m.get("examination"):
            ex = m["examination"]
            facts.append(f"examination: {ex.get('type', '')}"
                         + (f" ({ex.get('notes')})" if ex.get("notes") else ""))
        if m.get("grade") is not None:
            facts.append(f"final grade: {m['grade']}")
        lines.append(" · ".join(facts))
        if m.get("components"):
            lines.append("")
            component_titles = [c.get("title", c.get("id", "")) if isinstance(c, dict)
                                else str(c) for c in m["components"]]
            lines.append("Components (one grade): " + " + ".join(component_titles))
        attempts = m.get("attempts", []) or []
        if attempts:
            lines.append("")
            lines.append("| # | Termin | Date | Result | Grade | Notes |")
            lines.append("|---|---|---|---|---|---|")
            for i, att in enumerate(attempts, 1):
                lines.append(f"| {i} | {att.get('termin', '')} | {att.get('date', '')} "
                             f"| {att.get('result', '')} | {att.get('grade', '')} "
                             f"| {att.get('notes', '')} |")
        lines.append("")
    return "\n".join(lines)


def _strip_headings(text: str | None) -> str:
    """Drop headings, blockquote callouts and list bullets so `_first_para`
    lands on actual prose. Used for the manifest's `summary` fields."""
    if not text:
        return ""
    keep = []
    for line in text.split("\n"):
        stripped = line.strip()
        if (stripped.startswith("#") or stripped.startswith(">")
                or stripped.startswith("|") or stripped.startswith("```")
                or set(stripped) <= {"-", "*", "_"} and len(stripped) >= 3):
            continue
        keep.append(line)
    return "\n".join(keep)


def _first_para(text: str | None) -> str:
    if not text:
        return ""
    for block in text.split("\n\n"):
        block = " ".join(block.split())
        if block:
            return block
    return ""


def _materials_queue_rows(repo: Repo) -> list[str]:
    """Pending-human-decision piles under materials/ (human-operability #10).
    Shared by the coordination view and the reading room."""
    rows: list[str] = []
    materials = repo.root.parent / "materials"
    for qname in ("_unsorted", "_duplicates-for-review"):
        qdir = materials / qname
        if qdir.is_dir():
            n = sum(1 for f in qdir.rglob("*")
                    if f.is_file() and f.name != ".DS_Store")
            if n:
                rows.append(f"- `materials/{qname}/` — **{n} files** "
                            "awaiting a register-or-discard decision")
    return rows


def adoption_counts(repo: Repo) -> dict:
    """Adoption of the existing note review/evidence fields (no new schema —
    the fields have been in note.schema.json since v3; the gap is usage).
    Shared by the health report, the reading room, and `los.py status`."""
    notes = repo.notes.values()
    total = len(repo.notes)
    reviewed = sorted(n.id for n in notes if n.meta.get("reviewed"))
    with_evidence = sorted(n.id for n in notes if n.meta.get("evidence"))
    by_state: dict[str, int] = {}
    for n in notes:
        s = str(n.meta.get("state", "(unset)"))
        by_state[s] = by_state.get(s, 0) + 1
    # A reviewed note whose last Git touch postdates its review date has
    # drifted past its review; uncommitted edits count as drifted too.
    changed_since_review: list[str] = []
    for n in repo.notes.values():
        rev = n.meta.get("reviewed")
        if not rev:
            continue
        last = _git_last_commit(repo.root, n.path.relative_to(repo.root).as_posix())
        if not last or str(last) > str(rev):
            changed_since_review.append(n.id)
    return {
        "notes_total": total,
        "notes_reviewed": len(reviewed),
        "notes_with_evidence": len(with_evidence),
        "changed_since_review": sorted(changed_since_review),
        "by_state": by_state,
    }


def build_coordination_view(repo: Repo, generated_at: str) -> str:
    lines = _md_header("Coordination view", generated_at)
    lines.append("*Assembled from: the exam spine in records/modules.yaml, workspace "
                 "frontmatter, the facts in work/COORDINATION.md, and Git-derived "
                 "neglect signals. Disposable — rebuild anytime.*")
    lines.append("")

    lines.append("## Exam spine")
    lines.append("")
    lines.extend(_exam_spine_lines(repo))
    lines.append("")

    lines.append("## Active workspaces")
    lines.append("")
    active = sorted(repo.active_workspaces(), key=lambda w: w.id)
    if active:
        lines.append("| Workspace | Status | Standing | Deadline | Next action |")
        lines.append("|---|---|---|---|---|")
        for ws in active:
            na = _first_para(ws.section("Next Action"))
            deadline = ws.meta.get("deadline", "") or ""
            lines.append(f"| `{ws.id}` — {ws.meta.get('title', '')} | {ws.status} "
                         f"| {'yes' if ws.standing else ''} | {deadline} | {na} |")
    else:
        lines.append("(no active workspaces)")
    lines.append("")

    lines.append("## Coordination facts (work/COORDINATION.md)")
    lines.append("")
    if repo.coordination is not None:
        for heading in ("Commitments", "Priorities", "Dependencies", "Deferrals"):
            body = repo.coordination.section(heading)
            lines.append(f"### {heading}")
            lines.append("")
            lines.append(body if body else "(none)")
            lines.append("")
    else:
        lines.append("(work/COORDINATION.md missing)")
        lines.append("")

    lines.append("## Materials queues (pending human decisions)")
    lines.append("")
    queue_rows = _materials_queue_rows(repo)
    if queue_rows:
        lines.extend(queue_rows)
        lines.append("")
        lines.append("*Same failure mode as an unread inbox — these piles are "
                     "invisible unless surfaced. Register on first canonical "
                     "citation (WORKFLOWS §6a) or discard deliberately.*")
    else:
        lines.append("(empty — nothing awaits a decision)")
    lines.append("")

    lines.append("## Neglect signals (Git)")
    lines.append("")
    rows = []
    for ws in active:
        if ws.standing:
            continue
        rel = str(ws.path.parent.relative_to(repo.root))
        last = _git_last_commit(repo.root, rel)
        rows.append((ws.id, last))
    if rows:
        lines.append("| Workspace | Last commit touching it |")
        lines.append("|---|---|")
        for wid, last in rows:
            lines.append(f"| `{wid}` | {last or '(not yet committed)'} |")
        lines.append("")
        lines.append("*A workspace untouched for 21+ days is flagged by the validator "
                     "(WS-NEGLECT).*")
    else:
        lines.append("(no non-standing active workspaces)")
    lines.append("")
    return "\n".join(lines)


PREREQ_TYPES = ("requires", "builds-on")


def build_dependency_report(repo: Repo, backlinks: dict, generated_at: str) -> str:
    """Concept/module dependency view (ADR-001): direct + transitive
    prerequisites per concept, a layered study order over the prerequisite
    subgraph, and the module -> workspace -> concept graph."""
    prereqs: dict[str, set] = {}
    for rel in repo.relations:
        if rel.get("type") in PREREQ_TYPES:
            prereqs.setdefault(str(rel["from"]), set()).add(str(rel["to"]))

    def closure(cid: str) -> list[str]:
        seen, stack = set(), sorted(prereqs.get(cid, ()))
        while stack:
            c = stack.pop()
            if c in seen or c == cid:
                continue
            seen.add(c)
            stack.extend(sorted(prereqs.get(c, ())))
        return sorted(seen)

    lines = _md_header("Dependency report", generated_at)
    lines.append("*Prerequisite semantics = `requires` + `builds-on` edges from "
                 "the relation registry. `motivates`/`applies-in`/`contrasts-with` "
                 "edges are context, not prerequisites, and are excluded.*")
    lines.append("")

    lines.append("## Prerequisites per concept (direct → transitive)")
    lines.append("")
    for cid in sorted(repo.concepts):
        direct = sorted(prereqs.get(cid, ()))
        if not direct:
            continue
        label = repo.concepts[cid].get("label", cid)
        lines.append(f"- **{label}** (`{cid}`)")
        lines.append(f"  - direct: " + ", ".join(f"`{c}`" for c in direct))
        trans = [c for c in closure(cid) if c not in direct]
        if trans:
            lines.append(f"  - transitive: " + ", ".join(f"`{c}`" for c in trans))
    lines.append("")

    # Layered study order (Kahn levels over the prerequisite subgraph)
    lines.append("## Layered study order")
    lines.append("")
    lines.append("Concepts in the same layer are independent; every concept's "
                 "prerequisites live in earlier layers. Concepts with no "
                 "prerequisite edges in the registry are omitted unless someone "
                 "depends on them.")
    lines.append("")
    involved = set(prereqs)
    for deps in prereqs.values():
        involved |= deps
    remaining = dict((c, set(d for d in prereqs.get(c, ()) if d in involved))
                     for c in involved)
    layer_no = 0
    while remaining:
        ready = sorted(c for c, deps in remaining.items() if not deps)
        if not ready:  # cycle guard — report and stop
            lines.append(f"- ⚠️ cycle detected among: "
                         + ", ".join(f"`{c}`" for c in sorted(remaining)))
            break
        layer_no += 1
        labels = [f"`{c}`" for c in ready]
        lines.append(f"- **Layer {layer_no}:** " + " · ".join(labels))
        for c in ready:
            remaining.pop(c)
        for deps in remaining.values():
            deps.difference_update(ready)
    lines.append("")

    lines.append("## Modules → workspaces → concepts")
    lines.append("")
    m2w = backlinks.get("module_to_workspaces", {})
    for mid in sorted(repo.modules):
        module = repo.modules[mid]
        lines.append(f"- **{module.get('title', mid)}** (`{mid}`)")
        wids = m2w.get(mid, [])
        if not wids:
            lines.append("  - (no workspace references it)")
            continue
        for wid in wids:
            ws = repo.workspaces.get(wid)
            if ws is None:
                continue
            cids = sorted(ws.meta.get("concepts", []) or [])
            tail = (": " + ", ".join(f"`{c}`" for c in cids)) if cids else ""
            state = "archived" if ws.archived else ws.status
            lines.append(f"  - `{wid}` ({state}){tail}")
    lines.append("")
    return "\n".join(lines)


def build_concept_map(repo: Repo, generated_at: str) -> str:
    """Mermaid rendering of the prerequisite graph (requires + builds-on).

    Human-facing counterpart of the dependency report: GitHub and VS Code
    render the diagram natively. Context edges (motivates/applies-in/
    contrasts-with) are excluded, same as the dependency report.
    """
    lines = _md_header("Concept map (prerequisite graph)", generated_at)
    lines.append("*Arrows point from prerequisite to dependent — follow the "
                 "arrows to get a study order. Solid = `requires`, "
                 "dotted = `builds-on`. Textual version: "
                 "`dependency-report.md`.*")
    lines.append("")

    edges = sorted(
        (str(r["to"]), str(r["from"]), str(r["type"]))
        for r in repo.relations if r.get("type") in PREREQ_TYPES)
    if not edges:
        lines.append("(no prerequisite edges in the relation registry)")
        lines.append("")
        return "\n".join(lines)

    involved = sorted({c for e in edges for c in e[:2]})
    nodes = mermaid_node_ids(involved)
    lines.append("```mermaid")
    lines.append("graph LR")
    for cid in involved:
        label = str(repo.concepts.get(cid, {}).get("label", cid)).replace('"', "'")
        lines.append(f'    {nodes[cid]}["{label}"]')
    for pre, dep, rtype in edges:
        arrow = "-->" if rtype == "requires" else "-.->"
        lines.append(f"    {nodes[pre]} {arrow} {nodes[dep]}")
    lines.append("```")
    lines.append("")
    return "\n".join(lines)


def build_health(repo: Repo, generated_at: str) -> str:
    lines = _md_header("Health report", generated_at)
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- notes: {len(repo.notes)}")
    by_role: dict[str, int] = {}
    for n in repo.notes.values():
        by_role[n.meta.get("role", "synthesis")] = by_role.get(n.meta.get("role", "synthesis"), 0) + 1
    for role in sorted(by_role):
        lines.append(f"  - {role}: {by_role[role]}")
    lines.append(f"- concepts: {len(repo.concepts)}")
    lines.append(f"- concept relations: {len(repo.relations)}")
    lines.append(f"- sources: {len(repo.sources)}")
    lines.append(f"- modules: {len(repo.modules)}")
    lines.append(f"- active workspaces: {len(repo.active_workspaces())} "
                 f"(standing: {sum(1 for w in repo.active_workspaces() if w.standing)})")
    lines.append(f"- archived workspaces: {len(repo.archived_workspaces())}")
    inbox = repo.root / "work" / "inbox"
    n_inbox = len([f for f in inbox.iterdir() if not f.name.startswith(".")]) if inbox.is_dir() else 0
    lines.append(f"- inbox items: {n_inbox}")
    lines.append("")
    lines.append("## Notes without concept links")
    lines.append("")
    orphans = [n.id for n in sorted(repo.notes.values(), key=lambda n: n.id)
               if not n.meta.get("concepts")]
    lines.extend(f"- `{nid}`" for nid in orphans) if orphans else lines.append("(none)")
    lines.append("")
    lines.append("## Concepts without notes")
    lines.append("")
    linked = {c for n in repo.notes.values() for c in (n.meta.get("concepts") or [])}
    unlinked = [c for c in sorted(repo.concepts) if c not in linked]
    lines.extend(f"- `{c}`" for c in unlinked) if unlinked else lines.append("(none)")
    lines.append("")

    # Source wiring / visibility debt (ADR-005). A source surfaces in concept
    # retrieval only through a concept-linked evaluation, on a shelf only
    # through a collection, and via notes only through note `sources:` links.
    # This is a maintenance SIGNAL, never a backlog: debt is repaid on use
    # (WORKFLOWS §6a "wire on use"), not as a bulk project.
    in_collection: set[str] = set()
    for doc in repo.collections.values():
        for e in doc.get("entries") or []:
            if isinstance(e, dict) and e.get("source"):
                in_collection.add(str(e["source"]))
    note_linked = {str(s) for n in repo.notes.values()
                   for s in (n.meta.get("sources") or [])}
    with_eval: set[str] = set()
    concept_wired: set[str] = set()
    for sid, s in repo.sources.items():
        evs = [ev for ev in (s.get("evaluations") or []) if isinstance(ev, dict)]
        if evs:
            with_eval.add(sid)
        if any(ev.get("concepts") for ev in evs):
            concept_wired.add(sid)
    least = sorted(sid for sid in repo.sources
                   if sid not in concept_wired and sid not in in_collection
                   and sid not in note_linked)
    lines.append("## Source wiring (visibility debt)")
    lines.append("")
    lines.append(f"- sources with ≥1 evaluation: {len(with_eval)}/{len(repo.sources)}")
    lines.append(f"- concept-wired (≥1 evaluation naming concepts — visible to "
                 f"concept retrieval): {len(concept_wired)}/{len(repo.sources)}")
    lines.append(f"- on ≥1 shelf (collections): {len(in_collection & set(repo.sources))}"
                 f"/{len(repo.sources)}")
    lines.append(f"- referenced by ≥1 note: {len(note_linked & set(repo.sources))}"
                 f"/{len(repo.sources)}")
    lines.append(f"- **least visible** (no concept link, no shelf, no note): "
                 f"{len(least)}")
    if least:
        by_origin: dict[str, list[str]] = {}
        for sid in least:
            origin = repo.source_origins.get(sid)
            key = origin.name if origin else "(unknown origin)"
            by_origin.setdefault(key, []).append(sid)
        lines.append("")
        for key in sorted(by_origin):
            ids = " · ".join(f"`{sid}`" for sid in by_origin[key])
            lines.append(f"  - {key}: {ids}")
    lines.append("")
    lines.append("*Wire on use (WORKFLOWS §6a): when one of these actually comes "
                 "up in a session, add the minimal evaluation stub — concepts + "
                 "roles + one strengths line. Never bulk-backfill.*")
    lines.append("")

    # Review & evidence adoption (2026-08-03). The fields (`reviewed`,
    # `evidence`, `state`) have existed in note.schema.json since v3 — this
    # section surfaces how far they are actually used. Adopt on touch
    # (WORKFLOWS §13 review a note, §8 record evidence); never bulk-backfill.
    ad = adoption_counts(repo)
    lines.append("## Review & evidence adoption")
    lines.append("")
    lines.append(f"- notes with a `reviewed` date: {ad['notes_reviewed']}"
                 f"/{ad['notes_total']}")
    if ad["changed_since_review"]:
        lines.append("  - changed after their last review (Git postdates "
                     "`reviewed`, or uncommitted): "
                     + " · ".join(f"`{nid}`" for nid in ad["changed_since_review"]))
    lines.append(f"- notes with `evidence` entries: {ad['notes_with_evidence']}"
                 f"/{ad['notes_total']}")
    lines.append("- note states: "
                 + " · ".join(f"{k}: {ad['by_state'][k]}"
                              for k in sorted(ad["by_state"])))
    lines.append("")
    lines.append("*The schema already has these fields; the gap is adoption. "
                 "Set `reviewed` when a semantic review actually happens "
                 "(WORKFLOWS §13 — file modification is not review) and attach "
                 "`evidence` when a derivation/exercise/implementation exists "
                 "(§8). On-touch only — never as a bulk project.*")
    lines.append("")
    lines.append("*Run `python tools/validate.py` for the full rule check.*")
    lines.append("")
    return "\n".join(lines)


def _garden_relpath(repo: Repo, note) -> str:
    """Markdown link from generated/nebula.md to a garden note (both local)."""
    return "../" + note.path.relative_to(repo.root).as_posix()


def build_nebula(repo: Repo, generated_at: str) -> str:
    """The Nebula: a disposable index of the Garden (CLAUDE.md §14).

    Every free-form note in knowledge/garden/, grouped by inline #tag and
    annotated with a harvest-pressure signal — its last-touched date per Git, or
    'uncommitted' when it is not yet in history. Within each tag the loosest ends
    float up (uncommitted first, then oldest committed) so the ideas most in need
    of a harvest-commit-or-prune decision surface at the top.

    The Garden is deliberately unvalidated; this view is the only lens on it and,
    like every generated file, is disposable and never canonical. Deterministic:
    notes are sorted and dates come from Git, never the wall clock.
    """
    lines = _md_header("Nebula — the Garden of unvalidated ideas", generated_at)

    if not repo.garden_notes:
        lines.append(
            "The Garden is empty. Drop half-formed ideas into `knowledge/garden/` "
            "as plain Markdown (sprinkle `#tags` like `#chaos`, `#philosophy`); "
            "they gestate there — exempt from `make check` — until you say "
            '"Harvest the Garden" to promote the ripe ones into `knowledge/notes/`.')
        lines.append("")
        return "\n".join(lines)

    # One Git call per note, memoized: '' means uncommitted (not yet in history).
    dates = {
        n.path: _git_last_commit(repo.root, n.path.relative_to(repo.root).as_posix())
        for n in repo.garden_notes
    }

    total = len(repo.garden_notes)
    uncommitted = sum(1 for n in repo.garden_notes if not dates[n.path])
    lines.append(
        f"*{total} idea(s) gestating"
        + (f", {uncommitted} not yet committed" if uncommitted else "")
        + ". A disposable lens on an **unvalidated** layer — nothing here is "
        'canonical or link-checked. Say **"Harvest the Garden"** to promote ripe '
        "ideas into the fortress; let the rest gestate or prune them. Dates are "
        "last-touched per Git — **uncommitted and oldest first = ripest for "
        "harvest-or-discard**.*")
    lines.append("")

    # Group by tag (a note appears under each of its tags); untagged bucket last.
    by_tag: dict[str, list] = {}
    for n in repo.garden_notes:
        for k in (n.tags or ["(untagged)"]):
            by_tag.setdefault(k, []).append(n)

    for tag in sorted(by_tag, key=lambda t: (t == "(untagged)", t)):
        heading = "(untagged)" if tag == "(untagged)" else f"#{tag}"
        notes = by_tag[tag]
        lines.append(f"## {heading} · {len(notes)}")
        lines.append("")
        # '' (uncommitted) sorts before any ISO date, then oldest date first.
        for n in sorted(notes, key=lambda n: (dates[n.path], n.slug)):
            stamp = dates[n.path] or "uncommitted"
            others = [t for t in (n.tags or []) if t != tag]
            extra = ("  · " + " ".join(f"#{t}" for t in others)) if others else ""
            lines.append(f"- `{stamp}` — [{n.title}]({_garden_relpath(repo, n)}){extra}")
        lines.append("")

    return "\n".join(lines)


# ------------------------------------------------------- domain atlas (ADR-005)

# View-level shelf→domain mapping. Domains = the seven note buckets of
# ARCHITECTURE §3.3. Deliberately NOT a canonical field: collections stay
# domain-free records; this dict is presentation only (same pattern as
# tools/build_materials_index.py::COLLECTION_DOMAIN, whose domain set is the
# materials topic tree instead). A collection missing from the map lands under
# `cross-domain`, so a new shelf is never silently dropped from the atlas.
ATLAS_DOMAINS = [
    "mathematics", "machine-learning", "systems", "data-systems",
    "algorithms", "programming", "cross-domain",
]
ATLAS_COLLECTION_DOMAIN = {
    "math-bookshelf": "mathematics", "math-lecture-series": "mathematics",
    "ml-bookshelf": "machine-learning", "ml-lecture-series": "machine-learning",
    "ml-explainers": "machine-learning", "ml-broaden-later": "machine-learning",
    "papers-shelf": "machine-learning",
    "ml-systems-bookshelf": "systems", "ml-systems-lecture-series": "systems",
    "algorithms-bookshelf": "algorithms", "algorithms-lecture-series": "algorithms",
    "programming-bookshelf": "programming", "programming-video-courses": "programming",
    "python-internals-shelf": "programming", "project-toolbox": "programming",
}

_ATLAS_SKIP_NAMES = {".DS_Store", "INDEX.html", "README.md", "FILES.txt"}


def _atlas_short(text: str, limit: int = 220) -> str:
    """Collapse a collection description to one compact line."""
    s = " ".join(str(text).split())
    if len(s) <= limit:
        return s
    cut = s.rfind(" ", 0, limit)
    return s[: cut if cut > 0 else limit].rstrip(" ,;—-") + " …"


_ATLAS_ROLE_ORDER = {"crosswalk": 0, "reference": 1, "synthesis": 2,
                     "exercise-bank": 3, "mock-exam": 4}


def _atlas_role_order(role: str) -> tuple[int, str]:
    return (_ATLAS_ROLE_ORDER.get(role, 9), role)


def _atlas_note_link(note, repo: Repo) -> str:
    """One navigable atlas row for a note: title link, id, and state."""
    title = note.meta.get("title", note.id)
    try:
        rel = note.path.relative_to(repo.root).as_posix()
        label = f"[{title}](../{rel})"
    except ValueError:  # note outside the repo root — degrade to plain text
        label = str(title)
    state = note.meta.get("state")
    return f"{label} — `{note.id}`" + (f" · {state}" if state else "")


def _count_material_files(base: Path) -> int:
    """Files under a materials subtree (view signal only; hidden/support-skip
    names excluded). Returns 0 when the subtree does not exist."""
    if not base.is_dir():
        return 0
    n = 0
    for f in base.rglob("*"):
        if not f.is_file() or f.name in _ATLAS_SKIP_NAMES:
            continue
        rel = f.relative_to(base)
        if any(part.startswith(".") for part in rel.parts):
            continue
        n += 1
    return n


def build_domain_atlas(repo: Repo, generated_at: str) -> str:
    """The cross-domain map (ADR-005): every domain's note coverage, curated
    shelves and wiring hubs on one page, plus the strata deliberately OUTSIDE
    retrieval — so no session's field of view collapses to the active
    workspace's domain.

    The **At a glance** block is sized to be read at every session start
    (CLAUDE.md §2); the full sections are opened on demand (CLAUDE.md §7).
    Judgments are harvested from canonical fields (collection descriptions,
    note titles) — this view authors nothing.
    """
    lines = _md_header("Domain atlas — the cross-domain map", generated_at)

    # -- gather ------------------------------------------------------------
    notes_dir = repo.root / "knowledge" / "notes"
    notes_by_domain: dict[str, list] = {}
    for n in repo.notes.values():
        try:
            bucket = n.path.relative_to(notes_dir).parts[0]
        except ValueError:
            bucket = "cross-domain"
        if bucket.endswith(".md"):  # note directly under notes/ (unbucketed)
            bucket = "cross-domain"
        notes_by_domain.setdefault(bucket, []).append(n)

    shelves_by_domain: dict[str, list[tuple[str, dict, int]]] = {}
    for name in sorted(repo.collections):
        doc = repo.collections[name]
        entries = [e for e in (doc.get("entries") or []) if isinstance(e, dict)]
        dom = ATLAS_COLLECTION_DOMAIN.get(name, "cross-domain")
        shelves_by_domain.setdefault(dom, []).append((name, doc, len(entries)))

    domains = list(ATLAS_DOMAINS)
    for extra in sorted(set(notes_by_domain) | set(shelves_by_domain)):
        if extra not in domains:  # future bucket: appears, never dropped
            domains.append(extra)

    def role_counts(notes: list) -> dict[str, int]:
        out: dict[str, int] = {}
        for n in notes:
            r = n.meta.get("role", "synthesis")
            out[r] = out.get(r, 0) + 1
        return out

    # -- At a glance (the session-start block, CLAUDE.md §2) ---------------
    lines.append("## At a glance")
    lines.append("")
    for dom in domains:
        notes = notes_by_domain.get(dom, [])
        shelves = shelves_by_domain.get(dom, [])
        n_entries = sum(c for _, _, c in shelves)
        n_cross = sum(1 for n in notes if n.meta.get("role") == "crosswalk")
        bits = []
        noun = "note" if len(notes) == 1 else "notes"
        bits.append(f"{len(notes)} {noun}" + (f" ({n_cross} crosswalk)" if n_cross else ""))
        bits.append(f"{len(shelves)} shelves ({n_entries} entries)" if shelves
                    else "no shelves yet")
        lines.append(f"- **{dom}** — " + " · ".join(bits))
    lines.append(
        "- **Outside this map (deliberate):** Foundations archive (unregistered; "
        "names in `materials/FILES.txt`) · Master's Planning quarantine "
        "(boundary only) · frozen `legacy/` · quarantined `Job/` "
        "(CLAUDE.md §13) — details in the last section.")
    lines.append("")
    lines.append(
        "*Per-domain shelves and wiring hubs below · per-concept joins → "
        "`concept-index.md` · full source detail → `source-index.md` · wiring "
        "debt → `reports/health.md`.*")
    lines.append("")

    # -- full per-domain sections ------------------------------------------
    for dom in domains:
        notes = sorted(notes_by_domain.get(dom, []), key=lambda n: n.id)
        shelves = shelves_by_domain.get(dom, [])
        lines.append(f"## {dom}")
        lines.append("")
        if notes:
            rc = role_counts(notes)
            parts = " · ".join(f"{r} {rc[r]}" for r in sorted(rc))
            lines.append(f"Notes: {len(notes)} — {parts}")
        else:
            lines.append("Notes: none yet")
        cross = [n for n in notes if n.meta.get("role") == "crosswalk"]
        if cross:
            lines.append("")
            lines.append("Wiring hubs (crosswalks):")
            lines.append("")
            for n in cross:
                lines.append(f"- {_atlas_note_link(n, repo)}")
        if notes:
            # A map that only counts its territory is not a map: every note is
            # listed and linked, grouped by role, so the atlas can be navigated
            # instead of merely skimmed (ADR-005 asks for reach, not a census).
            lines.append("")
            lines.append("Notes by role:")
            lines.append("")
            by_role: dict[str, list] = {}
            for n in notes:
                by_role.setdefault(n.meta.get("role", "synthesis"), []).append(n)
            for role in sorted(by_role, key=_atlas_role_order):
                lines.append(f"- **{role}** ({len(by_role[role])})")
                for n in sorted(by_role[role], key=lambda x: str(x.meta.get("title", x.id))):
                    lines.append(f"  - {_atlas_note_link(n, repo)}")
        lines.append("")
        if shelves:
            lines.append("Shelves:")
            lines.append("")
            for name, doc, count in shelves:
                title = doc.get("title", name)
                desc = _atlas_short(doc.get("description", "")) if doc.get("description") else ""
                lines.append(f"- **[{title}](collections/{name}.md)** ({count})"
                             + (f" — {desc}" if desc else ""))
        else:
            lines.append("Shelves: none yet — sources for this domain surface only "
                         "through concept links and note references.")
        lines.append("")

    # -- deliberately excluded strata --------------------------------------
    lines.append("## Not in this map — deliberately excluded strata")
    lines.append("")
    materials = repo.learningos_root / "materials"
    if materials.is_dir():
        n_found = _count_material_files(materials / "Foundations")
        if n_found:
            lines.append(
                f"- **Foundations archive** — {n_found} files under "
                "`materials/Foundations/` (undergrad/general reference, NOT "
                "registered sources; browse only). Names are greppable in "
                "`materials/FILES.txt` (`make materials`); promotion path is "
                "WORKFLOWS §6a when one becomes relevant.")
        n_unsorted = _count_material_files(materials / "_unsorted")
        if n_unsorted:
            lines.append(
                f"- **materials/_unsorted** — {n_unsorted} files awaiting "
                "registration (WORKFLOWS §6a).")
    else:
        lines.append("- **Materials tree** — not reachable from this checkout; "
                     "archive counts unavailable.")
    lines.append(
        "- **Master's Planning** — Git-tracked operational quarantine; only its "
        "boundary record is normally loadable. Content, counts and menus are "
        "excluded until deliberate future promotion (WORKFLOWS §27).")
    if (repo.root.parent.parent / "legacy").is_dir():
        lines.append(
            "- **Legacy tree** — the frozen pre-v3 history beside `LearningOS/` "
            "(tag `pre-v3-baseline`); historical context only, never canonical, "
            "never retrieved by default (ARCHITECTURE §2.4).")
    lines.append(
        "- **`Job/`** — quarantined (CLAUDE.md §13); outside every map by design.")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------- concept canvas (ADR-006)

# JSON Canvas edge colors by relation type ("1".."6" = Obsidian presets).
CANVAS_EDGE_COLORS = {
    "requires": "1", "builds-on": "2", "derives": "3", "generalizes": "4",
    "contrasts-with": "5", "equivalent-to": "6",
    "applies-in": "#8fa1b3", "motivates": "#d08770",
}
_CANVAS_NODE_W = 320
_CANVAS_NODE_H = 150
_CANVAS_GAP_X = 200
_CANVAS_GAP_Y = 40


def _concept_depths(relations: list[dict], involved: set[str]) -> dict[str, int]:
    """Longest-prerequisite-path depth over requires/builds-on edges (the same
    edge set as the Mermaid concept map). Cycles fall back to depth 0."""
    prereqs: dict[str, set[str]] = {c: set() for c in involved}
    for r in relations:
        if r.get("type") in PREREQ_TYPES:
            a, b = str(r.get("from")), str(r.get("to"))
            if a in involved and b in involved:
                prereqs[a].add(b)
    depths: dict[str, int] = {}

    def depth(c: str, seen: frozenset[str]) -> int:
        if c in depths:
            return depths[c]
        if c in seen:
            return 0  # cycle guard
        d = 0
        for p in sorted(prereqs.get(c, ())):
            d = max(d, 1 + depth(p, seen | {c}))
        depths[c] = d
        return d

    for c in sorted(involved):
        depth(c, frozenset())
    return depths


def build_concept_canvas(repo: Repo, generated_at: str) -> dict:
    """JSON Canvas (https://jsoncanvas.org) rendering of the relation registry
    (ADR-006): every concept appearing in >=1 relation becomes a card (label,
    aliases, links to up to three notes); every relation becomes a labelled,
    colored edge. Deterministic layered layout: x = prerequisite depth,
    y = alphabetical within the layer. Obsidian renders this natively; the
    file is disposable like every generated output."""
    involved = set()
    for r in repo.relations:
        involved.add(str(r.get("from")))
        involved.add(str(r.get("to")))
    involved &= set(repo.concepts)

    depths = _concept_depths(repo.relations, involved)
    by_layer: dict[int, list[str]] = {}
    for c in sorted(involved):
        by_layer.setdefault(depths[c], []).append(c)

    note_links: dict[str, list[str]] = {c: [] for c in involved}
    for nid in sorted(repo.notes):
        n = repo.notes[nid]
        rel = n.path.relative_to(repo.root).as_posix()
        for c in n.meta.get("concepts") or []:
            if c in note_links and len(note_links[c]) < 3:
                note_links[c].append(f"[{nid}](../{rel})")

    nodes = []
    for layer in sorted(by_layer):
        for i, cid in enumerate(by_layer[layer]):
            rec = repo.concepts[cid]
            label = rec.get("label", cid)
            aliases = ", ".join(rec.get("aliases") or [])
            text = f"**{label}**\n`{cid}`"
            if aliases:
                text += f"\n_{aliases}_"
            if note_links[cid]:
                text += "\n" + " · ".join(note_links[cid])
            nodes.append({
                "id": cid, "type": "text", "text": text,
                "x": layer * (_CANVAS_NODE_W + _CANVAS_GAP_X),
                "y": i * (_CANVAS_NODE_H + _CANVAS_GAP_Y),
                "width": _CANVAS_NODE_W, "height": _CANVAS_NODE_H,
            })

    edges = []
    for r in repo.relations:
        a, b, t = str(r.get("from")), str(r.get("to")), str(r.get("type"))
        if a not in involved or b not in involved:
            continue
        edges.append({
            "id": f"{a}--{t}--{b}",
            "fromNode": a, "fromSide": "left",
            "toNode": b, "toSide": "right",
            "label": t, "color": CANVAS_EDGE_COLORS.get(t, "4"),
        })
    edges.sort(key=lambda e: e["id"])

    return {"_generated": _json_header(generated_at), "nodes": nodes, "edges": edges}


# ------------------------------------------------------- reading room (ADR-006)

def build_reading_room(repo: Repo, generated_at: str) -> str:
    """The human home page (ADR-006): one generated screen that composes the
    deeper views and links into them. Interface layers (Obsidian, GitHub
    mobile, a bare editor) open THIS file first. It deliberately duplicates no
    canonical fact — everything is drawn from the same inputs as the views it
    links, and it is disposable like every generated file. Deterministic:
    dates come from Git, never the wall clock (no countdowns — VALIDATION's
    byte-identical rule, human-operability review #11)."""
    lines = _md_header("Reading room", generated_at)
    lines.append("*The human home page — start here. Everything below is a "
                 "link into a deeper view; rebuild anytime with `make views` "
                 "(or `python tools/los.py generate`).*")
    lines.append("")

    # Academic dates include available sittings before registration and the
    # windows that gate them; all facts still live in the owning module.
    lines.append("## Academic dates")
    lines.append("")
    deadlines = _academic_deadlines(repo)
    if deadlines:
        for row in deadlines:
            date = row["start_date"]
            if row.get("end_date") != date:
                date += f" to {row['end_date']}"
            if row["kind"] == "registration-window":
                titles = ", ".join(module["title"] for module in row["modules"])
                lines.append(f"- **{date}** — {row['label']}: {titles}")
            else:
                lines.append(f"- **{date}** — {row['title']} ({row['label']}; "
                             f"{row['registration_state']})")
    else:
        lines.append("(no structured academic dates in module records)")
    lines.append("")
    lines.append("Full spine, priorities and neglect signals: "
                 "[coordination-view.md](coordination-view.md)")
    lines.append("")

    # Active workspaces with their next actions (from frontmatter + CONTEXT).
    active = sorted(repo.active_workspaces(), key=lambda w: w.id)
    lines.append(f"## Active workspaces ({len(active)})")
    lines.append("")
    if active:
        for ws in active:
            na = _first_para(ws.section("Next Action"))
            standing = " · standing" if ws.standing else ""
            lines.append(f"- `{ws.id}` ({ws.status}{standing})"
                         + (f" — next: {na}" if na else ""))
    else:
        lines.append("(no active workspaces)")
    lines.append("")

    # Recently changed notes: uncommitted first (most in need of a commit),
    # then newest last-commit date. Same Git-derived idiom as the Nebula.
    lines.append("## Recently changed notes")
    lines.append("")
    dated = []
    for n in repo.notes.values():
        rel = n.path.relative_to(repo.root).as_posix()
        dated.append((_git_last_commit(repo.root, rel), n))
    uncommitted = sorted((n for d, n in dated if not d), key=lambda n: n.id)
    committed = sorted(((d, n) for d, n in dated if d),
                       key=lambda t: (t[0], t[1].id), reverse=True)
    shown = 0
    for n in uncommitted[:10]:
        rel = n.path.relative_to(repo.root).as_posix()
        lines.append(f"- `uncommitted` — [{n.meta.get('title', n.id)}](../{rel}) "
                     f"· {n.meta.get('state', '')}")
        shown += 1
    for d, n in committed[: max(0, 10 - shown)]:
        rel = n.path.relative_to(repo.root).as_posix()
        lines.append(f"- `{d}` — [{n.meta.get('title', n.id)}](../{rel}) "
                     f"· {n.meta.get('state', '')}")
    if not dated:
        lines.append("(no notes yet)")
    lines.append("")

    # Queues that want a decision or a harvest.
    lines.append("## Queues")
    lines.append("")
    inbox = repo.root / "work" / "inbox"
    n_inbox = len([f for f in inbox.iterdir()
                   if not f.name.startswith(".")]) if inbox.is_dir() else 0
    lines.append(f"- inbox: {n_inbox} item(s) in `work/inbox/` "
                 "(the operator routes; trend toward empty)")
    lines.append(f"- garden: {len(repo.garden_notes)} idea(s) gestating — "
                 "[nebula.md](nebula.md)")
    lines.extend(_materials_queue_rows(repo)
                 or ["- materials queues: empty (nothing awaits a decision)"])
    lines.append("")

    # Review & evidence adoption, one line; details live in the health report.
    ad = adoption_counts(repo)
    lines.append("## Review & evidence adoption")
    lines.append("")
    lines.append(f"- reviewed: {ad['notes_reviewed']}/{ad['notes_total']} · "
                 f"with evidence: {ad['notes_with_evidence']}/{ad['notes_total']} · "
                 "details: [reports/health.md](reports/health.md)")
    lines.append("")

    lines.append("## All views")
    lines.append("")
    lines.append("[domain-atlas.md](domain-atlas.md) (cross-domain map) · "
                 "[concept-index.md](concept-index.md) · "
                 "[concept-map.md](concept-map.md) · "
                 "[concept-canvas.canvas](concept-canvas.canvas) (Obsidian) · "
                 "[source-index.md](source-index.md) · "
                 "[dependency-report.md](dependency-report.md) · "
                 "[module-view.md](module-view.md) · "
                 "[nebula.md](nebula.md) · "
                 "[reports/health.md](reports/health.md) · "
                 "[reports/validation-report.md](reports/validation-report.md)")
    lines.append("")
    return "\n".join(lines)


def generate_all(repo: Repo, generated_at: str | None = None) -> dict[str, str]:
    """Build all outputs; returns {relative path: content}.

    The default timestamp is the last-commit time (stable_generated_at), so
    repeated generation over the same committed tree is byte-for-byte identical.
    """
    generated_at = generated_at or stable_generated_at(repo.root)
    backlinks = build_backlinks(repo, generated_at)
    manifest = build_manifest(repo, generated_at, backlinks)
    outputs = {
        "manifest.json": json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        "backlinks.json": json.dumps(backlinks, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        "concept-index.md": build_concept_index(repo, backlinks, generated_at) + "\n",
        "source-index.md": build_source_index(repo, generated_at) + "\n",
        "module-view.md": build_module_view(repo, generated_at) + "\n",
        "coordination-view.md": build_coordination_view(repo, generated_at) + "\n",
        "dependency-report.md": build_dependency_report(repo, backlinks, generated_at) + "\n",
        "concept-map.md": build_concept_map(repo, generated_at) + "\n",
        "domain-atlas.md": build_domain_atlas(repo, generated_at) + "\n",
        "reports/health.md": build_health(repo, generated_at) + "\n",
        "nebula.md": build_nebula(repo, generated_at) + "\n",
        "reading-room.md": build_reading_room(repo, generated_at) + "\n",
        "concept-canvas.canvas": json.dumps(
            build_concept_canvas(repo, generated_at),
            indent=2, sort_keys=True, ensure_ascii=False) + "\n",
    }
    for name in sorted(repo.collections):
        outputs[f"collections/{name}.md"] = build_collection_view(
            repo, name, repo.collections[name], generated_at) + "\n"
    return outputs


# Files under generated/ that write_outputs must never delete: repo scaffolding,
# OS noise, and the validator's own report (written by tools/validate.py).
_KEEP_NAMES = {".gitkeep", ".DS_Store"}
_KEEP_REPORT_PREFIX = "validation-report"


def write_outputs(repo: Repo, outputs: dict[str, str]) -> None:
    """Write all outputs AND delete stale generated files, so that generated/
    exactly reflects the canonical data (e.g. views of deleted collections
    do not linger)."""
    gen = repo.root / "generated"
    (gen / "reports").mkdir(parents=True, exist_ok=True)
    for rel, content in outputs.items():
        target = gen / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        # Never expose a half-written projection to Obsidian. os.replace is an
        # atomic publication step on the same filesystem; manifest.json is
        # published last because it is the versioned interface contract.
        if rel == "manifest.json":
            continue
        tmp = target.with_name(f".{target.name}.tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, target)
    if "manifest.json" in outputs:
        target = gen / "manifest.json"
        tmp = target.with_name(".manifest.json.tmp")
        tmp.write_text(outputs["manifest.json"], encoding="utf-8")
        os.replace(tmp, target)
    _remove_stale(gen, outputs)


def _remove_stale(gen: Path, outputs: dict[str, str]) -> None:
    expected = {PurePosixPath(rel) for rel in outputs}
    stale_dirs: list[Path] = []
    for f in sorted(gen.rglob("*")):
        if f.is_dir():
            stale_dirs.append(f)
            continue
        if f.name in _KEEP_NAMES:
            continue
        rel = PurePosixPath(f.relative_to(gen).as_posix())
        if rel.parts and rel.parts[0] == "reports" \
                and f.name.startswith(_KEEP_REPORT_PREFIX):
            continue
        if rel not in expected:
            f.unlink()
    # Prune directories left empty by the deletions (deepest first);
    # rmdir refuses non-empty directories, so this is safe.
    for d in sorted(stale_dirs, reverse=True):
        if d.name == "reports":
            continue
        try:
            d.rmdir()
        except OSError:
            pass

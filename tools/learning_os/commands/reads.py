"""Bounded, snapshot-bound reads; complete content stays under its Core owner."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath

from learning_os.derived import DerivedError, evaluate
from learning_os.errors import unreadable_refusal
from learning_os.fingerprint import canonical_fingerprint
from learning_os.garden import garden_id
from learning_os.genout.atlas import ATLAS_DOMAINS
from learning_os.loader import load_repo
from learning_os.loading import FRONTMATTER_RE, Repo, load_garden, load_notes
from learning_os.material_analysis import observe_local_material
from learning_os.material_slices import parse_locator_page_ranges
from learning_os.material_synthesis import material_synthesis_freshness
from learning_os.materials_resolution import (
    MATERIAL_RESOURCE_SUFFIXES,
    MATERIAL_SCHEME,
    MATERIAL_SUFFIX_TOKEN,
    leading_material_locator,
    material_location,
    material_uri_authority,
    safe_material_locator,
)
from learning_os.pathing import PathBoundaryError, read_bytes_inside
from learning_os.search.index import NoteBlob, build_registry
from learning_os.search.model import POSTINGS_NODE_ID
from learning_os.search.query import candidates

from .suggest import expansion, not_found, with_suggestions
from .support import (
    StaleSnapshot,
    WriteRefused,
    _fresh_manifest,
    _fresh_manifest_and_repo,
    _operator_lock,
    _root,
)


def _window(args, maximum: int) -> tuple[int, int]:
    offset, limit = args.offset, args.limit
    if offset < 0 or not 1 <= limit <= maximum:
        raise WriteRefused(f"offset must be nonnegative and limit between 1 and {maximum}")
    if offset and not args.expected_snapshot:
        raise WriteRefused("continuation requires --expected-snapshot from the previous response")
    return offset, limit


def _snapshot(root, expected=None) -> str:
    actual = f"sha256:{canonical_fingerprint(root)}"
    if expected is not None and expected != actual:
        raise StaleSnapshot("snapshot changed; restart this read before continuing")
    return actual


def _print_stable(root, snapshot, payload) -> int:
    _snapshot(root, snapshot)
    print(json.dumps({"schema_version": 1, "snapshot_id": snapshot, **payload},
                     ensure_ascii=False, separators=(",", ":")))
    return 0


def _refusal(exc) -> int:
    print(f"los: {exc}", file=sys.stderr)
    return 3 if isinstance(exc, StaleSnapshot) else 2


def record_payload(manifest, record_id):
    resolved_id = (manifest.get("project_aliases") or {}).get(record_id, record_id)
    record = next((row for row in manifest["records"] if row.get("id") == resolved_id), None)
    if record is None:
        return None
    payload = dict(record)
    if resolved_id != record_id:
        payload["resolved_from"] = record_id
    return payload


def coordination_digest_fields(root: Path, sections) -> dict | None:
    """Whole-file plus per-section digests for the coordination record.

    The whole-file digest is the ``expected_content_sha256`` a
    coordination.section.revise apply must present; each per-section
    digest covers the projected section body exactly as served. Returns
    None when the file is absent or unreadable, so inspect degrades to
    the undigested record instead of refusing a read.
    """
    try:
        raw = read_bytes_inside(root, root / "work/COORDINATION.md")
    except (OSError, PathBoundaryError):
        return None
    fields: dict = {
        "content_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
    }
    if isinstance(sections, dict):
        fields["section_sha256"] = {
            str(heading): "sha256:" + hashlib.sha256(
                str(body).encode("utf-8")).hexdigest()
            for heading, body in sections.items()
        }
    return fields


def with_coordination_digests(root: Path, payload: dict) -> dict:
    """Attach coordination digests to an inspect payload, when it is one."""
    if not isinstance(payload, dict) or payload.get("type") != "coordination":
        return payload
    fields = coordination_digest_fields(root, payload.get("sections"))
    if fields is None:
        return payload
    return {**payload, **fields}


def _structure_nodes(structure):
    """(node, node_path) pairs for a project structure tree, in order."""
    found = []

    def visit(nodes, path):
        for node in nodes or []:
            if not isinstance(node, dict) or not isinstance(node.get("id"), str):
                continue
            here = [*path, node["id"]]
            found.append((node, here))
            visit(node.get("children"), here)

    if isinstance(structure, dict):
        visit(structure.get("nodes"), [])
    return found


def structural_payload(manifest: dict, record_id: str, repo=None) -> dict | None:
    """Resolve a structural sub-id to its owner context, or None.

    Pure over the manifest except for learning-path stages, which are not
    projected and need the loaded repo. Curriculum stages answer with
    their projected row plus the plan-edit-context invocation that owns
    edits (inspect carries no revision guards); path stages, detours,
    and project nodes answer with their row plus owners; bare milestone
    ids answer with their owning projects, since milestones carry no
    record of their own. Several owners for one id answer one ambiguous
    payload with every candidate in stable order.
    """
    matches: list[dict] = []
    for stage in manifest.get("stages", []) or []:
        if isinstance(stage, dict) and stage.get("id") == record_id:
            unit_id = stage.get("unit_id")
            matches.append({
                "id": record_id, "structural_kind": "curriculum-stage",
                "stage": dict(stage), "unit_id": unit_id,
                "study_map_id": stage.get("study_map_id"),
                "module_id": stage.get("module_id"),
                "edit_via": (f"plan-edit-context {unit_id} "
                             f"--stage-id {record_id}"),
            })
    if repo is not None:
        for path in sorted(getattr(repo, "learning_paths", {}).values(),
                           key=lambda candidate: candidate.id):
            for stage in path.data.get("stages", []) or []:
                if isinstance(stage, dict) and stage.get("id") == record_id:
                    matches.append({
                        "id": record_id, "structural_kind": "path-stage",
                        "stage": dict(stage), "path_id": path.id,
                        "workspace_id": path.workspace_id,
                        "archived": bool(path.archived),
                    })
    for study_map in manifest.get("study_maps", []) or []:
        if not isinstance(study_map, dict):
            continue
        for detour in study_map.get("detours", []) or []:
            if isinstance(detour, dict) and detour.get("id") == record_id:
                matches.append({
                    "id": record_id, "structural_kind": "detour",
                    "detour": dict(detour), "unit_id": study_map.get("unit_id"),
                    "study_map_id": study_map.get("id"),
                    "module_id": study_map.get("module_id"),
                })
    for record in manifest.get("records", []) or []:
        if not isinstance(record, dict) or record.get("type") != "project":
            continue
        for node, node_path in _structure_nodes(record.get("structure")):
            if node["id"] == record_id:
                matches.append({
                    "id": record_id, "structural_kind": "project-node",
                    "node": dict(node), "project_id": record.get("id"),
                    "node_path": node_path, "record_path": record.get("path"),
                })
        if record_id in (record.get("milestone_ids", []) or []):
            matches.append({
                "id": record_id, "structural_kind": "project-milestone",
                "project_id": record.get("id"), "record_path": record.get("path"),
                "note": ("milestones carry no record of their own; "
                         "the owning project is the record"),
            })
    if not matches:
        return None
    node_projects = {match["project_id"] for match in matches
                     if match["structural_kind"] == "project-node"}
    matches = [match for match in matches
               if match["structural_kind"] != "project-milestone"
               or match["project_id"] not in node_projects]
    if len(matches) == 1:
        return matches[0]
    return {"id": record_id, "structural_kind": "ambiguous",
            "candidates": matches}


#: Id prefixes that name structural sub-records rather than records.
STRUCTURAL_PREFIXES = ("stage-", "detour-", "step-", "workstream-", "milestone-")


def _inspect_candidates(manifest: dict, repo=None) -> list[str]:
    """Every id ``inspect`` could have resolved: records plus structural ids."""
    ids = [row.get("id") for row in manifest.get("records", []) or []
           if isinstance(row, dict) and isinstance(row.get("id"), str)]
    ids.extend(stage.get("id") for stage in manifest.get("stages", []) or []
               if isinstance(stage, dict) and isinstance(stage.get("id"), str))
    for study_map in manifest.get("study_maps", []) or []:
        if not isinstance(study_map, dict):
            continue
        ids.extend(detour.get("id") for detour in study_map.get("detours", []) or []
                   if isinstance(detour, dict) and isinstance(detour.get("id"), str))
    for record in manifest.get("records", []) or []:
        if not isinstance(record, dict) or record.get("type") != "project":
            continue
        ids.extend(node["id"] for node, _ in _structure_nodes(record.get("structure")))
        ids.extend(mid for mid in record.get("milestone_ids", []) or []
                   if isinstance(mid, str))
    if repo is not None:
        for path in getattr(repo, "learning_paths", {}).values():
            ids.extend(stage.get("id") for stage in path.data.get("stages", []) or []
                       if isinstance(stage, dict) and isinstance(stage.get("id"), str))
    return ids


def inspect_not_found(record_id: str, candidates=()) -> str:
    if isinstance(record_id, str) and record_id.startswith(STRUCTURAL_PREFIXES):
        return with_suggestions(
            f"record not found: {record_id} (no curriculum stage, path stage, "
            "detour, project node, or milestone carries this id)",
            record_id, candidates)
    return not_found("record", record_id, candidates)


def describe_unresolved_reference(manifest, record_id):
    """Name the record that references an unresolvable id, if there is one.

    Milestones and project structure nodes resolve through
    ``structural_payload``, so an advertised id that still misses is a
    dangling ``*_ids`` cross-reference (the validator refuses those; inspect
    reads without validating). On an inspect miss, point the caller at the
    referring record instead of a bare not-found. Returns None when nothing
    references the id.
    """
    for record in manifest.get("records", []) or []:
        referrer = record.get("id")
        if not referrer:
            continue
        for key, value in record.items():
            if (key.endswith("_ids") and isinstance(value, list)
                    and record_id in value):
                return (f"referenced by {referrer} "
                        f"({record.get('type', 'record')}) in {key}")
    return None


def inspect_batch(args) -> int:
    """Resolve a requested batch once; never return a partial or mixed read."""
    ids = [args.id, *args.more_ids]
    if len(ids) > 20:
        return _refusal("inspect accepts at most 20 IDs per batch")
    root = _root(args)
    try:
        with _operator_lock(root):
            snapshot = _snapshot(root)
            manifest, repo = _fresh_manifest_and_repo(root, snapshot_id=snapshot)
            records = []
            for record_id in ids:
                record = record_payload(manifest, record_id)
                if record is None:
                    record = structural_payload(manifest, record_id, repo)
                if record is not None:
                    record = with_coordination_digests(root, record)
                if record is None:
                    # The hint stays out of the refusal: _refusal classifies
                    # the exit code by message text, and a referrer id that
                    # says "snapshot" would turn this miss into exit 3.
                    code = _refusal(WriteRefused(inspect_not_found(
                        record_id, _inspect_candidates(manifest, repo))))
                    hint = describe_unresolved_reference(manifest, record_id)
                    if hint:
                        print(f"los: hint: {hint}", file=sys.stderr)
                    return code
                records.append(record)
            return _print_stable(root, snapshot, {
                "contract": "record-batch", "requested_ids": ids, "records": records,
            })
    except (WriteRefused, OSError) as exc:
        return _refusal(exc)


def _domain_glance(manifest):
    """Summarize the complete projection, independently of record pagination."""
    domains = {domain: {"domain": domain, "notes": 0, "crosswalks": 0,
                        "shelves": 0, "entries": 0}
               for domain in ATLAS_DOMAINS}
    for record in manifest.get("records", []):
        kind = record.get("type")
        if kind not in {"note", "collection", "topic-pack"}:
            continue
        domain = record.get("domain") or "cross-domain"
        if kind == "note" and record.get("path"):
            # The Domain atlas groups by the first directory under notes;
            # a record's domain can instead name a deeper subject folder.
            try:
                parts = PurePosixPath(record["path"]).relative_to("knowledge/notes").parts
                domain = parts[0] if len(parts) > 1 else "cross-domain"
            except ValueError:
                domain = "cross-domain"
        row = domains.setdefault(domain, {"domain": domain, "notes": 0,
                                         "crosswalks": 0, "shelves": 0, "entries": 0})
        if kind == "note":
            row["notes"] += 1
            row["crosswalks"] += record.get("role") == "crosswalk"
        else:
            row["shelves"] += 1
            row["entries"] += len(record.get("entries") or [])
    order = [*ATLAS_DOMAINS, *sorted(set(domains) - set(ATLAS_DOMAINS))]
    return [domains[domain] for domain in order]


def compact_bootstrap(args) -> int:
    root = _root(args)
    try:
        offset, limit = _window(args, 50)
        with _operator_lock(root):
            snapshot = _snapshot(root, args.expected_snapshot)
            manifest = _fresh_manifest(root, snapshot_id=snapshot)
            fields = ("id", "title", "status", "module_id", "program_id", "unit_id",
                      "current_study_map", "current_stage", "needs_study_map")
            collections = {}
            for name in ("programs", "modules", "projects", "units", "study_maps"):
                rows = sorted(manifest.get(name, []), key=lambda row: row["id"])
                items = [{key: row[key] for key in fields if key in row}
                         for row in rows[offset:offset + limit]]
                collections[name] = {"items": items, "total": len(rows),
                                     "next_offset": offset + limit if offset + limit < len(rows) else None}
            return _print_stable(root, snapshot, {
                "contract": "bootstrap-summary", "collections": collections,
                "resume_pointer": manifest.get("resume_pointer", {}),
                "counts": manifest.get("counts", {}),
                "domain_atlas": _domain_glance(manifest),
                "detail": {"record": "inspect ID", "notes": "note-read NOTE_ID",
                           "content_search": "search QUERY --type note --content",
                           "capabilities": "capabilities --compact --json",
                           "continuation": "bootstrap --compact --offset NEXT_OFFSET --expected-snapshot SNAPSHOT"},
            })
    except (WriteRefused, OSError) as exc:
        return _refusal(exc)


#: What the brief's ``pointer_state`` means. A confirmed pointer is the
#: learner's last explicit study action -- where study stopped -- never a
#: recommendation. The note ships in the payload so an agent reading only
#: this page cannot mistake one for the other.
POINTER_STATE_NOTE = "confirmed = where study stopped, not a recommendation"


def _pointer_state(manifest, pointer) -> str:
    """confirmed/missing/invalid for the brief page; the same rule as resume.

    Mirrors ``resume._resolve_stage``'s validity check against the manifest
    instead of the loaded repo, so the brief and resume cannot disagree:
    the pointer counts only when its module, unit, map, and stage all
    resolve and link together. Status plays no part here, exactly as in
    resume -- a pointer to a paused map is still where study stopped.
    """
    if not isinstance(pointer, dict) or not pointer:
        return "missing"
    units = {row.get("id"): row for row in manifest.get("units", [])
             if isinstance(row, dict)}
    maps = {row.get("id"): row for row in manifest.get("study_maps", [])
            if isinstance(row, dict)}
    unit = units.get(str(pointer.get("unit_id") or ""))
    study_map = maps.get(str(pointer.get("study_map_id") or ""))
    stages = study_map.get("stages", []) \
        if isinstance(study_map, dict) else []
    stage_ids = {stage.get("id") for stage in stages
                 if isinstance(stage, dict)}
    if (isinstance(unit, dict) and isinstance(study_map, dict)
            and unit.get("module_id") == pointer.get("module_id")
            and study_map.get("unit_id") == unit.get("id")
            and study_map.get("module_id") == unit.get("module_id")
            and pointer.get("stage_id") in stage_ids):
        return "confirmed"
    return "invalid"


def _recorded_options(manifest) -> list[dict]:
    """Every active track's recorded next action, in id order, unranked.

    Shown regardless of pointer state: the pointer says where study stopped,
    not which active workspace to choose next. Each active workspace's own
    next action carries its id and source path, never a derived ranking. A
    workspace with no recorded action still appears, with an empty action,
    so no track silently drops out of the page.
    """
    options = []
    for record in manifest.get("records", []):
        if not isinstance(record, dict) or record.get("type") != "workspace":
            continue
        if record.get("archived") or record.get("status") != "active":
            continue
        options.append({
            "workspace_id": record.get("id"),
            "next_action": record.get("next_action") or "",
            "source": record.get("path") or "",
        })
    return sorted(options, key=lambda row: str(row["workspace_id"]))


def _brief_deadlines(manifest: dict) -> list[dict]:
    """Brief-visible deadlines: absence of evidence reads as a missing fact.

    The projection says ``unregistered`` for a sitting with no recorded
    attempt; the brief is the surface where that absence is most easily
    misread as a decision, so it says ``registration not recorded``
    instead. ``unrecorded`` (elapsed — the record should exist by now)
    passes through unchanged. Row count and order are preserved.
    """
    rows = []
    for row in manifest.get("academic_deadlines", []):
        if isinstance(row, dict) and row.get("registration_state") == "unregistered":
            row = {**row, "registration_state": "registration not recorded"}
        rows.append(row)
    return rows


def brief_bootstrap(args) -> int:
    """One-page session entry: guards, resume, owed work, deadlines, expands.

    The plan-edit-context-brief shape applied to startup: identities and
    runnable commands, never collections or prose. Owed study maps name the
    units to prep, active maps name the stages to resume, deadlines carry
    the structured exam spine, and every follow-up read is a listed
    command. Single page by construction: paging belongs to --compact.
    """
    if getattr(args, "compact", False):
        return _refusal("bootstrap takes one of --brief, --compact")
    if args.offset:
        return _refusal("bootstrap --brief is a single page; "
                        "page the collections with --compact instead")
    root = _root(args)
    try:
        with _operator_lock(root):
            snapshot = _snapshot(root, args.expected_snapshot)
            manifest = _fresh_manifest(root, snapshot_id=snapshot)
            units = sorted(manifest.get("units", []),
                           key=lambda row: row["id"])
            owed = sorted(row["id"] for row in units
                          if row.get("needs_study_map"))
            # Resumable work only: paused maps are shelved tracks, not
            # candidates for the next session. Full bootstrap still lists
            # them; the brief names what can actually start.
            active = sorted(
                ({"id": row["id"], "unit_id": row.get("unit_id"),
                  "status": row.get("status"),
                  "current_stage": row.get("current_stage")}
                 for row in manifest.get("study_maps", [])
                 if row.get("status") in {"active", "ready"}),
                key=lambda row: row["id"])
            deadlines = _brief_deadlines(manifest)
            pointer = manifest.get("resume_pointer", {})
            state = _pointer_state(manifest, pointer)
            return _print_stable(root, snapshot, {
                "contract": "bootstrap-brief",
                "resume_pointer": pointer,
                "pointer_state": state,
                "pointer_state_note": POINTER_STATE_NOTE,
                "recorded_options": _recorded_options(manifest),
                "recorded_options_note": (
                    "workspace next actions are recorded options, not current "
                    "priorities; compare with current dates and state"
                ),
                "counts": manifest.get("counts", {}),
                "owed_study_maps": owed,
                "active_study_maps": active,
                "academic_deadlines": deadlines,
                "deadline_count": len(deadlines),
                "domain_atlas": _domain_glance(manifest),
                "expand": {
                    "full_compact": expansion(
                        "bootstrap", "--compact",
                        "--expected-snapshot", snapshot),
                    "continuation": expansion(
                        "bootstrap", "--compact", "--offset", "NEXT_OFFSET",
                        "--expected-snapshot", "SNAPSHOT"),
                    "resume": expansion("resume", "--json"),
                    "inspect": expansion("inspect", "ID"),
                    "coordination": expansion("inspect", "coordination"),
                    "intelligence_scan": expansion(
                        "intelligence-scan", "--brief", "--json"),
                    "note_read": expansion("note-read", "NOTE_ID"),
                    "inbox_list": expansion("inbox-list"),
                    "inbox_read": expansion("inbox-read", "NAME"),
                    "content_search": expansion(
                        "search", "QUERY", "--type", "note", "--content"),
                    "material_context": expansion("material-context", "QUERY"),
                    "ability_context": expansion(
                        "ability-context", "--expected-snapshot", snapshot),
                    "material_span": expansion(
                        "material-span", "UNIT_ID", "ROUTE_ID"),
                    "capability_detail": expansion(
                        "capabilities", "NAME", "--json"),
                    "plan_brief": [expansion(
                        "plan-edit-context", unit_id, "--brief",
                        "--expected-snapshot", snapshot)
                                   for unit_id in owed],
                },
            })
    except (WriteRefused, OSError) as exc:
        return _refusal(exc)


def _bytes_inside_owner(root, path, owner, *, escape, symlink):
    """Read bytes admitted by one owner directory; symlinks always refuse.

    The one admission rule for note, garden, and inbox reads: the resolved
    target must sit below the owner, and no path component may be a link —
    even one that would resolve in-tree. Only the refusal wording differs
    per surface.
    """
    try:
        path.resolve(strict=True).relative_to(owner.resolve(strict=True))
    except (ValueError, OSError) as exc:
        raise WriteRefused(escape) from exc
    if any(part.is_symlink() for part in (path, *path.parents) if part != root.parent):
        raise WriteRefused(symlink)
    return path.read_bytes()


def empty_search_hint(row_word: str, terms: list[str], hits: list[int]) -> str:
    """One-line stderr disclosure for an empty literal-AND result.

    Names how many rows each term matched on its own, so the caller can
    see which term eliminated the answer. stdout shapes stay untouched.
    """
    shown = [f"{term}={count}"
             for term, count in zip(terms[:20], hits[:20], strict=True)]
    if len(terms) > 20:
        shown.append(f"+{len(terms) - 20} more")
    plural = "s" if len(terms) != 1 else ""
    return (f"no {row_word} matches all {len(terms)} term{plural}; "
            f"per-term {row_word} hits: {' '.join(shown)}")


def _content_term_hits(root, ordered, terms):
    """Per-term note counts for an empty content result, or None.

    Best-effort by design: the search itself already answered [], so a
    read racing the hint must never fail the command.
    """
    try:
        hits = [0] * len(terms)
        for note in ordered:
            text = _note_bytes(root, note).decode("utf-8")
            for index, term in enumerate(terms):
                if term.search(text):
                    hits[index] += 1
        return hits
    except (WriteRefused, OSError, UnicodeError):
        return None


def _note_bytes(root, note):
    return _bytes_inside_owner(
        root, note.path, root / "knowledge" / "notes",
        escape="note path escapes its knowledge owner",
        symlink="note read refuses symlinks")


def _note_collection(root):
    """Load only the note registry for note reads/search, not a complete Repo.

    The partial model stays inside these note-only paths. Full canonical
    fingerprints still guard the read before and after, including continuation.
    """
    repo = Repo(root=root)
    load_notes(repo, root)
    return repo


def _garden_notes(root):
    """(stable id, note) pairs for every garden seed.

    Loaded lazily on a durable-note miss, so the registered-note path —
    including its parse-only-notes budget — never pays for the garden.
    Identity is the same ``garden_id`` the manifest projects, so search
    rows and this read cannot disagree about what an id names.
    """
    repo = Repo(root=root)
    load_garden(repo, root)
    garden_root = root / "knowledge" / "garden"
    return [(garden_id(garden_root, note.path), note)
            for note in repo.garden_notes]


def _garden_note(root, note_id):
    """The garden seed with one stable id, or None."""
    for stable_id, note in _garden_notes(root):
        if stable_id == note_id:
            return note
    return None


def _content_envelope(contract, ref_key, ref, relpath, raw, content, offset, limit):
    return {
        "contract": contract, ref_key: ref, "path": relpath,
        "content_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "offset": offset, "offset_unit": "unicode_characters",
        "total_characters": len(content),
        "start_line": content.count("\n", 0, offset) + 1,
        "content": content[offset:offset + limit],
        "next_offset": offset + limit if offset + limit < len(content) else None,
    }


def cmd_note_read(args) -> int:
    root = _root(args)
    try:
        offset, limit = _window(args, 16000)
        with _operator_lock(root):
            snapshot = _snapshot(root, args.expected_snapshot)
            repo = _note_collection(root)
            note = repo.notes.get(args.note_id)
            if note is None:
                seeds = _garden_notes(root)
                garden = next((seed for stable_id, seed in seeds
                               if stable_id == args.note_id), None)
                if garden is None:
                    candidates = [*repo.notes, *[stable_id for stable_id, _ in seeds]]
                    raise WriteRefused(not_found("note", args.note_id, candidates))
                raw = _bytes_inside_owner(
                    root, garden.path, root / "knowledge" / "garden",
                    escape="garden path escapes its garden owner",
                    symlink="garden read refuses symlinks")
                content = raw.decode("utf-8")
                return _print_stable(root, snapshot, _content_envelope(
                    "note-content", "note_id", args.note_id,
                    garden.path.relative_to(root).as_posix(),
                    raw, content, offset, limit))
            raw = _note_bytes(root, note)
            content = raw.decode("utf-8")
            return _print_stable(root, snapshot, _content_envelope(
                "note-content", "note_id", note.id,
                note.path.relative_to(root).as_posix(),
                raw, content, offset, limit))
    except (WriteRefused, OSError, UnicodeError) as exc:
        return _refusal(exc)


def _inbox_folder_envelope(root: Path, name: str) -> dict:
    """A folder drop's file names and the digest inbox-resolve checks.

    Uses the resolve path's own admission, collection and digest, so the
    value a reader is handed is exactly the value the write recomputes.
    """
    from .inbox import _admit, _collect, _folder_digest

    inbox = root / "work" / "inbox"
    try:
        files = _collect(inbox, _admit(inbox, name))
    except ValueError as exc:
        raise WriteRefused(str(exc)) from exc
    return {
        "contract": "inbox-folder", "item": name,
        "path": (inbox / name).relative_to(root).as_posix(),
        "files": sorted(files),
        "drop_sha256": _folder_digest(files),
    }


def cmd_inbox_read(args) -> int:
    """Read a bounded segment of one work/inbox file by inbox-relative name.

    Inbox drops are addressed by name — they have no registry and no stable
    ids — and may be binary, so non-UTF-8 bytes refuse rather than decode.
    Discovery lists non-dot files (the same rule as the inbox count); an
    exact name reads whatever it addresses, dot-files included. A folder
    drop answers its file names plus ``drop_sha256``, the digest
    ``inbox-resolve`` seals for the whole folder; no other read exposes it.
    """
    root = _root(args)
    try:
        offset, limit = _window(args, 16000)
        name = args.name
        if Path(name).is_absolute() or ".." in Path(name).parts:
            raise WriteRefused(f"inbox name must be relative to work/inbox: {name}")
        with _operator_lock(root):
            snapshot = _snapshot(root, args.expected_snapshot)
            target = root / "work" / "inbox" / name
            if target.is_dir() and not target.is_symlink():
                return _print_stable(root, snapshot, _inbox_folder_envelope(root, name))
            if not target.is_symlink() and not target.is_file():
                raise WriteRefused(f"inbox item not found: {name}")
            raw = _bytes_inside_owner(
                root, target, root / "work" / "inbox",
                escape=f"inbox item escapes work/inbox: {name}",
                symlink="inbox read refuses symlinks")
            try:
                content = raw.decode("utf-8")
            except UnicodeError as exc:
                raise WriteRefused(
                    f"inbox item is not UTF-8 text and has no text read: {name}"
                ) from exc
            return _print_stable(root, snapshot, _content_envelope(
                "inbox-content", "item", name,
                target.relative_to(root).as_posix(),
                raw, content, offset, limit))
    except (WriteRefused, OSError, UnicodeError) as exc:
        return _refusal(exc)


def _match_verified(items, terms):
    """Run the current regex verification over admitted note bytes.

    ``items`` is (note id, title, repo-relative path, raw bytes). Pure:
    every read happened before this call, so the indexed path verifies
    from discovered bytes without re-reading.
    """
    matches = []
    for note_id, title, relpath, raw in items:
        text = raw.decode("utf-8")
        found = [term.search(text) for term in terms]
        if not all(found):
            continue
        positions = sorted({match.start() for match in found if match})
        snippets = []
        for position in positions[:8]:
            start = max(text.rfind("\n", 0, position) + 1, position - 100)
            end = text.find("\n", position)
            end = min(end if end >= 0 else len(text), position + 180)
            snippets.append({"line": text.count("\n", 0, position) + 1,
                             "text": text[start:end]})
        matches.append({"id": note_id, "type": "note", "title": title,
                        "path": relpath,
                        "content_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
                        "snippets": snippets})
    return matches


# MEASURED (S23 cold-search scaling, 2026-09-26): 145 notes 1.02s cold /
# 0.76s warm; 290 notes 1.07s / 0.84s; 725 notes 2.00s / 1.14s. Loader
# dominates (warm tracks cold); no index or rebuild work triggered.
def _exhaustive_content_search(root, ordered, terms):
    """The current implementation, kept as the differential oracle."""
    matches = []
    for note in ordered:
        raw = _note_bytes(root, note)
        matches.extend(_match_verified(
            [(note.id, note.meta.get("title", note.id),
              note.path.relative_to(root).as_posix(), raw)], terms))
    return matches


def _indexed_content_search(root, ordered, terms, raw_terms):
    """Indexed path: derived postings narrow candidates, regex verifies.

    Reads every note once with the same admitted reader (identical
    refusals), then verifies only candidates from those bytes. A query
    the prefilter cannot narrow (None) verifies every note instead.
    """
    blobs = {}
    for note in ordered:
        blobs[note.id] = NoteBlob(
            note_id=note.id,
            relpath=note.path.relative_to(root).as_posix(),
            title=note.meta.get("title", note.id),
            raw=_note_bytes(root, note))
    registry, inputs = build_registry(list(blobs.values()))
    postings = evaluate(root, POSTINGS_NODE_ID, registry=registry, inputs=inputs).value
    shortlist = candidates(root, postings, raw_terms)
    if shortlist is None:
        selected = ordered
    else:
        wanted = set(shortlist)
        selected = [note for note in ordered if note.id in wanted]
    matches = []
    for note in selected:
        blob = blobs[note.id]
        matches.extend(_match_verified(
            [(blob.note_id, blob.title, blob.relpath, blob.raw)], terms))
    return matches


def content_search(args) -> int:
    root = _root(args)
    try:
        offset, limit = _window(args, 100)
        if args.type not in (None, "note"):
            raise WriteRefused("--content currently supports durable notes; use --type note")
        raw_terms = args.query.split()
        terms = [re.compile(re.escape(term), re.IGNORECASE) for term in raw_terms]
        if not terms:
            raise WriteRefused("content search requires a nonempty query")
        with _operator_lock(root):
            snapshot = _snapshot(root, args.expected_snapshot)
            repo = _note_collection(root)
            # A read refuses when the failures bear on the answer it is about to
            # give, and this search is over notes: an unreadable note may be a
            # hit that never appears, while an unreadable project cannot be.
            # Refusal rather than a partial answer, because the bounded-read
            # envelope is a closed contract — a short answer here would have to
            # report itself as total.
            note_dir = root / "knowledge" / "notes"
            note_failures = [
                (path, message) for path, message in repo.parse_failures
                if path.is_relative_to(note_dir)
            ]
            if note_failures:
                raise WriteRefused(unreadable_refusal(root, note_failures, "search"))
            ordered = sorted(repo.notes.values(), key=lambda row: row.id)
            try:
                matches = _indexed_content_search(root, ordered, terms, raw_terms)
            except DerivedError:
                # The index is a pure accelerator: any cache failure
                # (tampering already self-healed before raising) falls
                # back to the exhaustive implementation, never to a
                # partial answer. Bytes/symlink refusals are not
                # DerivedError and still propagate unchanged.
                matches = _exhaustive_content_search(root, ordered, terms)
            if not matches:
                hint_hits = _content_term_hits(root, ordered, terms)
                if hint_hits is not None:
                    print(f"los: {empty_search_hint('note', raw_terms, hint_hits)}",
                          file=sys.stderr)
            return _print_stable(root, snapshot, {
                "contract": "note-content-search", "items": matches[offset:offset + limit],
                "total": len(matches),
                "next_offset": offset + limit if offset + limit < len(matches) else None,
            })
    except (WriteRefused, OSError, UnicodeError) as exc:
        return _refusal(exc)


# ------------------------------------------------------- material context
ASSESSMENT_TEXT_FIELDS = ("contribution", "assumptions", "notation",
                          "exercise_value", "best_for", "limitations",
                          "locator")

# The declared source-feedback vocabulary, grouped for ranking. Positive
# values say the source served; mismatch values say it did not fit this
# use. "skipped" is recorded evidence about the stage, not about the
# source, so it is reported and never ranks.
POSITIVE_FEEDBACK = frozenset({"helpful", "useful-for-derivation",
                               "useful-for-review"})
MISMATCH_FEEDBACK = frozenset({"too-advanced", "wrong-perspective"})


def _use_evidence(repo):
    """Recorded stage-use evidence per source id: raw feedback counts.

    Canonical study-map data, so the read's snapshot guard already binds
    it — no observation entry is owed. Counts only; grouping into
    positive/mismatch happens at rank time from the sets above, so a new
    vocabulary value degrades to reported-but-unranked, never to a crash
    or a silent demotion.
    """
    tallies: dict[str, dict[str, int]] = {}
    for study_map in repo.study_maps.values():
        stages = study_map.data.get("stages", []) or []
        for stage in stages:
            if not isinstance(stage, dict):
                continue
            for entry in stage.get("source_feedback", []) or []:
                if not isinstance(entry, dict):
                    continue
                source_id = entry.get("source_id")
                if not source_id:
                    continue
                tally = tallies.setdefault(source_id, {})
                value = entry.get("feedback")
                if not value:
                    continue
                tally[value] = tally.get(value, 0) + 1
    return tallies


def _evidence_label(tally):
    positive = sum(count for value, count in tally.items()
                   if value in POSITIVE_FEEDBACK)
    mismatch = sum(count for value, count in tally.items()
                   if value in MISMATCH_FEEDBACK)
    return {"counts": dict(sorted(tally.items())),
            "positive": positive, "mismatch": mismatch}


def _use_evidence_from_manifest(manifest: dict) -> dict[str, dict[str, int]]:
    """Recorded stage-use evidence per source id, read from the manifest.

    The same tally `_use_evidence` computes from the loaded repo: every
    study map is projected and projected stages keep `source_feedback`
    verbatim, so the two agree exactly. Lets `related` skip the repo load
    on the manifest-reuse fast path (#83).
    """
    tallies: dict[str, dict[str, int]] = {}
    for study_map in manifest.get("study_maps", []) or []:
        if not isinstance(study_map, dict):
            continue
        for stage in study_map.get("stages", []) or []:
            if not isinstance(stage, dict):
                continue
            for entry in stage.get("source_feedback", []) or []:
                if not isinstance(entry, dict):
                    continue
                source_id = entry.get("source_id")
                if not source_id:
                    continue
                tally = tallies.setdefault(source_id, {})
                value = entry.get("feedback")
                if not value:
                    continue
                tally[value] = tally.get(value, 0) + 1
    return tallies


#: Declared-edge fields walked from the record itself, in stable order.
RELATED_LIST_FIELDS = ("concepts", "sources", "contexts", "notes",
                       "program_ids", "module_ids", "unit_ids", "unit_order",
                       "related_module_ids")
RELATED_SCALAR_FIELDS = ("workspace_id", "area_id", "module_id", "unit_id",
                         "current_study_map")

#: Backlink tables walked in both directions. Every table maps an owner to
#: its members; the walk answers the direct lookup and the inverse scan, so
#: membership in one direction always implies the reverse edge (JF-15). The
#: differently-shaped concept_relations table stays out: concept relations
#: are already walked both ways from the manifest relations list.
RELATED_BACKLINK_TABLES = ("concept_to_notes", "source_to_notes",
                           "workspace_to_notes", "module_to_workspaces",
                           "unit_to_workspaces", "module_to_units",
                           "source_to_units", "note_incoming")

#: The read-time label for a note→source analysis edge (#81). The edge says
#: "this note analyses pages of that source", not "this note cites it".
ANALYSES_VIA = "analyses"


def _analysis_source_of(record) -> str | None:
    """The registered source a record's resolved analysis binds, or None."""
    binding = record.get("material_analysis") if isinstance(record, dict) else None
    if not isinstance(binding, dict) or binding.get("resolution") != "resolved":
        return None
    source_id = binding.get("source_id")
    return source_id if isinstance(source_id, str) else None


def related_records(manifest: dict, raw_id: str, repo=None, *, tallies=None) -> list[dict]:
    """Ranked one-hop connections for one record id.

    Pure over the manifest (plus recorded use-evidence tallied from the
    repo when given, or the precomputed `tallies` when the caller read
    them from the manifest instead): the record's own declared edges,
    every backlink table in both directions, concept relations both ways,
    and project relationships both ways. Unknown ids answer [] — the
    caller owns the not-found error. Aliases resolve through project_aliases.

    Ranking is deterministic: more distinct edges first, then recorded
    stage use-evidence per source exactly as material-context ranks it
    (positive counts first, mismatch counts last), then stable id order.
    Each result names the edges that produced it in `via`. A source↔note
    edge through `source_to_notes` gains the additional `analyses` token
    when the note's resolved material analysis binds that source (#81).
    """
    by_id = {r.get("id"): r for r in manifest.get("records", [])}
    resolved = (manifest.get("project_aliases") or {}).get(raw_id, raw_id)
    rec = by_id.get(resolved)
    if rec is None:
        return []
    reasons: dict[str, set[str]] = {}

    def link(rid, why):
        if isinstance(rid, str) and rid in by_id:
            reasons.setdefault(rid, set()).add(why)

    for key in RELATED_LIST_FIELDS:
        for rid in rec.get(key, []) or []:
            link(rid, key)
    for key in RELATED_SCALAR_FIELDS:
        if rec.get(key):
            link(rec[key], key)
    backlinks = manifest.get("backlinks", {}) or {}
    for table in RELATED_BACKLINK_TABLES:
        members = (backlinks.get(table) or {}).get(resolved, []) or []
        for rid in members:
            link(rid, f"backlink:{table}")
            if table == "source_to_notes" \
                    and _analysis_source_of(by_id.get(rid)) == resolved:
                link(rid, ANALYSES_VIA)
        for owner, owned in ((backlinks.get(table) or {}).items()):
            if isinstance(owned, list) and resolved in owned:
                link(owner, f"inverse:{table}")
                if table == "source_to_notes" \
                        and _analysis_source_of(by_id.get(resolved)) == owner:
                    link(owner, ANALYSES_VIA)
    for relation in manifest.get("relations", []) or []:
        if not isinstance(relation, dict):
            continue
        if relation.get("from") == resolved:
            link(relation.get("to"), "relation")
        if relation.get("to") == resolved:
            link(relation.get("from"), "relation")
    for relation in manifest.get("project_relationships", []) or []:
        if not isinstance(relation, dict):
            continue
        if relation.get("from_project_id") == resolved:
            link(relation.get("to_id"), "project_relationship")
        if relation.get("to_id") == resolved:
            link(relation.get("from_project_id"), "project_relationship")
    if repo is not None:
        tallies = _use_evidence(repo)
    elif tallies is None:
        tallies = {}
    ranked = []
    for rid, whys in reasons.items():
        tally = tallies.get(rid, {}) if by_id[rid].get("type") == "source" else {}
        label = _evidence_label(tally)
        ranked.append((-len(whys), -label["positive"], label["mismatch"], rid))
    ranked.sort()
    return [{"id": rid, "type": by_id[rid].get("type"),
             "title": by_id[rid].get("title"), "path": by_id[rid].get("path"),
             "via": sorted(reasons[rid])}
            for _, _, _, rid in ranked]


def _resolve_concept(repo, raw):
    """A concept id or declared alias, matched case-insensitively."""
    if raw in repo.concepts:
        return raw
    lowered = raw.casefold()
    hits = [cid for cid, concept in repo.concepts.items()
            if isinstance(concept, dict)
            and any(str(alias).casefold() == lowered
                    for alias in (concept.get("aliases") or []))]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise WriteRefused(f"unknown concept: {raw!r} matches no id or declared alias")
    raise WriteRefused(f"concept {raw!r} is ambiguous across {len(hits)} concepts; use an id")


def _analysis_notes(repo):
    return sorted((note for note in repo.notes.values()
                   if isinstance(note.meta.get("material_analysis"), dict)),
                  key=lambda note: note.id)


def _approved_assessments(repo):
    found = []
    for synthesis_id in sorted(repo.unit_material_syntheses):
        data = repo.unit_material_syntheses[synthesis_id]
        if not isinstance(data, dict) or data.get("status") != "approved":
            continue
        unit_id = data.get("unit_id")
        assessments = data.get("route_assessments")
        if not isinstance(assessments, list):
            continue
        for assessment in assessments:
            if isinstance(assessment, dict):
                found.append((synthesis_id, unit_id, assessment))
    found.sort(key=lambda row: (row[1] or "", row[2].get("route_id") or ""))
    return found


def _materials_rel_for_uri(repo, uri) -> str | None:
    """The materials-relative file a ``material://`` URI names, or None.

    Identity only: the file need not exist. Anything resolving outside
    the materials tree — or to a directory rather than a material file —
    is not a material path at all, so folder-level URIs prove no file.
    """
    if not isinstance(uri, str) or not uri:
        return None
    path = material_location(repo, uri).get("material_path")
    if not isinstance(path, str) or not path.startswith("materials/"):
        return None
    rel = path[len("materials/"):]
    if PurePosixPath(rel).suffix.lower() not in MATERIAL_RESOURCE_SUFFIXES:
        return None
    return rel


def _route_material_files(repo, source_id, route) -> set[str]:
    """Every materials-relative file one route reads, or empty when unproven.

    A route's own ``vault_path`` wins as a single file; otherwise a
    semicolon-separated locator naming two or more files resolves to the
    set it names — the same deliberate two-file binding the dossier basis
    resolves for freshness; otherwise the locator's leading file resolves
    against the route's source; otherwise the route inherits the source
    record's held material. The multi-file branch is strict: every part
    must name exactly one safe distinct file, otherwise the route proves
    no file at all rather than guessing one. String routes, prose-only
    locators, and material-less sources prove no file.
    """
    if not isinstance(route, dict):
        route = {}
    vault = _materials_rel_for_uri(repo, route.get("vault_path"))
    if vault is not None:
        return {vault}
    record = repo.sources.get(source_id) if isinstance(source_id, str) else None
    held = record.get("material") if isinstance(record, dict) else None
    authority = material_uri_authority(held)
    if authority is None and isinstance(source_id, str) and source_id:
        # Legacy routes can name an exact source-id-prefixed file without
        # a source-level material field. A declared shared authority wins.
        authority = source_id
    locator = route.get("locator")
    if (isinstance(locator, str) and ";" in locator
            and len(MATERIAL_SUFFIX_TOKEN.findall(locator)) >= 2):
        if authority is None:
            return set()
        candidates: list[str] = []
        for part in locator.split(";"):
            matches = list(MATERIAL_SUFFIX_TOKEN.finditer(part))
            if len(matches) != 1:
                return set()
            candidate = safe_material_locator(part[:matches[0].end()].strip())
            if candidate is None:
                return set()
            candidates.append(candidate)
        if len(candidates) < 2 or len(candidates) != len(set(candidates)):
            return set()
        resolved: set[str] = set()
        for candidate in candidates:
            found = _materials_rel_for_uri(
                repo, f"{MATERIAL_SCHEME}{authority}/{candidate}")
            if found is None:
                return set()
            resolved.add(found)
        return resolved
    head = None
    if isinstance(locator, str):
        # Strict first, then the weaker head-of-prose question — the same
        # order the material projection resolves a row.
        head = safe_material_locator(locator) or leading_material_locator(locator)
    if head and authority:
        found = _materials_rel_for_uri(
            repo, f"{MATERIAL_SCHEME}{authority}/{head}")
        if found is not None:
            return {found}
    inherited = _materials_rel_for_uri(repo, held)
    return {inherited} if inherited is not None else set()


def _route_material_file(repo, source_id, route) -> str | None:
    """The materials-relative file one route reads, or None when unprovable.

    Single-file view of `_route_material_files`: exactly one proven file
    returns it, zero or several prove no single file.
    """
    files = _route_material_files(repo, source_id, route)
    return next(iter(files)) if len(files) == 1 else None


def _single_route_range(route) -> tuple[int, int] | None:
    """The one usable page range a route states, or None.

    Zero ranges (a whole-file route) and several ranges (a curated tour)
    both decline the page test: only a single stated range narrows what a
    note about the file must overlap to count as direct evidence.
    """
    locator = route.get("locator") if isinstance(route, dict) else None
    ranges = parse_locator_page_ranges(locator) if isinstance(locator, str) else []
    return ranges[0] if len(ranges) == 1 else None


def _note_pages(binding) -> tuple[int, int] | None:
    """A note's inspected physical page window, or None when unstated."""
    inspected = binding.get("inspected_range") if isinstance(binding, dict) else None
    if not isinstance(inspected, dict):
        return None
    start, end = inspected.get("start"), inspected.get("end")
    if (isinstance(start, bool) or isinstance(end, bool)
            or not isinstance(start, int) or not isinstance(end, int)):
        return None
    return (start, end) if start <= end else None


def _unit_note_scope(repo, binding, routes) -> str | None:
    """"direct", "related", or None: one note's standing against unit routes.

    THE shared note-to-route rule: material-context and the plan brief
    both answer from here. Material identity comes from existing
    resolution, never from a shared source id alone, and a route stating
    a single usable page range additionally requires physical overlap with
    the note's inspected window. Same-source-only notes are related, never
    direct; notes touching neither the source nor the file are out.
    ``routes`` is (source_id, route-dict) pairs; string routes arrive as
    (source_id, {}) and prove identity only through inheritance.
    """
    if not isinstance(binding, dict):
        return None
    note_sid = binding.get("source_id")
    note_ref = binding.get("material")
    pages = _note_pages(binding)
    standing = None
    for source_id, route in routes:
        same_source = (isinstance(note_sid, str) and note_sid
                       and note_sid == source_id)
        route_files = _route_material_files(repo, source_id, route)
        same_file = (isinstance(note_ref, str) and note_ref
                     and note_ref in route_files)
        if not same_source and not same_file:
            continue
        if same_source and same_file:
            window = _single_route_range(route) if len(route_files) == 1 else None
            if window is None or (
                    pages is not None
                    and window[0] <= pages[1] and pages[0] <= window[1]):
                return "direct"
        standing = "related"
    return standing


def _unit_route_pairs(repo, unit_id) -> list:
    """(source_id, route-dict) pairs routed to one unit.

    The same membership the scope check always used — a bare unit id or
    an expanded route carrying it — with string routes arriving as empty
    dicts so the shared rule, not the caller, decides what they prove.
    """
    unit = repo.units[unit_id]
    source_map = repo.module_source_maps.get(unit.module_id) or {}
    pairs = []
    for source in source_map.get("sources", []) or []:
        if not isinstance(source, dict) or not source.get("source_id"):
            continue
        for route in source.get("unit_routes", []) or []:
            if route == unit.id:
                pairs.append((source["source_id"], {}))
            elif isinstance(route, dict) and route.get("unit_id") == unit.id:
                pairs.append((source["source_id"], route))
    return pairs


def _route_material_index(repo, unit_id=None) -> dict:
    """route_id -> (source_id, route-dict), for one unit or every module."""
    if unit_id is not None:
        return {route.get("id"): pair for pair in _unit_route_pairs(repo, unit_id)
                for route in [pair[1]] if route.get("id")}
    index = {}
    for source_map in (repo.module_source_maps or {}).values():
        if not isinstance(source_map, dict):
            continue
        for source in source_map.get("sources", []) or []:
            if not isinstance(source, dict) or not source.get("source_id"):
                continue
            for route in source.get("unit_routes", []) or []:
                if isinstance(route, dict) and route.get("id"):
                    index.setdefault(route["id"], (source["source_id"], route))
    return index


def _check_material_ref(root, ref) -> str:
    """The exact materials-tree path a --material filter names, else refused.

    Exact: no canonicalization, so a near-miss matches nothing rather than
    something nearby. The boundary is still enforced — an escape refuses
    instead of reading outside the tree.
    """
    materials = root.parent / "materials"
    pure = PurePosixPath(ref) if isinstance(ref, str) else None
    if (pure is None or not ref or pure.is_absolute()
            or "\\" in ref
            or any(part in {".", ".."} for part in pure.parts)):
        raise WriteRefused(f"--material must be a materials-tree-relative path: {ref!r}")
    try:
        (materials / ref).resolve(strict=False).relative_to(materials.resolve())
    except (OSError, ValueError) as exc:
        raise WriteRefused(
            f"--material must be a materials-tree-relative path: {ref!r}") from exc
    return ref


def _explanation_snippets(title, text, body_offset, terms) -> list:
    """Title label plus true-file-line body windows for matched terms.

    A title hit yields one title snippet; body hits reuse the content
    search's windowing over the full text, so the reported lines are true
    file lines even though matching never sees the frontmatter. At most
    eight snippets either way, the title counting as one.
    """
    snippets = []
    if any(regex.search(title) for regex in terms):
        snippets.append({"label": "title", "text": title})
    body = text[body_offset:]
    positions = sorted({match.start() for regex in terms
                        if (match := regex.search(body)) is not None})
    for position in positions[:8 - len(snippets)]:
        absolute = body_offset + position
        start = max(text.rfind("\n", 0, absolute) + 1, absolute - 100)
        end = text.find("\n", absolute)
        end = min(end if end >= 0 else len(text), absolute + 180)
        snippets.append({"line": text.count("\n", 0, absolute) + 1,
                         "text": text[start:end]})
    return snippets


def _freshness_label(root, binding, observations=None):
    """Live source freshness: current, stale, or unreadable. Never inferred.

    When `observations` is given, the observed bytes (or their absence)
    are recorded under the material relpath so a paged continuation can
    prove the external state it pages over did not move between pages.
    """
    material = str(binding.get("material") or "")
    observation = observe_local_material(
        root.parent / "materials", material,
        str(binding.get("recorded_source_digest") or ""))
    if observations is not None:
        live = observation.get("live_digest")
        observations[f"material:{material}"] = \
            live if live is not None else observation["status"]
    status = observation["status"]
    if status in ("current", "stale"):
        return status
    return "unreadable"


def _observations_digest(observations: dict) -> str:
    encoded = json.dumps(
        {key: observations[key] for key in sorted(observations)},
        ensure_ascii=False, sort_keys=True,
        separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _note_purpose_hit(binding, purpose):
    if purpose is None:
        return True
    wanted = purpose.casefold()
    anchors = binding.get("anchors")
    if not isinstance(anchors, list):
        return False
    return any(wanted in str(anchor.get("purpose", "")).casefold()
               for anchor in anchors if isinstance(anchor, dict))


def _assessment_purpose_hit(assessment, purpose):
    if purpose is None:
        return True
    wanted = purpose.casefold()
    return any(wanted in str(assessment.get(field) or "").casefold()
               for field in ("best_for", "exercise_value"))


_ANCHOR_PREVIEW_LIMIT = 8
_ANCHOR_TEXT_LIMIT = 200


def _anchor_purpose_hit(anchor, wanted) -> bool:
    return (isinstance(anchor, dict)
            and wanted in str(anchor.get("purpose", "")).casefold())


def _anchor_selection(anchors, purpose):
    """Original-order anchors with literal purpose matches first, deduplicated.

    Returns (ordered, match_count): match_count is None without a purpose
    filter. Both groups keep file order; no anchor appears twice.
    """
    if not purpose:
        return list(anchors), None
    wanted = purpose.casefold()
    matches = [anchor for anchor in anchors
               if _anchor_purpose_hit(anchor, wanted)]
    seen = {id(anchor) for anchor in matches}
    return (matches + [anchor for anchor in anchors
                       if id(anchor) not in seen], len(matches))


def _clip_anchor_text(anchor):
    """The anchor with every long text field bounded, naming what clipped."""
    if not isinstance(anchor, dict):
        return anchor
    clipped = []
    shaped = {}
    for key, value in anchor.items():
        if isinstance(value, str) and len(value) > _ANCHOR_TEXT_LIMIT:
            shaped[key] = value[:_ANCHOR_TEXT_LIMIT]
            clipped.append(key)
        else:
            shaped[key] = value
    shaped["clipped_fields"] = clipped
    return shaped


def _anchor_expansion_command(args, limit, snapshot, observed) -> str:
    """Re-run this read's selected page with complete anchor indexes."""
    parts = ["material-context", args.query or ""]
    if args.concept:
        parts += ["--concept", args.concept]
    if args.purpose:
        parts += ["--purpose", args.purpose]
    if args.unit:
        parts += ["--unit", args.unit]
    if getattr(args, "material", None):
        parts += ["--material", args.material]
    if getattr(args, "include_related", False):
        parts += ["--include-related"]
    parts += ["--include-anchors", "--limit", str(limit),
              "--offset", str(args.offset),
              "--expected-snapshot", snapshot,
              "--expected-observations", observed]
    return expansion(*parts)


def _analysis_note_item(root, note, *, raw_terms, terms, concept_id, purpose,
                        unit, material_ref, scope, evidence, observations,
                        include_anchors=False):
    """One matched analysis note, or None when the terms miss.

    Terms match the explanation text — title plus body — with lexical AND;
    frontmatter (provenance paths, digests, ids) never matches. Title hits
    yield a title snippet; body hits yield true file line numbers. The
    scope label exists only under --unit, where direct and related mean
    something. Anchors preview bounded (purpose matches first) with exact
    totals; the complete index needs the explicit expansion.
    """
    raw = _note_bytes(root, note)
    text = raw.decode("utf-8")
    title = note.meta.get("title", note.id)
    front = FRONTMATTER_RE.match(text)
    body_offset = front.end() if front else 0
    body = text[body_offset:]
    matched = [raw_term for raw_term, regex in zip(raw_terms, terms, strict=True)
               if regex.search(title) or regex.search(body)]
    if len(matched) != len(raw_terms):
        return None
    binding = note.meta["material_analysis"]
    inspected = binding.get("inspected_range") or {}
    reasons = {"terms": matched}
    if concept_id is not None:
        reasons["concept"] = concept_id
    if purpose:
        reasons["purpose"] = purpose
    if unit:
        reasons["unit"] = unit
    if material_ref is not None:
        reasons["material"] = material_ref
    item = {
        "origin": "analysis-note",
        "id": note.id, "title": title,
        "path": note.path.relative_to(root).as_posix(),
        "use_evidence": _evidence_label(
            evidence.get(binding.get("source_id")) or {}),
        "match": {**reasons, "snippets": _explanation_snippets(
            title, text, body_offset, terms)},
        "source": {
            "ref": binding.get("material"),
            "pages": [inspected.get("start"), inspected.get("end")],
            "freshness": _freshness_label(root, binding, observations),
        },
        "review": {
            "semantic_review": note.meta.get("semantic_review"),
            "resolution": binding.get("resolution"),
        },
    }
    anchors = binding.get("anchors") or []
    ordered, match_count = _anchor_selection(anchors, purpose)
    if include_anchors:
        item["anchors"] = list(anchors)
        item["anchor_returned"] = len(anchors)
        item["anchors_truncated"] = False
    else:
        item["anchors"] = [_clip_anchor_text(anchor)
                           for anchor in ordered[:_ANCHOR_PREVIEW_LIMIT]]
        item["anchor_returned"] = len(item["anchors"])
        item["anchors_truncated"] = len(anchors) > _ANCHOR_PREVIEW_LIMIT
    item["anchor_total"] = len(anchors)
    if purpose:
        item["purpose_match_count"] = match_count
        item["purpose_other_count"] = len(anchors) - match_count
    if scope is not None:
        item["scope"] = scope
    return item


def cmd_material_context(args) -> int:
    """Find saved explanations from an explanation need.

    Corpus: durable analysis notes plus the route assessments of approved
    unit syntheses. Matching is deterministic lexical AND over terms against
    explanation text — note title plus body, never provenance frontmatter —
    with declared concept aliases, purpose substrings, unit scope, and an
    exact materials path as filters. Unit scope is route-based: direct notes
    share a routed file (and overlap its single stated page range when it
    states one); same-source-only notes are related, listed only through
    --include-related. Ranking is recorded stage use-evidence per source
    (positive feedback first, mismatch feedback last); ties keep stable
    order (notes by id, then assessments by unit and route), which is the
    whole answer until feedback exists.
    Freshness is observed live per result: notes carry source freshness,
    assessments carry their dossier's current freshness next to the stored
    review status. Review state and resolution are reported, never
    inferred. Every response binds the external observations and the
    normalized filters it used (`observations_sha256`); a continuation
    re-verifies them, so pages never describe different source states — or
    different filters — under one identity. An empty
    result describes the searched records only — never proof that no
    source explains the topic.
    """
    root = _root(args)
    try:
        offset, limit = _window(args, 20)
        if offset and not getattr(args, "expected_observations", None):
            raise WriteRefused(
                "continuation requires --expected-observations from the "
                "previous response")
        raw_terms = (args.query or "").split()
        terms = [re.compile(re.escape(term), re.IGNORECASE) for term in raw_terms]
        material_ref = getattr(args, "material", None)
        if not terms and material_ref is None:
            raise WriteRefused(
                "material context requires a nonempty query or --material")
        if getattr(args, "include_related", False) and not args.unit:
            raise WriteRefused("--include-related needs --unit")
        if material_ref is not None:
            _check_material_ref(root, material_ref)
        with _operator_lock(root):
            snapshot = _snapshot(root, args.expected_snapshot)
            repo = load_repo(root)
            note_dir = root / "knowledge" / "notes"
            note_failures = [
                (path, message) for path, message in repo.parse_failures
                if path.is_relative_to(note_dir)
            ]
            if note_failures:
                raise WriteRefused(unreadable_refusal(root, note_failures, "context"))
            synthesis_failures = [
                (path, message) for path, message in repo.parse_failures
                if path.name == "material-synthesis.yaml"
            ]
            if synthesis_failures:
                raise WriteRefused(unreadable_refusal(root, synthesis_failures, "context"))
            concept_id = _resolve_concept(repo, args.concept) \
                if args.concept else None
            if args.unit and args.unit not in repo.units:
                raise WriteRefused(with_suggestions(
                    f"unknown unit: {args.unit!r}", args.unit, repo.units))
            assessments = _approved_assessments(repo)
            related_count = 0
            searched_related: list = []
            if args.unit:
                assessments = [row for row in assessments if row[1] == args.unit]
                pairs = _unit_route_pairs(repo, args.unit)
                direct_pool = []
                related_pool = []
                for note in _analysis_notes(repo):
                    standing = _unit_note_scope(
                        repo, note.meta.get("material_analysis") or {}, pairs)
                    if standing == "direct":
                        direct_pool.append(note)
                    elif standing == "related":
                        related_pool.append(note)
                notes = direct_pool
                related_count = len(related_pool)
                if args.include_related:
                    searched_related = related_pool
            else:
                notes = _analysis_notes(repo)
            if concept_id is not None:
                notes = [note for note in notes
                         if concept_id in (note.meta.get("concepts") or [])]
                searched_related = [
                    note for note in searched_related
                    if concept_id in (note.meta.get("concepts") or [])]
                assessments = [row for row in assessments
                               if concept_id in (row[2].get("concept_ids") or [])]
            notes = [note for note in notes
                     if _note_purpose_hit(note.meta["material_analysis"], args.purpose)]
            searched_related = [
                note for note in searched_related
                if _note_purpose_hit(note.meta["material_analysis"], args.purpose)]
            assessments = [row for row in assessments
                           if _assessment_purpose_hit(row[2], args.purpose)]
            if material_ref is not None:
                notes = [note for note in notes
                         if (note.meta.get("material_analysis") or {}).get("material")
                         == material_ref]
                searched_related = [
                    note for note in searched_related
                    if (note.meta.get("material_analysis") or {}).get("material")
                    == material_ref]
                route_index = _route_material_index(repo, args.unit)
                assessments = [
                    row for row in assessments
                    if material_ref in _route_material_files(
                        repo, *route_index.get(row[2].get("route_id"), (None, {})))]
            # Use evidence is deliberately global: feedback says a source
            # served in some stage, which bears on every result bound to
            # that source, however the query scoped the pool.
            evidence = _use_evidence(repo)
            pool = {
                "analysis_notes": len(notes),
                "assessments": len(assessments),
                # Related notes are counted, never pooled: the resolution
                # tallies below describe the default-visible direct set.
                "related_analysis_notes": related_count,
                "analysis_by_resolution": {},
                "analysis_unreviewed": 0,
            }
            for note in notes:
                binding = note.meta["material_analysis"]
                resolution = binding.get("resolution")
                pool["analysis_by_resolution"][resolution] = \
                    pool["analysis_by_resolution"].get(resolution, 0) + 1
                if note.meta.get("semantic_review") == "unreviewed":
                    pool["analysis_unreviewed"] += 1
            items = []
            observations: dict[str, str] = {}
            dossier_freshness: dict[str, dict] = {}
            include_anchors = bool(getattr(args, "include_anchors", False))
            for note in notes:
                item = _analysis_note_item(
                    root, note, raw_terms=raw_terms, terms=terms,
                    concept_id=concept_id, purpose=args.purpose,
                    unit=args.unit, material_ref=material_ref,
                    scope="direct" if args.unit else None,
                    evidence=evidence, observations=observations,
                    include_anchors=include_anchors)
                if item is not None:
                    items.append(item)
            for synthesis_id, unit_id, assessment in assessments:
                joined = "\n".join(str(assessment.get(field) or "")
                                   for field in ASSESSMENT_TEXT_FIELDS)
                matched = [raw_term for raw_term, regex in zip(raw_terms, terms, strict=True)
                           if regex.search(joined)]
                if len(matched) != len(raw_terms):
                    continue
                excerpts = []
                for field in ASSESSMENT_TEXT_FIELDS:
                    if len(excerpts) >= 3:
                        break
                    value = str(assessment.get(field) or "")
                    if value and any(regex.search(value) for regex in terms):
                        excerpts.append({"field": field, "text": value[:200]})
                reasons = {"terms": matched}
                if concept_id is not None:
                    reasons["concept"] = concept_id
                if args.purpose:
                    reasons["purpose"] = args.purpose
                if args.unit:
                    reasons["unit"] = args.unit
                if material_ref is not None:
                    reasons["material"] = material_ref
                origin = repo.unit_material_synthesis_origins.get(synthesis_id)
                fresh = dossier_freshness.get(synthesis_id)
                if fresh is None:
                    dossier = repo.unit_material_syntheses.get(synthesis_id)
                    material_hashes = {}
                    fresh = material_synthesis_freshness(
                        root, unit_id, dossier
                        if isinstance(dossier, dict) else {}, repo=repo,
                        cache=material_hashes)
                    dossier_freshness[synthesis_id] = fresh
                    observations[f"dossier:{synthesis_id}"] = (
                        f"{fresh['status']}:{','.join(fresh['reasons'])}")
                    # Bind the bytes actually read by the shared freshness
                    # calculation: two different sources can both be stale
                    # for the same reason. Missing files remove an entry;
                    # newly available files add one on the next read.
                    observations.update({
                        f"dossier-material:{path}": digest
                        for path, digest in material_hashes.items()
                    })
                items.append({
                    "origin": "unit-assessment",
                    "unit_id": unit_id, "synthesis_id": synthesis_id,
                    "use_evidence": _evidence_label(
                        evidence.get(assessment.get("source_id")) or {}),
                    "route_id": assessment.get("route_id"),
                    "source_id": assessment.get("source_id"),
                    "locator": assessment.get("locator"),
                    "review_status": assessment.get("review_status"),
                    "freshness": fresh,
                    "concept_ids": assessment.get("concept_ids") or [],
                    "match": {**reasons, "excerpts": excerpts},
                    "open": {
                        "synthesis": origin.relative_to(root).as_posix()
                        if origin is not None else None,
                        "route_id": assessment.get("route_id"),
                    },
                })
            related_items = []
            for note in searched_related:
                item = _analysis_note_item(
                    root, note, raw_terms=raw_terms, terms=terms,
                    concept_id=concept_id, purpose=args.purpose,
                    unit=args.unit, material_ref=material_ref,
                    scope="related",
                    evidence=evidence, observations=observations,
                    include_anchors=include_anchors)
                if item is not None:
                    related_items.append(item)
            # Stable sort: evidence ranks, ties keep insertion order
            # (notes by id, then assessments by unit and route). Without
            # recorded feedback every key is (0, 0) and the order is
            # exactly the pre-ranking stable order. Related notes rank
            # under the same key but append after every direct item.
            items.sort(key=lambda row: (-row["use_evidence"]["positive"],
                                        row["use_evidence"]["mismatch"]))
            related_items.sort(key=lambda row: (
                -row["use_evidence"]["positive"],
                row["use_evidence"]["mismatch"]))
            items.extend(related_items)
            # The continuation binds the normalized filters alongside the
            # observed bytes: equivalent filters (reordered terms, a
            # concept alias for its id) page on, changed ones refuse.
            observations["filter/query"] = " ".join(
                sorted(term.casefold() for term in raw_terms))
            observations["filter/unit"] = args.unit or ""
            observations["filter/concept"] = concept_id or ""
            observations["filter/purpose"] = (args.purpose or "").casefold()
            observations["filter/material"] = material_ref or ""
            observations["filter/related"] = \
                "related" if args.include_related else "direct"
            observed = _observations_digest(observations)
            expected_observations = getattr(args, "expected_observations", None)
            if expected_observations is not None and expected_observations != observed:
                raise StaleSnapshot(
                    "material or filters observed by this query changed "
                    "between pages; re-run from offset 0")
            ranked_by = ("recorded stage use-evidence per source: positive "
                         "feedback first, mismatch feedback last; ties keep "
                         "stable order (notes by id, then assessments by "
                         "unit and route)")
            if args.include_related:
                ranked_by += ("; --include-related appends related notes "
                              "under the same ranking")
            returned = items[offset:offset + limit]
            payload = {
                "contract": "material-context",
                "ranked_by": ranked_by,
                "items": returned,
                "total": len(items),
                "next_offset": offset + limit if offset + limit < len(items) else None,
                "observations_sha256": observed,
                "searched": {
                    "query_terms": raw_terms, "concept": concept_id,
                    "purpose": args.purpose, "unit": args.unit,
                    "material": material_ref,
                    "include_related": bool(args.include_related),
                    "analysis_notes": len(_analysis_notes(repo)),
                    "assessments": len(_approved_assessments(repo)),
                },
                "pool": pool,
            }
            if not items:
                payload["empty"] = (
                    "no match in the searched records; this never proves "
                    "no source explains the topic")
            if not include_anchors and any(
                    item.get("origin") == "analysis-note"
                    and (item.get("anchors_truncated")
                         or any(row.get("clipped_fields")
                                for row in item.get("anchors", [])
                                if isinstance(row, dict)))
                    for item in returned):
                payload["expand"] = {"anchors": _anchor_expansion_command(
                    args, limit, snapshot, observed)}
            return _print_stable(root, snapshot, payload)
    except (WriteRefused, OSError, UnicodeError) as exc:
        return _refusal(exc)

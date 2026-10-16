"""Downward-owned command plumbing with a single owner (S13 candidate).

The operator lock, gateway refusal cellar, publish helpers and small
leaves, moved verbatim from commands.support so the ops pipeline can
import them downward. The session-ledger readers moved on to
`store/session_ledger.py` (S29); the operator-lock path still resolves
its state directory through that module's helpers.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath

import jsonschema
import yaml

from learning_os import observations
from learning_os.contracts.gateway import (
    current_gateway_request,
    intent_sha256,
)
from learning_os.domain.failures import WriteRefused
from learning_os.loading.yamlio import UniqueKeySafeLoader
from learning_os.material_analysis import observe_local_material
from learning_os.material_slices import parse_locator_page_ranges
from learning_os.materials_resolution import (
    MATERIAL_RESOURCE_SUFFIXES,
    MATERIAL_SCHEME,
    MATERIAL_SUFFIX_TOKEN,
    leading_material_locator,
    material_location,
    material_uri_authority,
    safe_material_locator,
)
from learning_os.store.codec import _dump_yaml
from learning_os.transactions import artifact_revision

# ---------------------------------------------------------------------------
# Fresh-manifest reads, moved verbatim from commands.support for the S15 pilot
# conversions (SPEC (az) item 2: the shared fresh-manifest closure moves below
# its callers instead of taking a new upward A1 import).










# ---------------------------------------------------------------------------
# Read preflight, moved verbatim from commands.reads (SPEC (az) item 2).




# ---------------------------------------------------------------------------
# Content-bound input, moved verbatim from commands.support (SPEC (az) item 2).


def _read_content_bound_file(
    path_value: str,
    expected_sha256: str | None = None,
    *,
    label: str = "file input",
) -> tuple[Path, bytes]:
    """Read an external file once and verify the bytes a V2 request approved.

    The returned bytes are the bytes the caller must parse or write. Hashing
    and then reopening the pathname would merely move the TOCTOU window.
    Direct human CLI preflights may omit the digest; an active V2 gateway
    context may not.
    """
    if path_value == "-" and current_gateway_request() is not None:
        raise WriteRefused(
            f"GatewayEnvelopeV2 {label} must be a real path with an approved SHA-256; "
            "unbound stdin is not allowed"
        )
    source = Path(path_value).expanduser().resolve()
    if not source.is_file():
        raise WriteRefused(f"no such {label}: {source}")
    try:
        content = source.read_bytes()
    except OSError as exc:
        raise WriteRefused(f"cannot read {label} {source}: {exc}") from exc
    if expected_sha256 is None:
        if current_gateway_request() is not None:
            raise WriteRefused(
                f"GatewayEnvelopeV2 {label} requires a SHA-256 bound to the exact bytes"
            )
        return source, content
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", expected_sha256):
        raise WriteRefused(
            f"{label} SHA-256 must use sha256:<64 lowercase hexadecimal digits>"
        )
    actual_sha256 = "sha256:" + hashlib.sha256(content).hexdigest()
    if actual_sha256 != expected_sha256:
        raise WriteRefused(
            f"approved {label} changed before use; expected {expected_sha256}, "
            f"found {actual_sha256}. Review the new bytes and create a new approval."
        )
    return source, content


def _read_structured_file(
    path_value: str,
    *,
    expected_sha256: str | None = None,
    label: str = "structured input",
) -> dict:
    """Read a JSON/YAML object from a path, or from stdin when given ``-``.

    Stdin matters for callers that build an envelope in memory: writing it to
    a temp file first means a real file holding canonical intent has to be
    created, found, and cleaned up on every write path, including the ones
    that fail. ``-`` removes that lifecycle entirely.
    """
    if path_value == "-" and expected_sha256 is None \
            and current_gateway_request() is None:
        raw = sys.stdin.read()
        try:
            data = json.loads(raw)
        except ValueError as exc:
            raise WriteRefused(f"cannot parse structured input from stdin: {exc}") from exc
        if not isinstance(data, dict):
            raise WriteRefused("structured input must be an object")
        return data
    path, raw_bytes = _read_content_bound_file(
        path_value,
        expected_sha256,
        label=label,
    )
    try:
        raw = raw_bytes.decode("utf-8")
        if path.suffix.lower() == ".json":
            data = json.loads(raw)
        else:
            data = yaml.safe_load(raw)
    except (UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
        raise WriteRefused(f"cannot parse {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise WriteRefused(f"structured input must be an object: {path}")
    return data


def _require_gateway_v2() -> None:
    if current_gateway_request() is None:
        raise WriteRefused(
            "this approved write must use GatewayEnvelopeV2; direct CLI publication is disabled"
        )


def _input_record_values(record, file_name, label: str) -> dict:
    """The record/file core of ``commands/vnext._input_record`` (SPEC (bl) 3).

    Converted handlers pass their request values directly; the vnext
    wrapper keeps extracting them from the argparse namespace until its
    last caller converts. Validations and messages are the originals.
    """
    if record is not None:
        if not isinstance(record, dict):
            raise WriteRefused(f"{label} must be an object")
        return record
    if not file_name:
        raise WriteRefused(f"{label} is required")
    return _read_structured_file(file_name)


# ---------------------------------------------------------------------------
# Structured record/file input, moved verbatim from commands.support for the
# plan record/file conversions (SPEC (bo) item 2).


# ---------------------------------------------------------------------------
# Canonical YAML serialization, moved verbatim from commands.support
# (SPEC (az) item 2).










# ---------------------------------------------------------------------------
# Material planning helpers, moved verbatim from commands.material for the
# route.patch conversion (SPEC (az) item 2, (bd)).

def _guard_rows(root, artifacts):
    return {rid: artifact_revision(root, rid) for rid in sorted(set(artifacts))}


def _apply_hint(args, capability, snapshot_id, revisions):
    """Ready-to-submit apply values for a successful --check.

    Direct CLI application is disabled, so the hint echoes everything the
    GatewayEnvelopeV2 needs except the per-request fields (request_id,
    idempotency_key, channel, approval): capability, exact payload,
    expected snapshot, and expected revisions. Output layer only —
    validation, guards, and receipts are unchanged.
    """
    if capability != "route.patch":
        return None
    return {
        "apply_via": "GatewayEnvelopeV2",
        "capability": capability,
        "payload": {
            "unit_id": args.unit_id,
            "route_id": args.route_id,
            "changes": args.changes,
        },
        "expected_snapshot": snapshot_id,
        "expected_revisions": dict(revisions),
        "apply_how": ("direct CLI application is disabled; submit a "
                      "GatewayEnvelopeV2 with this capability, payload, "
                      "expected_snapshot and expected_revisions"),
    }


def _map_for_unit(repo, unit_id):
    maps = [sm for sm in repo.study_maps.values() if sm.unit_id == unit_id]
    if len(maps) > 1:
        raise WriteRefused(f"unit {unit_id} has ambiguous study maps")
    return maps[0] if maps else None


def _changed_write(writes, path, data):
    content = _dump_yaml(data)
    # Callers compare record values first; this second check also avoids a
    # write intent when the exact serialized bytes are already current.
    if path.read_bytes() != content.encode("utf-8"):
        writes[path] = content


# ---------------------------------------------------------------------------
# Notes shared helpers, moved verbatim from commands.support, commands.capability,
# commands.query and commands.reads for the wave-1 notes conversions (SPEC (bl),
# CODEX-WAVE1-DISPOSITIONS-20261010 items 2-3). Bodies and signatures unchanged;
# _window_values is the extracted value-based core of commands.reads._window.


def prepare_review_envelope(capability_name: str, payload: dict,
                            snapshot: str, revisions: dict) -> dict:
    """Prepare a recoverable request during preflight, while its lock is held."""
    envelope = {
        "schema_version": 2,
        "request_id": f"request-reviewed-{observations.new_hex()}",
        "idempotency_key": f"reviewed-{observations.new_hex()}",
        "capability": capability_name,
        "channel": "codex",
        "expected_snapshot": snapshot,
        "expected_revisions": revisions,
        "payload": payload,
        "approval": {"kind": "operator-approval", "subject_sha256": ""},
    }
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    return envelope


def _inbox_search_rows(root: Path) -> list[dict]:
    """One discovery row per inbox file, matched on names only, never bytes.

    Inbox drops are arbitrary files (binary captures included), so the
    metadata search reads no content here: the haystack is the file name
    and path. Content stays behind ``inbox-read``, which refuses non-text.
    Raises OSError when the listing itself fails; a missing inbox is empty.
    """
    inbox = root / "work" / "inbox"
    if not inbox.is_dir():
        return []
    rows = []
    for path in sorted(inbox.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(inbox).as_posix()
        if any(part.startswith(".") for part in rel.split("/")):
            continue
        rows.append({"id": rel, "type": "inbox-item", "title": path.name,
                     "path": f"work/inbox/{rel}"})
    return rows


def _discovery_row(rec):
    """One stable discovery row, shared by search and inbox-list."""
    return {k: rec.get(k) for k in
            ("id", "type", "title", "path", "status",
             "state", "deprecated")}






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


def _window_values(offset: int, limit: int, expected_snapshot: str | None,
                   maximum: int) -> tuple[int, int]:
    """Offset/limit validation with the exact commands.reads._window rules."""
    if offset < 0 or not 1 <= limit <= maximum:
        raise WriteRefused(f"offset must be nonnegative and limit between 1 and {maximum}")
    if offset and not expected_snapshot:
        raise WriteRefused("continuation requires --expected-snapshot from the previous response")
    return offset, limit


# Atlas authoring guards, moved verbatim from commands.atlas for the
# atlas.question.save conversion (SPEC (bo) 2).


def _safe(root: Path, path: Path) -> Path:
    """Reject links before reading even when a link would resolve in-tree."""
    relative = path.relative_to(root)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise WriteRefused(f"Atlas cannot use a symlink: {relative}")
    return path


def _schema(root: Path, name: str, data: object) -> None:
    schema = json.loads((root / f"system/schema/{name}.schema.json").read_text())
    try:
        jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(data)
    except jsonschema.ValidationError as exc:
        raise WriteRefused(f"{name}: {exc.message}") from exc


# ---------------------------------------------------------------------------
# Atlas relation registries, moved verbatim from commands.atlas for the
# concept.relations.change conversion (SPEC (bo) 2).

RELATION_ARTIFACT = "registry-concept-relations"


def _registries(root: Path) -> dict[Path, dict]:
    single = _safe(root, root / "knowledge/concept-relations.yaml")
    folder = _safe(root, root / "knowledge/concept-relations")
    paths = ([single] if single.exists() else []) + (
        sorted(folder.glob("*.yaml")) if folder.exists() else [])
    if single.exists() and len(paths) > 1:
        raise WriteRefused("both consolidated and partitioned relations exist")
    records = {}
    for path in paths:
        data = yaml.load(_safe(root, path).read_text(encoding="utf-8"), Loader=UniqueKeySafeLoader)
        _schema(root, "concept-relations", data)
        records[path] = data
    return records


# At most this many untargeted rows ride the screen; the section's
# ``total`` stays exact past the bound. Moved verbatim from
# commands.resume for the plan reads (SPEC (bo) item 2).
MAX_STAGE_RESULTS = 5


# ---------------------------------------------------------------------------
# Analysis-note scope and freshness, moved verbatim from commands.reads
# for the plan reads (SPEC (bo) item 2).


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


# ---------------------------------------------------------------------------
# Offset/limit validation with the exact commands.reads._window rules,
# added with exactly the conductor's text for the plan reads and the
# notes wave (SPEC (bs) item 4).


# ---------------------------------------------------------------------------
# Use-evidence tallies and note bytes, moved verbatim from
# commands.reads for the plan reads (SPEC (bo) item 2).


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

# Value-based window core (SPEC (bl) item 3): the exact validations and
# messages of commands/reads.py:_window, taking request values directly so
# converted handlers pass no namespace.


# ---------------------------------------------------------------------------
# Inbox discovery rows, moved verbatim from commands/query.py (SPEC (bo)
# item 2): the status conversion needs them while search and inbox-list
# still call them from commands.


# ---------------------------------------------------------------------------
# Ranked intelligence scan, moved verbatim from commands/intelligence.py
# (SPEC (bo) item 2): the intelligence-scan conversion needs ranked_scan
# while cmd_resume still calls it from commands. It rests here: the body
# keeps its load_repo, which A4 forbids inside ops/handlers.










# ---------------------------------------------------------------------------
# Stage-use evidence tallies, moved verbatim from commands/reads.py
# (SPEC (bo) item 2): cli.related's related_records and plan's
# material-context both need them, so they rest here.


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

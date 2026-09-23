"""Governed registry intake: shelve metadata-only sources, correct intake fields.

`source.intake.record` (`los source-intake`) is the one standalone writer of
the source registry outside plan and migration transactions. It creates a
metadata-only source from intake evidence or corrects intake-owned fields of
an existing record. Evaluations, topics, material, routes, selections, notes,
feedback and observations are never touched here; anything outside the
create/correct allowlist is refused with the field named.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml

from learning_os.contracts.json_schema import validate_contract
from learning_os.loader import load_repo
from learning_os.revisions import artifact_revision
from learning_os.rules.common import CANONICAL_TREES

from .support import (
    WriteRefused,
    _dump_yaml,
    _expected_ok,
    _expected_revisions_from_args,
    _operator_lock,
    _read_structured_file,
    _root,
    _write_transaction,
)

SOURCE_ID = re.compile(r"^source-[a-z0-9]+(?:-[a-z0-9]+)*$")
SOURCE_TYPES = frozenset({
    "book", "paper", "lecture", "course", "video", "website",
    "documentation", "software", "conversation", "other",
})
MAX_BATCH = 20

# What a create may carry vs. a correct (D7, R2). Type and authors define the
# work itself, so they are set once; title, year and organization are edition
# metadata and stay correctable. Removals are explicit lists, never inferred
# from an absent key.
CREATE_FIELDS = frozenset({
    "action", "id", "partition", "title", "type", "authors", "organization",
    "year", "url", "identifiers", "discovery", "thematic_group_ids",
})
CORRECT_FIELDS = frozenset({
    "action", "id", "title", "organization", "year", "url", "identifiers",
    "remove_url", "remove_identifiers", "discovery", "thematic_group_ids",
})

PARTITION_FOR_GROUP = {
    "thematic-group-mathematics": "mathematics.yaml",
    "thematic-group-optimization": "optimization.yaml",
    "thematic-group-machine-learning": "machine-learning.yaml",
    "thematic-group-ml-systems": "ml-systems.yaml",
    "thematic-group-data-systems": "data-systems.yaml",
    "thematic-group-algorithms": "algorithms.yaml",
    "thematic-group-software": "software.yaml",
    "thematic-group-method-admin": "method-admin.yaml",
}
SUBJECT_PARTITIONS = frozenset(PARTITION_FOR_GROUP.values())


def _input_record(args, label: str) -> dict:
    value = getattr(args, "record", None)
    if value is not None:
        if not isinstance(value, dict):
            raise WriteRefused(f"{label} must be an object")
        return value
    file_name = getattr(args, "file", None)
    if not file_name:
        raise WriteRefused(f"{label} is required")
    return _read_structured_file(file_name)


def _require_gateway_v2() -> None:
    from learning_os.contracts.gateway import current_gateway_request

    if current_gateway_request() is None:
        raise WriteRefused(
            "this approved write must use GatewayEnvelopeV2; direct CLI publication is disabled"
        )


def _refuse_without_approval(args, label: str) -> int | None:
    if getattr(args, "approve", False):
        return None
    print(json.dumps({"ok": False, "error": f"{label} requires explicit approval"}))
    return 2


def _normalize_link(url: str) -> str:
    """A stable comparison form for taught-object identity, not a judgment.

    Scheme and host casefold, the fragment drops, one trailing slash drops.
    Anything that is not an http(s) URL compares as its own stripped text.
    """
    text = url.strip()
    try:
        parts = urlsplit(text)
    except ValueError:
        return text
    if parts.scheme.lower() not in ("http", "https") or not parts.hostname:
        return text
    path = parts.path.rstrip("/") or ""
    query = f"?{parts.query}" if parts.query else ""
    return f"{parts.scheme.lower()}://{parts.hostname.lower()}{path}{query}"


def _registry_link_index(repo) -> dict[str, tuple[str, str]]:
    """Every held address in normalized form -> (source id, where)."""
    index: dict[str, tuple[str, str]] = {}
    for sid in sorted(repo.sources):
        record = repo.sources[sid]
        url = record.get("url")
        if isinstance(url, str) and url.strip():
            index.setdefault(_normalize_link(url), (sid, "url"))
        identifiers = record.get("identifiers") or {}
        if isinstance(identifiers, dict):
            for label in sorted(identifiers):
                address = identifiers[label]
                if isinstance(address, str) and address.strip():
                    index.setdefault(
                        _normalize_link(address), (sid, f"identifiers.{label}"))
    return index


def _cited_elsewhere(root: Path, url: str, exclude: set[Path]) -> str | None:
    """First canonical file citing the exact URL, outside the files rewritten.

    Mirrors the validator's canonical-text walk (Markdown/YAML only, Garden
    and quarantine excluded): a route locator, stage resource or note that
    cites the address keeps it alive, and intake refuses to remove it.
    """
    for tree in CANONICAL_TREES:
        base = root / tree
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.suffix.lower() not in (".md", ".yaml", ".yml") \
                    or not path.is_file():
                continue
            try:
                relative = path.resolve().relative_to(root.resolve())
            except (OSError, ValueError):
                continue
            if relative.parts[:2] == ("knowledge", "garden") \
                    or "quarantine" in relative.parts:
                continue
            if path.resolve() in exclude:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if url in text:
                return relative.as_posix()
    return None


def _refuse_outside_allowlist(item: dict, allowed: frozenset[str], sid: str) -> None:
    for field in sorted(set(item) - allowed):
        if field in CREATE_FIELDS:
            raise WriteRefused(f"{sid}: field '{field}' is create-only")
        raise WriteRefused(
            f"{sid}: field '{field}' is outside the intake allowlist "
            "(evaluations, topics, material, routes, selections, notes, "
            "feedback and observations are never written through intake)"
        )


def _require_text(item: dict, field: str, sid: str) -> str:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        raise WriteRefused(f"{sid}: '{field}' must be a non-empty string")
    return value


def _plan_one(root: Path, repo, item: Any, index: int,
              planned: dict[str, tuple[str, str]]) -> tuple[dict, dict, Path]:
    """Validate one intake row; return (record, diff-row, destination)."""
    tag = f"records[{index}]"
    if not isinstance(item, dict):
        raise WriteRefused(f"{tag} must be an object")
    action = item.get("action")
    if action not in ("create", "correct"):
        raise WriteRefused(f"{tag}: 'action' must be 'create' or 'correct'")
    sid = item.get("id")
    if not isinstance(sid, str) or not SOURCE_ID.match(sid):
        raise WriteRefused(
            f"{tag}: 'id' must match source-<slug> "
            "(prospective candidate-source-* ids are never registered as active)"
        )
    known = repo.sources.get(sid)
    if action == "create":
        if known is not None:
            raise WriteRefused(f"{sid}: already registered (existing)")
        _refuse_outside_allowlist(item, CREATE_FIELDS, sid)
        title = _require_text(item, "title", sid)
        kind = item.get("type")
        if kind not in SOURCE_TYPES:
            raise WriteRefused(f"{sid}: 'type' must be one of {sorted(SOURCE_TYPES)}")
        discovery = item.get("discovery")
        if not isinstance(discovery, dict):
            raise WriteRefused(f"{sid}: create needs 'discovery' provenance")
        partition = item.get("partition")
        groups = item.get("thematic_group_ids", [])
        if not isinstance(groups, list) or any(not isinstance(g, str) for g in groups):
            raise WriteRefused(f"{sid}: 'thematic_group_ids' must be a list of ids")
        for gid in groups:
            if gid not in repo.thematic_groups:
                raise WriteRefused(f"{sid}: thematic group '{gid}' is not registered")
        if groups:
            allowed = sorted({PARTITION_FOR_GROUP[g] for g in groups})
            if partition not in allowed:
                raise WriteRefused(
                    f"{sid}: partition '{partition}' does not match its groups "
                    f"(expected one of {allowed})"
                )
        elif partition not in SUBJECT_PARTITIONS and partition != "sources.yaml":
            raise WriteRefused(
                f"{sid}: unclassified partition '{partition}' must be "
                "'sources.yaml' or a subject partition "
                f"({', '.join(sorted(SUBJECT_PARTITIONS))})"
            )
        if not isinstance(partition, str):
            raise WriteRefused(f"{sid}: create needs a 'partition' file")
        record: dict[str, Any] = {"id": sid, "title": title, "type": kind}
        for field in ("authors", "organization", "year", "url", "identifiers",
                      "discovery", "thematic_group_ids"):
            if item.get(field) is not None:
                record[field] = item[field]
        destination = (root / "sources" / "sources.yaml"
                       if partition == "sources.yaml"
                       else root / "sources" / "registry" / partition)
        before: dict[str, Any] = {}
    else:
        if known is None:
            raise WriteRefused(f"{sid}: correcting an unknown id")
        _refuse_outside_allowlist(item, CORRECT_FIELDS, sid)
        record = dict(known)
        url = item.get("url")
        remove_url = item.get("remove_url", False)
        if url is not None and remove_url:
            raise WriteRefused(f"{sid}: 'url' is both replaced and removed")
        if remove_url is True:
            if not record.get("url"):
                raise WriteRefused(f"{sid}: no 'url' held to remove")
        elif remove_url not in (False, None):
            raise WriteRefused(f"{sid}: 'remove_url' must be true to remove")
        remove_labels = item.get("remove_identifiers", [])
        if not isinstance(remove_labels, list) \
                or any(not isinstance(label, str) for label in remove_labels):
            raise WriteRefused(f"{sid}: 'remove_identifiers' must be a list of labels")
        held = record.get("identifiers") or {}
        if not isinstance(held, dict):
            raise WriteRefused(f"{sid}: existing identifiers are not a mapping")
        for label in remove_labels:
            if label not in held:
                raise WriteRefused(f"{sid}: identifiers label '{label}' is not held")
        incoming = item.get("identifiers") or {}
        if not isinstance(incoming, dict):
            raise WriteRefused(f"{sid}: 'identifiers' must be a label->address mapping")
        for label in remove_labels:
            if label in incoming:
                raise WriteRefused(f"{sid}: identifiers label '{label}' is both set and removed")
        for field in ("title", "organization", "year", "url", "discovery",
                      "thematic_group_ids"):
            if item.get(field) is not None:
                record[field] = item[field]
        if incoming:
            merged = dict(held)
            merged.update(incoming)
            record["identifiers"] = merged
        if remove_labels:
            kept = {label: address for label, address in record["identifiers"].items()
                    if label not in set(remove_labels)}
            if kept:
                record["identifiers"] = kept
            else:
                record.pop("identifiers", None)
        if remove_url is True:
            record.pop("url", None)
        groups = record.get("thematic_group_ids", [])
        if not isinstance(groups, list) or any(not isinstance(g, str) for g in groups):
            raise WriteRefused(f"{sid}: 'thematic_group_ids' must be a list of ids")
        for gid in groups:
            if gid not in repo.thematic_groups:
                raise WriteRefused(f"{sid}: thematic group '{gid}' is not registered")
        old_groups = known.get("thematic_group_ids", [])
        old_discovery = known.get("discovery")
        if (isinstance(old_discovery, dict) and groups != old_groups
                and "thematic_group_ids" in item):
            new_basis = record.get("discovery")
            old_pairs = {(b.get("kind"), b.get("ref"))
                         for b in (old_discovery.get("basis") or [])
                         if isinstance(b, dict)}
            new_pairs = {(b.get("kind"), b.get("ref"))
                         for b in ((new_basis or {}).get("basis") or [])
                         if isinstance(b, dict)} if isinstance(new_basis, dict) else set()
            if not (new_pairs - old_pairs):
                raise WriteRefused(
                    f"{sid}: correcting the shelf of a discovered source "
                    "needs a new discovery basis item"
                )
        origin = repo.source_origins.get(sid)
        destination = Path(origin) if origin else root / "sources" / "sources.yaml"
        before = known
    try:
        validate_contract(root, "sources.schema.json", {"sources": [record]})
    except ValueError as exc:
        raise WriteRefused(f"{sid}: {exc}") from exc
    titles = (record.get("discovery") or {}).get("child_titles") or {}
    labels = record.get("identifiers") or {}
    for label in sorted(titles):
        if label not in labels:
            raise WriteRefused(
                f"{sid}: discovery.child_titles key '{label}' "
                "has no matching identifiers label"
            )
    added: list[str] = []
    if action == "create":
        if isinstance(record.get("url"), str):
            added.append(record["url"])
        for address in (record.get("identifiers") or {}).values():
            if isinstance(address, str):
                added.append(address)
    else:
        if item.get("url") is not None and item.get("url") != before.get("url"):
            added.append(item["url"])
        for label, address in incoming.items():
            if held.get(label) != address and isinstance(address, str):
                added.append(address)
    link_index = _registry_link_index(repo)
    for raw in added:
        holder, where = link_index.get(_normalize_link(raw), (None, ""))
        if holder is not None and holder != sid:
            raise WriteRefused(
                f"{sid}: address {raw} is already held by '{holder}' ({where})"
            )
        earlier = planned.get(_normalize_link(raw))
        if earlier is not None and earlier[0] != sid:
            raise WriteRefused(
                f"{sid}: address {raw} is also added by '{earlier[0]}' in this batch"
            )
        planned[_normalize_link(raw)] = (sid, raw)
    if action == "correct":
        removed: list[str] = []
        if remove_url is True and isinstance(before.get("url"), str):
            removed.append(before["url"])
        for label in remove_labels:
            address = held.get(label)
            if isinstance(address, str):
                removed.append(address)
        exclude = {destination.resolve()} if destination.exists() else set()
        for raw in removed:
            cite = _cited_elsewhere(root, raw, exclude)
            if cite is not None:
                raise WriteRefused(
                    f"{sid}: cannot remove {raw} — still cited by {cite}"
                )
        keeps_link = isinstance(record.get("url"), str) \
            or any(isinstance(a, str) for a in (record.get("identifiers") or {}).values()) \
            or isinstance(record.get("material"), str)
        if removed and not keeps_link:
            raise WriteRefused(
                f"{sid}: removal would leave no reachable locator "
                "(url, identifiers address, or material)"
            )
    tracked = [f for f in
               ("title", "type", "authors", "organization", "year", "url",
                "identifiers", "discovery", "thematic_group_ids")
               if f in record or f in before]
    fields = {}
    for field in tracked:
        old, new = before.get(field), record.get(field)
        if old != new:
            fields[field] = {"before": old, "after": new}
    if action == "correct" and not fields:
        raise WriteRefused(f"{sid}: no intake field changes")
    try:
        filename = destination.resolve().relative_to(
            (root / "sources").resolve()).as_posix()
    except ValueError:
        filename = destination.name
    diff_row = {"id": sid, "action": action, "partition": filename, "fields": fields}
    return record, diff_row, destination


def _plan_intake(root: Path, items: Any) -> dict:
    """Validate a batch and render its diff, writes and guards."""
    if not isinstance(items, list) or not items:
        raise WriteRefused("intake payload needs a non-empty 'records' list")
    if len(items) > MAX_BATCH:
        raise WriteRefused(
            f"batch of {len(items)} exceeds the {MAX_BATCH}-record bound "
            "(one transaction and one receipt stay reviewable)"
        )
    repo = load_repo(root)
    planned: dict[str, tuple[str, str]] = {}
    diff = []
    per_file: dict[Path, dict[str, dict]] = {}
    seen: set[str] = set()
    for position, item in enumerate(items):
        record, row, destination = _plan_one(root, repo, item, position, planned)
        if record["id"] in seen:
            raise WriteRefused(f"{record['id']}: named twice in one batch")
        seen.add(record["id"])
        diff.append(row)
        per_file.setdefault(destination, {})[record["id"]] = record
    writes: dict[Path, str] = {}
    for destination, changed in per_file.items():
        if destination.exists():
            try:
                current = yaml.safe_load(destination.read_text(encoding="utf-8"))
            except (OSError, yaml.YAMLError) as exc:
                raise WriteRefused(f"cannot re-read {destination}: {exc}") from exc
            if not isinstance(current, dict) or not isinstance(current.get("sources"), list):
                raise WriteRefused(f"{destination} is not a source registry file")
            kept = [entry for entry in current["sources"]
                    if not (isinstance(entry, dict) and entry.get("id") in changed)]
            order = [entry.get("id") for entry in current["sources"]
                     if isinstance(entry, dict) and entry.get("id") in changed]
            merged = kept + [changed[sid] for sid in order
                             if sid in changed]
            merged += [changed[sid] for sid in sorted(changed) if sid not in set(order)]
            document = {"sources": merged}
        else:
            document = {"sources": [changed[sid] for sid in sorted(changed)]}
        writes[destination] = _dump_yaml(document)
    canonical = json.dumps(diff, sort_keys=True, ensure_ascii=False).encode("utf-8")
    artifact_ids = sorted(seen)
    return {
        "diff": diff,
        "diff_sha256": "sha256:" + hashlib.sha256(canonical).hexdigest(),
        "writes": writes,
        "artifact_ids": artifact_ids,
        "expected_revisions": {sid: artifact_revision(root, sid) for sid in artifact_ids},
    }


def cmd_source_intake_record(args) -> int:
    """Create metadata-only sources or correct intake-owned fields, atomically."""
    root = _root(args)
    try:
        data = _input_record(args, "intake records")
        plan = _plan_intake(root, data.get("records"))
    except WriteRefused as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    if getattr(args, "check", False):
        print(json.dumps({
            "ok": True, "check": True, "records": len(plan["diff"]),
            "diff": plan["diff"], "diff_sha256": plan["diff_sha256"],
            "expected_revisions": plan["expected_revisions"],
            "artifact_ids": plan["artifact_ids"],
        }, indent=2, ensure_ascii=False))
        return 0
    denied = _refuse_without_approval(args, "source intake")
    if denied is not None:
        return denied
    _require_gateway_v2()
    with _operator_lock(root):
        try:
            plan = _plan_intake(root, data.get("records"))
        except WriteRefused as exc:
            print(json.dumps({"ok": False, "error": str(exc)}))
            return 2
        expected_diff = getattr(args, "expected_diff_sha256", None)
        if not expected_diff:
            print(json.dumps({"ok": False, "error":
                              "apply needs --expected-diff-sha256 from a check run"}))
            return 2
        if expected_diff != plan["diff_sha256"]:
            print(json.dumps({"ok": False, "error":
                              "intake diff changed since check; re-run --check"}))
            return 2
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        code, errors, confirmation = _write_transaction(
            root,
            plan["writes"],
            capability="source.intake.record",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=tuple(plan["artifact_ids"]),
        )
    print(json.dumps({
        "ok": code == 0, **confirmation,
        **({"errors": [str(error) for error in errors]} if errors else {}),
    }, indent=2, ensure_ascii=False))
    return code

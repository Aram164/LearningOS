"""Governed one-line correction for a curated collection entry.

`collection.entry.revise` (`los collection-entry-revise`) revises the `why`
of one existing entry in one existing collection. The schema owns ordering,
grouping and each entry's one-line role in its list; the source record owns
pedagogical judgments about the source itself. This capability changes one
line of list-local prose and refuses everything else: unknown or duplicate
targets, no-ops, foreign fields, and empty or multi-line replacements.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

from learning_os.contracts.json_schema import validate_contract
from learning_os.loader import load_repo
from learning_os.revisions import artifact_revision

from .support import (
    WriteRefused,
    _expected_ok,
    _expected_revisions_from_args,
    _operator_lock,
    _read_structured_file,
    _root,
    _write_transaction,
)

SOURCE_ID = re.compile(r"^source-[a-z0-9]+(?:-[a-z0-9]+)*$")
COLLECTION_STEM = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
REVISE_FIELDS = frozenset({"collection", "source", "why"})


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


def _splice_why(raw: str, stem: str, position: int, sid: str,
                old: str, why: str) -> str:
    """Replace only the targeted entry's `why` scalar in the original text.

    A full YAML round-trip rewrites layout everywhere (81 to 91 lines on the
    math bookshelf); the revision owns one scalar, so only its source span is
    replaced. Indentation, the `why:` key, quoting elsewhere, sibling entries,
    header comments and blank lines survive byte-identical. Anything the
    splice cannot prove safe — flow style, anchors, duplicate keys, a raw
    text that no longer carries the loaded line — is refused, never guessed.
    """
    try:
        root = yaml.compose(raw)
    except yaml.YAMLError as exc:
        raise WriteRefused(f"collection '{stem}' does not parse: {exc}") from exc
    if not isinstance(root, yaml.MappingNode):
        raise WriteRefused(f"collection '{stem}' is not a mapping")
    entries_node = None
    for key, value in root.value:
        if isinstance(key, yaml.ScalarNode) and key.value == "entries":
            entries_node = value
    if not isinstance(entries_node, yaml.SequenceNode):
        raise WriteRefused(f"collection '{stem}' has no entries list")
    if position >= len(entries_node.value):
        raise WriteRefused(
            f"collection '{stem}' changed under the revision — re-run --check")
    entry_node = entries_node.value[position]
    if not isinstance(entry_node, yaml.MappingNode):
        raise WriteRefused(
            f"collection '{stem}' entry {position} is not a mapping")
    fields = [(k.value, v) for k, v in entry_node.value
              if isinstance(k, yaml.ScalarNode)]
    if sum(1 for name, _ in fields if name == "why") != 1:
        raise WriteRefused(
            f"collection '{stem}' entry {position} has no single 'why' scalar")
    sources = [v.value for name, v in fields
               if name == "source" and isinstance(v, yaml.ScalarNode)]
    if sources != [sid]:
        raise WriteRefused(
            f"collection '{stem}' changed under the revision — re-run --check")
    value = next(v for name, v in fields if name == "why")
    if not isinstance(value, yaml.ScalarNode) or value.value != old:
        raise WriteRefused(
            f"collection '{stem}' no longer carries the checked line — "
            "re-run --check")
    lines = raw.splitlines(keepends=True)
    start, end = value.start_mark, value.end_mark
    span_start = start.line
    span_end = end.line if end.column > 0 else end.line - 1
    # The prefix (indent, dash, `why:` key, spacing) is preserved verbatim;
    # flow style cannot reach here with a clean suffix (a closing `}`/`]`
    # always trails the scalar) and is refused below.
    prefix = lines[span_start][:start.column]
    comment = ""
    if value.style in (">", "|"):
        rest = lines[span_start][start.column:]
        match = re.match(r"^[|>][+-]?[0-9]?[ \t]*(#[^\n]*)?\n?$", rest)
        if match is None:
            raise WriteRefused(
                f"collection '{stem}' entry {position} carries an exotic "
                "block header — refusing the splice")
        comment = match.group(1) or ""
    else:
        rest = lines[span_end][end.column:]
        match = re.match(r"^[ \t]*(#[^\n]*)?\n?$", rest)
        if match is None:
            raise WriteRefused(
                f"collection '{stem}' entry {position} carries trailing "
                "content after its 'why' — refusing the splice")
        comment = match.group(1) or ""
    dumped = yaml.safe_dump({"why": why}, width=4096, allow_unicode=True,
                            sort_keys=False)
    if not dumped.startswith("why: "):
        raise WriteRefused("could not serialize the replacement line")
    scalar_lines = dumped[len("why: "):].rstrip("\n").split("\n")
    replacement = [prefix + scalar_lines[0] + "\n"]
    replacement.extend(line + "\n" for line in scalar_lines[1:])
    if comment:
        replacement[-1] = replacement[-1][:-1] + "  " + comment + "\n"
    if span_end == len(lines) - 1 and not lines[span_end].endswith("\n"):
        replacement[-1] = replacement[-1][:-1]
    return "".join(lines[:span_start] + replacement + lines[span_end + 1:])


def _plan_revise(root: Path, item: Any) -> dict:
    """Validate one collection-entry revision; return diff, writes, guards."""
    if not isinstance(item, dict):
        raise WriteRefused("collection revise payload must be an object")
    for field in sorted(set(item) - REVISE_FIELDS):
        raise WriteRefused(
            f"field '{field}' is outside the revise allowlist "
            "(only one entry's 'why' is revised here; source, group, order "
            "and every other entry are never written through revision)"
        )
    if "collection" not in item or "source" not in item or "why" not in item:
        raise WriteRefused("a revision needs 'collection', 'source' and 'why'")
    stem, sid, why = item.get("collection"), item.get("source"), item.get("why")
    if not isinstance(stem, str) or not COLLECTION_STEM.match(stem):
        raise WriteRefused("'collection' must be a kebab-case filename stem")
    if not isinstance(sid, str) or not SOURCE_ID.match(sid):
        raise WriteRefused("'source' must match source-<slug>")
    if not isinstance(why, str) or not why.strip() or "\n" in why or "\r" in why:
        raise WriteRefused("'why' must be a nonempty one-line string")
    repo = load_repo(root)
    doc = (repo.collections or {}).get(stem)
    if doc is None:
        raise WriteRefused(f"unknown collection: {stem}")
    origin = (repo.collection_origins or {}).get(stem)
    if origin is None:
        raise WriteRefused(f"collection '{stem}' has no file origin")
    entries = doc.get("entries") or []
    hits = [position for position, entry in enumerate(entries)
            if isinstance(entry, dict) and entry.get("source") == sid]
    if not hits:
        raise WriteRefused(f"collection '{stem}' has no entry for source {sid}")
    if len(hits) > 1:
        raise WriteRefused(
            f"collection '{stem}' matches {len(hits)} entries for {sid} — "
            "deduplicate the collection before revising one line"
        )
    (position,) = hits
    old = entries[position].get("why")
    if old == why:
        raise WriteRefused(
            f"collection '{stem}' entry for {sid} already carries that line: no change"
        )
    if not isinstance(old, str):
        raise WriteRefused(
            f"collection '{stem}' entry for {sid} carries a non-string 'why' — "
            "repair the collection before revising one line"
        )
    try:
        # Universal newlines: a CRLF shelf normalizes to LF here, like
        # every governed write in the system — content and layout survive,
        # endings follow the writer.
        raw = origin.read_text(encoding="utf-8")
    except OSError as exc:
        raise WriteRefused(f"cannot re-read {origin}: {exc}") from exc
    spliced = _splice_why(raw, stem, position, sid, old, why)
    try:
        before_text = yaml.safe_load(raw)
        parsed = yaml.safe_load(spliced)
    except yaml.YAMLError as exc:
        raise WriteRefused(f"collection '{stem}' splice failed to parse: {exc}") from exc
    # Differential proof, same parser both sides: the splice replaced exactly
    # the targeted scalar and nothing else. (Comparing against the loaded doc
    # instead would false-refuse on loader normalization such as dates.)
    expected = copy.deepcopy(before_text)
    expected["entries"][position]["why"] = why
    if parsed != expected:
        raise WriteRefused(
            f"collection '{stem}' splice verification failed — refusing the write")
    try:
        validate_contract(root, "collections.schema.json", parsed)
    except ValueError as exc:
        raise WriteRefused(f"{stem}: {exc}") from exc
    artifact = f"collection:{stem}"
    diff = [{"collection": stem, "source": sid,
             "group": entries[position].get("group"),
             "before": old, "after": why}]
    canonical = json.dumps(diff, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return {
        "diff": diff,
        "diff_sha256": "sha256:" + hashlib.sha256(canonical).hexdigest(),
        "writes": {origin: spliced},
        "artifact_ids": [artifact],
        "expected_revisions": {artifact: artifact_revision(root, artifact)},
    }


def cmd_collection_entry_revise(args) -> int:
    """Revise one collection entry's `why`, atomically."""
    root = _root(args)
    try:
        data = _input_record(args, "collection revise record")
        plan = _plan_revise(root, data)
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
    denied = _refuse_without_approval(args, "collection entry revision")
    if denied is not None:
        return denied
    _require_gateway_v2()
    with _operator_lock(root):
        try:
            plan = _plan_revise(root, data)
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
                              "revision diff changed since check; re-run --check"}))
            return 2
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        code, errors, confirmation = _write_transaction(
            root,
            plan["writes"],
            capability="collection.entry.revise",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=tuple(plan["artifact_ids"]),
        )
    print(json.dumps({
        "ok": code == 0, **confirmation,
        **({"errors": [str(error) for error in errors]} if errors else {}),
    }, indent=2, ensure_ascii=False))
    return code

#!/usr/bin/env python3
"""Freeze, map, and migrate legacy summary-cache entries to durable notes.

Three phases, run in order:

    freeze   copy every summary.md + meta.json byte-exactly into
             operations/migrations/summary-freeze-2026-09-21/ with a hashed
             inventory. Later phases read only the frozen bytes, never the
             disposable cache.
    map      bind frozen hashes to note ids, destinations, and a resolution
             (resolved / unresolved / unavailable / stale) in a reviewable
             mapping report. Refuses changed frozen bytes and id collisions.
    migrate  save each mapped row through note.analysis.save under a fresh
             snapshot guard, then record a migration manifest binding the
             mapping hash. Requires --apply; reruns replay identical rows.

Every phase is dry-run by default and refuses changed inputs rather than
regenerating evidence silently. Understands data-contract v35.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

from learning_os.commands.support import WriteRefused
from learning_os.contracts.gateway import intent_sha256
from learning_os.contracts.migration_lifecycle import (
    MigrationLifecycleError,
    declared_data_contract,
    refuse_retired_apply,
    retired_migration,
)
from learning_os.fingerprint import canonical_fingerprint
from learning_os.loader import load_repo
from learning_os.material_analysis import observe_local_material
from learning_os.materials_resolution import (
    material_location,
    material_uri_authority,
)
from learning_os.pathing import PathBoundaryError
from learning_os.rules.common import SUFFIX_RE
from learning_os.transactions import artifact_revision

MIGRATION_ID = "summaries-to-notes-v1"
SUPPORTED_THROUGH = 35
FREEZE_DIRNAME = "summary-freeze-2026-09-21"
INVENTORY_NAME = "freeze-inventory.yaml"
MAPPING_NAME = "summary-mapping-2026-09-21-r2.yaml"
MANIFEST_NAME = "summary-migration-manifest-r2.yaml"

HEX64 = re.compile(r"\A[0-9a-f]{64}\Z")
PAGES_DIR = re.compile(r"\Apages-(\d+)-(\d+)\Z")
SLUG_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _refuse(reason: str) -> int:
    print(f"{MIGRATION_ID}: refused: {reason}", file=sys.stderr)
    return 2


def _migrations_dir(root: Path) -> Path:
    return root / "operations" / "migrations"


def _readable_file(path: Path, label: str) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise WriteRefused(f"{label} is not a regular file: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise WriteRefused(f"cannot read {label}: {exc}") from exc


def _scan_cache(root: Path) -> tuple[list[dict], list[str]]:
    """Inventory the disposable summary cache. Problems refuse the freeze."""
    entries: list[dict] = []
    problems: list[str] = []
    cache = root / "generated" / "summaries"
    if not cache.is_dir():
        return [], []
    for digest_dir in sorted(cache.iterdir(), key=lambda p: p.name):
        if not digest_dir.is_dir() or digest_dir.is_symlink():
            problems.append(f"unexpected cache entry: {digest_dir.name}")
            continue
        digest = digest_dir.name
        if not HEX64.match(digest):
            problems.append(f"non-digest cache directory: {digest}")
            continue
        for pages_dir in sorted(digest_dir.iterdir(), key=lambda p: p.name):
            match = PAGES_DIR.match(pages_dir.name)
            if match is None or not pages_dir.is_dir() or pages_dir.is_symlink():
                problems.append(f"unexpected range directory: {digest}/{pages_dir.name}")
                continue
            start, end = int(match.group(1)), int(match.group(2))
            body_path = pages_dir / "summary.md"
            meta_path = pages_dir / "meta.json"
            try:
                body = _readable_file(body_path, "summary body")
                raw_meta = _readable_file(meta_path, "summary meta")
            except WriteRefused as exc:
                problems.append(str(exc))
                continue
            try:
                meta = json.loads(raw_meta.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                problems.append(f"unparseable meta: {digest}/{pages_dir.name}")
                continue
            if not isinstance(meta, dict):
                problems.append(f"meta is not an object: {digest}/{pages_dir.name}")
                continue
            if meta.get("sha256") != digest or meta.get("page_range") != [start, end]:
                problems.append(
                    f"meta does not match its cache location: {digest}/{pages_dir.name}")
                continue
            recorded = meta.get("summary_sha256")
            if recorded is None:
                integrity = "legacy-unrecorded"
            elif recorded != _sha256_bytes(body):
                problems.append(
                    f"recorded body checksum mismatch: {digest}/{pages_dir.name}")
                continue
            else:
                integrity = "verified"
            entries.append({
                "digest": digest, "pages": pages_dir.name,
                "material": meta.get("material"), "page_range": [start, end],
                "scope": meta.get("scope"), "model": meta.get("model"),
                "built": meta.get("built"), "meta_integrity": integrity,
                "body": body, "meta_bytes": raw_meta,
            })
    return entries, problems


def _load_inventory(path: Path) -> dict | None:
    if not path.is_file() or path.is_symlink():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return None
    return data if isinstance(data, dict) else None


def _inventory_matches(entries: list[dict], inventory: dict) -> bool:
    wanted = [{"digest": e["digest"], "pages": e["pages"],
               "summary_sha256": _sha256_bytes(e["body"]),
               "meta_sha256": _sha256_bytes(e["meta_bytes"])} for e in entries]
    recorded = [{"digest": e.get("digest"), "pages": e.get("pages"),
                 "summary_sha256": (e.get("files") or {}).get("summary.md", {}).get("sha256"),
                 "meta_sha256": (e.get("files") or {}).get("meta.json", {}).get("sha256")}
                for e in inventory.get("entries", [])]
    return wanted == recorded


def cmd_freeze(root: Path, *, apply: bool) -> int:
    entries, problems = _scan_cache(root)
    if problems:
        for problem in problems:
            print(f"{MIGRATION_ID}: {problem}", file=sys.stderr)
        return 2
    dest = _migrations_dir(root) / FREEZE_DIRNAME
    inventory_path = dest / INVENTORY_NAME
    inventory = _load_inventory(inventory_path)
    if inventory is not None:
        if _inventory_matches(entries, inventory):
            print(f"{MIGRATION_ID}: freeze already complete "
                  f"({len(entries)} entries, unchanged)")
            return 0
        return _refuse("frozen inventory exists and differs from the live cache; "
                       "resolve deliberately, never by silent regeneration")
    total = sum(len(e["body"]) + len(e["meta_bytes"]) for e in entries)
    if not apply:
        print(f"{MIGRATION_ID}: freeze would preserve {len(entries)} entries "
              f"({total} bytes) under {dest.relative_to(root)}")
        return 0
    dest.mkdir(parents=True, exist_ok=True)
    recorded = []
    for entry in entries:
        target = dest / entry["digest"] / entry["pages"]
        target.mkdir(parents=True, exist_ok=True)
        (target / "summary.md").write_bytes(entry["body"])
        (target / "meta.json").write_bytes(entry["meta_bytes"])
        if _sha256_file(target / "summary.md") != _sha256_bytes(entry["body"]):
            return _refuse(f"freeze write did not round-trip: {entry['digest']}")
        recorded.append({
            "digest": entry["digest"], "pages": entry["pages"],
            "material": entry["material"], "page_range": entry["page_range"],
            "scope": entry["scope"], "model": entry["model"],
            "built": entry["built"], "meta_integrity": entry["meta_integrity"],
            "files": {
                "summary.md": {"bytes": len(entry["body"]),
                               "sha256": _sha256_bytes(entry["body"])},
                "meta.json": {"bytes": len(entry["meta_bytes"]),
                              "sha256": _sha256_bytes(entry["meta_bytes"])},
            },
        })
    inventory_path.write_text(yaml.safe_dump(
        {"tool": MIGRATION_ID, "contract_version": declared_data_contract(root),
         "captured": date.today().isoformat(), "entries": recorded},
        sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"{MIGRATION_ID}: froze {len(recorded)} entries under "
          f"{dest.relative_to(root)}")
    return 0


def _slug(stem: str) -> str:
    slug = SLUG_NON_ALNUM.sub("-", stem.casefold()).strip("-")
    return slug or "material"


def _covering_sources(repo, materials_root: Path, material: str) -> list[str]:
    """Registered sources whose material target is the file or its parent."""
    try:
        wanted = (materials_root / material).resolve()
    except OSError:
        return []
    found = []
    for sid, source in repo.sources.items():
        ref = source.get("material") if isinstance(source, dict) else None
        if material_uri_authority(ref) is None:
            continue
        try:
            located = material_location(repo, ref)
        except (PathBoundaryError, OSError, ValueError):
            continue
        if not located.get("material_exists") or not located.get("material_path"):
            continue
        try:
            target = (repo.learningos_root / located["material_path"]).resolve()
        except OSError:
            continue
        if wanted == target or target in wanted.parents:
            found.append(sid)
    return sorted(found)


def _title_for(stem: str, start: int, end: int, body: bytes) -> str:
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        text = ""
    for line in text.splitlines():
        if line.startswith("# "):
            heading = line[2:].strip()
            if heading:
                return heading[:120]
    return f"{stem} pp. {start}\u2013{end}"


def _frozen_verified(root: Path, inventory: dict) -> str | None:
    """Refusal reason when frozen bytes no longer match, else None."""
    dest = _migrations_dir(root) / FREEZE_DIRNAME
    for entry in inventory.get("entries", []):
        for name in ("summary.md", "meta.json"):
            recorded = ((entry.get("files") or {}).get(name) or {}).get("sha256")
            target = dest / entry["digest"] / entry["pages"] / name
            try:
                if _sha256_file(target) != recorded:
                    return (f"frozen input changed: {entry['digest']}/{entry['pages']}"
                            f"/{name}; refusing to reinterpret it")
            except OSError:
                return f"frozen input unreadable: {entry['digest']}/{entry['pages']}/{name}"
    return None


def cmd_map(root: Path, *, apply: bool) -> int:
    dest = _migrations_dir(root) / FREEZE_DIRNAME
    inventory_path = dest / INVENTORY_NAME
    inventory = _load_inventory(inventory_path)
    if inventory is None:
        return _refuse("no frozen inventory; run the freeze phase first")
    problem = _frozen_verified(root, inventory)
    if problem is not None:
        return _refuse(problem)
    repo = load_repo(root)
    # Recorded summary paths are physical-tree relpaths (the same root
    # material_summarize --read resolves against), not .flat aliases.
    physical = repo.learningos_root / "materials"
    rows = []
    for entry in inventory.get("entries", []):
        material = entry.get("material")
        recorded = entry.get("digest")
        start, end = entry["page_range"]
        if not isinstance(material, str) or not material:
            return _refuse(f"frozen entry has no material: {recorded}/{entry['pages']}")
        observation = observe_local_material(physical, material, recorded)
        status = observation["status"]
        candidates = _covering_sources(repo, physical, material) \
            if status == "current" else []
        if status == "current" and len(candidates) == 1:
            resolution, source_id = "resolved", candidates[0]
            reason = f"live bytes match; covered by registered {source_id}"
        elif status == "current" and not candidates:
            resolution, source_id = "unresolved", None
            reason = "live bytes match but no registered source covers this file"
        elif status == "current":
            resolution, source_id = "unresolved", None
            reason = f"live bytes match but {len(candidates)} sources cover this file"
        elif status == "stale":
            resolution, source_id = "stale", None
            reason = "live bytes differ from the recorded digest"
        elif status == "missing":
            resolution, source_id = "unavailable", None
            reason = "no readable file at the recorded path"
        else:
            resolution, source_id = "unavailable", None
            reason = "recorded path escapes the materials root"
        stem = Path(material).stem
        # Zero-padded ranges sort in page order and never read as a
        # collision suffix (ID-SUFFIX warns on an -NN tail).
        note_id = f"note-{_slug(stem)}-pp{start:03d}-{end:03d}"
        domain = material.split("/", 1)[0]
        if not (root / "knowledge" / "notes" / domain).is_dir():
            domain = "cross-domain"
        frozen_body = (dest / recorded / entry["pages"] / "summary.md").read_bytes()
        try:
            frozen_body.decode("utf-8")
        except UnicodeDecodeError:
            return _refuse(f"frozen body is not valid UTF-8: {recorded}/{entry['pages']}")
        binding: dict = {
            "resolution": resolution,
            "material": material,
            "recorded_source_digest": recorded,
            "inspected_range": {"start": start, "end": end},
            "frozen_input_sha256": _sha256_bytes(frozen_body),
            "frozen_input_bytes": len(frozen_body),
        }
        if source_id is not None:
            binding["source_id"] = source_id
        if "live_digest" in observation:
            binding["live_source_digest"] = observation["live_digest"]
        if isinstance(entry.get("model"), str):
            binding["model"] = entry["model"]
        if isinstance(entry.get("built"), str):
            binding["built"] = entry["built"]
        rows.append({
            "digest": recorded, "pages": entry["pages"], "material": material,
            "page_range": [start, end], "note_id": note_id,
            "note_path": f"knowledge/notes/{domain}/{note_id}.md",
            "title": _title_for(stem, start, end, frozen_body),
            "resolution": resolution, "reason": reason,
            "meta_integrity": entry.get("meta_integrity"),
            "binding": binding,
        })
    seen: set[str] = set()
    for row in rows:
        if row["note_id"] in seen:
            return _refuse(f"mapping proposes a duplicate note id: {row['note_id']}")
        seen.add(row["note_id"])
        if SUFFIX_RE.match(row["note_id"]):
            return _refuse(f"mapping proposes a collision-looking id: {row['note_id']}; "
                           "numeric tails are collision-only")
        if row["note_id"] in repo.notes:
            return _refuse(f"note id already exists: {row['note_id']}; "
                           "change the mapping, never overwrite")
        if (root / row["note_path"]).exists():
            return _refuse(f"destination already exists: {row['note_path']}")
    if not apply:
        for row in rows:
            print(f"{row['resolution']:11} {row['note_id']} <- "
                  f"{row['digest'][:12]}/{row['pages']} ({row['reason']})")
        print(f"{MIGRATION_ID}: map would bind {len(rows)} rows")
        return 0
    mapping = {"tool": MIGRATION_ID,
               "contract_version": declared_data_contract(root),
               "created": date.today().isoformat(),
               "freeze_inventory_sha256": _sha256_file(inventory_path),
               "rows": rows}
    mapping_path = _migrations_dir(root) / MAPPING_NAME
    if mapping_path.is_file() and not mapping_path.is_symlink():
        if _sha256_file(mapping_path) == _sha256_bytes(
                yaml.safe_dump(mapping, sort_keys=False,
                               allow_unicode=True).encode("utf-8")):
            print(f"{MIGRATION_ID}: mapping already complete ({len(rows)} rows)")
            return 0
        return _refuse("a different mapping report already exists; refusing to overwrite")
    mapping_path.write_text(yaml.safe_dump(mapping, sort_keys=False, allow_unicode=True),
                            encoding="utf-8")
    print(f"{MIGRATION_ID}: mapped {len(rows)} rows to "
          f"{mapping_path.relative_to(root)}")
    return 0


def cmd_migrate(root: Path, *, apply: bool) -> int:
    if not apply:
        return _refuse("migrate writes canonical notes and requires --apply")
    migrations = _migrations_dir(root)
    inventory_path = migrations / FREEZE_DIRNAME / INVENTORY_NAME
    mapping_path = migrations / MAPPING_NAME
    inventory = _load_inventory(inventory_path)
    if inventory is None:
        return _refuse("no frozen inventory; run the freeze phase first")
    try:
        mapping = yaml.safe_load(mapping_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        return _refuse(f"cannot read mapping report: {exc}")
    if not isinstance(mapping, dict) or not isinstance(mapping.get("rows"), list):
        return _refuse("mapping report is malformed")
    if mapping.get("freeze_inventory_sha256") != _sha256_file(inventory_path):
        return _refuse("mapping binds a different frozen inventory; refusing")
    problem = _frozen_verified(root, inventory)
    if problem is not None:
        return _refuse(problem)
    los = root / "tools" / "los.py"
    repo = load_repo(root)
    results = []
    for row in mapping["rows"]:
        digest, pages = row["digest"], row["pages"]
        body_file = migrations / FREEZE_DIRNAME / digest / pages / "summary.md"
        frozen_body = body_file.read_bytes()
        prior = repo.notes.get(row["note_id"])
        if prior is not None:
            # A rerun must not dispatch a second mutation: verify the
            # existing note is byte-identical and record a replay. Anything
            # else means the mapping moved under a previous migrate.
            try:
                prior_raw = prior.path.read_bytes()
            except OSError:
                return _refuse(f"{row['note_id']}: existing note unreadable")
            stored = (prior.meta.get("material_analysis") or {}).get(
                "frozen_input_bytes")
            identical = (
                prior.meta.get("title") == row["title"]
                and prior.meta.get("material_analysis") == row["binding"]
                and prior.path == root / row["note_path"]
                and isinstance(stored, int)
                and prior_raw[-stored:] == frozen_body)
            if not identical:
                return _refuse(
                    f"{row['note_id']}: note exists and differs from the mapping; "
                    "reconcile deliberately, never by overwrite")
            results.append({"note_id": row["note_id"],
                            "note_path": row["note_path"], "replayed": True,
                            "save": {"ok": True, "replayed": True}})
            print(f"replayed: {row['note_id']}")
            continue
        key = f"summaries-migrate-{row['note_id']}"
        envelope = {
            "schema_version": 2,
            "request_id": f"request-{key}",
            "idempotency_key": key,
            "capability": "note.analysis.save",
            "channel": "operator",
            "expected_snapshot": "sha256:" + canonical_fingerprint(root),
            "expected_revisions": {
                row["note_id"]: artifact_revision(root, row["note_id"])},
            "approval": {"kind": "operator-approval",
                         "subject_sha256": "sha256:" + "0" * 64},
            "payload": {
                "analysis": {"id": row["note_id"], "title": row["title"],
                             "path": row["note_path"],
                             "binding": row["binding"]},
                "body_file": str(body_file),
                "body_file_sha256": "sha256:" + _sha256_file(body_file),
            },
        }
        envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
        proc = subprocess.run(
            [sys.executable, str(los), "--root", str(root), "capability",
             "note.analysis.save", "--payload-file", "-"],
            input=json.dumps(envelope), capture_output=True, text=True,
            timeout=120)
        if proc.returncode != 0:
            return _refuse(f"{row['note_id']}: save refused: "
                           f"{(proc.stdout + proc.stderr).strip()}")
        try:
            result = json.loads(proc.stdout)
        except ValueError:
            return _refuse(f"{row['note_id']}: unreadable save result")
        results.append({"note_id": row["note_id"], "note_path": row["note_path"],
                        "replayed": bool(result.get("replayed")),
                        "save": result})
        print(f"{'replayed' if result.get('replayed') else 'saved'}: {row['note_id']}")
    manifest_path = migrations / MANIFEST_NAME
    manifest_path.write_text(yaml.safe_dump(
        {"tool": MIGRATION_ID, "contract_version": declared_data_contract(root),
         "migrated_at": date.today().isoformat(),
         "mapping_sha256": _sha256_file(mapping_path), "notes": results},
        sort_keys=False, allow_unicode=True), encoding="utf-8")
    print(f"{MIGRATION_ID}: migrated {len(results)} notes; manifest at "
          f"{manifest_path.relative_to(root)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("phase", choices=("freeze", "map", "migrate"))
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    parser.add_argument("--apply", action="store_true",
                        help="perform writes (default is a no-write dry run)")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        retired = retired_migration(root, MIGRATION_ID,
                                    supported_through=SUPPORTED_THROUGH)
    except MigrationLifecycleError as exc:
        return _refuse(str(exc))
    if refuse_retired_apply(retired, apply=args.apply):
        return 2 if args.apply else 0
    if args.phase == "freeze":
        return cmd_freeze(root, apply=args.apply)
    if args.phase == "map":
        return cmd_map(root, apply=args.apply)
    return cmd_migrate(root, apply=args.apply)


if __name__ == "__main__":
    raise SystemExit(main())

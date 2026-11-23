"""Append-only LearnKit export engine (P6 steps 37–40).

The canonical note is the only source of prompt and solution text; the
sidecar is the only source of verification. A card is exported only when
its item is extracted deterministically, currently checked, flashcard-shaped
and anchored to exactly one registered physical PDF source. Delivery is
create-only into a separately marked practice vault: existing files are
kept byte-identical, a changed reviewed card refuses with the exact
card-replacement message, and nothing is ever deleted or rewritten.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from learning_os.domain.failures import WriteRefused
from learning_os.domain.practice import content_sha256
from learning_os.store.practice import note_items

MARKER_NAME = ".learningos-practice-vault.json"
ATLAS_MARKER = ".los-atlas-fixture"
CHANGED_MESSAGE = (
    "Existing reviewed card differs. "
    "Resolve it through a separate card-replacement workflow."
)
ANCHOR = re.compile(r"^\s*\^learnkit-[\w-]+\s*$")
FORBIDDEN_FIELD = re.compile(r"[|\x00-\x1f\x7f]|^learnkit-|\]\(|://|obsidian:")


def _symlink_components(path: Path) -> str | None:
    aliases = {"/var": "/private/var", "/tmp": "/private/tmp", "/etc": "/private/etc"}
    current = Path(path.anchor) if path.is_absolute() else Path(".")
    for part in path.parts:
        if part == path.anchor:
            continue
        current /= part
        if current.is_symlink():
            if aliases.get(str(current)) == str(current.resolve()):
                continue
            return f"path crosses a symlink: {current}"
    return None


def marker_payload(vault: Path) -> dict:
    path = vault / MARKER_NAME
    if path.is_symlink() or not path.is_file():
        raise WriteRefused("practice vault marker is missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise WriteRefused(f"practice vault marker is unreadable: {exc}") from exc
    if (not isinstance(payload, dict)
            or payload.get("schema_version") != 1
            or payload.get("purpose") != "learnkit-practice"
            or payload.get("experimental") is not True
            or not isinstance(payload.get("vault_id"), str)
            or not payload.get("vault_id")):
        raise WriteRefused("practice vault marker is not the exact experimental marker")
    return payload


def validate_vault(vault: Path, root: Path, *, for_init: bool = False) -> dict | None:
    """Refuse linked, repo-intersecting or wrongly marked destinations."""
    problem = _symlink_components(vault)
    if problem:
        raise WriteRefused(problem)
    resolved = vault.resolve() if vault.exists() else vault.absolute()
    core = root.resolve()
    if resolved == core or core in resolved.parents or resolved in core.parents:
        raise WriteRefused("practice vault intersects the Core repository")
    ancestor = resolved
    while True:
        if (ancestor / ".git").exists():
            raise WriteRefused("practice vault intersects a Git checkout")
        if ancestor.parent == ancestor:
            break
        ancestor = ancestor.parent
    if (vault / ATLAS_MARKER).exists():
        raise WriteRefused("refusing an Atlas fixture as a practice vault")
    cards = vault / "Cards"
    if cards.is_symlink():
        raise WriteRefused("Cards directory is a symlink")
    if for_init:
        return None
    return marker_payload(vault)


def init_vault(vault: Path, root: Path) -> dict:
    """Create the foreign-vault marker in an absent or empty destination."""
    if vault.is_symlink():
        raise WriteRefused("practice vault path is a symlink")
    if vault.exists() and any(vault.iterdir()):
        raise WriteRefused("init requires an absent or empty destination")
    validate_vault(vault, root, for_init=True)
    vault.mkdir(parents=True, exist_ok=True)
    marker = {
        "schema_version": 1,
        "purpose": "learnkit-practice",
        "experimental": True,
        "vault_id": str(uuid.uuid4()),
    }
    (vault / MARKER_NAME).write_text(
        json.dumps(marker, indent=2) + "\n", encoding="utf-8")
    return marker


def card_filename(item_id: str) -> str:
    return hashlib.sha256(item_id.encode("utf-8")).hexdigest()[:24] + ".md"


def _field(text: str, limit: int, what: str) -> str | None:
    value = " ".join(text.split())
    if not value or len(value) > limit:
        return f"{what} must be 1..{limit} single-line characters"
    if FORBIDDEN_FIELD.search(value):
        return f"{what} carries forbidden characters or syntax"
    return None


def card_body(prompt: str, solution: str, item_id: str,
              source_id: str, page: int, concept_ids: list[str]) -> str:
    groups = ", ".join(sorted(set(concept_ids)))
    return (f"Q | {prompt} |\n"
            f"A | {solution} |\n"
            f"I | {item_id} · {source_id} · pdf p. {page} |\n"
            f"G | {groups} |\n")


@dataclass
class CardPlanEntry:
    item_id: str
    path: str
    action: str  # create | keep | changed-existing | refuse
    reason: str | None
    expected_file_sha256: str | None
    body: str | None = field(default=None, repr=False)
    content_sha256: str | None = field(default=None, repr=False)


def _strip_anchor(text: str) -> str | None:
    """The card body in an existing file, or None when malformed."""
    lines = text.split("\n")
    anchors = [line for line in lines if ANCHOR.match(line)]
    if len(anchors) > 1:
        return None
    kept = [line for line in lines if not ANCHOR.match(line) and line.strip()]
    if len(kept) != 4 or not kept[0].startswith("Q | ") \
            or not kept[1].startswith("A | ") or not kept[2].startswith("I | ") \
            or not kept[3].startswith("G | "):
        return None
    return "\n".join(kept) + "\n"


def build_plan(repo, item_ids: list[str], vault: Path) -> list[CardPlanEntry]:
    """One plan entry per selected item, in selection order."""
    by_note: dict[str, tuple[list, list[str]]] = {}
    entries: list[CardPlanEntry] = []
    for item_id in item_ids:
        note_id = item_id.partition("#")[0]
        path = f"Cards/{card_filename(item_id)}"
        if note_id not in by_note:
            note = repo.notes.get(note_id)
            by_note[note_id] = note_items(repo, note) if note else ([], ["unknown note"])
        effective, diagnostics = by_note[note_id]
        entry = next((e for e in effective if e.item.item_id == item_id), None)
        if entry is None:
            entries.append(CardPlanEntry(
                item_id, path, "refuse",
                "; ".join(diagnostics) or "unknown practice item", None))
            continue
        entry.content_sha256 = content_sha256(
            entry.item.item_id, entry.item.prompt, entry.item.solution)
        row = entry.row
        if diagnostics:
            entries.append(CardPlanEntry(
                item_id, path, "refuse",
                "ambiguous parse: " + "; ".join(diagnostics), None))
            continue
        if entry.item.kind != "flashcard":
            entries.append(CardPlanEntry(
                item_id, path, "refuse", "item is not flashcard-shaped", None))
            continue
        if not entry.checked:
            reason = "; ".join(entry.reasons) or f"status is {entry.status}"
            entries.append(CardPlanEntry(
                item_id, path, "refuse", f"item is not checked: {reason}", None))
            continue
        concepts = list((row or {}).get("concept_ids") or [])
        if not concepts or any(cid not in repo.concepts for cid in concepts):
            entries.append(CardPlanEntry(
                item_id, path, "refuse", "item has no canonical concepts", None))
            continue
        bindings = list((row or {}).get("source_bindings") or [])
        if len(bindings) != 1:
            entries.append(CardPlanEntry(
                item_id, path, "refuse",
                "item needs exactly one physical PDF anchor", None))
            continue
        prompt = " ".join(entry.item.prompt.split())
        solution = " ".join(entry.item.solution.split())
        problem = (_field(prompt, 200, "prompt")
                   or _field(solution, 300, "answer"))
        if problem:
            entries.append(CardPlanEntry(item_id, path, "refuse", problem, None))
            continue
        body = card_body(prompt, solution, item_id,
                         bindings[0]["source_id"], int(bindings[0]["page"]), concepts)
        target = vault / path
        if target.is_symlink():
            entries.append(CardPlanEntry(
                item_id, path, "refuse", "card path is a symlink", None))
            continue
        if not target.exists():
            entries.append(CardPlanEntry(
                item_id, path, "create", None,
                hashlib.sha256(body.encode("utf-8")).hexdigest(), body))
            continue
        existing = target.read_text(encoding="utf-8")
        existing_sha = hashlib.sha256(existing.encode("utf-8")).hexdigest()
        stripped = _strip_anchor(existing)
        if stripped is None:
            entries.append(CardPlanEntry(
                item_id, path, "refuse",
                "existing card is malformed or carries extra blocks", None))
        elif stripped == body:
            entries.append(CardPlanEntry(
                item_id, path, "keep", None, existing_sha, body))
        elif f"I | {item_id} · " not in stripped:
            entries.append(CardPlanEntry(
                item_id, path, "refuse",
                "existing card names a different item", None))
        else:
            entries.append(CardPlanEntry(
                item_id, path, "changed-existing", CHANGED_MESSAGE,
                existing_sha, body))
    return entries


def plan_document(repo, item_ids: list[str], vault: Path,
                  marker: dict) -> tuple[dict, list[CardPlanEntry]]:
    from learning_os.store.fingerprint import snapshot as _snapshot

    entries = build_plan(repo, item_ids, vault)
    hashes = {entry.item_id: entry.content_sha256 for entry in entries}
    document = {
        "schema_version": 1,
        "vault_id": marker["vault_id"],
        "snapshot_id": _snapshot(repo.root),
        "selected_ids": list(item_ids),
        "source_content_hashes": hashes,
        "items": [{
            "item_id": entry.item_id,
            "path": entry.path,
            "action": entry.action,
            "reason": entry.reason,
            "expected_file_sha256": entry.expected_file_sha256,
        } for entry in entries],
    }
    return document, entries


def apply_plan(repo, document: dict, vault: Path) -> dict:
    """Publish a checked plan create-only; partial progress is reported."""
    marker = marker_payload(vault)
    if document.get("vault_id") != marker["vault_id"]:
        raise WriteRefused("plan belongs to a different practice vault")
    item_ids = list(document.get("selected_ids") or [])
    _document, entries = plan_document(repo, item_ids, vault, marker)
    planned = {entry["item_id"]: entry
               for entry in document.get("items") or []}
    for entry in entries:
        current = (document.get("source_content_hashes") or {}).get(entry.item_id)
        if entry.content_sha256 != current:
            raise WriteRefused(f"stale plan: {entry.item_id} changed since check")
        planned_entry = planned.get(entry.item_id)
        if planned_entry is None or planned_entry.get("action") != entry.action:
            raise WriteRefused(f"stale plan: {entry.item_id} action changed since check")
    if any(entry.action == "refuse" for entry in entries):
        reasons = "; ".join(
            f"{e.item_id}: {e.reason}" for e in entries if e.action == "refuse")
        raise WriteRefused(f"export blocked before writing: {reasons}")
    if any(entry.action == "changed-existing" for entry in entries):
        raise WriteRefused(CHANGED_MESSAGE)

    cards_dir = vault / "Cards"
    cards_dir.mkdir(exist_ok=True)
    lock_path = cards_dir / ".los-export.lock"
    try:
        lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise WriteRefused("another export holds the destination lock") from None
    created: list[str] = []
    kept: list[str] = []
    try:
        for entry in entries:
            target = vault / entry.path
            if entry.action == "keep":
                if hashlib.sha256(target.read_bytes()).hexdigest() \
                        != entry.expected_file_sha256:
                    raise WriteRefused(
                        f"card changed since check: {entry.item_id}")
                kept.append(entry.item_id)
                continue
            # Create-only publish: stage in Cards, fsync, hardlink (no replace).
            fd, staged = tempfile.mkstemp(dir=cards_dir, prefix=".los-stage-")
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(entry.body or "")
                    handle.flush()
                    os.fsync(handle.fileno())
                try:
                    os.link(staged, target)
                    created.append(entry.item_id)
                except FileExistsError:
                    existing = target.read_text(encoding="utf-8")
                    if _strip_anchor(existing) == entry.body:
                        kept.append(entry.item_id)
                    else:
                        raise WriteRefused(
                            f"card appeared with different content: {entry.item_id}"
                        ) from None
            finally:
                if os.path.exists(staged):
                    os.unlink(staged)
    finally:
        os.close(lock_fd)
        lock_path.unlink(missing_ok=True)
    return {"created": created, "kept": kept,
            "counts": {"created": len(created), "kept": len(kept)}}

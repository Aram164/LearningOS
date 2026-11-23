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
import stat
import uuid
from contextlib import ExitStack
from dataclasses import dataclass, field
from pathlib import Path

from learning_os.domain.failures import WriteRefused
from learning_os.domain.practice import content_sha256
from learning_os.store.fingerprint import snapshot
from learning_os.store.loading import load_repo
from learning_os.store.practice import note_items

MARKER_NAME = ".learningos-practice-vault.json"
ATLAS_MARKER = ".los-atlas-fixture"
CHANGED_MESSAGE = (
    "Existing reviewed card differs. "
    "Resolve it through a separate card-replacement workflow."
)
ANCHOR = re.compile(r"^\s*\^learnkit-[\w-]+\s*$")
FORBIDDEN_FIELD = re.compile(r"[|\x00-\x1f\x7f]|\^learnkit-|\]\(|://|obsidian:", re.IGNORECASE)
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW


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
    return _validate_marker(payload)


def _validate_marker(payload: object) -> dict:
    if (not isinstance(payload, dict)
            or set(payload) != {"schema_version", "purpose", "experimental", "vault_id"}
            or type(payload["schema_version"]) is not int
            or payload["schema_version"] != 1
            or payload["purpose"] != "learnkit-practice"
            or payload["experimental"] is not True):
        raise WriteRefused("practice vault marker is not the exact experimental marker")
    try:
        if str(uuid.UUID(payload["vault_id"])) != payload["vault_id"]:
            raise ValueError("noncanonical UUID")
    except (AttributeError, TypeError, ValueError):
        raise WriteRefused("practice vault marker has an invalid vault ID") from None
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
        if (ancestor / ".git").exists() or (
            (ancestor / "LearningOS/repository/AGENTS.md").is_file()
            and (ancestor / "LearningOS/obsidian-ui/AGENTS.md").is_file()
        ):
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


def write_plan(path: Path, document: dict, root: Path, vault: Path) -> None:
    """Write the report to scratch outside the canonical and practice trees."""
    problem = _symlink_components(path)
    if problem:
        raise WriteRefused(problem)
    target = path.resolve()
    for boundary in (root.resolve(), vault.resolve()):
        if target == boundary or boundary in target.parents:
            raise WriteRefused("export plan must be written outside Core and the practice vault")
    with ExitStack() as stack:
        directory = _open_vault(target.parent, stack)
        for ancestor in target.parents:
            if (ancestor / ".git").exists():
                raise WriteRefused("export plan must be written outside Git checkouts")
        fd = os.open(target.name, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                     0o600, dir_fd=directory)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            if not stat.S_ISREG(os.fstat(fd).st_mode) or os.fstat(fd).st_nlink != 1:
                raise WriteRefused("export plan destination is not an ordinary scratch file")
            handle.truncate(0)
            handle.write(json.dumps(document, indent=2) + "\n")


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
    with (vault / MARKER_NAME).open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(marker, indent=2) + "\n")
    return marker


def card_filename(item_id: str) -> str:
    return hashlib.sha256(item_id.encode("utf-8")).hexdigest()[:24] + ".md"


def _field(text: str, limit: int, what: str) -> str | None:
    if not text or len(text) > limit:
        return f"{what} must be 1..{limit} single-line characters"
    if FORBIDDEN_FIELD.search(text):
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


def _read_regular(name: str | Path, *, directory: int | None = None) -> bytes:
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    with os.fdopen(fd, "rb") as handle:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise WriteRefused("export destination contains a non-regular file")
        return handle.read()


def build_plan(repo, item_ids: list[str], vault: Path, *,
               directory: int | None = None) -> list[CardPlanEntry]:
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
        source_digest = content_sha256(
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
        prompt = entry.item.prompt
        solution = entry.item.solution
        problem = (_field(prompt, 200, "prompt")
                   or _field(solution, 300, "answer"))
        if problem:
            entries.append(CardPlanEntry(item_id, path, "refuse", problem, None))
            continue
        body = card_body(prompt, solution, item_id,
                         bindings[0]["source_id"], int(bindings[0]["page"]), concepts)
        target = vault / path
        try:
            existing = _read_regular(target if directory is None else target.name,
                                     directory=directory)
        except FileNotFoundError:
            entries.append(CardPlanEntry(
                item_id, path, "create", None,
                hashlib.sha256(body.encode("utf-8")).hexdigest(), body, source_digest))
            continue
        except (OSError, WriteRefused):
            entries.append(CardPlanEntry(
                item_id, path, "refuse", "card is linked or unreadable", None))
            continue
        existing_sha = hashlib.sha256(existing).hexdigest()
        try:
            stripped = _strip_anchor(existing.decode("utf-8"))
        except UnicodeDecodeError:
            stripped = None
        if stripped is None:
            entries.append(CardPlanEntry(
                item_id, path, "refuse",
                "existing card is malformed or carries extra blocks", None))
        elif stripped == body:
            entries.append(CardPlanEntry(
                item_id, path, "keep", None, existing_sha, body, source_digest))
        elif not stripped.splitlines()[2].startswith(f"I | {item_id} · "):
            entries.append(CardPlanEntry(
                item_id, path, "refuse",
                "existing card names a different item", None))
        else:
            entries.append(CardPlanEntry(
                item_id, path, "changed-existing", CHANGED_MESSAGE,
                existing_sha, body, source_digest))
    return entries


def plan_document(repo, item_ids: list[str], vault: Path,
                  marker: dict) -> tuple[dict, list[CardPlanEntry]]:
    current = snapshot(repo.root)
    entries = build_plan(repo, item_ids, vault)
    if snapshot(repo.root) != current:
        raise WriteRefused("Core changed during export check; run check again")
    hashes = {entry.item_id: entry.content_sha256 for entry in entries}
    document = {
        "schema_version": 1,
        "vault_id": marker["vault_id"],
        "snapshot_id": current,
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


def _assert_exportable(entries: list[CardPlanEntry]) -> None:
    refusals = [f"{entry.item_id}: {entry.reason}" for entry in entries
                if entry.action == "refuse"]
    if refusals:
        raise WriteRefused(f"export blocked before writing: {'; '.join(refusals)}")
    if any(entry.action == "changed-existing" for entry in entries):
        raise WriteRefused(CHANGED_MESSAGE)


def _check_plan(document: dict, entries: list[CardPlanEntry]) -> None:
    raw_items = document.get("items")
    digests = document.get("source_content_hashes")
    if not isinstance(raw_items, list) or not isinstance(digests, dict):
        raise WriteRefused("export plan is malformed")
    if len(raw_items) != len(entries) or set(digests) != {e.item_id for e in entries}:
        raise WriteRefused("export plan selection changed")
    for expected, entry in zip(raw_items, entries, strict=True):
        if (not isinstance(expected, dict) or expected.get("item_id") != entry.item_id
                or expected.get("path") != entry.path
                or digests[entry.item_id] != entry.content_sha256):
            raise WriteRefused(f"stale plan: {entry.item_id} changed since check")
        action = expected.get("action")
        if action == "create" and entry.action in {"create", "keep"}:
            digest = hashlib.sha256((entry.body or "").encode("utf-8")).hexdigest()
        elif action == entry.action:
            digest = entry.expected_file_sha256
        else:
            raise WriteRefused(f"stale plan: {entry.item_id} action changed since check")
        if expected.get("expected_file_sha256") != digest:
            raise WriteRefused(f"card changed since check: {entry.item_id}")


def _open_vault(vault: Path, stack: ExitStack) -> int:
    # macOS provides the approved /tmp, /var and /etc aliases. After resolving
    # those names, open every component without following any substituted link.
    absolute = Path(os.path.abspath(vault))
    aliases = {"tmp", "var", "etc"}
    parts = absolute.parts[1:]
    if parts and parts[0] in aliases and Path("/", parts[0]).is_symlink():
        parts = ("private", *parts)
    fd = os.open(absolute.anchor, DIRECTORY_FLAGS)
    stack.callback(os.close, fd)
    for part in parts:
        fd = os.open(part, DIRECTORY_FLAGS, dir_fd=fd)
        stack.callback(os.close, fd)
    return fd


def _publish(directory: int, name: str, body: str) -> bool:
    staged = f".los-stage-{uuid.uuid4().hex}"
    fd = os.open(staged, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                 0o600, dir_fd=directory)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(body.encode("utf-8"))
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(staged, name, src_dir_fd=directory, dst_dir_fd=directory,
                    follow_symlinks=False)
            return True
        except FileExistsError:
            existing = _read_regular(name, directory=directory).decode("utf-8")
            if _strip_anchor(existing) != body:
                raise WriteRefused("card appeared with different content") from None
            return False
    finally:
        os.unlink(staged, dir_fd=directory)


def apply_plan(repo, document: dict, vault: Path) -> dict:
    """Recheck under the destination lock and publish approved cards create-only."""
    marker = validate_vault(vault, repo.root)
    if (not isinstance(document, dict) or document.get("schema_version") != 1
            or marker is None or document.get("vault_id") != marker["vault_id"]):
        raise WriteRefused("plan does not match this practice vault and export format")
    item_ids = document.get("selected_ids")
    if (not isinstance(item_ids, list) or not item_ids
            or not all(isinstance(item, str) for item in item_ids)
            or len(set(item_ids)) != len(item_ids)):
        raise WriteRefused("export plan needs distinct selected item IDs")
    expected_snapshot = document.get("snapshot_id")
    if expected_snapshot != snapshot(repo.root):
        raise WriteRefused("Core changed since export check; run check again")
    initial = build_plan(repo, item_ids, vault)
    _assert_exportable(initial)
    _check_plan(document, initial)

    created: list[str] = []
    kept: list[str] = []
    with ExitStack() as stack:
        vault_fd = _open_vault(vault, stack)
        actual_marker = _validate_marker(json.loads(_read_regular(MARKER_NAME, directory=vault_fd)))
        if actual_marker != marker:
            raise WriteRefused("practice vault marker changed since check")
        try:
            os.mkdir("Cards", dir_fd=vault_fd)
        except FileExistsError:
            pass
        directory = os.open("Cards", DIRECTORY_FLAGS, dir_fd=vault_fd)
        stack.callback(os.close, directory)
        lock = ".los-export.lock"
        try:
            lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                              0o600, dir_fd=directory)
        except FileExistsError:
            raise WriteRefused("another export holds the destination lock") from None
        stack.callback(os.unlink, lock, dir_fd=directory)
        stack.callback(os.close, lock_fd)
        if expected_snapshot != snapshot(repo.root):
            raise WriteRefused("Core changed since export check; run check again")
        entries = build_plan(load_repo(repo.root), item_ids, vault, directory=directory)
        _assert_exportable(entries)
        _check_plan(document, entries)
        if expected_snapshot != snapshot(repo.root):
            raise WriteRefused("Core changed during export; run check again")
        for entry in entries:
            name = Path(entry.path).name
            try:
                if entry.action == "keep":
                    digest = hashlib.sha256(_read_regular(name, directory=directory)).hexdigest()
                    if digest != entry.expected_file_sha256:
                        raise WriteRefused("card changed since check")
                    kept.append(entry.item_id)
                elif _publish(directory, name, entry.body or ""):
                    created.append(entry.item_id)
                else:
                    kept.append(entry.item_id)
            except (OSError, UnicodeDecodeError, WriteRefused) as exc:
                raise WriteRefused(
                    f"export interrupted at {entry.item_id}: {exc}. "
                    f"Already created: {', '.join(created) or 'none'}. Run check again."
                ) from exc
    return {"created": created, "kept": kept,
            "counts": {"created": len(created), "kept": len(kept)}}

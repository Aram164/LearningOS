"""Proposal preflight checks on a staged shadow copy (SPEC §11.3).

``check_proposal`` stages the proposal's writes and deletes on a shadow
copy of the canonical roots, validates exactly once, and returns the
reviewable check record. Nothing here commits: the shadow is removed on
the way out. ``_staged_shadow`` is the helper moved from
``commands/module.py``, extended with a ``deletes`` ignore set (deleted
paths are never copied in, so the shadow proves absence without a second
write primitive) and byte-tolerant writes.
"""

from __future__ import annotations

import contextlib
import shutil
import tempfile
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path

from learning_os.loader import load_repo
from learning_os.ops.context import OpContext
from learning_os.ops.proposal import TransactionProposal
from learning_os.revisions import load_revisions
from learning_os.rules import validate
from learning_os.store.fs import _atomic_text
from learning_os.transactions import _atomic_write_bytes, transaction_artifacts
from learning_os.warning_baseline import (
    delta,
    load_baseline,
    signatures_from_issues,
)


@contextlib.contextmanager
def _staged_shadow(root: Path, writes: Mapping[Path, str | bytes],
                   deletes: Iterable[Path] = ()) -> Iterator[Path]:
    """A shadow copy of ``repository/`` carrying planned writes, no canonical I/O.

    Content validation runs here; the real-tree perimeter layer runs against
    ``root`` because the shadow has no wrapper by design.

    ``deletes`` paths are excluded while copying, so the shadow proves
    absence the same way it proves staged content. Byte writes go through
    the engine's atomic byte writer; text writes through the shared atomic
    text writer.
    """
    ignored_at_root = {
        ".git", ".obsidian", ".pytest_cache", ".venv", "generated",
        "migration", "tests", "tools",
    }
    delete_rels: set[str] = set()
    for raw in deletes:
        try:
            delete_rels.add(
                Path(raw).resolve().relative_to(root.resolve()).as_posix())
        except ValueError:
            continue

    def ignore_names(directory, names):
        directory = Path(directory).resolve()
        ignored = {"__pycache__"}
        if directory == root.resolve():
            ignored.update(ignored_at_root)
        if directory == (root / "knowledge").resolve():
            ignored.add("attachments")
        if directory == (root / "curriculum").resolve():
            # Prospective planning is a deliberately opened quarantine. A
            # normal module-plan preflight must not copy or inspect it; a
            # promotion supplies only the exact sanitized catalog write it
            # wants the shadow repository to validate.
            ignored.add("quarantine")
        if delete_rels and directory.is_relative_to(root.resolve()):
            here_rel = directory.relative_to(root.resolve())
            here = "" if str(here_rel) == "." else here_rel.as_posix()
            for name in names:
                candidate = f"{here}/{name}" if here else name
                if any(candidate == doomed or candidate.startswith(doomed + "/")
                       for doomed in delete_rels):
                    ignored.add(name)
        return [name for name in names if name in ignored]

    with tempfile.TemporaryDirectory(prefix="learningos-plan-check-") as tmp:
        shadow = Path(tmp) / "repository"
        shutil.copytree(root, shadow, symlinks=True, ignore=ignore_names)
        attachments = root / "knowledge" / "attachments"
        if attachments.exists():
            link = shadow / "knowledge" / "attachments"
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(attachments, target_is_directory=True)
        for external_name in ("materials", "projects"):
            external = root.parent / external_name
            if external.exists():
                (shadow.parent / external_name).symlink_to(external, target_is_directory=True)
        for path, content in writes.items():
            try:
                rel = path.resolve().relative_to(root.resolve())
            except ValueError:
                raise ValueError(f"planned write escapes repository: {path}") from None
            if isinstance(content, bytes):
                _atomic_write_bytes(shadow / rel, content)
            else:
                _atomic_text(shadow / rel, content)
        yield shadow


def check_proposal(ctx: OpContext, proposal: TransactionProposal) -> dict:
    """Stage the proposal on a shadow copy, validate once, return the record.

    The record carries the capability, the ok flag, the refusal list, the
    staged run's warning regressions against the real tree's baseline, the
    live snapshot, the current revisions for the proposal's artifacts, and
    the sorted relative write/delete lists. Exactly one ``validate`` call;
    the shadow is removed before returning.
    """
    root = ctx.root
    write_rels: list[str] = []
    for path in proposal.writes:
        try:
            rel = Path(path).resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            raise ValueError(
                f"planned write escapes repository: {path}") from None
        write_rels.append(rel)
    delete_rels: list[str] = []
    for path in (proposal.deletes or ()):
        try:
            rel = Path(path).resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            raise ValueError(
                f"planned delete escapes repository: {path}") from None
        delete_rels.append(rel)
    with _staged_shadow(root, proposal.writes, proposal.deletes or ()) as shadow:
        staged_repo = load_repo(shadow)
        issues = validate(staged_repo, online=False)
        if proposal.validate_extra is not None:
            errors = [str(error)
                      for error in proposal.validate_extra(staged_repo, issues)]
        else:
            errors = [str(issue) for issue in issues if issue.severity == "E"]
        signatures, _ = signatures_from_issues(issues)
        baseline, _ = load_baseline(root)
        regressions, _repairs = delta(baseline, signatures)
    revisions = load_revisions(root)
    artifacts = transaction_artifacts(
        root, proposal.artifact_ids, proposal.writes,
        proposal.deletes or ())
    return {
        "schema": 1,
        "capability": proposal.capability,
        "ok": not errors,
        "errors": errors,
        "warnings_delta": regressions,
        "expected_snapshot": ctx.snapshot_id(),
        "expected_revisions": {
            artifact: revisions.get(artifact, 0)
            for artifact in artifacts
        },
        "writes": sorted(write_rels),
        "deletes": sorted(delete_rels),
    }

"""Learner-authored Atlas changes. Every write uses the ordinary V2 transaction."""

from __future__ import annotations

import copy
import json

from learning_os.ops._legacy_plumbing import (
    RELATION_ARTIFACT,
    _operator_lock,
    _registries,
)

from ..domain.failures import WriteRefused
from ..domain.suggest import with_suggestions
from ..fingerprint import canonical_fingerprint
from ..loader import load_repo
from ..revisions import artifact_revision
from .support import (
    _expected_ok,
    _root,
)


def cmd_atlas_context(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        snapshot = "sha256:" + canonical_fingerprint(root)
        if not _expected_ok(root, getattr(args, "expected_snapshot", None)):
            return 3
        repo = load_repo(root)
        if args.concept_id not in repo.concepts:
            raise WriteRefused(with_suggestions(
                f"unknown concept: {args.concept_id}",
                args.concept_id, repo.concepts))
        # This is a scoped editor read, not another full-manifest endpoint.
        rows = [copy.deepcopy(row) for data in _registries(root).values()
                for row in data["relations"]
                if args.concept_id in (row["from"], row["to"])]
        questions = []
        for note in repo.notes.values():
            question = note.meta.get("atlas_question")
            if not isinstance(question, dict):
                continue
            target = question["target"]
            ids = target.get("concepts", []) or [target.get("from"), target.get("to")]
            if args.concept_id in ids:
                questions.append({"id": note.id, "title": note.meta["title"],
                                  "path": note.path.relative_to(root).as_posix(),
                                  "revision": artifact_revision(root, note.id),
                                  **copy.deepcopy(question)})
        if snapshot != "sha256:" + canonical_fingerprint(root):
            raise WriteRefused("snapshot changed while reading Atlas")
        print(json.dumps({"schema_version": 1, "snapshot_id": snapshot,
                          "relation_revision": artifact_revision(root, RELATION_ARTIFACT),
                          "relations": rows, "questions": questions}, ensure_ascii=False))
    return 0

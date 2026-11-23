"""Atlas-area converted handlers (PLAN D4)."""

from __future__ import annotations

import copy
import json
from datetime import UTC, date
from pathlib import Path

import yaml
from jsonschema import ValidationError

from learning_os.app.context import OpContext
from learning_os.app.proposal import Result, TransactionProposal
from learning_os.app.registry import OperationEffects, register
from learning_os.derive import abilities
from learning_os.derive.learning_runtime import runtime_path
from learning_os.domain.failures import NotFound, WriteRefused
from learning_os.domain.suggest import suggest, with_suggestions
from learning_os.store import observations
from learning_os.store.codec import render_frontmatter as _render_frontmatter
from learning_os.store.contracts.atlas_question import (
    QUESTION_FIELDS,
    QUESTION_FIELDS_ORDERED,
    QUESTION_HANDLER_OWNED,
)
from learning_os.store.contracts.gateway import current_gateway_request
from learning_os.store.contracts.json_schema import (
    load_standalone_validator,
    validate_contract,
)
from learning_os.store.fingerprint import snapshot as _snapshot
from learning_os.store.loading.yamlio import UniqueKeySafeLoader
from learning_os.store.revisions import artifact_revision
from learning_os.store.transactions import parse_expected_revisions


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
    validator = load_standalone_validator(
        root / f"system/schema/{name}.schema.json", format_checker=True,
    )
    try:
        validator.validate(data)
    except ValidationError as exc:
        raise WriteRefused(f"{name}: {exc.message}") from exc

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




@register("ability.context", kind="porcelain", effects=OperationEffects.READ)
def ability_context(ctx: OpContext, req: dict) -> Result:
    """Snapshot-bound ability horizon and focused expansion."""
    root = ctx.root
    try:
        if not 1 <= req["limit"] <= 50:
            raise WriteRefused(
                "ability-context limit must be 1..50",
                site="ability.context.bad-limit",
                prefixed=True,
                exit_code=2,
            )
        brief = req.get("brief", False)
        section = req.get("section")
        if brief and not req["ability_id"]:
            raise WriteRefused(
                "ability-context --brief needs a named ability",
                site="ability.context.brief-needs-id",
                prefixed=True,
                exit_code=2,
            )
        if section and not req["ability_id"]:
            raise WriteRefused(
                "ability-context --section needs a named ability",
                site="ability.context.section-needs-id",
                prefixed=True,
                exit_code=2,
            )
        if brief and section:
            raise WriteRefused(
                "ability-context takes --brief or --section evidence, not both",
                site="ability.context.brief-and-section",
                prefixed=True,
                exit_code=2,
            )
        offset = req.get("offset", 0) or 0
        if offset < 0:
            raise WriteRefused(
                "ability-context offset must be nonnegative",
                site="ability.context.negative-offset",
                prefixed=True,
                exit_code=2,
            )
        if req["ability_id"] and offset and not section:
            raise WriteRefused(
                "ability-context --offset pages the global horizon or "
                "--section evidence, not a focused ability",
                site="ability.context.offset-needs-section",
                prefixed=True,
                exit_code=2,
            )
        if brief and req["limit"] != 12:
            # 12 is the parser default: an explicit window on a single
            # summary is silently meaningless, so it refuses instead.
            raise WriteRefused(
                "ability-context --brief is one summary; page evidence with "
                "--section evidence",
                site="ability.context.brief-with-limit",
                prefixed=True,
                exit_code=2,
            )
        if offset and not req["expected_snapshot"]:
            raise WriteRefused(
                "continuation requires --expected-snapshot from the previous "
                "response",
                site="ability.context.offset-needs-snapshot",
                prefixed=True,
                exit_code=2,
            )
        snapshot = _snapshot(root, req["expected_snapshot"])
        repo = ctx.repo()
        if repo.parse_failures:
            raise WriteRefused(
                "ability-context refuses unreadable canonical records",
                site="ability.context.unreadable-records",
                prefixed=True,
                exit_code=2,
            )
        payload = abilities.ability_context(
            repo, focus=req["ability_id"], limit=req["limit"],
            offset=offset, brief=brief, section=section, snapshot=snapshot)
        if (req["ability_id"] is not None
                and req["ability_id"] not in repo.abilities
                and payload.get("state") == "unmapped"):
            # An unknown identity, not a known-but-unmapped ability.
            # The unmapped shape stays what the UI reads (its decoder
            # tolerates extra keys); the flag and suggestions say this
            # is a mistyped id and where to look next.
            payload["known_identity"] = False
            payload["suggestions"] = suggest(req["ability_id"], repo.abilities)
        result = {"schema_version": 1, "snapshot_id": snapshot,
                  "contract": "ability-context-v1", **payload}
        validate_contract(root, "ability-context.schema.json", result)
        rows = payload.get("abilities", [])
        if "ability" in payload:
            rows = [payload["ability"]]
        for row in rows:
            reasons, codes = row.get("reasons"), row.get("reason_codes")
            if not isinstance(reasons, list) or not isinstance(codes, list) \
                    or len(reasons) != len(codes):
                raise WriteRefused(
                    "ability-context reason_codes must be parallel to reasons",
                    site="ability.context.reasons-not-parallel",
                    prefixed=True,
                    exit_code=2,
                )
        _snapshot(root, snapshot)
        return Result(
            {"schema_version": 1, "snapshot_id": snapshot, **result},

        )
    except (OSError, ValueError) as exc:
        raise WriteRefused(
            str(exc),
            prefixed=True,
            exit_code=2,
        ) from exc


@register("ability.candidate.append", kind="command", effects=OperationEffects.CANONICAL_WRITE)
def ability_candidate_append(ctx: OpContext, req: dict) -> Result:
    """Capture a tentative cross-ability connection; it never grants credit."""
    root = ctx.root
    if current_gateway_request() is None:
        raise WriteRefused(
            "ability candidates require GatewayEnvelopeV2",
            site="ability.candidate.append.gateway-required",
            prefixed=True,
            exit_code=2,
        )
    repo = ctx.repo()
    if (req["from_ability"] not in repo.abilities
            or req["to_ability"] not in repo.abilities
            or req["from_ability"] == req["to_ability"]
            or repo.abilities[req["from_ability"]].get("lifecycle") == "retired"
            or repo.abilities[req["to_ability"]].get("lifecycle") == "retired"):
        raise WriteRefused(
            "candidate endpoints must be two active abilities",
            site="ability.candidate.append.bad-endpoints",
            prefixed=True,
            exit_code=2,
        )
    if not req["source_ref"].startswith(
            ("conversation://", "note://", "project://")):
        raise WriteRefused(
            "candidate source-ref must identify the discovery",
            site="ability.candidate.append.bad-source-ref",
            prefixed=True,
            exit_code=2,
        )
    try:
        abilities.read_ability_candidates(repo)
        path = runtime_path(root, root / "knowledge/ability-candidates.jsonl")
        row = {
            "id": "ability-candidate-" + observations.new_hex(),
            "from": req["from_ability"], "to": req["to_ability"],
            "kind": req["kind"], "carries": req["carries"],
            "changes": req["changes"], "conditions": list(req["condition"]),
            "source_ref": req["source_ref"],
            "created_at": observations.now().astimezone(UTC).isoformat(),
            "state": "candidate",
        }
        validator = load_standalone_validator(
            root / "system/schema/ability-candidate.schema.json",
            format_checker=True,
        )
        errors = sorted(validator.iter_errors(row), key=str)
        if errors:
            raise WriteRefused(
                f"ability candidate: {errors[0].message}",
                site="ability.candidate.append.candidate-schema-refused",
                prefixed=True,
                exit_code=2,
            )
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        new = old + ("\n" if old and not old.endswith("\n") else "")
        new += json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
        try:
            expected_revisions = parse_expected_revisions(
                req.get("expected_revision"))
        except ValueError as exc:
            raise WriteRefused(
                str(exc),
                site="ability.candidate.append.bad-expected-revision",
                prefixed=True,
                exit_code=2,
            ) from exc
        return Result(
            {"ok": True, "candidate_id": row["id"]},
            proposal=TransactionProposal(
                capability="ability.candidate.append",
                writes={path: new},
                artifact_ids=["ability-candidates"],
                expected_revisions=expected_revisions,
            ),


        )
    except (OSError, ValueError) as exc:
        raise WriteRefused(
            str(exc),
            prefixed=True,
            exit_code=2,
        ) from exc


@register("atlas.question.save", kind="command", effects=OperationEffects.CANONICAL_WRITE)
def atlas_question_save(ctx: OpContext, req: dict) -> Result:
    """Save or resolve an explicitly authored personal question."""
    root = ctx.root
    question = req["question"]
    if not isinstance(question, dict):
        raise WriteRefused("question must be an object")
    unknown = set(question) - QUESTION_FIELDS
    if unknown:
        raise WriteRefused(
            "question has unknown fields: " + ", ".join(sorted(unknown))
            + f" (accepted: {', '.join(QUESTION_FIELDS_ORDERED)}; "
            + f"{'/'.join(QUESTION_HANDLER_OWNED)} are set by the handler)",
            site="atlas.question.save.unknown-fields",
        )
    if not isinstance(question.get("id"), str):
        raise WriteRefused(
            "question needs a string id",
            site="atlas.question.save.id-not-string",
        )
    if "target" in question and not isinstance(question["target"], dict):
        raise WriteRefused(
            "question target must be an object",
            site="atlas.question.save.target-not-object",
        )
    repo = ctx.repo()
    note_id = question["id"]
    existing = repo.notes.get(note_id)
    if existing:
        if existing.meta.get("role") != "question" or "atlas_question" not in existing.meta:
            raise WriteRefused(
                "this note is not an Atlas question",
                site="atlas.question.save.not-a-question",
            )
        if "target" in question and question["target"] != existing.meta["atlas_question"]["target"]:
            raise WriteRefused(
                "the original question target is preserved",
                site="atlas.question.save.retarget-refused",
            )
        meta, body, path = copy.deepcopy(existing.meta), existing.body, existing.path
    else:
        if not all(key in question for key in ("title", "text", "target")):
            raise WriteRefused(
                "new questions require title, text and target",
                site="atlas.question.save.new-needs-fields",
            )
        meta = {"id": note_id, "type": "note", "role": "question",
                "title": question["title"], "created": observations.today().isoformat(),
                "authorship": "user", "atlas_question": {
                    "state": "open", "target": copy.deepcopy(question["target"])}}
        body = question["text"]
        # Validate id before it can be used as a filename.
        try:
            _schema(root, "note", meta)
        except WriteRefused as exc:
            raise WriteRefused(
                str(exc), site="atlas.question.save.bad-new-note",
            ) from exc
        path = root / "knowledge/notes/questions" / f"{note_id}.md"
        if path.exists():
            raise WriteRefused("question destination already exists")
        target = question["target"]
        concept_ids = target.get("concepts", []) or [target.get("from"), target.get("to")]
        if any(cid not in repo.concepts for cid in concept_ids):
            raise WriteRefused(
                "question target contains an unknown concept",
                site="atlas.question.save.unknown-concept",
            )
        if "from" in target and not any(all(row.get(k) == target[k] for k in ("from", "type", "to")) for row in repo.relations):
            raise WriteRefused(
                "question connection target does not exist",
                site="atlas.question.save.missing-connection",
            )
    _safe(root, path)
    if "title" in question:
        meta["title"] = question["title"]
    if "text" in question:
        if not isinstance(question["text"], str) or not question["text"].strip():
            raise WriteRefused(
                "question text cannot be empty",
                site="atlas.question.save.blank-text",
            )
        body = question["text"]
    for field in ("state", "answer_notes"):
        if field in question:
            meta["atlas_question"][field] = copy.deepcopy(question[field])
    try:
        _schema(root, "note", meta)
    except WriteRefused as exc:
        raise WriteRefused(
            str(exc), site="atlas.question.save.bad-question-fields",
        ) from exc
    for answer in meta["atlas_question"].get("answer_notes", []):
        if answer not in repo.notes or answer == note_id:
            raise WriteRefused(
                "answer note must resolve to another durable note",
                site="atlas.question.save.bad-answer-note",
            )
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="atlas.question.save.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "note_id": note_id,
         "note_path": path.relative_to(root).as_posix()},
        proposal=TransactionProposal(
            capability="atlas.question.save",
            writes={path: _render_frontmatter(meta, body)},
            artifact_ids=[note_id],
            expected_revisions=expected_revisions,
        ),


    )


#: The Atlas keeper (ADR-024 §Amendment 2026-11-23): an agent running a
#: bounded job writes relations on this channel, under Aram's standing
#: delegation, and Aram vetoes or pins afterwards in the app.
KEEPER_CHANNEL = "system-task"
KEEPER_DELEGATION = "system/contracts/delegations/atlas-keeper.yaml"
_DELEGATION_KEYS = frozenset({
    "schema_version", "delegate", "granted_by", "granted", "expires",
    "status", "capability", "channel", "max_operations",
})


def _keeper_refused(reason: str, site: str) -> WriteRefused:
    return WriteRefused(reason, site=f"concept.relations.change.{site}")


def _keeper_delegation(root: Path) -> dict:
    """The active delegation, or a refusal naming why there is none.

    Every keeper receipt records the `system-task` channel and its commit
    time. The delegation is Git-tracked, so a committed delegation can be
    matched to a write by time; an uncommitted edit in force at write time is
    not recorded (its digest waits for a receipt field in the next format).
    """
    path = root / KEEPER_DELEGATION

    def inactive(why: str) -> WriteRefused:
        return _keeper_refused(
            f"the Atlas keeper has no active delegation: {why}", "keeper-delegation")

    if path.is_symlink() or not path.is_file():
        raise inactive(f"{KEEPER_DELEGATION} is missing")
    raw = path.read_bytes()
    try:
        data = yaml.load(raw.decode("utf-8"), Loader=UniqueKeySafeLoader)
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        raise inactive(f"{KEEPER_DELEGATION} is unreadable ({exc})") from exc
    if (not isinstance(data, dict) or set(data) != _DELEGATION_KEYS
            or data["schema_version"] != 1
            or data["capability"] != "concept.relations.change"
            or data["channel"] != KEEPER_CHANNEL
            or type(data["max_operations"]) is not int
            or not 1 <= data["max_operations"] <= 50
            or not isinstance(data["expires"], date)
            or not isinstance(data["granted"], date)):
        raise inactive(f"{KEEPER_DELEGATION} does not have the declared shape")
    if data["status"] != "active":
        raise inactive(f"its status is {data['status']}")
    today = observations.now().date()
    if not data["granted"] <= today <= data["expires"]:
        raise inactive(f"it covers {data['granted']} to {data['expires']}, not {today}")
    return data


def _keeper_scope(operations: list, delegation: dict) -> None:
    """Refuse what the keeper may not do; Aram's decisions stay his."""
    if len(operations) > delegation["max_operations"]:
        raise _keeper_refused(
            f"the keeper's delegation allows at most {delegation['max_operations']} "
            "operations per batch", "keeper-scope")
    for operation in operations:
        kind = operation["action"]
        old = operation.get("old") if isinstance(operation.get("old"), dict) else {}
        new = operation.get("new") if isinstance(operation.get("new"), dict) else {}
        if kind == "remove":
            raise _keeper_refused(
                "the keeper retracts a relation with a reason; it never deletes one",
                "keeper-scope")
        if old.get("pinned") is True or old.get("origin") == "aram":
            raise _keeper_refused(
                "relations Aram authored or pinned are his; the keeper may only "
                "report a conflict with them", "keeper-scope")
        if new.get("pinned") is True or new.get("status") == "vetoed" \
                or new.get("evidence_disputed", False) != old.get("evidence_disputed", False):
            raise _keeper_refused(
                "pinning, vetoing and disputing evidence are Aram's decisions",
                "keeper-scope")
        if new.get("origin", "pilot") != old.get("origin", "pilot"):
            raise _keeper_refused(
                "the keeper writes relations as origin pilot and never changes "
                "a relation's origin", "origin-mismatch")
        if new.get("status", "active") == "active" and not new.get("evidence"):
            raise _keeper_refused(
                "an active keeper relation must cite at least one verified quote "
                "from the course materials", "keeper-evidence")


@register("concept.relations.change", kind="command", effects=OperationEffects.CANONICAL_WRITE)
def concept_relations_change(ctx: OpContext, req: dict) -> Result:
    """Apply only explicitly authored relation operations.

    The app (`ui`) records Aram's own additions as origin `aram`. The Atlas
    keeper (`system-task`) writes only under an active delegation, only with
    verified evidence, never over a pinned or Aram-authored row, and its
    additions are stamped origin `pilot`.
    """
    root = ctx.root
    changes = req["change"]
    if not isinstance(changes, dict) or set(changes) != {"operations"}:
        raise WriteRefused(
            "change must contain only operations",
            site="concept.relations.change.change-not-operations",
        )
    operations = changes["operations"]
    if not isinstance(operations, list) or not 1 <= len(operations) <= 50:
        raise WriteRefused(
            "supply between 1 and 50 explicit operations",
            site="concept.relations.change.empty-operations",
        )
    request = current_gateway_request()
    channel = request.channel if request is not None else None
    if channel == KEEPER_CHANNEL:
        delegation = _keeper_delegation(root)
        for operation in operations:
            if not isinstance(operation, dict) or not isinstance(operation.get("action"), str):
                break  # the per-operation checks below refuse it precisely
        else:
            _keeper_scope(operations, delegation)
    registries = _registries(root)
    repo = ctx.repo()
    from learning_os.domain.relations import is_decorated

    def _stamped(new_row: dict) -> dict:
        """An added row with its author recorded (who made it, not who kept it)."""
        author = {"ui": "aram", KEEPER_CHANNEL: "pilot"}.get(channel)
        if author is None:
            return copy.deepcopy(new_row)
        if new_row.get("origin", author) != author:
            raise _keeper_refused(
                f"a relation added through {channel} is recorded as origin {author}",
                "origin-mismatch")
        return {**copy.deepcopy(new_row), "origin": author}

    def _check_evidence(row: dict) -> None:
        # Known source + current digest + the quote verbatim on the pinned
        # page, through the existing span machinery (plan step 6).
        from learning_os.store.practice import verified_binding

        for binding in row.get("evidence") or []:
            problem = verified_binding(repo, binding)
            if problem:
                raise WriteRefused(
                    problem,
                    site="concept.relations.change.evidence-refused",
                )

    changed = set()
    for operation in operations:
        if not isinstance(operation, dict):
            raise WriteRefused(
                "operation must be an object",
                site="concept.relations.change.operation-not-object",
            )
        kind = operation.get("action")
        required = {"add": {"action", "new"}, "replace": {"action", "old", "new"},
                    "remove": {"action", "old"}}.get(kind)
        if required is None or set(operation) != required:
            raise WriteRefused(
                "expected exact add, replace, or remove operation",
                site="concept.relations.change.inexact-operation",
            )
        for key in ("old", "new"):
            if key in operation:
                try:
                    _schema(root, "concept-relations", {"relations": [operation[key]]})
                except WriteRefused as exc:
                    raise WriteRefused(
                        str(exc),
                        site="concept.relations.change.bad-relation-row",
                    ) from exc
        if "new" in operation:
            _check_evidence(operation["new"])
            new_row = operation["new"]
            if new_row.get("status") in ("retracted", "vetoed"):
                reason = str(new_row.get("status_reason", ""))
                if not reason.strip() or len(reason.strip()) > 400:
                    raise WriteRefused(
                        "retract/veto requires a 1-400 character reason",
                        site="concept.relations.change.reason-required",
                    )
        if "old" in operation:
            matches = [(path, i) for path, data in registries.items()
                       for i, row in enumerate(data["relations"]) if row == operation["old"]]
            if len(matches) != 1:
                raise WriteRefused(
                    "the exact previous relation no longer exists uniquely; reload and review",
                    site="concept.relations.change.old-not-found",
                )
            path, index = matches[0]
            old_row = operation["old"]
            if old_row.get("pinned"):
                unpin = (kind == "replace"
                         and {**operation["new"]} == {**old_row, "pinned": False})
                if not unpin:
                    raise WriteRefused(
                        "a pinned relation only accepts an exact unpin toggle",
                        site="concept.relations.change.pinned-row",
                    )
            if kind == "remove" and is_decorated(old_row):
                raise WriteRefused(
                    "decorated relations are retracted, not hard-deleted",
                    site="concept.relations.change.decorated-remove",
                )
            if (kind == "replace" and old_row.get("status") == "vetoed"
                    and operation["new"].get("status", "active") == "active"):
                old_sources = {b.get("source_id")
                               for b in old_row.get("evidence") or []}
                fresh = [b for b in operation["new"].get("evidence") or []
                         if b.get("source_id") not in old_sources]
                if not fresh:
                    raise WriteRefused(
                        "restoring a vetoed relation requires fresh evidence "
                        "from a previously unused registered source",
                        site="concept.relations.change.restore-needs-fresh-evidence",
                    )
            if kind == "remove":
                registries[path]["relations"].pop(index)
            else:
                registries[path]["relations"][index] = copy.deepcopy(operation["new"])
        else:
            single = root / "knowledge/concept-relations.yaml"
            path = single if single in registries else root / "knowledge/concept-relations/atlas.yaml"
            _safe(root, path)
            registries.setdefault(path, {"relations": []})["relations"].append(_stamped(operation["new"]))
        changed.add(path)
    writes = {path: yaml.safe_dump(registries[path], sort_keys=False, allow_unicode=True)
              for path in changed}
    # Existing validator rejects duplicates, unknown endpoints/sources and prerequisite cycles.
    try:
        expected_revisions = parse_expected_revisions(req.get("expected_revision"))
    except ValueError as exc:
        raise WriteRefused(
            str(exc), site="concept.relations.change.bad-expected-revision",
        ) from exc
    return Result(
        {"ok": True, "operation_count": len(operations)},
        proposal=TransactionProposal(
            capability="concept.relations.change",
            writes=writes,
            artifact_ids=[RELATION_ARTIFACT],
            expected_revisions=expected_revisions,
        ),


    )


@register("atlas.context", kind="porcelain", effects=OperationEffects.READ)
def atlas_context(ctx: OpContext, req: dict) -> Result:
    """Read connection editor guards and personal questions for one concept."""
    root = ctx.root
    snapshot = _snapshot(root, req.get("expected_snapshot"))
    repo = ctx.repo()
    if req["concept_id"] not in repo.concepts:
        complaint = with_suggestions(
            f"unknown concept: {req['concept_id']}",
            req["concept_id"], repo.concepts)
        raise NotFound(
            "concept", req["concept_id"], repo.concepts,
            message=complaint,
            site="atlas.context.unknown-concept",
        )
    # This is a scoped editor read, not another full-manifest endpoint.
    rows = [copy.deepcopy(row) for data in _registries(root).values()
            for row in data["relations"]
            if req["concept_id"] in (row["from"], row["to"])]
    questions = []
    for note in repo.notes.values():
        question = note.meta.get("atlas_question")
        if not isinstance(question, dict):
            continue
        target = question["target"]
        ids = target.get("concepts", []) or [target.get("from"), target.get("to")]
        if req["concept_id"] in ids:
            questions.append({"id": note.id, "title": note.meta["title"],
                              "path": note.path.relative_to(root).as_posix(),
                              "revision": artifact_revision(root, note.id),
                              **copy.deepcopy(question)})
    if _snapshot(root) != snapshot:
        raise WriteRefused(
            "snapshot changed while reading Atlas",
            site="atlas.context.snapshot-changed",
        )
    return Result(
        {"schema_version": 1, "snapshot_id": snapshot,
         "relation_revision": artifact_revision(root, RELATION_ARTIFACT),
         "relations": rows, "questions": questions},

    )

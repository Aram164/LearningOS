"""Seal one GatewayEnvelopeV2 in process (WORKFLOWS §25c).

``tools/seal_envelope.py`` is the command line over the guard derivation
here. Its ``--submit`` uses the same code to seal an envelope and submit it
in one call (agent-cost PLAN D1). Sealing in process adds no authority. On the operator channel the approval subject is
the operator's assertion, not proof that a human was present, so the gateway
computing ``intent_sha256`` asserts nothing that a caller computing it did
not. The sealed envelope then passes every gateway guard unchanged.

A one-call write keeps its sealed envelope in a per-key retry file in the
checkout's process-state directory. After a lost response, a retry with the
same key and payload resubmits the exact committed request, and the gateway
replays it instead of seeing a new intent under a used key. The file is
retry state only. Deleting it loses exact replay for that key (such a retry
then refuses as ``IDEMPOTENCY_CONFLICT``), never data. It is not canonical,
not committed and not backed up.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from pathlib import Path

from learning_os.app.registry import REGISTRY
from learning_os.store.contracts.gateway import GATEWAY_SCHEMA_VERSION, intent_sha256
from learning_os.store.fingerprint import canonical_fingerprint

# capability-envelope.schema.json bounds request_id at 128 characters.
REQUEST_ID_MAX = 128


def fresh_request_id(key: str) -> str:
    """Mint a new request id for this sealing run (WORKFLOWS §25c step 4).

    Each sealing run is a new attempt with its own key, so a key-derived id is
    never needed. An exact retry does not come back here: it resubmits the
    envelope this run already produced, because replay binds the committed
    request id and refuses a re-sealed envelope under a used key.
    """
    suffix = secrets.token_hex(4)
    stem = key[:REQUEST_ID_MAX - len("request--") - len(suffix)]
    return f"request-{stem}-{suffix}"


def load_payload(spec: str) -> dict:
    """A payload given inline as JSON, or as ``@PATH`` to a JSON file."""
    text = Path(spec[1:]).read_text(encoding="utf-8") if spec.startswith("@") else spec
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"payload is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    return payload


class _DryRunCapture(Exception):
    """The dry-run handler reached the transaction boundary with this set."""

    def __init__(self, artifacts: list[str]):
        super().__init__("dry run reached the transaction boundary")
        self.artifacts = artifacts


def derive_guards_auto(root: Path, *, capability: str, payload: dict,
                       key: str, request_id: str, channel: str,
                       approval_kind: str, snapshot: str | None,
                       parser_factory) -> tuple[str, dict[str, int]]:
    """Derive the exact guard set with a gateway dry run.

    Runs the capability's own handler through the gateway's ``_dispatch``
    — the same payload validation, the same namespace, the same handler —
    with the transaction service stubbed to capture the artifact set and
    stop before any write. Returns the snapshot and the artifact set bound
    to the revision ledger read under the same operator lock, so the two
    answer the same instant and a concurrent canonical change still
    refuses the sealed envelope as ``STALE_SNAPSHOT``.

    This adds no authority: the dry run commits nothing, and the sealed
    envelope passes through every gateway guard unchanged.
    """
    from learning_os.app.gateway import dispatch as _dispatch
    from learning_os.app.lock import operator_lock as _operator_lock
    from learning_os.domain.failures import WriteRefused
    from learning_os.store.contracts.capability_catalog import command_definitions
    from learning_os.store.contracts.gateway import (
        GatewayRequestContext,
        gateway_request_context,
        verified_gateway_snapshot,
    )
    from learning_os.store.revisions import load_revisions
    from learning_os.store.transactions import transaction_artifacts

    definitions = command_definitions(root)
    if capability not in definitions:
        raise ValueError(f"unknown capability: {capability}")
    from learning_os.store.contracts.payloads import subparsers as _subparsers

    command_parser = _subparsers(parser_factory()).get(
        definitions[capability].cli_command or "")
    if command_parser is None:
        raise ValueError(
            f"capability {capability} declares no CLI command to derive guards from")
    if command_parser.get_default("func") is None:
        raise ValueError(
            f"capability {capability} has no bound handler to derive guards from")

    # Intercept at the class, not at one module's import of it: a handler
    # may commit through ``support._write_transaction`` or through its own
    # ``from learning_os.store.transactions import TransactionService`` (the AI
    # delivery path does). Patching one module's name would let the second
    # kind reach the real ``commit`` — with this dry run's placeholder
    # approval — so the boundary is the method every instance shares.
    from learning_os.store import transactions as _transactions

    real_commit = _transactions.TransactionService.commit

    def _dry_run_commit(self, *, artifact_ids=(), writes=None, deletes=(),
                        **_ignored):
        raise _DryRunCapture(transaction_artifacts(
            self.root, artifact_ids, writes or {}, deletes))

    # The request identities are the envelope's own: request-scoped
    # artifacts (capture, garden) derive from the idempotency key, so the
    # dry run must carry the key the envelope will be sealed under. The
    # intent hash is a placeholder — the stubbed boundary never checks
    # approval, and the real envelope's approval is computed afterwards
    # over the derived guards.
    context = GatewayRequestContext(
        request_id=request_id,
        idempotency_key=key,
        capability=capability,
        channel=channel,
        intent_sha256="sha256:" + "0" * 64,
        approval_kind=approval_kind,
        approval_subject_sha256="sha256:" + "0" * 64,
        expected_snapshot=None,  # set once the snapshot below is read
    )
    envelope_stub = {
        "schema_version": GATEWAY_SCHEMA_VERSION,
        "capability": capability,
        "expected_snapshot": snapshot,
        "expected_revisions": {},
    }
    _transactions.TransactionService.commit = _dry_run_commit  # type: ignore[method-assign]
    try:
        with _operator_lock(root):
            # The snapshot is a content digest, not a loaded-domain
            # property: the path-based walk answers it without parsing the
            # repository, and the dry-run handler below loads once for its
            # own planner. Same digest, same lock, one load and one walk.
            live_snapshot = snapshot or f"sha256:{canonical_fingerprint(root)}"
            envelope_stub["expected_snapshot"] = live_snapshot
            context = GatewayRequestContext(
                request_id=context.request_id,
                idempotency_key=context.idempotency_key,
                capability=context.capability,
                channel=context.channel,
                intent_sha256=context.intent_sha256,
                approval_kind=context.approval_kind,
                approval_subject_sha256=context.approval_subject_sha256,
                expected_snapshot=live_snapshot,
            )
            with gateway_request_context(context), verified_gateway_snapshot(
                    root, live_snapshot):
                try:
                    code, result = _dispatch(
                        root, definitions[capability], envelope_stub, payload,
                        parser_factory=parser_factory)
                except _DryRunCapture as captured:
                    revisions = load_revisions(root)
                    return live_snapshot, {
                        artifact: revisions.get(artifact, 0)
                        for artifact in captured.artifacts
                    }
                except WriteRefused as exc:
                    raise ValueError(
                        f"{exc}; fix the payload and seal again") from exc
            if code == 2:
                # The handler refused the payload itself (an unknown id, a
                # failed check): explicit guards cannot fix that, so say so
                # instead of sending the caller on a second refused round trip.
                raise ValueError(
                    f"{result.get('error', capability + ' failed')}; "
                    "fix the payload and seal again")
            raise ValueError(
                "guard derivation stopped before any transaction"
                f" (exit {code}: {result.get('error', capability + ' failed')}); "
                "seal this payload with explicit --revision guards instead")
    finally:
        _transactions.TransactionService.commit = real_commit  # type: ignore[method-assign]


def derive_registered_guards(root: Path, *, capability: str, payload: dict,
                             key: str, request_id: str, channel: str,
                             approval_kind: str, snapshot: str | None,
                             parser_factory, check_out: str | None = None,
                             preflight: bool = True) -> tuple[str, dict[str, int]]:
    """Derive the guard set for a registered operation through the pipeline.

    The same admission (``prepare_dispatch``), namespace-to-request
    filtering, gateway request context and lock/snapshot discipline as the
    gateway's registered compute step, but the handler's proposal is
    checked once with ``check_proposal`` instead of committed. The record
    supplies the snapshot and revision guards; with ``check_out`` the
    record (plus the sealing payload) is written even when the check
    fails, so the reviewer reads the refusal. No transaction interception:
    a registered handler returns its proposal rather than committing.

    ``preflight=False`` skips the staged-shadow check. The guards never
    came from it: they are the revision ledger read for the proposal's
    artifact set under this lock. The one-call write uses it, because its
    commit validates the real tree anyway, and the shadow check would
    only run the same rules a second time on a copy of the repository.
    """
    from learning_os.app.check import check_proposal
    from learning_os.app.context import OpContext
    from learning_os.app.gateway import prepare_dispatch
    from learning_os.app.lock import operator_lock as _operator_lock
    from learning_os.domain.failures import WriteRefused
    from learning_os.store.contracts.capability_catalog import command_definitions
    from learning_os.store.contracts.gateway import (
        GatewayRequestContext,
        gateway_request_context,
        verified_gateway_snapshot,
    )
    from learning_os.store.contracts.requests import request_schema

    definitions = command_definitions(root)
    if capability not in definitions:
        raise ValueError(f"unknown capability: {capability}")
    from learning_os.store.contracts.payloads import subparsers as _subparsers

    command_parser = _subparsers(parser_factory()).get(
        definitions[capability].cli_command or "")
    if command_parser is None:
        raise ValueError(
            f"capability {capability} declares no CLI command to derive guards from")
    if command_parser.get_default("func") is None:
        raise ValueError(
            f"capability {capability} has no bound handler to derive guards from")

    operation = REGISTRY[capability]
    envelope_stub = {
        "schema_version": GATEWAY_SCHEMA_VERSION,
        "capability": capability,
        "expected_snapshot": snapshot,
        "expected_revisions": {},
    }
    context = GatewayRequestContext(
        request_id=request_id,
        idempotency_key=key,
        capability=capability,
        channel=channel,
        intent_sha256="sha256:" + "0" * 64,
        approval_kind=approval_kind,
        approval_subject_sha256="sha256:" + "0" * 64,
        expected_snapshot=None,  # set once the snapshot below is read
    )
    with _operator_lock(root):
        # SPEC (co): one context, one walk. The context is built before
        # the snapshot read so the seal reuses its cached walk; the check
        # record below then reads the same cached token instead of
        # walking again. An explicit caller snapshot never seeds the
        # cache: the record keeps its independent walk.
        ctx = OpContext(
            root=root,
            operation=capability,
            channel=channel,
            invocation="check",
            gateway=context,
        )
        live_snapshot = snapshot or ctx.snapshot_id()
        envelope_stub["expected_snapshot"] = live_snapshot
        context = GatewayRequestContext(
            request_id=context.request_id,
            idempotency_key=context.idempotency_key,
            capability=context.capability,
            channel=context.channel,
            intent_sha256=context.intent_sha256,
            approval_kind=context.approval_kind,
            approval_subject_sha256=context.approval_subject_sha256,
            expected_snapshot=live_snapshot,
        )
        ctx.gateway = context
        with gateway_request_context(context), verified_gateway_snapshot(
                root, live_snapshot):
            try:
                _, namespace = prepare_dispatch(
                    root, definitions[capability], envelope_stub, payload,
                    parser_factory=parser_factory)
            except WriteRefused as exc:
                raise ValueError(
                    f"{exc}; fix the payload and seal again") from exc
            properties = request_schema(root, capability).get(
                "properties", {})
            req = {name: value for name, value in vars(namespace).items()
                   if name in properties}
            try:
                res = operation.handler(ctx, req)
            except WriteRefused as exc:
                raise ValueError(
                    f"{exc}; fix the payload and seal again") from exc
            if res.proposal is None:
                if check_out:
                    raise ValueError(
                        "--check-out requires a registered operation "
                        "returning a proposal")
                raise ValueError(
                    "guard derivation stopped before any transaction "
                    f"({capability} returned no proposal); seal this payload "
                    "with explicit --revision guards instead")
            if not preflight:
                if req.get("check") is True:
                    raise ValueError(
                        "a check payload never commits; run the command's "
                        "own --check instead of a one-call write")
                from learning_os.store.revisions import load_revisions
                from learning_os.store.transactions import transaction_artifacts

                revisions = load_revisions(root)
                artifacts = transaction_artifacts(
                    root, res.proposal.artifact_ids, res.proposal.writes,
                    res.proposal.deletes or ())
                return live_snapshot, {
                    artifact: revisions.get(artifact, 0)
                    for artifact in artifacts
                }
            record = check_proposal(ctx, res.proposal)
    if check_out is not None:
        sealing = {name: value for name, value in payload.items()
                   if name != "check"}
        Path(check_out).write_text(
            json.dumps({**record, "payload": sealing}, indent=2,
                       sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8")
    if record["ok"] is not True:
        errors = record.get("errors") or ["the check failed"]
        raise ValueError(
            f"{'; '.join(errors)}; fix the payload and seal again")
    if check_out is None and req.get("check") is True:
        # A check never commits: the legacy dry run of a passing check
        # stopped before any transaction and advised explicit guards
        # (SPEC (bd) item 5). A check record (--check-out) is the reviewed
        # journey and keeps its guards.
        raise ValueError(
            "guard derivation stopped before any transaction"
            f" (exit 0: {capability} failed); "
            "seal this payload with explicit --revision guards instead")
    return snapshot or record["expected_snapshot"], dict(
        record["expected_revisions"])




def retry_path(root: Path, key: str) -> Path:
    """Where the sealed envelope for ``key`` is kept for an exact retry."""
    from learning_os.store.session_ledger import process_state_dir

    # The root is part of the name because roots without a git directory
    # (synthetic repositories) share the temp-dir state location.
    name = hashlib.sha256(f"{root.resolve()}\n{key}".encode()).hexdigest()[:40]
    return process_state_dir(root) / "sealed-requests" / f"{name}.json"


def seal_with_key(root: Path, *, capability: str, payload: dict, key: str,
                  parser_factory, channel: str = "operator",
                  approval_kind: str = "operator-approval",
                  session_id: str | None = None,
                  request_id: str | None = None) -> dict:
    """The sealed envelope for one operator write under idempotency ``key``.

    If ``key`` already committed this exact capability and payload, the
    stored envelope is returned unchanged, so the gateway replays the
    original receipt. Otherwise a fresh envelope is sealed against the live
    snapshot, with guards derived the way ``seal_envelope.py --guards auto``
    derives them, minus the staged-shadow check (the commit validates once),
    and stored before it is returned. A used key with a different payload
    is sealed fresh and refused by the gateway as ``IDEMPOTENCY_CONFLICT``.
    """
    from learning_os.store.evidence import load_idempotency_entries
    from learning_os.store.fs import atomic_text

    path = retry_path(root, key)
    committed = load_idempotency_entries(root).get(key)
    if committed is not None and path.is_file():
        stored = json.loads(path.read_text(encoding="utf-8"))
        if stored.get("capability") == capability and stored.get("payload") == payload \
                and intent_sha256(stored) == committed.get("intent_sha256"):
            return stored
    request_id = request_id or fresh_request_id(key)
    common = dict(capability=capability, payload=payload, key=key,
                  request_id=request_id, channel=channel,
                  approval_kind=approval_kind, snapshot=None,
                  parser_factory=parser_factory)
    if capability in REGISTRY:
        snapshot, revisions = derive_registered_guards(root, preflight=False, **common)
    else:
        snapshot, revisions = derive_guards_auto(root, **common)
    envelope = {
        "schema_version": GATEWAY_SCHEMA_VERSION,
        "request_id": request_id,
        "idempotency_key": key,
        "capability": capability,
        "channel": channel,
        **({"session_id": session_id} if session_id is not None else {}),
        "expected_snapshot": snapshot,
        "expected_revisions": revisions,
        "payload": payload,
    }
    envelope["approval"] = {"kind": approval_kind,
                            "subject_sha256": intent_sha256(envelope)}
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_text(path, json.dumps(envelope, indent=2, sort_keys=True,
                                ensure_ascii=False) + "\n")
    return envelope

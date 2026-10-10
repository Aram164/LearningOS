"""AI-area handlers: ``ai-action.delivery.apply`` (PLAN D4, SPEC §12 R5, (be)) and ``cli.ai-action-list``, ``cli.ai-action-status``, ``cli.ai-action-prepare``, ``cli.ai-action-append-slices``, ``cli.ai-action-validate-delivery`` (SPEC §12)."""

from __future__ import annotations

import dataclasses
import json

from learning_os.ai_actions import (
    AIActionError,
    AIActionService,
    DeliveryBindingError,
    DeliveryIdempotencyConflict,
    DeliveryRevisionConflict,
    DeliveryScopeError,
    StaleDeliveryError,
)
from learning_os.contracts.gateway import current_gateway_request
from learning_os.domain.codes import IDEMPOTENCY_CONFLICT, OUT_OF_SCOPE, UNCONFIRMED
from learning_os.domain.failures import (
    IdempotencyConflict,
    OutOfScope,
    RevisionConflict,
    StaleSnapshot,
    Unconfirmed,
    WriteRefused,
)
from learning_os.ops._legacy_plumbing import _publish, _record_touched
from learning_os.ops.context import OpContext
from learning_os.ops.proposal import Result
from learning_os.ops.registry import register
from learning_os.transactions import parse_expected_revisions

#: The typed refusal for each ``_ai_refusal`` code (SPEC (be) item 1).
_TYPED = {
    OUT_OF_SCOPE: OutOfScope,
    IDEMPOTENCY_CONFLICT: IdempotencyConflict,
    UNCONFIRMED: Unconfirmed,
}


def _ai_refusal(exc: AIActionError) -> tuple[str, bool] | None:
    """Map a delivery failure to its V2 ``(code, retryable)`` by type.

    Stale deliveries never reach this helper — the handler records them
    beside its exit-3 return. ``None`` is an untyped validation failure,
    which the gateway reports as ``INVALID_REQUEST``.
    """
    if isinstance(exc, DeliveryScopeError):
        return (OUT_OF_SCOPE, False)
    if isinstance(exc, DeliveryIdempotencyConflict):
        return (IDEMPOTENCY_CONFLICT, False)
    if isinstance(exc, DeliveryBindingError):
        return (UNCONFIRMED, False)
    return None


def _refusal(exc: AIActionError, operation: str) -> WriteRefused:
    """The old command wrapper's catch, as a typed refusal (SPEC §12, (ac), (be)).

    It printed ``str(exc)`` (the captured complaint) and returned 3 for a
    stale delivery, recording ``REVISION_CONFLICT`` or ``STALE_SNAPSHOT``,
    else 2 with the ``_ai_refusal`` code, or untyped.
    """
    message = str(exc)
    if isinstance(exc, StaleDeliveryError):
        typed = (RevisionConflict if isinstance(exc, DeliveryRevisionConflict)
                 else StaleSnapshot)
        return typed(message, gateway_message=message.strip(), exit_code=3)
    refusal = _ai_refusal(exc)
    if refusal is None:
        return WriteRefused(message, gateway_message=message.strip(),
                            exit_code=2)
    typed = _TYPED[refusal[0]]
    assert typed.gateway_retryable is refusal[1]
    site = (f"{operation}.binding" if isinstance(exc, DeliveryBindingError)
            else None)
    return typed(message, site=site, gateway_message=message.strip(),
                 exit_code=2)


def _dumps_delivery(payload: dict) -> str:
    """The exact delivery encoder: indented, unescaped."""
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _delivery_output(receipt: dict) -> dict:
    """The command's success JSON from the service's receipt."""
    return {
        "ok": True,
        "transaction_id": receipt["transaction_id"],
        "receipt_path": receipt["receipt_path"],
        "snapshot_after": receipt["snapshot_after"],
        "artifact_revisions": receipt["revision_updates"],
        "replayed": receipt.get("replayed", False),
        "receipt": receipt,
    }


@register("ai-action.delivery.apply", kind="command")
def ai_action_apply_delivery(ctx: OpContext, req: dict) -> Result:
    """Apply an approved AI delivery in one receipted transaction."""
    root = ctx.root
    authority = current_gateway_request()
    if authority is None:
        raise WriteRefused(
            "approved delivery application must use GatewayEnvelopeV2"
        )
    if authority.capability != "ai-action.delivery.apply" \
            or authority.approval_kind != "approved-delivery":
        raise Unconfirmed(
            "ai-action.delivery.apply requires approved-delivery approval"
        )
    try:
        service = AIActionService(root)
        try:
            expected_revisions = parse_expected_revisions(
                req.get("expected_revision"))
        except ValueError as exc:
            raise WriteRefused(str(exc)) from exc
        proposal, replayed, touched_base = service.apply_delivery_proposal(
            req["delivery_id"],
            delivery_sha256=req["delivery_sha256"],
            artifact_sha256=req["artifact_sha256"],
            expected_snapshot=req["expected_snapshot"],
            expected_revisions=expected_revisions,
        )
    except AIActionError as exc:
        raise _refusal(exc, ctx.operation) from exc
    if proposal is None:
        # A replay: nothing commits and nothing was touched.
        replayed.pop("touched_paths", [])
        return Result(_delivery_output(replayed), json_dumps=_dumps_delivery)
    prepared: dict = {}

    def translate(exc: BaseException) -> BaseException | None:
        translated = AIActionService._translate_commit_failure(exc)
        return None if translated is None else _refusal(translated, ctx.operation)

    def after_commit(code, errors, confirmation):
        # The service's receipt read and the command's touched bookkeeping,
        # once, after a successful commit, under the same lock (az) S15 3.
        if code != 0:
            return
        receipt = service.apply_delivery_receipt(confirmation, touched_base)
        touched = [root / rel for rel in receipt.pop("touched_paths", [])]
        if touched:
            _record_touched(root, touched)
        prepared["receipt"] = receipt

    def finish(confirmation):
        return _delivery_output(prepared["receipt"])

    return Result(
        {"delivery_id": req["delivery_id"]},
        proposal=dataclasses.replace(proposal, translate=translate),
        after_commit=after_commit,
        finish=finish,
        json_dumps=_dumps_delivery,
    )


@register("cli.ai-action-list", kind="tool")
def ai_action_list(ctx: OpContext, req: dict) -> Result:
    """List the provider-independent AI actions."""
    actions = AIActionService(ctx.root).list_actions()
    return Result({"ok": True, "actions": actions},
                  json_dumps=_dumps_delivery)


@register("cli.ai-action-status", kind="tool")
def ai_action_status(ctx: OpContext, req: dict) -> Result:
    """Show one prepared request status."""
    request = AIActionService(ctx.root).request_status(req["request_id"])
    return Result({"ok": True, "request": request},
                  json_dumps=_dumps_delivery)


@register("cli.ai-action-prepare", kind="porcelain")
def ai_action_prepare(ctx: OpContext, req: dict) -> Result:
    """Persist a bounded AI request bundle."""
    root = ctx.root
    service = AIActionService(root)
    request = service.prepare(
        action_id=req["action_id"], target_kind=req["target_kind"],
        target_id=req["target_id"], provider=req.get("provider"),
        expected_snapshot=req.get("expected_snapshot"),
        request_id=req.get("request_id"),
    )
    _publish(root)
    return Result({
        "ok": True, "request": service.request_status(request["id"]),
        "bundle_path": service.repository.request_dir(
            request["id"]).relative_to(root).as_posix(),
    }, json_dumps=_dumps_delivery)


@register("cli.ai-action-append-slices", kind="porcelain")
def ai_action_append_slices(ctx: OpContext, req: dict) -> Result:
    """Attach one targeted follow-up slice pass to a prepared request."""
    root = ctx.root
    service = AIActionService(root)
    result = service.append_slices(
        request_id=req["request_id"], route_id=req["route_id"],
        start=req["start"], end=req["end"], kind=req["kind"],
        concept_ids=req.get("concept_id") or [], reason=req["reason"],
        material_uri=req.get("material_uri"),
        expected_snapshot=req.get("expected_snapshot"),
    )
    _publish(root)
    return Result({"ok": True, "continuation": result},
                  json_dumps=_dumps_delivery)


@register("cli.ai-action-validate-delivery", kind="tool")
def ai_action_validate_delivery(ctx: OpContext, req: dict) -> Result:
    """Validate one imported delivery without applying it."""
    result = AIActionService(ctx.root).validate_delivery(req["delivery_id"])
    return Result(result, json_dumps=_dumps_delivery)

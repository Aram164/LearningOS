"""CLI validation and projection publication, executed in process."""
from learning_os.app.context import OpContext
from learning_os.app.projection import publish
from learning_os.app.proposal import Result
from learning_os.app.registry import OperationEffects, register
from learning_os.app.validation import validation_run


def validation_text(payload: dict) -> str:
    status = "FAIL" if payload["errors"] else "OK"
    return "\n".join([*payload["issues"], "",
        f"{payload['errors']} error(s), {payload['warnings']} warning(s) — {status}"])


def generation_text(payload: dict) -> str:
    return "published generated/manifest.json (atomic contract snapshot)"


@register("repository.validate", kind="tool", human=validation_text, effects=OperationEffects.DERIVED_WRITE)
def validate_command(ctx: OpContext, req: dict) -> Result:
    payload = validation_run(ctx.root, online=bool(req.get("online")))
    return Result(payload, diagnostic_failed=bool(payload["errors"]))


@register("projection.generate", kind="porcelain", human=generation_text, effects=OperationEffects.DERIVED_WRITE)
def generate_command(ctx: OpContext, req: dict) -> Result:
    publish(ctx.root)
    return Result({"ok": True, "published": "generated/manifest.json"})

"""Task IR P1: four typed operations compiled into existing Core machinery.

Experimental and narrow by design. A task spec names typed operations over
existing canonical IDs; this module validates the spec, compiles its reads
into one agent plan for the existing runner, and drives the single writable
operation (``route.patch``) through the existing reviewed seal flow
(``seal_envelope.py --guards auto --check-out`` at preview, then
``--guards-from ... --submit`` at apply). No new approval format, no new
transaction engine, no new session entity, and no ``los`` verbs are added:
the runner mode in ``tools/agent_run.py`` is the only new surface.

Operation mapping (effects always come from the registry classification of
the underlying operation, never from a name):

- ``context.inspect`` -> ``inspect`` (``project.inspect``, read): one known
  unit, stage, route, or record ID.
- ``material.find`` -> ``plan-edit-context`` (``plan.edit-context``, read):
  the typed routes of one known unit, or of one stage of it. Lexical
  explanation search (``material-context``) stays a direct call in P1.
- ``session.propose`` -> ``runtime-session`` (``runtime.session``, read):
  the requirement ID is derived with
  :func:`learning_os.derive.learning_runtime.requirement_id_for`; no
  requirement store is invented.
- ``route.patch`` -> ``route.patch`` (canonical-write): preview plus one
  guarded canonical write through the Gateway.

Typed references only: an operation input may name an earlier operation's
documented output through ``{"from_operation": ..., "field": ...}``.
String expression languages (``$steps[...]`` and friends) are refused.

Idempotency: the spec digest is the SHA-256 of the runner's canonical form
(:func:`learning_os.app.agent_reporting.encode`) of the normalized spec.
Reusing a ``request_id`` with a different digest is an error. The write
operation's idempotency key and gateway request ID are derived once at
preview, persisted in the run evidence keyed by ``(request_id,
operation_id)``, and looked up on every retry: apply resubmits through the
saved check record and the gateway's kept envelope, never resealing against
a fresh snapshot, and an uncertain dispatch is never redispatched.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from learning_os.app import handlers as _handlers  # noqa: F401  (registration)
from learning_os.app.agent_reporting import encode
from learning_os.app.registry import REGISTRY, OperationEffects
from learning_os.derive.learning_runtime import requirement_id_for
from learning_os.domain.material_refs import PATCH_FIELDS

TOOLS = Path(__file__).resolve().parents[2]

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_OP_ID = re.compile(r"^[a-z][a-z0-9-]{0,63}$")

#: The one writable workflow P1 supports: exactly one route.patch per spec.
MAX_OPERATIONS = 16

#: Documented typed outputs per operation (the only fields a reference may
#: name). Reads expose identifiers and the snapshot they were read at; the
#: write exposes its receipt-backed evidence.
OUTPUTS: dict[str, tuple[str, ...]] = {
    "context.inspect": ("record_id", "snapshot_id"),
    "material.find": ("route_id", "route_ids", "snapshot_id"),
    "session.propose": ("requirement_id", "snapshot_id"),
    "route.patch": ("route_id", "receipt_path", "transaction_id"),
}

#: IR operation -> underlying registry operation whose declared effects
#: classify the IR operation.
UNDERLYING: dict[str, str] = {
    "context.inspect": "project.inspect",
    "material.find": "plan.edit-context",
    "session.propose": "runtime.session",
    "route.patch": "route.patch",
}


class TaskSpecError(ValueError):
    """A task spec, reference, or persisted run state is invalid."""

    def __init__(self, message: str, code: str = "TASK_IR_INVALID") -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class RouteRef:
    """A route identity: one literal canonical ID or one typed reference."""

    literal: str | None = None
    from_operation: str | None = None


@dataclass(frozen=True)
class Operation:
    id: str
    op: str
    unit_id: str | None = None
    stage_id: str | None = None
    route_id: str | None = None
    record_id: str | None = None
    route_ref: RouteRef | None = None
    set_fields: dict[str, str] = field(default_factory=dict)
    claim_evidence: dict[str, object] | None = None
    context: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class TaskSpec:
    request_id: str
    session_id: str
    operations: tuple[Operation, ...]
    normalized: dict[str, object]


@dataclass(frozen=True)
class CompiledTask:
    plan: dict[str, object]
    write: Operation | None
    read_ids: tuple[str, ...]


def _fail(message: str, code: str = "TASK_IR_INVALID") -> TaskSpecError:
    return TaskSpecError(message, code)


def _text(raw: dict[str, object], name: str, op_id: str, *,
          required: bool = False) -> str | None:
    value = raw.get(name)
    if value is None:
        if required:
            raise _fail(f"operation {op_id}: {name} is required")
        return None
    if not isinstance(value, str) or not value.strip():
        raise _fail(f"operation {op_id}: {name} must be a nonempty string")
    return value


def _route_ref(raw: dict[str, object], op_id: str,
               earlier: dict[str, Operation]) -> RouteRef:
    has_literal = "route_id" in raw
    has_ref = "route_ref" in raw
    if has_literal == has_ref:
        raise _fail(f"operation {op_id}: name exactly one of route_id or route_ref")
    if has_literal:
        value = raw["route_id"]
        if not isinstance(value, str) or not value.strip():
            raise _fail(f"operation {op_id}: route_id must be a nonempty string")
        return RouteRef(literal=value)
    ref = raw["route_ref"]
    if not isinstance(ref, dict) or set(ref) != {"from_operation", "field"}:
        raise _fail(f"operation {op_id}: route_ref must name from_operation and field")
    source, field_name = ref["from_operation"], ref["field"]
    if not isinstance(source, str) or source not in earlier:
        raise _fail(f"operation {op_id}: route_ref names unknown or later operation {source!r}",
                    "TASK_IR_BAD_REFERENCE")
    if field_name != "route_id" or field_name not in OUTPUTS[earlier[source].op]:
        raise _fail(f"operation {op_id}: operation {source} exposes no route_id output",
                    "TASK_IR_BAD_REFERENCE")
    return RouteRef(from_operation=source)


def _operation(raw: object, earlier: dict[str, Operation]) -> Operation:
    if not isinstance(raw, dict):
        raise _fail("each operation must be an object")
    op_id = raw.get("id")
    if not isinstance(op_id, str) or not _OP_ID.fullmatch(op_id):
        raise _fail("operation id must match ^[a-z][a-z0-9-]{0,63}$")
    if op_id in earlier:
        raise _fail(f"duplicate operation id: {op_id}")
    op = raw.get("op")
    if op not in OUTPUTS:
        raise _fail(f"operation {op_id}: unknown op {op!r}")
    allowed = {"id", "op"}
    if op == "context.inspect":
        allowed |= {"record_id", "unit_id", "stage_id", "route_id"}
        record = raw.get("record_id") or raw.get("route_id") or raw.get("stage_id") or raw.get("unit_id")
        if not isinstance(record, str) or not record.strip():
            raise _fail(f"operation {op_id}: context.inspect needs a known unit, stage, route, or record id")
        return Operation(id=op_id, op=op, record_id=record)
    if op == "material.find":
        allowed |= {"unit_id", "stage_id"}
        return Operation(id=op_id, op=op,
                         unit_id=_text(raw, "unit_id", op_id, required=True),
                         stage_id=_text(raw, "stage_id", op_id))
    if op == "session.propose":
        allowed |= {"unit_id", "stage_id", "context"}
        context = raw.get("context", {})
        if not isinstance(context, dict):
            raise _fail(f"operation {op_id}: context must be an object")
        return Operation(id=op_id, op=op,
                         unit_id=_text(raw, "unit_id", op_id, required=True),
                         stage_id=_text(raw, "stage_id", op_id, required=True),
                         context=dict(context))
    allowed |= {"unit_id", "route_id", "route_ref", "set_fields", "claim_evidence"}
    route_ref = _route_ref(raw, op_id, earlier)
    set_fields = raw.get("set_fields")
    if not isinstance(set_fields, dict) or not set_fields:
        raise _fail(f"operation {op_id}: set_fields must be a nonempty object")
    for key, value in set_fields.items():
        if key not in PATCH_FIELDS:
            raise _fail(f"operation {op_id}: set_fields field {key!r} is not a declared material field")
        if not isinstance(value, str) or not value.strip():
            raise _fail(f"operation {op_id}: set_fields.{key} must be nonempty text")
    evidence = raw.get("claim_evidence")
    if evidence is not None and not isinstance(evidence, dict):
        raise _fail(f"operation {op_id}: claim_evidence must be an object")
    extra = set(raw) - allowed
    if extra:
        raise _fail(f"operation {op_id}: undeclared field(s): {', '.join(sorted(extra))}")
    return Operation(id=op_id, op=op,
                     unit_id=_text(raw, "unit_id", op_id, required=True),
                     route_ref=route_ref, set_fields=dict(set_fields),
                     claim_evidence=dict(evidence) if evidence is not None else None)


def _reject_expressions(value: object) -> None:
    if isinstance(value, str) and ("$" in value or value.startswith("{")):
        raise _fail("string expressions are not typed references; use route_ref", "TASK_IR_BAD_REFERENCE")
    if isinstance(value, dict):
        for item in value.values():
            _reject_expressions(item)
    if isinstance(value, list):
        for item in value:
            _reject_expressions(item)


def parse_spec(raw: object) -> TaskSpec:
    """Validate one task spec; the only admission path for task IR input."""
    if not isinstance(raw, dict):
        raise _fail("task spec must be a JSON object")
    extra = set(raw) - {"schema_version", "request_id", "session_id", "operations"}
    if extra:
        raise _fail(f"undeclared spec field(s): {', '.join(sorted(extra))}")
    if raw.get("schema_version") != 1:
        raise _fail("task spec schema_version must be 1")
    request_id = raw.get("request_id")
    if not isinstance(request_id, str) or not _ID.fullmatch(request_id) or len(request_id) > 128:
        raise _fail("request_id must match ^[A-Za-z0-9][A-Za-z0-9._:-]*$ (max 128)")
    session_id = raw.get("session_id", f"task-{request_id}")
    if not isinstance(session_id, str) or not session_id.strip() or len(session_id) > 128:
        raise _fail("session_id must be a nonempty string (max 128)")
    raw_ops = raw.get("operations")
    if not isinstance(raw_ops, list) or not 1 <= len(raw_ops) <= MAX_OPERATIONS:
        raise _fail(f"operations must hold 1..{MAX_OPERATIONS} operations")
    _reject_expressions(raw_ops)
    operations: dict[str, Operation] = {}
    ordered: list[Operation] = []
    for item in raw_ops:
        operation = _operation(item, operations)
        operations[operation.id] = operation
        ordered.append(operation)
    writes = [item for item in ordered if item.op == "route.patch"]
    if len(writes) > 1:
        raise _fail("P1 admits exactly one canonical transaction: at most one route.patch")
    for operation in ordered:
        entry = REGISTRY.get(UNDERLYING[operation.op])
        if entry is None:
            raise _fail(f"underlying operation is not registered: {UNDERLYING[operation.op]}")
        expected = (OperationEffects.CANONICAL_WRITE if operation.op == "route.patch"
                    else OperationEffects.READ)
        if entry.effects != expected:
            raise _fail(f"{UNDERLYING[operation.op]} is classified {entry.effects}, not {expected}; refusing to infer effects")
    normalized: dict[str, object] = {
        "schema_version": 1, "request_id": request_id, "session_id": session_id,
        "operations": json.loads(encode(raw_ops)),
    }
    return TaskSpec(request_id=request_id, session_id=session_id,
                    operations=tuple(ordered), normalized=normalized)


def spec_digest(spec: TaskSpec) -> str:
    """SHA-256 of the runner's canonical form of the normalized spec."""
    return "sha256:" + hashlib.sha256(encode(spec.normalized).encode("utf-8")).hexdigest()


def operation_key(request_id: str, operation_id: str) -> str:
    """The write key derived once at preview for (request_id, operation_id)."""
    digest = hashlib.sha256(encode([request_id, operation_id]).encode("utf-8")).hexdigest()
    return f"task-{digest[:40]}"


def compile_spec(spec: TaskSpec) -> CompiledTask:
    """Compile reads into one agent plan; the write stays a seal intent.

    Deterministic: the same spec compiles to the same plan bytes. The write
    is not a plan step because the runner submits only presealed envelopes;
    P1 keeps sealing in the reviewed preview/apply flow instead of
    inventing plan syntax for it.
    """
    steps: list[dict[str, object]] = []
    write: Operation | None = None
    for operation in spec.operations:
        if operation.op == "route.patch":
            write = operation
            continue
        depends = ([operation.route_ref.from_operation] if operation.route_ref
                   and operation.route_ref.from_operation else [])
        if operation.op == "context.inspect":
            steps.append({"id": operation.id, "argv": ["inspect", str(operation.record_id)],
                          "summary": {"fields": ["id", "type"], "max_items": 5, "max_bytes": 2000}})
        elif operation.op == "material.find":
            argv = ["plan-edit-context", str(operation.unit_id)]
            fields = ["snapshot_id", "routes"]
            if operation.stage_id:
                argv += ["--stage-id", operation.stage_id]
                fields = ["snapshot_id", "stage.resources"]
            steps.append({"id": operation.id, "argv": argv, "depends_on": depends,
                          "summary": {"fields": fields, "max_items": 20, "max_bytes": 8000}})
        else:
            requirement = requirement_id_for(str(operation.unit_id), str(operation.stage_id))
            steps.append({"id": operation.id,
                          "argv": ["runtime-session", "--requirement", requirement,
                                   "--context-json", encode(operation.context)],
                          "summary": {"fields": ["snapshot_id", "contract"],
                                      "max_items": 5, "max_bytes": 2000}})
    plan: dict[str, object] = {"schema_version": 2, "session_id": spec.session_id,
                               "on_error": "stop", "steps": steps}
    return CompiledTask(plan=plan, write=write,
                        read_ids=tuple(op.id for op in spec.operations
                                       if op.op != "route.patch"))


def resolve_route(compiled: CompiledTask, outputs: dict[str, dict[str, object]]) -> str:
    """Bind the write's route from a literal ID or an earlier find output."""
    write = compiled.write
    if write is None or write.route_ref is None:
        raise _fail("compiled task has no route.patch to bind")
    if write.route_ref.literal is not None:
        return write.route_ref.literal
    source = outputs.get(str(write.route_ref.from_operation), {})
    route_id = source.get("route_id")
    if not isinstance(route_id, str) or not route_id:
        raise _fail("material.find did not resolve to exactly one route; refusing to guess",
                    "TASK_IR_UNRESOLVED_ROUTE")
    return route_id


def write_payload(write: Operation, route_id: str) -> dict[str, object]:
    payload: dict[str, object] = {"unit_id": write.unit_id, "route_id": route_id,
                                  "changes": dict(write.set_fields)}
    if write.claim_evidence is not None:
        payload["claim_evidence"] = write.claim_evidence
    return payload


ReadRunner = Callable[[dict[str, object], Path], dict[str, object]]
SealCheck = Callable[[Path, dict[str, object], str, Path], tuple[int, str, str]]
SealSubmit = Callable[[Path, Path, dict[str, object], str, str], tuple[int, str, str]]


def _run_seal(argv: list[str]) -> tuple[int, str, str]:
    proc = subprocess.run(argv, capture_output=True, text=True, timeout=600)
    return proc.returncode, proc.stdout, proc.stderr


def default_seal_check(root: Path, payload: dict[str, object], key: str,
                       record_path: Path) -> tuple[int, str, str]:
    return _run_seal([sys.executable, str(TOOLS / "seal_envelope.py"), "--root", str(root),
                      "--capability", "route.patch", "--payload", encode(payload),
                      "--key", key, "--guards", "auto", "--check-out", str(record_path)])


def default_seal_submit(root: Path, record_path: Path, payload: dict[str, object],
                        key: str, request_id: str) -> tuple[int, str, str]:
    return _run_seal([sys.executable, str(TOOLS / "seal_envelope.py"), "--root", str(root),
                      "--capability", "route.patch", "--payload", encode(payload),
                      "--key", key, "--request-id", request_id,
                      "--guards-from", str(record_path), "--submit"])


def _evidence_path(evidence_dir: Path, request_id: str) -> Path:
    name = hashlib.sha256(request_id.encode("utf-8")).hexdigest()[:32]
    return evidence_dir / f"task-{name}.json"


def _save_evidence(path: Path, evidence: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(encode(evidence) + "\n", encoding="utf-8")
    tmp.replace(path)


def _load_evidence(path: Path, spec: TaskSpec) -> dict[str, object] | None:
    if not path.is_file():
        return None
    try:
        evidence = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise _fail(f"run evidence is unreadable: {path}", "TASK_IR_EVIDENCE") from exc
    if not isinstance(evidence, dict) or evidence.get("request_id") != spec.request_id:
        raise _fail("run evidence belongs to another request", "TASK_IR_EVIDENCE")
    if evidence.get("spec_digest") != spec_digest(spec):
        raise _fail("request_id was already used with a different spec", "TASK_IR_REQUEST_CONFLICT")
    return evidence


def _outputs_from_report(spec: TaskSpec, report: dict[str, object]) -> dict[str, dict[str, object]]:
    raw_steps = report.get("steps")
    rows: dict[str, dict[str, object]] = {}
    if isinstance(raw_steps, list):
        for item in raw_steps:
            if isinstance(item, dict):
                rows[str(item.get("id"))] = cast(dict[str, object], item)
    outputs: dict[str, dict[str, object]] = {}
    for operation in spec.operations:
        if operation.op == "route.patch":
            continue
        row: dict[str, object] = rows.get(operation.id, {})
        raw_output = row.get("output")
        output: dict[str, object] = raw_output if isinstance(raw_output, dict) else {}
        if operation.op == "context.inspect":
            outputs[operation.id] = {"record_id": operation.record_id,
                                     "snapshot_id": output.get("snapshot_id"),
                                     "status": row.get("status")}
        elif operation.op == "material.find":
            route_ids: list[str] = []
            stage = output.get("stage")
            if isinstance(stage, dict) and isinstance(stage.get("resources"), list):
                route_ids = [str(item["route_id"]) for item in stage["resources"]
                             if isinstance(item, dict) and item.get("route_id")]
            raw_routes = output.get("routes")
            if isinstance(raw_routes, list):
                route_ids = [str(item["id"]) for item in raw_routes
                             if isinstance(item, dict) and item.get("id")]
            route_ids = list(dict.fromkeys(route_ids))
            outputs[operation.id] = {
                "route_ids": route_ids,
                "route_id": route_ids[0] if len(route_ids) == 1 else None,
                "snapshot_id": output.get("snapshot_id"), "status": row.get("status")}
        else:
            outputs[operation.id] = {
                "requirement_id": requirement_id_for(str(operation.unit_id), str(operation.stage_id)),
                "snapshot_id": output.get("snapshot_id"), "status": row.get("status")}
    return outputs


def _record_changes(record: dict[str, object]) -> dict[str, object] | None:
    """The previewed per-field changes from a seal check record, if carried."""
    for value in record.values():
        if isinstance(value, dict):
            changes = value.get("changes")
            if isinstance(changes, dict):
                return changes
            nested = _record_changes(value)
            if nested is not None:
                return nested
    return None


def preview_task(root: Path, spec: TaskSpec, evidence_dir: Path, *,
                 run_reads: ReadRunner,
                 seal_check: SealCheck = default_seal_check) -> dict[str, object]:
    """Run reads and the reviewed check; zero canonical writes, zero receipts."""
    if evidence_dir.resolve().is_relative_to(root.resolve()):
        raise _fail("evidence directory must live outside the data root", "TASK_IR_EVIDENCE")
    evidence_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = _evidence_path(evidence_dir, spec.request_id)
    prior = _load_evidence(path, spec)
    if prior is not None and prior.get("status") in ("committed", "uncertain"):
        return _report(spec, prior, resumed=True)
    compiled = compile_spec(spec)
    empty_report: dict[str, object] = {"steps": [], "totals": {"ok": 0, "steps": 0}}
    report = run_reads(compiled.plan, root) if compiled.read_ids else empty_report
    outputs = _outputs_from_report(spec, report)
    operations: list[dict[str, object]] = []
    for operation in spec.operations:
        if operation.op == "route.patch":
            continue
        status = outputs[operation.id].get("status")
        operations.append({"id": operation.id, "op": operation.op,
                           "status": "ok" if status == "ok" else "refused",
                           "outputs": {k: v for k, v in outputs[operation.id].items()
                                       if k != "status"}})
    evidence: dict[str, object] = {
        "request_id": spec.request_id, "spec_digest": spec_digest(spec),
        "status": "previewed", "operations": operations, "outputs": outputs,
    }
    if compiled.write is not None:
        write = compiled.write
        failed_read = next((row for row in operations if row["status"] != "ok"), None)
        if failed_read is not None:
            operations.append({"id": write.id, "op": write.op, "status": "refused",
                               "outputs": {}, "error": "a read it depends on did not complete"})
            evidence["status"] = "partial"
        else:
            try:
                route_id = resolve_route(compiled, outputs)
            except TaskSpecError as exc:
                operations.append({"id": write.id, "op": write.op, "status": "refused",
                                   "outputs": {}, "error": str(exc), "code": exc.code})
                evidence["status"] = "partial"
            else:
                payload = write_payload(write, route_id)
                key = operation_key(spec.request_id, write.id)
                record_path = evidence_dir / f"task-{spec.request_id}-{write.id}.check.json"
                code, _out, err = seal_check(root, payload, key, record_path)
                if code != 0 and "no material changes to apply" in err:
                    # The existing machinery itself refuses a no-change patch
                    # before any write; that refusal is the unchanged proof.
                    evidence.update({"key": key, "payload": payload, "route_id": route_id})
                    operations.append({"id": write.id, "op": write.op,
                                       "status": "unchanged",
                                       "outputs": {"route_id": route_id}})
                    evidence["status"] = "unchanged"
                elif code != 0 or not record_path.is_file():
                    operations.append({"id": write.id, "op": write.op, "status": "refused",
                                       "outputs": {"route_id": route_id},
                                       "error": (err.strip().splitlines() or ["preview check failed"])[-1]})
                    evidence["status"] = "partial"
                else:
                    record = json.loads(record_path.read_text(encoding="utf-8"))
                    changes = _record_changes(record)
                    unchanged = changes is not None and not changes
                    evidence.update({"key": key, "gateway_request_id": f"request-{key}",
                                     "payload": payload, "check_record": str(record_path),
                                     "route_id": route_id})
                    operations.append({"id": write.id, "op": write.op,
                                       "status": "unchanged" if unchanged else "needs_review",
                                       "outputs": {"route_id": route_id}})
                    evidence["status"] = "unchanged" if unchanged else "needs_review"
    _save_evidence(path, evidence)
    return _report(spec, evidence)


def _committed_receipt(root: Path, key: str) -> dict[str, object] | None:
    from learning_os.store.evidence import load_idempotency_entries

    entry = load_idempotency_entries(root).get(key)
    if entry is None:
        return None
    return {"transaction_id": entry.get("transaction_id"),
            "receipt_path": entry.get("receipt_path")}


def apply_task(root: Path, spec: TaskSpec, evidence_dir: Path, *,
               seal_submit: SealSubmit = default_seal_submit) -> dict[str, object]:
    """Apply the previewed write once; retries look up, never redispatch blind."""
    if evidence_dir.resolve().is_relative_to(root.resolve()):
        raise _fail("evidence directory must live outside the data root", "TASK_IR_EVIDENCE")
    path = _evidence_path(evidence_dir, spec.request_id)
    evidence = _load_evidence(path, spec)
    if evidence is None:
        raise _fail("no preview evidence for this request; run preview first", "TASK_IR_NO_PREVIEW")
    if evidence.get("status") in ("committed", "uncertain", "unchanged"):
        return _report(spec, evidence, resumed=True)
    if evidence.get("status") != "needs_review":
        return _report(spec, evidence, resumed=True)
    compiled = compile_spec(spec)
    assert compiled.write is not None  # needs_review is only set with a write
    key = str(evidence["key"])
    record_path = Path(str(evidence["check_record"]))
    payload = evidence["payload"]
    if not isinstance(payload, dict) or not record_path.is_file():
        raise _fail("preview evidence is incomplete", "TASK_IR_EVIDENCE")
    evidence["status"] = "dispatched"
    _save_evidence(path, evidence)

    def settle(status: str, **extra: object) -> dict[str, object]:
        raw_operations = evidence.get("operations")
        operations: list[object] = [dict(row) if isinstance(row, dict) else row
                                    for row in raw_operations] \
            if isinstance(raw_operations, list) else []
        for row in operations:
            if isinstance(row, dict) and row.get("op") == "route.patch":
                row["status"] = status
        evidence.update({"status": status, "operations": operations, **extra})
        _save_evidence(path, evidence)
        return _report(spec, evidence)
    try:
        code, out, err = seal_submit(root, record_path, payload, key,
                                     str(evidence["gateway_request_id"]))
    except Exception as exc:  # dispatch may have crossed the commit boundary
        return settle("uncertain", error=f"dispatch interrupted: {exc}")
    if code == 0:
        result = json.loads(out) if out.strip() else {}
        receipt = {"transaction_id": result.get("transaction_id"),
                   "receipt_path": result.get("receipt_path"),
                   "replayed": result.get("replayed") is True}
        if not receipt["receipt_path"] or not (root / str(receipt["receipt_path"])).is_file():
            return settle("uncertain",
                          error="gateway reported success without a receipt on disk")
        return settle("committed", receipt=receipt)
    recovered = _committed_receipt(root, key)
    if recovered is not None:
        return settle("committed", receipt=recovered)
    detail = (err.strip().splitlines() or [out.strip() or "gateway refused the write"])[-1]
    return settle("refused", error=detail)


def _report(spec: TaskSpec, evidence: dict[str, object], *,
            resumed: bool = False) -> dict[str, object]:
    operations = evidence.get("operations", [])
    status = str(evidence.get("status", "refused"))
    report: dict[str, object] = {
        "schema_version": 1, "kind": "task-ir-p1", "request_id": spec.request_id,
        "spec_digest": evidence.get("spec_digest"), "status": status,
        "operations": operations, "resumed": resumed,
    }
    if evidence.get("receipt") is not None:
        report["receipt"] = evidence["receipt"]
    if evidence.get("error") is not None:
        report["error"] = evidence["error"]
    return report

"""GatewayEnvelopeV2 admission: envelope and payload validation, and approval-bound file inputs."""

from __future__ import annotations

import contextlib
import errno
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from learning_os.domain.failures import WriteRefused
from learning_os.store import observations
from learning_os.store.contracts.gateway import (
    GatewayRequestContext,
    current_gateway_request,
    intent_sha256,
)
from learning_os.store.materials.reading_cards import protected_reads
from learning_os.store.session_ledger import DEFAULT_SESSION_CHANNEL

STUDY_FENCE_CORE_ENV = "LOS_STUDY_FENCE_CORE"
STUDY_FENCE_SCRATCH_ENV = "LOS_STUDY_FENCE_SCRATCH"
STUDY_STAGED_MANIFEST_ENV = "LOS_STUDY_STAGED_MANIFEST"


def _real_path(raw_path: Path | str, *, cwd: Path | None = None) -> Path:
    expanded = Path(raw_path).expanduser()
    if not expanded.is_absolute() and cwd is not None:
        expanded = cwd / expanded
    return Path(os.path.realpath(expanded))


def _is_within(candidate: Path, base: Path) -> bool:
    real_base = Path(os.path.realpath(base))
    return candidate == real_base or real_base in candidate.parents


def _lexical_study_path(
    raw_path: str,
    *,
    cwd: Path | None = None,
    label: str = "file input",
) -> Path:
    if not isinstance(raw_path, str) or not raw_path.strip() or raw_path == "-" or "\x00" in raw_path:
        raise WriteRefused(f"study mode requires a concrete path for {label}")
    expanded = Path(raw_path).expanduser()
    if not expanded.is_absolute():
        expanded = (cwd if cwd is not None else Path.cwd()) / expanded
    return Path(os.path.abspath(expanded))


def _match_study_anchor(
    raw_path: str,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path | None = None,
    label: str = "file input",
    allow_core: bool = True,
) -> tuple[Path, Path, tuple[str, ...]]:
    """Anchor a caller path onto scratch_dir or core_root without resolving sub-tree symlinks."""
    lex = _lexical_study_path(raw_path, cwd=cwd, label=label)
    real_core = Path(os.path.realpath(core_root))
    protected = tuple(Path(os.path.realpath(closed)) for closed in protected_reads(real_core))

    candidates: list[Path] = []
    if scratch_dir is not None:
        real_scratch = Path(os.path.realpath(scratch_dir))
        for closed in protected:
            if real_scratch == closed or closed in real_scratch.parents:
                raise WriteRefused(
                    f"study mode blocks {label} inside protected LearningOS tree: {real_scratch}"
                )
        candidates.append(real_scratch)
    if allow_core:
        candidates.append(real_core)

    prefixes = tuple(reversed((lex, *lex.parents)))
    for real_root in candidates:
        matched_anc: Path | None = None
        if lex == real_root or real_root in lex.parents:
            matched_anc = real_root
        else:
            root_str = str(real_root)
            for anc in prefixes:
                if str(anc) == "/":
                    continue
                try:
                    if os.path.realpath(anc) == root_str:
                        matched_anc = anc
                        break
                except (OSError, ValueError):
                    continue
        if matched_anc is None:
            continue

        rel_parts = lex.relative_to(matched_anc).parts
        if any(part in ("", ".", "..") for part in rel_parts):
            raise WriteRefused(f"study mode blocks invalid path traversal for {label}: {lex}")
        anchored = real_root.joinpath(*rel_parts) if rel_parts else real_root
        if real_root == real_core:
            for closed in protected:
                if anchored == closed or closed in anchored.parents:
                    raise WriteRefused(
                        f"study mode blocks {label} inside protected LearningOS tree: {anchored}"
                    )
        return real_root, anchored, rel_parts

    try:
        real_target = _real_path(raw_path, cwd=cwd)
    except (RuntimeError, ValueError, OSError) as exc:
        raise WriteRefused(f"study mode cannot resolve {label} {raw_path!r}: {exc}") from exc
    for closed in protected:
        if real_target == closed or closed in real_target.parents:
            raise WriteRefused(
                f"study mode blocks {label} inside protected LearningOS tree: {real_target}"
            )
    raise WriteRefused(f"study mode blocks {label} outside the study boundary: {real_target}")


def _fd_open_flags(*, directory: bool) -> int:
    flags = os.O_RDONLY | os.O_NOFOLLOW
    if directory:
        flags |= os.O_DIRECTORY
    else:
        flags |= os.O_NONBLOCK
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    return flags


def _open_study_dir_fd(
    real_root: Path,
    dir_parts: tuple[str, ...],
    *,
    label: str,
    anchored: Path,
    allow_missing: bool,
) -> int | None:
    """Open ``real_root/dir_parts`` step-by-step refusing every symlink with O_NOFOLLOW."""
    dir_flags = _fd_open_flags(directory=True)
    try:
        dir_fd = os.open(real_root, dir_flags)
    except OSError as exc:
        is_link = False
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            with contextlib.suppress(OSError):
                is_link = stat.S_ISLNK(os.lstat(real_root).st_mode)
        if exc.errno == errno.ELOOP or is_link:
            raise WriteRefused(f"study mode blocks symlink in {label}: {anchored}") from exc
        if allow_missing and exc.errno == errno.ENOENT:
            return None
        raise WriteRefused(f"cannot access {label} root {real_root}: {exc}") from exc

    for part in dir_parts:
        try:
            next_fd = os.open(part, dir_flags, dir_fd=dir_fd)
        except OSError as exc:
            is_link = False
            if exc.errno in (errno.ELOOP, errno.ENOTDIR):
                with contextlib.suppress(OSError):
                    is_link = stat.S_ISLNK(os.lstat(part, dir_fd=dir_fd).st_mode)
            os.close(dir_fd)
            if exc.errno == errno.ELOOP or is_link:
                raise WriteRefused(f"study mode blocks symlink in {label}: {anchored}") from exc
            if allow_missing and exc.errno == errno.ENOENT:
                return None
            if exc.errno in (errno.ENOENT, errno.ENOTDIR):
                raise WriteRefused(f"no such {label}: {anchored}") from exc
            raise WriteRefused(f"cannot access {label} {anchored}: {exc}") from exc
        os.close(dir_fd)
        dir_fd = next_fd
    return dir_fd


def check_study_path(
    raw_path: str,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path | None = None,
    label: str = "file input",
    allow_core: bool = True,
) -> Path:
    """Enforce the study-mode read/write fence without traversing symlinks inside roots."""
    real_root, anchored, rel_parts = _match_study_anchor(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=allow_core,
    )
    if not rel_parts:
        if not allow_core:
            raise WriteRefused(f"{label} target must be a file inside study scratch: {anchored}")
        dir_fd = _open_study_dir_fd(
            real_root, (), label=label, anchored=anchored, allow_missing=True,
        )
        if dir_fd is not None:
            os.close(dir_fd)
        return anchored

    parent_fd = _open_study_dir_fd(
        real_root,
        rel_parts[:-1],
        label=label,
        anchored=anchored,
        allow_missing=True,
    )
    if parent_fd is not None:
        try:
            try:
                st = os.lstat(rel_parts[-1], dir_fd=parent_fd)
            except FileNotFoundError:
                pass
            except OSError as exc:
                raise WriteRefused(f"cannot inspect {label} {anchored}: {exc}") from exc
            else:
                if stat.S_ISLNK(st.st_mode):
                    raise WriteRefused(f"study mode blocks symlink in {label}: {anchored}")
                if not allow_core and stat.S_ISDIR(st.st_mode):
                    raise WriteRefused(f"{label} target must be a file, not a directory: {anchored}")
                if not allow_core and stat.S_ISREG(st.st_mode) and st.st_nlink > 1:
                    raise WriteRefused(f"study mode blocks hardlink in {label}: {anchored}")
        finally:
            os.close(parent_fd)
    return anchored


def check_study_new_output_path(
    raw_path: str,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path | None = None,
    label: str = "output path",
    draft_path: str | None = None,
) -> Path:
    """Validate a new writable scratch path whose parent exists and whose leaf does not."""
    real_root, anchored, rel_parts = _match_study_anchor(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=False,
    )
    if not rel_parts:
        raise WriteRefused(f"{label} target must be a file inside study scratch: {anchored}")
    if draft_path:
        try:
            _, anchored_draft, _ = _match_study_anchor(
                draft_path,
                core_root=core_root,
                scratch_dir=scratch_dir,
                cwd=cwd,
                label="draft",
                allow_core=True,
            )
        except WriteRefused:
            anchored_draft = None
        if anchored_draft is not None and anchored == anchored_draft:
            raise WriteRefused(f"{label} target must not replace the reviewed draft: {raw_path}")

    parent_fd = _open_study_dir_fd(
        real_root,
        rel_parts[:-1],
        label=label,
        anchored=anchored,
        allow_missing=True,
    )
    if parent_fd is None:
        raise WriteRefused(f"{label} directory does not exist: {anchored.parent}")
    try:
        try:
            st = os.lstat(rel_parts[-1], dir_fd=parent_fd)
        except FileNotFoundError:
            return anchored
        except OSError as exc:
            raise WriteRefused(f"cannot inspect {label} {anchored}: {exc}") from exc
        if stat.S_ISLNK(st.st_mode):
            raise WriteRefused(f"study mode blocks symlink in {label}: {anchored}")
        raise WriteRefused(f"{label} target already exists; refusing to overwrite: {raw_path}")
    finally:
        os.close(parent_fd)


def _read_regular_under_root(
    real_root: Path,
    rel_parts: tuple[str, ...],
    *,
    label: str,
    anchored: Path,
    require_existing: bool,
) -> bytes | None:
    if not rel_parts:
        raise WriteRefused(f"no such {label}: {anchored}")
    parent_fd = _open_study_dir_fd(
        real_root,
        rel_parts[:-1],
        label=label,
        anchored=anchored,
        allow_missing=not require_existing,
    )
    if parent_fd is None:
        return None
    file_flags = _fd_open_flags(directory=False)
    try:
        try:
            leaf_fd = os.open(rel_parts[-1], file_flags, dir_fd=parent_fd)
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise WriteRefused(f"study mode blocks symlink in {label}: {anchored}") from exc
            if exc.errno in (errno.ENOENT, errno.ENOTDIR):
                if not require_existing:
                    return None
                raise WriteRefused(f"no such {label}: {anchored}") from exc
            raise WriteRefused(f"cannot read {label} {anchored}: {exc}") from exc
    finally:
        os.close(parent_fd)

    try:
        st = os.fstat(leaf_fd)
    except OSError as exc:
        os.close(leaf_fd)
        raise WriteRefused(f"cannot stat {label} {anchored}: {exc}") from exc
    if not stat.S_ISREG(st.st_mode):
        os.close(leaf_fd)
        raise WriteRefused(f"no such {label}: {anchored}")
    try:
        with os.fdopen(leaf_fd, "rb") as handle:
            return handle.read()
    except OSError as exc:
        raise WriteRefused(f"cannot read {label} {anchored}: {exc}") from exc


def read_study_file(
    raw_path: str,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path | None = None,
    label: str = "file input",
    allow_core: bool = True,
) -> tuple[Path, bytes]:
    """Validate and read a regular study file via O_NOFOLLOW descriptors."""
    real_root, anchored, rel_parts = _match_study_anchor(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=allow_core,
    )
    data = _read_regular_under_root(
        real_root,
        rel_parts,
        label=label,
        anchored=anchored,
        require_existing=True,
    )
    assert data is not None
    return anchored, data


def _read_staged_study_file(
    raw_path: str,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path | None = None,
    label: str = "file input",
    allow_core: bool = True,
) -> tuple[Path, bytes] | None:
    manifest_env = os.environ.get(STUDY_STAGED_MANIFEST_ENV)
    if not manifest_env:
        return None
    manifest_lex = Path(os.path.abspath(Path(manifest_env).expanduser()))
    manifest_dir = Path(os.path.realpath(manifest_lex.parent))
    manifest_bytes = _read_regular_under_root(
        manifest_dir,
        (manifest_lex.name,),
        label="staged study manifest",
        anchored=manifest_dir / manifest_lex.name,
        require_existing=True,
    )
    assert manifest_bytes is not None
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise WriteRefused(f"corrupt staged study manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise WriteRefused("staged study manifest must be a JSON object")

    _real_root, anchored, _rel_parts = _match_study_anchor(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=allow_core,
    )
    entries = manifest.get("entries")
    if not isinstance(entries, dict):
        raise WriteRefused("staged study manifest missing entries")
    rel_staged = entries.get(str(anchored))
    if not isinstance(rel_staged, str) or not rel_staged:
        return None
    rel_parts = Path(rel_staged).parts
    if not rel_parts or any(part in ("", ".", "..", "/") for part in rel_parts):
        raise WriteRefused("invalid staged study entry path")
    staged_bytes = _read_regular_under_root(
        manifest_dir,
        rel_parts,
        label=label,
        anchored=anchored,
        require_existing=True,
    )
    assert staged_bytes is not None
    return anchored, staged_bytes


def read_study_or_staged_file(
    raw_path: str,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path | None = None,
    label: str = "file input",
    allow_core: bool = True,
) -> tuple[Path, bytes]:
    """Read a validated study input from the broker's host stage or via O_NOFOLLOW."""
    staged = _read_staged_study_file(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=allow_core,
    )
    if staged is not None:
        return staged
    return read_study_file(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=allow_core,
    )


def read_optional_study_or_staged_file(
    raw_path: str,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path | None = None,
    label: str = "file input",
    allow_core: bool = True,
) -> tuple[Path, bytes | None]:
    """Read a study input when it exists; return ``(anchored, None)`` only if missing."""
    staged = _read_staged_study_file(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=allow_core,
    )
    if staged is not None:
        return staged
    real_root, anchored, rel_parts = _match_study_anchor(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=allow_core,
    )
    data = _read_regular_under_root(
        real_root,
        rel_parts,
        label=label,
        anchored=anchored,
        require_existing=False,
    )
    return anchored, data


def read_content_bound_file(
    path_value: str,
    expected_sha256: str | None = None,
    *,
    label: str = "file input",
) -> tuple[Path, bytes]:
    """Read an external file once and verify the bytes a V2 request approved.

    The returned bytes are the bytes the caller must parse or write. Hashing
    and then reopening the pathname would merely move the TOCTOU window.
    Direct human CLI preflights may omit the digest; an active V2 gateway
    context may not.
    """
    if path_value == "-" and current_gateway_request() is not None:
        raise WriteRefused(
            f"GatewayEnvelopeV2 {label} must be a real path with an approved SHA-256; "
            "unbound stdin is not allowed"
        )
    fence_core = os.environ.get(STUDY_FENCE_CORE_ENV)
    if fence_core:
        fence_scratch = os.environ.get(STUDY_FENCE_SCRATCH_ENV)
        source, content = read_study_or_staged_file(
            path_value,
            core_root=Path(fence_core),
            scratch_dir=Path(fence_scratch) if fence_scratch else None,
            label=label,
        )
    else:
        source = Path(path_value).expanduser().resolve()
        if not source.is_file():
            raise WriteRefused(f"no such {label}: {source}")
        try:
            content = source.read_bytes()
        except OSError as exc:
            raise WriteRefused(f"cannot read {label} {source}: {exc}") from exc
    if expected_sha256 is None:
        if current_gateway_request() is not None:
            raise WriteRefused(
                f"GatewayEnvelopeV2 {label} requires a SHA-256 bound to the exact bytes"
            )
        return source, content
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", expected_sha256):
        raise WriteRefused(
            f"{label} SHA-256 must use sha256:<64 lowercase hexadecimal digits>"
        )
    actual_sha256 = "sha256:" + hashlib.sha256(content).hexdigest()
    if actual_sha256 != expected_sha256:
        raise WriteRefused(
            f"approved {label} changed before use; expected {expected_sha256}, "
            f"found {actual_sha256}. Review the new bytes and create a new approval."
        )
    return source, content


def read_structured_file(
    path_value: str,
    *,
    expected_sha256: str | None = None,
    label: str = "structured input",
) -> dict:
    """Read a JSON/YAML object from a path, or from stdin when given ``-``.

    Stdin matters for callers that build an envelope in memory: writing it to
    a temp file first means a real file holding canonical intent has to be
    created, found, and cleaned up on every write path, including the ones
    that fail. ``-`` removes that lifecycle entirely.
    """
    if path_value == "-" and expected_sha256 is None \
            and current_gateway_request() is None:
        raw = sys.stdin.read()
        try:
            data = json.loads(raw)
        except ValueError as exc:
            raise WriteRefused(f"cannot parse structured input from stdin: {exc}") from exc
        if not isinstance(data, dict):
            raise WriteRefused("structured input must be an object")
        return data
    path, raw_bytes = read_content_bound_file(
        path_value,
        expected_sha256,
        label=label,
    )
    try:
        raw = raw_bytes.decode("utf-8")
        if path.suffix.lower() == ".json":
            data = json.loads(raw)
        else:
            data = yaml.safe_load(raw)
    except (UnicodeDecodeError, ValueError, yaml.YAMLError) as exc:
        raise WriteRefused(f"cannot parse {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise WriteRefused(f"structured input must be an object: {path}")
    return data


def prepare_review_envelope(capability_name: str, payload: dict,
                            snapshot: str, revisions: dict) -> dict:
    """Prepare a recoverable request during preflight, while its lock is held.

    The envelope names the channel whose session ledger the reviewed write
    joins: the active gateway request's channel, else the operator default
    a bare `session-end` resolves. A fixed agent channel split one
    operator's writes across two ledgers, so `session-end --commit-message`
    committed the shared ledgers without the receipt and note they name.
    """
    request = current_gateway_request()
    channel = request.channel if request is not None else DEFAULT_SESSION_CHANNEL
    envelope = {
        "schema_version": 2,
        "request_id": f"request-reviewed-{observations.new_hex()}",
        "idempotency_key": f"reviewed-{observations.new_hex()}",
        "capability": capability_name,
        "channel": channel,
        "expected_snapshot": snapshot,
        "expected_revisions": revisions,
        "payload": payload,
        "approval": {"kind": "operator-approval", "subject_sha256": ""},
    }
    from learning_os.store.session_ledger import resolve_session_identity
    session_id, source = resolve_session_identity(channel=channel)
    if source != "channel":
        envelope["session_id"] = session_id
    envelope["approval"]["subject_sha256"] = intent_sha256(envelope)
    return envelope


_CONTENT_BOUND_V2 = frozenset({
    "legacy.archive.lock.publish",
    "masters-planning.catalog.update",
    "masters-planning.comparison.publish",
    "collection.entry.revise",
    "source.intake.record",
    "source.record.revise",
    "unit.material-synthesis.publish",
    "unit.plan.revise",
})


def _payload_schema_path(root: Path, name: str) -> Path:
    return root / "system" / "schema" / "capabilities" / f"{name}.schema.json"


def validate_payload(root: Path, name: str, payload: dict) -> None:
    """Refuse a payload the capability never declared.

    A missing schema is itself a refusal: an undeclared payload surface means
    the capability is not actually specified, and guessing would let the
    gateway accept fields no contract describes.
    """
    path = _payload_schema_path(root, name)
    if not path.is_file():
        raise WriteRefused(f"no declared payload schema for capability {name}")
    schema = json.loads(path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(payload),
                    key=lambda error: list(error.path))
    if errors:
        detail = "; ".join(f"{'/'.join(str(p) for p in e.path) or '<payload>'}: {e.message}"
                           for e in errors[:4])
        raise WriteRefused(f"invalid payload for {name}: {detail}")


def prepare_dispatch(
    root: Path,
    definition,
    envelope: dict,
    payload: dict,
    *,
    parser_factory=None,
):
    """Shared gateway admission (SPEC 11.2 K1).

    Refuses misplaced approval and content-bound file payloads, validates
    the payload, and builds the schema-derived namespace with envelope guards.
    ``parser_factory`` is accepted for caller compatibility and unused.
    Returns ``(None, namespace)``.
    """
    from learning_os.store.contracts.payloads import payload_to_namespace_from_schema

    if envelope.get("schema_version") == 2 and "approve" in payload:
        raise WriteRefused(
            "GatewayEnvelopeV2 approval belongs only in the envelope, not its payload"
        )
    if envelope.get("schema_version") == 2 \
            and definition.name in _CONTENT_BOUND_V2 \
            and "file" in payload:
        raise WriteRefused(
            f"GatewayEnvelopeV2 {definition.name} requires an inline record so "
            "approval is bound to the exact content"
        )
    validate_payload(root, definition.name, payload)
    namespace = payload_to_namespace_from_schema(
        root, definition.name, payload,
        root=str(root),
        expected_snapshot=envelope.get("expected_snapshot"),
        expected_revisions=envelope.get("expected_revisions", {}),
    )
    # A validated V2 envelope binds an approved user gesture to the intent
    # hash; handlers check ``namespace.approve`` identically to CLI ``--approve``.
    if envelope.get("schema_version") == 2 and hasattr(namespace, "approve"):
        namespace.approve = True
    # Handlers that can report either prose or JSON must report JSON here.
    if hasattr(namespace, "json"):
        namespace.json = True
    return None, namespace


def validate_capability_envelope(root: Path, envelope: dict, *, kind: str) -> None:
    if kind == "request" and envelope.get("schema_version") != 2:
        # Before dispatch, and before the schema's oneOf can misread the
        # shape: an envelope without `schema_version: 2` used to travel all
        # the way to the handler, which answered with a circular pointer.
        # The general sealing recipe is WORKFLOWS §25c.
        raise WriteRefused(
            "invalid capability envelope: schema_version 2 required "
            "(WORKFLOWS §25c)"
        )
    schema = json.loads((root / "system/schema/capability-envelope.schema.json").read_text(encoding="utf-8"))
    try:
        schema["$defs"][kind]
    except KeyError as exc:  # pragma: no cover - a repository contract defect
        raise WriteRefused(f"capability envelope schema has no {kind} definition") from exc
    directional_schema = {
        "$schema": schema.get("$schema", "https://json-schema.org/draft/2020-12/schema"),
        "$defs": schema["$defs"],
        "$ref": f"#/$defs/{kind}",
    }
    errors = sorted(
        Draft202012Validator(directional_schema).iter_errors(envelope),
        key=lambda error: list(error.path),
    )
    if errors:
        raise WriteRefused("invalid capability envelope: " + "; ".join(error.message for error in errors[:4]))


def context_from_v2(envelope: dict) -> GatewayRequestContext:
    subject_hash = intent_sha256(envelope)
    approval = envelope["approval"]
    if approval["subject_sha256"] != subject_hash:
        raise WriteRefused(
            "approval subject does not match the current capability intent"
        )
    raw_session = envelope.get("session_id")
    sealed_session = raw_session.strip() if isinstance(raw_session, str) else None
    return GatewayRequestContext(
        request_id=envelope["request_id"],
        idempotency_key=envelope["idempotency_key"],
        capability=envelope["capability"],
        channel=envelope["channel"],
        intent_sha256=subject_hash,
        approval_kind=approval["kind"],
        approval_subject_sha256=approval["subject_sha256"],
        expected_snapshot=envelope["expected_snapshot"],
        session_id=sealed_session or None,
    )

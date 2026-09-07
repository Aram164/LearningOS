"""Shared plumbing for every command: repository root, the operator lock, atomic writes,
the transaction wrapper and its receipt, and the small YAML/Markdown helpers."""

from __future__ import annotations

import contextlib
import contextvars
import datetime as _dt
import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

from learning_os.contracts.gateway import (
    current_gateway_request,
    gateway_snapshot_is_verified,
)
from learning_os.fingerprint import canonical_fingerprint, source_fingerprint
from learning_os.genout import (
    build_backlinks,
    build_manifest,
    generate_all,
    stable_generated_at,
    write_outputs,
)
from learning_os.loader import load_repo
from learning_os.rules import validate
from learning_os.transactions import (
    TransactionConflict,
    TransactionFailure,
    TransactionService,
    TransactionSnapshotConflict,
    parse_expected_revisions,
    reconcile_inflight_transactions,
)

TOOLS = Path(__file__).resolve().parent.parent.parent
_HELD_OPERATOR_LOCKS: contextvars.ContextVar[frozenset[str]] = (
    contextvars.ContextVar("learningos_held_operator_locks", default=frozenset())
)

def _root(args) -> Path:
    return Path(args.root).resolve() if args.root else TOOLS.parent


def _allocate_attachment_path(attachment_dir: Path, source_name: str) -> Path:
    """A destination no existing attachment occupies.

    Attachment bytes are approved canonical content, so the previous holder of a
    name must never be overwritten. A timestamp was not a uniqueness argument:
    it is precise to one second and the name it produced was never itself
    checked, so two uploads of `handwriting.png` within the same second silently
    replaced the first one's bytes.

    Every candidate is checked now, and the counter guarantees the search ends
    on a free name. Checking existence is sufficient here — and only here —
    because every caller allocates while holding the operator lock, so no other
    process can take the name between this check and the transaction that writes
    it.
    """
    target = attachment_dir / source_name
    if not target.exists():
        return target

    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    target = attachment_dir / f"{stamp}-{source_name}"
    if not target.exists():
        return target

    counter = 1
    while True:
        target = attachment_dir / f"{stamp}-{counter}-{source_name}"
        if not target.exists():
            return target
        counter += 1


@contextlib.contextmanager
def _operator_lock(root: Path):
    """Cross-process lock for every write/generation transaction."""
    root_key = str(root.resolve())
    held = _HELD_OPERATOR_LOCKS.get()
    if root_key in held:
        yield
        return
    token = hashlib.sha256(root_key.encode("utf-8")).hexdigest()[:16]
    lock_path = Path(tempfile.gettempdir()) / f"learningos-{token}.lock"
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        reconcile_inflight_transactions(root)
        context_token = _HELD_OPERATOR_LOCKS.set(held | {root_key})
        try:
            yield
        finally:
            _HELD_OPERATOR_LOCKS.reset(context_token)
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


class WriteRefused(Exception):
    """A canonical write could not be performed; nothing was changed."""



def _atomic_text(path: Path, content: str) -> None:
    """Temp file + os.replace, cleaning up after any failure.

    Every mutating command funnels through here, so an ordinary filesystem
    problem — target replaced by a directory, permission denied, full disk —
    must surface as an actionable refusal instead of a traceback that leaves a
    stray `.tmp` sibling behind.
    """
    tmp = path.with_name(f".{path.name}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
    except OSError as exc:
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)
        raise WriteRefused(f"cannot write {path}: {exc.strerror or exc}") from exc


def _expected_ok(root: Path, expected: str | None) -> bool:
    if expected is None:
        return True
    request = current_gateway_request()
    if request is not None:
        if request.expected_snapshot != expected:
            print(
                "los: handler snapshot does not match the approved gateway intent",
                file=sys.stderr,
            )
            return False
        # cmd_capability marks this only while it holds the same operator lock
        # through the complete handler dispatch. Direct service tests and any
        # future bypass do not inherit the shortcut and must compare normally.
        if gateway_snapshot_is_verified(root, expected):
            return True
    if not expected.strip():
        # An empty token is almost always a scripting slip (a command
        # substitution that returned nothing), not a deliberate unguarded
        # write. Omitting the flag remains the way to write unguarded.
        print("los: --expected-snapshot was empty; refusing to write without a "
              "concurrency token", file=sys.stderr)
        return False
    # The snapshot is a content digest, not a loaded-domain property. Loading
    # the whole repository only to call the same path-based digest added a full
    # parse to every UI write and did not strengthen the concurrency check.
    actual = f"sha256:{canonical_fingerprint(root)}"
    if actual == expected:
        return True
    print("los: projection conflict — authored files changed since the app loaded; "
          "reload before writing", file=sys.stderr)
    print(json.dumps({"expected": expected, "actual": actual}), file=sys.stderr)
    return False


def _publish(root: Path) -> None:
    repo = load_repo(root)
    write_outputs(repo, generate_all(repo))


def _publish_repo(repo) -> None:
    write_outputs(repo, generate_all(repo))


def _path_or_error(root: Path, path_id: str):
    repo = load_repo(root)
    learning_path = repo.learning_paths.get(path_id)
    if learning_path is None or learning_path.archived:
        print(f"los: active learning path not found: {path_id}", file=sys.stderr)
        return repo, None
    return repo, learning_path


def _fresh_manifest(root: Path) -> dict:
    repo = load_repo(root)
    generated_at = stable_generated_at(root)
    backlinks = build_backlinks(repo, generated_at)
    return build_manifest(repo, generated_at, backlinks)


def _print_rows(rows: list[dict]) -> int:
    print(json.dumps(rows, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def _read_content_bound_file(
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


def _read_structured_file(
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
    path, raw_bytes = _read_content_bound_file(
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


# --------------------------------------------------------- curriculum writes
def _session_ledger(root: Path) -> Path:
    token = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"learningos-{token}-touched.json"


def _session_path_state(root: Path, relative: str) -> dict[str, str]:
    """Return the exact post-transaction state used to prove session ownership."""
    lexical = root / relative
    try:
        resolved = lexical.resolve()
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return {"state": "unsafe"}
    if lexical.is_symlink():
        return {"state": "unsafe"}
    if not resolved.exists():
        return {"state": "absent"}
    if not resolved.is_file():
        return {"state": "not-file"}
    try:
        digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
    except OSError:
        return {"state": "unreadable"}
    return {"state": "file", "sha256": digest}


def _load_session_paths(root: Path) -> dict[str, dict[str, str]]:
    ledger = _session_ledger(root)
    if not ledger.is_file():
        return {}
    try:
        data = json.loads(ledger.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise WriteRefused(f"session ownership ledger is unreadable: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1 \
            or not isinstance(data.get("paths"), dict):
        raise WriteRefused("session ownership ledger has an unsupported contract")
    output: dict[str, dict[str, str]] = {}
    for relative, state in data["paths"].items():
        if not isinstance(relative, str) or not relative \
                or Path(relative).is_absolute() or ".." in Path(relative).parts \
                or not isinstance(state, dict):
            raise WriteRefused("session ownership ledger contains an invalid path row")
        output[relative] = {str(key): str(value) for key, value in state.items()}
    return output


def _record_touched(root: Path, paths) -> None:
    ledger = _session_ledger(root)
    current = _load_session_paths(root) if ledger.is_file() else {}
    for path in paths:
        p = Path(path)
        try:
            rel = p.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            continue
        # Canvas files are Obsidian UI state, not part of a learning-session
        # action ledger. The protection is about the file type, not the first
        # three default names Obsidian happened to generate.
        if p.suffix.lower() != ".canvas":
            current[rel] = _session_path_state(root, rel)
    _atomic_text(ledger, json.dumps({
        "schema_version": 1,
        "paths": dict(sorted(current.items())),
    }, indent=2, sort_keys=True) + "\n")


def _write_transaction(root: Path, writes: dict[Path, str | bytes],
                       *, capability: str = "legacy.write",
                       expected_revisions: dict[str, int] | None = None,
                       artifact_ids=(), deletes=()) -> tuple[int, list, dict]:
    """Commit one named, receipt-producing canonical transaction.

    Returns ``(code, errors, confirmation)``. The confirmation travels back to
    the caller explicitly rather than through module state: a command reports
    the receipt for *its own* transaction, and a module global could not
    express that — it outlived the operator lock and was read after release.
    On any failure the confirmation is empty, so a caller cannot accidentally
    report a receipt for a write that did not happen.
    """
    if current_gateway_request() is None:
        return 2, [
            "canonical writes must use GatewayEnvelopeV2; direct CLI application "
            "is disabled"
        ], {}
    service = TransactionService(root)
    delete_paths = tuple(Path(path) for path in deletes)
    for path in (*writes, *delete_paths):
        if path.exists() and not path.is_file():
            return 2, [f"cannot change {path}: target is not a regular file"], {}
    validated_repo = None

    def validation_errors():
        nonlocal validated_repo
        validated_repo = load_repo(root)
        return [
            issue for issue in validate(validated_repo, online=False)
            if issue.severity == "E"
        ]

    def publish_validated_state() -> str:
        nonlocal validated_repo
        repo = validated_repo or load_repo(root)
        _publish_repo(repo)
        projected_snapshot = f"sha256:{source_fingerprint(repo)}"
        validated_repo = None
        return projected_snapshot

    try:
        result = service.commit(
            capability=capability,
            writes=writes,
            deletes=delete_paths,
            artifact_ids=artifact_ids,
            expected_revisions=expected_revisions or {},
            validate_state=validation_errors,
            publish=publish_validated_state,
            rollback_publish=lambda: _publish(root),
            touched=lambda paths: _record_touched(root, paths),
        )
    except TransactionConflict as exc:
        print("los: artifact revision conflict — reload the affected record before writing",
              file=sys.stderr)
        print(json.dumps({
            "conflicts": {artifact: {"expected": expected, "actual": actual}
                          for artifact, (expected, actual) in exc.conflicts.items()}
        }, ensure_ascii=False), file=sys.stderr)
        return 3, [], {}
    except TransactionSnapshotConflict:
        # The V2 gateway owns the typed stale-snapshot response. Let the exact
        # expected/actual values cross that boundary without being flattened
        # into a generic transaction failure.
        raise
    except TransactionFailure as exc:
        # Canonical write refusal is a handled operator error, not an internal
        # process failure. Preserve the gateway's established exit-code 2.
        return 2, [str(exc)], {}
    return 0, [], _confirmation_from(result)


def _expected_revisions_from_args(args) -> dict[str, int]:
    try:
        return parse_expected_revisions(getattr(args, "expected_revision", None))
    except ValueError as exc:
        raise WriteRefused(str(exc)) from exc


def _add_expected_revision_argument(parser) -> None:
    parser.add_argument(
        "--expected-revision", action="append", default=[],
        help="artifact-level concurrency token <artifact-id>=<revision>; repeatable",
    )


def _confirmation_from(result) -> dict:
    """Receipt facts a command reports after its own successful transaction."""
    if result is None:
        return {}
    parts = result.receipt_path.parts
    try:
        relative = Path(*parts[parts.index("operations"):]).as_posix()
    except ValueError:
        relative = result.receipt_path.name
    return {
        "transaction_id": result.transaction_id,
        "receipt_path": relative,
        "artifact_revisions": dict(result.revisions),
        "snapshot_after": result.snapshot_after,
        "replayed": bool(result.replayed),
    }


def _unit_map_or_error(root: Path, unit_id: str):
    repo = load_repo(root)
    unit = repo.units.get(unit_id)
    if unit is None:
        print(f"los: unit not found: {unit_id}", file=sys.stderr)
        return repo, None, None
    map_id = unit.data.get("current_study_map")
    study_map = repo.study_maps.get(map_id) if map_id else None
    if study_map is None:
        print(f"los: unit has no current study map: {unit_id}", file=sys.stderr)
        return repo, unit, None
    return repo, unit, study_map


class _NoAliasSafeDumper(yaml.SafeDumper):
    """Keep authored YAML deterministic even when an input package uses anchors."""

    def ignore_aliases(self, data):  # noqa: ANN001 - PyYAML callback signature
        return True


def _dump_yaml(data: dict) -> str:
    return yaml.dump(data, Dumper=_NoAliasSafeDumper, sort_keys=False,
                     allow_unicode=True, width=100)


def _dump_study_map(study_map, data: dict) -> str:
    from learning_os.material_refs import preserve_map_refs

    return _dump_yaml(preserve_map_refs(study_map, data))


def _render_frontmatter(meta: dict, body: str) -> str:
    return "---\n" + _dump_yaml(meta).rstrip() + "\n---\n\n" + body.lstrip()




def _replace_registry_list_record(content: str, record_id: str, record: dict) -> str:
    """Render one record in a top-level YAML list without reformatting siblings."""
    lines = content.splitlines(keepends=True)
    id_line = next((i for i, line in enumerate(lines)
                    if re.match(rf"^[ ]*(?:- )?id: {re.escape(record_id)}[ ]*$",
                                line.rstrip("\r\n"))), None)
    if id_line is None:
        raise ValueError(f"registry record not found in source text: {record_id}")
    id_indent = len(lines[id_line]) - len(lines[id_line].lstrip(" "))
    if lines[id_line].lstrip(" ").startswith("- id:"):
        start = id_line
        item_indent = " " * id_indent
    else:
        item_indent = " " * max(0, id_indent - 2)
        start = next((i for i in range(id_line, -1, -1)
                      if lines[i].startswith(item_indent + "- ")), None)
        if start is None:
            raise ValueError(f"registry list item not found for: {record_id}")
    end = next((i for i in range(start + 1, len(lines))
                if lines[i].startswith(item_indent + "- ")), len(lines))
    rendered = _dump_yaml(record).rstrip().splitlines()
    replacement = item_indent + "- " + rendered[0] + "\n"
    replacement += "\n".join(item_indent + "  " + line if line else ""
                              for line in rendered[1:])
    replacement += "\n\n"
    return "".join(lines[:start]) + replacement + "".join(lines[end:]).lstrip("\n")


def _stage(data: dict, stage_id: str):
    return next((row for row in data.get("stages", []) or []
                 if isinstance(row, dict) and row.get("id") == stage_id), None)


# ---------------------------------------------------- validate / generate
def _delegate(script: str, extra: list[str], args) -> int:
    """One implementation of every rule: shell out to the canonical script."""
    cmd = [sys.executable, str(TOOLS / script), *extra]
    if args.root:
        cmd += ["--root", str(_root(args))]
    return subprocess.run(cmd).returncode

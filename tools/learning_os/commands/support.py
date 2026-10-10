"""Shared plumbing for every command: repository root, the operator lock, atomic writes,
the transaction wrapper and its receipt, and the small YAML/Markdown helpers."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from learning_os import observations
from learning_os.contracts.gateway import (
    current_gateway_request,
    gateway_snapshot_is_verified,
)
from learning_os.domain.codes import STALE_SNAPSHOT
from learning_os.domain.failures import WriteRefused
from learning_os.domain.suggest import not_found
from learning_os.fingerprint import canonical_fingerprint
from learning_os.loader import load_repo
from learning_os.ops._legacy_plumbing import (
    DEFAULT_SESSION_CHANNEL,
    SESSION_LEDGER_SCHEMA_VERSION,
    _current_session_id,
    _dump_yaml,
    _is_anchored,
    _json_layout,
    _process_state_dir,
    _record_gateway_refusal,
    _row_recorded_at,
    _session_ledger,
)
from learning_os.ops.commit import commit_proposal
from learning_os.ops.context import OpContext
from learning_os.ops.proposal import TransactionProposal
from learning_os.transactions import parse_expected_revisions

TOOLS = Path(__file__).resolve().parent.parent.parent


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

    stamp = observations.now().replace(tzinfo=None).strftime("%Y%m%d-%H%M%S")
    target = attachment_dir / f"{stamp}-{source_name}"
    if not target.exists():
        return target

    counter = 1
    while True:
        target = attachment_dir / f"{stamp}-{counter}-{source_name}"
        if not target.exists():
            return target
        counter += 1


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
            _record_gateway_refusal(STALE_SNAPSHOT, True)
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
    if current_gateway_request() is None:
        # Found by synthetic use: a direct CLI write with a current snapshot is
        # refused by `_write_transaction` as "use GatewayEnvelopeV2", but the
        # same write with a stale or invented one was refused here first, as a
        # projection conflict telling the caller to reload and try again. It
        # cannot succeed on any snapshot, so "reload before writing" sends a
        # script into a loop against a door that is closed for another reason.
        # Both facts are true; the one that decides the outcome goes first.
        print("los: canonical writes must use GatewayEnvelopeV2; direct CLI "
              "application is disabled — reloading will not change this. The "
              "supplied snapshot is also out of date. Submit the write with "
              "`los capability NAME --payload-file ENVELOPE.json` "
              "(envelope: WORKFLOWS §25c).", file=sys.stderr)
        print(json.dumps({"expected": expected, "actual": actual}), file=sys.stderr)
        return False
    print("los: projection conflict — authored files changed since the app loaded; "
          "reload before writing", file=sys.stderr)
    print(json.dumps({"expected": expected, "actual": actual}), file=sys.stderr)
    _record_gateway_refusal(STALE_SNAPSHOT, True)
    return False


def _print_rows(rows: list[dict]) -> int:
    print(json.dumps(rows, **_json_layout(), sort_keys=True, ensure_ascii=False))
    return 0


# --------------------------------------------------------- curriculum writes

#: Environment variable naming the Core client and its build, stamped by the
#: interface on every Core child it spawns (`obsidian-ui/<build>`). An
#: unmarked call stays valid: terminal agents send nothing, and `session-end`
#: never refuses one. Informational only — staleness is proven by comparing
#: the installed build against the built one (see `health._ui_plugin_check`),
#: never by trusting this marker.
CLIENT_ENV = "LOS_CLIENT"


#: A ledger row older than this is reported as stale and is no longer staged
#: by default. A forgotten window is surfaced, never silently inherited.
SESSION_LEDGER_STALE_HOURS = 24


def _legacy_session_ledger(root: Path) -> Path:
    """The pre-session shared ledger filename, now read-only history."""
    token = hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:16]
    return Path(tempfile.gettempdir()) / f"learningos-{token}-touched.json"


def _row_is_stale(row: dict, now: _dt.datetime | None = None) -> bool:
    """Whether a row is too old to stage without an explicit flag.

    A row whose age cannot be proven is stale: staging it would inherit a
    claim of unknown vintage.
    """
    moment = _row_recorded_at(row)
    if moment is None:
        return True
    now = now or observations.now().astimezone(_dt.UTC)
    return (now - moment).total_seconds() > SESSION_LEDGER_STALE_HOURS * 3600


def _read_sibling_session_ledger(path: Path) -> tuple[str, dict[str, dict]] | None:
    """Parse one foreign ledger file, tolerantly: a corrupt sibling must not
    break this session's close — its own owner still hits the strict loader."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("paths"), dict):
        return None
    identity = data.get("session_id")
    if data.get("schema_version") != SESSION_LEDGER_SCHEMA_VERSION \
            or not isinstance(identity, str) or not identity:
        return None
    rows: dict[str, dict] = {}
    for relative, state in data["paths"].items():
        if not isinstance(relative, str) or not relative \
                or Path(relative).is_absolute() or ".." in Path(relative).parts \
                or not isinstance(state, dict):
            return None
        rows[relative] = {str(key): str(value) for key, value in state.items()}
    return identity, rows


def _load_other_session_ledgers(root: Path,
                                session_id: str | None = None
                                ) -> dict[str, dict[str, dict]]:
    """Every session ledger for this root except this session's own.

    Includes the pre-session shared file (reported as `legacy`, with its rows
    undated) so an upgrade never silently drops rows — they surface as
    foreign, never staged. During the transition from the temp-dir location,
    ledgers still sitting in the old location are found here too and
    reported as foreign — including this session's own previous-location
    rows, which are labelled so they cannot be mistaken for the live ones.
    """
    own = _current_session_id(explicit=session_id)
    token = hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:16]
    pattern = f"learningos-{token}-*-touched.json"
    others: dict[str, dict[str, dict]] = {}
    own_ledger = _session_ledger(root, own)

    def _claim(candidate: Path, *, previous_location: bool) -> None:
        if candidate == own_ledger:
            return
        parsed = _read_sibling_session_ledger(candidate)
        if parsed is None:
            return
        identity, rows = parsed
        if identity == own:
            if not previous_location:
                return
            identity = f"{own} (previous location)"
        if identity in others:
            others[identity] = {**rows, **others[identity]}
        else:
            others[identity] = rows

    try:
        current = sorted(_process_state_dir(root).glob(pattern))
    except OSError:
        current = []
    for candidate in current:
        _claim(candidate, previous_location=False)
    if _is_anchored(root):
        # The old temp-dir location: every ledger written there before the
        # move still surfaces, as foreign, until the OS reclaims it.
        try:
            previous = sorted(Path(tempfile.gettempdir()).glob(pattern))
        except OSError:
            previous = []
        for candidate in previous:
            _claim(candidate, previous_location=True)
    legacy = _legacy_session_ledger(root)
    if legacy.is_file():
        try:
            data = json.loads(legacy.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, ValueError):
            data = None
        if isinstance(data, dict) and isinstance(data.get("paths"), dict):
            rows = {}
            for relative, state in data["paths"].items():
                if isinstance(relative, str) and relative \
                        and not Path(relative).is_absolute() \
                        and ".." not in Path(relative).parts \
                        and isinstance(state, dict):
                    rows[relative] = {str(key): str(value)
                                      for key, value in state.items()}
            if rows:
                others.setdefault("legacy", rows)
    return others


def _write_transaction(root: Path, writes: dict[Path, str | bytes],
                       *, capability: str = "legacy.write",
                       expected_revisions: dict[str, int] | None = None,
                       artifact_ids=(), deletes=(),
                       metadata=None,
                       validate_extra=None) -> tuple[int, list, dict]:
    """Commit one named, receipt-producing canonical transaction.

    A thin call into ``ops/commit.py:commit_proposal``: the body moved there
    unchanged. The legacy context carries the transaction capability as the
    operation, the live gateway channel (else the operator default), a command
    invocation, and the live gateway request; the commit step reads only the
    root from it. Caller containers pass through uncoerced.

    Returns ``(code, errors, confirmation)``. The confirmation travels back to
    the caller explicitly rather than through module state: a command reports
    the receipt for *its own* transaction, and a module global could not
    express that — it outlived the operator lock and was read after release.
    On any failure the confirmation is empty, so a caller cannot accidentally
    report a receipt for a write that did not happen.

    ``validate_extra`` is one plan-class gate: ``validate_extra(repo, issues)``
    receives the staged repository and that run's complete validation issues
    (errors and warnings alike) and returns the refusal list the transaction
    fails on. It runs inside the commit's validation step — after the writes
    land, before anything is published — so a refusal still rolls everything
    back. Without it the gate is the historical errors-only list.
    """
    request = current_gateway_request()
    ctx = OpContext(
        root=root,
        operation=capability,
        channel=request.channel if request is not None else DEFAULT_SESSION_CHANNEL,
        invocation="command",
        gateway=request,
    )
    proposal = TransactionProposal(
        capability=capability,
        writes=writes,
        artifact_ids=artifact_ids,
        deletes=deletes,
        expected_revisions=expected_revisions or {},
        metadata=metadata,
        validate_extra=validate_extra,
    )
    return commit_proposal(ctx, proposal)


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


def _unit_map_or_error(root: Path, unit_id: str):
    repo = load_repo(root)
    unit = repo.units.get(unit_id)
    if unit is None:
        print(f"los: {not_found('unit', unit_id, repo.units)}", file=sys.stderr)
        return repo, None, None
    map_id = unit.data.get("current_study_map")
    study_map = repo.study_maps.get(map_id) if map_id else None
    if study_map is None:
        print(f"los: unit has no current study map: {unit_id}", file=sys.stderr)
        return repo, unit, None
    return repo, unit, study_map


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


# ---------------------------------------------------- validate / generate
def _delegate(script: str, extra: list[str], args) -> int:
    """One implementation of every rule: shell out to the canonical script."""
    cmd = [sys.executable, str(TOOLS / script), *extra]
    if args.root:
        cmd += ["--root", str(_root(args))]
    return subprocess.run(cmd).returncode

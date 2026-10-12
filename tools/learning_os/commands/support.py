"""Shared plumbing for every command: repository root, the operator lock, atomic writes,
the transaction wrapper and its receipt, and the small YAML/Markdown helpers."""

from __future__ import annotations

import json
import re
import subprocess
import sys
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
    _dump_yaml,
    _json_layout,
    _record_gateway_refusal,
)
from learning_os.ops.commit import commit_proposal
from learning_os.ops.context import OpContext
from learning_os.ops.proposal import TransactionProposal
from learning_os.store.session_ledger import DEFAULT_SESSION_CHANNEL
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

"""Judgment-free capture into work/inbox/. Routing stays the operator's job."""

from __future__ import annotations

import datetime as _dt
import json
import re
import sys

from learning_os.contracts.gateway import current_gateway_request

from .support import (
    WriteRefused,
    _expected_revisions_from_args,
    _operator_lock,
    _read_content_bound_file,
    _root,
    _write_transaction,
)


# ---------------------------------------------------------------- capture
def cmd_capture(args) -> int:
    """Judgment-free capture into work/inbox/ with a transaction receipt."""
    root = _root(args)
    with _operator_lock(root):
        inbox = root / "work" / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")

        if args.file:
            try:
                src, content = _read_content_bound_file(
                    args.file,
                    getattr(args, "file_sha256", None),
                    label="capture file",
                )
            except WriteRefused as exc:
                print(f"los: {exc}", file=sys.stderr)
                return 2
            target = inbox / src.name
            if target.exists():
                target = inbox / f"{stamp}-{src.name}"
        else:
            capture_text = args.text if args.text is not None else sys.stdin.read()
            if not capture_text.strip():
                print("los: nothing to capture (empty input)", file=sys.stderr)
                return 2
            slug = re.sub(r"[^a-z0-9]+", "-",
                          (args.title or capture_text).lower()).strip("-")[:40] or "capture"
            target = inbox / f"{stamp}-{slug}.md"
            serial = 2
            while target.exists():
                target = inbox / f"{stamp}-{slug}-{serial}.md"
                serial += 1
            content = (f"# {args.title}\n\n{capture_text}\n" if args.title
                       else capture_text.rstrip() + "\n")

        relative = target.relative_to(root).as_posix()
        gateway_request = current_gateway_request()
        artifact_id = (
            f"capture-request:{gateway_request.idempotency_key}"
            if gateway_request is not None
            else f"capture:{relative}"
        )
        code, errors, confirmation = _write_transaction(
            root, {target: content}, capability="capture.create",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[artifact_id],
        )
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code

    if getattr(args, "json", False):
        print(json.dumps({"ok": True, "captured": relative,
                          **confirmation}, ensure_ascii=False))
        return 0
    print(f"captured -> {relative}")
    print("routing is the operator's job (WORKFLOWS §21); the inbox trends "
          "toward empty")
    return 0

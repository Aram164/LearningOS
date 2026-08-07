"""Review surfaces: shelving prepare/apply and the explicit session close."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from .support import _dump_yaml, _expected_ok, _expected_revisions_from_args, _operator_lock, _publish, _root, _session_ledger, _unit_map_or_error, _write_transaction

TOOLS = Path(__file__).resolve().parent.parent.parent

def cmd_shelving_prepare(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, _, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None:
            return 2
        data = copy.deepcopy(study_map.data)
        items = []
        if args.items_file:
            raw = json.loads(Path(args.items_file).read_text(encoding="utf-8"))
            items = raw.get("items", raw) if isinstance(raw, dict) else raw
            if not isinstance(items, list):
                print("los: shelving items file must contain a JSON list", file=sys.stderr)
                return 2
        proposal_path = study_map.path.parent / "shelving-proposal.md"
        lines = ["# Shelving proposal review packet", "",
                 "> Operational proposal only. No canonical change is applied until selected IDs are explicitly approved.", ""]
        for stage in data.get("stages", []) or []:
            lines.extend([f"## {stage.get('title', stage.get('id'))}", ""])
            note = root / str(stage.get("working_note", ""))
            lines.append(note.read_text(encoding="utf-8", errors="replace") if note.is_file()
                         else "*(No stage note yet.)*")
            lines.append("")
            if stage.get("attachments"):
                lines.append("Attachments: " + ", ".join(a["path"] for a in stage["attachments"]))
                lines.append("")
        shelving = data.setdefault("shelving", {})
        shelving.update({"state": "proposed" if items else "draft",
                          "proposal_path": proposal_path.relative_to(root).as_posix(),
                          "summary": args.summary or "Review stage notes and attachments without rewriting learner wording."})
        if items:
            shelving["items"] = items
        code, errors, confirmation = _write_transaction(
            root, {
                proposal_path: "\n".join(lines).rstrip() + "\n",
                study_map.path: _dump_yaml(data),
            },
            capability="review.prepare",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.unit_id, study_map.id],
        )
        if code:
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "unit_id": args.unit_id,
                      "proposal_path": shelving["proposal_path"],
                      "state": shelving["state"]}, ensure_ascii=False))
    return 0


def _approved_destination(root: Path, item: dict) -> Path | None:
    rel = str(item.get("destination", ""))
    target = (root / rel).resolve()
    allowed = (root / "knowledge" / "notes").resolve(), (root / "knowledge" / "garden").resolve()
    if not any(parent == target or parent in target.parents for parent in allowed):
        return None
    return target


def cmd_shelving_apply(args) -> int:
    if not args.approve:
        print("los: shelving apply requires --approve and explicit selected proposal IDs",
              file=sys.stderr)
        return 2
    root = _root(args)
    selected = set(args.selected)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, _, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None:
            return 2
        data = copy.deepcopy(study_map.data)
        shelving = data.get("shelving") or {}
        items = [item for item in shelving.get("items", []) or []
                 if item.get("id") in selected]
        if not items or {item.get("id") for item in items} != selected:
            print("los: every selected ID must exist in the current proposal", file=sys.stderr)
            return 2
        writes: dict[Path, str] = {}
        for item in items:
            target = _approved_destination(root, item)
            if target is None or target.exists():
                print(f"los: unsafe or existing shelving destination: {item.get('destination')}",
                      file=sys.stderr)
                return 2
            content = item.get("content")
            if not isinstance(content, str) or not content.strip():
                print(f"los: proposal item {item.get('id')} has no reviewable content", file=sys.stderr)
                return 2
            writes[target] = content.rstrip() + "\n"
        shelving["state"] = "applied"
        writes[study_map.path] = _dump_yaml(data)
        code, errors, confirmation = _write_transaction(
            root, writes, capability="review.apply",
            expected_revisions=_expected_revisions_from_args(args),
            artifact_ids=[args.unit_id, study_map.id, *sorted(selected)],
        )
        if code:
            print("los: approved shelving changes failed validation and were rolled back",
                  file=sys.stderr)
            for issue in errors[:12]:
                print(issue, file=sys.stderr)
            return code
    print(json.dumps({"ok": True, "unit_id": args.unit_id,
                      "applied": sorted(selected)}, ensure_ascii=False))
    return 0


def cmd_session_end(args) -> int:
    root = _root(args)
    ledger = _session_ledger(root)
    touched = json.loads(ledger.read_text(encoding="utf-8")) if ledger.is_file() else []
    touched = [path for path in touched
               if path not in {"Untitled.canvas", "Untitled 1.canvas", "Untitled 2.canvas"}]
    # `validate.py` resolves its repository from its own location unless told
    # otherwise, so a bare `cwd=root` would validate the repository the tools
    # live in — not the one this session touched. Pass the root explicitly.
    validation = subprocess.run(
        [sys.executable, str(TOOLS / "validate.py"), "--root", str(root)], cwd=root,
        capture_output=True, text=True)
    if validation.returncode != 0:
        print(validation.stdout, end="")
        print(validation.stderr, end="", file=sys.stderr)
        return validation.returncode or 1
    # Errors gate; warnings are advisory and reported. Gating on zero warnings
    # made session-end impossible in a repository carrying the by-design
    # "material may be offline" set — and validate.py's own contract is that
    # link rot never blocks.
    validation_line = next((line for line in validation.stdout.splitlines()
                            if "warning(s)" in line), "").strip()
    with _operator_lock(root):
        _publish(root)
    all_changed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all", "--", "."],
        cwd=root, capture_output=True, text=True, timeout=30).stdout.splitlines()
    owned = [line for line in all_changed if line[3:] in touched]
    unrelated = [line for line in all_changed if line[3:] not in touched]
    payload = {"ok": True, "touched": touched, "owned_changes": owned,
               "unrelated_changes": unrelated, "committed": False, "pushed": False,
               "validation": validation_line}
    if not args.commit_message:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    if not touched:
        print("los: no files were touched through this learning session", file=sys.stderr)
        return 2
    subprocess.run(["git", "add", "--", *touched], cwd=root, check=True, timeout=30)
    commit = subprocess.run(["git", "commit", "-m", args.commit_message], cwd=root,
                            capture_output=True, text=True, timeout=180)
    if commit.returncode != 0:
        print(commit.stdout, end="")
        print(commit.stderr, end="", file=sys.stderr)
        return commit.returncode
    payload["committed"] = True
    if args.push:
        pushed = subprocess.run(["git", "push"], cwd=root, capture_output=True,
                                text=True, timeout=180)
        if pushed.returncode != 0:
            print(pushed.stdout, end="")
            print(pushed.stderr, end="", file=sys.stderr)
            return pushed.returncode
        payload["pushed"] = True
    ledger.unlink(missing_ok=True)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0

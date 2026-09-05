"""Review surfaces: shelving prepare/apply and the explicit session close."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

from learning_os.unit_notes import unit_note_sections

from .support import (
    WriteRefused,
    _dump_yaml,
    _expected_ok,
    _expected_revisions_from_args,
    _load_session_paths,
    _operator_lock,
    _publish,
    _read_content_bound_file,
    _root,
    _session_ledger,
    _session_path_state,
    _unit_map_or_error,
    _write_transaction,
)

TOOLS = Path(__file__).resolve().parent.parent.parent

def _unit_note_packet_sections(root: Path, unit) -> list[dict]:
    """The learner's saved session reasoning, in the order it was recorded.

    `unit-note` owns session reasoning at the unit's working note; shelving used
    to traverse only stage-owned notes, so a saved section stayed safely stored
    and never reached the review packet it was written for (2026-09-05 audit,
    F06). Both models are read here; neither rewrites the learner's wording.
    """
    if unit is None:
        return []
    declared = str(unit.data.get("working_note") or "").strip()
    note = root / declared if declared else unit.path.parent / "notes.md"
    try:
        resolved = note.resolve()
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return []
    if not resolved.is_file():
        return []
    try:
        text = resolved.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return unit_note_sections(text)


def _packet_note_lines(sections: list[dict], stage_titles: dict[str, str]) -> list[str]:
    lines: list[str] = []
    for section in sections:
        stage_ids = [sid for sid in section.get("stage_ids") or [] if sid]
        context = ", ".join(
            f"{stage_titles.get(sid, sid)} (`{sid}`)" for sid in stage_ids
        ) or "no stage named"
        lines.extend([
            f"### {section.get('title') or 'Learning session note'}", "",
            f"*Session note recorded {section.get('recorded_at') or 'at an unrecorded time'}"
            f" — stage context: {context}.*", "",
            section.get("text") or "*(Empty section.)*", "",
        ])
        attachments = section.get("attachments") or []
        if attachments:
            lines.extend([
                "Attachments: " + ", ".join(
                    str(item.get("path")) for item in attachments
                    if isinstance(item, dict) and item.get("path")
                ),
                "",
            ])
    return lines


def cmd_shelving_prepare(args) -> int:
    root = _root(args)
    with _operator_lock(root):
        if not _expected_ok(root, args.expected_snapshot):
            return 3
        _, unit, study_map = _unit_map_or_error(root, args.unit_id)
        if study_map is None:
            return 2
        data = copy.deepcopy(study_map.data)
        items = []
        if args.items_file:
            try:
                _source, item_bytes = _read_content_bound_file(
                    args.items_file,
                    getattr(args, "items_file_sha256", None),
                    label="shelving items file",
                )
                raw = json.loads(item_bytes.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError, WriteRefused) as exc:
                print(f"los: cannot read shelving items: {exc}", file=sys.stderr)
                return 2
            items = raw.get("items", raw) if isinstance(raw, dict) else raw
            if not isinstance(items, list):
                print("los: shelving items file must contain a JSON list", file=sys.stderr)
                return 2
        proposal_path = study_map.path.parent / "shelving-proposal.md"
        stage_titles = {
            str(stage.get("id")): str(stage.get("title") or stage.get("id"))
            for stage in data.get("stages", []) or []
            if isinstance(stage, dict) and stage.get("id")
        }
        sections = _unit_note_packet_sections(root, unit)
        lines = ["# Shelving proposal review packet", "",
                 "> Operational proposal only. No canonical change is applied until selected IDs are explicitly approved.", ""]
        lines.extend(["## Session notes", ""])
        if sections:
            lines.extend(_packet_note_lines(sections, stage_titles))
        else:
            lines.extend(["*(No session note saved for this unit yet.)*", ""])
        seen_stage_notes: set[str] = set()
        for stage in data.get("stages", []) or []:
            note_ref = str(stage.get("working_note", ""))
            note = root / note_ref if note_ref else None
            stage_text = (
                note.read_text(encoding="utf-8", errors="replace")
                if note is not None and note.is_file() else ""
            ).strip()
            attachments = stage.get("attachments") or []
            # A stage with neither recorded text nor attachments would add an
            # empty heading between the sections that do carry reasoning.
            if not stage_text and not attachments:
                continue
            if note_ref and note_ref in seen_stage_notes:
                continue
            if note_ref:
                seen_stage_notes.add(note_ref)
            lines.extend([f"## {stage.get('title', stage.get('id'))}", "",
                          f"*Stage note `{note_ref}`.*" if note_ref else "*Stage note.*",
                          ""])
            lines.append(stage_text or "*(No stage note text; attachments only.)*")
            lines.append("")
            if attachments:
                lines.append("Attachments: " + ", ".join(a["path"] for a in attachments))
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
                      "state": shelving["state"],
                      **confirmation}, ensure_ascii=False))
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
                      "applied": sorted(selected),
                      **confirmation}, ensure_ascii=False))
    return 0


def cmd_session_end(args) -> int:
    root = _root(args)
    ledger = _session_ledger(root)
    try:
        recorded = _load_session_paths(root)
    except WriteRefused as exc:
        print(f"los: {exc}", file=sys.stderr)
        return 2
    touched = sorted(
        path for path in recorded if Path(path).suffix.lower() != ".canvas"
    )
    ownership_conflicts = [
        path for path in touched
        if _session_path_state(root, path) != recorded[path]
    ]
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
    # "material may be offline" set. External link rot is gated only by the
    # explicit online validator and never runs during session-end.
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
               "validation": validation_line,
               "ownership_conflicts": ownership_conflicts}
    if not args.commit_message:
        # A review-only close ends this ownership window. Keeping the ledger
        # would make a later session inherit paths it never touched.
        ledger.unlink(missing_ok=True)
        payload["session_closed"] = True
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 0
    if not touched:
        print("los: no files were touched through this learning session", file=sys.stderr)
        return 2
    ownership_conflicts = [
        path for path in touched
        if _session_path_state(root, path) != recorded[path]
    ]
    payload["ownership_conflicts"] = ownership_conflicts
    if ownership_conflicts:
        print(
            "los: refusing to stage files changed after their recorded LearningOS "
            "transaction: " + ", ".join(ownership_conflicts),
            file=sys.stderr,
        )
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

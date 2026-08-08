#!/usr/bin/env python3
"""Learning OS CLI — the stable machine gateway for interface layers (ADR-006).

    python tools/los.py status            # one-screen repository state
    python tools/los.py bootstrap         # AI/app startup contract + active paths
    python tools/los.py status --json     # same, machine-readable (stable keys)
    python tools/los.py validate          # delegate to tools/validate.py
    python tools/los.py generate          # delegate to tools/generate.py
    python tools/los.py path-note ...     # save stage-bound working notes
    python tools/los.py path-progress ... # advance the ordered path
    python tools/los.py capture ...       # drop an unrelated capture into work/inbox/

Interface layers (the Obsidian UI project, scripts, agents) call THESE
commands instead of parsing YAML or reimplementing rules. The Python loader
remains the single authority; `validate` and `generate` are thin delegations
to the canonical scripts, so there is exactly one implementation of every
rule.

Deliberately NOT here (OPERATOR.md, CLAUDE.md §3–§5, §14): anything requiring operator
judgment — routing inbox items, creating notes and assigning roles, harvesting
the Garden, finishing sessions, semantic edits. `capture` is the one write
because it is judgment-free: it puts bytes in `work/inbox/`, where routing is
explicitly the operator's job. Exit codes: 0 ok · 1 validation errors ·
2 usage/environment error · 3 optimistic-concurrency conflict.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from learning_os.ai_actions import AIActionError, StaleDeliveryError  # noqa: E402

# Command registry: one module per domain, so a behaviour is found by name.
from learning_os.commands.ai import (  # noqa: E402
    cmd_ai_action_apply_delivery, cmd_ai_action_import_delivery, cmd_ai_action_list,
    cmd_ai_action_prepare, cmd_ai_action_status, cmd_ai_action_validate_delivery,
)
from learning_os.commands.capability import (  # noqa: E402
    cmd_capability,
)
from learning_os.commands.capture import (  # noqa: E402
    cmd_capture,
)
from learning_os.commands.detour import (  # noqa: E402
    cmd_detour_create, cmd_detour_resolve,
)
from learning_os.commands.module import (  # noqa: E402
    cmd_module_list, cmd_module_plan_import,
)
from learning_os.commands.note import (  # noqa: E402
    cmd_note_evidence, cmd_note_revise,
)
from learning_os.commands.path import (  # noqa: E402
    cmd_path_attach, cmd_path_note, cmd_path_progress,
)
from learning_os.commands.project import (  # noqa: E402
    cmd_project_create, cmd_project_list, cmd_project_update,
)
from learning_os.commands.query import (  # noqa: E402
    cmd_bootstrap, cmd_capabilities, cmd_generate, cmd_inspect, cmd_program_list,
    cmd_related, cmd_search, cmd_status, cmd_validate,
)
from learning_os.commands.review import (  # noqa: E402
    cmd_session_end, cmd_shelving_apply, cmd_shelving_prepare,
)
from learning_os.commands.source import (  # noqa: E402
    cmd_source_feedback,
)
from learning_os.commands.stage import (  # noqa: E402
    cmd_stage_attach, cmd_stage_note, cmd_stage_progress,
)
from learning_os.commands.support import (  # noqa: E402
    WriteRefused, _add_expected_revision_argument,
)
from learning_os.commands.unit import (  # noqa: E402
    cmd_unit_list, cmd_unit_map_import, cmd_unit_note,
)


# --------------------------------------------------------- parser / main
def build_parser() -> argparse.ArgumentParser:
    """The complete CLI surface.

    Factored out of ``main`` so the capability gateway can introspect it:
    a capability's payload schema is derived from the very parser that
    defines its named command, which makes the two provably the same
    surface instead of two hand-maintained copies that drift.
    """
    parser = argparse.ArgumentParser(
        prog="los", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=None,
                        help="repository root (default: parent of tools/)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("status", help="one-screen repository state")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("capabilities", help="discover the stable operator contract")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.set_defaults(func=cmd_capabilities)

    p = sub.add_parser("bootstrap", help="machine bootstrap with active learning paths")
    p.set_defaults(func=cmd_bootstrap)

    p = sub.add_parser("search", help="search the complete fresh projection")
    p.add_argument("query")
    p.add_argument("--type", default=None, help="optional record type")
    p.add_argument("--limit", type=int, default=50)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("inspect", help="inspect one record by stable id")
    p.add_argument("id")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("related", help="list records related to one stable id")
    p.add_argument("id")
    p.set_defaults(func=cmd_related)

    p = sub.add_parser("program-list", help="list programs and boundary areas")
    p.set_defaults(func=cmd_program_list)

    p = sub.add_parser("module-list", help="list modules with optional program/status filters")
    p.add_argument("--program-id", default=None)
    p.add_argument("--status", default=None)
    p.set_defaults(func=cmd_module_list)

    p = sub.add_parser("unit-list", help="list units with optional module/component/status filters")
    p.add_argument("--module-id", default=None)
    p.add_argument("--component-id", default=None)
    p.add_argument("--status", default=None)
    p.set_defaults(func=cmd_unit_list)


    p = sub.add_parser("project-list", help="list first-class projects")
    p.add_argument("--status", default=None)
    p.set_defaults(func=cmd_project_list)

    p = sub.add_parser("project-create", help="create one first-class project transactionally")
    p.add_argument("--file", required=True)
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_project_create)

    p = sub.add_parser("project-update", help="replace one project with revision protection")
    p.add_argument("project_id")
    p.add_argument("--file", required=True)
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_project_update)

    p = sub.add_parser("capability", help="execute a declared capability request envelope")
    p.add_argument("name")
    p.add_argument("--payload-file", required=True)
    p.set_defaults(func=cmd_capability)

    p = sub.add_parser("validate", help="delegate to tools/validate.py")
    p.add_argument("--online", action="store_true", help="also audit external URLs")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("generate", help="delegate to tools/generate.py")
    p.set_defaults(func=cmd_generate)

    p = sub.add_parser("ai-action-list", help="list provider-independent AI actions")
    p.set_defaults(func=cmd_ai_action_list)

    p = sub.add_parser("ai-action-prepare", help="persist a bounded AI request bundle")
    p.add_argument("--action-id", required=True)
    p.add_argument("--target-kind", required=True)
    p.add_argument("--target-id", required=True)
    p.add_argument("--provider", default="manual-bundle")
    p.add_argument("--expected-snapshot", default=None)
    p.add_argument("--request-id", default=None)
    p.add_argument("--confirm-job-export", action="store_true")
    p.set_defaults(func=cmd_ai_action_prepare)

    p = sub.add_parser("ai-action-import-delivery",
                       help="import and validate an approved delivery directory")
    p.add_argument("path")
    p.set_defaults(func=cmd_ai_action_import_delivery)

    p = sub.add_parser("ai-action-validate-delivery",
                       help="validate one imported delivery without applying it")
    p.add_argument("delivery_id")
    p.set_defaults(func=cmd_ai_action_validate_delivery)

    p = sub.add_parser("ai-action-apply-delivery",
                       help="atomically apply one approved, validated delivery")
    p.add_argument("delivery_id")
    p.set_defaults(func=cmd_ai_action_apply_delivery)

    p = sub.add_parser("ai-action-status", help="show one prepared request status")
    p.add_argument("request_id")
    p.set_defaults(func=cmd_ai_action_status)

    p = sub.add_parser("capture",
                       help="drop text or a file into work/inbox/ (no routing)")
    p.add_argument("--text", default=None, help="capture this text (else stdin)")
    p.add_argument("--file", default=None, help="copy this file into the inbox")
    p.add_argument("--title", default=None, help="optional title for text captures")
    p.add_argument("--json", action="store_true",
                   help="confirm structurally instead of in prose (used by the app)")
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_capture)

    p = sub.add_parser("unit-map-import",
                       help="create/import the single current study map for a unit")
    p.add_argument("unit_id")
    p.add_argument("--file", required=True)
    p.add_argument("--replace", action="store_true")
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_unit_map_import)

    p = sub.add_parser("module-plan-import",
                       help="transactionally import a standardized module plan and its units")
    p.add_argument("module_id")
    p.add_argument("--file", required=True)
    p.add_argument("--check", action="store_true",
                   help="run contract, routing, and shadow-repository validation without writing")
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_module_plan_import)

    p = sub.add_parser("note-revise",
                       help="replace one existing note after explicit full-file review")
    p.add_argument("note_id")
    p.add_argument("--file", required=True)
    p.add_argument("--approve", action="store_true")
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_note_revise)

    p = sub.add_parser("note-evidence",
                       help="record one evidence trail on a note; the body is never touched")
    p.add_argument("note_id")
    p.add_argument("evidence_type", choices=("derivation", "explanation", "implementation",
                                             "exercise", "exam", "external"))
    p.add_argument("ref", help="typed URI for the trail, e.g. material://…, note://…, https://…")
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_note_evidence)


    p = sub.add_parser("unit-note", help="append one session-level section to a unit working note")
    p.add_argument("unit_id")
    p.add_argument("--title", default=None)
    p.add_argument("--text", default=None)
    p.add_argument("--stage-id", action="append", default=[],
                   help="completed stage context; repeat for multiple stages")
    p.add_argument("--attachment", action="append", default=[],
                   help="copy one file into the unit note attachments; repeatable")
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_unit_note)

    p = sub.add_parser("stage-note", help="save or append a unit-stage working note")
    p.add_argument("unit_id")
    p.add_argument("stage_id")
    p.add_argument("--text", default=None)
    p.add_argument("--replace", action="store_true")
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_stage_note)

    p = sub.add_parser("stage-progress", help="activate, pause, complete, skip, or revisit a unit stage")
    p.add_argument("unit_id")
    p.add_argument("stage_id")
    p.add_argument("status", choices=("active", "paused", "complete", "skipped", "revisit"))
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_stage_progress)

    p = sub.add_parser("stage-attach", help="attach a file inside a unit stage")
    p.add_argument("unit_id")
    p.add_argument("stage_id")
    p.add_argument("--file", required=True)
    p.add_argument("--label", default=None)
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_stage_attach)

    p = sub.add_parser("source-feedback", help="record stage-local evidence about source usefulness")
    p.add_argument("unit_id")
    p.add_argument("stage_id")
    p.add_argument("source_id")
    p.add_argument("feedback", choices=("helpful", "too-advanced", "wrong-perspective",
                                        "useful-for-derivation", "useful-for-review", "skipped"))
    p.add_argument("--note", default=None)
    # ADR-009: narrow the judgment to one identified resource inside source_id —
    # one paper in a bundled course, one chapter of a book. Without this the
    # write path cannot reach the identity the records already carry, so four
    # opinions about four AMLS papers still collapse into one indistinguishable
    # set. source_id stays required either way, so provenance is never lost.
    p.add_argument("--resource-id", default=None,
                   help="optional resource-* id on the same stage to attach this judgment to")
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_source_feedback)

    p = sub.add_parser("detour-create", help="record a prerequisite detour with a return stage")
    p.add_argument("unit_id")
    p.add_argument("stage_id")
    p.add_argument("--title", required=True)
    p.add_argument("--classification", required=True,
                   choices=("required-now", "helpful-now", "deferred", "reference-only"))
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_detour_create)

    p = sub.add_parser("detour-resolve", help="resolve a detour and return to its originating stage")
    p.add_argument("unit_id")
    p.add_argument("detour_id")
    p.add_argument("--resolution", default=None)
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_detour_resolve)

    p = sub.add_parser("shelving-prepare", help="prepare a review packet; never applies canonical changes")
    p.add_argument("unit_id")
    p.add_argument("--items-file", default=None,
                   help="optional JSON proposal items produced with explicit unit context")
    p.add_argument("--summary", default=None)
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_shelving_prepare)

    p = sub.add_parser("shelving-apply", help="apply only explicitly approved proposal IDs")
    p.add_argument("unit_id")
    p.add_argument("--selected", nargs="+", required=True)
    p.add_argument("--approve", action="store_true")
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_shelving_apply)

    p = sub.add_parser("session-end", help="validate, show exact session-owned files, optionally commit/push")
    p.add_argument("--commit-message", default=None)
    p.add_argument("--push", action="store_true")
    p.set_defaults(func=cmd_session_end)

    p = sub.add_parser("path-note", help="save or append working notes for one path stage")
    p.add_argument("path_id")
    p.add_argument("stage_id")
    p.add_argument("--text", default=None, help="note text (else stdin)")
    p.add_argument("--replace", action="store_true", help="replace this stage note")
    p.add_argument("--expected-snapshot", default=None,
                   help="optimistic concurrency token from manifest _generated.snapshot_id")
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_path_note)

    p = sub.add_parser("path-progress", help="advance or activate a learning path stage")
    p.add_argument("path_id")
    p.add_argument("stage_id")
    p.add_argument("status", choices=("active", "complete", "skipped"))
    p.add_argument("--expected-snapshot", default=None,
                   help="optimistic concurrency token from manifest _generated.snapshot_id")
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_path_progress)

    p = sub.add_parser("path-attach", help="copy handwriting/media into a stage-owned attachment folder")
    p.add_argument("path_id")
    p.add_argument("stage_id")
    p.add_argument("--file", required=True)
    p.add_argument("--label", default=None)
    p.add_argument("--expected-snapshot", default=None,
                   help="optimistic concurrency token from manifest _generated.snapshot_id")
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_path_attach)

    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except StaleDeliveryError as exc:
        print(f"los: {exc}", file=sys.stderr)
        return 3
    except AIActionError as exc:
        print(f"los: {exc}", file=sys.stderr)
        return 1
    except WriteRefused as exc:
        # Nothing was changed: _atomic_text cleans up its temp file and
        # _write_transaction rolls the set back before re-raising.
        print(f"los: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

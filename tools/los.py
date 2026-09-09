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

from learning_os.ai_actions import AIActionError, StaleDeliveryError  # noqa: E402
from learning_os.backup_manifest import BackupManifestError  # noqa: E402

# Command registry: one module per domain, so a behaviour is found by name.
from learning_os.commands.ai import (  # noqa: E402
    cmd_ai_action_apply_delivery,
    cmd_ai_action_import_delivery,
    cmd_ai_action_list,
    cmd_ai_action_prepare,
    cmd_ai_action_status,
    cmd_ai_action_validate_delivery,
)
from learning_os.commands.atlas import (  # noqa: E402
    cmd_atlas_context,
    cmd_atlas_question_save,
    cmd_concept_relations_change,
)
from learning_os.commands.capability import cmd_capability  # noqa: E402
from learning_os.commands.capture import cmd_capture  # noqa: E402
from learning_os.commands.detour import cmd_detour_create, cmd_detour_resolve  # noqa: E402
from learning_os.commands.garden import cmd_garden_seed_create  # noqa: E402
from learning_os.commands.intelligence import cmd_intelligence_scan  # noqa: E402
from learning_os.commands.material import (  # noqa: E402
    cmd_module_materials_compact,
    cmd_plan_edit_context,
    cmd_route_patch,
)
from learning_os.commands.module import cmd_module_list, cmd_module_plan_import  # noqa: E402
from learning_os.commands.note import cmd_note_evidence, cmd_note_revise  # noqa: E402
from learning_os.commands.path import (  # noqa: E402
    cmd_path_attach,
    cmd_path_note,
    cmd_path_progress,
)
from learning_os.commands.plan import cmd_plan_template  # noqa: E402
from learning_os.commands.project import (  # noqa: E402
    cmd_project_create,
    cmd_project_list,
    cmd_project_update,
)
from learning_os.commands.query import (  # noqa: E402
    cmd_bootstrap,
    cmd_capabilities,
    cmd_generate,
    cmd_inspect,
    cmd_program_list,
    cmd_related,
    cmd_search,
    cmd_status,
    cmd_validate,
)
from learning_os.commands.reads import cmd_note_read  # noqa: E402
from learning_os.commands.review import (  # noqa: E402
    cmd_session_end,
    cmd_shelving_apply,
    cmd_shelving_prepare,
)
from learning_os.commands.source import cmd_source_feedback  # noqa: E402
from learning_os.commands.stage import (  # noqa: E402
    cmd_stage_attach,
    cmd_stage_note,
    cmd_stage_progress,
)
from learning_os.commands.support import WriteRefused, _add_expected_revision_argument  # noqa: E402
from learning_os.commands.unit import (  # noqa: E402
    cmd_unit_list,
    cmd_unit_map_import,
    cmd_unit_note,
    cmd_unit_source_selection,
)
from learning_os.commands.vnext import (  # noqa: E402
    cmd_backup_manifest,
    cmd_backup_verify,
    cmd_health_report,
    cmd_job_learning_migrate,
    cmd_legacy_archive_inspect,
    cmd_legacy_archive_lock_publish,
    cmd_legacy_archive_status,
    cmd_masters_planning_catalog_update,
    cmd_masters_planning_comparison_publish,
    cmd_masters_planning_dashboard,
    cmd_route_identity_migrate,
    cmd_unit_material_synthesis_publish,
)
from learning_os.contracts.payloads import json_object, sha256_value  # noqa: E402
from learning_os.health import HealthReportError  # noqa: E402
from learning_os.legacy_archive import LegacyArchiveError  # noqa: E402
from learning_os.masters_planning import MastersPlanningError  # noqa: E402
from learning_os.material_synthesis import MaterialSynthesisError  # noqa: E402
from learning_os.transactions import TransactionFailure  # noqa: E402


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
    p.add_argument("name", nargs="?", help="one public capability, including its declared payload schema")
    p.add_argument("--compact", action="store_true", help="JSON index of capability names; fetch one name for details")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.set_defaults(func=cmd_capabilities)

    p = sub.add_parser("bootstrap", help="machine bootstrap with active learning paths")
    p.add_argument("--compact", action="store_true", help="bounded startup summaries; details stay available through inspect")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--expected-snapshot", default=None)
    p.set_defaults(func=cmd_bootstrap)

    p = sub.add_parser("search", help="search the complete fresh projection")
    p.add_argument("query")
    p.add_argument("--type", default=None, help="optional record type")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--content", action="store_true", help="search complete durable note text with exact line snippets")
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--expected-snapshot", default=None)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("intelligence-scan", help="read-only observation loop: propose candidate investigations")
    p.add_argument("--days", type=int, default=30, help="recency window for changed files (default: 30)")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.set_defaults(func=cmd_intelligence_scan)

    p = sub.add_parser("note-read", help="read a bounded segment of a durable note by stable ID")
    p.add_argument("note_id")
    p.add_argument("--offset", type=int, default=0, help="zero-based Unicode character offset")
    p.add_argument("--limit", type=int, default=8000, help="maximum characters, bounded to 16000")
    p.add_argument("--expected-snapshot", default=None)
    p.set_defaults(func=cmd_note_read)

    p = sub.add_parser("inspect", help="inspect one record by stable id")
    p.add_argument("id")
    p.add_argument("more_ids", nargs="*", help="inspect up to 20 records from one fresh snapshot")
    p.set_defaults(func=cmd_inspect)

    p = sub.add_parser("related", help="list records related to one stable id")
    p.add_argument("id")
    p.set_defaults(func=cmd_related)

    p = sub.add_parser("program-list", help="list programs and boundary areas")
    p.set_defaults(func=cmd_program_list)

    p = sub.add_parser(
        "plan-template",
        help="print the one canonical authored-plan template for a domain profile",
    )
    p.add_argument("profile", choices=("curriculum",))
    p.add_argument("--title", required=True)
    p.add_argument("--unit-id", default=None)
    p.add_argument("--module-id", default=None)
    p.add_argument(
        "--json",
        action="store_true",
        help="answer the plan-template-v1 query envelope instead of YAML (used by the interface)",
    )
    p.set_defaults(func=cmd_plan_template)

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

    # `--file` for humans, `--project` for callers already holding the record.
    # Both are declared, so the generated payload schema describes the surface
    # the gateway actually accepts (engineering audit 2026-08-08, finding 2).
    p = sub.add_parser("project-create", help="create one first-class project transactionally")
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--file")
    source.add_argument("--project", type=json_object, help="the project record as inline JSON")
    p.add_argument(
        "--file-sha256", type=sha256_value, default=None,
        help="SHA-256 of the exact project file bytes approved for this request",
    )
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_project_create)

    p = sub.add_parser("project-update", help="replace one project with revision protection")
    p.add_argument("project_id")
    source = p.add_mutually_exclusive_group(required=True)
    source.add_argument("--file")
    source.add_argument("--project", type=json_object, help="the project record as inline JSON")
    p.add_argument(
        "--file-sha256", type=sha256_value, default=None,
        help="SHA-256 of the exact project file bytes approved for this request",
    )
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_project_update)

    p = sub.add_parser("capability", help="execute a declared capability request envelope")
    p.add_argument("name")
    p.add_argument("--payload-file", required=True)
    p.add_argument(
        "--replay-only", action="store_true",
        help="verify an already committed idempotent receipt without running the handler",
    )
    # Capability dispatch reuses this parser without importing the CLI module
    # back from the command package. Passing the factory explicitly keeps the
    # command graph acyclic while retaining one parser as the schema authority.
    p.set_defaults(func=cmd_capability, _parser_factory=build_parser)

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
    p.add_argument(
        "--delivery-sha256",
        required=True,
        help="SHA-256 of the exact imported delivery.yaml bytes",
    )
    p.add_argument(
        "--artifact-sha256",
        required=True,
        type=json_object,
        help="JSON object mapping every artifact_ref to its exact SHA-256",
    )
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_ai_action_apply_delivery)

    p = sub.add_parser("ai-action-status", help="show one prepared request status")
    p.add_argument("request_id")
    p.set_defaults(func=cmd_ai_action_status)

    p = sub.add_parser(
        "unit-material-synthesis-publish",
        help="check or publish one reviewed unit material dossier",
    )
    p.add_argument("unit_id")
    record = p.add_mutually_exclusive_group(required=True)
    record.add_argument("--file")
    record.add_argument("--record", type=json_object)
    p.add_argument("--check", action="store_true")
    p.add_argument("--approve", action="store_true")
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_unit_material_synthesis_publish)

    p = sub.add_parser(
        "legacy-archive-inspect",
        help="inspect only explicitly allowlisted safe Legacy files",
    )
    p.add_argument("--archive-root", required=True)
    p.add_argument("--allowlist", required=True)
    p.set_defaults(func=cmd_legacy_archive_inspect)

    p = sub.add_parser(
        "legacy-archive-status",
        help="read the last approved Legacy archive lock without rescanning",
    )
    p.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    p.set_defaults(func=cmd_legacy_archive_status)

    p = sub.add_parser(
        "legacy-archive-lock-publish",
        help="publish one reviewed safe Legacy disposition lock",
    )
    record = p.add_mutually_exclusive_group(required=True)
    record.add_argument("--file")
    record.add_argument("--record", type=json_object)
    p.add_argument("--approve", action="store_true")
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_legacy_archive_lock_publish)

    p = sub.add_parser(
        "masters-planning-dashboard",
        help="open the sanitized prospective planning catalog deliberately",
    )
    p.add_argument("--confirm-masters-planning", action="store_true")
    p.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    p.set_defaults(func=cmd_masters_planning_dashboard)

    p = sub.add_parser(
        "masters-planning-catalog-update",
        help="publish a reviewed academic-only prospective catalog",
    )
    record = p.add_mutually_exclusive_group(required=True)
    record.add_argument("--file")
    record.add_argument("--record", type=json_object)
    p.add_argument("--approve", action="store_true")
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_masters_planning_catalog_update)

    p = sub.add_parser(
        "masters-planning-comparison-publish",
        help="publish one reviewed prospective source comparison",
    )
    p.add_argument("candidate_module_id")
    record = p.add_mutually_exclusive_group(required=True)
    record.add_argument("--file")
    record.add_argument("--record", type=json_object)
    p.add_argument("--approve", action="store_true")
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_masters_planning_comparison_publish)

    p = sub.add_parser(
        "route-identity-migrate",
        help="atomically apply one exact approved v13 route-identity diff",
    )
    p.add_argument(
        "--plan-sha256",
        required=True,
        type=sha256_value,
        help="sha256 of the exact dry-run unified diff",
    )
    p.add_argument(
        "--review",
        type=json_object,
        default=None,
        help="inline schema-version-1 route review bound to the approved plan",
    )
    p.add_argument("--approve", action="store_true")
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_route_identity_migrate)

    p = sub.add_parser(
        "job-learning-migrate",
        help="atomically migrate the exact approved legacy Job learning set",
    )
    p.add_argument(
        "--plan-sha256",
        required=True,
        type=sha256_value,
        help="sha256 of the exact deterministic migration plan",
    )
    p.add_argument("--approve", action="store_true")
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_job_learning_migrate)

    p = sub.add_parser("health-report", help="build one explicit vNext health report")
    p.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    p.set_defaults(func=cmd_health_report)

    desc = (
        "A backup carries Core's canonical data and the UI checkout in full. "
        "Core's own code is deliberately not included. Recovery pairs the restored data "
        "with a Core checkout at the commit the manifest records."
    )
    p = sub.add_parser(
        "backup-manifest",
        help="hash the explicit LearningOS backup allowlist",
        description=desc,
    )
    p.add_argument("--ui-root", default=None)
    p.add_argument("--materials-root", default=None)
    p.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    p.set_defaults(func=cmd_backup_manifest)

    p = sub.add_parser(
        "backup-verify", help="verify a trusted restore against a backup manifest",
        description="Full verification runs the restored installer in dry-run mode against a "
        "temporary vault. Use --checksums-only to check integrity without executing restored code. "
        "A backup carries Core's canonical data and the UI checkout in full. "
        "Core's own code is deliberately not included. Recovery pairs the restored data "
        "with a Core checkout at the commit the manifest records.",
    )
    p.add_argument("--manifest", required=True)
    p.add_argument("--restored-core", required=True)
    p.add_argument("--restored-ui", required=True)
    p.add_argument("--restored-materials", required=True)
    p.add_argument(
        "--checksums-only", action="store_true",
        help="skip projection, validation, installer dry-run, and restored UI bundle smoke checks",
    )
    p.set_defaults(func=cmd_backup_verify)

    p = sub.add_parser("capture",
                       help="drop text or a file into work/inbox/ (no routing)")
    p.add_argument("--text", default=None, help="capture this text (else stdin)")
    p.add_argument("--file", default=None, help="copy this file into the inbox")
    p.add_argument(
        "--file-sha256", type=sha256_value, default=None,
        help="SHA-256 of the exact file bytes approved for this capture",
    )
    p.add_argument("--title", default=None, help="optional title for text captures")
    p.add_argument("--json", action="store_true",
                   help="confirm structurally instead of in prose (used by the app)")
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_capture)

    p = sub.add_parser(
        "garden-seed-create",
        help="plant one free-form Garden seed without classification or AI",
    )
    p.add_argument(
        "--text",
        required=True,
        help="the seed text exactly as supplied by the learner",
    )
    p.add_argument(
        "--title",
        default=None,
        help="optional explicit title; mechanically prepended as Markdown H1",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="confirm structurally instead of in prose (used by the app)",
    )
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_garden_seed_create)

    p = sub.add_parser("atlas-context", help="read connection editor guards and personal questions for one concept")
    p.add_argument("concept_id")
    p.add_argument("--expected-snapshot", default=None)
    p.set_defaults(func=cmd_atlas_context)

    p = sub.add_parser("concept-relations-change", help="apply only explicitly authored relation operations")
    p.add_argument("--change", required=True, type=json_object)
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_concept_relations_change)

    p = sub.add_parser("atlas-question-save", help="save or resolve an explicitly authored personal question")
    p.add_argument("--question", required=True, type=json_object)
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_atlas_question_save)

    p = sub.add_parser("plan-edit-context", help="read compact plan or one material's edit context")
    p.add_argument("unit_id")
    route = p.add_mutually_exclusive_group()
    route.add_argument("--route-id", default=None,
                       help="one exact route and its stage overrides")
    route.add_argument("--route-ids", nargs="+", default=None, metavar="ROUTE_ID",
                       help="1 to 20 distinct routes of this unit, in requested order")
    p.add_argument("--expected-snapshot", default=None)
    p.set_defaults(func=cmd_plan_edit_context)

    p = sub.add_parser("route-patch", help="edit one route and synchronize its exact references")
    p.add_argument("unit_id")
    p.add_argument("route_id")
    p.add_argument("--changes", type=json_object, required=True)
    p.add_argument("--check", action="store_true")
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_route_patch)

    p = sub.add_parser("module-materials-compact", help="losslessly share repeated stage material fields")
    p.add_argument("module_id")
    p.add_argument("--check", action="store_true")
    p.add_argument("--plan-sha256", type=sha256_value, default=None)
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_module_materials_compact)

    p = sub.add_parser("unit-map-import",
                       help="create/import the single current study map for a unit")
    p.add_argument("unit_id")
    p.add_argument("--file", required=True)
    p.add_argument(
        "--file-sha256", type=sha256_value, default=None,
        help="SHA-256 of the exact study-map file bytes approved for import",
    )
    p.add_argument("--replace", action="store_true")
    p.add_argument(
        "--check", action="store_true",
        help="print the concrete replacement diff and write nothing",
    )
    p.add_argument(
        "--intentional-reorder", default=None, metavar="REASON",
        help="reviewed reason for changing the relative order of surviving stages",
    )
    p.add_argument(
        "--intentional-state-reset", default=None, metavar="REASON",
        help="reviewed reason for discarding preserved stage and map state",
    )
    p.add_argument(
        "--retire-stage", action="append", default=None, metavar="STAGE_ID",
        help="acknowledge one stage this revision removes (repeatable)",
    )
    p.add_argument(
        "--retire-reason", default=None, metavar="REASON",
        help="reviewed disposition for the evidence of every retired stage",
    )
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_unit_map_import)

    p = sub.add_parser("module-plan-import",
                       help="transactionally import a standardized module plan and its units")
    p.add_argument("module_id")
    module_plan_source = p.add_mutually_exclusive_group(required=True)
    module_plan_source.add_argument(
        "--file",
        help="reviewed YAML plan for an existing canonical module",
    )
    module_plan_source.add_argument(
        "--promotion",
        type=json_object,
        help=(
            "inline MasterPlanning promotion package; live application is "
            "GatewayEnvelopeV2-only"
        ),
    )
    p.add_argument(
        "--file-sha256", type=sha256_value, default=None,
        help="SHA-256 of the exact module-plan file bytes approved for import",
    )
    p.add_argument(
        "--package-sha256",
        default=None,
        help="exact promotion package hash returned by --check",
    )
    p.add_argument(
        "--approve",
        action="store_true",
        help="direct approval flag; GatewayEnvelopeV2 owns this value for live promotion",
    )
    p.add_argument("--check", action="store_true",
                   help="run contract, routing, and shadow-repository validation without writing")
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_module_plan_import)

    p = sub.add_parser("note-revise",
                       help="replace one existing note after explicit full-file review")
    p.add_argument("note_id")
    p.add_argument("--file", required=True)
    p.add_argument(
        "--file-sha256", type=sha256_value, default=None,
        help="SHA-256 of the exact replacement-note bytes approved for revision",
    )
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
    p.add_argument(
        "--attachment-sha256", action="append", default=[], type=sha256_value,
        help="SHA-256 for the corresponding --attachment; repeat in the same order",
    )
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_unit_note)

    p = sub.add_parser(
        "unit-source-selection",
        help="select or remove one material option from a unit's complete menu",
    )
    p.add_argument("unit_id")
    p.add_argument("source_id")
    p.add_argument("locator")
    p.add_argument("action", choices=("select", "remove"))
    p.add_argument("--purpose", default=None)
    p.add_argument("--expected-snapshot", default=None)
    _add_expected_revision_argument(p)
    p.set_defaults(func=cmd_unit_source_selection)

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
    p.add_argument(
        "--file-sha256", type=sha256_value, default=None,
        help="SHA-256 of the exact attachment bytes approved for this request",
    )
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
    p.add_argument(
        "--items-file-sha256", type=sha256_value, default=None,
        help="SHA-256 of the exact shelving-items file bytes approved for review",
    )
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
    p.add_argument(
        "--file-sha256", type=sha256_value, default=None,
        help="SHA-256 of the exact attachment bytes approved for this request",
    )
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
    except TransactionFailure as exc:
        print(f"los: {exc}", file=sys.stderr)
        return 2
    except (MaterialSynthesisError, LegacyArchiveError, MastersPlanningError,
            BackupManifestError, HealthReportError) as exc:
        print(f"los: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

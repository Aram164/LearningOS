"""Area groups for the test suite (test-suite-trim).

Every ``test_*.py`` file belongs to exactly one group. ``conftest.py`` applies
the group name as a pytest marker at collection time (so ``pytest -m gateway``
runs one area), and :func:`groups_for_paths` maps changed files to the groups
that must rerun (used by ``tools/affected_tests.py`` and ``make test-affected``).

Conventions:
* A test file lives in the group of the subsystem it pins, not the harness it
  uses. CLI-driven tests of the write path are ``gateway``; CLI-driven tests of
  plans, materials or dossiers stay with their area.
* Shared machinery (loader, rules, generator framework, transactions,
  contracts, schemas) maps to ALL groups — that is expected and encoded below.
* Unknown paths map to ALL groups (fail closed). Narrow a rule only when the
  area boundary is certain.
"""

from __future__ import annotations

from pathlib import Path

GROUPS: dict[str, list[str]] = {
    # Curriculum, study maps, routes, units, plan revisions and promotion.
    "studyplan": [
        "test_curriculum_v2.py",
        "test_lecture_study_map_assembly.py",
        "test_learning_paths.py",
        "test_learning_plan_contract.py",
        "test_master_promotion.py",
        "test_module_lifecycle.py",
        "test_compact_module_plan_revision.py",
        "test_module_plan_warning_gate.py",
        "test_phaseB_prospective_lineage.py",
        "test_lineage_writer_interpositions.py",
        "test_pilot_replay.py",
        "test_plan_edit_brief.py",
        "test_plan_inventory.py",
        "test_plan_resume.py",
        "test_plan_rigor.py",
        "test_plan_write_once.py",
        "test_study_map_obligation.py",
        "test_unit_plan_revision.py",
    ],
    # Materials farm, attachments, slices, summaries, ingestion.
    "materials": [
        "test_build_materials_tree.py",
        "test_ingest_transcript.py",
        "test_material_analysis_save.py",
        "test_material_context.py",
        "test_material_context_boundaries.py",
        "test_material_editing.py",
        "test_material_locator_fallback.py",
        "test_material_observation_port.py",
        "test_material_slices.py",
        "test_material_span.py",
        "test_material_summaries.py",
        "test_material_text_cache.py",
        "test_materials_manifest.py",
        "test_materials_catalogue.py",
        "test_verbatim.py",
        "test_verbatim_anchor_admission.py",
    ],
    # Semantics, synthesis, dossiers, goals, runtime, operator questions.
    "synthesis": [
        "test_abilities.py",
        "test_agent_tasks.py",
        "test_ai_actions.py",
        "test_context_dossiers.py",
        "test_evidence_staleness.py",
        "test_goal_lifecycle_properties.py",
        "test_goal_proposals.py",
        "test_claim_status_audits.py",
        "test_goal_select.py",
        "test_lineage_restamp.py",
        "test_model_question_scoring.py",
        "test_policy_query.py",
        "test_proof_carrying_change.py",
        "test_resume_dossier.py",
        "test_semantic_contract.py",
        "test_semantic_lineage.py",
        "test_session_compiler.py",
        "test_session_counts.py",
        "test_synthesis_analysis_refs.py",
        "test_unit_dossier_command.py",
        "test_verified_operator_questions.py",
        "test_vnext_boundaries.py",
    ],
    # Generation, projections, views, derived state, search index, Garden.
    "generation": [
        "test_derived_engine.py",
        "test_derived_state.py",
        "test_garden_projection.py",
        "test_garden_seed.py",
        "test_generation.py",
        "test_manifest_reuse.py",
        "test_module_concept_atlas.py",
        "test_projection_fidelity.py",
        "test_related.py",
        "test_render.py",
        "test_search_index.py",
        "test_thematic_navigation_projection.py",
    ],
    # Contracts, manifest, normative corpus, tree contract, UI contract mirror.
    "contracts": [
        "test_contract_bundle.py",
        "test_contract_differential.py",
        "test_contract_register.py",
        "test_manifest_contract.py",
        "test_manifest_stages.py",
        "test_manifest_routes.py",
        "test_normative_corpus.py",
        "test_procedures.py",
        "test_release_pair_receipt.py",
        "test_source_examination.py",
        "test_tree_contract.py",
    ],
    # Gateways, CLI, capabilities, transactions, recovery, operations,
    # diagnostics, and the write path they exercise.
    "gateway": [
        "test_agent_efficiency.py",
        "test_atlas_authoring.py",
        "test_bounded_reads.py",
        "test_capability_catalog.py",
        "test_capability_dispatch.py",
        "test_capability_receipts.py",
        "test_causal_resolver.py",
        "test_cli.py",
        "test_codex_wrapper.py",
        "test_diagnostic_store.py",
        "test_evidence_parity.py",
        "test_inbox_resolve.py",
        "test_intelligence_scan.py",
        "test_note_create.py",
        "test_note_evidence.py",
        "test_observation_gesture.py",
        "test_observations.py",
        "test_operator_lock.py",
        "test_operations.py",
        "test_operations_gate.py",
        "test_ops_check.py",
        "test_ops_commit.py",
        "test_ops_context.py",
        "test_ops_pipeline.py",
        "test_arch_error_details.py",
        "test_expansion_runnable.py",
        "test_projects.py",
        "test_read_suggestions.py",
        "test_recovery_conflicts.py",
        "test_resume_pointer.py",
        "test_scenario_fixtures.py",
        "test_search_hints.py",
        "test_search_values.py",
        "test_source_intake.py",
        "test_source_record_revise.py",
        "test_stage_result.py",
        "test_collection_entry_revise.py",
        "test_coordination_revision.py",
        "test_structural_inspect.py",
        "test_trace_context.py",
        "test_transactions.py",
        "test_transaction_faults.py",
        "test_architecture_hardening_adversarial.py",
        "test_ui_gateway_recovery.py",
        "test_validation_cache.py",
        "test_workspace_next_action.py",
        "test_write_scopes.py",
        "test_gateway_v2.py",
        "test_gateway_choice_parity.py",
        "test_gateway_typed_refusals.py",
        "test_scenarios_effects.py",
        "test_scenarios_health_shim.py",
        "test_scenarios_recovery.py",
        "test_scenarios_session.py",
        "test_scenarios_zz_operational_owners.py",
        "test_scenarios_zz_refusal_sites.py",
        "test_seal_guards_auto.py",
        "test_write_payload_clarity.py",
        "test_session_ledger.py",
    ],
    # Validation, hygiene, perimeter, audits, and architecture guards.
    "validation": [
        "test_affected_tests.py",
        "test_arch_caches.py",
        "test_arch_doc_commands.py",
        "test_arch_doc_command_controls.py",
        "test_arch_doc_blocks.py",
        "test_arch_engine_neutrality.py",
        "test_arch_error_vocabulary.py",
        "test_arch_idroundtrip.py",
        "test_arch_layers.py",
        "test_arch_types.py",
        "test_arch_outcomes.py",
        "test_arch_plumbing.py",
        "test_arch_private_names.py",
        "test_arch_callbacks.py",
        "test_arch_cli_parity.py",
        "test_arch_json_everywhere.py",
        "test_arch_output.py",
        "test_arch_prose.py",
        "test_arch_ratchets.py",
        "test_arch_request_schemas.py",
        "test_arch_suggestions.py",
        "test_arch_surface.py",
        "test_arch_world.py",
        "test_arch_writes.py",
        "test_code_reachability.py",
        "test_compute_once.py",
        "test_digest_review.py",
        "test_deep_audit_repairs.py",
        "test_domain_failures.py",
        "test_domain_stages.py",
        "test_external_urls.py",
        "test_failures_prefixed.py",
        "test_ops_encoders.py",
        "test_githistory.py",
        "test_local_attachments.py",
        "test_health_vnext.py",
        "test_hygiene.py",
        "test_improvements.py",
        "test_library_reconciliation.py",
        "test_mismatches.py",
        "test_module_surface.py",
        "test_move_map.py",
        "test_perimeter.py",
        "test_resource_integrity.py",
        "test_runtime_efficiency.py",
        "test_runtime_review.py",
        "test_scenarios.py",
        "test_source_discovery.py",
        "test_system_audit_2026_09_05.py",
        "test_tool_entrypoint_contract.py",
        "test_validation.py",
        "test_warning_baseline.py",
        "test_workflows.py",
        "test_pre_push_hook.py",
    ],
    # Migrations and multi-year format compatibility.
    "migrations": [
        "test_format_fixtures.py",
        "test_job_quarantine_collapse.py",
        "test_legacy_exit_review.py",
        "test_migration_lifecycle.py",
        "test_route_identity_migration.py",
        "test_summaries_migration.py",
    ],
}

FILE_TO_GROUP: dict[str, str] = {
    name: group for group, names in GROUPS.items() for name in names
}

ALL_GROUPS = frozenset(GROUPS)

# (path prefix, groups) — first match wins, ``None`` means all groups.
# Order matters: specific production areas first, shared machinery late,
# canonical data and the catch-all last.
PATH_RULES: list[tuple[str, frozenset[str] | None]] = [
    # --- test files map to their own group (handled before prefix rules) ---
    # --- area production code ---
    ("tools/learning_os/derive/material_synthesis.py", frozenset({"materials", "synthesis", "studyplan", "generation", "contracts"})),
    ("tools/learning_os/store/material_analysis.py", frozenset({"materials", "synthesis", "studyplan", "generation", "contracts"})),
    ("tools/learning_os/material_", frozenset({"materials"})),
    ("tools/learning_os/materials_", frozenset({"materials"})),
    ("tools/learning_os/commands/material.py", frozenset({"materials", "gateway", "studyplan"})),
    ("tools/material_summarize.py", frozenset({"materials", "studyplan"})),
    ("tools/material_text.py", frozenset({"materials"})),
    ("tools/material_toc.py", frozenset({"materials"})),
    ("tools/ingest_transcript.py", frozenset({"materials"})),
    ("tools/build_materials_index.py", frozenset({"materials"})),
    ("tools/build_materials_tree.py", frozenset({"materials"})),
    ("tools/materials_index/", frozenset({"materials"})),
    ("tools/materials_manifest.py", frozenset({"materials"})),
    ("tools/normalise_material_uris.py", frozenset({"materials"})),
    ("tools/migrations/lift_angle_out_of_locator.py", frozenset({"materials", "studyplan"})),
    ("tools/assemble_lecture_study_maps.py", frozenset({"studyplan"})),
    ("tools/verify_plan_receipt.py", frozenset({"studyplan"})),
    ("tools/plan_write_audit.py", frozenset({"studyplan"})),
    ("tools/refresh_amls_fixture.py", frozenset({"studyplan"})),
    ("tools/learning_os/derive/routes.py", frozenset({"studyplan"})),
    ("tools/learning_os/domain/route_identity.py", frozenset({"studyplan", "migrations"})),
    ("tools/learning_os/domain/unit_notes.py", frozenset({"studyplan"})),
    ("tools/learning_os/app/admin/masters_planning.py", frozenset({"studyplan"})),
    ("tools/learning_os/derive/semantics/", frozenset({"synthesis"})),
    ("tools/learning_os/app/ai_actions/", frozenset({"synthesis"})),
    ("tools/learning_os/derive/learning_runtime.py", frozenset({"synthesis"})),
    ("tools/learning_os/derive/search/", frozenset({"generation"})),
    ("tools/learning_os/derive/garden.py", frozenset({"generation"})),
    ("tools/learning_os/store/derived/", frozenset({"generation", "contracts"})),
    ("tools/learning_os/commands/query.py", frozenset({"synthesis", "gateway"})),
    ("tools/learning_os/commands/ai.py", frozenset({"synthesis", "gateway"})),
    ("tools/learning_os/commands/operations.py", frozenset({"gateway"})),
    ("tools/learning_os/commands/capability.py", frozenset({"gateway"})),
    ("tools/learning_os/commands/plan.py", frozenset({"gateway", "studyplan"})),
    ("tools/learning_os/commands/module.py", frozenset({"gateway", "studyplan"})),
    ("tools/learning_os/commands/source_catalog.py", frozenset({"gateway"})),
    ("tools/learning_os/commands/project.py", frozenset({"gateway"})),
    ("tools/learning_os/commands/review.py", frozenset({"gateway", "studyplan"})),
    ("tools/learning_os/commands/lineage_restamp.py", frozenset({"synthesis", "gateway"})),
    ("tools/learning_os/commands/workspace.py", frozenset({"gateway"})),
    ("tools/learning_os/store/diagnostics/", frozenset({"gateway"})),
    ("tools/diagnostics_prune.py", frozenset({"gateway"})),
    ("tools/seal_envelope.py", frozenset({"gateway"})),
    ("tools/learning_os/store/contracts/", frozenset({"contracts", "gateway"})),
    ("tools/contract_bundle.py", frozenset({"contracts"})),
    ("tools/schema_contract.py", frozenset({"contracts"})),
    ("tools/manifest_contract.py", frozenset({"contracts"})),
    ("tools/tree_contract.py", frozenset({"contracts"})),
    ("tools/release_pair_receipt.py", frozenset({"contracts"})),
    ("tools/verified_pairs.py", frozenset({"validation"})),
    ("tools/evaluate_operator_questions.py", frozenset({"synthesis"})),
    ("tools/codex_obsidian.py", frozenset({"gateway"})),
    ("tools/code_reachability.py", frozenset({"validation"})),
    ("tools/library_reconciliation.py", frozenset({"validation"})),
    ("tools/legacy_exit_review.py", frozenset({"migrations"})),
    ("tools/migrations/", frozenset({"migrations", "gateway"})),
    ("tools/stress_check.py", frozenset({"validation"})),
    ("tools/generate_capability_schemas.py", frozenset({"gateway", "contracts"})),
    # --- shared machinery: every group ---
    ("tools/learning_os/store/loader.py", None),
    ("tools/learning_os/store/loading/", None),
    ("tools/learning_os/derive/validation/", None),
    ("tools/learning_os/derive/projection/", None),
    ("tools/learning_os/store/transactions.py", None),
    ("tools/learning_os/store/revisions.py", None),
    ("tools/learning_os/store/evidence.py", None),
    ("tools/learning_os/store/fingerprint.py", None),
    ("tools/learning_os/domain/failures.py", None),
    ("tools/learning_os/store/layout.py", None),
    ("tools/learning_os/store/warning_baseline.py", None),
    ("tools/learning_os/store/session/githistory.py", None),
    ("tools/learning_os/app/backup_manifest.py", None),
    ("tools/learning_os/store/legacy_archive.py", None),
    ("tools/learning_os/domain/render.py", None),
    ("tools/learning_os/derive/health.py", None),
    ("tools/learning_os/__init__.py", None),
    ("tools/learning_os/commands/__init__.py", None),
    ("tools/learning_os/commands/support.py", None),
    ("tools/los.py", None),
    ("tools/validate.py", None),
    ("tools/generate.py", None),
    ("tools/warning_baseline.py", None),
    ("system/schema/", None),
    ("system/contracts/", None),
    ("system/templates/", None),
    # --- canonical data: the full_repo tests pin it across groups ---
    ("knowledge/", None),
    ("curriculum/", None),
    ("sources/", None),
    ("records/", None),
    ("work/", None),
    ("operations/", None),
    ("migration/", frozenset({"migrations", "validation", "studyplan"})),
    ("archive/", frozenset({"migrations", "validation"})),
    ("bases/", frozenset({"generation", "validation"})),
    ("projects/", frozenset({"gateway", "validation"})),
    # --- repo config and CI ---
    (".github/", frozenset({"validation"})),
    ("tools/hooks/", frozenset({"validation"})),
    ("tests/fixtures/", None),
    ("tests/benchmark_", frozenset({"gateway"})),
    ("tests/diagnosis_baseline.py", frozenset({"gateway"})),
]


def check_map(test_dir: Path | None = None) -> list[str]:
    """Every ``test_*.py`` in exactly one group; returns error strings."""
    root = Path(test_dir) if test_dir is not None else Path(__file__).resolve().parent
    on_disk = sorted(p.name for p in root.glob("test_*.py"))
    errors = []
    seen: dict[str, str] = {}
    for group, names in GROUPS.items():
        for name in names:
            if name in seen:
                errors.append(f"{name} is in both {seen[name]} and {group}")
            seen[name] = group
    for name in on_disk:
        if name not in seen:
            errors.append(f"{name} is on disk but in no group")
    for name in seen:
        if name not in on_disk:
            errors.append(f"{name} is grouped but missing on disk")
    return errors


def groups_for_paths(paths: list[str]) -> set[str]:
    """Changed repo-relative paths -> groups to rerun (fail closed: ALL)."""
    groups: set[str] = set()
    for raw in paths:
        path = raw.strip().lstrip("./")
        if not path:
            continue
        name = path.rsplit("/", 1)[-1]
        if path.startswith("tests/") and name in FILE_TO_GROUP:
            groups.add(FILE_TO_GROUP[name])
            continue
        if path in ("tests/conftest.py", "tests/group_map.py",
                    "tests/repo_builders.py", "tests/gateway_helpers.py"):
            return set(ALL_GROUPS)
        matched: frozenset[str] | None | bool = False
        for prefix, rule_groups in PATH_RULES:
            if path == prefix.rstrip("/") or path.startswith(prefix):
                matched = rule_groups
                break
        if matched is False or matched is None:
            return set(ALL_GROUPS)
        groups.update(matched)
    return groups


def tests_for_groups(groups: set[str]) -> list[str]:
    """Sorted ``tests/<file>`` paths for the given groups."""
    files = [f"tests/{name}" for group in groups for name in GROUPS.get(group, [])]
    return sorted(files)

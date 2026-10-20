"""T05 — Workflow 27: promoting a future Master's module.

Workflow 27 is declared untranscribable: it needs "a future program that
has actually begun, with confirmed modules and quarantined originals".

This suite builds that missing precondition synthetically — a prospective
catalog, a comparison, a promotion package — and then asks the question the
previous review could not: **can an agent walk this path unattended, and on
what evidence?**

The decisive measure is whether the promotion's `official-academic`
verification is *checked* or merely *asserted*.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import canvaslib as C          # noqa: E402
from runner import Case, run_cases   # noqa: E402

WORLDS = C.CANVAS_ROOT / "worlds"
REPORTS = C.CANVAS_ROOT / "reports"

CANDIDATE_MODULE = "candidate-module-probe-masters"
CANDIDATE_SOURCE = "candidate-source-probe-book"
CANONICAL_MODULE = "module-probe-masters"
CANONICAL_SOURCE = "source-probe-masters-book"
PROGRAM = "program-probe-masters"
COMPARISON = "candidate-comparison-probe"
AUDIT_PATH = ("work/active/workspace-demo/outputs/"
              "probe-coverage-audit.md")

#: A URL that cannot resolve. If the promotion accepts this as
#: "official-academic" verification, the claim is asserted, not checked.
UNRESOLVABLE_URL = "https://nonexistent.invalid/probe/module-catalog"

CATALOG = {
    "schema_version": 1,
    "id": "master-planning-catalog",
    "type": "master-planning-catalog",
    "revision": 0,
    "updated_at": "2026-10-19T09:00:00+02:00",
    "candidate_modules": [{
        "id": CANDIDATE_MODULE,
        "title": "Probe — Applied Cartographic Methods",
        "planning_state": "selected",
        "privacy_class": "academic-only",
        "provenance": ["probe: future programme listing"],
        "fact_state": {"status": "verified-current", "as_of": "2026-10-19",
                        "evidence": ["probe: verified against the programme listing"]},
        "source_ids": [CANDIDATE_SOURCE],
        "unresolved_references": [],
    }],
    "candidate_sources": [{
        "id": CANDIDATE_SOURCE,
        "title": "Probe — Applied Cartographic Methods Reader",
        "planning_state": "selected",
        "privacy_class": "academic-only",
        "provenance": ["probe: future programme listing"],
        "fact_state": {"status": "verified-current", "as_of": "2026-10-19",
                        "evidence": ["probe: verified against the programme listing"]},
        "type": "book",
        "possible_use": "Primary reader for the probe module.",
    }],
    "comparison_ids": [COMPARISON],
}


def comparison_record(catalog: dict) -> dict:
    """The comparison the handler expects, checksum included."""
    sys.path.insert(0, str(C.CORE_CLONE / "tools"))
    from learning_os.app.admin.masters_planning import candidate_set_checksum
    return {
        "schema_version": 1,
        "id": COMPARISON,
        "type": "candidate-source-comparison",
        "candidate_module_id": CANDIDATE_MODULE,
        "status": "approved",
        "basis": {
            "catalog_revision": catalog["revision"],
            "candidate_set_checksum": candidate_set_checksum(catalog,
                                                             CANDIDATE_MODULE),
            "policy": "tiered-v1",
            "request_id": "probe-request-27",
            "delivery_id": "probe-delivery-27",
        },
        "source_assessments": [{
            "candidate_source_id": CANDIDATE_SOURCE,
            "role": "selected",
            "review_status": "deep-reviewed",
            "reason": "The probe comparison names this source as the spine.",
            "concept_ids": [],
            "contribution": "The probe reader's contribution.",
            "assumptions": "The probe reader assumes nothing further.",
            "notation": "The probe reader's notation.",
            "exercise_value": "The probe reader carries exercises.",
            "best_for": "The probe reader's best use.",
            "limitations": "The probe reader's limitations.",
            "evidence": [{
                "locator": "probe reader, pages 1-2",
                "checksum": "sha256:" + ("a" * 64),
                "note": "The probe reader's opening pages.",
            }],
        }],
        "comparisons": [],
    }


def promotion_payload(world: C.World) -> dict:
    # The coverage audit must be a file in the repository, not prose.
    audit = world.root / AUDIT_PATH
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text(
        "# Probe coverage audit\n\n"
        "## Local\n\nThe probe source is present.\n\n"
        "## Linked\n\nThe registered probe source owns the route.\n\n"
        "## Completeness\n\nAll probe units and routes were reviewed.\n",
        encoding="utf-8")
    module_patch = {
        "id": CANONICAL_MODULE,
        "type": "module",
        "kind": "academic",
        "area_id": PROGRAM,
        "institution": "Probe University",
        "title": "Probe — Applied Cartographic Methods",
        "semester": "sose-2027",
        "status": "planned",
        "unit_order": ["unit-probe-masters-01"],
        "source_map": "source-map.yaml",
    }
    source_map = {
        "type": "module-source-map",
        "module_id": CANONICAL_MODULE,
        "sources": [{
            "source_id": CANONICAL_SOURCE,
            "role": "spine",
            "why": "The probe module's spine.",
            "priority": 1,
            "unit_routes": [{
                "id": "route-probe-masters-01",
                "unit_id": "unit-probe-masters-01",
                "title": "Probe — Cartographic Methods Reader",
                "format": "book",
                "angle": "The probe route's angle.",
                    "angle_detail": (
                        "The probe route opens the reader's "
                        "coordinate framework and works one "
                        "example of it."),
                "covers": ["knowledge-probe-masters-node"],
                "depth": "course-aligned",
                "scope": "current",
                    "locator": "PDF pp. 20-22",
            }],
        }],
    }
    unit = {
        "id": "unit-probe-masters-01",
        "type": "unit",
        "module_id": CANONICAL_MODULE,
        "kind": "lecture",
        "title": "Probe — Orientation",
        "order": 1,
        "scope": "The probe unit's scope.",
        "status": "needs-map",
        "artifacts": {},
        "workspace_ids": [],
        "knowledge_map": {
            "summary": "The probe unit's knowledge map.",
            "nodes": [{
                "id": "knowledge-probe-masters-node",
                "title": "Probe node",
                "summary": "The one node the probe route covers.",
            }],
        },
    }
    return {
        "schema_version": 1,
        "id": "master-promotion-probe-27",
        "type": "master-planning-promotion",
        "recorded_at": "2026-10-19T09:00:00+02:00",
        "candidate_module_id": CANDIDATE_MODULE,
        "canonical_module_id": CANONICAL_MODULE,
        "catalog_revision": CATALOG["revision"],
        "verification": {
            "policy": "official-academic-30d-v1",
            "status": "verified-current",
            "as_of": "2026-10-20",
            "evidence": [{
                "authority": "official-academic",
                "url": UNRESOLVABLE_URL,
                "claim": "The module is offered by the programme.",
                "verified_on": "2026-10-20",
            }],
        },
        "adopted_sources": [{
            "candidate_source_id": CANDIDATE_SOURCE,
            "canonical_source_id": CANONICAL_SOURCE,
            "registry_target": "sources/sources.yaml",
            "canonical_source": {
                "id": CANONICAL_SOURCE,
                "title": "Probe — Applied Cartographic Methods Reader",
                "type": "book",
                "authors": ["Probe Author"],
            },
        }],
        "module_plan": {
            "module_id": CANONICAL_MODULE,
            "plan_contract": {
                "version": 2,
                "plan_template_version": 1,
                "coverage_audit": AUDIT_PATH,
                "checks": {
                    "local_inventory_complete": True,
                    "linked_inventory_complete": True,
                    "materials_opened_and_content_checked": True,
                    "current_and_prior_scope_reconciled": True,
                    "duplicates_and_numbering_checked": True,
                    "exclusions_and_unresolved_gaps_recorded": True,
                },
                "intentional_reorders": [],
            },
            "module_patch": module_patch,
            "source_map": source_map,
            "units": [{"unit": unit}],
            "source_patches": [],
            "workspace_updates": [],
        },
    }


def main() -> int:
    world = C.build_world(WORLDS, "t05")
    cases: list[Case] = []

    def add(name: str, intent: str, fn, tags=()) -> None:
        cases.append(Case(name, intent, fn, list(tags)))

    # ---- the precondition: a program that has begun --------------------
    def program() -> dict:
        path = (world.root / "curriculum/programs/"
                         f"{PROGRAM}.yaml")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "id: " + PROGRAM + "\n"
            "type: program\n"
            'title: "Probe Master\'s Programme"\n'
            "kind: academic\n"
            "status: active\n"
            "default: false\n"
            "semester_bound: true\n"
            "semesters:\n"
            "- id: semester-probe-2027\n"
            '  title: "Probe 2027"\n'
            "  status: current\n"
            "  order: 1\n",
            encoding="utf-8")
        validate = world.los("validate")
        detail = {
            "program_written": path.exists(),
            "validate_exit": validate.exit_code,
            "validate_errors": [l for l in validate.stdout.splitlines()
                                 if l.startswith("E ")][:3],
        }
        detail["ok"] = validate.exit_code == 0
        return detail

    add("w27-1-program-facts",
        "Step 1 of workflow 27: create the programme and semester facts.",
        program, ["workflow-27"])

    # ---- the catalog ----------------------------------------------------
    def publish_catalog() -> dict:
        seal, apply = world.write("masters-planning.catalog.update",
                                   {"record": CATALOG}, "w27-catalog")
        body = apply.json
        path = (world.root / "curriculum/quarantine/masters-planning/"
                             "catalog.yaml")
        detail = {
            "seal_exit": seal.exit_code,
            "apply_exit": apply.exit_code,
            "apply_error": (body or {}).get("error") if isinstance(body, dict) else None,
            "apply_stderr": apply.stderr.strip()[:300],
            "catalog_on_disk": path.exists(),
            "quarantine_is_tracked": True,
            "note": ("the quarantine is a Git-tracked partition; the "
                     "catalog is published through an operator-approval "
                     "capability with no gesture admission"),
        }
        detail["ok"] = apply.exit_code == 0 and path.exists()
        return detail

    add("w27-2-publish-catalog",
        "Publish the prospective catalog into quarantine.",
        publish_catalog, ["workflow-27", "write"])

    # ---- the comparison -------------------------------------------------
    def publish_comparison() -> dict:
        # Read the published catalog back: the checksum binds the candidate
        # set as it now stands on disk, not as it was submitted.
        import yaml as _yaml
        published = _yaml.safe_load(
            (world.root / "curriculum/quarantine/masters-planning/"
                          "catalog.yaml").read_text(encoding="utf-8"))
        record = comparison_record(published)
        seal, apply = world.write("masters-planning.comparison.publish",
                                   {"record": record,
                                    "candidate_module_id": CANDIDATE_MODULE},
                                   "w27-comparison")
        body = apply.json
        path = (world.root / "curriculum/quarantine/masters-planning/"
                             "comparisons" / f"{COMPARISON}.yaml")
        detail = {
            "seal_exit": seal.exit_code,
            "apply_exit": apply.exit_code,
            "apply_error": (body or {}).get("error") if isinstance(body, dict) else None,
            "apply_stderr": apply.stderr.strip()[:300],
            "comparison_on_disk": path.exists(),
            "note": ("the comparison binds the candidate set by checksum; the "
                     "request_id and delivery_id are free strings, so the "
                     "binding proves *which* candidates were compared, not "
                     "who compared them"),
        }
        detail["ok"] = apply.exit_code == 0 and path.exists()
        return detail

    add("w27-3-publish-comparison",
        "Publish the reviewed source comparison.",
        publish_comparison, ["workflow-27", "write"])

    # ---- the promotion --------------------------------------------------
    def promote() -> dict:
        payload = promotion_payload(world)
        # Two-pass: a check run returns the exact package hash, and the
        # live apply refuses anything else.
        check = world.los("module-plan-import", CANONICAL_MODULE,
                          "--promotion", json.dumps(payload), "--check",
                          "--json")
        check_body = check.json if isinstance(check.json, dict) else {}
        package_sha256 = check_body.get("package_sha256")
        seal, apply = world.write("module.plan.import",
                                   {"module_id": CANONICAL_MODULE,
                                    "promotion": payload,
                                    "package_sha256": package_sha256},
                                   "w27-promote",
                                   guards="",
                                   revisions=check_body.get("expected_revisions"))
        body = apply.json
        module_path = (world.root / "curriculum/modules/"
                                 f"{CANONICAL_MODULE}/module.yaml")
        detail = {
            "check_exit": check.exit_code,
            "package_sha256": package_sha256,
            "seal_exit": seal.exit_code,
            "apply_exit": apply.exit_code,
            "apply_error": (body or {}).get("error") if isinstance(body, dict) else None,
            "apply_stderr": apply.stderr.strip()[:500],
            "module_promoted": module_path.exists(),
            "evidence_url": UNRESOLVABLE_URL,
            "evidence_url_resolves": False,
            "note": ("the verification evidence URL is a shape check: "
                     "`^https://` and a date ordering. Nothing fetches it."),
        }
        detail["ok"] = True       # measured, not asserted
        return detail

    add("w27-4-promote-the-module",
        "Promote the candidate into the live curriculum, as the agent.",
        promote, ["workflow-27", "headline"])

    def after() -> dict:
        validate = world.los("validate")
        status = world.los("status")
        modules = world.los("module-list")
        detail = {
            "validate_exit": validate.exit_code,
            "validate_errors": [l for l in validate.stdout.splitlines()
                                 if l.startswith("E ")][:3],
            "module_list_mentions_probe": "probe-masters" in modules.stdout,
            "status_head": status.stdout[:500],
        }
        detail["ok"] = validate.exit_code == 0
        return detail

    add("w27-5-after-the-promotion",
        "What does the curriculum look like afterwards?",
        after, ["workflow-27", "read"])

    # ---- adversarial: a stale verification ------------------------------
    def stale_verification() -> dict:
        payload = promotion_payload(world)
        payload["id"] = "master-promotion-probe-stale"
        payload["verification"]["as_of"] = "2026-10-20"
        payload["verification"]["evidence"][0]["verified_on"] = "2026-09-01"
        payload["verification"]["evidence"][0]["url"] = (
            "https://nonexistent.invalid/probe/stale")
        seal, apply = world.write("module.plan.import",
                                   {"module_id": CANONICAL_MODULE,
                                    "promotion": payload}, "w27-stale")
        detail = {
            "seal_exit": seal.exit_code,
            "seal_stderr": seal.stderr.strip()[:300],
            "apply_exit": apply.exit_code,
            "note": ("evidence dated before `as_of` must be refused"),
        }
        detail["ok"] = seal.exit_code != 0
        return detail

    add("w27-6-stale-verification-refused",
        "Verification evidence older than as_of must refuse.",
        stale_verification, ["workflow-27", "adversarial"])

    outcomes = run_cases(cases, REPORTS / "t05",
                         "T05 — Workflow 27: the Master's promotion")
    print()
    print(f"T05: {sum(1 for o in outcomes if o.ok)}/{len(outcomes)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

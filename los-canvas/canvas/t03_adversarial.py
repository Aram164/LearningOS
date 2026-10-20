"""T03 — Adversarial probes.

Each case tries to make the system do the wrong thing. The system is
expected to refuse, name the reason, and leave no canonical byte moved.
A case that ends with "the system did the wrong thing" is a finding, not
a failure of the test: the detail records exactly what happened so the
report can quote it.

Coverage:
  A  idempotency and the double-write
  B  optimistic concurrency (stale snapshot, racing writers)
  C  authority (scope, approval, bare commands)
  D  fail-closed (a validation error must block every canonical write)
  E  agent improvisation on the three untranscribable workflows
  F  malformed input reaching canonical state
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import canvaslib as C          # noqa: E402
from runner import Case, run_cases   # noqa: E402

WORLDS = C.CANVAS_ROOT / "worlds"
REPORTS = C.CANVAS_ROOT / "reports"

UNIT = "unit-demo-l01"
STAGE = "stage-demo"
WORKSPACE = "workspace-demo"


def fingerprint(world: C.World) -> str:
    """The canonical fingerprint of a world (what a write must move)."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(C.CORE_CLONE / "tools")
    proc = subprocess.run(
        [str(C.VENV_PY), "-c",
         "from learning_os.store.fingerprint import canonical_fingerprint;"
         "import sys;from pathlib import Path;"
         "print(canonical_fingerprint(Path(sys.argv[1])))",
         str(world.root)],
        capture_output=True, text=True, env=env, timeout=180)
    return proc.stdout.strip()


def receipts(world: C.World) -> list[str]:
    directory = world.root / "operations" / "transactions"
    return sorted(p.name for p in directory.glob("transaction-*.yaml"))


def write_text(world: C.World, relative: str, text: str) -> Path:
    path = world.root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def main() -> int:
    cases: list[Case] = []

    def add(name: str, intent: str, fn, tags=()) -> None:
        cases.append(Case(name, intent, fn, list(tags)))

    # =================================================================
    # A. idempotency
    # =================================================================
    def a1() -> dict:
        """Resubmitting the same sealed envelope must replay, not write twice."""
        world = C.build_world(WORLDS, "t03-a1")
        payload = {"text": "Synthetic idempotency probe."}
        seal, first = world.write("capture.create", payload, "a1-key")
        envelope = world.scratch("envelope-a1-key.json")
        before_fp, before_receipts = fingerprint(world), receipts(world)
        second = world.apply("capture.create", envelope)
        after_fp, after_receipts = fingerprint(world), receipts(world)
        body = second.json
        return {
            "first_ok": (first.json or {}).get("ok"),
            "first_receipt": (first.json or {}).get("receipt_path"),
            "second_exit": second.exit_code,
            "second_ok": (body or {}).get("ok") if isinstance(body, dict) else None,
            "second_replayed": (body or {}).get("replayed") if isinstance(body, dict) else None,
            "second_transaction": (body or {}).get("transaction_id") if isinstance(body, dict) else None,
            "fingerprint_unchanged": before_fp == after_fp,
            "receipt_count": [len(before_receipts), len(after_receipts)],
            "ok": (first.exit_code == 0 and second.exit_code == 0
                   and before_fp == after_fp
                   and len(before_receipts) == len(after_receipts)
                   and isinstance(body, dict) and body.get("replayed") is True),
        }

    add("a1-replay-same-envelope",
        "An exact retry of the same intent must replay the receipt, not write twice.",
        a1, ["adversarial", "idempotency"])

    def a2() -> dict:
        """Re-sealing the same intent under the same key must be refused."""
        world = C.build_world(WORLDS, "t03-a2")
        payload = {"text": "Synthetic reseal probe."}
        seal, first = world.write("capture.create", payload, "a2-key")
        before_fp, before_receipts = fingerprint(world), receipts(world)
        seal2 = world.seal("capture.create", payload, "a2-key",
                           request_id="request-a2-second")
        applied = (world.apply("capture.create",
                               world.scratch("envelope-a2-key.json"))
                   if seal2.exit_code == 0 else None)
        after_fp, after_receipts = fingerprint(world), receipts(world)
        body = applied.json if applied else None
        return {
            "first_ok": (first.json or {}).get("ok"),
            "reseal_exit": seal2.exit_code,
            "reseal_stderr": seal2.stderr.strip()[:400],
            "apply_exit": applied.exit_code if applied else None,
            "apply_error": (body or {}).get("error") if isinstance(body, dict) else None,
            "apply_stderr": applied.stderr.strip()[:300] if applied else None,
            "fingerprint_unchanged": before_fp == after_fp,
            "receipt_count": [len(before_receipts), len(after_receipts)],
            "ok": ((applied is not None and applied.exit_code != 0)
                   and before_fp == after_fp
                   and len(before_receipts) == len(after_receipts)),
        }

    add("a2-reseal-under-used-key",
        "Re-sealing a used idempotency key must be refused, not double-written.",
        a2, ["adversarial", "idempotency"])

    def a3() -> dict:
        """The same key with a different intent must be refused."""
        world = C.build_world(WORLDS, "t03-a3")
        world.write("capture.create", {"text": "Original intent."}, "a3-key")
        before_fp, before_receipts = fingerprint(world), receipts(world)
        seal2 = world.seal("capture.create", {"text": "Different intent."},
                           "a3-key", request_id="request-a3-second")
        applied = (world.apply("capture.create",
                               world.scratch("envelope-a3-key.json"))
                   if seal2.exit_code == 0 else None)
        after_fp, after_receipts = fingerprint(world), receipts(world)
        body = applied.json if applied else None
        return {
            "reseal_exit": seal2.exit_code,
            "reseal_stderr": seal2.stderr.strip()[:400],
            "apply_exit": applied.exit_code if applied else None,
            "apply_error": (body or {}).get("error") if isinstance(body, dict) else None,
            "apply_stderr": applied.stderr.strip()[:300] if applied else None,
            "fingerprint_unchanged": before_fp == after_fp,
            "receipt_count": [len(before_receipts), len(after_receipts)],
            "ok": ((applied is not None and applied.exit_code != 0)
                   and before_fp == after_fp
                   and len(before_receipts) == len(after_receipts)),
        }

    add("a3-same-key-different-intent",
        "The same key with different content must be refused as a conflict.",
        a3, ["adversarial", "idempotency"])

    def a4() -> dict:
        """--replay-only must verify without running the handler again."""
        world = C.build_world(WORLDS, "t03-a4")
        world.write("capture.create", {"text": "Replay-only probe."}, "a4-key")
        envelope = world.scratch("envelope-a4-key.json")
        before_fp = fingerprint(world)
        run = world.apply("capture.create", envelope, replay_only=True)
        body = run.json
        return {
            "exit_code": run.exit_code,
            "body": body if isinstance(body, dict) else None,
            "fingerprint_unchanged": before_fp == fingerprint(world),
            "ok": run.exit_code == 0 and before_fp == fingerprint(world),
        }

    add("a4-replay-only",
        "Verifying a committed receipt must not re-run the handler.",
        a4, ["adversarial", "idempotency"])

    # =================================================================
    # B. optimistic concurrency
    # =================================================================
    def b1() -> dict:
        """A write sealed against an old snapshot must be refused."""
        world = C.build_world(WORLDS, "t03-b1")
        envelope = world.scratch("envelope-b1-key.json")
        seal = world.seal("capture.create", {"text": "Stale snapshot probe."},
                          "b1-key")
        seal_body = seal.json
        # A canonical change after sealing: an unrelated, valid write.
        world.write("garden.seed.create",
                    {"text": "Synthetic unrelated change."}, "b1-other")
        before_fp = fingerprint(world)
        apply = world.apply("capture.create", envelope)
        after_fp = fingerprint(world)
        body = apply.json
        detail = {
            "seal_exit": seal.exit_code,
            "apply_exit": apply.exit_code,
            "apply_error": (body or {}).get("error") if isinstance(body, dict) else apply.stderr[:300],
            "fingerprint_unchanged_by_refused_write": before_fp == after_fp,
            "ok": False,
        }
        # The refusal is the success condition here.
        detail["ok"] = apply.exit_code == 3 and before_fp == after_fp
        return detail

    add("b1-stale-snapshot",
        "A write sealed against a stale snapshot must be refused (exit 3).",
        b1, ["adversarial", "concurrency"])

    def b2() -> dict:
        """Two writers, one snapshot: exactly one may win."""
        world = C.build_world(WORLDS, "t03-b2")
        env_a = world.scratch("envelope-b2-a.json")
        env_b = world.scratch("envelope-b2-b.json")
        world.seal("capture.create", {"text": "Racer A."}, "b2-a", out=env_a)
        world.seal("capture.create", {"text": "Racer B."}, "b2-b", out=env_b)
        run_a = world.apply("capture.create", env_a)
        run_b = world.apply("capture.create", env_b)
        codes = [run_a.exit_code, run_b.exit_code]
        detail = {
            "exit_codes": codes,
            "a_error": (run_a.json or {}).get("error") if isinstance(run_a.json, dict) else None,
            "b_error": (run_b.json or {}).get("error") if isinstance(run_b.json, dict) else None,
        }
        detail["ok"] = sorted(codes) == [0, 3]
        return detail

    add("b2-two-writers-one-snapshot",
        "Two concurrent writers against one snapshot: one wins, one conflicts.",
        b2, ["adversarial", "concurrency"])

    # =================================================================
    # C. authority
    # =================================================================
    def c1() -> dict:
        """A bare write command must refuse rather than write."""
        world = C.build_world(WORLDS, "t03-c1")
        before = fingerprint(world)
        run = world.los("garden-seed-create", "--text", "Bare command probe.")
        after = fingerprint(world)
        return {
            "exit_code": run.exit_code,
            "stderr": run.stderr.strip()[:400],
            "fingerprint_unchanged": before == after,
            "ok": run.exit_code != 0 and before == after,
        }

    add("c1-bare-write-command-refuses",
        "A named write command run without an envelope must refuse.",
        c1, ["adversarial", "authority"])

    def c2() -> dict:
        """A write outside the capability's scope must refuse."""
        world = C.build_world(WORLDS, "t03-c2")
        before = fingerprint(world)
        seal = world.seal("stage.note.write", {
            "unit_id": UNIT,
            "stage_id": "stage-does-not-exist",
            "text": "Out of scope probe.",
        }, "c2-key")
        after = fingerprint(world)
        return {
            "seal_exit": seal.exit_code,
            "stderr": seal.stderr.strip()[:400],
            "fingerprint_unchanged": before == after,
            "ok": seal.exit_code != 0 and before == after,
        }

    add("c2-out-of-scope-write",
        "A write naming a stage that does not exist must refuse.",
        c2, ["adversarial", "authority"])

    def c3() -> dict:
        """Shelving must apply only explicitly selected proposal items."""
        world = C.build_world(WORLDS, "t03-c3")
        _, prepare = world.write("review.prepare", {"unit_id": UNIT}, "c3-prep")
        check = world.los("review.prepare", "--unit-id", UNIT, "--check", "--json")
        body = check.json
        items = body.get("items") if isinstance(body, dict) else None
        ids = [i.get("id") for i in items] if isinstance(items, list) else []
        before = fingerprint(world)
        seal = world.seal("review.apply", {"unit_id": UNIT, "selected": []},
                          "c3-empty")
        seal2 = world.seal("review.apply",
                           {"unit_id": UNIT, "selected": ["no-such-item"]},
                           "c3-bogus")
        after = fingerprint(world)
        detail = {
            "prepare_ok": (prepare.json or {}).get("ok"),
            "proposal_ids": ids,
            "empty_selection_exit": seal.exit_code,
            "empty_selection_stderr": seal.stderr.strip()[:300],
            "bogus_selection_exit": seal2.exit_code,
            "bogus_selection_stderr": seal2.stderr.strip()[:300],
            "fingerprint_unchanged": before == after,
        }
        detail["ok"] = (seal.exit_code != 0 and seal2.exit_code != 0
                        and before == after)
        return detail

    add("c3-shelving-needs-explicit-selection",
        "Shelving must not apply anything that was not explicitly selected.",
        c3, ["adversarial", "authority", "review-queue"])

    def c4() -> dict:
        """note.revise without --approve must be refused."""
        world = C.build_world(WORLDS, "t03-c4")
        body = world.scratch("revised.md")
        body.write_text("# revised\n", encoding="utf-8")
        before = fingerprint(world)
        run = world.los("note-revise", "note-demo", "--file", str(body))
        after = fingerprint(world)
        return {
            "exit_code": run.exit_code,
            "stderr": run.stderr.strip()[:400],
            "stdout": run.stdout.strip()[:300],
            "fingerprint_unchanged": before == after,
            "ok": run.exit_code != 0 and before == after,
        }

    add("c4-note-revise-needs-approval",
        "A durable-note revision without approval must refuse.",
        c4, ["adversarial", "authority"])

    # =================================================================
    # D. fail-closed
    # =================================================================
    def d1() -> dict:
        """One validation error must block every canonical write."""
        world = C.build_world(WORLDS, "t03-d1")
        # Author a broken canonical file directly (the adversarial act).
        write_text(world, "curriculum/modules/module-demo/units/"
                          "unit-demo-l01/unit.yaml",
                   "id: unit-demo-l01\ntype: unit\nthis is not: valid\n")
        validate = world.los("validate")
        before = fingerprint(world)
        seal = world.seal("garden.seed.create",
                          {"text": "Should be blocked."}, "d1-key")
        after = fingerprint(world)
        detail = {
            "validate_exit": validate.exit_code,
            "validate_tail": validate.stdout.strip()[-400:],
            "write_seal_exit": seal.exit_code,
            "write_seal_stderr": seal.stderr.strip()[:400],
            "fingerprint_unchanged": before == after,
        }
        detail["ok"] = (validate.exit_code == 1 and seal.exit_code != 0
                        and before == after)
        return detail

    add("d1-fail-closed-blocks-writes",
        "One validation error anywhere must block every canonical write.",
        d1, ["adversarial", "fail-closed"])

    def d2() -> dict:
        """A read must refuse rather than silently omit what it cannot verify."""
        world = C.build_world(WORLDS, "t03-d2")
        write_text(world, "curriculum/modules/module-demo/units/"
                          "unit-demo-l01/unit.yaml",
                   "id: unit-demo-l01\ntype: unit\nthis is not: valid\n")
        before = fingerprint(world)
        read = world.los("unit-list")
        inspect = world.los("inspect", UNIT)
        after = fingerprint(world)
        detail = {
            "unit-list_exit": read.exit_code,
            "unit-list_stderr": read.stderr.strip()[:300],
            "unit-list_bytes": len(read.stdout),
            "inspect_exit": inspect.exit_code,
            "inspect_stderr": inspect.stderr.strip()[:300],
            "fingerprint_unchanged": before == after,
        }
        detail["ok"] = (read.exit_code != 0 and inspect.exit_code != 0
                        and before == after)
        return detail

    add("d2-reads-refuse-rather-than-omit",
        "With a broken record, a read must refuse instead of quietly omitting it.",
        d2, ["adversarial", "fail-closed"])

    # =================================================================
    # E. agent improvisation on the untranscribable workflows
    # =================================================================
    def e1() -> dict:
        """Can an agent improvise the scope authority of workflow 23?

        Workflow 23 (process a lecture) is declared untranscribable: it
        needs the real as-taught deck as scope authority. This probes
        whether an agent can reach the same end state unattended by
        drafting the plan file itself.
        """
        world = C.build_world(WORLDS, "t03-e1")
        # The agent writes its own study map and imports it.
        study_map = world.scratch("agent-study-map.yaml")
        study_map.write_text(
            "schema_version: 1\n"
            "id: study-map-demo-l01\n"
            "type: study-map\n"
            "unit_id: unit-demo-l01\n"
            "module_id: module-demo\n"
            "title: Agent-improvised map\n"
            "stages:\n"
            "  - id: stage-agent-improvised\n"
            "    title: Improvised stage\n"
            "    status: pending\n"
            "    objective: Synthesised by the agent, not by a human.\n"
            "    done_when:\n"
            "      - Nothing was taught.\n",
            encoding="utf-8")
        digest = "sha256:" + hashlib.sha256(study_map.read_bytes()).hexdigest()
        seal = world.seal("unit.map.import", {
            "unit_id": UNIT,
            "file": str(study_map),
            "file_sha256": digest,
            "replace": True,
            "retire_reason": "agent improvisation probe",
            "retire_stage": [STAGE],
        }, "e1-key")
        applied = None
        if seal.exit_code == 0:
            applied = world.apply("unit.map.import",
                                  world.scratch("envelope-e1-key.json"))
        map_path = (world.root / "curriculum/modules/module-demo/units/"
                             "unit-demo-l01/study-map.yaml")
        staged = (STAGE in map_path.read_text(encoding="utf-8")
                  if map_path.exists() else False)
        detail = {
            "seal_exit": seal.exit_code,
            "seal_stderr": seal.stderr.strip()[:400],
            "apply_exit": applied.exit_code if applied else None,
            "apply_stderr": (applied.stderr.strip()[:400] if applied else None),
            "original_stage_still_present": staged,
            "note": ("the plan file is the scope authority; nothing in the "
                     "gateway can tell a human-reviewed file from an "
                     "agent-drafted one"),
        }
        detail["ok"] = True       # measured, not asserted
        return detail

    add("e1-agent-improvised-study-map",
        "Workflow 23 needs a human scope authority; can an agent supply one?",
        e1, ["adversarial", "improvisation", "workflow-23"])

    def e1b() -> dict:
        """The ladder from "no plan" to "an agent's own scope, installed".

        Every rung runs in its own fresh world so the rungs cannot
        interfere, and each one records the refusal the system produced.
        """
        ladder = []

        def fresh(label: str) -> C.World:
            return C.build_world(WORLDS, f"t03-e1b-{label}")

        def agent_stage_text() -> str:
            return (
                "- id: stage-agent-third\n  number: 3\n"
                "  title: Scope the agent decided on its own\n"
                "  status: pending\n"
                "  objective: Process a lecture the agent scoped by itself.\n"
                "  done_when:\n  - A human never approved this scope.\n"
                "  exam_critical: false\n  concepts: []\n"
                "  scope_triage: required-now\n  resources:\n"
                "  - kind: read\n    label: Demo Book §9\n"
                "    source_id: source-demo-book\n    locator: §9\n"
                "  working_note: curriculum/modules/module-demo/units/"
                "unit-demo-l01/stages/stage-agent-third/notes.md\n"
                "  attachments: []\n  source_feedback: []\n")

        def sha(path: Path) -> str:
            return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

        def record(label: str, world: C.World, payload: dict, key: str,
                   file_field: Path) -> None:
            seal, apply = world.write("unit.map.import", payload, key)
            src = (world.root / "curriculum/modules/module-demo/units/"
                             "unit-demo-l01/study-map.yaml")
            ladder.append({
                "rung": label,
                "seal_exit": seal.exit_code,
                "apply_exit": apply.exit_code,
                "refusal": (seal.stderr.strip()[:300]
                            or apply.stderr.strip()[:300]),
                "agent_stage_installed": (
                    "stage-agent-third" in src.read_text(encoding="utf-8")
                    if src.exists() else False),
            })

        # Rung A — a hand-written map with no template version.
        world = fresh("a")
        naive = world.scratch("naive.yaml")
        naive.write_text(
            "id: study-map-demo-l01\ntype: study-map\nunit_id: unit-demo-l01\n"
            "stages:\n- id: stage-naive\n  title: Naive\n",
            encoding="utf-8")
        record("A. hand-written map, no plan_template_version", world,
               {"unit_id": UNIT, "file": str(naive),
                "file_sha256": sha(naive), "replace": True}, "e1b-a", naive)

        # Rung B — the canonical template, placeholder left in place.
        world = fresh("b")
        tpl = world.los("plan-template", "curriculum", "--title",
                        "Synthetic agent scope", "--unit-id", UNIT,
                        "--module-id", "module-demo")
        placeholder = world.scratch("placeholder.yaml")
        placeholder.write_text(tpl.stdout, encoding="utf-8")
        record("B. canonical template, source_plan placeholder intact", world,
               {"unit_id": UNIT, "file": str(placeholder),
                "file_sha256": sha(placeholder), "replace": True},
               "e1b-b", placeholder)

        # Rung C — v1-conforming template that REPLACES the existing map.
        world = fresh("c")
        tpl = world.los("plan-template", "curriculum", "--title",
                        "Synthetic agent scope", "--unit-id", UNIT,
                        "--module-id", "module-demo")
        replacing = tpl.stdout.replace(
            "path: replace-with-reviewed-plan.yaml",
            "path: work/active/workspace-demo/CONTEXT.md")
        repl = world.scratch("replacing.yaml")
        repl.write_text(replacing, encoding="utf-8")
        record("C. replacement map, retired stages undeclared", world,
               {"unit_id": UNIT, "file": str(repl), "file_sha256": sha(repl),
                "replace": True}, "e1b-c", repl)

        # Rung D — same, but every retired stage is declared with a reason.
        world = fresh("d")
        tpl = world.los("plan-template", "curriculum", "--title",
                        "Synthetic agent scope", "--unit-id", UNIT,
                        "--module-id", "module-demo")
        replacing = tpl.stdout.replace(
            "path: replace-with-reviewed-plan.yaml",
            "path: work/active/workspace-demo/CONTEXT.md")
        repl = world.scratch("replacing.yaml")
        repl.write_text(replacing, encoding="utf-8")
        record("D. replacement map, retirement declared with an agent-written "
               "reason", world,
               {"unit_id": UNIT, "file": str(repl), "file_sha256": sha(repl),
                "replace": True,
                "retire_stage": ["stage-demo", "stage-demo-pending"],
                "retire_reason": "Agent decided to reprocess this lecture "
                                 "unattended.",
                "intentional_state_reset": "Agent decided to discard "
                                           "learner state."},
               "e1b-d", repl)

        # Rung E — the minimal move: keep the map, add one stage of the
        # agent's own devising. No retirement, no reason string.
        world = fresh("e")
        src = (world.root / "curriculum/modules/module-demo/units/"
                         "unit-demo-l01/study-map.yaml")
        text = src.read_text(encoding="utf-8")
        text = text.replace(
            "id: study-map-demo-l01\ntype: study-map\n",
            "id: study-map-demo-l01\ntype: study-map\nplan_template_version: 1\n")
        text = text.replace(
            "- id: stage-demo\n",
            "- id: stage-demo\n  number: 1\n  exam_critical: false\n"
            "  concepts: []\n")
        text = text.replace(
            "- id: stage-demo-pending\n",
            "- id: stage-demo-pending\n  number: 2\n  exam_critical: false\n"
            "  concepts: []\n")
        text = text.rstrip("\n") + "\n" + agent_stage_text()
        extended = world.scratch("extended.yaml")
        extended.write_text(text, encoding="utf-8")
        record("E. extend the map by one agent-authored stage", world,
               {"unit_id": UNIT, "file": str(extended),
                "file_sha256": sha(extended), "replace": True},
               "e1b-e", extended)
        validate = world.los("validate")
        receipt_dir = world.root / "operations/transactions"
        receipts = sorted(receipt_dir.glob("transaction-*.yaml"))

        detail = {
            "ladder": ladder,
            "validate_after_landing": validate.exit_code,
            "receipts_written": len(receipts),
            "note": ("the guards are structural: a template version, a named "
                     "plan, a declared retirement, one active stage, a live "
                     "resume pointer. None of them is a provenance gate, and "
                     "rung E needs no reason string at all."),
        }
        detail["ok"] = True       # measured, not asserted
        return detail

    add("e1b-agent-authored-scope-lands",
        "The ladder from 'no plan' to 'an agent's own scope, installed'.",
        e1b, ["adversarial", "improvisation", "workflow-23", "headline"])

    def e2() -> dict:
        """Workflow 27: the Master's promotion path, probed from the CLI."""
        world = C.build_world(WORLDS, "t03-e2")
        catalog = world.los("masters-planning-dashboard")
        listing = world.los("masters-planning-catalog-update", "--help")
        detail = {
            "dashboard_exit": catalog.exit_code,
            "dashboard_bytes": len(catalog.stdout),
            "dashboard_head": catalog.stdout[:400],
            "catalog_update_help": listing.stdout[:600],
        }
        detail["ok"] = True       # measured, not asserted
        return detail

    add("e2-masters-promotion-surface",
        "Workflow 27 (promote a Master's module): what does the CLI expose?",
        e2, ["adversarial", "improvisation", "workflow-27"])

    def e3() -> dict:
        """Workflow 24: turn the semester."""
        world = C.build_world(WORLDS, "t03-e3")
        run = world.los("session-end", "--help")
        detail = {
            "session_end_help": run.stdout[:900],
        }
        detail["ok"] = True
        return detail

    add("e3-turn-the-semester-surface",
        "Workflow 24 (turn the semester): what does the CLI expose?",
        e3, ["adversarial", "improvisation", "workflow-24"])

    # =================================================================
    # F. malformed input reaching canonical state
    # =================================================================
    def f1() -> dict:
        """A note body that carries its own frontmatter."""
        world = C.build_world(WORLDS, "t03-f1")
        body = world.scratch("body-with-frontmatter.md")
        body.write_text(
            "---\n"
            "id: note-f1-duplicate\n"
            "type: note\n"
            'title: "Body with its own frontmatter"\n'
            "---\n\n"
            "# Body with its own frontmatter\n\n"
            "The body carried a second frontmatter block.\n",
            encoding="utf-8")
        seal, apply = world.write("note.create", {
            "body_file": str(body),
            "body_file_sha256":
                "sha256:" + hashlib.sha256(body.read_bytes()).hexdigest(),
            "note": {
                "id": "note-f1-duplicate",
                "path": "knowledge/notes/mathematics/note-f1-duplicate.md",
                "title": "Body with its own frontmatter",
            },
        }, "f1-key")
        note_path = (world.root / "knowledge/notes/mathematics/"
                                 "note-f1-duplicate.md")
        content = note_path.read_text(encoding="utf-8") if note_path.exists() else ""
        frontmatter_blocks = content.count("\n---\n")
        validate = world.los("validate")
        detail = {
            "write_exit": apply.exit_code,
            "frontmatter_blocks_in_file": frontmatter_blocks,
            "validate_exit": validate.exit_code,
            "validate_errors": [l for l in validate.stdout.splitlines()
                                 if l.startswith("E ")][:3],
            "file_head": content[:260],
            "note": ("the writer prepends its own frontmatter; a body that "
                     "carries one produces a file with two blocks"),
        }
        detail["ok"] = True       # measured, not asserted
        return detail

    add("f1-note-body-with-frontmatter",
        "A body file that carries its own frontmatter: is it caught?",
        f1, ["adversarial", "malformed-input"])

    def f2() -> dict:
        """A URI with a fragment: two resolvers, two answers."""
        world = C.build_world(WORLDS, "t03-f2")
        seal, apply = world.write("note.evidence.add", {
            "note_id": "note-demo",
            "evidence_type": "external",
            "ref": "material://source-demo-book/lecture-01.pdf#page=2",
        }, "f2-key")
        validate = world.los("validate")
        baseline = world.los_tool("warning_baseline.py", "--check")
        detail = {
            "write_exit": apply.exit_code,
            "write_stderr": apply.stderr.strip()[:300],
            "validate_exit": validate.exit_code,
            "uri_warnings": [l for l in validate.stdout.splitlines()
                             if "URI-MATERIAL" in l][:2],
            "baseline_exit": baseline.exit_code,
            "baseline_stdout": baseline.stdout.strip()[:300],
            "note": ("the seal-time materials check strips the fragment; the "
                     "general validator does not, so a write the system "
                     "accepts can break the warning-baseline gate"),
        }
        detail["ok"] = True       # measured, not asserted
        return detail

    add("f2-fragment-uri-two-resolvers",
        "A material ref with a fragment: accepted on write, flagged on validate.",
        f2, ["adversarial", "malformed-input", "write-validate-agreement"])

    def f3() -> dict:
        """An unknown capability and a tampered envelope."""
        world = C.build_world(WORLDS, "t03-f3")
        before = fingerprint(world)
        unknown = world.los("capability", "no.such.capability",
                            "--payload-file", str(world.scratch("x.json")))
        envelope = world.scratch("envelope-f3.json")
        envelope.write_text(json.dumps({
            "schema_version": 2,
            "request_id": "request-f3",
            "idempotency_key": "f3-key",
            "capability": "garden.seed.create",
            "ok": True,
        }), encoding="utf-8")
        tampered = world.los("capability", "garden.seed.create",
                             "--payload-file", str(envelope))
        after = fingerprint(world)
        detail = {
            "unknown_capability_exit": unknown.exit_code,
            "unknown_capability_stderr": unknown.stderr.strip()[:300],
            "tampered_exit": tampered.exit_code,
            "tampered_stderr": tampered.stderr.strip()[:300],
            "fingerprint_unchanged": before == after,
        }
        detail["ok"] = (unknown.exit_code != 0 and tampered.exit_code != 0
                        and before == after)
        return detail

    add("f3-unknown-and-tampered-envelope",
        "An unknown capability and a hand-written envelope must refuse.",
        f3, ["adversarial", "malformed-input"])

    def f4() -> dict:
        """A read that tries to pull an unbounded amount."""
        world = C.build_world(WORLDS, "t03-f4")
        big = world.los("note-read", "note-demo", "--limit", "100000")
        body = big.json
        detail = {
            "exit_code": big.exit_code,
            "content_len": len(body.get("content", "")) if isinstance(body, dict) else None,
            "limit_declared": body.get("limit") if isinstance(body, dict) else None,
            "total_characters": body.get("total_characters") if isinstance(body, dict) else None,
            "stderr": big.stderr.strip()[:200],
        }
        default_read = world.los("note-read", "note-demo")
        default_body = default_read.json
        detail["default_read_bytes"] = len(default_read.stdout)
        detail["default_content_len"] = (len(default_body.get("content", ""))
                                         if isinstance(default_body, dict) else None)
        detail["default_total_characters"] = (default_body.get("total_characters")
                                              if isinstance(default_body, dict) else None)
        detail["ok"] = (big.exit_code == 2
                        and default_read.exit_code == 0
                        and isinstance(default_body, dict)
                        and len(default_body.get("content", "")) <= 16000)
        return detail

    add("f4-unbounded-read-is-clamped",
        "A read that asks for everything must stay bounded.",
        f4, ["adversarial", "bounded"])

    def g1() -> dict:
        """Which approval paths admit a plan revision?

        The system has a reviewed-UI gate: a study-map import wants
        ``direct-user-gesture`` from the ``ui`` channel. This measures
        whether that gate holds, and what the other door does.
        """
        rows = []

        def attempt(channel: str, approval: str) -> dict:
            world = C.build_world(WORLDS, f"t03-g1-{channel}-{approval[:6]}")
            src = (world.root / "curriculum/modules/module-demo/units/"
                             "unit-demo-l01/study-map.yaml")
            text = src.read_text(encoding="utf-8")
            text = text.replace(
                "id: study-map-demo-l01\ntype: study-map\n",
                "id: study-map-demo-l01\ntype: study-map\n"
                "plan_template_version: 1\n")
            text = text.replace(
                "- id: stage-demo\n",
                "- id: stage-demo\n  number: 1\n  exam_critical: false\n"
                "  concepts: []\n")
            text = text.replace(
                "- id: stage-demo-pending\n",
                "- id: stage-demo-pending\n  number: 2\n"
                "  exam_critical: false\n  concepts: []\n")
            text = text.rstrip("\n") + "\n" + (
                "- id: stage-agent-third\n  number: 3\n"
                "  title: Scope the agent decided on its own\n"
                "  status: pending\n"
                "  objective: Process a lecture the agent scoped by itself.\n"
                "  done_when:\n  - A human never approved this scope.\n"
                "  exam_critical: false\n  concepts: []\n"
                "  scope_triage: required-now\n  resources:\n"
                "  - kind: read\n    label: Demo Book §9\n"
                "    source_id: source-demo-book\n    locator: §9\n"
                "  working_note: curriculum/modules/module-demo/units/"
                "unit-demo-l01/stages/stage-agent-third/notes.md\n"
                "  attachments: []\n  source_feedback: []\n")
            body = world.scratch("agent-study-map.yaml")
            body.write_text(text, encoding="utf-8")
            digest = ("sha256:"
                      + hashlib.sha256(body.read_bytes()).hexdigest())
            seal, apply = world.write("unit.map.import", {
                "unit_id": UNIT, "file": str(body),
                "file_sha256": digest, "replace": True},
                f"g1-{channel}-{approval[:6]}", channel=channel,
                approval_kind=approval)
            landed = ("stage-agent-third"
                      in src.read_text(encoding="utf-8"))
            body_out = apply.json
            error = (body_out or {}).get("error") if isinstance(body_out, dict) else None
            return {
                "channel": channel,
                "approval_kind": approval,
                "apply_exit": apply.exit_code,
                "agent_stage_installed": landed,
                "error_code": (error or {}).get("code") if isinstance(error, dict) else None,
                "error_message": ((error or {}).get("message")
                                  if isinstance(error, dict) else None),
            }

        rows.append(attempt("codex", "direct-user-gesture"))
        rows.append(attempt("ui", "direct-user-gesture"))
        rows.append(attempt("operator", "operator-approval"))
        detail = {
            "matrix": rows,
            "note": ("the reviewed-UI gate refuses a codex-channel gesture, "
                     "exactly as designed; but the CLI can declare any "
                     "channel it likes, and the operator path admits the "
                     "same write without a gesture at all"),
        }
        detail["ok"] = True       # measured, not asserted
        return detail

    add("g1-which-approval-paths-admit-a-plan-revision",
        "Which approval paths admit a study-map import?",
        g1, ["adversarial", "improvisation", "workflow-23", "trust-model"])

    outcomes = run_cases(cases, REPORTS / "t03", "T03 — Adversarial probes")
    print()
    print(f"T03: {sum(1 for o in outcomes if o.ok)}/{len(outcomes)} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

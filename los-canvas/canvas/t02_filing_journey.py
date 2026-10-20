"""T02 — The operator's filing journey.

This is the agent-librarian's ordinary day, exercised end to end on
synthetic content and through the *only* sanctioned write path: seal a
GatewayEnvelopeV2, apply it, read the receipt, read the change back.

Every step records:
  * the capability,
  * whether the write committed (`ok` + a receipt on disk),
  * what it cost to make the write and to read it back.

The point of the file is the *cost* column. The previous review said the
governance cost of this system is "paid in tokens and steps, not minutes".
This measures that claim on a real path instead of asserting it.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import canvaslib as C          # noqa: E402
from runner import Case, approx_tokens, run_cases   # noqa: E402

WORLDS = C.CANVAS_ROOT / "worlds"
REPORTS = C.CANVAS_ROOT / "reports"

UNIT = "unit-demo-l01"
STAGE = "stage-demo"
WORKSPACE = "workspace-demo"
#: The requirement's own id, from generated/learning-requirements.json.
#: NOTE: `los resume` (text form) prints the requirement's *concept* here
#: instead — see Finding F-01 in the report.
REQUIREMENT = "req-demo-l01-demo"


class Journey:
    """Counts what the operator spends."""

    def __init__(self, world: C.World) -> None:
        self.world = world
        self.steps: list[dict] = []
        self.read_tokens = 0
        self.write_tokens = 0

    def step(self, name: str, capability: str, payload: dict, key: str,
             **kw) -> dict:
        seal, apply = self.world.write(capability, payload, key, **kw)
        record = {
            "step": name,
            "capability": capability,
            "seal_exit": seal.exit_code,
            "apply_exit": apply.exit_code,
            "seal_stderr": seal.stderr.strip()[:400],
            "apply_stderr": apply.stderr.strip()[:600],
            "seal_tokens": approx_tokens(seal.stdout),
            "apply_tokens": approx_tokens(apply.stdout),
        }
        body = apply.json
        if isinstance(body, dict):
            record["ok"] = body.get("ok")
            record["replayed"] = body.get("replayed")
            record["transaction_id"] = body.get("transaction_id")
            record["receipt_path"] = body.get("receipt_path")
            record["error"] = body.get("error")
        else:
            record["ok"] = False
        if record.get("receipt_path"):
            receipt = self.world.root / record["receipt_path"]
            record["receipt_on_disk"] = receipt.exists()
        self.write_tokens += record["seal_tokens"] + record["apply_tokens"]
        self.steps.append(record)
        return record

    def read(self, name: str, *args: str) -> dict:
        run = self.world.los(*args)
        record = {
            "step": name,
            "argv": list(args),
            "exit_code": run.exit_code,
            "tokens": approx_tokens(run.stdout),
            "bytes": len(run.stdout),
        }
        body = run.json
        if isinstance(body, dict):
            record["keys"] = sorted(body.keys())[:25]
        self.read_tokens += record["tokens"]
        self.steps.append(record)
        return record


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    world = C.build_world(WORLDS, "t02")
    j = Journey(world)
    cases: list[Case] = []

    def add(name: str, intent: str, fn, tags=()) -> None:
        cases.append(Case(name, intent, fn, list(tags)))

    # -- 1. capture a fragment --------------------------------------------
    def step_capture() -> dict:
        payload = {
            "text": ("Synthetic capture: the variance identity needs the "
                     "independence assumption spelled out, otherwise the "
                     "worked example reads as a coincidence."),
            "title": "Synthetic fragment",
        }
        record = j.step("capture", "capture.create", payload, "t02-capture")
        record["inbox_after"] = _inbox_names(world)
        record["ok"] = bool(record.get("ok")) and record["inbox_after"]
        return record

    add("j1-capture-inbox",
        "A learner (or the agent) drops an unsorted fragment.",
        step_capture, ["write"])

    # -- 2. read it back --------------------------------------------------
    def step_read_inbox() -> dict:
        listing = j.read("inbox-list", "inbox-list")
        names = _inbox_names(world)
        captured = next((n for n in names if "synthetic-fragment" in n), None)
        read = (j.read("inbox-read", "inbox-read", captured)
                if captured else None)
        body = world.los("inbox-read", captured).json if captured else None
        digest = body.get("content_sha256") if isinstance(body, dict) else None
        return {
            "listing": listing,
            "captured_name": captured,
            "read": read,
            "content_sha256": digest,
            "ok": listing["exit_code"] == 0 and bool(digest),
        }

    add("j2-read-inbox",
        "The operator lists the inbox and reads one drop, bounded.",
        step_read_inbox, ["read"])

    # -- 3. file it as a durable note -------------------------------------
    def step_note() -> dict:
        body = world.scratch("note-canvas-body.md")
        body.write_text(
            "---\n"
            "id: note-canvas-variance\n"
            "type: note\n"
            'title: "Synthetic — Variance needs independence"\n'
            'created: "2026-10-20"\n'
            "role: synthesis\n"
            "state: rough\n"
            "authorship: operator-drafted\n"
            "concepts: [concept-variance]\n"
            "sources: [source-demo-book]\n"
            "contexts: [workspace-demo]\n"
            "---\n\n"
            "# Synthetic — Variance needs independence\n\n"
            "The variance identity E[XY] = E[X]E[Y] holds only under "
            "independence. The worked example in the synthetic deck "
            "silently assumes it.\n",
            encoding="utf-8")
        payload = {
            "body_file": str(body),
            "body_file_sha256": sha256_file(body),
            "note": {
                "id": "note-canvas-variance",
                "path": "knowledge/notes/mathematics/note-canvas-variance.md",
                "title": "Synthetic — Variance needs independence",
                "role": "synthesis",
                "concepts": ["concept-variance"],
                "sources": ["source-demo-book"],
                "contexts": [WORKSPACE],
            },
        }
        record = j.step("note.create", "note.create", payload, "t02-note")
        record["ok"] = bool(record.get("ok"))
        return record

    add("j3-create-durable-note",
        "The operator files the fragment as a durable, source-bound note.",
        step_note, ["write"])

    def step_read_note() -> dict:
        read = j.read("note-read", "note-read", "note-canvas-variance")
        body = world.los("note-read", "note-canvas-variance").json
        return {
            "read": read,
            "path": body.get("path") if isinstance(body, dict) else None,
            "has_content": bool((body or {}).get("content")),
            "ok": read["exit_code"] == 0 and bool((body or {}).get("content")),
        }

    add("j4-read-back-the-note",
        "The operator reads the note back — the filing is observable.",
        step_read_note, ["read"])

    # -- 4. bind evidence -------------------------------------------------
    def step_evidence() -> dict:
        payload = {
            "note_id": "note-canvas-variance",
            "evidence_type": "derivation",
            "ref": "material://source-demo-book/lecture-01.pdf",
        }
        record = j.step("note.evidence.add", "note.evidence.add", payload,
                        "t02-evidence")
        record["ok"] = bool(record.get("ok"))
        return record

    add("j5-bind-evidence",
        "The operator binds one piece of evidence to the note.",
        step_evidence, ["write"])

    # -- 5. relate a concept ---------------------------------------------
    def step_relation() -> dict:
        payload = {"change": {"operations": [{
            "action": "add",
            "new": {"from": "concept-variance", "type": "requires",
                    "to": "concept-expected-value"},
        }]}}
        record = j.step("concept.relations.change",
                        "concept.relations.change", payload, "t02-relation")
        record["ok"] = bool(record.get("ok"))
        return record

    add("j6-relation",
        "The operator records one explicit concept relation.",
        step_relation, ["write"])

    # -- 6. plant a garden seed ------------------------------------------
    def step_garden() -> dict:
        payload = {"text": ("Synthetic half-formed idea: maybe the variance "
                            "identity is a special case of the covariance "
                            "identity, and the deck should say so.")}
        record = j.step("garden.seed.create", "garden.seed.create", payload,
                        "t02-garden")
        record["ok"] = bool(record.get("ok"))
        return record

    add("j7-garden-seed",
        "A deliberately half-formed idea is planted, not filed.",
        step_garden, ["write"])

    # -- 7. save a question ----------------------------------------------
    def step_question() -> dict:
        payload = {"question": {
            "id": "note-canvas-question-variance",
            "title": "Synthetic — Is the independence assumption stated?",
            "text": ("The synthetic deck's variance example never says the "
                     "variables are independent. Where should that be "
                     "stated?"),
            "target": {"concepts": ["concept-variance"]},
        }}
        record = j.step("atlas.question.save", "atlas.question.save", payload,
                        "t02-question")
        record["ok"] = bool(record.get("ok"))
        return record

    add("j8-save-question",
        "The operator saves a question as a first-class record.",
        step_question, ["write"])

    # -- 8. register a synthetic source -----------------------------------
    def step_source() -> dict:
        payload = {"record": {"records": [{
            "action": "create",
            "id": "source-canvas-synthetic",
            "partition": "sources.yaml",
            "title": "Synthetic Variance Deck",
            "type": "lecture",
            "authors": ["Canvas Author"],
            "year": 2026,
            "discovery": {
                "observed": "2026-10-20",
                "basis": [{"kind": "catalogue-entry",
                           "ref": "https://example.invalid/synthetic-catalogue"}],
                "possible_use": "Reference for the variance identity.",
            },
        }]}}
        # Source intake is a documented two-pass: a check run returns the
        # diff hash, and the apply refuses anything else.
        check = world.los("source-intake", "--record", json.dumps(payload["record"]),
                          "--check", "--json")
        check_body = check.json if isinstance(check.json, dict) else {}
        diff_hash = check_body.get("diff_sha256")
        payload["expected_diff_sha256"] = diff_hash
        record = j.step("source.intake.record", "source.intake.record",
                        payload, "t02-source")
        record["check_exit"] = check.exit_code
        record["diff_sha256"] = diff_hash
        record["ok"] = bool(record.get("ok")) and check.exit_code == 0
        return record

    add("j9-register-source",
        "The operator registers one global source identity.",
        step_source, ["write"])

    # -- 9. record feedback on a stage ------------------------------------
    def step_feedback() -> dict:
        payload = {
            "unit_id": UNIT,
            "stage_id": STAGE,
            "source_id": "source-demo-book",
            "feedback": "helpful",
            "note": "Synthetic: the worked example is clear, the caveat is not.",
        }
        record = j.step("source.feedback.record", "source.feedback.record",
                        payload, "t02-feedback")
        record["ok"] = bool(record.get("ok"))
        return record

    add("j10-source-feedback",
        "The operator records lightweight personal evidence.",
        step_feedback, ["write"])

    # -- 10. record an observation ----------------------------------------
    def step_observation() -> dict:
        payload = {
            "workspace": WORKSPACE,
            "requirement": REQUIREMENT,
            "activity": "Synthetic: worked the expected-value example.",
            "result": "partial",
            "tags": "canvas,synthetic",
        }
        record = j.step("learner.observation.append",
                        "learner.observation.append", payload,
                        "t02-observation")
        record["ok"] = bool(record.get("ok"))
        return record

    add("j11-record-observation",
        "The operator records one attempt — evidence, never mastery.",
        step_observation, ["write"])

    # -- 11. write the stage working note ---------------------------------
    def step_stage_note() -> dict:
        payload = {
            "unit_id": UNIT,
            "stage_id": STAGE,
            "text": ("Synthetic session note: the independence caveat is the "
                     "one thing the deck never says."),
        }
        record = j.step("stage.note.write", "stage.note.write", payload,
                        "t02-stage-note")
        record["ok"] = bool(record.get("ok"))
        return record

    add("j12-stage-note",
        "Stage-specific learning belongs in the stage's working note.",
        step_stage_note, ["write"])

    # -- 12. shelving is approval-gated -----------------------------------
    def step_shelving() -> dict:
        prepare = j.step("review.prepare", "review.prepare",
                         {"unit_id": UNIT}, "t02-review-prepare")
        body = world.los("review.prepare", "--unit-id", UNIT, "--check",
                         "--json").json
        items = body.get("items") if isinstance(body, dict) else None
        detail = {
            "prepare": prepare,
            "proposal_items": items if isinstance(items, list) else None,
            "proposal_count": len(items) if isinstance(items, list) else None,
        }
        detail["ok"] = bool(prepare.get("ok"))
        return detail

    add("j13-shelving-prepare",
        "The operator prepares the review packet — nothing is applied yet.",
        step_shelving, ["write", "review-queue"])

    # -- 13. end the session ----------------------------------------------
    def step_session_end() -> dict:
        run = world.los("session-end", "--json")
        body = run.json or {}
        detail = {
            "exit_code": run.exit_code,
            "stderr": run.stderr.strip()[:600],
            "stdout_head": run.stdout[:600],
            "keys": sorted(body.keys())[:25] if isinstance(body, dict) else None,
        }
        detail["ok"] = run.exit_code == 0
        return detail

    add("j14-session-end",
        "The session ends deliberately; the ledger names its own rows.",
        step_session_end, ["write", "session"])

    # -- 14. read-back: what did the world look like afterwards? ----------
    def step_readback() -> dict:
        validate = world.los("validate")
        warnings = world.los_tool("warning_baseline.py", "--check")
        status = world.los("status")
        detail = {
            "validate_exit": validate.exit_code,
            "validate_stdout": validate.stdout.strip()[-300:],
            "warnings_exit": warnings.exit_code,
            "warnings_stdout": warnings.stdout.strip()[-300:],
            "status_stdout": status.stdout.strip()[:900],
        }
        detail["ok"] = validate.exit_code == 0 and warnings.exit_code == 0
        return detail

    add("j15-read-back-the-world",
        "After the journey: the world still validates and the baseline holds.",
        step_readback, ["read", "verification"])

    # -- the cost ledger ---------------------------------------------------
    def cost() -> dict:
        detail = {
            "steps": len(j.steps),
            "writes": sum(1 for s in j.steps if "capability" in s),
            "reads": sum(1 for s in j.steps if "argv" in s),
            "write_tokens": j.write_tokens,
            "read_tokens": j.read_tokens,
            "total_tokens": j.write_tokens + j.read_tokens,
            "per_step": [
                {k: v for k, v in s.items()
                 if k in ("step", "capability", "apply_exit", "seal_exit",
                          "tokens", "seal_tokens", "apply_tokens")}
                for s in j.steps
            ],
        }
        detail["ok"] = all(s.get("ok") for s in j.steps
                           if "capability" in s and "ok" in s)
        return detail

    add("j16-cost-ledger",
        "What did one filing session cost in steps and tokens?",
        cost, ["cost"])

    outcomes = run_cases(cases, REPORTS / "t02", "T02 — The operator's filing journey")
    print()
    print(f"T02: {sum(1 for o in outcomes if o.ok)}/{len(outcomes)} passed")
    return 0


def _inbox_names(world: C.World) -> list[str]:
    run = world.los("inbox-list")
    body = run.json
    if isinstance(body, list):
        return [row.get("id") for row in body if isinstance(row, dict)]
    return []


if __name__ == "__main__":
    raise SystemExit(main())

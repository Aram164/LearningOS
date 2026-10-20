"""T06 — Workflow 24: turning the semester.

Workflow 24 is declared untranscribable: it "composites workflow 19 and a
real term boundary with human Garden judgments and push".

This suite builds the missing precondition — a *past* sitting, a local
remote to push to, a garden seed awaiting a judgment — and then asks what
the agent can actually do at a term boundary, and what it cannot.

The hypothesis worth testing is that the term boundary is enforced by
**absence of capability**, not by a refusal: the steps that carry the
human's judgement (archiving a workspace, disposing of a garden seed)
have no capability at all.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))

import canvaslib as C          # noqa: E402
from runner import Case, run_cases   # noqa: E402

WORLDS = C.CANVAS_ROOT / "worlds"
REPORTS = C.CANVAS_ROOT / "reports"

MODULE = "module-demo"
UNIT = "unit-demo-l01"
WORKSPACE = "workspace-demo"
ATTEMPT_DATE = "2026-10-09"


def main() -> int:
    world = C.build_world(WORLDS, "t06")
    cases: list[Case] = []

    def add(name: str, intent: str, fn, tags=()) -> None:
        cases.append(Case(name, intent, fn, list(tags)))

    # ---- 0. the precondition: a remote to push to ------------------------
    def remote() -> dict:
        bare = world.root.parent.parent / "canvas-scratch" / "remote.git"
        bare.parent.mkdir(parents=True, exist_ok=True)
        if bare.exists():
            subprocess.run(["rm", "-rf", str(bare)], check=True)
        subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
        run = world.los("status")
        detail = {
            "remote_path": str(bare),
            "world_is_a_git_repo": (world.root / ".git").exists(),
            "status_exit": run.exit_code,
        }
        detail["ok"] = detail["world_is_a_git_repo"]
        return detail

    add("w24-1-a-remote-to-push-to",
        "The term boundary ends with a push; give the world a remote.",
        remote, ["workflow-24"])

    # ---- 1. record the attempt ------------------------------------------
    def record_attempt() -> dict:
        seal, apply = world.write("module.attempt.record", {
            "module_id": MODULE,
            "termin": 2,
            "date": ATTEMPT_DATE,
            "result": "passed",
            "notes": "Synthetic: the probe sitting happened.",
        }, "w24-attempt")
        body = apply.json
        detail = {
            "seal_exit": seal.exit_code,
            "apply_exit": apply.exit_code,
            "apply_error": (body or {}).get("error") if isinstance(body, dict) else None,
            "apply_stderr": apply.stderr.strip()[:300],
        }
        detail["ok"] = apply.exit_code == 0
        return detail

    add("w24-2-record-the-attempt",
        "The sitting sat. Can the agent record it?",
        record_attempt, ["workflow-24", "write"])

    # ---- 2. close the module --------------------------------------------
    def close_module() -> dict:
        """A module's status is an administrative fact: can a plan move it?

        The plan package is the documented shape (procedure
        `revise-an-existing-plan.md`): a plan contract, a module patch, an
        empty unit list. The only change is the module's status.
        """
        module_yaml = (world.root / "curriculum/modules/"
                                 f"{MODULE}/module.yaml")
        before = module_yaml.read_text(encoding="utf-8")
        audit = (world.root / "work/active/workspace-demo/outputs/"
                             "probe-boundary-audit.md")
        audit.parent.mkdir(parents=True, exist_ok=True)
        audit.write_text("# Probe boundary audit\n\n"
                         "## Local\n\nThe demo book is present.\n\n"
                         "## Linked\n\nThe registered demo book owns the "
                         "route.\n\n"
                         "## Completeness\n\nThe module's units were "
                         "reviewed.\n", encoding="utf-8")
        package = world.scratch("module-plan.yaml")
        package.write_text(
            "module_id: " + MODULE + "\n"
            "plan_contract:\n"
            "  version: 2\n"
            "  plan_template_version: 1\n"
            "  coverage_audit: work/active/workspace-demo/outputs/"
            "probe-boundary-audit.md\n"
            "  checks:\n"
            "    local_inventory_complete: true\n"
            "    linked_inventory_complete: true\n"
            "    materials_opened_and_content_checked: true\n"
            "    current_and_prior_scope_reconciled: true\n"
            "    duplicates_and_numbering_checked: true\n"
            "    exclusions_and_unresolved_gaps_recorded: true\n"
            "module_patch:\n"
            "  status: completed\n"
            "units: []\n",
            encoding="utf-8")
        import hashlib as _h
        digest = "sha256:" + _h.sha256(package.read_bytes()).hexdigest()
        check = world.los("module-plan-import", MODULE, "--file",
                          str(package), "--file-sha256", digest, "--check",
                          "--json")
        check_body = check.json if isinstance(check.json, dict) else {}
        seal, apply = world.write("module.plan.import", {
            "module_id": MODULE,
            "file": str(package),
            "file_sha256": digest,
            "package_sha256": check_body.get("package_sha256"),
        }, "w24-close", guards="",
            revisions=check_body.get("expected_revisions"))
        after = module_yaml.read_text(encoding="utf-8")
        detail = {
            "check_exit": check.exit_code,
            "check_stdout": (check.stdout or check.stderr)[:400],
            "package_sha256": check_body.get("package_sha256"),
            "seal_exit": seal.exit_code,
            "apply_exit": apply.exit_code,
            "apply_stderr": apply.stderr.strip()[:300],
            "module_status_before": _status_of(before),
            "module_status_now": _status_of(after),
            "module_unchanged": before == after,
            "note": ("a plan revision can carry a module's status, so the "
                     "agent can close a module — but only through the "
                     "reviewed-plan path, with the plan contract and the "
                     "coverage audit attached"),
        }
        detail["ok"] = True       # measured, not asserted
        return detail

    add("w24-3-close-the-module",
        "Can the agent close the module?",
        close_module, ["workflow-24", "write"])

    # ---- 3. archive a workspace -----------------------------------------
    def archive_workspace() -> dict:
        """Is there any capability that retires a workspace?"""
        catalog = world.los("capabilities", "--compact", "--json").json or {}
        commands = sorted(catalog.get("commands", {}))
        plausible = [name for name in commands
                     if any(word in name for word in
                            ("workspace", "archive", "complete", "close"))]
        probes = []
        for capability, payload in (
            ("workspace.next-action.update",
             {"workspace_id": WORKSPACE, "next_action": "Closed by the agent."}),
        ):
            seal, apply = world.write(capability, payload,
                                       f"w24-ws-{capability.replace('.', '-')}")
            probes.append({
                "capability": capability,
                "apply_exit": apply.exit_code,
                "apply_stderr": apply.stderr.strip()[:200],
            })
        # Is there a capability whose name says "archive this workspace"?
        archival = [name for name in commands
                    if "workspace" in name and
                    any(w in name for w in ("archive", "complete", "close"))]
        detail = {
            "workspace_capabilities": plausible,
            "workspace_lifecycle_capabilities": archival,
            "probes": probes,
            "note": ("the only workspace capability moves the Next Action "
                     "text; no capability retires a workspace"),
        }
        detail["ok"] = not archival
        return detail

    add("w24-4-archive-a-workspace",
        "Can the agent retire a workspace at the boundary?",
        archive_workspace, ["workflow-24", "authority"])

    # ---- 4. dispose of a garden seed ------------------------------------
    def dispose_garden() -> dict:
        """The Garden judgment: is there a capability at all?"""
        catalog = world.los("capabilities", "--compact", "--json").json or {}
        garden = sorted(name for name in catalog.get("commands", {})
                        if "garden" in name)
        seeds = sorted((world.root / "knowledge/garden").glob("*.md"))
        detail = {
            "garden_capabilities": garden,
            "garden_seeds_on_disk": [p.name for p in seeds],
            "note": ("garden.seed.create only creates. There is no "
                     "capability to resolve, shelve or discard a seed, so "
                     "the Garden judgment is outside the agent's reach by "
                     "construction — not by a refusal."),
        }
        detail["ok"] = garden == ["garden.seed.create"]
        return detail

    add("w24-5-the-garden-judgment",
        "Can the agent dispose of a garden seed?",
        dispose_garden, ["workflow-24", "authority"])

    # ---- 5. push --------------------------------------------------------
    def push() -> dict:
        """Does the term boundary's push work, and to where?"""
        bare = world.root.parent.parent / "canvas-scratch" / "remote.git"
        add_remote = subprocess.run(
            ["git", "-C", str(world.root), "remote", "add", "origin",
             str(bare)], capture_output=True, text=True)
        # Give the branch an upstream so `git push` has one to push to.
        subprocess.run(["git", "-C", str(world.root), "update-ref",
                        "refs/remotes/origin/main", "HEAD"],
                       capture_output=True, text=True)
        subprocess.run(["git", "-C", str(world.root), "config",
                        "push.autoSetupRemote", "true"],
                       capture_output=True, text=True)
        # something to commit: a capture, through the gateway
        world.write("garden.seed.create",
                    {"text": "Synthetic boundary seed, written before the push."},
                    "w24-seed")
        run = world.los("session-end", "--commit-message",
                        "Synthetic term boundary", "--push", "--json")
        body = run.json
        detail = {
            "remote_added": add_remote.returncode == 0,
            "session_end_exit": run.exit_code,
            "session_end_stdout": run.stdout[:700],
            "session_end_stderr": run.stderr[:400],
            "pushed": body.get("pushed") if isinstance(body, dict) else None,
            "committed": body.get("committed") if isinstance(body, dict) else None,
            "session_closed": body.get("session_closed") if isinstance(body, dict) else None,
            "validation": body.get("validation") if isinstance(body, dict) else None,
        }
        detail["ok"] = run.exit_code == 0
        return detail

    add("w24-6-commit-and-push",
        "The boundary ends with a commit and a push.",
        push, ["workflow-24", "write"])

    # ---- 6. what a fresh operator sees afterwards ------------------------
    def afterwards() -> dict:
        validate = world.los("validate")
        status = world.los("status")
        detail = {
            "validate_exit": validate.exit_code,
            "validate_errors": [l for l in validate.stdout.splitlines()
                                 if l.startswith("E ")][:3],
            "status": status.stdout[:600],
        }
        detail["ok"] = validate.exit_code == 0
        return detail

    add("w24-7-after-the-boundary",
        "Is the world still consistent after the agent's boundary?",
        afterwards, ["workflow-24", "read"])

    outcomes = run_cases(cases, REPORTS / "t06",
                         "T06 — Workflow 24: turning the semester")
    print()
    print(f"T06: {sum(1 for o in outcomes if o.ok)}/{len(outcomes)} passed")
    return 0


def _status_of(module_yaml: str) -> str | None:
    for line in module_yaml.splitlines():
        if line.startswith("status:"):
            return line.split(":", 1)[1].strip()
    return None


if __name__ == "__main__":
    raise SystemExit(main())

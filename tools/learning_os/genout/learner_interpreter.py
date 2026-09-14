import json
from datetime import datetime

from ..learning_runtime import collect_requirements, read_observations, requirement_fingerprint
from ..loader import Repo

NEGATIVE_RESULTS = frozenset({"incorrect", "partial"})


def interpret_observations(observations: list[dict], requirement: dict | None = None) -> dict:
    """Credit only distinct unaided activities meeting the target's evidence contract.

    A negative result is read four ways, and keeping them apart is the whole
    point of this function:

    * **Current-target failure** — the record is against this exact definition
      and carries every condition the target names. It resets the successes
      before it; that is what "I still get this wrong" is supposed to do.
    * **A different situation** — the record says outright that one of the
      target's conditions did *not* hold (``conditions_not_met``). It bears on
      something else, so it resets nothing and leaves nothing open.
    * **Stale** — the definition has since changed (``requirement_sha256``
      differs). Visible, and never a statement about the current question.
    * **Unresolved** — the record is against this definition but does not say
      whether the target's conditions held. It is not a failure and it is not
      nothing: it is a report of difficulty nobody can interpret yet.

    That fourth case used to be silently discarded. Recording a new difficulty
    through the advertised minimal path — `los observe … --result partial
    --note "a new unfamiliar example exposed the misconception"`, with no
    ``--condition`` flags — left the requirement reading ``demonstrated``,
    ``satisfied``, no next steps: the learner said "I still get this wrong" and
    the system went on telling him he was finished (audit
    `workbench/audits/synthetic-learner-2026-09-12`, F02).

    Nothing here infers the missing flags. "Unfamiliar", "uncued" and
    "unassisted" are claims about what actually happened, and an absent field
    is not a quiet yes — reading it as one would manufacture the very evidence
    qualifiers this system exists to keep honest. So an unresolved result does
    not demote the work to ``fragile`` either, which would assert a breakdown
    just as unfounded. It withholds the satisfied verdict and asks.

    **Difficulty resets the basis, it does not discard the history.** A report
    the system cannot read still means the previous conclusion is no longer
    current, so the successes that produced it stop counting toward it — the
    same epoch reset a qualified failure performs, without the breakdown a
    qualified failure asserts. Only an explicit correction, or two distinct
    qualified activities recorded *after* the difficulty, establish a new
    basis, and the activities already credited before it are spent: redoing
    one is consistent with the difficulty rather than an answer to it. Without
    that, repeating a single already-credited activity put the success set
    back at two and the requirement read ``demonstrated``, ``satisfied``
    again — the reported difficulty cleared by evidence that predated it
    (review `workbench/audits/repair-review-2026-09-13`, R1/D4). The rule
    applies to a qualified failure too, on the same reasoning: D4 names the
    unresolved case because that is what was reported, but "answered by
    evidence that predates the difficulty" is the same defect either way.

    When later evidence does restore the conclusion, the original report stays
    in ``resolved_difficulty`` alongside the exact activities that justified
    moving on; its missing facts are never treated as filled in. Attempts that
    could not count toward the new basis are named in ``not_counted_evidence``
    rather than silently ignored.
    """
    ordered = sorted(observations, key=lambda obs: (datetime.fromisoformat(obs["timestamp"]), obs["id"]))
    evidence_ids = [obs["id"] for obs in ordered]
    conditions = set((requirement or {}).get("conditions", []))
    evidence_spec = set((requirement or {}).get("evidence_spec", []))
    requirement_hash = requirement_fingerprint(requirement) if requirement else None
    superseded = {obs["supersedes"] for obs in ordered if obs.get("supersedes")}
    successes: set[str] = set()
    qualified: list[str] = []
    unresolved: list[dict] = []
    resolved: list[dict] = []
    elsewhere: list[dict] = []
    spent: set[str] = set()
    not_counted: list[dict] = []
    had_success = False
    recent_failure = False
    for obs in ordered:
        if obs["id"] in superseded:
            continue
        current = bool(evidence_spec) and obs.get("requirement_sha256") == requirement_hash
        stated = set(obs.get("conditions", []))
        refuted = sorted(conditions & set(obs.get("conditions_not_met", [])))
        missing = sorted(conditions - stated - set(refuted))
        matches = current and not missing and not refuted
        unaided = obs.get("assistance", "").strip().lower() == "none"
        negative = obs["result"] in NEGATIVE_RESULTS
        if current and refuted and negative:
            # He said which condition did not hold. That is an answer, not a
            # gap: the attempt happened somewhere else, so it neither resets
            # this target's successes nor leaves a question open.
            elsewhere.append({"id": obs["id"], "result": obs["result"],
                              "conditions_not_met": refuted})
        elif matches and negative:
            recent_failure = True
            unresolved.clear()
            spent |= successes
            successes.clear()
            qualified.clear()
        elif current and missing and negative:
            # Against this target, reporting difficulty, silent about the
            # conditions. Held open until he says, or corrects it — and the
            # basis that stood before it stops being current.
            unresolved.append({
                "id": obs["id"],
                "result": obs["result"],
                "missing_conditions": missing,
                "assistance_stated": "assistance" in obs,
            })
            spent |= successes
            successes.clear()
            qualified.clear()
        elif (matches and unaided and obs["result"] == "correct"
              and evidence_spec <= set(obs.get("evidence_tags", []))):
            had_success = True
            if (unresolved or recent_failure) and obs["activity"] in spent:
                # Redoing an activity that was already part of the credit the
                # difficulty invalidated does not rebuild it. Passing the same
                # task again is consistent with the difficulty rather than an
                # answer to it, and treating it as one is how a reported
                # difficulty got cleared by evidence that predated it (review
                # `workbench/audits/repair-review-2026-09-13`, R1/D4).
                not_counted.append({
                    "id": obs["id"],
                    "activity": obs["activity"],
                    "reason": "this activity was already credited before the "
                              "open difficulty, so repeating it cannot "
                              "establish a new basis",
                })
                continue
            successes.add(obs["activity"])
            qualified.append(obs["id"])
            if len(successes) >= 2:
                recent_failure = False
                # Two distinct qualified activities *since* the difficulty are
                # a new current basis. The report itself stays on the record.
                for row in unresolved:
                    resolved.append({**row, "resolved_by": list(qualified)})
                unresolved.clear()
                # Recovery does not make earlier credited activities new.
                # Keep them spent if another difficulty opens later; otherwise
                # A/B -> difficulty -> C/D -> difficulty -> A/B restores the
                # conclusion using precisely the old credit D4 excludes.
    status = "unseen" if not ordered else "uncertain"
    if len(successes) >= 2 and not recent_failure:
        status = "demonstrated"
    elif recent_failure and had_success:
        status = "fragile"
    # `withheld` is whether a satisfied recommendation was actually displaced,
    # which is what the learner is told. An `uncertain` target was already
    # honest about what is established, and claiming otherwise would be its own
    # small lie.
    withheld = bool(unresolved) and had_success
    if unresolved:
        status = "unresolved"
    unresolved_reason = (_unresolved_reason(unresolved, withheld=withheld)
                         if unresolved else None)
    reasons = {
        "demonstrated": _demonstrated_reason(resolved),
        "unresolved": unresolved_reason,
    }
    return {
        "status": status,
        "unresolved_reason": unresolved_reason,
        "evidence_ids": evidence_ids,
        "evidence_basis": [{"id": obs["id"], **obs.get("origin", {})} for obs in ordered],
        "qualifying_evidence_ids": qualified,
        "superseded_evidence_ids": sorted(superseded),
        "unresolved_evidence": unresolved,
        "resolved_difficulty": resolved,
        "different_condition_evidence": elsewhere,
        "not_counted_evidence": not_counted,
        "requirement_sha256": requirement_hash,
        "last_observed_at": ordered[-1]["timestamp"] if ordered else None,
        "derivation": "target-conditions-and-evidence-v3",
        "reason": reasons.get(status, "insufficient or conflicting target-specific evidence"),
    }


def _demonstrated_reason(resolved: list[dict]) -> str:
    """Say what established this, and what it had to get past."""
    base = ("two distinct unaided activities meet the target conditions and "
            "evidence specification")
    if not resolved:
        return base
    ids = sorted({obs_id for row in resolved for obs_id in row["resolved_by"]})
    count = len(resolved)
    noun = "report" if count == 1 else "reports"
    return (
        f"{base}. {count} earlier {noun} of difficulty ({', '.join(row['id'] for row in resolved)}) "
        f"never said whether the target's conditions held, and that is still "
        f"unknown; it was answered by new evidence rather than explained — "
        f"{', '.join(ids)} were recorded afterwards."
    )


def _unresolved_reason(unresolved: list[dict], *, withheld: bool) -> str:
    """Name the difficulty and the exact flags that would settle it.

    ``withheld`` says whether this actually displaced a satisfied verdict. It
    usually does, and claiming it when it did not would be its own small lie —
    an `uncertain` target was already reporting that nothing is established.
    """
    missing = sorted({name for row in unresolved for name in row["missing_conditions"]})
    count = len(unresolved)
    noun = "result" if count == 1 else "results"
    consequence = (
        "the recommendation to move on is withheld until that is settled"
        if withheld else
        "it is not read as a failure of this target and resets nothing"
    )
    flags = " ".join(f"--condition {name}" for name in missing)
    not_met = " ".join(f"--condition-not-met {name}" for name in missing)
    return (
        f"{count} {noun} reported difficulty against this target without saying "
        f"whether its conditions held, so {consequence}. Missing: "
        f"{', '.join(missing)}. Settle it by superseding the result with the "
        f"same report plus {flags} if they held, or "
        f"{not_met} for the ones that did not — or by recording two distinct "
        f"qualified activities after it, which establishes a new basis without "
        f"claiming the missing facts were ever known."
    )


def build_learner_interpretations_json(repo: Repo, generated_at: str) -> str:
    interpretations = _collect_and_interpret(repo)
    output = {
        "_generated": {
            "generated_at": generated_at,
            "warning": "GENERATED file - do not edit; rebuilt by python tools/generate.py"
        },
        "interpretations": interpretations
    }
    return json.dumps(output, separators=(",", ":"), sort_keys=True, ensure_ascii=False)

def build_learner_interpretations_md(repo: Repo) -> str:
    interpretations = _collect_and_interpret(repo)
    lines = ["# Learner Interpretations (Runtime Projection)\n", "> **WARNING:** This file is GENERATED. Do not edit directly.\n"]
    if not interpretations:
        lines.append("No interpretations available.")

    for req_id, data in sorted(interpretations.items()):
        lines.append(f"## {req_id}")
        lines.append(f"- **Status**: `{data['status']}`")
        if "blockers" in data:
            lines.append(f"- **Blockers**: {', '.join(data['blockers'])}")
        lines.append(f"- **Reason**: {data['reason']}")
        lines.append(f"- **Requirement definition**: `{data['requirement_sha256']}`")
        qualified = set(data["qualifying_evidence_ids"])
        superseded = set(data["superseded_evidence_ids"])
        unresolved = {row["id"] for row in data.get("unresolved_evidence", [])}
        answered = {row["id"] for row in data.get("resolved_difficulty", [])}
        elsewhere = {row["id"] for row in data.get("different_condition_evidence", [])}
        for basis in data["evidence_basis"]:
            label = ("corrected" if basis["id"] in superseded
                     else "qualifying" if basis["id"] in qualified
                     else "unresolved difficulty" if basis["id"] in unresolved
                     else "difficulty answered by later evidence" if basis["id"] in answered
                     else "a different situation" if basis["id"] in elsewhere
                     else "not qualifying")
            lines.append(f"- **Evidence**: `{basis['id']}` — {label}; `{basis.get('path', '')}:{basis.get('line', '')}`")
        lines.append("\n---\n")
    return "\n".join(lines) + "\n"

def _collect_and_interpret(repo: Repo) -> dict[str, dict]:
    requirements = collect_requirements(repo)
    observations = read_observations(repo, requirements)
    return {
        req["id"]: interpret_observations(
            [obs for obs in observations if obs["requirement"] == req["id"]], req
        )
        for req in requirements
    }

"""Direct-user-gesture admission: which capabilities a gesture may authorize, and from which channel."""

from __future__ import annotations

#: Capabilities admitted to ``direct-user-gesture`` approval from any channel.
#:
#: The gesture kind means "the user herself acted", so the test is what the
#: write *is*, not which process sent it: admitted exactly when the record
#: being written is the learner's own study activity or her own choice among
#: material someone already authored — her progress, her prose, her files,
#: her experience of a resource, her questions, her selections — bounded to
#: one unit, stage or workspace and guarded by exact artifact revisions.
#:
#: Canonical semantics, plan structure and content are not on this list. Some
#: of them are admitted through ``UI_REVIEWED_ALLOWLIST`` below, which is a
#: narrower thing: the same approval kind, restricted to the ``ui`` channel,
#: for the workflows where the application shows the exact change before an
#: explicit Save or Apply. Everything else — every agent-origin semantic
#: write — keeps the approved operator/delivery path.
#:
#: Until 2026-09-13 this list held only the three writers that happened to
#: exist when it was introduced, and its comment described `capture.create`
#: and `garden.seed.create` as "the pre-existing UI-originated writers" —
#: which was never true. The installed UI drove eleven more write paths
#: through the same gesture, and Core refused four ordinary study actions in
#: the learner's face (audit `synthetic-learner-2026-09-12`, F01). The
#: policy above is the one this list now implements; the mirror in
#: ``system/contracts/capabilities.yaml`` (``admission:``) is pinned to it by
#: ``tests/test_observation_gesture.py``, and the UI's own producer-side copy
#: is pinned by its ``scripts/check-contract.mjs``.
GESTURE_ALLOWLIST = frozenset({
    # Aram's own evidence: append-only ledger, tested ``--supersedes``
    # correction path, one JSONL line of blast radius, and a local
    # `los observe` command where the terminal session is the approval.
    "learner.observation.append",
    # Her explicit decision on a proposed goal: one ledger map write,
    # batch-bound by the exact `--check` review, terminal-approved (D8).
    "goal.decision.record",
    # Unrouted, unclassified inbox and Garden input; the handler names the
    # file, so both guard the request rather than an artifact.
    "capture.create",
    "garden.seed.create",
    # Her own study record for one stage or unit.
    "stage.progress.update",
    "unit.note.append",
    "stage.attachment.add",
    "detour.create",
    "detour.resolve",
    # Her own contextual experience of a resource. The source record's own
    # identity and evaluations are untouched — that judgment stays canonical
    # and stays off this list.
    "source.feedback.record",
    # Her own question, and its open/resolved state (ADR-017). Wording and
    # target are preserved by the handler; this never describes mastery.
    "atlas.question.save",
    # Her choice among the routes the module map already offers. The complete
    # material menu is authored content and is unchanged by a selection.
    "unit.source-selection.set",
})


#: Canonical changes this application may authorize, and only this application.
#:
#: ADR-017 designed the Atlas for Aram to author concept connections by hand,
#: without an AI provider, an external editor, or handwritten YAML. Refusing
#: that legibly is still refusing it, and a readable refusal does not satisfy
#: a current, binding architecture decision (review
#: `workbench/audits/repair-review-2026-09-13`, D1). The same reasoning covers
#: the rest: shelving *preparation* applies nothing at all, while shelving
#: *application*, a study-map import, and the two append-only ability records
#: (a confirmed claim and a tentative connection, added 2026-09-23) each show
#: the exact change first and then wait for a deliberate control.
#:
#: **A deliberate Save or Apply on an exact visible preview is the review.**
#: That is what these contracts already meant by explicit approval; the review
#: was happening on screen and the envelope had no way to say so. There is no
#: second approval protocol here, no extra confirmation dialog, and no
#: relabelling of a click as operator approval — the same V2 envelope, the same
#: guards, the same receipt.
#:
#: The restriction to ``channel == "ui"`` is what keeps this from widening
#: agent authority: a codex- or system-task-origin envelope claiming a gesture
#: for these still fails closed. The channel label is provenance inside this
#: trusted local application, not cryptographic proof that a human was present,
#: and it is not treated as more than that. Every guard these capabilities
#: already carry — exact previous rows, registry and artifact revisions, the
#: snapshot, duplicate/endpoint/cycle checks, exact-byte binding of reviewed
#: files, the import preflight — is unchanged, and that is what actually
#: protects canonical state.
UI_REVIEWED_ALLOWLIST = frozenset({
    # Connections Aram authored, applied from the exact-row preview (ADR-017).
    "concept.relations.change",
    # Preparing a shelving packet proposes; it applies nothing.
    "review.prepare",
    # Applying the selected items, after their proposed changes were shown.
    "review.apply",
    # A reviewed map file, after its no-write `--check` preflight.
    "unit.map.import",
    # Aram's own ability claim, recorded from Review only after the exact
    # record — claim, result, assistance, conditions, criteria, work pointer —
    # is on screen, with "Confirm & record" as the deliberate control. Its
    # confirmation pointer names that app request, so the receipt is the
    # confirmation. Append-only: corrections supersede, never rewrite, and the
    # reviewed ability identity is still bound by its claim, conditions, and criteria hash.
    # Admitted over `ui` only (Aram, 2026-09-23): an agent that records a
    # claim Aram confirmed in conversation keeps the operator path.
    "learner.ability-observation.append",
    # A tentative connection Aram noticed, recorded from the same exact
    # preview. It carries no evidence and never changes a reviewed bridge,
    # readiness or transfer; promotion to a bridge stays an operator review.
    "ability.candidate.append",
})


#: Channels a reviewed-UI admission accepts. One entry, deliberately.
UI_REVIEWED_CHANNELS = frozenset({"ui"})


#: Why a gesture is not enough, per capability, for the write paths an
#: interface can legitimately reach from a human click. Core answers with this
#: instead of naming the approval kind: "direct-user-gesture is not admitted
#: for X" is true, and tells a learner nothing she can act on.
GESTURE_REFUSAL_RECOVERY: dict[str, str] = {
    "module.plan.import": (
        "a module plan is applied from a reviewed file after its required "
        "preflight, through an operator request (WORKFLOWS §25a)"
    ),
    "route.patch": (
        "material details change through the reviewed `route-patch --check` "
        "preflight and an operator request (WORKFLOWS §25a)"
    ),
    "note.revise": (
        "revising a note body is a semantic edit: it needs an explicit "
        "request and a reviewable diff, not a gesture"
    ),
    "stage.note.write": (
        "this is a retired compatibility surface; save the note against the "
        "unit with unit.note.append instead"
    ),
}


def gesture_allowed(capability: str, channel: str | None = None) -> bool:
    """Whether a capability admits ``direct-user-gesture`` from this channel.

    ``channel`` is optional so a focused caller that already knows the request
    is user-originated (``los observe``) need not restate it; a reviewed-UI
    capability, however, is admitted only when the channel is actually named.
    """
    if capability in GESTURE_ALLOWLIST:
        return True
    return (capability in UI_REVIEWED_ALLOWLIST
            and channel in UI_REVIEWED_CHANNELS)


def gesture_refusal(capability: str, channel: str | None = None) -> str:
    """Explain a gesture refusal in terms of what to do instead."""
    if capability in UI_REVIEWED_ALLOWLIST:
        # Not "this needs approval" — it has one, from the wrong producer.
        return (
            f"{capability} is authorized by a reviewed action in the "
            f"LearningOS app, not by a {channel or 'remote'}-channel request: "
            f"apply it from the screen that shows the exact change, or send it "
            f"through the approved operator path"
        )
    recovery = GESTURE_REFUSAL_RECOVERY.get(capability)
    if recovery:
        return (
            f"{capability} cannot be authorized by a direct user gesture: "
            f"{recovery}"
        )
    return (
        f"{capability} cannot be authorized by a direct user gesture: it "
        f"writes canonical content, which needs an approved operator request "
        f"rather than a click"
    )

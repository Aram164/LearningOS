"""Finite durability protocol model; S9 extends it with reviewed retirement.

The model distinguishes namespace visibility from persistence. A failed barrier
may leave the visible rename durable or volatile. This is a logical persistence
model, not a claim that process termination simulates physical power loss.
Production interruption witnesses are attached when S1/S2 integrate the helper.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class State:
    phase: str = "start"
    journal: bool = False
    data: bool = False
    data_durable: bool = False
    receipt: bool = False
    receipt_durable: bool = False
    settled: bool = False


def transitions(state: State, *, broken_rollback: bool = False) -> list[tuple[str, State]]:
    steps = {
        "start": ("journal-barrier", {"phase": "journal", "journal": True}),
        "journal": ("data-publish", {"phase": "data", "data": True}),
        "data": ("data-barrier", {"phase": "data-durable", "data_durable": True}),
        "data-durable": ("receipt-publish", {"phase": "receipt", "receipt": True}),
        "receipt": ("receipt-barrier", {"phase": "committed", "receipt_durable": True}),
        "committed": ("settlement-barrier", {"phase": "settled", "settled": True}),
        "settled": ("journal-retire", {"phase": "done", "journal": False}),
    }
    results = []
    if state.phase in steps:
        name, changes = steps[state.phase]
        results.append((name, replace(state, **changes)))
    if state.phase in {"journal", "data", "data-durable"}:
        results.append(("failure-before-receipt: guarded-rollback",
                        State(phase="rolled-back")))
    if state.phase == "receipt":
        results.append(("receipt-barrier-failed: preserve-forward",
                        replace(state, phase="uncertain")))
        if broken_rollback:
            results.append(("BROKEN: rollback-behind-visible-receipt",
                            replace(state, phase="broken", data=False, data_durable=False)))
    if state.phase in {"receipt", "uncertain"}:
        # The receipt rename may already be persistent despite the failed or
        # interrupted directory barrier. Both outcomes must remain coherent.
        results.extend([
            ("power-loss: receipt-survives", replace(state, phase="restart-committed",
                                                    receipt_durable=True)),
            ("power-loss: receipt-absent", replace(state, phase="restart-uncommitted",
                                                  receipt=False)),
        ])
    if state.phase == "restart-committed":
        results.append(("recovery: establish-durability", replace(state, phase="committed")))
    if state.phase == "uncertain":
        results.append(("recovery: visible-valid-receipt", replace(state, phase="committed",
                                                                 receipt_durable=True)))
    if state.phase == "restart-uncommitted":
        results.append(("recovery: rollback-without-receipt", State(phase="rolled-back")))
    return results


def invariant(state: State) -> bool:
    return (
        (not state.receipt or (state.data and state.data_durable))
        and (not state.receipt_durable or state.receipt)
        and (not state.settled or state.receipt_durable)
        and (not state.receipt or state.receipt_durable or state.journal)
    )


def explore(*, broken_rollback: bool = False) -> tuple[set[State], list[str] | None]:
    queue = deque([(State(), [])])
    seen = set()
    while queue:
        state, trace = queue.popleft()
        if state in seen:
            continue
        seen.add(state)
        if not invariant(state):
            return seen, trace
        queue.extend((following, [*trace, step]) for step, following in transitions(
            state, broken_rollback=broken_rollback))
    return seen, None


def test_finite_protocol_preserves_receipt_and_forward_effects():
    states, violation = explore()
    assert violation is None, violation
    assert {"uncertain", "done", "restart-committed", "restart-uncommitted", "rolled-back"} <= {
        state.phase for state in states}


def test_disabled_receipt_protection_has_a_counterexample():
    _, violation = explore(broken_rollback=True)
    assert violation is not None
    assert violation[-1] == "BROKEN: rollback-behind-visible-receipt"

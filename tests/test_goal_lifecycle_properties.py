"""The earned 90% of TLA+: the goal lifecycle as a data table over 13
states deserves an exhaustive walk, not a model checker. Three protocol
properties, pinned in plain pytest: authorization is unreachable without
proposal, terminal states have no exits, and every non-terminal state can
still reach a terminal one.
"""

from __future__ import annotations

from learning_os.semantics.goals import STATES, TERMINAL_STATES, TRANSITIONS


def _reachable(start: str) -> set[str]:
    seen, frontier = set(), [start]
    while frontier:
        state = frontier.pop()
        for nxt in TRANSITIONS[state]:
            if nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    return seen


def test_authorized_is_unreachable_without_proposed():
    predecessors = [state for state in STATES if "authorized" in TRANSITIONS[state]]
    assert predecessors == ["proposed"]
    # Belt and braces: enumerate every simple path out of `detected` and
    # require `proposed` on each one that arrives at `authorized`.
    paths = [("detected",)]
    for _ in STATES:
        grown = False
        for path in list(paths):
            for nxt in TRANSITIONS[path[-1]]:
                if nxt in path:
                    continue
                paths.append((*path, nxt))
                grown = True
        if not grown:
            break
    arrivals = [path for path in paths if path[-1] == "authorized"]
    assert arrivals, "authorized is reachable at all"
    assert all("proposed" in path for path in arrivals)


def test_terminal_states_have_no_exits():
    assert set(TERMINAL_STATES) == {"closed", "rejected", "superseded"}
    for state in TERMINAL_STATES:
        assert TRANSITIONS[state] == (), f"{state} is terminal but exits"
    for state in STATES:
        assert state in TRANSITIONS, f"{state} has no declared exits"


def test_every_non_terminal_state_can_reach_a_terminal_one():
    terminal = set(TERMINAL_STATES)
    for state in STATES:
        if state in terminal:
            continue
        assert _reachable(state) & terminal, \
            f"{state} can never reach a terminal state"

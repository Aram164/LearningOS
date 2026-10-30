# Claude task adapter

The assigned task determines the reading route. This adapter grants no standing
role and no extra write authority. Paths are from the Core repository root,
which is `repository/` if you start one level above it.

This repository is one learner's study system. A message about where the learner
stopped, what to study, a result to record, a plan to change, or one starting
with `log:` is learner work: use the operator route. Answer it from the entry
read, not from Git history or `work/proposals/`, which record how the system was
built.

- **Change code, architecture, contracts, tests or documentation:** read
  [system/DEVELOPER.md](DEVELOPER.md), then the owning component and task references.
- **Operate learner records:** read [system/OPERATOR.md](OPERATOR.md) and use its task
  entry read. Open [system/OPERATOR-POLICY.md](OPERATOR-POLICY.md) when the task raises
  a question about permissions, note handling, ambiguity, Garden or migration.
- **Both kinds of work:** preserve the hard boundaries in `system/OPERATOR.md`.
  Audience is a reading route, never permission to ignore a relevant binding rule.

## 2. Bootstrap order

Procedure: [system/procedures/bootstrap-order.md](procedures/bootstrap-order.md).

## 7. Retrieval behavior

Procedure: [system/procedures/retrieval-behavior.md](procedures/retrieval-behavior.md).

The corpus declares authority/status independently from audience. Its two entry
points route the work; the task scope supplies the bounded operator reads.
The Job-policy amendment from ADR-013 is preserved in `system/OPERATOR-POLICY.md`;
this adapter does not reinstate the retired Job boundary.

Former references to CLAUDE.md sections 1, 3–6 and 8–14 now resolve to the
same-numbered sections in `system/OPERATOR-POLICY.md`. Sections 2 and 7 retain their
executable transcript routes here.

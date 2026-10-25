# Claude task adapter

The assigned task determines the reading route. This adapter grants no standing
role and no extra write authority.

- **Change code, architecture, contracts, tests or documentation:** read
  [DEVELOPER.md](DEVELOPER.md), then the owning component and task references.
- **Operate learner records:** read [OPERATOR.md](OPERATOR.md), use its task
  entry read, and consult [OPERATOR-POLICY.md](OPERATOR-POLICY.md) for permissions,
  note handling, ambiguity, Garden and migration policy.
- **Both kinds of work:** preserve the hard boundaries in OPERATOR.md. Audience
  is a reading route, never permission to ignore a relevant binding rule.

## 2. Bootstrap order

Procedure: [bootstrap order](procedures/bootstrap-order.md).

## 7. Retrieval behavior

Procedure: [retrieval behavior](procedures/retrieval-behavior.md).

The corpus declares authority/status independently from audience. Its two entry
points route the work; the task scope supplies the bounded operator reads.
The Job-policy amendment from ADR-013 is preserved in OPERATOR-POLICY.md;
this adapter does not reinstate the retired Job boundary.

Former references to CLAUDE.md sections 1, 3–6 and 8–14 now resolve to the
same-numbered sections in OPERATOR-POLICY.md. Sections 2 and 7 retain their
executable transcript routes here.

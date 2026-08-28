# ADR-013 — Job learning is ordinary learning

**Date:** 2026-08-26 · **Status:** accepted (Aram)

**Supersedes:** ADR-010 and the Job-quarantine/Job-contract portions of ADR-003,
ADR-004, ADR-012, `system/CLAUDE.md` §13, and Architecture invariant 24. Future
Master's Planning quarantine is unchanged.

## Context

LearningOS separated employment-motivated learning into a quarantined `Job/`
tree with its own dashboard, access confirmation, schemas, write commands,
validation exclusions, and UI surface. The separation protected confidentiality
but also added an executive-function decision every time Aram wanted to learn.
It blocked the cross-domain visibility the concept system exists to create.

The content is learning regardless of why it matters. Rust lifetimes, Polars,
ML pipelines, and university statistics need the same materials, concepts,
study maps, notes, evidence, and revision discipline. Confidential employer code
is a separate concern from the learning records derived from studying it.

## Decision

### One learning architecture

Job learning uses ordinary LearningOS records under the active non-semester
program `program-job`:

```text
program-job
└── module
    └── unit
        └── study map
            └── stage
```

The normal program, module, unit, study-map, note, concept, source, search,
manifest, AI-action, validation, gateway, and receipt contracts apply. There is
no Job-specific schema, dashboard, access grant, transaction root, plan profile,
or validation path. The UI may show a `Job` badge or grouped section, but that
is presentation only and confers no authority.

### Stratum stays external

The Stratum Git worktree lives at `semestercontext/Stratum/`, alongside
`LearningOS/`. Its branch, remotes, upstream tracking, and ordinary development
workflow belong to that repository. LearningOS does not index, validate,
migrate, or manage it.

An agent may inspect relevant Stratum paths when the current user task needs
code context, including to inform a learning plan. That inspection does not
turn the repository into LearningOS data and grants no ambient read or write
authority to other workflows.

### Connections grow with the learner

The existing concept and relation system remains open across every module.
Agents may surface candidate connections during study, but no speculative graph
is pre-built. A relation is recorded only after Aram confirms that the
connection is meaningful. The graph grows with demonstrated knowledge rather
than ahead of it.

## Migration

The former Job learning tree is a bounded legacy input to the one-time
`legacy.job-learning.migrate` capability. The reviewed mapping creates
`program-job`, five ordinary modules and units, study maps, notes, concepts,
sources, and provenance without inferring mastery or relations. It removes the
obsolete `program-job-boundary` record in the same atomic transaction and
leaves the source tree untouched for recovery evidence.

Direct apply is refused. The real transaction requires GatewayEnvelopeV2,
ReceiptV2, exact input snapshots, artifact revisions, and the approved plan
hash. Applying it is additionally blocked until an external backup and a
restore-to-new-directory drill prove recovery. Preparing code, contracts, and
dry-run evidence does not satisfy that gate.

## Contract consequences

- Data contract v14 removes the obsolete Job dashboard and Job plan record
  schemas and the Job-only stage branch from the shared learning-plan
  vocabulary. Existing canonical formats remain readable; no canonical data
  migration is required for this schema removal.
- Manifest contract v7 removes `job_derived` from Garden projection rows. Job
  modules use the ordinary projection and the UI mirrors the exact v7 schema
  hash.
- The one-time migration capability remains until the reviewed migration is
  applied and retired. Historical ADRs and frozen contract history remain as
  evidence; they are not active authority.

## Consequences

The system has one fewer access ceremony and one fewer place for behavior to
drift. Job modules can appear beside university and skills modules in normal
search and study flows. Confidentiality is handled by keeping external code
external and scoping any requested inspection, not by hiding the learner's own
knowledge from LearningOS.

Future Master's Planning remains the sole curriculum quarantine. No part of
this decision promotes prospective Master's content or weakens its boundary.

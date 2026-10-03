# ADR-018 — The operation boundary and enforced architecture

**Date:** 2026-10-03

Source: the disposable workbench plan `../PLAN.md` (revision 4), cited by path
for history only.

## Context

LearningOS does what it should, but its construction resists system-wide rules:
PLAN §1 records that four friction rounds kept circling defect kinds with no
single home. PLAN §3 diagnoses why, locating the application core in the CLI
handlers where every rule is re-implemented per command. This ADR records the
accepted plan that gives each such rule one home, one check, and a ratchet that
only shrinks.

## Decision

- **D1** (PLAN §4 D1): replace gradually, moving each operation only once proven equivalent; never a rewrite.
- **D2** (PLAN §4 D2): one operation boundary with authoritative request schemas; the CLI parser is generated with lossless transport metadata.
- **D3** (PLAN §4 D3): typed failure kinds map to public codes, retryability, and exits by invocation context; fine reasons live in `details`.
- **D4** (PLAN §4 D4): handlers return a TransactionProposal; TransactionService keeps its protocol with only a behaviour-neutral phase marker added.
- **D5** (PLAN §4 D5): check runs the pipeline without committing; the seal consumes check guards and apply validates again.
- **D6** (PLAN §4 D6): one identifier module holds canonical forms, parsers, printers, and declared aliases.
- **D7** (PLAN §4 D7): the session is a state machine whose review witness binds ledger version plus exact file states.
- **D8** (PLAN §4 D8): `los goal` goes through the transaction service with receipt, validation, and session membership.
- **D9** (PLAN §4 D9): the existing derived engine is the only cache substrate after a full cache inventory.
- **D10** (PLAN §4 D10): Ajv owns UI wire shape in production while handwritten decoders keep contextual bindings.
- **D11** (PLAN §4 D11): procedures are executable transcripts under system/procedures, with the runner chosen by a Scrut-first bake-off.
- **D12** (PLAN §4 D12): checks live in tests/architecture with identified exceptions in ratchets.yaml that only shrink.
- **D13** (PLAN §4 D13): runtime declarations go only for migrations that are done; the scripts remain with their fail-closed lifecycle.
- **D14** (PLAN §4 D14): dev tooling is import-linter, strict mypy on new modules, and a pinned Scrut; no new runtime dependency.
- **D15** (PLAN §4 D15): behaviour is characterized by effect scenarios recording outputs, bytes, receipts, and ledger effects.
- **D16** (PLAN §4 D16): one output convention keeps success bytes, adds universal --json, and fixes refusal rendering and exits.
- **D17** (PLAN §4 D17): layers are declared over existing packages; only modules mixing layers are split.
- **D18** (PLAN §4 D18): landing waits for 2026-10-10 and proceeds as reviewable Core/UI pairs from hardened clones after Aram's go-ahead.
- **D19** (PLAN §4 D19): handlers receive an observation and effect context with snapshot plus overridable observation ports.
- **D20** (PLAN §4 D20): the pipeline order is fixed from resolve through trace, with explicit replay branches and a three-way outcome.

## Enforcement

- **A1**: layers point down, enforced by an exhaustive import-linter contract.
- **A2**: one canonical writer, proven by an independent before/after oracle plus audit attribution and a static lint.
- **A3**: no decisions from prose; public codes come only from the typed mapping.
- **A4**: plumbing lives only in the pipeline, never in handlers.
- **A5**: every lookup miss suggests the near-matched value with a NOT_FOUND reason.
- **A6**: every printed id parses as canonical in every same-kind command field.
- **A7**: one output convention per operation: --json, the error schema, and the characterized exit and retryability.
- **A8**: docs run; every transcript executes and every doc command parses.
- **A9**: every declared refusal site is witnessed by a scenario asserting its effect.
- **A10**: every engine-backed cache proves warm transitions against uncached results on an independent input inventory.
- **A11**: the generated surface snapshot matches the base except for approved entries.
- **A12**: behaviour is unchanged, proven by effect scenarios and captured-world identity.
- **A13**: request schemas are complete with descriptions, id kinds, CLI metadata, and examples.
- **A14**: one error vocabulary defined once and generated into the envelope schema.
- **A15**: every session state transition is tested, including failed commit and failed push.
- **A16**: recovery and retry scenarios cover replay, escalation, rollback, and crashes at every named point.

## Consequences

Four defect classes become structurally impossible rather than merely fixed.
Classifying failures by matching prose gives way to typed kinds with a
contextual outcome mapping, so a message can never again decide a code. Writing
canonical files outside the transaction engine fails the write witness, so no
second writer can grow silently. Procedures that do not execute cannot pass,
because the document is the test. And the public surface cannot drift, because
the frozen snapshot refuses any unapproved addition, removal, or change.

## Status

Accepted (Aram, 2026-10-03): Aram accepted PLAN revision 4 on 2026-10-03.

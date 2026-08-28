# Unit Working Notes

## Title

Polars ↔ pandas fluency — one operation, two backends

## Horizon

now

## Cadence

One 90–120 minute session per week. Each session runs the same five-pass loop: retrieve from memory, solve it in pandas, mirror it in Polars, record every behavioural difference, then classify each difference against the eight divergence axes and commit a failing case for it to the standing parity harness built in Stage 2. Every fourth session, spend 30 minutes re-solving two earlier exercises without notes. All practice code lives outside Job/stratum.

## Outcome

Given any pandas operation, predict its exact behaviour — values, dtypes, row order, null handling, and failure mode — write the idiomatic Polars equivalent from memory, and state precisely where the two diverge, which divergences can be closed by construction, and which must be declared unsupported. Fluency is evidenced by a cumulative parity harness whose cases were written before the answers were looked up, plus closed-book retrieval; it is never inferred from reading.

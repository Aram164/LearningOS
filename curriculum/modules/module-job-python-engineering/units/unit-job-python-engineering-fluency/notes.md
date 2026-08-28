# Unit Working Notes

## Title

Python engineering fluency — independent design, implementation, and review

## Horizon

now

## Cadence

One 90–120 minute stage per week, with longer engineering capstones explicitly marked. Use the independence loop every time: (1) write the problem, non-goals, inputs, outputs, invariants, failure cases, and a test sketch; (2) spend at least 25 minutes implementing or debugging with no AI; (3) consult official documentation and runtime evidence; (4) only then use an AI agent for questions, critique, or alternative designs; (5) review every suggested line, record accepted and rejected advice, and add a test for a plausible agent mistake; (6) rebuild or explain the core mechanism without AI within 48 hours. Every third week includes a 45-minute no-AI retrieval session. At selected stages, trace one narrow behavior through an open-source repository from public API to implementation to tests; never try to read the whole repository. All practice stays outside the Stratum checkout.

## Outcome

Given an ambiguous Python idea, unfamiliar codebase, or Job ticket, independently turn it into a precise contract; choose clear data and module boundaries; implement a small reviewable change; test normal, boundary, and failure behavior; debug from evidence; reason about types, complexity, resources, concurrency, packaging, and operations; and review or maintain the result over time. AI is a bounded reviewer and accelerator, never the source of the specification or proof of correctness. Fluency is evidenced by delayed no-AI reconstruction, open-source code traces, engineering decision records, and a final maintainable package whose design and every accepted line can be explained.

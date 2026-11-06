# Documentation terminology drift: one artifact under several names, dead section cites (2026-11-06)

Task: agent-perspective hunt on branch `codex/review-shortcomings-20261105`. Workflow
step: cross-document reading.

Observation (verified, texts): one artifact (`notes.md` of a stage) is called "stage
note", "working note", "stage working note", and "stage's working note" across
OPERATOR.md, capture-routing.md, and repository AGENTS.md. `capabilities` (discovery)
vs `capability` (submit) differ by one letter and are both real verbs. Repository
AGENTS.md's compressed entry-read list names 2 of the ~20 entry reads, so an agent with
a `log:` task following it literally starts from the wrong command.
`OPERATOR-POLICY.md` printed section numbering runs 1, 3, 4, 5, 6, 8–14 — no §2, no §7 —
so any external pointer to "POLICY §2/§7" dead-ends.

Inference: none of these change behavior; each raises the chance an agent misroutes a
step, especially under tight context.

Safety retained: routing contracts themselves agree where checked (capture routing,
envelope discipline, log: handling).

Smallest improvement: a short glossary block (OPERATOR.md or developer/CODEMAP.md)
mapping the name variants to the one artifact; renumber or gap-mark POLICY sections
(renumbering moves cite targets, so do it with the corpus/doc checks green).
Safeguards to retain: heading anchors consumed by the procedure index and task-scope.

Filing: GitHub issue not filed — `gh` CLI unavailable (blocked by tooling availability,
2026-11-06). Proposed issue title: "terminology drift across operator docs; POLICY
numbering skips §2 and §7".

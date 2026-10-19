# Intelligence Plane — second reading of the source material (2026-09-11)

Parent: `intelligence-plane-plan.md` and the Phase 0–6/10 + hardening records.
This is not a new phase. It is a re-derivation from the same referenced
systems, asking a different question than the first pass did.

The first pass asked: **what do these systems do, and what is the LearningOS
analogue?** It answered well — seventeen borrowings, fourteen shipped in three
days, three correctly deferred with re-open bars.

This pass asks: **what were these systems built to buy, and does the shipped
analogue buy it here, for one person studying alone with two exams in
nineteen and twenty-eight days?**

Nine of the fourteen shipped analogues buy their intended thing. Five buy the
structure without the payoff, and one imported a trust model backwards. That
delta is this document.

---

## The framing the first pass missed

Every system in the dossier is a **multi-tenant, adversarial, or
high-concurrency** system. Snowflake serves untrusted query authors. Calcite
optimizes for machines that cannot ask. Bazel caches across a fleet. PROV
exists so a third party can audit. Necula's PCC exists because the code
producer is *untrusted by construction*. MVCC exists because writers collide.

LearningOS is none of those. It has **one author, one machine, one operator at
a time, and a lock**. The structures still transfer — the first pass was right
that they do — but the *reason each structure earns its cost* does not
transfer uniformly. Three of them earn it here for a different reason than in
the original, one earns nothing, and one is actively inverted.

The correct import filter for this system is not "is this a good pattern."
It is:

> **Does this reduce the operator's cost of re-entering context, or the cost
> of a wrong study decision?** If neither, it is bulk.

That filter is just ARCHITECTURE.md §1 ("reduce organizational effort rather
than create a second administrative workload") made operational, and it is the
one constraint the Intelligence Plane build did not check itself against.

---

## Finding 0 — the trust model is inverted for the one write that matters

**Source: Necula, proof-carrying code (dossier §14).**

PCC's load-bearing sentence is not "changes carry proofs." It is: *an
**untrusted producer** supplies a proof that its output satisfies the host's
policy.* The asymmetry is the whole idea. A trusted producer carrying a proof
is pure overhead.

What shipped applies the envelope **uniformly by capability**, not by producer.
The consequence:

`learner.observation.append` — Aram recording that he got three of five CLT
questions wrong — currently requires a full GatewayEnvelopeV2:
re-read `bootstrap --compact` for `expected_snapshot`, re-read
`revisions.yaml` for `expected_revisions`, build the payload, compute
`approval.subject_sha256` through the production `intent_sha256` helper, then
`los capability learner.observation.append --payload-file envelope.json`.

That is the identical ceremony as an agent mutating canonical curriculum
semantics. For the one write in the system where:

- the author **is** the ground truth (nothing to prove — he is not an
  untrusted producer of facts about himself),
- the ledger is **append-only** with an explicit `--supersedes` correction
  path (already built, already tested),
- the blast radius is **one JSONL line in one workspace**,
- and the write happens **at the end of a study session**, which is exactly
  when remaining executive capacity is lowest.

There are **zero `observations.jsonl` files in the tree.** I am not reading
that as "he does not study." I am reading it as: the loop that was built to
capture what studying produced costs more than it returns, so it is not used,
and the runtime's replan path has no input.

### Derivation: asymmetric admission

Split the trust decision on **producer × reversibility**, which is what PCC
actually says:

| Producer | Target | Admission |
|---|---|---|
| agent | canonical semantics | full envelope — unchanged |
| agent | anything | full envelope — unchanged |
| Aram | append-only ledger, own evidence | `direct-user-gesture` |

`APPROVAL_KINDS` in `tools/learning_os/contracts/gateway.py` **already
contains `direct-user-gesture`** and nothing in the tree uses it. The concept
was imported and never wired.

**Implementation.** A new approval kind path in
`tools/learning_os/commands/capability.py` that, for a closed allowlist of
capabilities (`learner.observation.append` only, to start) with
`approval.kind == "direct-user-gesture"`, takes the snapshot itself under the
operator lock instead of requiring the caller to supply and hash it. The
snapshot guard does not weaken — it is *taken* rather than *asserted*, which
for a single-writer system with a lock is the same guarantee. `subject_sha256`
is computed internally over the same `intent_subject`, so the receipt is
byte-identical in shape to today's.

Then one thin command:

```
los observe <requirement> --activity exercise --result partial \
    --conditions unfamiliar-example --note "3/5, missed the asymptotic case"
```

- `tools/learning_os/commands/observation.py`: ~40 lines (the append logic
  exists; this adds the direct path and argument surface)
- `tools/learning_os/commands/capability.py`: ~35 lines (the allowlist and
  the gesture branch)
- `system/contracts/capabilities.yaml`: one `admission:` field on the entry
- `tests/`: the allowlist is closed (a capability not on it refuses the
  gesture); the receipt shape is unchanged; a canonical-semantics capability
  can never take this path
- `system/SEMANTIC-CONTRACT.md` + `system/WORKFLOWS.md §8`: the rule, stated

**~110 lines. Highest value item in this document.** It is the difference
between the Learning Runtime having inputs and not having inputs.

**What it does not do:** it does not touch the gateway for any agent-authored
write, does not remove the snapshot guard, does not make the ledger mutable,
and does not extend to a second capability without an explicit decision.

---

## Finding 1 — a detector without a selector is worse than no detector

**Source: goal-driven autonomy (dossier §10) and Snowflake's suggestion
loop (§3).**

GDA's lifecycle is Formulate → **Select** → Expand → Commit → Dispatch.
Snowflake's suggestions arrive *ranked and few*. Both exist because an
unranked candidate list transfers the triage cost to the human, which is the
cost the system was supposed to absorb.

Measured on the live repository today:

```
$ los intelligence-scan --days 14
intelligence scan: 296 candidate investigation(s) — filing is yours:
```

296 goals: 249 `covering-routes-stale`, 22 `lineage-stale`,
22 `source-changed-under-claim`, 3 `study-map-obligation`. **All 296 in state
`detected`.** Nothing has ever reached `formulated`.

Three separate defects produce that number, and all three have small fixes.

### 1a. The dedup channel exists and is never fed

`ScanInput.known_ids` is a declared field. Every detector takes `known_ids`.
`collect_observations()` (`scan.py:411`) **constructs `ScanInput` without it**,
so it defaults to `()` on every run. Every scan re-emits every goal forever,
including ones already rejected.

*Implementation:* `operations/goal-ledger.yaml` — one map of
`goal_id → {state, decided_at, note}`, written only by an explicit
`los goal <id> --reject|--defer|--close`. `collect_observations` reads it and
passes the non-`detected` ids as `known_ids`.
**~50 lines plus a small schema.** The plumbing is already there; this feeds it.

### 1b. The engine does not apply its own rewrite to its own output

`rewrite_dossier_dedup` — common-subexpression elimination, borrowed from
Calcite — shipped in `tasks.py` and is applied to agent task plans. The
redundancy is not in the task plans. It is in the goal queue: the 249
`covering-routes-stale` goals are mostly *one* fact fanned out per route
("SaD L11's nodes moved; N routes cover them").

*Implementation:* a pure `cluster_goals(goals) -> tuple[GoalCluster, ...]` in
`goals.py`, grouping by the shared cause in `evidence` (the `node:` set for
`covering-routes-stale`, the `moved:` key for `lineage-stale`). A cluster
carries the member goal ids so nothing is lost. **~60 lines, pure, trivially
testable.** 296 → roughly 15–25.

### 1c. There is no ordering, because the ordering input was deleted

Phase 4's amendment removed `COST_WEIGHTS`, `step_cost` and all telemetry.
The record documents *what* was removed in detail; it never says *why*, and
commit `0b2f093` has an empty body. In a repository where the deferred-phases
record carries a measurement **and a re-open bar** for every shelved idea,
that is the one decision with no recorded reason.

I think the amendment was right and the replacement was missing. A *learned*
cost model needs data that does not exist and would not exist for months at
this volume. But "no learned model" does not imply "no order."

**The ordering signal this system has and a database does not: exam
proximity.** `_academic_deadlines(repo)` already computes sittings,
registration windows and their dates, and `reading-room.md` already renders
them. A goal about an enrolled module with a sitting in nineteen days is not
comparable to a goal about a shelved module.

*Implementation:* a pure `rank_clusters(clusters, *, today, deadlines,
module_status) -> tuple[RankedCluster, ...]` with a **hand-written, readable**
ordering — no weights to tune, no learning:

1. blocks a sitting inside 30 days, module enrolled
2. blocks a sitting inside 90 days, module enrolled
3. active module, no dated pressure
4. everything else
5. shelved / dropped / archived modules — last, always

Ties break on cluster size. **~70 lines.** It is a sort, not a cost model, and
it is the thing that makes the queue an answer instead of a backlog.

**1a + 1b + 1c together: ~180 lines.** After them, `intelligence-scan` prints
something like *"4 worth your attention before 09-30"* instead of 296 lines,
and the GDA lifecycle finally has a Select step.

---

## Finding 2 — the highest-value dossier is per-session, not per-route

**Source: Bazel hermeticity and content-addressed caching (dossier §6),
crossed with PHILOSOPHY §3.5.**

Bazel's payoff is *not recomputing what has not changed*. Phase 5 shipped that
faithfully: `context://<unit-id>/semantic-dossier@<digest16>`, one hash per
dependency, invalidating exactly like a rebuild.

But the expensive recomputation in this system is not an agent re-deriving a
route. It is **Aram re-deriving where he was.** That is §3.5, named in the
philosophy as "a major burden," and it is the ADHD-specific cost the whole
repository exists to absorb.

What exists today: a `resume` pointer with five fields — `module_id`,
`unit_id`, `study_map_id`, `stage_id`, `updated`. That is a bookmark. It tells
you the address; it does not restore the context.

### Derivation: `los resume`

Same dependency-hashing machinery as `dossiers.py`, different subject. One
screen, compiled and cached, answering what a returning operator actually
needs:

```
$ los resume
M2 · SaD L08 · stage-sad-l08-clt          (last touched 2026-09-09, 2 days ago)

  Requirement  distinguish original-variable-normality from
               asymptotic-normality-of-sample-mean
               under: unfamiliar-example, no-explicit-clt-cue
  Evidence     correctly-classify, explain-reason  — none recorded yet

  Open here    Dekking §4.2 (transform-sum edge unresolved)
               Leuphana pp. 11-16 — collides with L09q2, unre-extracted
  Last result  none

  Next         los observe req-m2-sad-l08-sad-l08-clt --activity ...
  Exam         M2 2. Termin — 2026-10-09 (28 days)
```

Every line already exists somewhere: the stage from the resume pointer, the
requirement from `collect_requirements`, the open items from
`deferred-items-2026-09-08.md`, the result from `observations.jsonl` (empty
today — Finding 0 fills it), the exam from `_academic_deadlines`.

*Implementation:* `tools/learning_os/genout/resume_dossier.py`, a pure builder
over those five readers, cached under the existing dossier cache with the
existing hash-key discipline. `tools/learning_os/commands/` gets a read-only
`cmd_resume`. **~130 lines plus tests.** No new canonical entity, no new write
path, no schema change.

**This is the single feature in this document with the clearest return for how
you actually work.** It converts a five-field bookmark into the "you already
studied this, here is the path, here were the sources, here is what you were
trying to answer" that PHILOSOPHY §3.5 asks for by name.

---

## Finding 3 — the TMS is pointed at the cheap half

**Source: Doyle, truth maintenance (dossier §8).**

Phase 10 shipped forward-only assumption tracking, a `withdrawn` status, and
refusal of blank/self assumptions. Correct, and correctly scoped away from
canonical knowledge.

But it tracks **route claims** — whether a route is adequately evidenced.
Those are cheap to recompute: re-read the map, re-check the locator.

The belief whose retraction actually matters is on the learning side:

> *2026-09-12 — CLT: correctly-classify satisfied.*
> *2026-09-20 — the L08 study map's CLT stage changed.*
> **Is the 09-12 evidence still evidence?**

That is the exact shape Doyle's TMS was built for — a belief held under
assumptions that later moved — and it is a question a learner genuinely cannot
answer from memory three weeks before an exam. Right now nothing asks it,
because `requirement_sha256` is recorded on each observation (good — the
fingerprint is already there) and nothing ever compares it to the current
requirement.

### Derivation: observation staleness

A pure `stale_observations(repo, observations) -> tuple[StaleEvidence, ...]`:
recompute `requirement_fingerprint` for each requirement, compare to the
`requirement_sha256` stored on each observation, emit a mismatch.

Feed the result into `scan.py` as one more detector, `evidence-superseded`,
and into `los resume` as a line: *"2 earlier results were against a
requirement that has since changed."*

**~55 lines.** The fingerprint is already recorded on every observation; this
compares it. It becomes live the moment Finding 0 makes observations cheap
enough to exist.

---

## Finding 4 — 23 predicates with no query surface

**Source: Snowflake Semantic Views (dossier §1).**

A semantic layer exists to be **queried**. Snowflake's whole argument is that
applications stop independently reinterpreting the physical model *because
they can ask*.

`PREDICATES` holds 23 entries. `grep semantics tools/los.py` returns nothing
but `intelligence-scan`. The predicates are reachable only from Python, from
the test suite, and from `evaluate_operator_questions.py`. `policy.py` — the
Phase 1.5 "policy-query envelope" — has **no CLI surface at all**.

So the semantic layer, whose stated purpose is to stop agents re-deriving
meaning from scattered YAML, cannot currently be consulted by an agent.

### Derivation

```
los semantic <PredicateName> --input k=v ...      # evaluate one, JSON out
los semantic --list                               # the registry, with inputs and authority
```

`PREDICATES` already carries each predicate's input names, authority reference
and prose. The command is a thin dispatcher over `evaluate()`.

**~70 lines.** It is the cheapest item here and the one that makes the other
23 predicates worth their existing cost. Put it in `OPERATOR.md` so agents
find it.

---

## Finding 5 — run the conformance suite once

**Source: Snowflake Cortex Analyst evaluations (dossier §2).**

The held-out-split idea is, in my view, the best single idea in the dossier
and the one nobody else in this space has. It turns "is this model good at
LearningOS?" into a number, which is more useful for your actual operating
decisions than any public benchmark.

The harness is genuinely well built. I read it. Format 2 fixed a real leak
(format 1 published the reference procedure inside the model package, reducing
the task to following a supplied recipe). Non-leakage is pinned by test — the
serialized package provably contains no `procedure`, `expected` or `accepted`
token. A malformed submission refuses the **whole batch** rather than
partial-scoring. `unadjudicated` is a distinct verdict from pass and fail, so
a novel-but-valid procedure is not scored as wrong. `fixture-rot` separates
fixture debt from model signal. And the docstring states outright that counts
are bookkeeping, not competence labels.

**Twenty fixtures. One careful harness. Zero recorded trials.** No report file
exists anywhere in the tree.

*Implementation: none.* `prepare`, run the five held-out against Astra and
Claude, `score`, commit the report under
`work/active/.../outputs/`. Two hours, no code. Until one trial exists,
Phase 1's entire conformance premise is unfalsifiable.

---

## What not to build, and why

These are re-confirmations of the existing deferrals plus two additions. Each
carries the reason, in the style of the deferred-phases record.

**Blackboard scheduler (dossier §11).** Stays shelved. It is a solution to
*which of many contending knowledge sources should act next*. You have a
pipeline with four fixed roles and a config file. Correct as deferred.

**Fine-grained MVCC (§16).** Stays shelved, and I would go further: the
`_operator_lock` plus manifest-snapshot guard **is** the right concurrency
control for a single writer. Read-set/write-set validation buys nothing
without concurrent writers and costs a schema.

**Rego / OPA (§12).** Do not import. You already have decision/enforcement
separation (validator + capability contracts + predicates). Rego would add a
language and a runtime to express rules you already express in tested Python
that the same test suite covers.

**Learned cost model / telemetry (§5).** Stays deleted. The amendment was
right. At this volume a learned router would be fitting noise. Finding 1c's
static exam-proximity ordering is the replacement, and it needs no data.

**TLA+ (§17).** Do not build the model. But take the cheap 90%: `TRANSITIONS`
in `goals.py` is already a data table over 13 states. An exhaustive walk
asserting *no path reaches `authorized` without passing `proposed`*, *terminal
states have no exits*, and *every non-terminal state can reach a terminal one*
is **~40 lines of plain pytest**, no dependency, no model checker. That is the
protocol property worth pinning; the rest of TLA+ is not earned here.

**A fifth canonical family.** Nothing in this document adds one. Every
finding above is derived, cached, or an append-only ledger outside the four.

---

## Order of work

Sequenced against your actual calendar, not by architectural tidiness.

**Before 2026-09-30 (hours, not days):**

| | Item | Size | Buys |
|---|---|---|---|
| 0 | Asymmetric admission + `los observe` | ~110 | the runtime gets inputs |
| 2 | `los resume` session dossier | ~130 | §3.5 context reconstruction |
| 1a | Feed `known_ids` from a goal ledger | ~50 | rejected goals stay rejected |

**Between the sittings, if there is slack — otherwise after 2026-10-09:**

| | Item | Size | Buys |
|---|---|---|---|
| 1b | Cluster the goal queue | ~60 | 296 → ~20 |
| 1c | Rank by exam proximity | ~70 | the missing GDA Select step |
| 4 | `los semantic` query surface | ~70 | 23 predicates become reachable |
| 5 | Run the VOQ suite once | 0 code | the number nobody else has |

**After 2026-10-09:**

| | Item | Size | Buys |
|---|---|---|---|
| 3 | Observation staleness (TMS, learning side) | ~55 | Doyle applied where it pays |
| — | Lifecycle property walk | ~40 | the earned 90% of TLA+ |

Total: **under 600 lines** across nine independently shippable slices, no new
canonical family, no schema migration, no gateway weakening, every one
revertible at its own boundary.

---

## The one-sentence version

The first pass imported the *structures* of seventeen systems and shipped
fourteen of them faithfully; this pass says that for a single-author,
exam-driven, ADHD-targeted learning repository, four of those structures are
pointed at the cheap half of their problem, one has its trust asymmetry
backwards, and the total repair is about six hundred lines — after which the
Intelligence Plane would be doing the thing it was designed to do rather than
demonstrating that it could.

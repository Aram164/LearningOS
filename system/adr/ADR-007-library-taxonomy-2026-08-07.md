# ADR-007 — Library taxonomy: grouping learning material by subject, not by era

**Status:** ACCEPTED 2026-08-07 — Aram approved the eight-group set as proposed,
including Optimization & Learning Theory as its own group, ML Systems separate
from Machine Learning, and Software & Languages kept as one group with five
subgroups. Migration step 1 applied the same day; steps 2–6 pending.

**Context:** Aram, 2026-08-07: *"a cornerstone of our system was that learning
material is an independent object. How it's used is then documented in the
limited scope of its usage. Now I have a sea of learning materials yet they are
super scattered — be it former semester, current one, or just accumulated
stuff… all this must be saved in a logical and well-grouped manner which is not
dependent on when it was registered. Then creating my view of these learning
materials for the various modules/stages is the remaining task when needed."*

---

## What the inventory actually shows

228 registered sources, 16 shelves, 5 thematic groups, 1,141 physical files of
which 263 are unregistered. Three findings drove this ADR.

**1. The logical layer is already the right shape.** Thematic groups exist,
shelves carry `thematic_group_ids`, `sources.schema.json` already permits
`thematic_group_ids` on a source, and 21 sources sit on more than one shelf —
so multi-membership ("A and B") is supported and in use today. Module and stage
resources already *project over* sources rather than owning them. **This ADR
changes no schema and needs no data-contract bump.** It is a re-homing.

**2. Three storage axes name time, not subject.**

| location | what it actually means |
|---|---|
| `materials/Foundations/` | "from my bachelor's" — an era, not a subject |
| `materials/ML/AML/`, `materials/Math/SaD/` | *this semester's module codes* |
| `materials/Books/` | format first, subject second |
| `sources/registry/stage2-sources.yaml`, `stage2b-unsorted-intake.yaml` | the migration batch that ingested them |
| `sources/registry/external-shelf.yaml`, `external-supplements.yaml` | how they arrived |

The clearest symptom: linear algebra lives in `Foundations/Math/Lina/` while
analysis and probability live in `Math/`. Linear algebra is mathematics whether
it was learned in 2021 or 2026. Likewise `Foundations/TheoInfo/` (39 files) and
`CS-Theory/` hold the same subject, separated only by which degree they belong
to. 228 source records are filed under names describing *when they arrived*.

**3. The current 5 groups have four load-bearing gaps.** Evidence from the
distribution, not from taste:

- `programming-languages` holds four unrelated things: Python craft (Fluent
  Python, Hettinger, Beazley), CPython internals (Guo, Byterun, MRO), software
  engineering practice (Architecture Patterns, Robust Python, pytest,
  Hypothesis), and PL theory (TAPL, Software Foundations/Coq, Cornell CS 6120
  compilers). SWE, which Aram named explicitly, has no home.
- Optimization is scattered across 7+ substantial sources (Boyd & Vandenberghe,
  Nocedal & Wright, Bertsimas & Tsitsiklis, Korte & Vygen, Williamson & Shmoys,
  Schrijver, Toussaint's full TU script) each triple-tagged
  `mathematics + cs-theory + machine-learning` — the signature of a missing group.
- ML systems exists only as the dual tag `machine-learning + data-systems`,
  despite being an entire module (AMLS), the thesis subject, and the job domain.
- Method and administrative material (PRISMA, StuPO 2015, dataset catalogues)
  has no subject home at all.

---

## Decision — seven subject groups, era-independent

Each group is chosen to stay true for a decade, not a semester. Subgroups do the
fine-grained work; a source may belong to several groups, and the cross-cutting
cases are named rather than forced.

### 1. Mathematics (~62 sources)
Probability & statistics · Analysis & calculus · Linear algebra · Discrete &
combinatorics · Proof craft
*Absorbs `Foundations/Math/*` including Lina and Vorkurs.*

### 2. Optimization & Learning Theory (~14)
Convex & numerical optimization · Combinatorial & approximation · Statistical
learning theory · Kernel methods
*The bridge that is currently triple-tagged. Made explicit so Boyd, Nocedal,
Mohri and Shalev-Shwartz stop being filed three times over.*

### 3. Machine Learning (~50)
Statistical & classical ML · Deep learning · Reinforcement learning · Computer
vision · Explainers & intuition

### 4. ML Systems (~16)
Training & serving at scale · ML compilation · Performance & parallelism ·
Data management for ML
*AMLS, the thesis, and the BIFOLD/DEEM job all live here.*

### 5. Data Systems (~13)
Databases · Distributed systems · Provenance & lineage · Reliability &
benchmarking

### 6. Algorithms & Computation (~20)
Algorithms & data structures · Complexity & computability · Parameterized &
approximation · Experimental algorithmics
*Absorbs `Foundations/TheoInfo/` (39 files) — same subject, different degree.*

### 7. Software & Languages (~30)
Python craft & idiom · CPython internals · Software engineering practice ·
Languages & compilers (incl. Rust, TAPL, Coq) · Tooling & environment
*Splits the current `programming-languages` bucket along the seam the material
already has.*

### Plus one non-subject group
**8. Method & Administration (~6)** — research method (PRISMA), degree
regulations (StuPO), dataset catalogues. Small, but everything needs a home or
it silently becomes invisible.

### Cross-cutting cases, named explicitly
These stay multi-membered on purpose — the "A and B" Aram asked for:

| source | groups |
|---|---|
| Mathematics for Machine Learning | Mathematics + Machine Learning |
| Mitzenmacher & Upfal — Probability and Computing | Mathematics + Algorithms |
| Programming Massively Parallel Processors | ML Systems + Software & Languages |
| Designing Data-Intensive Applications | Data Systems + Software & Languages |
| MIT 6.172 — Performance Engineering | ML Systems + Algorithms |
| Cornell CS 6120 — Advanced Compilers | Software & Languages + Algorithms |

---

## Physical tree follows the same taxonomy

`materials/` is tracked by **no** Git repository, so re-homing costs nothing in
history — this is unrelated to the `knowledge/attachments/` question (265 MB of
handwritten scans committed into git), which remains open and separate.

```
materials/
  mathematics/          analysis/ probability-statistics/ linear-algebra/ proof-craft/
  optimization/         convex/ combinatorial/ learning-theory/
  machine-learning/     classical/ deep-learning/ vision/ rl/ explainers/
  ml-systems/           scale/ compilation/ performance/ data-for-ml/
  data-systems/         databases/ distributed/ provenance/ reliability/
  algorithms/           structures/ complexity/ approximation/
  software/             python/ internals/ engineering/ languages/ tooling/
  method-admin/
  _unsorted/            (existing intake queue, unchanged)
```

Dissolved: `Foundations/` (era), `Books/` (format), `ML/AML` and `Math/SaD`
(module codes), `Degree/` (→ `method-admin/`), `CS-Theory/` (→ `algorithms/`).
Book vs course vs video is already carried by the source `type` field and does
not need to be a directory level.

`materials/.flat/` continues to resolve every `material://source-<id>/…` URI, so
**no reference breaks** regardless of where a file physically sits — that
indirection is exactly what makes this move safe. The 109 references that
currently name physical paths directly (`MATERIAL-URI-FORM`) must be converted
to the id form *before* the move, or they will break.

Registry partitions are renamed to match: `sources/registry/mathematics.yaml`,
`optimization.yaml`, `machine-learning.yaml`, `ml-systems.yaml`,
`data-systems.yaml`, `algorithms.yaml`, `software.yaml`, `method-admin.yaml`.
Source **ids do not change** — only which file holds the record.

---

## Consequences

**Good.** Grouping survives semesters, degrees and jobs. A source is findable by
what it *is*, not by when it arrived. Module and stage views become pure
projections, which is what the architecture always claimed. The raw folder is
navigable with no tooling, honouring the human-fallback principle.

**Costs.** ~1,141 files move; the manifest built on 2026-08-07 verifies the move
is lossless. 228 source records change file, not identity. The 109 physical-form
URIs must be converted first. Generated views and the domain atlas rebuild.

**Risks.** A file moved but not re-linked becomes invisible — mitigated by
`make check` (`MATERIAL-MISSING` is an error) and by verifying the manifest
before and after. Multi-membership can become a dumping habit; the rule is that
a second group must be *justified in the shelf entry's `why`*, as today.

**Not changing:** no schema edits, no data-contract bump, source ids, note
bodies, `Job/` quarantine, or the concept layer.

---

## Migration order (each step independently reversible)

1. Convert the 109 physical-form `material://` URIs to id form; `MATERIAL-URI-FORM` clears.
2. Extend `curriculum/thematic-groups.yaml` to the 8 groups; keep old ids as aliases.
3. Re-tag the 228 sources and 16 shelves; bulk-shelve the 263 unregistered files at folder level.
4. Re-partition `sources/registry/*.yaml` by subject.
5. Physically move `materials/`, rebuild `.flat/`, rebuild the manifest, verify against the pre-move manifest.
6. Rebuild views; `make check` must print 0 errors.

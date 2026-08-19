# Critical review — Learning OS v3, 2026-08-19

- **Status:** review (not an ADR; no decision is adopted here)
- **Requested register:** adversarial — the strongest case *against* the system as built
- **Scope:** architecture & contracts, code & implementation
- **Entry point:** ADR-012 (agent-UI contract consolidation), same day

## 0. Method and what could not be checked

Read-only inspection of `repository/` via file reads and grep. The Linux
sandbox would not provision, so **nothing was executed**: no `tools/validate.py`,
no `pytest`, no `tools/manifest_contract.py`, no `npm run contract:check`. The
`obsidian-ui` repository is not mounted, so every claim about the UI mirror is
inferred from Core-side evidence only.

Where a finding depends on runtime behaviour it is marked *(unverified — needs a
run)*. Everything else cites a file and line.

---

## 1. Verdict

The architecture is unusually well-reasoned and the prose is better than most
professional codebases. That is the problem this review is about.

Three claims, in descending confidence:

1. **ADR-012 does not do what it says.** Its thesis is "one executable boundary
   per architectural rule." Of its eight decisions, at least three are satisfied
   by *file placement* rather than by an executable boundary, and one of them
   reintroduces the exact drift topology the repository already diagnosed and
   fixed once (§3, C1–C4).
2. **The write path is architecturally expensive in a way that compounds.** A
   single canonical write costs roughly four full repository loads, two full
   validations, three whole-content SHA-256 walks, and a complete regeneration
   of every generated view (§4, I1). The system is explicitly designed to
   outlive the degree (PHILOSOPHY principle 12); this cost scales with the
   corpus.
3. **The knowledge layer the machinery protects is almost entirely
   machine-produced.** 3 of 99 notes carry `authorship: user`. `evidence` is
   attached to 0 of 99. `reviewed` is set on 0 of 99 (§5). The invariants that
   protect user meaning are guarding a corpus that does not yet contain much of
   it.

The uncomfortable synthesis: effort has been flowing into the contract layer
because the contract layer is the part that gives clean, satisfying feedback.
Twelve ADRs in 34 days (2026-07-16 → 2026-08-19), of which ADR-006 onward —
seven ADRs in the last sixteen days — are about interfaces, gateways,
transactions, projections, and contract locks. None are about learning.

---

## 2. Where this review agrees with the system

Stated up front so the criticism is not mistaken for a rejection.

- The ownership table (ARCHITECTURE §4) and the "one canonical fact, one owner"
  invariant are correct and rare. Most personal knowledge systems fail here.
- `fingerprint.py`'s docstring is a model of *why*-documentation: it names the
  two implementations that used to exist, the failure they could produce, and
  why the fix lives where it does.
- The refusal to score mastery (ARCHITECTURE §12) is the right call and is
  argued honestly.
- `test_project_capability_envelope_round_trips`
  (`tests/test_capability_catalog.py:78`) and
  `test_a_versioned_query_cannot_skip_its_schema` (:46) are real behavioural
  tests through the real CLI. There are good tests here.
- Rollback that reports unrestored paths rather than claiming success
  (`transactions.py:280-300`) is genuinely honest engineering.

---

## 3. Findings — contracts and architecture

### C1 · The "one public capability catalogue" contains four incompatible record shapes, and only two are executable · **High**

ADR-012 decision 1: "`system/contracts/capabilities.yaml` is the only public
command/query registry."

The file has five command- or query-bearing sections:

| Section | Shape | Loaded by |
|---|---|---|
| `queries` | handler / result / schema | `capability_catalog.py:45` — validated |
| `commands` | handler / cli_command / writes | `capability_catalog.py:45` — validated |
| `internal_commands` | handler / writes | `capability_catalog.py:45` — validated |
| `domain_capabilities` (:269) | writes / invariants, **no handler** | `ai_actions/service.py:49` — a *second, independent* reader with no validation |
| `ai_action_interface` (:285) | bare name strings | **nothing in production** |

`load_capability_catalog` iterates exactly `("queries", "commands",
"internal_commands")`. `domain_capabilities` is never validated by the
catalogue loader — it is re-parsed by `AIActionService.capability_writes()`
with its own `_read_yaml` and its own shape assumptions. So the file that exists
to end parallel representations is itself read by two loaders that disagree
about what it contains.

Worse, `ai_action_interface.queries` and `.commands` name six capabilities —
`ai_action.list`, `ai_action.status`, `ai_action.prepare`,
`ai_action.import_delivery`, `ai_action.validate_delivery`,
`ai_action.apply_delivery`. Grepping the whole repository for those strings
returns **one** file: `capabilities.yaml` itself. They are not handlers, not CLI
commands, not dispatchable, not tested. They are prose wearing YAML, sitting
inside the file ADR-012 designates as the executable catalogue.

Structural corroboration: `contract_version: 1` is at line 1, while
`schema_version: 1` and `contract: learningos-capabilities` are at lines 267–268,
*after* the `forbidden` list. A file whose own header keys are scattered across
it is a file that has been appended to by several hands without one owner.

### C2 · ADR-012 delegates the Job-schema drift gate to the consumer's CI — the failure mode the repository already fixed once · **High**

`tools/manifest_contract.py:14-21` states the lesson in the repository's own
words:

> "Until 2026-08-08 only the consumer declared the projection version... Core
> could reshape the manifest, pass its own CI, and push; the incompatibility
> surfaced in the other repository."

The fix was to move enforcement *into the producer*: `build_manifest` refuses to
publish a drifted shape, so Core's own test run fails.

ADR-012's Consequences then say, for the Job dashboard schema: "`npm run
contract:check` compares the Job schema mirror byte-for-meaning." `npm` means
the UI repository. `.github/workflows/validate.yml` runs `python
tools/validate.py` and `pytest` — and **nothing else**. There is no producer-side
gate that fails when the Core Job schema and the UI mirror diverge.

So the Job dashboard contract sits in exactly the topology the manifest contract
was rescued from: Core can change the schema, pass its own CI, and push; the
incompatibility surfaces in the other repository. ADR-012 states "Core and UI
contract changes must land together" as a consequence, but a consequence
enforced only in the consumer's repo is a convention, not a boundary.

*(Unverified: the UI repo is not mounted; if `contract:check` also runs in Core's
CI through some path not in `validate.yml`, this finding weakens.)*

### C3 · ARCHITECTURE.md invariant 24 has said `job-dashboard-v1` since ADR-010 shipped v2 · **Medium**

Grep for the contract name:

- `commands/job.py:24` — `CONTRACT = "job-dashboard-v2"`
- `capabilities.yaml:6`, `schema/job-dashboard.schema.json:3,10`,
  `ADR-010:33`, `ADR-012:34`, both tests — **v2**
- `ARCHITECTURE.md:618` (invariant 24) — **v1**
- `ACCEPTANCE-TESTS.md:164` — **v1**

ADR-010 (2026-08-14) introduced v2. The top-level invariant list and the
acceptance tests have been wrong for five days, and ADR-012 — whose entire
subject is consolidating contract representations — shipped on 2026-08-19
without correcting either.

This is small in itself and large as evidence: the invariant list is the
document CLAUDE.md hard-rule bootstrap points an operator at, and no mechanism
exists to keep it true. `CANONICAL_ROOTS` (`fingerprint.py:25-34`) covers
`system/schema` and `system/contracts` but not `system/*.md` — deliberate, since
prose should not move the snapshot, but it also means the prose has no gate at
all.

### C4 · The scope check has a blanket bypass that swallows one of the three capabilities it governs · **Medium**

`ai_actions/service.py:57-73` implements the "post-action scope check" that
CLAUDE.md hard rule 12 requires. Line 62:

```python
if rel.startswith("operations/ai-actions/"):
    return
```

Any capability may write anywhere under that prefix without declaring it. The
comment justifies this ("gateway bookkeeping is exchange state"). But
`capabilities.yaml:276-281` declares:

```yaml
garden.update:
  writes:
  - operations/ai-actions/garden-state/
```

`garden.update`'s entire declared write scope is inside the blanket exemption.
Its scope check is a no-op that reads like a control. Two of the three
`domain_capabilities` are meaningfully scoped; one is theatre.

### C5 · The capability envelope schema cannot tell a request from a response · **Low**

`schema/capability-envelope.schema.json` is a `oneOf` over `request` and
`result`, and `capability.py` validates *both directions* against it
(:101 for the request, :131 for the response). A caller can post a
`result`-shaped object as a request; it validates, `payload` defaults to `{}` at
:105, and the capability is dispatched with an empty payload. The payload schema
will usually reject it — but the envelope gate, which exists precisely to catch
malformed traffic, does not.

### C6 · Generated-output inventory has drifted from the architecture · **Low**

ARCHITECTURE §2.5 and §3.2 enumerate the generated artifacts. Actual
`generated/` also contains `library.md`, `concept-map.md`,
`dependency-report.md`, `nebula.md`, and `collections/` (15 files). Some are
covered elsewhere (nebula in CLAUDE.md §14, atlas/reading-room/canvas in §2.5);
`library.md`, `concept-map.md`, `dependency-report.md`, and `collections/` are
not enumerated anywhere in ARCHITECTURE. Low severity, same disease as C3.

---

## 4. Findings — implementation

### I1 · A single canonical write costs four repository loads, two validations, three content digests, and a full regeneration · **High**

Tracing one `los note-revise`-class write:

| Step | Cost | Evidence |
|---|---|---|
| `_expected_ok` | `load_repo` + full-content SHA walk | `support.py:75` |
| `_write_transaction` baseline | `load_repo` + full `validate` | `support.py:186` |
| `commit` → `snapshot_before` | full-content SHA walk | `transactions.py:278` |
| `validate_state` | `load_repo` + full `validate` | `support.py:194` |
| `publish` | `load_repo` + `generate_all` + write ~30 files | `support.py:84-86` |
| `commit` → `snapshot_after` | full-content SHA walk | `transactions.py:319` |

`canonical_fingerprint` (`fingerprint.py:37-60`) reads **every byte of every
file** under eight canonical roots, including `work/`, which holds workspace
`inputs/` and `outputs/`. `source_fingerprint` memoises per-`Repo`, but
`transactions.py` calls the path-taking form twice, so neither walk benefits.

For an interactive UI where every stage-progress tick and note append goes
through this path, that is a wall the system will hit — and it degrades
monotonically with exactly the growth the philosophy plans for. *(Unverified:
no timings taken. The structural claim stands regardless of the current
constant.)*

### I2 · The transaction does not validate the resulting repository; it diffs error strings · **High**

Gate B (ARCHITECTURE) and the `TransactionService` docstring both say the service
"validates the resulting repository." `support.py:185-196` actually does:

```python
baseline_errors = {str(issue) for issue in validate(...) if issue.severity == "E"}
...
return [issue for issue in validate(...)
        if issue.severity == "E" and str(issue) not in baseline_errors]
```

Two consequences:

1. **The transaction knowingly commits into an invalid repository** as long as it
   introduces no *new* error strings. CLAUDE.md hard rule 9 says work is not done
   until the validator prints 0 errors; the write path does not enforce that.
2. **Comparison is on the rendered string.** An error the write genuinely causes,
   whose `str(issue)` collides with a pre-existing error elsewhere, is silently
   filtered out. Deduplicating by formatted message rather than by
   `(code, path, id)` makes the filter lossy in exactly the case it matters.

### I3 · The machine gateway parses the human CLI's stdout, and can report success with no receipt · **High**

`capability.py:38-81` dispatches by building the argparse parser, calling the
CLI handler under `contextlib.redirect_stdout`, and `json.loads`-ing whatever
was printed. Lines 75-80:

```python
try:
    result = json.loads(text) if text else {}
except json.JSONDecodeError:
    result = {"output": text}
```

Then :121-129 builds the response with `ok = (code == 0)` and
`transaction_id = confirmation.get("transaction_id")`.

So if any handler prints a warning, a deprecation line, or prose because it
lacks a `--json` flag (selected duck-typed at :65 via `hasattr(namespace,
"json")`), the gateway returns **`ok: true`, `transaction_id: null`,
`receipt_path: null`** — and the response validates, because both fields are
nullable in the envelope schema. A committed canonical write, reported as
successful, with no link into the receipt chain. Given that
`capabilities.yaml:259-266` forbids deleting receipts precisely to keep that
chain complete, the chain's completeness resting on every handler's print
formatting is the wrong dependency direction.

The comment at :41-43 defends this as avoiding a second implementation. The cost
is that the human surface became the machine contract's implementation, and
in-process global stdout redirection became the IPC. A shared function returning
a typed result, called by both the CLI printer and the gateway, gets the same
no-divergence guarantee without the serialization round-trip. The lazy `import
los` at :47 ("the cycle must stay lazy") is the acknowledged cost of the current
shape.

### I4 · Invariant 26 is enforced by a three-element hardcoded filename list · **Medium**

ARCHITECTURE invariant 26: "A learning-session commit stages only its action
ledger. Unrelated files, including untracked Canvas files, are never absorbed."

`support.py:162`:

```python
if rel not in {"Untitled.canvas", "Untitled 1.canvas", "Untitled 2.canvas"}:
```

`Untitled 3.canvas` defeats it. An invariant stated as a general principle and
implemented as a literal denylist of three strings will be false the first time
Obsidian produces a fourth.

### I5 · No package metadata; 15 files mutate `sys.path` · **Medium**

There is no `pyproject.toml` or `setup.py` — only `requirements-dev.txt`. Every
entry point does `sys.path.insert` (15 files, including
`tools/validate.py:19`, `tools/manifest_contract.py:40`, `tests/conftest.py`,
and `rules/contract.py:26-33`, which inserts a path *inside a function* to
import a sibling "without a package dependency"). For 108 modules with a
declared cross-repository contract, that is under-engineered relative to
everything around it — and it is why an internal module has to path-hack to
reach `tools/schema_contract.py`.

Also: CI pins Python 3.12 (`validate.yml:22`); the local `.venv` is 3.14. The
suite runs on a version the developer never uses.

### I6 · `source_fingerprint` mutates the object it documents as immutable · **Low**

`fingerprint.py:63-73` — docstring says "one immutable loaded repository", then
`repo._source_fingerprint_cache = result` inside a bare
`except (AttributeError, TypeError): pass`. If a `Repo` ever outlives a write,
the cache is silently stale, and the swallowed exception guarantees no signal.
Currently safe because `publish` reloads; fragile by construction.

### I7 · Durability is not what "transaction" implies · **Low**

`_atomic_write_bytes` (`transactions.py:138-151`) uses temp-file + `os.replace`.
That gives atomic *visibility*, not durability — there is no `fsync` on the file
or the parent directory. A crash between replace and writeback can leave a
receipt present with unwritten content.

Related and worth confirming: the repository lives under
`~/Desktop/semestercontext/`. If macOS "Desktop & Documents in iCloud" is
enabled, both `os.replace` atomicity and `fcntl.flock`
(`support.py:30-39`) have weaker guarantees than the design assumes, and the
whole write path rests on those two primitives. *(Unverified — check whether
iCloud Drive syncs Desktop on this machine.)*

### I8 · Two of the ADR-012 tests assert on strings, not behaviour · **Medium**

`tests/test_capability_catalog.py:18-23`:

```python
gateway = (repo_root / "tools/learning_os/commands/capability.py").read_text(...)
assert "_capability_handlers" not in gateway
```

This is a grep against one identifier. Rename the second registry to `_handlers`,
or move it one module over, and the test passes while the property it names is
false. It tests a string, not the absence of a duplicate registry.

`:33-43` asserts a YAML dict equals a hardcoded literal — for
`ai_action_interface`, the section §3/C1 shows no production code reads. That is
a change-detector over documentation, counted as coverage.

The effect is that the two ADR-012 claims hardest to verify are the two backed
by the weakest tests, and the suite is green either way.

---

## 5. The finding that reframes the other two

From `generated/reports/health.md` (generated 2026-08-19T01:33) and a grep over
note frontmatter:

| Measure | Value |
|---|---|
| Notes | 99 |
| — role `synthesis` | **4** |
| — role `exercise-bank` + `mock-exam` | 53 |
| — role `reference` | 37 |
| `authorship: user` | **3** |
| `authorship: mixed` or `operator-drafted` | ~96 |
| Notes with `evidence` entries | **0 / 99** |
| Notes with a `reviewed` date | **0 / 99** |
| Notes carrying "Not yet worked by Aram" | 12 |
| Sources registered | 242 |
| — referenced by ≥1 note | 84 |
| — invisible (no concept, no shelf, no note) | 50 |
| Concepts / relations | 108 / 99 |

Read against the founding documents:

- PHILOSOPHY principle 2 is "preserve user-authored meaning." Three notes are
  user-authored — the three handwritten SAD transcriptions.
- ARCHITECTURE §5.1 defines a note as "an evolving synthesis artifact." Four
  notes carry `role: synthesis`.
- ARCHITECTURE §12 makes evidence the honest answer to metacognitive
  uncertainty — PHILOSOPHY §3.6, the user's own hardest problem. CLAUDE.md hard
  rule 7 forbids declaring mastery and requires showing evidence trails "or their
  documented absence." **The absence is total.** Asked "have I actually worked
  through this?", the system's honest answer today is "no evidence exists for any
  note."
- PHILOSOPHY §3.3 is "I should not repeatedly rebuild the same reading list."
  158 of 242 registered sources have never been cited by a note; 50 are invisible
  to every retrieval path. The registry grew faster than its use.
- 108 concepts with 99 relations is a near-forest, not a graph — thin support for
  §4.1's "make those connections durable and retrievable."

`note-algo2-b-trees.md:14-15` states it plainly in the repository's own voice:

> "Operator-drafted from `ad2_btrees.pdf` (44 sl.). Companions:
> `-exercise-bank`, `-viva-drill`. **Not yet worked by Aram.**"

**The adversarial reading:** the system was built to externalize organization so
that cognitive effort could go into deriving, explaining, applying, and
connecting (PHILOSOPHY §11). What it currently does at scale is *produce study
material*. Twelve notes announce they have not been worked. The Algo-2 corpus is
33 notes generated in a burst on 2026-08-16, three per topic, with zero evidence
entries.

Generated study material is not worthless. But it is not what the invariants
protect, it is not what the transaction service exists to guard, and it is not
what "reduce organizational burden" means — a lecture converted into three notes
you have not read is organizational burden that has been *created*, cleanly
filed and schema-valid. That is the tiebreaker in CLAUDE.md hard rule 10 pointing
the other way.

The Algo-2 corpus makes the pattern legible: **all 37 notes under
`knowledge/notes/algorithms/` carry `created: "2026-08-16"`** — twelve topics ×
(reference + exercise-bank + viva-drill), plus one prerequisites note, produced
in a single day. Every one is `authorship: operator-drafted`. None has an
`evidence` entry. Twelve say so on their own front page.

And it explains the ADR cadence. Contract work has short, legible feedback loops:
write the schema, run the validator, see 0 errors. Learning does not. A system
built by someone who names scope explosion as their central difficulty
(PHILOSOPHY §3.2) has, in five weeks, produced 108 modules under `tools/`,
28 test modules, 12 ADRs, and 14 top-level system documents to serve four
synthesis notes. The failure mode the architecture was designed to prevent has
reappeared one level up — in the architecture.

---

## 6. What to do, in order

1. **Stop building.** No new ADR, no new capability, no new generated view until
   §5's numbers move. Concretely: attach `evidence` to five existing notes and
   set `reviewed` on them. If that turns out to be unpleasant enough that it does
   not happen, that is the most important finding in this document, and it is
   about the schema, not about discipline.
2. **Close C2.** Add a Core-side test that loads the Job schema and compares it
   to the UI mirror, or move the mirror into Core and have the UI import it.
   A cross-repo invariant enforced only downstream is not enforced.
3. **Fix I3.** Have handlers return a typed result object; let the CLI printer
   and the gateway both consume it. Delete the stdout round-trip. Until then, at
   minimum make a non-JSON-parseable handler output a hard failure rather than
   `ok: true`.
4. **Fix I2.** Compare validation issues by identity, not by rendered string, and
   decide explicitly whether a transaction may commit into an
   already-invalid repository. Currently it may, silently.
5. **Delete `ai_action_interface` from `capabilities.yaml`** (C1) or implement it.
   Delete the test that asserts its literal shape. Fold `domain_capabilities`
   into the validated loader or move it to its own file with its own schema.
6. **Fix C3 and C6** — one-line corrections, and then consider whether
   ARCHITECTURE §16 should be generated from the things it describes rather than
   hand-maintained.
7. **Add `pyproject.toml`** (I5) and align the CI Python version with the venv.
8. **Defer I1.** It is real and it will bite, but not before §5 is addressed —
   and if the corpus stays this size, it never bites at all.

---

## 7. The question worth answering before any of the above

> If the tooling froze exactly as it is today — no more ADRs, no more
> capabilities, no more views — would the learning get better or worse?

If the answer is "better," the system is finished and the remaining work is
using it. If the answer is "worse," the next thing built should be the specific
thing that makes it worse, and this document should be able to name it.

It currently cannot.

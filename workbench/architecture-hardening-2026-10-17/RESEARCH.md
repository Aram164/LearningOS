# Research supporting LearningOS architecture hardening

17 October 2026. Research and proposed design, not an implementation or release approval.

This research addresses the four demonstrated correctness findings and the five source-quality concerns in the [correctness review](/Users/aramaljanadi/.codex/visualizations/2026/10/17/01a14ba3-c560-7e83-946e-639b5bcc05d6/learningos-architecture-review/review.md) and [source review](/Users/aramaljanadi/.codex/visualizations/2026/10/17/01a14ba3-c560-7e83-946e-639b5bcc05d6/learningos-architecture-review/code-quality-review.md). Repository observations were checked against Core `074f4717e14527798752de84b3c9c4e88348b658` and UI `a88b1188ad54439b4df32813904de182c06a105c`.

## 1. Replace architectural seams incrementally

[Parallel Change](https://martinfowler.com/bliki/ParallelChange.html) describes expanding an interface, moving consumers, then removing the old interface. [Branch by Abstraction](https://martinfowler.com/bliki/BranchByAbstraction.html) describes introducing a temporary seam so implementations can be replaced while the system remains usable. Neither requires permanent dual implementations.

**Application here:** retain the modular monolith and TransactionService. Characterize each existing operation, introduce the narrower interface, migrate consumers, and delete the compatibility path in that slice. Compare old and new operations in separate disposable worlds; never execute a real mutation twice against the learner's repository. A temporary adapter needs a named deletion condition. This continues the direction already established by [ADR-018](/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository/system/adr/ADR-018-operations-boundary-and-enforced-architecture-2026-10-03.md), rather than launching another architectural replacement.

## 2. Separate transport decoding from application semantics

[Cockburn's ports-and-adapters account](https://alistair.cockburn.us/hexagonal-architecture) places translation into application messages at the adapter boundary. [Parnas's original modularity paper](https://www.cs.lafayette.edu/~gexia/cs301/resources/parnas.html) argues for hiding decisions that can change independently, rather than simply dividing a processing sequence into modules. The hosted Parnas text is a transcription; no exact quotation is relied upon.

**Application here:** the gateway should not build an argparse parser to invoke a registered operation. Existing request schemas already own operation metadata, and registered handlers already accept context plus a request dictionary. The replacement can therefore be a small schema-derived normalization function, not a second operation catalogue. Similarly, material ranking belongs with derivation, while exact file observations and note reads stay in an application service. Session ownership repair belongs with the existing session service, not generic dispatch.

## 3. Defaults are behavior, not merely schema annotations

[JSON Schema's annotations documentation](https://json-schema.org/understanding-json-schema/reference/annotations) states that `default` does not itself insert a missing value. [Python's argparse documentation](https://docs.python.org/3.12/library/argparse.html#default) describes its separate default and conversion behavior.

**Application here:** validate the raw gateway payload before adding internal defaults. Preserve omitted versus explicit null, false, empty lists, fresh mutable defaults, choices, revision argument spellings and content-bound file inputs. The normalized internal request can legitimately contain `None` where an optional wire field, when present, must be a string. Generating internal request types directly from wire schemas would silently conflate two contracts. There is no need to reproduce arbitrary argparse features: the currently used actions and defaults form a bounded inventory.

## 4. Types should expose meaningful alternatives

[Python TypedDict](https://docs.python.org/3.12/library/typing.html#typing.TypedDict) supports static descriptions of dictionary shapes; it does not validate values at runtime. [TypeScript discriminated unions](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#discriminated-unions) support narrowing and exhaustive handling. [Indexed access types](https://www.typescriptlang.org/docs/handbook/2/indexed-access-types.html) preserve types already present in another contract.

**Application here:** keep runtime schema validation, then type normalized requests and narrow internal commit results. Reuse the pipeline's existing final Outcome instead of inventing another top-level result system. Remove the refusal ContextVar after all its facts are carried explicitly. In the UI, collection accessors should return generated unit/stage types; heterogeneous search can keep a generic record type. Use three finite commit policies for ordinary, goal and AI-delivery behavior, retaining domain-specific preconditions and transaction-bound effects explicitly. No generic policy plugin framework is warranted.

## 5. Atomic replacement and file flushing solve different problems

[Linux fsync](https://man7.org/linux/man-pages/man2/fsync.2.html) distinguishes flushing a file from persisting its directory entry. [rename](https://man7.org/linux/man-pages/man2/rename.2.html) gives namespace replacement semantics, not a compare-and-swap on the old file's bytes. [SQLite's atomic commit explanation](https://www.sqlite.org/atomiccommit.html) shows how ordered journal, data, directory and commit-evidence persistence form one protocol.

**Application here:** introduce a small durable-filesystem module used by the existing transaction engine. Account for parent creation, unlink, rename, receipt publication and recovery, as well as replacement. A journal must be durable before destructive changes; authoritative commit evidence must be durable before success. Move settled journals into a durable settled namespace before garbage collection so interrupted cleanup does not leave an apparently active, partially deleted journal. Do not replace this work with extra `fsync` calls scattered through handlers.

## 6. macOS requires a platform-specific durability decision

[Apple's official archived fsync manual](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/fsync.2.html) distinguishes ordinary filesystem synchronization from the stronger `F_FULLFSYNC` request to flush device caches. [SQLite's sync flags](https://sqlite.org/c3ref/c_sync_dataonly.html) also distinguish platform-dependent synchronization strength.

**Application here:** verify actual host/filesystem support before choosing barriers. Use strong synchronization at proof-critical write barriers where supported; propagate synchronization errors instead of claiming success. Do not infer modern filesystem support from the archived manual's historical filesystem list. Process interruption testing alone cannot establish physical power-loss durability. The plan requires an explicit platform capability result and fault-model evidence, with any remaining hardware assumption stated.

## 7. Advisory locks do not exclude an unrelated editor

[flock's manual](https://man7.org/linux/man-pages/man2/flock.2.html) describes advisory locking: cooperating processes participate. Combining such a lock with atomic rename still does not prevent another process from writing through an existing descriptor.

**Application here:** add uncached preimage checks after journal publication and immediately before each mutation, including deletions and delayed ledger changes. Preserve foreign bytes during rollback and stop for reviewed recovery on conflict. This closes the demonstrated interval in which an already completed external edit was silently overwritten. It does not create perfect isolation from arbitrary editor writes between the final check and replacement. Full exclusion would require an additional writer-cooperation or storage-ownership product decision. The plan does not silently impose one on plain-text learning files.

## 8. Idempotency needs a policy for delayed requests

[AWS's Making retries safe with idempotent APIs](https://aws.amazon.com/builders-library/making-retries-safe-with-idempotent-APIs/) discusses caller-provided identities, intent binding, atomic recording and late-arriving requests.

**Application here:** an unresolved request cannot be made safe by clearing the UI slot. A reviewed resolution must persist a terminal fence under the same exclusive lock used by execution. That fence prevents future execution of the exact original request, even if an old process sends it later. It does not prove the request historically had no effects. Verified committed evidence settles the existing transaction instead. Source inspection adds a LearningOS-specific requirement: protect active original journals with an explicitly incompatible journal version before resolution effects, because automatic recovery precedes ledger admission. Version the ledger too, and bind its transition to the resolution receipt so historical evidence remains verifiable. Keep the original envelope, draft and exact resolution envelope durably before dispatch; a later retry of the user's desired action requires a new visible approval.

## 9. Independent evidence is stronger than one green suite

[SQLite's testing account](https://www.sqlite.org/testing.html) combines independent harnesses and fault simulation, including dropped or reordered unsynchronized writes. Its crash simulation illustrates why terminating a process is not equivalent to losing power. [pyperf's command documentation](https://pyperf.readthedocs.io/en/latest/cli.html) describes repeated measurements, instability checks and comparisons across processes.

**Application here:** retain the existing tests, but add an independently implemented filesystem-effects oracle, deterministic interleavings and controls that deliberately remove a protection to prove the harness can detect its absence. Compare public results, authored bytes, receipts, ledgers, drafts and generated semantics. Measure fresh-process reads and writes, UI interaction and the new freshness check separately. Set regression budgets before implementation and keep correctness unconditional. Benchmark methodology can be adopted without adding a new runtime dependency or turning noisy timings into a universal CI gate.

## Resulting recommendation

Use staged interface replacement, stronger persistence and conflict detection, explicit request/outcome types, finite commit policies and a reviewed recovery transition. Preserve the current transaction owner, authored formats, global validation, material provenance, derived-state engine and public command behavior. The companion [implementation plan](/Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/architecture-hardening-2026-10-17/PLAN.md) turns these conclusions into bounded changes with independent acceptance criteria.

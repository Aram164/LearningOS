# Four execution flows

These traces were checked against the code at the change's base. The map checker
checks Python symbol existence; it does not prove runtime execution or every
branch. Refusals, replay, check-only mode and recovery remain covered by their
own tests. Sequence participant labels describe responsibilities.

<!-- system-map:external Obsidian-LosRuntime.run -->

## Sealed canonical write

<!-- system-map:participant S tools/seal_envelope.py::_submit -->
<!-- system-map:participant A tools/learning_os/adapters/capability.py::cmd_capability -->
<!-- system-map:participant P tools/learning_os/app/pipeline.py::run_gateway -->
<!-- system-map:participant H component:operation-handlers -->
<!-- system-map:participant C tools/learning_os/app/commit.py::commit_proposal -->
<!-- system-map:participant T tools/learning_os/store/transactions.py::TransactionService.commit -->

<!-- system-map:symbol tools/seal_envelope.py::_submit -->
<!-- system-map:symbol tools/learning_os/adapters/capability.py::cmd_capability -->
<!-- system-map:symbol tools/learning_os/app/pipeline.py::run_gateway -->
<!-- system-map:symbol tools/learning_os/app/pipeline.py::_registered_compute -->
<!-- system-map:symbol tools/learning_os/app/commit.py::commit_proposal -->
<!-- system-map:symbol tools/learning_os/store/transactions.py::TransactionService.commit -->

```mermaid
sequenceDiagram
  participant S as seal_envelope._submit
  participant A as capability.cmd_capability
  participant P as pipeline.run_gateway
  participant H as registered handler
  participant C as commit.commit_proposal
  participant T as TransactionService.commit
  S->>S: seal exact intent and files under retry key
  S->>A: submit sealed envelope
  A->>P: envelope, definitions, attempt
  P->>P: validate, approve, lock, guard and replay-check
  P->>H: admitted request through _registered_compute
  H-->>P: bounded proposal
  P->>C: _commit_with_gesture delegates commit
  C->>T: writes, revisions, snapshot, validation/publication callbacks
  T-->>C: committed receipt or typed failure/recovery result
  C-->>P: confirmation
  P-->>A: outcome
  A-->>S: exit/result
```

Exact replay returns before recomputing the handler. Check mode validates a
shadow proposal instead of committing. A durable receipt marks the commit
boundary. Receipt-publication uncertainty preserves forward state and the
journal for reconciliation; later bookkeeping failure does not undo a commit.

## Generate disposable views

<!-- system-map:participant G tools/generate.py::main -->
<!-- system-map:participant L tools/learning_os/store/loading/__init__.py::load_repo -->
<!-- system-map:participant B tools/learning_os/derive/projection/outputs.py::generate_all -->
<!-- system-map:participant W tools/learning_os/derive/projection/outputs.py::write_outputs -->

<!-- system-map:symbol tools/generate.py::main -->
<!-- system-map:symbol tools/learning_os/store/loading/__init__.py::load_repo -->
<!-- system-map:symbol tools/learning_os/derive/projection/outputs.py::generate_all -->
<!-- system-map:symbol tools/learning_os/derive/projection/outputs.py::write_outputs -->

```mermaid
sequenceDiagram
  participant G as generate.main
  participant L as loader.load_repo
  participant B as outputs.generate_all
  participant W as outputs.write_outputs
  G->>L: load authored snapshot
  L-->>G: repository read model
  G->>B: derive outputs from repository
  B-->>G: relative output paths and content
  G->>W: publish disposable outputs
```

Generation is not an alternative canonical writer. Errors refuse publication
instead of silently omitting unreadable state.

## Offline validation

<!-- system-map:participant V tools/validate.py::main -->
<!-- system-map:participant P tools/learning_os/store/validation_cache.py::observe_pins -->
<!-- system-map:participant L tools/learning_os/store/loading/__init__.py::load_repo -->
<!-- system-map:participant C tools/learning_os/derive/validation/core.py::Validator.run -->

<!-- system-map:symbol tools/validate.py::main -->
<!-- system-map:symbol tools/learning_os/store/validation_cache.py::observe_pins -->
<!-- system-map:symbol tools/learning_os/derive/validation/core.py::Validator.run -->

```mermaid
sequenceDiagram
  participant V as validate.main
  participant P as validation_cache.observe_pins
  participant L as loader.load_repo
  participant C as Validator.run
  V->>P: observe current canonical/material/contract pins
  V->>L: load records
  V->>C: run rules over loaded state
  C-->>V: errors and visible warnings
  V->>V: print result, optional report, refresh disposable cache
```

Warning-baseline comparison is a separate gate. A validation cache is auxiliary
and cannot turn a new observation into an earlier trusted result.

## UI read through the public process boundary

<!-- system-map:participant U external:Obsidian-LosRuntime.run -->
<!-- system-map:participant L tools/los.py::main -->
<!-- system-map:participant A tools/learning_os/adapters/cli_entry.py::run -->
<!-- system-map:participant P tools/learning_os/app/pipeline.py::run_cli -->
<!-- system-map:participant H tools/learning_os/app/handlers/reads.py::bootstrap -->

<!-- system-map:symbol tools/los.py::main -->
<!-- system-map:symbol tools/learning_os/adapters/cli_entry.py::run -->
<!-- system-map:symbol tools/learning_os/app/pipeline.py::run_cli -->
<!-- system-map:symbol tools/learning_os/app/handlers/reads.py::bootstrap -->

```mermaid
sequenceDiagram
  participant U as Obsidian LosRuntime.run
  participant L as los.main
  participant A as cli_entry.run
  participant P as pipeline.run_cli
  participant H as reads.bootstrap
  U->>L: execFile interpreter, script, args, session/trace environment
  L->>A: parsed command
  A->>P: generated adapter selects operation
  P->>H: bounded request and read context
  H-->>P: read-only result
  P-->>U: rendered JSON through process output
```

The UI boundary was traced in sibling `src/infrastructure/los-runtime.ts` at
UI `f7dbc1f`. This Core-only checker does not validate TypeScript symbols.
The read shown is an example; it does not claim every UI read is bootstrap.

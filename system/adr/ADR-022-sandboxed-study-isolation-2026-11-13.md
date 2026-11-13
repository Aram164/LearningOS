# ADR-022: OS-enforced sandboxed study boundary and thin UX hooks

Date: 2026-11-13. Status: accepted. Amends
`system/adr/ADR-021-private-reading-memory-2026-11-12.md` §5 and
`system/ARCHITECTURE.md` to record Phase D (macOS Seatbelt isolation paired with
the host-side default-deny study broker) and the v1 scope decisions made at
release certification.

## Decision

1. **OS enforcement replaces harness `PreToolUse` blocking (amends ADR-021 §5).**
   `PreToolUse` AST/path parsing and `onFailure: "block"` in `study_hooks.py`
   are retired. Study sessions instead launch through `tools/study_launch.py`,
   which runs the child inside macOS `/usr/bin/sandbox-exec` (Seatbelt) and
   exposes only an unsandboxed host AF_UNIX gateway broker
   (`tools/learning_os/adapters/study_broker.py`) over `LOS_GATE_SOCK`:
   - Seatbelt uses `(allow default)` with explicit literal/subpath rules from
     `tools/learning_os/store/study_fence.py::protected_reads` denying reads to
     `LearningOS/materials/`, `LearningOS/reading-memory/`,
     `generated/text-cache/`, `generated/material-search/`,
     `generated/material-outlines/`, `generated/derived-state/`,
     `generated/summaries/`, and all children of `operations/ai-actions/requests/`
     except `.gitkeep`, while denying all writes anywhere under `LearningOS/`.
   - `generated/summaries/` is read-denied alongside the text/search caches
     because promoted chapter summaries (`tools/material_summarize.py`) can
     condense up to 80% (`MAX_SOURCE_FRACTION = 0.8`) of primary PDF page text.
   - Temporary files, `--check-out`, `--out`, and `--report-out` live in an
     ephemeral `$LOS_SCRATCH_DIR` allocated outside `LearningOS/` and removed
     after `tools/study_launch.py` records `session_end` in `finally:`.
   - Over `LOS_GATE_SOCK`, the broker pins the launcher-minted session UUID,
     `--root`, and host `LOS_OBSERVATIONS`, rewrites `material-span --extract` to
     `material-study-span`, blocks file inputs touching `protected_reads(core)`
     or writes under `LearningOS/`, executes allowed read/study-write
     subcommands in isolated `python -I` children, and keeps canonical commits
     and host validation behind explicit host approval (`tools/seal_envelope.py`).

2. **Optional UX hooks and declared perimeter.**
   `tools/study_hooks.py` provides only optional lifecycle UX hooks
   (`SessionStart`, `Stop`, `SubagentStop`, `SessionEnd`) forwarding over
   `LOS_GATE_SOCK` when sandboxed, and emits a direct notice when invoked
   without `LOS_GATE_SOCK` (unfenced mode). Its generated settings profile at
   `LearningOS/.claude` (`settings.json`, produced by
   `tools/study_hooks.py profile --out DIR`) is declared `optional: true` in
   `system/contracts/perimeter.yaml` and omitted from the root tree diagram as
   a dotfile. Gateway reading-debt enforcement (`MAX_OPEN_ENTRIES = 4`, pending/
   covered admission, `--dismiss`, and `--adopt`) is agent-independent; only
   within-turn `overdue` escalation (`STOP_ASKS = 2`) depends on the `Stop` UX
   hook.

3. **Boundary scope and runtime caches.**
   Seatbelt `(allow default)` protects LearningOS canonical data, raw materials,
   and `LearningOS/reading-memory/` integrity rather than full-host confinement.
   Host agent runtime state outside `LearningOS/` (such as `~/.claude/projects/`
   tool-result caches or agent session logs) stays writable and persists on
   the host after `$LOS_SCRATCH_DIR` is removed.

4. **V1 runtime certification, Darwin verification, and deferred items.**
   - **Supported study runtime (v1):** Release certification covers Claude Code
     (tested end-to-end with Seatbelt, the broker, and optional `.claude`
     hooks). Multi-vendor launch paths (`codex`, `gemini`) exist in
     `tools/study_launch.py` as non-certified experimental paths in v1.
   - **macOS Darwin verification:** `tests/test_study_launch.py` skips live
     `/usr/bin/sandbox-exec` probes on Linux CI (`DARWIN_SEATBELT`); running
     that suite on macOS is part of release and live-install verification.
   - **Covered-span primary text vs pointers (F1 disposition):** V1 keeps
     Option B source fidelity — covered spans on `material-study-span` return
     verified primary text by default unless `--omit-covered-text` is passed,
     compact served cards on search/context strip `pointers`, and cards never
     serve as coverage evidence. Post-v1 benchmark re-specification and
     opt-in pointer-page navigation remain follow-up work.
   - **Deferred structural cleanups:** Splitting `study_broker.py` across layers
     and extending A2 `os.open` write-flag auditing (`test_arch_writes.py`) are
     deferred post-v1 under explicit ratchet discipline.

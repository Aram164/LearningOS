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
     `tools/learning_os/store/study_fence.py` (`protected_reads` and
     `protected_read_literals`) denying reads to `LearningOS/.env`,
     `LearningOS/materials/`, `LearningOS/reading-memory/`,
     `generated/.text-cache/`, `generated/material-search/`,
     `generated/material-outlines/`, `generated/derived-state/`,
     `knowledge/summaries/`, and all children of `operations/ai-actions/requests/`
     except `.gitkeep`. **Writes are default-deny (amended 2026-11-20, D-02):**
     the profile denies `file-write*` everywhere, allows back only
     `$LOS_SCRATCH_DIR`, `/dev`, `/private/tmp`, the launched runtime's own
     study home (§3) and what that runtime must still write in the real home
     folder (amended 2026-11-20, third pass): for Claude Code, as literal
     directories only, the three locks it takes to refresh its OAuth token
     (`~/.claude/.oauth_refresh.lock`, `~/.claude/.storage-write.lock`,
     `~/.claude.lock`; without them a sandboxed Claude session failed with
     an expired token), and the login keychain; for Codex, the literal
     `~/.codex/auth.json`; for agy, its traced conversation, transcript, log
     and cache paths, the Gemini CLI's `tmp/` and `history/`, npm's logs and
     the login keychain; for the Gemini CLI, the last three; for `--cmd`,
     nothing. **Everything else in the real runtime folders stays denied,
     including the state other sessions take as input (amended 2026-11-20,
     second pass):** Claude Code's `shell-snapshots/`, `session-env/`,
     `todos/`, `tasks/` and transcripts; Codex's `models_cache.json` (every
     model's base instructions), `memories*`, `queue_*.sqlite` (messages
     waiting for other threads), `state_*.sqlite`, `cache/`,
     `shell_snapshots/`, `tmp/` (PATH helpers), `.tmp/` (plugin staging) and
     `computer-use/` (the program Codex's `notify` runs after every turn);
     npm's package cache and npx's installs; and all of
     `/private/tmp/claude-<uid>/`, which holds other Claude Code sessions'
     scratchpads and task output (a sandboxed Claude Code keeps its temp
     root in `$LOS_SCRATCH_DIR`, via `CLAUDE_CODE_TMPDIR`). Each of these
     let a study agent run code in, or put instructions into, a session
     outside the sandbox. Then it denies
     again `LearningOS/`, Claude project memory, the wrapper's `AGENTS.md`,
     `CLAUDE.md`, `CLAUDE.local.md`, `GEMINI.md`, `.mcp.json`, `.claude/`,
     `.opencode/`, `.codex/`, `.gemini/`, the read-only surfaces of the real
     runtime folders (`~/.codex/{AGENTS*.md,config.toml,rules,skills,
     plugins,prompts,automations,hooks*}`), and in a study home its
     ownership marker and Codex's `auth.json` link. The earlier denylist on top of
     `(allow default)` left every unnamed path writable: `CLAUDE.md` in any
     parent folder, agy's MCP config (which agy loads and runs inside the
     sandbox, verified), CLI binaries under `~/.local/bin` and Homebrew's
     prefix, `~/Library/LaunchAgents`, and `~/.gitconfig`.
   - `knowledge/summaries/` is read-denied alongside the text/search caches
     because promoted chapter summaries (`tools/material_summarize.py`) can
     condense up to 80% (`MAX_SOURCE_FRACTION = 0.8`) of primary PDF page text.
   - Temporary files, `--check-out`, `--out`, and `--report-out` live in
     `$LOS_SCRATCH_DIR` allocated outside `LearningOS/`, ephemeral per launch by
     default and removed after `tools/study_launch.py` records `session_end` in
     `finally:`. Opt-in `--persist-scratch` or `--scratch-dir` initializes a
     dedicated `0700` directory with `.learningos-scratch.json` bound to that
     LearningOS checkout and `--session` UUID (refusing pre-existing unrelated
     or other-session directories and write-denying the marker inside Seatbelt),
     which remains on disk until manually removed.
   - `tools/study_launch.py` filters inherited host environment variables down
     to an explicit POSIX/runtime/provider allowlist (dropping arbitrary host
     secrets and `LOS_OBSERVATIONS`) before spawning the sandboxed child.
     **By exact name only (amended 2026-11-20, fourth pass).**
     - Vendor variables pass only as provider credentials, endpoint and model
       choice: `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`, `ANTHROPIC_MODEL`
       and the like, `CLAUDE_CODE_OAUTH_TOKEN`, `OPENAI_API_KEY`,
       `CODEX_API_KEY`, the Gemini and Google keys, and agy's account
       choice.
     - Locale, XDG and CoreFoundation settings keep their prefixes.
     - The earlier vendor prefixes (`CLAUDE_`, `CODEX_`, `ANTHROPIC_`,
       `OPENAI_`, `GEMINI_`, `GOOGLE_`, `AGY_`) are gone. A launch from
       inside a Claude Code session forwarded that session's state for its
       own children into the sandbox:
       - its messaging socket and token, a channel back into an unsandboxed
         session;
       - its session, account and organization ids, and its notes folder;
       - feature flags, such as `CLAUDE_CODE_CHILD_SESSION`, which turned
         the study session's transcripts off.
     - Codex's token-URL overrides stay out as well: they redirect where the
       refresh token is sent.
     - A denylist of such names would have to keep up with every runtime's
       next release. An allowlist fails closed instead: a new provider
       variable a runtime needs is added by name, deliberately.
   - **The SSH agent is out of reach (amended 2026-11-21).**
     - `SSH_AUTH_SOCK` is no longer forwarded.
     - The profile also denies connecting to the host's agent socket and to
       every unix socket under `~/.ssh`. The agent socket is found at launch
       from `SSH_AUTH_SOCK`, and from launchd for a launch without the
       variable. The `~/.ssh` rule covers OpenSSH's default `agent/` folder
       and ControlMaster sockets.
     - The variable alone was not enough: reads are open, so a study agent
       could find the socket and sign with Aram's keys, pushing to his
       repositories or logging in to his hosts.
     - Seatbelt matches a unix socket by its resolved path, so each rule
       names the real path. A connect through a symlink, the `/tmp` alias or
       a hard link made outside the sandbox is refused too, and a hard link
       made inside it cannot be created (measured).
     - The study gate and every other unix socket stay reachable.
   <!-- los:reference {"kind": "command", "text": "los capability"} -->
   - Over `LOS_GATE_SOCK`, the broker pins the launcher-minted session UUID,
     `--root`, and host `LOS_OBSERVATIONS`, rewrites `material-span --extract` to
     `material-study-span`, blocks file inputs touching `protected_read_targets(core)`
     or writes under `LearningOS/`, executes allowed read/study-write
     subcommands in isolated `python -I` children, restricts canonical writes to
     an allowlisted study subset behind intent-bound envelopes
     (`tools/seal_envelope.py`, excluding durable note creation/revision, unit
     plan revision, concept-relation edits, review, and program mutations;
     `unit-plan-revise --check` remains read-only preflight only), and refuses
     UI or non-operator approval envelopes across both `seal_envelope` and
     `los capability`. The broker validates the *declared* approval kind
     (`approval.kind == 'operator-approval'`) and binds the request contents
     (the seal's intent hash covers capability, payload, and guards); it does
     not witness a separate human approval event. Whether study writes should
     require such an event is a product-policy decision for Aram, not a
     guarantee this boundary currently makes.

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

3. **Boundary scope, runtime caches, environment filtering, and egress.**
   Seatbelt keeps reads open outside the closed trees and makes writes
   default-deny (§1). **Per-session runtime homes (amended 2026-11-20, third
   pass).**
   - Claude Code and Codex run with a home of their own for each study
     session (`CLAUDE_CONFIG_DIR`, `CODEX_HOME`), under
     `~/.local/state/learningos/study-runtimes/<checkout>/<runtime>/<session>/`.
   - The launcher seeds a new home with a minimal config: onboarding done,
     Core trusted, Codex's file login store, and display and model
     preferences copied from the real config. Hooks, permissions, plugins,
     MCP servers and Codex's `notify` are never copied.
   - It keeps the home after the session. A resumed launch returns to it:
     `--session`, or `--resume-runtime-id` with the runtime's own session
     id, which also finds the one home whose transcript carries that id.
   - **Retention (amended 2026-11-21).**
     - A Claude Code or Codex launch removes the homes, of any checkout and
       runtime, unused for 30 days. That is Claude Code's own default
       transcript retention (`cleanupPeriodDays`), after which the
       transcripts a resume needs are gone anyway.
     - Last use is the mtime of the home's marker. The launcher refreshes it
       at every launch, and the sandbox cannot change it.
     - The home being launched or resumed is never removed: the lookup and
       the refresh run first, and pruning skips it.
     - Only directories with the launcher's marker are touched, and links
       inside them are removed, never followed.
     - The cost is one directory scan per launch.
   - Their transcripts, caches and settings therefore never reach a session
     outside the sandbox, which closes the residual accepted until then: a
     study agent could edit the transcripts unsandboxed sessions of the Core
     project read back on resume, and Codex's memory pipeline read.

   Residuals, re-scoped:
   - **The credentials the runtimes refresh stay writable.** Refresh tokens
     rotate, so each runtime must keep one login shared with unsandboxed
     sessions. A private copy that refreshed inside the sandbox would leave
     the real login holding a dead token.
     - Claude Code keeps its default keychain item and its three refresh
       locks in the real `~/.claude`: `CLAUDE_SECURESTORAGE_CONFIG_DIR=""`
       replaces the config directory for credentials only (claude 2.1.283).
     - The refresh lock's owner record stays denied (amended 2026-11-21).
       Unsandboxed Claude Code trusts it to take over a lock whose holder is
       gone. Claude Code 2.1.283 writes it best effort: `Mc` logs "owner
       record not written" and refreshes anyway. So the deny costs at most a
       wait. If a study session dies holding the refresh lock, other
       sessions wait until the lock goes stale, after 60 s (`stale: 60000`).
       The credential-store lock goes stale after 15 s.
     - Codex writes the real `~/.codex/auth.json` through the home's link.
       codex 0.153.4 saves it in place and reads it again before refreshing.
       The link can be neither removed nor replaced from inside.
     - **Version gate (amended 2026-11-21).** The launcher runs Codex only at
       versions verified to save the login in place
       (`_CODEX_IN_PLACE_AUTH_VERSIONS`, now 0.153.4, read in
       `FileAuthStorage::save`).
       - Any other version, or an unreadable one, is refused before a home or
         a session exists, and the message says what to re-verify.
       - Reason: a Codex that saved by rename could not save through the
         link. It would fetch a rotated token pair and lose it, which likely
         logs every Codex session out. ASSUMPTION: the auth server rejects a
         reused refresh token.
       - Failing closed costs one source check per Codex upgrade.
   - **Credential files stay readable.** Reads are open outside the closed
     trees, so a study agent can read, and with open egress send out, the
     private key files under `~/.ssh` and other tokens kept as files.
     Denying the agent socket (§1) stops signing through the agent, not a copy
     of a key without a passphrase. Whether to read-deny `~/.ssh` and similar
     stores is open (2026-11-21), next to the question of the keychain folder
     that Claude Code, agy and the Gemini CLI may write.
   - **agy has no home override** (no data-dir flag; its
     `ANTIGRAVITY_EXECUTABLE_DATA_DIR` only serves sidecar plugins). It keeps
     its traced path rules, now granted to agy launches only. An agy study
     agent can still edit agy's conversation and memory files, which
     unsandboxed agy sessions read. The Gemini CLI, which can no longer sign
     in, keeps its two path rules the same way.

   A runtime that starts writing somewhere new is refused and must be traced
   and added to `tools/study_launch.py` deliberately.
   `tools/study_launch.py` filters inherited host environment variables through
   an explicit POSIX/runtime/provider allowlist of exact names (dropping
   unrelated host secrets, `LOS_OBSERVATIONS` and every host session's own
   state, §1), while outbound HTTPS network access remains
   permitted so supported AI runtimes can reach dynamic API/CDN endpoints.

4. **V1 runtime certification, Darwin verification, and deferred items.**
   - **Supported study runtime (v1):** Release certification covers Claude Code
     (tested end-to-end with Seatbelt, the broker, and optional `.claude`
     hooks). Multi-vendor launch paths (`codex`, `gemini`, `agy`) exist in
     `tools/study_launch.py` (with `--format agy` / `--runtime agy` hook support
     in `tools/study_hooks.py`) as non-certified experimental paths in v1.
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

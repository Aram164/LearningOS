# Verification campaign V1–V5 (GLM 5.8 Flash, five chats in parallel)

Written by Claude on 2026-10-25 for Aram. Each chat reads **Ground rules**,
then only its own batch. Evidence and failing tests only: no fixes, no pushes.

## Pinned base (identical for all five chats)

- Core `fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46`
- UI `f7dbc1f7607157d5c1c2edb84a14e6a26ab89f94`

Do not use "origin/main at clone time": main may move while the five run,
and the five must test one pair.

## Ground rules

**Setup, in your own folder only.** `N` is your batch number:

```
mkdir -p ~/los-glm-VN-2026-10 && cd ~/los-glm-VN-2026-10
git clone https://github.com/Aram164/LearningOS.git repository
git clone https://github.com/Aram164/learningos-obsidian-ui.git obsidian-ui
git -C repository checkout --detach fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46
git -C obsidian-ui checkout --detach f7dbc1f7607157d5c1c2edb84a14e6a26ab89f94
```

- Verify both HEADs with `git rev-parse HEAD`, and record them.
- Core needs `cd repository && python3.14 -m venv .venv && .venv/bin/pip install -e '.[dev]'`.
- The UI needs `cd obsidian-ui && npm install`.
- Do not run `make setup` or `make hooks`.
- The two folders must be siblings named exactly `repository` and `obsidian-ui`.

**Running in parallel.** Four other chats run at the same time.
- Stay inside `~/los-glm-VN-2026-10/` and your own report folder.
- Never read or write another batch's folder.
- Run one test process at a time, with no `-n` and no xdist.
- Never run the full suite or `make system-check`. Run one focused pytest
  file, or one node test file, per process.

**Never:**
- push, create branches, PRs or issues on GitHub, or dispatch workflows;
- touch the live checkouts: `semestercontext/LearningOS/repository`,
  `LearningOS/obsidian-ui`, or the `semestercontext/` root;
- touch the learner's Obsidian vault, launch the Obsidian app, or write under
  `LearningOS/materials`, which is read-only;
- edit production code, `system/contracts/` (Core) or `src/contracts/` (UI);
- call a real model API.

**Registering a Core test file.** A new Core test file must be registered
in `tests/group_map.py` and `.github/shard-manifest.json` in your clone, or
pytest collection fails. Follow `system/DEVELOPER.md`, task row "Add a test file".

**What counts as a finding.** A finding needs:
- a test that fails on the pin for the stated reason (pytest in Core, node in
  the UI), or, for a documentation claim, a command whose output contradicts
  the document;
- the exact command and its output;
- the contract or document line it violates;
- the source location.

Everything else goes in one of three other categories:
- **Coverage gap:** you could not exercise it.
- **Absence:** authored content is missing. That is a count, never a defect,
  per ADR-017 decision 5.
- **Observation:** no contract line is violated.

Never propose concepts, relations or tags, and never declare mastery. Mark
any claim you did not verify as an ASSUMPTION.

**Output.** Write to `LearningOS/workbench/glm-v-2026-10-25/VN/`, a path
relative to `semestercontext/`:
- `REPORT.md`, with these sections: Base · Reading route · Results per item
  (HELD / FINDING / GAP) · Findings · Coverage gaps · Untested scope ·
  ASSUMPTIONS;
- one folder per finding, `<slug>/{test_or_probe file, finding.md}`;
- `probes/` with copies of every probe file, and `logs/` with the command
  outputs.

Checkpoint `REPORT.md` as you go. To finish, write
`LearningOS/workbench/glm-v-2026-10-25/signals/VN.done` containing
`VN/REPORT.md`, then stop.

## V1 — the developer docs and system map against the code

**Scope:**
- `system/DEVELOPER.md`;
- `system/developer/CODEMAP.md`, `C4.md`, `FLOWS.md` and `changing-contracts.md`;
- all 23 pages in `system/developer/components/`.

These landed today (PR #28). Read `tests/test_system_map.py` and
`tools/system_map.py` first, so you attack only what that guard does not
already check.

**Method.** Extract every concrete claim:
- a path;
- a module, class or function;
- a CLI command or flag;
- a capability id;
- a test file;
- a contract file;
- a call or import edge;
- a flow step and its order.

Then verify each one against the code:
- the path exists;
- the symbol is defined (use `grep`, or `ast` in a small script);
- the edge is a real import or call;
- the command parses: `.venv/bin/python tools/los.py <cmd> --help`, or
  `capabilities <id> --json`;
- the flow's order matches the code.

**Also count:**
- `tools/learning_os/` modules that CODEMAP never mentions;
- components whose page names no test.

**Output:** a claim table (claim, document:line, check, result), totals for
verified / false / unverifiable, and one finding per false claim. Each finding
needs a pytest asserting the documented claim, failing on the pin.

## V2 — the Obsidian UI's on-screen rendering

**Scope:**
- every leaf in `src/views/`: home, library, unit, module, program, review,
  garden, shelving, abilities, project, boundary and nav;
- the render functions under `src/features/`.

K3 tested the atlas's logic, not its DOM.

**Read first:**
- the UI's `CLAUDE.md` (rules 2, 12 and 13), `DESIGN.md` and `ARCHITECTURE.md`;
- how existing tests render: `tests/harness.js`, `tests/fixture-workspace.js`,
  `tests/source-module-loader.js` and `tests/test-fixture-workspace.js`;
- the data in `fixture-vault/`.

**DOM library.** If no DOM library is installed, `npm install --no-save jsdom`
in your clone only.

**Assert, against the fixture vault:**
- Home shows one resumable focus, a short Today list and a short Continue
  elsewhere list. No primary view is a bare list of links (rule 13). Record
  references are typed chips or actions.
- Every view renders with the CLI unavailable and with a stale or missing
  manifest (rule 2), and shows its empty state instead of throwing.
- No view throws on a missing optional field.
- Every interactive element has an accessible name. Button groups are
  keyboard-navigable.
- The atlas DOM:
  - an orphaned question is a non-clickable row reading "— no longer
    authored";
  - the depth remainder is counted on screen;
  - the inspector shows both sentences of one strict row;
  - the Domains lens renders.

**Output.** Each finding needs a failing node test. Views the harness cannot
mount are coverage gaps.

## V3 — the derived layer (learning runtime, semantics)

**Scope:**
- `system/SEMANTIC-CONTRACT.md`;
- `system/developer/components/{learner-derivations,semantics,derived-store}.md`;
- `tools/learning_os/derive/learning_runtime.py` and what it calls;
- the `semantic.query` capability, read with `tools/los.py capabilities
  semantic.query --json`;
- `tests/scenarios/cases/semantic.query.yaml`, so you don't duplicate it.

**Attack with fixture repos.** Use `mini_repo` and `tests/repo_builders.py`
to probe these properties:
1. **Pure:** the same records give byte-identical output across two runs and
   under reordered input files.
2. **Read-only:** no derived value lands in a canonical file. Run `git status`
   after each probe.
3. **Faithful:** every derived item cites records that exist. Changing an
   unrelated record leaves the result unchanged; removing a cited record
   changes it or names the loss.
4. **No mastery:** search every output string for mastery or understanding
   claims. Absent evidence is shown as absent (ARCHITECTURE §12).
5. **Session compiler and replanning** respect study-map stage order, the
   current stage, detours and shelving. They never reorder by semantic
   relations (ADR-016 decision 2).

**Output.** Each finding needs a failing pytest.

## V4 — AI actions end to end

**Scope:**
- `system/AI-ACTIONS.md`;
- `system/developer/components/{ai-action-store,ai-delivery}.md`;
- every AI-related capability listed by
  `.venv/bin/python tools/los.py capabilities --compact --json`;
- invariant 12 in `system/CLAUDE.md`: general AI is read-only.

Use stub or fixture providers only. No network.

**Attack:**
1. **Exact-target binding:** change the target after the request bundle is
   built. The delivery or apply must refuse.
2. **Partial approval:** approving a subset applies only the selected items.
3. **Receipts:** each is written once, and matches what was applied.
4. **Replay:** an exact replay answers replayed with no second write. A
   delivery for another request id is refused.
5. **Relation proposals:** an AI relation proposal stays visibly pending
   until selected, and enters only through `concept.relations.change`, never
   a second path (ADR-017 decision 2).
6. **No provider configured:** every manual path still works (ADR-017
   decision 3).
7. **No direct writes:** a provider response never writes a canonical file
   directly.

**Output.** Each finding needs a failing pytest that drives the real gateway,
as in `tests/gateway_helpers.py`.

## V5 — the backup and restore drill

**Scope:**
- `system/procedures/back-up-and-restore.md`, the executable transcript of
  WORKFLOWS §31;
- `system/developer/components/backup.md`;
- `tests/scenarios/cases/backup.manifest.yaml` and `backup.verify.yaml`.

C1-E already covered the symlinked-subtree case. Skip it.

**Drill.** Write only under `~/los-glm-V5-2026-10/`. First run the documented
procedure exactly as written on a fixture repo. Then run it on a full copy of
your clone:
1. Back up.
2. Verify.
3. Restore into an empty `~/los-glm-V5-2026-10/scratch/restore-1/`.
4. Diff the trees, excluding only what the backup contract declares excluded.
5. Run `validate` and `generate` in the restored tree.
6. Compare `generated/manifest.json`, minus timestamps.

**Attack:**
- one tampered byte in the backup;
- a deleted file;
- a restore into a non-empty folder;
- a restore by code at another revision (restore provenance);
- local-only attachments listed in `system/contracts/local-attachments.yaml`
  but absent from your clone;
- materials referenced but absent. Point at a fixture; never at
  `LearningOS/materials`.

**Output.** Each finding needs a failing pytest, or a transcript showing that
the documented step does not do what the document says.

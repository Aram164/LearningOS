# Learning OS v3 — Repository

Plain-file knowledge repository for deep technical learning. Fresh Git repository, scaffolded 2026-07-16 (Stage 1, Phase 2 of the migration).

Operational learning is module-first: program/area → module → optional
component → unit → one current study map → ordered stages. The physical
tree is under `curriculum/`; workspaces coordinate units through explicit IDs,
and durable knowledge remains under `knowledge/`. The manifest v2 resume
pointer is a shortcut only—it never hides other modules or study maps.

## Quick start

The **operator** is whoever drives this repository through its rules — normally
Claude reading `CLAUDE.md`, but a person with a text editor and Git can operate
it by hand. The repository is the source of truth; the operator only files,
links, and rebuilds views. Everything under `generated/` is a disposable view —
never edit it.

1. **With Claude:** open this folder in a chat and say what you're working on.
   The operator reads `CLAUDE.md`, then `work/COORDINATION.md` +
   the relevant `curriculum/modules/*/module.yaml`, then your active workspace, plus the at-a-glance
   block of `generated/domain-atlas.md` (the cross-domain map). That's the
   whole interface.
2. **By hand:** the one-page home is `generated/reading-room.md` (run
   `make views` to refresh) — exams, workspaces, recent notes, queues, all
   linked. Exam facts live in each owning academic module; the full "what should I
   do next?" dashboard is `generated/coordination-view.md`; your knowledge is
   under `knowledge/notes/`; capture anything into `work/inbox/` (or
   `python tools/los.py capture --text "…"`).
3. **After editing:** run `make check`. The pre-commit hook blocks commits while
   the validator reports errors.

The rest of this file is the full manual; the four commands are under
[Commands](#commands).

- **What this is / how it works:** `system/SPEC-README.md` → `system/PHILOSOPHY.md` → `system/ARCHITECTURE.md`
- **How the operator behaves:** `system/CLAUDE.md` — the single canonical contract; root `CLAUDE.md` (and the `LearningOS/` project-root entry) are symlinks to it
- **Bounded AI actions:** `system/AI-ACTIONS.md` — exact-target request bundles, capability validation, approval and receipts
- **Migration state:** **COMPLETE — cutover 2026-07-17.** Pilot approved (5/5 frozen criteria, `migration/pilot-report.md`); Stage 2 full migration executed same day (`migration/final-report.md`). This repository is the operational root; the legacy `semestercontext/` tree is frozen history (banners point here).
- **Legacy:** the frozen pre-v3 tree is `semestercontext/` (tag `pre-v3-baseline`); this folder is designed to be moved beside it after cutover.
- **Roots:** materials → `../materials/` (`material://<source-id>/…` resolves there), code projects → `../projects/` — both outside the authored tree by design (materials move in Stage 2, Step 8).

## How to use it (the whole manual)

**Start a session:** open this folder in a chat. The operator reads `CLAUDE.md`,
then `work/COORDINATION.md` + the module-first `curriculum/` tree, then your active
workspace — plus the at-a-glance block of `generated/domain-atlas.md`, so every
session starts with the full cross-domain map in view. You just say what
you're working on.

**"What should I do next?"** → the operator rebuilds and reads the coordination
view (exam spine + every workspace's next action). Recommendations are computed
fresh, never read from stored plans.

**Study something:** name the concept — German works ("Kettenregel",
"Hypothesentest"). You get: your notes on it, its prerequisites (dependency
report), and the best source for the purpose — first learning, review,
derivation, drill (selector views).

**Capture anything:** drop it in `work/inbox/` or your workspace `scratch/` —
photos of handwritten pages included. No naming, no filing; say what it is and
the operator routes it. If you ever catch yourself making a filing decision,
stop — that's the operator's job.

**Something becomes worth keeping:** it turns into a note under `knowledge/`
(your reasoning preserved verbatim; the operator asks before any semantic
rewrite, split, or merge).

**A fact changes** ("I registered for X", "deferring Y"): say it once. Exam
events land ONLY in the owning academic `module.yaml`, decisions in `COORDINATION.md` —
never in prose copies.

**An effort ends:** its workspace is archived whole; the durable notes stay.

**Trust but verify:** `python tools/validate.py` after any batch of edits
(session-end habit). Never edit anything under the generated output tree —
it's a disposable view; delete it freely.

## Without the operator (human fallback — no Claude needed)

Everything is plain text; nothing requires any tool to read. The four questions:

- **Exam dates, registrations, grades?** Open the owning academic module under
  `curriculum/modules/` — it is
  commented and readable raw. This file is the only truth for those facts.
- **What should I do next?** Run `make views` (or `python tools/generate.py`),
  then open `generated/coordination-view.md` — exam spine, every workspace's
  next action, neglect signals. Check its `Generated:` timestamp; if views feel
  stale, rebuild (the post-commit hook does this automatically after commits).
- **Where is my knowledge on X?** Browse `knowledge/notes/<domain>/` —
  filenames say what they are — or ctrl-F `generated/concept-index.md`
  (German terms work; aliases are indexed). The prerequisite graph is drawn in
  `generated/concept-map.md`; the one-page cross-domain map (every domain's
  notes, shelves, and what's deliberately outside retrieval) is
  `generated/domain-atlas.md`.
- **Where do I put this?** `work/inbox/` — no naming, no filing, ever.

If something looks broken: `make check` names every problem; `git log` is the
history; `generated/` can always be deleted and rebuilt. No proprietary
anything — a text editor and Git are enough to operate this repository forever.

## Commands

```bash
make setup      # once per clone/move: create .venv, install deps, install both Git hooks
make check      # validate (schemas + VALIDATION.md rules)
make views      # rebuild everything under the gitignored output tree
make status     # one-screen repository state
make inventory  # rebuild the materials manifest (see "Materials durability")
make test-fast  # quick feedback: synthetic fixtures, no checked-in repository load
make test       # complete suite, including full-repository integration checks
make            # list the one-word commands
```

Interface layers (the Obsidian UI project, scripts, other agents) use the
stable CLI gateway instead of parsing YAML — `python tools/los.py status
--json | validate | generate | capture` (ADR-006). Provider-independent AI
actions use the same gateway through `ai-action-list`, `ai-action-prepare`,
`ai-action-import-delivery`, `ai-action-validate-delivery`,
`ai-action-apply-delivery`, and `ai-action-status`; see `system/AI-ACTIONS.md`.
The loader stays the single authority; the CLI only delegates.

`make setup` creates a project-local virtual environment at `.venv/` (gitignored)
and installs the package with its `dev` dependencies from `pyproject.toml`, so
the tooling never touches your system Python —
this sidesteps the PEP 668 / Homebrew "externally-managed-environment" error you
hit on a clean macOS install. Every later `make` target and both Git hooks use
`.venv/bin/python` automatically when it exists, and fall back to the system
`python3` otherwise. Build with a specific interpreter via
`make setup PYTHON=python3.14`.

(Equivalent direct calls once the venv exists: `.venv/bin/python tools/validate.py`
[`--online` adds the URL audit], `.venv/bin/python tools/generate.py`,
`.venv/bin/python -m pytest -m "not full_repo"`, `.venv/bin/python -m pytest`.)
Requires Python 3.12+, `pyyaml`, `jsonschema>=4`,
`pytest` — the tools fail fast with the exact fix if a dependency is missing or
too old.

Two Git hooks (canonical copies in `tools/hooks/`, installed by `make setup`):
**pre-commit** blocks any commit while the validator reports errors (warnings
print but never block); **post-commit** rebuilds `generated/` so the local
dashboards are never stale.

## Changing a schema (the data contract)

Every record schema is `additionalProperties: false`, and canonical records carry
no per-record version. That is strict by design, but it means editing a schema
silently redefines what "valid" means for data already on disk — and years later
there is no way to ask "what format was this note written under, and what brings
it forward?"

`system/contracts/data-contract.yaml` records the current format version and a
fingerprint over `system/schema/*.schema.json` (the schemas governing stored
records; capability payload schemas are excluded — they validate requests, not
data at rest). `make check` compares them, so a schema edit cannot land without a
deliberate decision. When `SCHEMA-CONTRACT-DRIFT` fires:

1. **Does existing data still validate?** `tests/fixtures/formats/v<N>/` holds a
   frozen snapshot of each historical format and is loaded against the *current*
   schemas. If those tests still pass, the change is backward-compatible.
2. **If not, write the migration** under `tools/migrations/` — idempotent,
   dry-run by default, in the style of `curriculum_v2.py`.
3. **Bump the contract:**
   `python tools/schema_contract.py --bump --note "…" [--migration …]`
4. **Freeze the new shape** as a *new* `tests/fixtures/formats/v<N+1>/` and add
   it to `FORMATS` in `tests/test_format_fixtures.py`.

Never edit or regenerate an existing fixture — see
`tests/fixtures/formats/README.md`. A fixture that tracks current code can never
fail, and one that gets edited to pass destroys the record of the format it was
supposed to preserve.

## Changing the manifest (the interface contract)

The data contract above governs what this repository *stores*. What it
*publishes* is a separate contract with separate consumers:
`generated/manifest.json` is the one shape every interface reads, and
`system/contracts/manifest-contract.yaml` declares its version and its exact key
sets.

They are versioned independently and deliberately: a record can gain an optional
field without changing the projection, and the projection can be reshaped
without touching a single stored record.

| what | contract | version |
|---|---|---|
| canonical record format | `system/contracts/data-contract.yaml` | 4 |
| published manifest shape | `system/contracts/manifest-contract.yaml` | 3 |

`build_manifest` checks itself against that declaration on every build, so a
change to the published shape fails here rather than downstream. That is the
point: until 2026-08-08 only the consumer declared the version (in the Obsidian
UI's lock file), so Core could add a top-level key, pass its own tests, push —
and break the other repository. It happened, with `topics`.

When `MANIFEST-CONTRACT-DRIFT` fires:

1. **Bump:** `python tools/manifest_contract.py --bump --note "…"` — it rebuilds
   with enforcement off, adopts the shape actually produced, and records the
   history entry. `--show` prints the current shape without changing anything.
2. **Mirror into the UI in the same change** — `contracts/manifest-v<N>.lock.json`,
   `MANIFEST_CONTRACT_VERSION`, `ManifestV<N>`, and the fixture vault manifest.
   Core and the UI release together; a bump that lands alone is the exact bug
   this contract exists to prevent.

Additive still bumps. Consumers declare an exact version and fail closed, so
"only added a key" is not "invisible".

## Materials durability

`materials/` is the one part of the system Git does not protect. It sits outside
the authored tree by design (~1.9 GB of PDFs, slides and notebooks) and is
tracked by no repository, yet hundreds of `material://` references resolve into
it. A lost drive would therefore turn a large part of the knowledge base into
dangling pointers, and nothing would say so.

`records/materials-manifest.yaml` is the repository's own durable record of that
tree — every file's path, size and SHA-256. It is version-controlled, so the
inventory survives even when the files do not. With it, `make check`
distinguishes cases that otherwise look identical:

| situation | what you get |
|---|---|
| drive unmounted | one `MATERIALS-OFFLINE` warning — not data loss |
| file moved or removed on purpose | `MATERIALS-DRIFT` warning — run `make inventory` |
| file a canonical record points at is gone | `MATERIAL-MISSING` **error** |
| reference to a file never inventoried | `MATERIAL-UNREGISTERED` **error** |

Presence and size are checked on every `make check` (a few hundred
milliseconds); content is not, because hashing 1.9 GB does not belong in a
pre-commit hook. `make verify-materials` does the full SHA-256 pass.

**Backup, and proving a restore worked.** Copy `materials/` wherever you keep
backups — it is ordinary files, so any tool will do. What the manifest adds is
the ability to *check* a restore instead of hoping:

```bash
python tools/materials_manifest.py --against /Volumes/backup/materials --deep
```

That reports every file missing from the copy, every file whose contents differ,
and every file present in the copy but unknown to the inventory — exit code 1 if
the restore is incomplete. Run it after restoring, and occasionally against the
backup itself; a backup nobody has ever verified is a guess.

Rebuild the manifest with `make inventory` after deliberately adding, moving or
removing sources, and commit it with the change that caused it.

## Transactional writes and Projects

Canonical UI/CLI mutations are declared in
`system/contracts/capabilities.yaml` and committed atomically through the
shared transaction service. Successful writes produce receipts and increment
only the affected artifact revisions. The Bachelor thesis is the first
first-class Project; its former module ID remains a compatibility alias while
manifest v2 is still supported.

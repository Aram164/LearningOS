# Human-Operability Review — 2026-07-17

> Post-cutover review requested by Aram: "find ways to make the system as
> operable by humans as possible without any sacrifice into functionality."
> Reviewed: README, CLAUDE.md (both copies), ARCHITECTURE, PHILOSOPHY,
> VALIDATION, WORKFLOWS, all generated views, COORDINATION.md, modules.yaml,
> a workspace CONTEXT, the materials tree, and the Git state.
> Companion to `external-review-2026-07-16.md` (which fixed the *machine*
> interface; this one audits the *human* fallback path).

## Verdict up front

The system is already unusually human-operable for a machine-first design:
every canonical artifact is plain text a human can read cold — `modules.yaml`
is commented and self-explaining, workspace CONTEXT files read like briefing
memos, the coordination view is a real dashboard, and filenames equal IDs so
`knowledge/notes/mathematics/note-sad-l04-exercise-bank.md` tells you what it
is before you open it. Nothing below requires changing a single invariant.
The gaps are all of one kind: **the human paths exist but are undocumented,
unautomated, or unreachable away from this machine.**

Applied in this session (approved beforehand): the ⛔ hard-rules card at the
top of both CLAUDE.md copies, and the pre-commit validation gate
(`tools/hooks/pre-commit`, installed; blocks on errors, prints warnings).

---

## Tier 1 — highest value, zero architectural risk

**1. A "Without the operator" section in README.** The manual is entirely
Claude-mediated ("open this folder in a chat"). A human at a uni PC, on a
phone, or years from now needs four lines: exam facts → `records/modules.yaml`
(read it raw, it is commented); "what next" → `python tools/generate.py`, then
`generated/coordination-view.md`; find knowledge → browse
`knowledge/notes/<domain>/` or ctrl-F `generated/concept-index.md`; capture →
drop anything in `work/inbox/`, no naming. This codifies paths that already
work — pure documentation.

**2. A private Git remote (GitHub).** The single biggest win, twice over:
(a) *access* — the GitHub mobile/web apps make every note, record, and
workspace readable from anywhere, and the >100 MB attachment problem was
already solved at migration (lossless splits); (b) *survival* — right now the
entire canon lives on one disk. `generated/` stays gitignored, so dashboards
aren't visible remotely — acceptable for now (records and workspaces are);
a later GitHub Action could publish views to a `views` branch without
touching the "never commit generated/" invariant.

**3. Auto-fresh dashboards: a post-commit hook running `generate.py`.** The
views carry a Generated timestamp, but a human reading a stale dashboard
won't notice. Regenerating on every commit makes the local views always
current with zero habit required. Deterministic output + gitignored tree =
zero drift risk. (The pre-commit hook already validates; this is its twin.)

**4. One-word commands — a `Makefile`** (or `tools/refresh` script):
`make check` = validate, `make views` = generate, `make test` = pytest,
`make setup` = the pip install line + hook installation. Humans reliably
remember one word; they do not reliably remember
`pip install --break-system-packages --upgrade "jsonschema>=4"`.

**5. Fail-fast dependency check in `validate.py`.** With an old `jsonschema`,
the validator currently dies with an `AttributeError` traceback
(`Draft202012Validator`) — reproduced live in this session's sandbox. A
two-line version check printing "run: pip install --upgrade jsonschema"
converts the scariest human moment (tool explodes) into an instruction.

**6. Update the Cowork project instructions.** They still say "Read
HANDOFF.md first, then SEMESTER-STATUS.md" — both retired legacy. Point them
at `LearningOS/repository/` (README → CLAUDE.md → COORDINATION +
modules.yaml). Only Aram can edit project settings.

## Tier 2 — real improvements, small spec amendments needed

**7. A generated Mermaid concept map** (`generated/concept-map.mermaid`,
`requires` + `builds-on` edges only). GitHub and VS Code render Mermaid
natively — the human finally *sees* the prerequisite graph instead of reading
the dependency report. Deterministic, disposable, one addition to the
WORKFLOWS §12 output list.

**8. Alphabet/TOC jump links atop `concept-index.md` and `source-index.md`**
(2 033 and 4 751 lines). Ctrl-F works, but a generated table of contents makes
both indexes navigable by scrolling humans and on GitHub mobile, where
in-page search is weak. Generator-only change.

**9. A CLAUDE.md sync check in the validator** (W-level). Root `CLAUDE.md`
and `system/CLAUDE.md` are meant to be identical except §13 — that is a
hand-maintained invariant today, exactly the kind that drifts. One
mechanical diff in `validate.py` retires the trap. (This session updated
both copies in lockstep; the check makes that automatic forever.)

**10. Surface the silent decision queues.** `materials/_unsorted/` (521 MB)
and `materials/_duplicates-for-review/` are pending-human-decision piles that
nothing ever mentions again — the same failure mode as the old inbox, which
*does* have a 14-day validator warning. A W-level count ("_unsorted holds N
items") in the validation report keeps them visible without nagging.

## Tier 3 — worth considering, decide deliberately

**11. Countdown column in the exam spine** ("42 days"). High human value,
but it makes output depend on the generation date, which strains the
byte-identical-except-timestamps determinism rule (VALIDATION §Generated).
Doable if the rule is amended to bless date-derived fields explicitly;
otherwise skip — the dates are plain to read.

**12. A weekly digest outside the repo** (Cowork scheduled task): rebuild
views, then summarize exam spine + neglect signals + inbox/unsorted counts
into a short brief. Nothing enters the repo; the repo stays the single
source. The existing `agnes-2pz-registration` reminder (fires 2026-08-31)
is exactly this pattern — dates own the facts, alarms live outside.

**13. A read-only Obsidian vault** pointed at `knowledge/notes/` — only if a
browsing UI is ever actually missed: gitignore `.obsidian/`, disable link
auto-updates, never author there. Per ADR-001/external review, no dashboards,
no plugins, no second linking convention. Default recommendation: don't.

## Explicitly rejected (would sacrifice functionality or invariants)

Committing `generated/` to Git (stale-view drift — the v2 disease);
a hand-written TODAY.md or any human-maintained dashboard (second source of
truth); Obsidian as an authoring layer (rejected in ARCHITECTURE §17 for
cause); wikilink conversion of note bodies (verbatim preservation rule);
auto-running `pytest` in the pre-commit hook (slow hooks train humans to
`--no-verify`, which kills the gate).

## Suggested order

2 (remote — also the backup) → 1, 6 (documentation, minutes) → 3, 4, 5
(automation trio) → 9, 10 (validator additions) → 7, 8 (view polish) →
11–13 as appetite allows.

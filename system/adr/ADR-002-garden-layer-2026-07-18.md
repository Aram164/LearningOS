# ADR-002 — Garden & Harvest exploratory layer (2026-07-18)

**Status:** accepted · implemented in commit `d5dd87f` · **Context:** Aram
proposed a dual-layer model — a strict "Fortress" (`knowledge/notes/`, full YAML
+ validation) beside a free-form "Garden" (`knowledge/garden/`) where half-formed,
cross-cutting ideas can be captured and gestate without paying the Fortress's
price of admission, and later be promoted ("Harvested") into canonical notes.
The proposal is recorded verbatim in the appendix.

The frozen architecture (entity families, ownership rules, invariants) is
unchanged. The Garden is deliberately *pre-canonical*: nothing in it is a note,
concept, source, or fact until Harvested, so no schema, registry, or invariant
applies to it.

## Adopted (with refinements)

- **The Garden** (`knowledge/garden/`): free-form Markdown, optional inline
  `#tags`, no frontmatter, never loaded as canonical notes.
- **The Nebula** (`generated/nebula.md`): a disposable view grouping garden
  notes by tag with a Git-based harvest signal (uncommitted + oldest first).
- **"Harvest the Garden"** routine and the contract that governs it:
  `system/CLAUDE.md` §14.

Refinements made to the proposal as submitted:

1. **Contract target corrected.** §14 was added to the *canonical*
   `system/CLAUDE.md` (root `CLAUDE.md` is a symlink), not a stray root copy.
2. **Garden ≠ inbox.** The proposal's premise ("capture is high-friction")
   understated the existing zero-friction path (`work/inbox/`, workspace
   `scratch/`). §14 draws the distinction explicitly: inbox is a *processing
   queue* meant to empty; the Garden is a *durable holding ground* where ideas
   are allowed to sit. This keeps the Garden from becoming a second inbox.
3. **Validator exemption (the piece the proposal missed).** The validator sweeps
   every `.md` under `knowledge/` for link integrity, ownership, and URLs, so
   free-form notes would have raised `LINK-BROKEN`/URI errors and broken the
   green bar. `knowledge/garden/` is now exempted from those three
   canonical-tree sweeps (`tools/learning_os/rules.py` `_in_garden`) and
   `nebula.md` is allowlisted — this is what actually makes the Garden "exempt
   from `make check`" as promised. Stray non-Markdown there is still flagged
   (the Garden stays text-only).
4. **Anti-rot rule.** A parallel unvalidated store risks becoming a graveyard.
   §14 adds a standing "promote / keep gestating / prune" triage surfaced from
   the Nebula's staleness signal, so the Garden trends toward a nursery, not an
   attic.
5. **Tag extraction hardened.** Inline/fenced code spans are stripped before
   pulling `#tags`, so a hashtag written as code (e.g. `` `#tags` ``) is not
   mistaken for a real tag.

## Consequences

- Non-breaking and additive: the Fortress (canonical notes, schemas, validation,
  all existing views) is untouched. `make check` stays green; `make views`
  now also builds `nebula.md`; `make garden` is a convenience alias.
- New surface to maintain: one dataclass + scan in the loader, one builder in
  the generator, three one-line guards + an allowlist entry in the validator,
  §14 in the contract. Verified: validator 0/0 (including a deliberately broken
  garden note), 55/55 tests pass, `nebula.md` byte-for-byte reproducible.
- Open follow-up (not blocking): regression tests for the garden loader/Nebula
  and the validator exemption are not yet added — see the test backlog in
  `review-recommendations-2026-07-17.md`.

---

## Appendix — original proposal (as submitted by Aram, verbatim)

> # Proposal: Extend Learning OS with an "Exploratory Garden" Layer
>
> **Status:** Ready for implementation
> **Scope:** Loader, Generator, AI Contract
> **Impact:** Non-breaking (additive) — the existing exam‑prep core remains untouched.
>
> ## 1. The Problem We Are Solving
>
> Learning OS v3 is an excellent "Fortress" for **exam‑ready, structured knowledge**. Every note in `knowledge/notes/` must carry strict YAML frontmatter (`concepts`, `sources`, `state`, etc.) and pass validation (`make check`). This ensures correctness, traceability, and automated views — but it introduces friction for the **exploratory, messy, interdisciplinary phase** of learning.
>
> When you encounter a new, complex topic, you often don't know which concepts it belongs to, which sources it references, or even if it will survive as a coherent idea. Forcing a half‑baked insight into a strict schema at capture time is:
> - **Premature**: It imposes categories before you understand them.
> - **Bureaucratic**: It breaks the flow of deep thinking.
> - **Disincentivising**: It discourages capturing fragile, cross‑cutting epiphanies.
>
> The current architecture punishes early‑stage thinking, which is the opposite of what a "Learning OS" should do.
>
> ## 2. The Solution: A Dual‑Layer Model (Fortress & Garden)
>
> We introduce a **second, unstructured layer** — the **Garden** — that lives alongside the strict **Fortress**.
>
> ### The Fortress (Existing)
> - **Location**: `knowledge/notes/`
> - **Rules**: Strict YAML frontmatter, full validation, concept links, source citations.
> - **Purpose**: Durable, exam‑ready, canonical knowledge.
>
> ### The Garden (New)
> - **Location**: `knowledge/garden/`
> - **Rules**: **No required YAML frontmatter**. Exempt from `make check`. Pure Markdown, with optional inline tags (e.g., `#chaos`, `#philosophy`).
> - **Purpose**: Raw, messy, half‑baked ideas, cross‑cutting reflections, interdisciplinary "sparks".
>
> The AI (Claude) handles all the heavy lifting: shelving captured thoughts into the garden, extracting tags, and—during a "Harvest"—promoting mature ideas into the fortress with proper YAML frontmatter.
>
> ## 3. Implementation Plan (Code‑Level)
>
> ### 3.1 Loader (`tools/learning_os/loader.py`)
> **Changes**:
> 1. Add a new dataclass `GardenNote` to represent unstructured notes.
> 2. Add a `garden_notes` field to the `Repo` dataclass.
> 3. In `load_repo()`, after loading strict notes, scan `knowledge/garden/` for `.md` files.
> 4. For each garden note, read its content and extract inline tags (using a simple regex for `#word`).
> 5. **Do not parse YAML frontmatter** — treat the file as pure Markdown.
>
> **Benefits**: The validator iterates only over `repo.notes` (the fortress), so garden notes are completely ignored by `make check`.
>
> ### 3.2 Generator (`tools/learning_os/genout.py`)
> **Changes**:
> 1. Add a new function `build_nebula(repo, generated_at)`.
> 2. This function groups garden notes by their extracted tags.
> 3. It generates `generated/nebula.md` — a clean Markdown index with a warning header, grouped tags, and links to each note.
> 4. Add this function to the `generate_all()` outputs.
>
> **Benefits**: The Nebula view is a disposable view (like the concept index), and it gives you a quick overview of all "loose" ideas, grouped by theme.
>
> ### 3.3 AI Contract (`CLAUDE.md`)
> **Changes**: Add a new section (e.g., §14) titled **"Garden & Harvest (exploratory layer)"**. Define the **"Harvest the Garden"** routine:
> 1. Read every `.md` file in `knowledge/garden/`.
> 2. Evaluate if the idea has matured.
> 3. Propose a full YAML frontmatter (ID, title, concepts, sources, role, state, etc.).
> 4. Ask for the user's approval (per note or batch).
> 5. Move the approved note to `knowledge/notes/` (adding the frontmatter).
> 6. Run `make check` and `make views` to integrate it.
>
> **Benefits**: The user never has to learn a new interface. They simply say *"Harvest the Garden"* and Claude handles the entire promotion pipeline.
>
> ### 3.4 (Optional) Makefile
> Add a `make nebula` target that calls `python tools/generate.py`. Since `generate_all()` now includes `nebula.md`, the view will be rebuilt automatically. This is just a convenience for quick checks.
>
> ## 4. User Workflow (How It Feels)
> 1. **Capture**: You have a cross‑cutting thought. Instead of forcing it into a note with YAML, you drop it into `knowledge/garden/` (or ask Claude to do so). You might sprinkle inline tags like `#philosophy` or `#neural-networks`.
> 2. **Organise (AI does this)**: When you run `make views` (or ask Claude to "refresh the views"), `generated/nebula.md` is rebuilt. You can now browse your messy ideas grouped by their emergent tags.
> 3. **Promote**: When an idea matures, you say *"Harvest the Garden"*. Claude reads all garden notes, proposes a strict frontmatter for the ripe ones, and moves them to `knowledge/notes/` after your approval.
>
> ## 5. Why This Is the Right Approach
> - **Zero manual overhead**: The AI handles shelving, tagging, and promotion. The human only decides *which* ideas are ready for the fortress.
> - **Preserves the fortress**: The garden is a parallel universe. The validator, concept index, and exam views are unchanged.
> - **Encourages capture**: You no longer hesitate to write down half‑baked ideas because the "cost" is near zero.
> - **Maintains long‑term value**: The Nebula view ensures messy thoughts aren't lost, and the Harvest routine ensures the best ideas eventually enter the canonical system.
>
> ## 6. Summary of Patches
>
> | File | Change | Line Impact |
> | :--- | :--- | :--- |
> | `tools/learning_os/loader.py` | Add `GardenNote`, `garden_notes`, scan `knowledge/garden/` | ~20 lines added |
> | `tools/learning_os/genout.py` | Add `build_nebula()` and include it in `generate_all` | ~30 lines added |
> | `CLAUDE.md` | Add §14 describing the Garden & Harvest routine | ~25 lines added |
> | `Makefile` (optional) | Add `make nebula` target | ~3 lines added |
>
> No file is deleted. No existing logic is removed. The change is entirely additive and non‑breaking.
>
> ## 7. Next Steps
> 1. Apply the patches (or ask Claude to apply them with the repository open).
> 2. Create the `knowledge/garden/` directory.
> 3. Add a few raw Markdown files with inline tags to test the Nebula.
> 4. Run `make views` and inspect `generated/nebula.md`.
> 5. Trigger a "Harvest" to verify the promotion workflow.
>
> This upgrade transforms Learning OS into a **living laboratory** — where messy thoughts gestate, mature, and eventually graduate into canonical knowledge. It fully aligns with the system's philosophy: *"Reduce organizational burden rather than create it."*

# SYSTEM-ARCHITECTURE-REVIEW — External Evaluation

> **Date:** 2026-07-16 · **Scope:** the degree-long knowledge system (`MASTERS-ARCHITECTURE.md`, `SYSTEM-MANUAL.md`, the tier-1/2/3 stack, CONCEPT-INDEX, DEGREE-WIRING, module-cards).
> **Not** part of the canonical system — an outside read, deliberately carrying no system frontmatter. Integrate or discard.
> **Method:** read the spec + manual + real artifacts on disk (AML L02–L07, SaD units, index, wiring, template, a module card) + four workflow answers from Aram (2026-07-16).

---

## The central finding

**The system is designed for a human navigator and operated by an AI one.**

The architecture invests heavily in human-facing navigation: an Obsidian DASHBOARD (Dataview), Smart Connections semantic pane, a ctrl-F CONCEPT-INDEX with human-readable depth glyphs, a TOOLING.md stack. But the stated retrieval behavior is: *"ask Claude."* The index is, in practice, a **Claude-facing routing table**, not something the human reads.

This single mismatch explains both reported pain points:

- **Sprawl** hurts because the human aids that were supposed to tame it (dashboard, graph, semantic pane) aren't the interface actually used — and the interface that *is* used (Claude over the file tools) was never explicitly optimized for.
- **Trust** ("is this really worked, or just planned?") hurts because the workedness signal (🟢🟡⚪ depth) is a hand-maintained assertion in the index, one step removed from the file it describes, and the human no longer personally vouches for it — they trust Claude, who trusts a flag that can drift.

Everything below is this finding seen through the four requested lenses.

---

## 1 · Knowledge architecture — is the structure logically minimal?

**Strong.** The normalization rules are genuinely good and rare: one-inbox-per-tier, "index points INTO units, never copies," the anchor-file rule (one frontmatter block per unit, not four), archive-never-delete, stable `<MODULE>-<Semester>` IDs. Inside the *markdown system* there is very little redundancy. This is better-disciplined than most personal knowledge bases.

**Two non-minimalities the design doesn't see:**

1. **A dead second interface.** The system maintains *both* a human-navigation stack (Obsidian dashboards, Smart Connections, index ergonomics, TOOLING.md) *and* the implicit Claude-navigation path — and only the latter is used. Half the navigation architecture is built for a reader who doesn't show up. That's not minimal; it's a dual-interface system carrying one dead interface.
2. **Workedness is asserted, not derived.** "Is this concept worked?" lives in two places at once: the actual file (does a full Ultimate Reference exist?) and the 🟢🟡⚪ flag in the index row. Two sources of truth for one fact → they can disagree → drift. In a minimal system, depth is *computed from the artifact*, never typed by hand into a parallel table.

---

## 2 · Cognitive workflow — does it match how humans actually learn?

**Strong where it counts:** scope-to-lecture (learn the thing as taught, not the textbook chapter), single-study-script (kills decision fatigue), Exercise Bank → Anki (spaced retrieval), prerequisite wiring (learn in dependency order). These are well-aligned with how learning actually consolidates.

**Two frictions, both confirmed by the "mixed authoring" answer:**

1. **False uniformity.** The 4-file / one-pass unit is treated as *the* degree-wide standard, but authoring is module-dependent (math ≠ ML ≠ systems). A proof-based math course learned iteratively does not fit the same mold as a concept-based ML lecture Claude can draft in one pass. Forcing one artifact shape over heterogeneous learning modes means the unit is high-value for some modules and low-value busywork for others — and the system can't tell which.
2. **No home for the messy middle.** The system stores only *finished* artifacts (Reference, Mini Plan, Bank, Exam). There is no canonical place for rough notes, live insights, or open questions — but that messy middle is *where understanding actually forms*. For modules where you learn first and Claude formalizes after, the elaborate unit is a post-hoc transcription of something you already understood — cognitively cheap. The system optimizes note **production**; it does little for **comprehension** during the hard part.

---

## 3 · LLM compatibility — can future agents navigate it efficiently?

This is now the **primary** interface ("ask Claude"), so it is the most important lens — and the system is only *accidentally* good at it.

**Genuinely above-average LLM-legibility:** plain markdown, stable IDs, frontmatter, root-relative paths, an explicit concept→path index, explicit module wiring, a HANDOFF→STATUS bootstrap order. A cold Claude session can orient itself. Most people's notes can't offer this.

**Three problems that bite at your stated scale (5–10k md, uncapped):**

1. **Signal-to-noise / context budget.** 175 markdown files sit inside ~60,600 total files (PDFs, repos, venvs, video dumps). Every agent that greps or explores pays for the material haystack — a plain directory listing already overflows a tool-call token budget today. `.gitignore` fixes *git*, not *Claude's file tools*. At your target scale the md system will be buried in 200k+ material files, and "ask Claude" degrades: the agent spends its budget *locating*, not answering. **The clean system is not isolated from the noisy archive.**
2. **The agent's map isn't authoritative.** You trust Claude → Claude trusts CONCEPT-INDEX → the index is hand-maintained and can be stale or incomplete (e.g. "gradient boosting" isn't indexed; several rows are ⚪/🟡 plan-level). When the map is wrong, a capable agent silently re-derives or invents a path instead of failing loudly. For a Claude-navigated system, **index freshness is mission-critical**, yet nothing enforces it except a ritual that has never run.
3. **No machine-readable manifest.** Navigation lives in prose tables meant for human eyes. A future agent would navigate far more reliably from a *generated* manifest (concept → path → depth → last-verified) **derived from the files**, not authored beside them.

---

## 4 · Long-term maintainability — manageable after 5–10 years?

**Right instinct:** operational-dies / knowledge-promotes means semester cruft never accumulates in the permanent layer. That is the correct longevity move and most systems get it wrong.

**Three risks that compound with time:**

1. **The keystone step is unproven.** The entire degree layer's value depends on the promotion ritual — 2–3h, manual, and **never executed once.** Every module card on disk is still a stub. A system whose central maintenance step has zero successful runs is carrying unquantified risk: if the first ritual is painful or skipped, the degree layer quietly rots into permanent stubs.
2. **Manual metadata vs uncapped scale.** Depth flags, index rows, and wiring edges are all hand-maintained. "Don't want to cap scale" + "metadata typed by hand" is a direct collision — maintenance load grows with the corpus while the maintainer's time doesn't.
3. **Trust decay is the actual killer.** Your pain #2 (is this really worked?) is the early symptom of the failure mode that ends knowledge bases: the index drifts → you stop believing it → you stop using it → it becomes dead weight. This is already why you "ask Claude" instead of reading the index. Left alone, it spreads from the index to the units themselves.

---

## Weaknesses ranked by cost-if-deferred

Cheapest to fix now, most expensive to retrofit later — top of list first.

1. **Interface mismatch (root cause).** Reorient the design around Claude as the primary reader: invest in machine-navigability, stop maintaining the unused human-navigation stack. Cheap today; in five years it's a pile of Obsidian-shaped decisions to unwind.
2. **Material sprawl pollutes the agent's search space** (pain #1). Structurally separate the markdown *system* from the material *archive* so Claude searches a clean tree (e.g. a `system/` root, or an agent-facing allowlist/manifest of the 175 files). Trivial at 175 files; miserable at 5k buried in 200k.
3. **Workedness asserted, not derived** (pain #2, trust). Make depth *computed and verifiable* from the artifact, and **generate** the index from the files rather than typing rows. Cheap while there are 175 files; a nightmare to reconcile at 5k.
4. **Unproven keystone ritual + all-stub degree layer.** Run one *mini* promotion soon (even on a single finished module) to de-risk the process before ten semesters depend on it.
5. **False uniformity of the unit model.** Let module *type* dictate artifact shape — full 4-file units where Claude drafts from slides; something lighter where you learn first and just want an indexed pointer.

---

## The one-line version

The bones are excellent and the discipline is real. The single architectural weakness worth fixing before it gets expensive is that **the system is built for a human to navigate and a human to trust, but you navigate and trust through Claude** — so the highest-leverage move is to make the corpus *machine-navigable and machine-verifiable* (clean system/archive split + a generated, self-checking index), and to retire the human-navigation scaffolding you don't use.

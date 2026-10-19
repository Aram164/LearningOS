---
id: masters-architecture
type: brain
status: live
---

# MASTERS-ARCHITECTURE — The Degree-Long Knowledge System (v2)

> **v1:** 2026-07-10 (seed) · **v2:** 2026-07-10 (rebuild: file conventions, validation layer, tooling integration, semester retrofit). Read after `MASTERS-HANDOFF.md` for knowledge-architecture questions (module selection → `MASTERS-MODULE-PLAN.md`).
>
> **Design goals:** versatile (any tool or chat session can read/query it) · robust (machine-validated, no duplication, plain text) · extendable (templates + stable IDs + skills) · cheap to run (zero paid tools, zero servers, one-command validation, metadata added only at natural moments).

---

## §1 Two layers, different lifetimes

| Layer | Contents | Lifetime |
|---|---|---|
| **Operational** | brain/status files, step IDs, chat division, load planner, open loops, neglect tracker | **One semester.** Frozen at semester end. |
| **Knowledge** | tier-3 lecture units, crosswalks, bridges, wiring docs, resource libraries, exam artifacts | **The whole degree.** Grows monotonically. |

**Rule: operational artifacts get archived; knowledge artifacts get promoted** (ritual → §6).

## §2 Components (semester pattern → degree level)

| Semester level (SoSe 26, proven) | Degree level (this folder) |
|---|---|
| `HANDOFF.md` + `SEMESTER-STATUS.md` | `MASTERS-HANDOFF.md` + `MASTERS-STATUS.md` |
| `LEARNING-RESOURCES.md` (tier 1) | `MASTERS-*-RESOURCES.md` × 6 axes |
| ChatN module plans (tier 2) | per-semester plans from `templates/SEMESTER-KICKOFF-Template.md` |
| `Plans/WIRING.md` (domain↔domain) | `DEGREE-WIRING.md` (module↔module) |
| Tier-3 lecture units (tier 3) | same units, standardized by `templates/LECTURE-UNIT-Template.md` |
| — | `CONCEPT-INDEX.md` — concept → worked note (the retrieval layer) |
| — | `module-cards/` — one passport per completed module |
| `tools/check_links.py` | `Masters-Planning/tools/check_system.py` (links + index + cards + metadata, degree-wide) |
| — | `skills-src/` — rituals as installable Cowork skills |
| — | `TOOLING.md` — optional viewer/SR/literature stack setup |

## §3 File conventions (v2 — what makes everything queryable)

### 3.1 Frontmatter schema

Knowledge-layer files carry a minimal YAML block (≤7 keys). This one schema serves Obsidian/Dataview queries, `check_system.py` linting, and Claude sessions alike:

```yaml
---
id: AML-SoSe26-L05        # stable, unique; module IDs per §7
type: unit | card | crosswalk | bridge | wiring | index | overview | brain | template | skill
module: AML-SoSe26        # owning module (omit for cross-module files)
concepts: [logistic-regression, mle, cross-entropy]   # slugs, match CONCEPT-INDEX
depth: full | partial | plan    # = 🟢 / 🟡 / ⚪
status: live | stub | frozen
---
```

### 3.2 Anchor-file rule (keeps it cheap)

A tier-3 unit = folder of 4 files (Reference/Mini Plan/Exercise Bank/Mock Exam). **Only the Ultimate Reference carries frontmatter** — one metadata block per unit, not four. Retrofitted 2026-07-10 across all 12 existing SoSe-26 units + 8 reference docs.

### 3.3 Path citation rule

File references in prose/tables are root-relative from `semestercontext/` in backticks (existing convention). `check_system.py` validates every such reference — cite paths precisely and the system stays self-checking.

### 3.4 When metadata gets added (never as a chore)

- New unit → frontmatter comes from the template at creation.
- Completed module → cards/index rows at the promotion ritual.
- Never retro-edit en masse mid-semester (the Jul-10 retrofit was the one-time bootstrap).

## §4 Validation (robustness, one command)

```
python3 Masters-Planning/tools/check_system.py        # links + index paths + card gaps + frontmatter lint
lychee --offline .                                    # optional extra: markdown-link syntax checker (see TOOLING.md)
```

Run at: every promotion ritual, after any restructure, before relying on the index in a new semester. Non-zero exit = something to fix. (`lychee` complements but does not replace `check_system.py` — our backtick citations aren't markdown links.)

## §5 Semester kickoff (~1 h, each semester)

`templates/SEMESTER-KICKOFF-Template.md` (or skill `semester-kickoff` once installed). Degree-specific steps: wire backwards from `DEGREE-WIRING.md` incoming edges + Module Cards; "revise via" pointers for indexed concepts; register semester in §8; verify module facts fresh (Moses/AGNES).

## §6 End-of-semester promotion ritual (~2–3 h, after exams)

`skills-src/promotion-ritual/SKILL.md` is the executable version. Steps: (1) freeze operational layer, (2) fill Module Cards, (3) CONCEPT-INDEX rows for new worked concepts, (4) new DEGREE-WIRING edges, (5) promote resources to axis files, (6) frontmatter on any new anchor files, (7) `check_system.py` green.

## §7 Naming & longevity

1. **Stable module IDs:** `<MODULE>-<Semester>` (`AML-SoSe26`, `DBT-WiSe2728`) — used in frontmatter `id`/`module`, card filenames, wiring nodes, index rows.
2. Root-relative paths; no redirect stubs — fix links and re-run the validator.
3. Tier-3 unit format is the degree-wide standard (template, not example-by-imitation).
4. One inbox per tier: material → axis RESOURCES · worked concept → CONCEPT-INDEX · module edge → DEGREE-WIRING.
5. Doppelanrechnung locks (AMLS, mlprov) block LP credit, never knowledge reuse.

## §8 Semester registry

| Semester | System root | Brain | State |
|---|---|---|---|
| SoSe 2026 (Bachelor) | `semestercontext/` (parent) | `SEMESTER-STATUS.md` | 🟢 live — metadata retrofit Jul 10; content untouched from Masters sessions (iron rule) |
| WiSe 26/27 (Bachelor Endspurt) | TBD at kickoff | — | future |
| M1 WiSe 27/28 … M5 | TBD at kickoff | — | future (slots: `MASTERS-MODULE-PLAN.md`) |

## §9 Tooling (optional layer — details in `TOOLING.md`)

Adopted stance: **markdown is the system; tools are lenses.** Obsidian (viewer + Dataview/Breadcrumbs/Smart Connections), lychee, Anki+MCP (post-M2), Zotero+MCP (Masters/thesis). Nothing in the system depends on any of them — delete every tool and the files still work in any chat session.

## §10 What NOT to build

- No database, no server, no paid tool as a dependency.
- No per-concept note files — the index points INTO units, never copies.
- No live semester↔degree mirroring — sync only at promotion.
- No plugin-packaging of rituals until the first promotion ritual has proven them (decision 2026-07-10).

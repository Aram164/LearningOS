---
id: system-manual
type: brain
status: live
---

# SYSTEM-MANUAL — What We Built & How To Work With It

> **Created:** 2026-07-10 · The operator's manual for the whole knowledge system. `MASTERS-ARCHITECTURE.md` is the *spec* (what the system is); this is the *manual* (how you use it). Read this when you forget how the pieces fit — or hand it to a fresh Claude session.

---

## §1 The system in one paragraph

Every semester runs a **semester system** (like `semestercontext/` now): a brain file tracks live state, module plans sequence the work, and studying produces **tier-3 lecture units** — your worked, exam-grade notes. The semester machinery (deadlines, step IDs, priorities) *dies* when the semester ends; the knowledge (units, crosswalks, bridges) *lives forever*. The **degree layer** (`Masters-Planning/`) is what makes that knowledge reusable across five years: a **concept index** routes any concept to your worked note, **module cards** are passports of completed modules, **degree wiring** says which module feeds which, and two **rituals** (kickoff, promotion) move things between the layers at semester boundaries. A **validator** keeps every reference honest; **Obsidian** is a lens over the same files, never a dependency. Nothing lives in two places; everything is plain markdown any chat session can read.

## §2 The mental model

```
            DEGREE LAYER (Masters-Planning/ — permanent, grows forever)
   CONCEPT-INDEX ── DEGREE-WIRING ── module-cards/ ── MASTERS-*-RESOURCES
        ▲  routes into      ▲ edges added         ▲ filled at
        │  worked notes     │ at promotion        │ promotion
   ═════╪═══════════ PROMOTION RITUAL (each semester end) ═════╪═════
        │                                                      │
            SEMESTER SYSTEM (one per semester — frozen at end)
   Brain (STATUS) → Module plans (ChatN) → TIER-3 UNITS ← the gold
   SESSION-LOG · CHAT-DIVISION · LEARNING-RESOURCES · WIRING
        ▲
   ═════╪═══════════ KICKOFF RITUAL (each semester start) ═════════
        └── new semester wires BACKWARDS: reads cards + index first
```

Three tiers *within* a semester (unchanged from what you proved this semester): **tier 1** = LEARNING-RESOURCES (all material, the only inbox) → **tier 2** = module plans + crosswalks (what to study, in what order, from which source) → **tier 3** = lecture units (the actual study surface). New material always enters at tier 1; studying always happens at tier 3.

## §3 Component map (what exists, where, when you touch it)

### Degree layer (`Masters-Planning/`)

| Component | What it is | You touch it… |
|---|---|---|
| `MASTERS-HANDOFF.md` → `MASTERS-STATUS.md` | Degree brain (read order) | every Masters-planning session |
| `MASTERS-ARCHITECTURE.md` | The spec: layers, conventions, rituals | when changing the system itself |
| **`CONCEPT-INDEX.md`** | concept → your worked note (🟢🟡⚪ depth) | **look up constantly**; add rows when units complete |
| **`DEGREE-WIRING.md`** | module→module edges, whole degree | at kickoff (read) + promotion (write) |
| `module-cards/` | one passport per completed module (6 SoSe-26 stubs) | fill at promotion; read at kickoff |
| `templates/` | LECTURE-UNIT, MODULE-CARD, SEMESTER-KICKOFF | copy from, never edit casually |
| `skills-src/` | 3 installable Claude skills (unit-builder ✅ installed, promotion-ritual, semester-kickoff) | install via Settings → Capabilities |
| `Masters-Planning/tools/check_system.py` | validator: citations, links, cards, frontmatter | after restructures + at rituals |
| `TOOLING.md` | tool stack setup + adoption timing | when adopting a tool |
| `DASHBOARD.md` | live Dataview tables (opens in Obsidian) | glance anytime |
| `MASTERS-MODULE-PLAN/MENU/MTS-Ground-Truth` + 6 `*-RESOURCES` | module selection + per-axis learning libraries (pre-existing) | module decisions; promotion step 5 |

### Semester system (`semestercontext/` root — current instance)

| Component | What it is | You touch it… |
|---|---|---|
| `HANDOFF.md` → `SEMESTER-STATUS.md` | Semester brain (read order; §0.5 Open Loops!) | every study session |
| `SESSION-LOG.md` | append-only archive | after every session |
| `CHAT-DIVISION.md` | which chat owns which module | opening a chat |
| `LEARNING-RESOURCES.md` | tier 1 — the only material inbox | new find → here, nowhere else |
| `Plans/<domain>/<module>/` | tier 2 — plans, crosswalks + tier-3 unit folders | per the plan |
| `Plans/WIRING.md` | domain↔domain routing (this semester) | cross-domain sessions |
| `lychee.toml` | link-checker config (root, auto-loaded) | rarely |

## §4 The workflows — exactly what to do, when

### W1 · Study a lecture (the core loop, ~weekly)

1. Open the module's chat; check `SEMESTER-STATUS.md` §0.5 Open Loops + priorities.
2. Build/use the lecture's **tier-3 unit** — say *"build the unit for AML L08"* (the `lecture-unit-builder` skill is installed). It reads the slides + crosswalk, checks CONCEPT-INDEX for concepts you already worked (→ "revise via" pointers instead of re-learning), produces the 4 files, adds index rows, updates the plan pointer, runs the validator.
3. Study from the unit's **Mini Plan only** (single-study-script rule). Ultimate Reference = the worked treatment; Exercise Bank + Mock Exam = practice.
4. Append one `SESSION-LOG.md` line; tick step IDs in `SEMESTER-STATUS.md`.

### W2 · Look something up (any time a concept appears — in a lecture, paper, or at work)

Four routes, fastest first: **(a)** `CONCEPT-INDEX.md` — ctrl-F the concept, jump to the worked note; **(b)** `Masters-Planning/DASHBOARD.md` in Obsidian — live tables, edit the concept query; **(c)** Smart Connections pane in Obsidian — semantic "related notes" while reading anything; **(d)** ask a Claude chat — it reads the same index. If the concept isn't indexed but you HAVE worked it: that's a missing row — add it.

### W3 · Weekly hygiene (~10 min)

`lychee --offline .` from the repo root (link rot) · glance at DASHBOARD ("units not at full depth" = build queue) · Open Loops §0.5 sweep. After any restructure additionally: `python3 Masters-Planning/tools/check_system.py`.

### W4 · Semester end → PROMOTION RITUAL (~2–3 h, after exams; next: Aug–Okt 2026)

Run `skills-src/promotion-ritual/SKILL.md` (install it first, or hand it to a chat). It: freezes the semester brain → fills the 6 module cards (grades, artifact paths, retrospective) → adds CONCEPT-INDEX rows + upgrades depth flags → adds DEGREE-WIRING edges → promotes resource finds to the axis files → validator + `lychee .` green. **This is the step that turns a finished semester into permanent, routed knowledge. Never skip it.**

### W5 · Semester start → KICKOFF RITUAL (~1 h; next: WiSe 26/27, then M1)

Run `skills-src/semester-kickoff/SKILL.md`. It clones the proven structure (brain, plans, prefixes) and — the degree-specific move — **wires backwards**: each new module's plan opens with the prerequisite module cards and index rows (*"known content — revise, don't re-learn"*). That is the mechanism by which ML 2-X will seamlessly absorb your AML work and DL1 your MLE→cross-entropy derivation.

### W6 · Found new learning material (30 seconds)

One inbox, one protocol: `LEARNING-RESOURCES.md` **§0 Intake Protocol** — add a one-line entry (type 📒🎥🧪📄🔧 + status + tags + why); free files get downloaded into the owning module's material folder and marked `✓ local` with the path (validator-checked); web-native stays 🌐 (lychee-checked); `⬇️` marks the download queue, swept at each promotion ritual. Never paste a find anywhere else first.

### W0 · Working with Claude (any session)

Fresh semester session: reads `HANDOFF.md` → `SEMESTER-STATUS.md` (project instruction). Masters session: `MASTERS-HANDOFF.md` → `MASTERS-STATUS.md`. Either can navigate everything else from there — that's why registration of new files in the HANDOFF tables matters.

## §5 The invariants (rules that keep it alive — break these and it rots)

1. **One inbox per tier:** material → LEARNING-RESOURCES · worked concept → CONCEPT-INDEX · module edge → DEGREE-WIRING · unresolved action → STATUS §0.5 · finished session → SESSION-LOG. Never a second list of the same thing.
2. **The index points INTO units; it never copies content.** No per-concept files.
3. **Anchor-file rule:** one frontmatter block per unit, on the Ultimate Reference only.
4. **Scope-to-lecture:** units cover the lecture as taught, not the textbook chapter (the ISLP-Ch-7 ≠ L04 lesson).
5. **Single study script:** once a unit exists, its Mini Plan is the only study script for that lecture.
6. **Archive, never delete; no redirect stubs** — fix links, re-run the validator.
7. **Stable IDs:** `<MODULE>-<Semester>` everywhere (`AML-SoSe26`); root-relative backtick paths.
8. **Operational freezes, knowledge promotes** — sync between layers happens only at the rituals.
9. **Tools are lenses.** Delete Obsidian/lychee tomorrow and the system still works in any text editor or chat.
10. **Never invent module data** (Ground-Truth rule) — Moses/AGNES re-check before decisions.

## §6 Metadata quick reference

```yaml
---                              # on: unit anchors, cards, crosswalks, brains…
id: AML-SoSe26-L05               # unique, stable
type: unit | card | crosswalk | bridge | wiring | index | overview | brain | template | skill | plan
module: AML-SoSe26               # owning module (omit if cross-module)
concepts: [logistic-regression, mle, cross-entropy]
depth: full | partial | plan     # = 🟢 | 🟡 | ⚪  (index + dashboard use this)
status: live | stub | frozen
---
```

Added at natural moments only: unit creation (template does it), promotion ritual. Never as a mid-semester chore.

## §7 Commands & tools cheat sheet

| Action | Command / place |
|---|---|
| Validate citations, cards, frontmatter | `python3 Masters-Planning/tools/check_system.py` |
| Check markdown/web links | `lychee --offline .` (weekly) · `lychee .` (ritual) — config auto-loaded from root |
| Live tables | `Masters-Planning/DASHBOARD.md` in Obsidian (Dataview) |
| Graph by domain colors | Obsidian graph view (groups pre-configured) |
| Semantic related-notes | Smart Connections pane (local, offline) |
| Build a lecture unit | ask Claude: "build the unit for <module> L<NN>" (skill installed) |
| Later (deliberate timing) | Anki + MCP after M2 (Exercise Banks → decks) · Zotero + MCP at Masters kickoff (papers layer) |

## §8 Lifecycle from today

| When | What happens |
|---|---|
| **Now → Jul 27** | Exams own everything (mlprov Jul 15 · **AML Rücktritt Jul 15** · M2 Jul 27). System use = W1/W2/W3 only. F.N/AN.X exam prep naturally builds the missing SaD/AN units. |
| **Aug–Okt** | AMLS (Aug 06/27) + AML 30.09 + Algo2 Okt. **First promotion ritual** after the dust settles — fills the 6 cards, upgrades the index. Then: package skills as a plugin (they're proven now), adopt Anki. |
| **WiSe 26/27** | First kickoff ritual (Bachelor Endspurt + Mathe-2). Small semester, good rehearsal. |
| **M1 WiSe 27/28** | The payoff: DBT/HA/MDS/TPS open with AMLS + Algo2 cards — see `DEGREE-WIRING.md` §2. Zotero layer starts. |
| **M5** | Thesis at DEEM — five years of indexed, routed knowledge behind it. |

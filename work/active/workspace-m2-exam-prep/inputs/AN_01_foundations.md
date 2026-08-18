# AN — node plan 1: Foundations and the real numbers

**Node** `knowledge-an-foundations` · **Stage** `stage-m2-analysis-an0`
(210 min, `exam_critical: true`)
**Builds on** — nothing. This is the root of the dependency chain.
**Unlocks** sequences, and through them everything else.

> **The map's own words:** *"Completeness is the load-bearing idea everything
> later rests on."* Every convergence argument in AN.A–AN.G ultimately cashes out
> here. Under-doing this node doesn't cost you marks on this node — it costs them
> four nodes later, where the failure looks like "I can't do epsilon-N."

## Scope

Assumed prerequisites, real-number axioms, order, **completeness**, intervals,
suprema and infima, powers and roots. Script Chapters 1–2.

## Sources — which, at which angle

| When | Source | Angle | Locator |
|---|---|---|---|
| **Spine** | `source-analysis-skript` | The authority. Active pass — definitions, theorem conditions, results | Ch. 1–2 |
| **Practice, first** | `source-analysis-skript` | HU series, this examiner's notation. Before any external bank | `ana_inf_serie05–09`, topic-matched |
| **If set/mapping language is the blocker** | `source-analysis-grundlagen-handouts` | **Prerequisite repair only.** The script assumes set and mapping language without building it; these supply exactly that. **Open the one missing subsection — never read through** | `Mengen-und-Abbildungen.pdf`, `Relationen.pdf`, targeted subsection |
| **If a definition genuinely doesn't make sense** | `source-lebl-basic-analysis` | The free English **text-twin of the script** — closest structural match on the whole menu. Ch. 0–1 map to this node | Ch. 0–1 |
| **Alternative second voice, German** | `source-grieser-analysis1` | "The German Abbott" — heavy motivation, exercises with Hinweise *and* Lösungen, in Klausur vocabulary | topic-matched |
| **Solved drill** | `source-forster-wessoly` | The German solved-exercise standard; per its record, *"the exam points live here"* | topic-matched |
| **Second solved bank, only when Forster is exhausted** | `source-deitmar-uebungsbuch` | Fresh problems, not a second explanation. **Kap. 1–2 → AN.0** | Kap. 1–2 |
| **Repair, hard cap** | `source-mit-18100a` | Full rigour, deliberately more than this exam needs. **Two windows only** and this node is not one of them — L7–L9 is sequences | *not this node* |

**Do not** reach for Abbott here — its chapter map starts at Ch. 2
(sequences/series). Lebl Ch. 0–1 is the structural match for foundations.

## What to produce

1. **A completeness one-pager.** Statement of the completeness axiom, plus the
   two or three places the script immediately uses it. This page gets referenced
   from AN.A, AN.B and AN.C — write it to be reread.
2. **Sup/inf worked set.** Six to eight suprema/infima determined from scratch,
   including at least two where the sup is *not* attained. This is the single
   most common source of quiet errors later.
3. **Ledger entries** for every miss, classified.

## How to self-test

Closed-book, at the end of the 210 minutes:

- [ ] State the completeness axiom from memory, and say what fails without it.
- [ ] Given three sets, determine sup and inf and **say whether each is
      attained** — the "attained" half is the part that gets skipped.
- [ ] State the order axioms you actually used today, without listing all of them.
- [ ] One HU-series subproblem on this material, cold and timed.

**Done when** you can answer "why does this sequence converge?" with a reason
that bottoms out in completeness, rather than in "it obviously does."

## Traps

- **Skimming because it's "just prerequisites."** The map calls completeness
  load-bearing for a reason; this is the node whose weakness surfaces elsewhere.
- **Reading the Grundlagen handouts front to back.** Their route says *open the
  one missing subsection*. If you're reading them linearly you've turned repair
  into a course.
- **Sup/inf on paper only.** Every later criterion (monotone convergence, the
  compactness theorems) leans on the attained/not-attained distinction.
- **Opening MIT 18.100A here.** Its two permitted windows are sequences
  (L7–L9) and L23–L24. Using it for foundations is exactly the "linear second
  course" its route forbids.

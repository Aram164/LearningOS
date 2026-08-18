---
id: note-algo2-stable-matching-viva-drill
type: note
title: "Algo 2 T10 — Viva Drill: Stable Matching"
created: "2026-08-16"
role: mock-exam
state: evolving
authorship: operator-drafted
concepts: [concept-stable-matching]
sources: [source-algo2-hu-materials]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_stablematching.pdf`.
> `role: mock-exam` is the schema's nearest value; **this is an oral drill.**
> Unverified by Aram.

# Algo 2 · Topic 10 — Viva Drill

> 🔑 **The most "explainable" topic in the course** — no heavy machinery, three
> clean proofs, and a memorable punchline. That makes it a likely opener, and a
> likely place for the examiner to check whether you can *prove* rather than
> recite.

---

## A. The five-minute summary

1. The motivating setting: assignment with **preferences on both sides**, where
   self-interest and timing wreck naive procedures.
2. The problem, and — precisely — what **instability** means: a *mutual*
   incentive to deviate.
3. Gale-Shapley (1962), deferred acceptance: men propose down their list, women
   hold and upgrade.
4. Three results: terminates in ≤ `n²`; output is **perfect**; output is
   **stable**.
5. The punchline: **every** execution gives the same matching `S*`, which is
   best-possible for every man and **worst-possible for every woman**.
6. One line: extends to capacities — university places, residency matching.

---

## B. Follow-up trees

**B1. "Was heißt instabil?"** ⚠️ *the definitional question — get it exact*
- → "Reicht es, dass eine Person unzufrieden ist?" → **No**, it takes a *pair* who
  both prefer each other to their assigned partners
- → "Geben Sie ein Beispiel."
- → "Kann ein stabiles Matching alle unglücklich machen?" → yes, easily

**B2. "Beschreiben Sie Gale-Shapley."**
- → "Wer macht die Anträge?" → the men, in the deck's formulation
- → "Was macht eine Frau, die schon verlobt ist?" → compares, keeps the better
- → "In welcher Reihenfolge macht ein Mann Anträge?" → down his list
- → "Was gilt für eine Frau im Verlauf?" → engaged forever after the first
  proposal, partner only improves
- → "Und für einen Mann?" → prospects only worsen

**B3. "Terminiert der Algorithmus?"**
- → "Wie viele Iterationen?" → ≤ `n²`
- → "Warum?" → each iteration is a *new* proposal; there are `n²` possible ones
- → "Ist die Ausgabe ein perfektes Matching?" → yes; if a man were free he'd still
  have someone to propose to, so the loop would continue

**B4. "Beweisen Sie die Stabilität."** ⚠️ *the proof most likely to be requested*
- → assume the instability, derive a contradiction from "her partner only improves"
- → "Wo genau nutzen Sie, dass Männer absteigend anfragen?" → to conclude `m′`
  proposed to `f` *before* `f′`
- → "Wo nutzen Sie, dass Frauen sich nur verbessern?" → to conclude her final
  partner is at least as good as `m′`

**B5. "Hängt das Ergebnis von der Reihenfolge ab?"**
- → **No** — every execution yields `S*`
- → "Was ist `S*`?" → each man with `best(m)`, his best partner over all stable
  matchings
- → "Und für die Frauen?" ⚠️ → each gets her **worst** possible stable partner
- → "Was folgt daraus praktisch?" → **the proposing side wins**; who proposes is a
  policy decision, not a technicality

**B6. "Was, wenn Kapazitäten im Spiel sind?"**
- → universities with `f(u)` places; still always a stable matching
- → "Kennen Sie eine reale Anwendung?" → residency matching, school choice

---

## C. Board work

| # | Draw / write while talking | Target |
|---|---|---|
| C1 | The instability definition, formally | 30 s |
| C2 | Gale-Shapley pseudocode | 45 s |
| C3 | A 3×3 instance and a full run | 120 s |
| C4 | The stability proof | 90 s |
| C5 | The `n²` counting argument | 20 s |

---

## D. Traps

**D1.** *"Instabil heißt, jemand ist unzufrieden?"* — No. It requires **two**
people who both prefer each other over their current partners. Getting this
imprecise is the fastest way to lose the topic.

**D2.** *"Das Ergebnis hängt davon ab, wen man zuerst nimmt?"* — No. The theorem
on sl. 34 says every execution returns `S*`. Non-deterministic schedule,
deterministic outcome.

**D3.** *"Der Algorithmus ist fair?"* — It is **maximally unfair** in a precise
sense: optimal for every proposer, pessimal for every receiver. Saying this
crisply is the strongest single answer in the topic.

**D4.** *"Das ist doch dasselbe wie bipartites Matching?"* — Different problem.
That one maximizes size and ignores preferences; this one is always perfect and
optimizes stability.

**D5.** *"Gibt es immer ein stabiles Matching?"* — For this problem, yes, always —
Gale-Shapley constructs one. (For the non-bipartite *stable roommates* variant it
can fail, but that is outside the deck; do not volunteer a proof.)

**D6.** *"Warum sind die Präferenzlisten vollständig?"* — Because that is what
guarantees a *perfect* matching. With incomplete lists the problem changes.

---

## E. Two-minute version

> "Beim Stable Matching sind zwei gleich große Mengen gegeben, jede Person hat
> eine vollständige Präferenzliste über die andere Menge, und gesucht ist ein
> perfektes Matching ohne Instabilität. Instabil heißt dabei: es gibt ein Paar
> `(f,m)` und `(f′,m′)` im Matching, sodass `f` den `m′` bevorzugt **und**
> gleichzeitig `m′` die `f` bevorzugt — beide hätten also einen Anreiz
> abzuweichen. Gale und Shapley lösen das 1962 mit Deferred Acceptance: freie
> Männer machen Anträge, absteigend entlang ihrer Liste; eine Frau hält den ihr
> liebsten bisherigen Antrag und tauscht, wenn ein besserer kommt. Daraus folgt:
> eine Frau ist ab dem ersten Antrag durchgehend verlobt und verbessert sich nur,
> ein Mann verschlechtert sich nur. Der Algorithmus terminiert nach höchstens
> `n²` Iterationen, weil jede Iteration einen neuen Antrag verbraucht; die Ausgabe
> ist perfekt, denn ein freier Mann hätte noch jemanden zum Anfragen; und sie ist
> stabil — sonst hätte der bevorzugte Mann der Frau früher einen Antrag gemacht,
> und ihr Partner verbessert sich ja nur. Bemerkenswert ist noch: jede Ausführung
> liefert dasselbe Matching, in dem jeder Mann seine bestmögliche und jede Frau
> ihre schlechtestmögliche stabile Partnerin bekommt."

**~95 seconds.**

---
id: note-algo2-amortized-analysis-viva-drill
type: note
title: "Algo 2 T02 — Viva Drill: Amortisierte Analyse"
created: "2026-08-16"
role: mock-exam
state: evolving
authorship: operator-drafted
concepts: [concept-amortized-analysis]
sources: [source-algo2-hu-materials]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_amortizedanalysis.pdf`.
> `role: mock-exam` is the schema's nearest value; **this is an oral drill** —
> 30-minute Zoom viva. Unverified by Aram.

# Algo 2 · Topic 2 — Viva Drill

> 🔑 **Most likely topic to be examined in depth.** It is a *method*, so it can be
> asked about on its own **and** as a follow-up inside Fibonacci heaps or splay
> trees. Budget more drill time here than for any other topic.

---

## A. The five-minute summary

Asked as *"Was ist amortisierte Analyse und wozu braucht man sie?"*

1. The problem: bounding `c(Q)` for a whole sequence; summing per-operation worst
   cases is legal but far too pessimistic, because the expensive cases cannot all
   occur.
2. Three methods, in increasing power: aggregate, accounting, potential.
3. One example carried through — the multipop stack is the cleanest.
4. The potential theorem, its conditions, and what it buys (one function, all
   bounds follow).
5. Where it is used: Fibonacci heaps, splay trees, dynamic arrays.

**Self-check:** did you say the word *deterministic*? If not, you've left the
door open for the average-case trap in §D.

---

## B. Follow-up trees

**B1. "Erklären Sie die Potentialmethode."**
- → "Schreiben Sie die Definition der amortisierten Kosten auf."
- → "Welche Bedingungen braucht die Potentialfunktion?"
  - → "Sind die notwendig oder hinreichend?" ⚠️ *(sl. 36 — the real condition is
    `Φ(D_m) ≥ Φ(D₀)`; the usual pair is sufficient and chosen to work for all
    sequences)*
- → "Geben Sie ein Potential für den Stapel an." → `Φ(S) = |S|`
  - → "Rechnen Sie `d(multipop)` aus." → `ℓ` pops cost `ℓ`, potential drops `ℓ` → `≤ 1`
- → "Und für den Binärzähler?" → number of ones
  - → "Warum genau 2?" → clears `j−1` ones, sets one: `j + (2−j) = 2`

**B2. "Warum reicht es nicht, die Worstcases aufzuaddieren?"**
- → "Geben Sie ein konkretes Beispiel." → multipop: naive `O(m²)`, true `O(m)`
- → "Warum können nicht alle Operationen teuer sein?" → each pop needs a prior push
- → "Ist das ein Durchschnittsargument?" ⚠️ **No** — see §D1

**B3. "Nennen Sie die drei Methoden und ihre Vor- und Nachteile."**
- → "Wann würden Sie Aggregat-Analyse nehmen?" → fixed known sequence, simple ops
- → "Warum ist sie bei komplexen Datenstrukturen schwierig?"
- → "Was macht die Potentialmethode mächtiger?" → one function, bounds follow automatically

**B4. "Rechnen Sie den Binärzähler vor."**
- → "Wie oft kippt Bit `i`?" → every `2^i`-th increment
- → "Schreiben Sie die Summe." → `Σ ⌊m/2^i⌋ < 2m`
- → "Warum taucht `k` im Ergebnis nicht auf?"

**B5. "Account-Methode am Stapel."**
- → "Ihre fiktiven Kosten?" → 2 / 1 / 1
- → "Wie beweisen Sie `d(Q) ≥ c(Q)`?" → induction over `m`
- → "Die naive Hypothese scheitert — warum?" ⚠️ *(sl. 19, the `Fehlversuch`)*
- → "Was ist die richtige Hypothese?" → `d(Q) ≥ c(Q) + |S|`
  - → "Was bedeutet der Term `|S|` inhaltlich?" → one unit of credit per stacked
    element, precisely what a later multipop spends

---

## C. Board derivations

| # | Write while talking | Target |
|---|---|---|
| C1 | `d(q) = c(q) + Φ(D″) − Φ(D′)` | 15 s |
| C2 | The potential theorem with both conditions | 30 s |
| C3 | `Σ_{i=0}^{k−1} ⌊m/2^i⌋ < 2m` | 30 s |
| C4 | The three stack costs, actual and fictitious | 30 s |
| C5 | `d(Q) = Φ(D_m) − Φ(D₀) + c(Q)` and the iff | 45 s |
| C6 | Amortized costs of all three stack ops under `Φ = |S|` | 60 s |

---

## D. Traps

**D1.** *"Amortisierte Analyse ist also eine Art Durchschnittsanalyse?"* —
**No, and do not soften this.** It is a deterministic worst-case bound over a
sequence. No probability distribution, no randomization, no assumption about
inputs; the guarantee holds for *every* sequence. (Contrast: cuckoo hashing's
bounds in T06 genuinely *are* probabilistic. The course teaches both, and the
examiner may well probe whether you can tell them apart.)

**D2.** *"Ein Splay-Tree-Zugriff kann `Θ(n)` kosten — also stimmt `O(log n)`
nicht?"* — Both are true. The `O(log n)` is **amortized**; individual operations
may be linear. State it that way, unprompted.

**D3.** *"Im Cormen stehen andere fiktive Kosten."* — Correct, and the deck says
so explicitly on sl. 18 (*"Achtung: Hier weichen wir vom Buch ab"*). Give the
deck's, and mention you know the book differs. That reads as having read both.

**D4.** *"Die Potentialfunktion muss doch nur `Φ(D₀) = 0` erfüllen?"* — That is
half of it; you also need `Φ(Dᵢ) ≥ 0`. And both together are *sufficient*, not
necessary — the exact condition is `Φ(D_m) ≥ Φ(D₀)`.

**D5.** *"Können amortisierte Kosten kleiner als die tatsächlichen sein?"* —
Yes, and that is the whole point: potential can fall. `multipop` is the example.

---

## E. Two-minute version

> "Bei Datenstrukturen interessiert die Gesamtkosten `c(Q)` einer Folge von
> Operationen. Die Summe der Einzel-Worstcases ist zwar eine korrekte Schranke,
> aber oft viel zu pessimistisch — beim Stapel mit Multipop etwa `O(m²)`, obwohl
> tatsächlich `O(m)` gilt, denn jedes Pop braucht ein früheres Push. Drei
> Methoden: Aggregat-Analyse beweist die Gesamtschranke direkt; die
> Account-Methode setzt fiktive Kosten an und zeigt, dass das Konto nie negativ
> wird; die Potentialmethode definiert eine Potentialfunktion auf den Zuständen
> und setzt `d(q) = c(q) + ΔΦ`. Gilt `Φ(D₀) = 0` und `Φ ≥ 0`, ist die Summe der
> amortisierten Kosten eine obere Schranke. Wichtig: das ist keine
> Durchschnittsanalyse, sondern deterministisch für jede Folge. Angewendet wird
> es vor allem bei Fibonacci-Heaps, Splay-Bäumen und dynamischen Arrays."

**~65 seconds.** Learn verbatim.

---

## F. Method-transfer drill

The examiner's favourite move on a *method* topic is **"und jetzt mit einer
anderen Methode."** Practise all six cells:

| | Aggregate | Accounting | Potential |
|---|---|---|---|
| **Stack + multipop** | ☐ | ☐ | ☐ |
| **`k`-bit counter** | ☐ | ☐ | ☐ |

Tick a cell only when you can deliver it **aloud, cold, in under 90 seconds**.
Six ticks is the completion criterion for this topic — it is exactly the deck's
own structure, and it makes you method-agnostic under questioning.

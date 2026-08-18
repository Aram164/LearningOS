---
id: note-algo2-fast-multiplication-viva-drill
type: note
title: "Algo 2 T01 — Viva Drill: Schnellere Multiplikation"
created: "2026-08-16"
role: mock-exam
state: evolving
authorship: operator-drafted
concepts: [concept-fast-multiplication, concept-recurrences-master-theorem]
sources: [source-algo2-hu-materials]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_fastmultiplication.pdf`.
> **`role: mock-exam` is the schema's nearest value; the artifact is an oral drill**
> — Algo 2 is examined as a 30-minute Zoom viva, not a written Klausur. Difficulty
> at or above the real exam by design. Unverified by Aram.

# Algo 2 · Topic 1 — Viva Drill

**Format being rehearsed:** 30 min oral, Zoom, by arrangement. Twelve topics in
30 minutes means **roughly two minutes per topic if everything is touched** — so
in practice the examiner picks a few and goes deep. Both modes are drilled here.

**How to use:** speak every answer **out loud**, standing, without notes. Time
yourself. Reading these silently trains the wrong skill — see Phase 0.9.

---

## A. The five-minute summary

Deliver this cold, timed, as if asked *"Erzählen Sie mir von der schnelleren
Multiplikation."*

**Target shape (aim for 4–5 min):**

1. The problem and the baseline — school method, `< 3n²`, **and tight**.
2. The recursive rewrite — the split, four multiplications, and the honest
   admission that this alone gains nothing.
3. Karatsuba's trick — the identity, and *three* not five.
4. The recurrences side by side, and the sentence **"entscheidend ist 3 vs. 4."**
5. The master theorem, `d = log₂3`, and `O(n^{log₂3})`.
6. One sentence of Ausblick: Toom-k, and that the FFT lecture returns to this
   problem.

**Self-check:** did you say *why* the additions don't matter? Most summaries skip
it, and it is the step that makes the improvement legitimate.

---

## B. Opening questions and their follow-up trees

Each root is a plausible opener. The indented lines are what a good examiner asks
**next** — that is where vivas are actually won or lost.

**B1. "Warum ist Karatsuba schneller als die Schulmethode?"**
- → "Wie viele Multiplikationen genau, und warum nicht fünf?"
  - → "Zeigen Sie die Identität." *(be ready to write it)*
  - → "Verifizieren Sie den mittleren Term algebraisch."
- → "Und die Additionen? Die sind doch mehr geworden."
  - → "Warum spielt das asymptotisch keine Rolle?"
- → "Wie kommen Sie von der Rekurrenz auf die Schranke?"
  - → "Nennen Sie das Mastertheorem." *(Phase 0.2 territory)*
  - → "Welcher Fall ist das?"

**B2. "Schreiben Sie die Rekurrenz der rekursiven Schulmethode auf."**
- → "Und die von Karatsuba?"
- → "Was ist der einzige relevante Unterschied?" *(answer: the factor, 3 vs 4)*
- → "Wenn ich `4n` auf `100n` erhöhe — ändert sich die Schranke?" *(no)*
- → "Wenn ich den Faktor auf 2 senken könnte — was käme heraus?"
  *(`Θ(n)`, since `log₂2 = 1`; note this is not achievable this way)*

**B3. "Was kostet die Addition zweier `n`-ziffriger Zahlen?"**
- → "Und die Multiplikation mit einer einziffrigen Zahl?"
- → "Warum ist die Addition die richtige Vergleichsgröße?"

**B4. "Geht es noch schneller als Karatsuba?"**
- → "Toom-k — was ist die Idee?"
- → "Warum wird es mit wachsendem `k` nicht beliebig gut?"
- → "Kennen Sie einen ganz anderen Ansatz?" *(FFT — topic 12; say the
  connection, don't improvise the algorithm here)*

---

## C. Board derivations — be able to write these while talking

| # | Write | Talk-through target |
|---|---|---|
| C1 | The split `a = a₁B^k + a₀`, `b = b₁B^k + b₀` | 20 s |
| C2 | The four-multiplication expansion | 30 s |
| C3 | Karatsuba's identity | 45 s |
| C4 | Both recurrences, stacked | 30 s |
| C5 | Master theorem statement | 45 s |
| C6 | `a = 3, b = 2, d = log₂3` → the bound | 30 s |

**Drill method:** write each while narrating. If the writing stops when the
talking starts, it isn't automatic yet.

---

## D. Traps the examiner can set

**D1.** *"Karatsuba braucht fünf Multiplikationen, oder?"* — No. Apparently five,
actually three; `a₁b₁` and `a₀b₀` are each reused. **Do not agree to be polite.**

**D2.** *"Die Schulmethode ist doch `O(n²)` — also könnte sie auch `O(n log n)`
sein?"* — `O` is an upper bound, but the deck states the method also does not use
essentially fewer than `3n²`. The bound is tight; `Θ(n²)`.

**D3.** *"`log₂3`, das ist ungefähr 1,58 — woher kommt die Zahl?"* — From
`d = log_b a` with `a = 3`, `b = 2`. If you can only recite `1.585`, the examiner
knows immediately.

**D4.** *"Ist die Konstante 153 wichtig?"* — It is in the theorem and it is
large; asymptotic superiority only pays off above a crossover point. Saying this
unprompted reads as understanding rather than recall.

**D5.** *"Warum haben Sie überhaupt rekursiv umgeschrieben, wenn es nichts
bringt?"* — Because the rewrite is what exposes the branching factor as the
tunable quantity. The recursion is the *setup*; Karatsuba is the payoff.

---

## E. Two-minute version

For when the examiner is sampling breadth:

> "Schulmethode braucht `Θ(n²)`, genauer weniger als `3n²` Elementaroperationen,
> und das ist scharf. Schreibt man sie rekursiv mit `a = a₁B^k + a₀`, bekommt man
> vier Multiplikationen halber Länge — also `4T(n/2) + O(n)`, weiterhin `Θ(n²)`.
> Karatsuba nutzt `(a₁+a₀)(b₁+b₀)`, um den mittleren Term aus den beiden anderen
> Produkten zu gewinnen: drei statt vier Multiplikationen, sechs Additionen.
> Die Additionen sind asymptotisch irrelevant, entscheidend ist der Faktor 3
> statt 4. Mit dem Mastertheorem, `a = 3`, `b = 2`, `d = log₂3`, folgt
> `O(n^{log₂3})`, also etwa `n^{1,58}`."

**~50 seconds spoken.** Learn this one verbatim — it is the highest-value 50
seconds in the topic.

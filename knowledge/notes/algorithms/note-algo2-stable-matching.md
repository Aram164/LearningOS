---
id: note-algo2-stable-matching
type: note
title: "Algo 2 T10 — Reference: Stable Matching (Gale-Shapley)"
created: "2026-08-16"
role: reference
state: evolving
authorship: operator-drafted
concepts: [concept-stable-matching, concept-bipartite-matching]
sources: [source-algo2-hu-materials, source-kleinberg-tardos]
contexts: [workspace-algo2-exam-prep]
---

> **Build note (2026-08-16).** Operator-drafted from `ad2_stablematching.pdf`
> (42 sl.). Companions: `-exercise-bank`, `-viva-drill`. Not yet worked by Aram.

# Algo 2 · Topic 10 — Stable Matching

*Lectures: 22. Juni `[1-36]`, 29. Juni `[37-end]`.*
***Literatur:** Kleinberg & Tardos, *Algorithm Design*, Abschnitt 1.1 — held
locally. **Leseempfehlung:** Cseh 2017, "Popular Matchings".*

**Agenda (sl. 2):** application/motivation · the stable matching problem ·
**Gale-Shapley** · analysis · further properties.

> ⚠️ **A different problem from T09**, despite the adjacency. Bipartite matching
> maximizes **cardinality**; stable matching always produces a **perfect**
> matching and optimizes for **stability against preferences**.

---

## 1. Motivation (sl. 4–8)

**Job placement (sl. 4).** Firms advertise posts; applicants apply; offers and
acceptances happen over time.

**What goes wrong (sl. 5)** — self-interest plus timing: an applicant accepts,
then gets a better offer and reneges; a firm makes an offer, then finds a better
candidate and withdraws it.

**Attempted fix (sl. 6):** strict rules — offers and acceptances are binding. But
the real question (sl. 7) is whether a configuration exists in which **neither
side has an incentive to deviate**.

**Formally (sl. 8):** given two sets with **preferences over each other**, find an
assignment that is stable in that sense.

---

## 2. The problem (sl. 10–14)

**Simplification (sl. 10):** the deck uses the classical symmetric form — pairs
drawn from two equal-sized sets — which generalizes.

> **Stable Matching Problem (sl. 11).**
> **Input:** sets `F = {f₁,…,f_n}` and `M = {m₁,…,m_n}`; for each `f ∈ F` a
> **complete preference order** over `M`, and for each `m ∈ M` one over `F`.
> **Output:** a perfect matching `S` that is **stable**.
>
> **Instability.** `S` is unstable if there are `(f,m), (f′,m′) ∈ S` such that
> `f` prefers `m′` over `m` **and** `m′` prefers `f` over `f′`. Such a pair would
> abandon their assigned partners. `S` is **stable** if no such pair exists.

**Example 1 (sl. 12).** `f` and `f′` both prefer `m` over `m′`; `m` and `m′` both
prefer `f` over `f′`. There is still a stable matching — agreement on rankings does
not by itself create instability.

**Example 2 (sl. 13).** Preferences "cross over" (`f` prefers `m′`, `f′` prefers
`m`, `m` prefers `f`, `m′` prefers `f′`), producing a different structure —
returned to in §4 to show what Gale-Shapley does with it.

> **The two questions (sl. 14):** under what conditions does a stable matching
> **exist**, and can we find one **efficiently**? The lecture answers: always, and
> yes.

---

## 3. Gale-Shapley (sl. 16–20)

Published 1962 by David Gale and Lloyd Shapley; also known as **deferred
acceptance**.

**Ideas (sl. 17–18).** Start with no pairs. One group — say the men — **proposes**.
A free woman receiving her first proposal becomes engaged. An engaged woman who
receives a further proposal compares the two and keeps the one she prefers,
freeing the other. Men propose **down their own list**, in order.

```
Gale-Shapley:
1  set all women and men free
2  while there is a free man m who has not yet proposed to every woman do
3      let f be the highest-ranked woman on m's list to whom he has not proposed
4      if f is free then engage (f, m)
5      else let m' be f's current partner
6          if f prefers m over m' then engage (f, m); set m' free
7          else f rejects m
8  return the set of engaged pairs
```

**Comment (sl. 20):** the description is simple; that it terminates *and* returns
a **stable** matching is not obvious and is exactly what §4 establishes.

---

## 4. Analysis (sl. 22–30)

**From a woman's perspective (sl. 23):** `f` is free until her first proposal;
**from then on she is always engaged**, and her partner only ever **improves**.

**From a man's perspective (sl. 24):** `m` becomes engaged only by proposing, and
his proposals move **monotonically down** his preference list — so his prospects
only ever worsen.

> **Lemma (sl. 25).** The algorithm terminates after at most **`n²`** iterations
> of the while-loop.
>
> **Proof:** each iteration issues a proposal that has never been made before;
> there are `n` men with `n` women each, so at most `n²` proposals exist.

> **Lemma (sl. 26).** If a man is free at some point, there is at least one woman
> he has not yet proposed to.
>
> Otherwise all `n` women would be engaged — and since engagements pair distinct
> men, all `n` men would be too, contradicting that `m` is free.

> **Lemma (sl. 27).** The output `S` is a **perfect matching**.
>
> It is a matching since each person has at most one partner; on termination no
> man is free (by the previous lemma the loop could otherwise continue), so all
> `n` men and hence all `n` women are matched.

> **Theorem (sl. 28–29).** The output `S` is **stable**.
>
> **Proof.** Suppose `(f,m), (f′,m′) ∈ S` with `f` preferring `m′` over `m`, and
> `m′` preferring `f` over `f′`. Since `m′` prefers `f` and proposes in decreasing
> order, he proposed to `f` **before** `f′`. At that moment `f` either accepted or
> already had someone she preferred. Either way, from then on `f`'s partner only
> improves — so her final partner `m` is at least as good as `m′`, contradicting
> that she prefers `m′`. ∎

**Summary (sl. 30):** always a stable matching, in at most `n²` iterations.
*Frage/Übung* posed there for the reader.

---

## 5. Further properties — fairness (sl. 32–39)

**What does GS do to Example 2 (sl. 32)?** The men get their preferred outcome.

**Observation (sl. 33):** generalize it — if the `n` men have **distinct** women
at rank one, they all get their first choice, whatever the women want.

> **Theorem (sl. 34–37).** Let `best(m)` be the best partner `m` has in **any**
> stable matching, and `S* = {(best(m), m) : m ∈ M}`. **Every execution of
> Gale-Shapley yields `S*`.**
>
> In particular the result is **independent of the order in which free men are
> chosen** in line 3 — the algorithm is deterministic in its output despite being
> non-deterministic in its schedule. And it is **men-optimal**.
>
> **Proof idea (sl. 36–37):** suppose some execution `A` produces a matching in
> which a man is not paired with his best possible partner. Consider the first
> moment in `A` at which some man `m` is rejected by his best possible partner
> `f`. Then `f` prefers whoever she holds; combining this with a stable matching in
> which `(f,m)` occurs yields an instability there — contradiction.

> **Korollar (sl. 38–39).** In `S*`, **every woman is paired with her worst
> possible partner** — the worst over all stable matchings.
>
> **Proof:** suppose `(f,m) ∈ S*` and some stable matching `S′` gives `f` a partner
> `m′` she likes *less*. Using men-optimality of `S*`, one constructs an
> instability in `S′`.

> 🎯 **The proposing side wins, completely.** That single fact is the most
> memorable content in the lecture and the most likely thing to be asked about.

---

## 6. Überblick and Ausblick (sl. 41–42)

**Überblick.** Stable matching is prototypical for **assignment problems with
preferences**; a stable matching always exists; Gale-Shapley finds one in `O(n²)`;
the outcome is optimal for the proposing side and pessimal for the other.

**Ausblick (sl. 42).** The generalization to **allocating university places** —
universities have capacities — also always has a stable matching. *(This is the
real-world deployment: medical residency matching and school choice both run
deferred acceptance.)*

---

## 7. Exam-critical minimum

| Must be automatic | Where |
|---|---|
| The problem statement with complete preference lists | sl. 11 |
| **The definition of instability**, stated precisely | sl. 11 |
| Gale-Shapley pseudocode | sl. 19 |
| Women: engaged forever after the first proposal, partners improve | sl. 23 |
| Men: proposals move monotonically down the list | sl. 24 |
| Termination in ≤ `n²` iterations, with the proposal-counting argument | sl. 25 |
| Output is a perfect matching | sl. 26–27 |
| **Stability proof** | sl. 28–29 |
| `S* = {(best(m), m)}`, and that **every** execution yields it | sl. 34–35 |
| **Corollary: every woman gets her worst stable partner** | sl. 38–39 |
| Extension to capacities (university places) | sl. 42 |

**Traps:** stating instability as "someone is unhappy" — it requires a **mutual**
preference to deviate; claiming the outcome depends on the processing order (it
does not); confusing this with T09's bipartite matching; forgetting that
preference lists are **complete**, which is what makes the perfect matching
possible.

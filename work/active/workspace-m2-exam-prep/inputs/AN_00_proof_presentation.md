# AN — node plan 0: Proof reading and presentation

**Node** `knowledge-an-proof-presentation` · **Stage** `stage-m2-analysis-calibrate`
(60 min, `exam_critical: true`, currently `pending` — this is the unstarted first
stage of the whole Analysis track)
**Builds on** `knowledge-an-foundations` (nominally — in practice run it *first*,
because it sets the depth for everything after)

> **This is a skill, not a chapter.** It runs alongside all nine other nodes. The
> 60 minutes here are setup; the actual practice happens every time you write a
> solution for AN.0–AN.G.

## The one thing this node decides

**How deep to go on proofs.** The script's course contract (pp. iv–vii) says
proofs need **not** be memorized — definitions, theorem conditions/results, and
application carry the exam. Every hour you would have spent memorizing proofs is
an hour that belongs to AN.X. Getting this calibration wrong in either direction
is the most expensive mistake available in this track:

- too deep → you run out of time before AN.X and arrive at a combined Klausur
  having never done mixed practice;
- too shallow → you cannot justify a step when the exam asks *why*, and you lose
  the theorem-condition marks that are the cheapest on the paper.

## Sources — which, at which angle

| When | Source | Angle | Locator |
|---|---|---|---|
| **Start here** | `source-analysis-skript` | The course contract *is* the scope boundary. Read pp. iv–x and the contents pp. ii–iii as a **triage instrument**, not as an introduction | `unser skript.pdf` printed pp. iv–x, contents pp. ii–iii (PDF pp. 2–10) |
| **Immediately after** | `source-analysis-skript` | The tutor's proof-list disclaimer. Treat as a **repair list, not an exam prediction** | `kleine_beweise.pdf`, both pages |
| **Cold sample** | `source-analysis-skript` | The only tasks calibrated to this examiner. One subproblem, before studying anything | `ana_inf_serieWV.pdf`, one of WV1.1–WV1.4 |
| **On a diagnosed presentation error only** | `source-ableitinger-musterloesungen` | Model solutions as **writing samples, not answers** — what a marker expects a correct proof to *look like on paper*. One example, matched to the specific error | one matching example |
| **If a correct write-up in the script's vocabulary is what's missing** | `source-fritzsche-trainingsbuch` | German drill with the **solution reasoning written out**, not just answers | Kap. 1–4, topic-matched |
| **Unevaluated — do not open casually** | `source-velleman-how-to-prove-it`, `source-ohlbach-eisinger-beweise` | Both are routed here and both carry **no registered evaluation**. They are the obvious-looking "learn to prove" picks and that is exactly why they are a trap: no one has assessed whether they match this script's depth. If you do open one, **repay the visibility debt** with a one-line evaluation stub | establish on first use |

## What to produce

1. **The error ledger** — the artifact this whole track runs on. Five classes:
   `definition · theorem-condition · method-choice · algebra · time`. Create it
   here, from the cold WV sample, and **never restart it.** It accumulates across
   all ten nodes and becomes the specification for AN.X's mocks.
2. **A written scope statement, from memory**, of how Wiederholung / Ausflug /
   Exkurs change study priority. Three lines. If you cannot write them without
   looking, the calibration hasn't happened.
3. **A proof-depth rule in one sentence**, in your own words, that you will apply
   for the next 46 hours.

## How to self-test

The stage's own `done_when`, unchanged:

- [ ] Explain from memory how **Wiederholung** (required), **Ausflug**
      (exam-light application context) and **Exkurs** (not exam-relevant) change
      study priority.
- [ ] Record that the script prioritizes definitions, theorem
      assumptions/results, and application; proofs serve understanding and are
      not memorized by default.
- [ ] Read the `kleine_beweise.pdf` disclaimer and treat it as a repair list.
- [ ] Complete one 20-minute cold sample from `ana_inf_serieWV.pdf` and start the
      error ledger.

## Traps

- **Treating `kleine_beweise.pdf` as a prediction of what's on the exam.** It is
  a list of proofs a tutor thought worth doing. The script's contract outranks it.
- **Starting the ledger "properly later."** The first entries come from a cold
  sample precisely because you haven't studied yet — that's the calibration
  signal, and it is unrepeatable.
- **Reading Velleman cover to cover.** It's a whole book on proof technique for
  an exam that says proofs need not be memorized. If you're reaching for it, ask
  what specific write-up failed first.

## Runs alongside

Every node. When a solution is *correct but you're unsure it would earn full
marks*, that is this node, not the topic node — one Ableitinger example, matched
to that error, then back.

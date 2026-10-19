# Routing the kleine Beweise — coverage audit, 2026-09-12

Plan package: `LearningOS/workbench/audits/kleine-beweise-routing-2026-09-12/repair.yaml`

## What prompted this, and a correction

Earlier today I scouted video coverage for the twenty results in
`material://source-analysis-skript/kleine_beweise.pdf` and reported
`source-mit-18100a` as covering **9 of 20**. That number was wrong. It came from
matching the OCW **lecture titles** against the handout, which is not evidence
about content — and it contradicted the source record's own strengths note,
which already said L17+L19 carry "derivative (rules+Rolle+MVT)".

Reading the notes instead gives **17 of 20**, each a numbered theorem with a
written proof on a nameable page. Two of the three misses were also artifacts of
that first pass: they disappeared once the PDF's `ﬀ`/`′` ligatures were
normalised before searching.

## Local — MIT 18.100A lecture notes

`material://source-mit-18100a/mit18_100af20_lec_full2.pdf`, 92 pp, opened
2026-09-12. Every row below was located by extracting the page text, normalising
ligatures, and reading the theorem statement — not by keyword proximity.

| Handout result | MIT | Lecture | PDF page |
|---|---|---|---|
| Lemma 3.21, second half (convergent ⇒ bounded) | Theorem 72 | L7 | 24 |
| Satz 3.30 (Monotonieprinzip) | Theorem 75/76, as an *iff* | L7 | 25 |
| Satz 3.40 (Teilfolgenkriterium) | Theorem 79 | L7 | 26 |
| Satz 3.25 (Grenzwertsätze) | Theorem 89 | L8 | 28 |
| Satz 3.42 (Cauchy ⇒ beschränkt) | Theorem 110 | L10 | 35 |
| Satz 3.43 (Cauchy-Kriterium) | Theorem 112 | L10 | 36 |
| Satz 4.12 (Majorantenkriterium) | Theorem 135 (Comparison Test) | L11 | 41 |
| Satz 4.15 (Wurzelkriterium) | Theorem 142 (Root test) | L12 | 44 |
| Lemma 5.3 (Häufungspunkte ⇔ Folge) | Theorem 149 | L13 | 47 |
| Satz 5.20 (Rechenregeln stetiger Fkt.) | Theorem 174 | L15 | 54 |
| Lemma 6.3 (diffbar ⇒ stetig) | Theorem 202 | L18 | 62 |
| Satz 6.4 (Rechenregeln der Differenziation) | Theorem 212 | L19 | 65 |
| Lemma 6.11 (f′(x₀)=0 notwendig) | Theorem 215 | L19 | 66 |
| Korollar 6.13 (Rolle) | Theorem 216 | L19 | 67 |
| Korollar 6.14 (f′≡0 ⇒ konstant) | Theorem 220 | L19 | 68 |
| Satz 6.15 (Monotonie ⇔ f′) | Theorem 221, as an *iff* | L19 | 68 |
| Satz 7.20 (Partielle Integration) | Theorem 252 | L22 | 79 |

**Three genuine misses**, each checked against the whole document, not one page:

- **Lemma 3.21, first half** — uniqueness of the limit is never stated. The only
  occurrences of "unique" in 92 pages are the notation key (p. 3) and the
  definition of a function (p. 7).
- **Satz 5.21** — continuity of a composition is *used* but never stated as a
  result.
- **Satz 7.24** — the Mittelwertsatz der Integralrechnung is not a theorem here;
  the differential MVT is applied inside the FTC proof on p. 78 instead.

The five MIT routes on ch03–ch07 gain these theorem numbers and pages. Their
`covers` edges are untouched, so no lineage claim is raised for them.

## Linked — two new sources, registered before this package

Both records were written into `sources/registry/mathematics.yaml` first, with
their evaluations, and validate clean. Playlist contents, video titles, ids and
durations were read from YouTube on 2026-09-12 with `yt-dlp --flat-playlist`;
each video was matched to a handout result **by its own stated title**, never by
topic guess.

| Source | Language | Shape | Handout coverage |
|---|---|---|---|
| `source-henning-dierks` | German | one named result per video, 4–27 min, ten Analysis 1 playlists | 18 / 20 |
| `source-wrath-of-math` | English | one theorem per video, 3–10 min, 105-video Real Analysis playlist | 13 / 20 |

Eight new routes, each raising one lineage claim:

- **Dierks on ch03–ch07** (five routes). ch06 is the one that earns the source:
  all six of that chapter's proofs get a video each, three titled "Beweis", where
  no other video source proves more than one. ch07 carries the only titled proof
  of Satz 7.24 found anywhere.
- **Wrath of Math on ch03, ch05, ch06** (three routes). ch03 exists for two
  specific rows — Satz 3.42 at 5:33 and Satz 3.40 at 8:54, neither of which any
  other source proves on its own. The ch06 route is deliberately recorded as
  covering **only** Rolle, and says so, so the boundary is explicit rather than
  rediscovered later.

No Wrath of Math route on ch04 or ch07: its Real Analysis playlist has neither
series test and no integration-by-parts proof, so a route there would claim
coverage it does not have.

## Explicitly not routed

`source-professor-leonard` keeps its existing first-exposure routes and gains
nothing here. The earlier scout inferred this from a video title, which was not
good enough; it is now recorded on his own words, from captions fetched
2026-09-12:

- Rolle/MVT (`qW89xdGfSzw`): *"I'm going to give you a rundown of Rolle's theorem
  in about a minute … So, it's just a concept."*
- Product and quotient rules (`AvCQQ3X4Nuc`): *"if you want the proof of this
  come and see me … I usually will prove the things but I'm not going to prove
  the quotient rule, the product rule for you."*

That last clause is worth keeping: he does prove elsewhere, which is why his
intuition and first-exposure role is unchanged. He is simply not a route for
these twenty.

`source-brightsideofmaths` was scouted and covers 10/20 at 6–12 min, but it is
strictly redundant against Dierks plus the MIT notes and adds a third language
register for no new result. Not registered; revisit only if Dierks is ever
unavailable.

## Still unresolved

- **Satz 7.24 has a single source.** One German video, no second opinion, and
  the MIT notes do not state it. If that video disappears the row has nothing.
- **No transcripts yet for either new source.** The routes address videos by id,
  title and duration, which is exact, but not by timestamp the way the 3b1b rows
  now are. `tools/ingest_transcript.py` would close that; both records carry the
  playlist URLs it needs.
- ch06 and ch07 still have no current HU practice at all. Unchanged, and still
  the larger gap than any of this.

## Completeness

- [x] Every MIT row located by reading the theorem statement in the notes, ligatures normalised first.
- [x] Every miss verified against the whole document, not a single page.
- [x] Every video matched by its own stated title; ids and durations read from the live listing.
- [x] Both new source records registered with evaluations, and validated, before routing.
- [x] Every new covers edge carries lineage evidence naming locator text, the playlist URL and the handout.
- [x] Every new covers edge names an existing knowledge node.
- [x] A source excluded on evidence is recorded with that evidence, including what it argues against.
- [x] Inlined stage copies in ch03–ch07 re-synchronised to the sharpened MIT routes.

No claim of mastery or readiness is made anywhere in this document.

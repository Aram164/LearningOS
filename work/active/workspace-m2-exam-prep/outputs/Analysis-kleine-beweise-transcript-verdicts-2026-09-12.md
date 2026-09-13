# Routing the kleine Beweise — transcript verdicts, 2026-09-12

Sequel to `Analysis-kleine-beweise-routing-2026-09-12.md` (v1). v1 matched
videos to the twenty handout rows by title; this pass opened every mapped
video's captions and checked the proof is actually in it.

Workbench: `LearningOS/workbench/audits/kleine-beweise-transcripts-2026-09-12/`
(`proof-set.json`, `verdicts-ledger.json` with 49 rows, `VERIFY-PROTOCOL.md`).
Vehicle for the resulting route-text corrections is `route.patch` per route
(structure, order, and coverage are untouched, so no module import). Transcripts
live under `materials/mathematics/analysis/<source>/transcript/` and are
checksummed by `make inventory` (1517 files).

## What changed since v1, and three corrections

**Overturn 1 — `#05-22` proves nothing (Satz 3.49).** `W-MN5CDs23E` asserts the
determinate-divergence rules without a K-N0 argument and spends its bulk proving
indeterminacy instead — a different statement. The ch03-Dierks route text that
calls it "the one that matters most" and "proved nowhere else" is wrong twice
over: the video proves nothing, and nothing else proves it either (see 3.49).

**Overturn 2 — `#07-03` proves neither of its rows.** `-WFcUvR2Qdc` states the
subsequence direction as "irgendwie klar" with zero eps-N0 argument (3.40), and
defines only the Folgen-Haeufungspunkt, never the Mengen version Lemma 5.3 asks
for. Both rows survive via Wrath (`0oRN_pxq2IM`, `RmsvftFNMtE`, each PROVES).

**Overturn 3 — MIT covers 16 of 20, not 17.** v1's table has 17 rows but Satz
3.49 is not among them and is not in the misses either. Full-text search of the
92-page notes finds no determinate-divergence arithmetic (divergence is defined
only as negation of convergence), so 3.49 is a fourth genuine MIT miss — and
with the video overturn it has zero verified coverage anywhere.

**Leonard quote, precise form.** He refuses the quotient proof and defers the
product proof to the book (`AvCQQ3X4Nuc` [05:30], [20:30], [38:30]); the video
itself proves neither — one example-verification is explicitly disclaimed as
"kein Beweis" [08:30]. The exclusion holds; the route text naming is corrected.

## Local — MIT notes, re-checked

`material://source-mit-18100a/mit18_100af20_lec_full2.pdf`, full-text search.
Stands: the 17 v1 rows minus nothing, plus the correction above — 16 verified
rows; misses are 3.21a (uniqueness), 3.49 (no determinate arithmetic), 5.21
(composition never stated), 7.24 (integral MVT never stated).

## Linked — verified video coverage per row

Spans are `[mm:ss]` windows in the managed transcripts. Joint means several
videos together cover the row; each listed video is PROVES unless marked.

- 3.21a Dierks `65bMgATj_cg` [02:00–03:30 +]; Wrath `1xsIpCa961w` has no captions
  at all — title only, watch pending.
- 3.21b Dierks `uomK6mgdUTI`, Wrath `7N-4XZlxBho` [00:00–05:00].
- 3.25 Dierks joint (`ZlAt8sMMfks` sum+scalar, `2XTBBHI9ODE` product,
  `SSghzbB6154` quotient — each PARTIAL alone, full jointly); Wrath one per law
  (`Max7ZPWnV1Q`, `ZlAT0_W4yP0`, `Zvy860EOlVk`, `W3EWjNSoxqE`, `wBNKbQ-xNiw`).
- 3.30 Dierks `baGiNGdvKXM` (incl. (ii)), Wrath `4NURDmE79VU` (incl. (ii)).
- 3.40 Wrath `0oRN_pxq2IM` [00:30–08:00] — now the only video carrier.
- 3.42 row covered by MIT Thm 110 only. Wrath `GulH7nS_65c` (5:33, the only
  standalone video anywhere) is caption-unverifiable: the English ASR itself is
  broken at source. Title only, watch pending — do not cite as carrier.
- 3.43 Dierks `_QjL5Bu1DHg` (both directions, own route); Wrath joint
  (`SubZMuVBajM` =>, `xhBfPoSjAR0` <=); the 24-min iff video `1h_CErk0NFs` is
  ASR-broken, watch pending.
- 3.49 no verified coverage anywhere (MIT miss; Dierks disqualified; Wrath and
  Brightside have no video). The exam gap that matters most from this pass.
- 4.12 Dierks `mvOTUcTF1qk` (+ Minoranten `FV1mUh2UKw8` as proved corollary,
  Beispiel `tGogdahDqeg` as drill, correctly framed).
- 4.15 Dierks `1otGChJnFbA` (both halves); Brightside `yLbgdL9HAeg` PARTIAL
  (q-forms proved, limsup form asserted) — backup only.
- 5.3 Wrath `RmsvftFNMtE` [05:30–10:00] — now the only video carrier.
- 5.20 Dierks `y1J-27SqDS0` (via Satz 3.25, the handout's route); Wrath
  `Sbk-DDhuEvc` (via functional limit laws — same result, different road).
- 5.21 Dierks `kSqVzSClJD4` [04:30–14:30], Wrath `-n4cnyDkd6A`.
- 6.3 Dierks `yBiBNqvjYaA`; Brightside `TLdBLqPTsYc` is definition-only
  (NOT-A-PROOF) — redundancy holds here.
- 6.4 Dierks joint (`R2T1aizH15M` product, `wpyVmyhPtUI` quotient,
  `gNc1IN6gzhU` chain, `UQw143h_hk0` linearity — the last unlisted in the route
  locator; v2 adds it).
- 6.11 Dierks `hxkQk2dVdxQ`; 6.13 Dierks `Lc-kcNT91KY`, Wrath `uuGDahLA2Rk`;
  6.14 Dierks `TFEz7S70baQ`; 6.15 Dierks `gO0g7PKkJIU` (`qpho9TwLM6s` is the
  sharpness counterexample, correctly supplementary).
- 7.20 Dierks `5W8Jf4MeHxI` [02:00–06:30 + statement 07:00–08:30]; Brightside
  `2EH3XnaDPKU` [05:56–07:24] is a genuine second proof (unregistered source —
  redundancy finding below, not a route).
- 7.24 Dierks `cXVoFGeXFj4` (parts (a)(b)(c) at [00:00/03:00/05:30]) — genuine,
  still single-source; transcript hunt across Dierks/Leonard/EoC found no
  second video.

## Explicitly not routed — re-audited

`source-professor-leonard` keeps its intuition role and gains nothing: both
cited videos re-checked against full transcripts, exclusion holds with the
corrected wording above. `source-brightsideofmaths` stays unregistered, but
the v1 redundancy sentence needs its nuance on record: of the claimed 10/20,
checked rows give a genuine second proof for 7.20, partial backups for 4.15
and 6.14/6.15, nothing for 6.3, and two rows (`mI40-tAtP58`, `5Scawd2WLLA`)
have no captions at all. Registering it buys robustness for one row (7.20),
not coverage — Aram's call, evidence attached.

## Still unresolved

- **Satz 3.49 has no verified proof anywhere.** New from this pass and the
  largest gap: needs a source hunt (books first — Fritzsche/Forster drill —
  or a new video), owned by neither route.
- **Satz 7.24 has a single source**, now transcript-confirmed genuine.
- **Three videos need a direct watch**: `GulH7nS_65c` (3.42, ASR broken),
  `1h_CErk0NFs` (3.43 iff, ASR broken), `1xsIpCa961w` (3.21a, no captions).
  The Gemini-watch layer was built for exactly this (`VERIFY-PROTOCOL.md`)
  but the `gemini` CLI produced zero output over 40+ minutes twice and was
  stood down; resume path is one authenticated `gemini -p` per video.
- **Two Brightside rows need captions or a watch** (`mI40-tAtP58`,
  `5Scawd2WLLA`) before the redundancy call is final.
- ch06/ch07 still have no current HU practice. Unchanged.
- Leonard (31), Wrath (16) and EoC (12) are original-language, Dierks (272)
  German; every transcript carries a `- track:` label.

## Completeness

- [x] Every mapped video judged from its transcript content, never its title;
  five title-matches overturned or qualified (3.40, 3.49, 5.3, 3.42-leg,
  3.43-iff-leg).
- [x] Every miss verified against the whole artifact (MIT full-text search;
  per-playlist caption grep for the 7.24 hunt).
- [x] Both exclusions re-checked against full transcripts with quoted evidence.
- [x] Caption track-language defect found, fixed in `tools/ingest_transcript.py`
  (`SOURCE_LANG` + `pick_track`), pinned by 4 new tests (25 pass), artifacts
  carry a `- track:` label.
- [x] Transcripts checksummed (`make inventory`: 1517 files); validator at
  0 errors with no new warning signature (re-run at close).
- [x] Route-text corrections below change descriptions only — no structure,
  order, scope, covers, or learner state.

No claim of mastery or readiness is made anywhere in this document.

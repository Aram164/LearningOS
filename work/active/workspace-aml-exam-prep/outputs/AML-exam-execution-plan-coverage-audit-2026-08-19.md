# AML exam execution-plan coverage audit — 2026-08-19

Plan package: `work/active/workspace-aml-exam-prep/outputs/AML-exam-execution-plan-2026-08-19.yaml`

Purpose: correct the AML L11 scope record and add one auxiliary, progress-tracked
exam-preparation unit without replacing any of the eleven lecture units. The new
unit owns cold calibration, evidence-routed repair, the handwritten A4 sheet,
mixed mocks, and the final taper. Lecture knowledge maps and complete material
menus remain the permanent content surface.

This is a focused revision over the exhaustive inventory in
`work/active/workspace-m2-exam-prep/outputs/SaD-AML-source-completeness-audit-2026-08-03.md`.
That audit opened and classified the complete AML material shelf available at
the time. Since then, the current 2026 L11 Transformers deck and Übung 08–11
were added. Those five files are opened and reconciled below; no other AML
material root or registered source family changed.

Scope authority: current 2026 lecture decks, followed by current exercise decks.
The Themen list on Übung 10 slide 3 is the course's explicit exam-scope evidence.

## Local inventory

### Inherited complete inventory

| Surface | Evidence retained | Disposition in this revision |
|---|---|---|
| Current L01–L10 decks, primer, Bonusblatt 01–04, older L01–L10 variants | Exhaustive 2026-08-03 audit and existing rich source routes | Preserved unchanged; current decks remain scope authority, older variants remain prior-year |
| Existing Übung 02–07 family, including the duplicate logistic-regression variant | Exhaustive 2026-08-03 audit, duplicate reconciliation, and existing routes | Preserved; current exercises remain course-aligned practice |
| Local CS4780 bank, books, videos, websites, course notes and registered optional sources | Exhaustive 2026-08-03 audit and current source map | Preserved as a complete choice menu; not scheduled as parallel courses |
| L02–L10 durable references, exercise banks and per-lecture mocks | Current unit artifact links and note registry | Reused by the exam-prep stages; no duplicate notes are created |

### New or scope-sensitive files opened in this revision

| Locator | Version/year | Format | Opened/inspected evidence | Actual contents | Duplicate/version relation | Disposition | Unit route | Lecture-specific angle |
|---|---|---|---|---|---|---|---|---|
| `material://source-aml-ss26-lectures/lecture-slides/VL 11-transformers.pdf` | current, 2026-07-17 | course-material | all 81 pages text-extracted; rendered slides 27, 52, 55, 73 and 80 inspected | tokens, embeddings, contextual embeddings, simplified attention, Q/K/V and multi-head attention, positional encoding, Transformer blocks, language modelling, bonus parallelization/masking | SHA-256 `1eb5d3…e7af`; different content and hash from older RNN deck | current | `unit-aml-l11`, `unit-aml-exam-prep` | 2026 L11 scope authority and lecturer notation; explicitly contains no RNN/LSTM material |
| `material://source-aml-ss26-lectures/older-lecture-slides/11-rnn_dcf4e38afab7f0a5b8b543f98a43238d.pdf` | prior year | course-material | prior audit plus hash comparison | RNN forward passes, BPTT, GRU and LSTM | SHA-256 `884cc0…fa9a`; not a variant of the Transformers deck | superseded/out-of-scope | no current unit route | retained in the archive, removed from the 2026 L11 material menu |
| `material://source-aml-ss26-lectures/exercise-slides/Übung 08.pdf` | current | exercise | all 48 pages text-extracted; title/agenda and worked dual-perceptron pages inspected | dual/kernel perceptron, MLP bridge, fourth sheet and bonus discussion | SHA-256 `05648a…27b` | current | `unit-aml-l07`, `unit-aml-l08`, `unit-aml-exam-prep` | current lecturer-worked bridge from kernel perceptrons into MLPs |
| `material://source-aml-ss26-lectures/exercise-slides/Übung 09.pdf` | current | exercise | all 62 pages text-extracted; title/agenda and feedforward pages inspected | feedforward networks plus bonus and sheet discussion | SHA-256 `34c116…9a` | current | `unit-aml-l08`, `unit-aml-exam-prep` | current worked forward-pass and network practice |
| `material://source-aml-ss26-lectures/exercise-slides/Übung 10.pdf` | current | exercise/exam notice | all 76 pages text-extracted; slides 2–3 rendered and visually inspected | first-sitting logistics, explicit L01–L11 Themen list ending in Transformers, computation graphs, autodiff/backprop and framework material | SHA-256 `42e902…4be` | current | `unit-aml-l09`, `unit-aml-exam-prep` | current backprop practice and the authoritative exam-scope/logistics notice |
| `material://source-aml-ss26-lectures/exercise-slides/Übung 11.pdf` | current | exercise | all 68 pages text-extracted; title/agenda and CNN calculation pages inspected | CNN calculations, fourth sheet and fourth bonus-sheet discussion | SHA-256 `26f18f…ca6d` | current | `unit-aml-l10`, `unit-aml-exam-prep` | current lecturer-worked CNN arithmetic and architecture practice |

There is no L11 Transformers Übung. Übung 11 is a CNN session dated before the
2026-07-17 Transformers deck. The L11 exercise bank and mock therefore remain
operator-drafted diagnostic assets without a lecturer-worked Transformer sheet.

## Linked inventory

| URL | Named by | Format | Official/primary evidence | Verified on | Actual topic/locator | Disposition | Unit route | Lecture-specific angle |
|---|---|---|---|---|---|---|---|---|
| `https://web.stanford.edu/~jurafsky/slp3/` | AML L11 slide 72 and `note-aml-l11-transformers` | official draft book | authors' Stanford page; January 6, 2026 release | 2026-08-19 | Chapter 8 — Transformers; Chapters 2–3 only as token/language-model prerequisites | complementary | `unit-aml-l11` | the deck's own named further reading and the closest notation-compatible derivation fallback |

No other linked source is added or newly selected. Existing verified AML links
retain their current dispositions from the 2026-08-03 audit. All RNN-specific
L11 routes are removed because RNNs are not part of the 2026 lecture; their
global source records remain available outside the current L11 menu.

## Current/prior and duplicate reconciliation

| Current asset | Prior/alternate asset | Content match/difference | Authority decision | Route |
|---|---|---|---|---|
| `VL 11-transformers.pdf` | `older-lecture-slides/11-rnn_….pdf` | Different hashes, titles, model families and worked examples; the current deck teaches Transformers and no recurrence | Current deck replaces rather than supplements the older RNN lecture | current deck → `unit-aml-l11`; older RNN → superseded, no route |
| Übung 08–11 | existing Übung 02–07 family | New sessions cover late-course perceptron/MLP/backprop/CNN material; no duplicate hashes among the four new files | Route each by actual content, not session number | L07–L10 plus exam-prep synthesis |
| Übung 10 slide 3 Themen list | legacy block plan | Explicitly names L01–L11 and ends with Transformers | Current exercise notice controls exam coverage; legacy Blocks K–M are sequencing history only | `unit-aml-exam-prep` scope/calibration |

## Explicit exclusions and unresolved gaps

| Material/topic | Disposition | Evidence | Reason | Revisit condition |
|---|---|---|---|---|
| Older RNN/LSTM/GRU lecture and all RNN-specific external routes | superseded/out-of-scope | current L11 deck plus Übung 10 Themen list | 2026 L11 is Transformers and contains no RNN content | only if the lecturer publishes a contrary 2026 notice |
| L11 lecturer-worked exercises | unresolved absence | local exercise inventory ends with CNN Übung 11 | no Transformer Übung exists | add only if a current lecturer-worked asset appears |
| L11 slides 73–81 “BONUS: Parallelizing” | current deck, scope ambiguous; learn-anyway | rendered slides 73 and 80 | labelled Bonus, but contains scaled matrix attention and causal masking | clarify with lecturer if possible; until then retain as a low-cost exam-safety node |
| Exact second-sitting duration | unresolved administrative detail | Übung 10 confirms 120 minutes only for the first sitting; the owning module record carries the current second-sitting slot | a room slot is not proof of working time | rehearse 120 minutes until a second-sitting notice confirms otherwise |
| New full-course mock note | intentionally not created | ten per-lecture mocks already exist | the plan can assemble fresh mixed papers from unseen items without duplicating durable notes | create only if the learner later requests a fixed reusable paper |

## Unit knowledge and material matrix

| Unit | Knowledge nodes and edges | Authoritative scope | Course material | Books | Videos/websites/courses | Practice/exercises | Optional/prior-year | Coverage gap |
|---|---|---|---|---|---|---|---|---|
| `unit-aml-l01`–`unit-aml-l10` | existing individual maps preserved | current 2026 decks | exact existing routes plus newly routed Übung 08–11 for L07–L10 | existing complete menus | existing complete menus | current sheets/bonus decks, note banks and mocks | existing prior-year routes | no new gap; progress evidence is handled by the auxiliary exam unit |
| `unit-aml-l11` | language task → tokens/embeddings → attention/QKV → position/block → CE training; bonus masking depends on attention | `VL 11-transformers.pdf`; scope confirmed by Übung 10 slide 3 | current 81-page deck | Jurafsky Ch. 8 | none selected before a failed diagnostic | exercise bank + 75-minute mock; no lecturer Übung | old RNN route removed as superseded | no lecturer-worked Transformer exercise |
| `unit-aml-exam-prep` | scope/calibration → classical repair + neural repair → mixed transfer → error control and logistics | L01–L11 decks and Übung 10 scope notice | current deck/exercise archive | none scheduled as a parallel course | only lecture-level menus may supply a diagnosed repair | existing reference/bank/mock artifact sets | legacy block plan is sequencing evidence only | exact second-sitting duration unresolved |

## Completeness sign-off

- [x] Every file in the inherited exhaustive AML inventory remains explicitly disposed.
- [x] Every post-audit AML file (current L11 and Übung 08–11) has an inventory row.
- [x] The one newly routed official web source was opened and verified on 2026-08-19.
- [x] New materials were opened; scope did not come from filenames or counts.
- [x] Current and prior L11 were compared by rendered content and hash.
- [x] Numbering and late-course exercise routes were reconciled by actual content.
- [x] Every item has a disposition and every selectable new route has an angle.
- [x] Learner choices remain separate from the complete menu; only current course material is selected for the auxiliary execution path.
- [x] The L11 exercise gap, bonus ambiguity and duration uncertainty are explicit.
- [x] Every ordinary lecture remains an individual unit; the new exam block is auxiliary.

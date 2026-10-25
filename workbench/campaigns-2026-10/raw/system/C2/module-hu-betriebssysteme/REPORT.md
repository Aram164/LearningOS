# C2 — module-hu-betriebssysteme — evidence report (item L2-8)

2026-10-24, GLM-5.3-Flash session, evidence only per the campaign Ground rules.
**Result: 0 defects.** Every check below was run by this session; nothing here
is taken from another session's output without saying so.

- Clone: `~/los-glm-C2-2026-10/repository` at `a2e2d49d` on
  `takeover/complete-and-install-2026-10-23` (verified identical to the live
  branch tip at session start; read-only, never pushed).
- Material: `materials/data-systems/architecture/bs-hu-prior-slides/02_structure.pdf`,
  sha256 `b82d9c9e6652bffcef034e405f740615a5134011457fd1fef7fc1a93dfdbd9bf`,
  46 pages.
- Scripts and evidence: `scripts/audit_abcd.py`, `scripts/audit-abcd-results.json`,
  `scripts/02_structure-page-text.txt` (full page text, for the 20% re-check).

## Module shape

One unit (`unit-bs-os-structure`), one source (`source-bs-hu-prior-slides`),
7 routes all on `02_structure.pdf` (page ranges 1–7, 8–12, 13–18, 19–22,
23–27, 28–34, 35–44), 7 stages each holding one route-bound `read` resource
plus one direct `kind: reference` vocabulary row on stage 7 (`pdf p. 46`).
8 stage resources total. No detours, no shelving, all stages `pending`
(set up 2026-10-23, Aram has not started it; no learner session records exist).

## Provenance — live shape is original design

The module was created on 2026-10-23 by the operator plan package
`LearningOS/workbench/bs-initial-setup-2026-10-23/module-plan.yaml`
(referenced by the study map's `source_plan.path` and by
`work/active/workspace-bs-foundations/outputs/bs-material-coverage-audit.md`,
which states the package lives "outside the authored repository").

- Programmatic diff of the package against live `source-map.yaml` and
  `study-map.yaml`: **all route fields and all stage fields content-identical,
  zero differences**. Nothing was overwritten after generation.
- The package's `slide-scope-evidence.json` / coverage audit record the same
  7 page ranges, the p45 cartoon exclusion and the p46 vocabulary disposition.
- The material's sha256 matches both the coverage audit's recorded hash and
  `records/materials-manifest.yaml` (captured 2026-10-21).

This module therefore has no September-broadcast history to compare against:
it postdates that damage, and its live shape equals its generating plan. Any
defect found below would have been original design; none was found.

## Check A — vault_path / material:// resolution

One distinct URI, used by all 7 routes and the vocabulary row:
`material://source-bs-hu-prior-slides/02_structure.pdf`. Resolved with the
system's own `resolve_material_target` (resolution root `materials/.flat`,
boundary `materials/`): →
`data-systems/architecture/bs-hu-prior-slides/02_structure.pdf`, exists.
OK.

(Note for the re-checker: passing the clone-parent's *symlinked* materials
path as the boundary root makes the resolver's containment check fail — an
artifact of my harness, not a system behaviour; with the resolved real path
it passes. First run tripped on this; second run OK.)

## Check B — page ranges vs real page count

Real page count: 46 (pypdf via the system extractor). All 8 locators parse
and lie inside 1–46:

| route/resource | locator | range | verdict |
|---|---|---|---|
| route-bs-os-hardware | pdf pp. 1–7 | 1–7 | OK |
| route-bs-interrupts | pdf pp. 8–12 | 8–12 | OK |
| route-bs-memory | pdf pp. 13–18 | 13–18 | OK |
| route-bs-privileges | pdf pp. 19–22 | 19–22 | OK |
| route-bs-syscall-boundary | pdf pp. 23–27 | 23–27 | OK |
| route-bs-linux-example | pdf pp. 28–34 | 28–34 | OK |
| route-bs-os-structures | pdf pp. 35–44 | 35–44 | OK |
| resource-bs-vocabulary | pdf p. 46 | 46 | OK |

Coverage note: the ranges tile pp. 1–44 contiguously; p45 is excluded by the
documented decision ("Schlusskarikatur" — verified: its entire text is
"Mr. Osborne, may I be excused? My brain is full."), p46 is the separately
routed vocabulary page. Locators say `pdf pp.` — PDF page numbers, matching
the slide footers ("May 2006 - 16" on PDF p16). No printed-page anchors
anywhere in this module.

## Check C — content claims against the PDF text

Extraction: the system's `pdf_text` (pypdf), with ligature/quote/dash
normalisation. The deck's text layer is clean (no stream-token failures).

**All 7 anchor quotes from the plan's `claim_evidence` verified on exactly
their claimed pages** (normalized substring match):

- p7 "Device Controller is in charge of a particular device type." (route-bs-os-hardware)
- p9 "A trap is raised synchronously by the software, either by an error or a by a trap-instruction." (route-bs-interrupts)
- p16 "base register – holds the smallest legal physical memory address." (route-bs-memory)
- p20 "Mode bit added to CPU state to indicate mode of operation:" (route-bs-privileges)
- p24 "System Call – the method used by a process to request action by the operating system." (route-bs-syscall-boundary)
- p33 "Kernel will copy data from/to process' user-mode memory space" (route-bs-linux-example)
- p37 "The kernel sources may well be structured, but at runtime, every procedure can call any other procedure directly." (route-bs-os-structures)

**Per-route anchors from angle/angle_detail/done_when:**

- route-bs-os-hardware (1–7): "device controller" p7, "cpu" pp5–7, "memory" pp5+7, "bus" pp5–6. OK. p1 is the deck cover/TOC slide, legitimately inside the reading range.
- route-bs-interrupts (8–12): "trap" pp9+11; p11 the flow graphic separates "Interrupt Service Routine (Interrupt Dispatcher)" from "Interrupt handler" — the angle's claim; "irql" pp11–12. The stage-2 drill asks whether Level 2 may interrupt a Level-28 handler: p12 carries the x86 IRQL table with **28 = Clock** and **2 = Dispatch** as bare numerals (so the phrase "level 2" extracts nowhere — table cells), plus the masking rule "Servicing an interrupt raises IRQL … masks subsequent interrupts at equal and lower IRQLs". The drill is answerable from the slide. OK.
- route-bs-memory (13–18): "base register"/"limit register" p16, "page" p18; the three consecutive images the angle describes are pp16 (bounds), 17 (MMU: "Add one layer of indirection", virtual/physical), 18 (page table). The stage-3 drill's numbers are **on the p16 diagram**: `300040`, `120900`, `420940`; the drill's 300039/420939 appear nowhere in the deck — they are the drafted out-of-range test addresses, consistent with the audit's declared "operator-drafted original practice". One caveat, not a defect: p18's text layer carries only the title "Address Translation with Page Table"; the page-number-p → frame-f/offset-d labels sit in the diagram with no text layer, so this session verified the third image by slide title plus the original audit's recorded visual inspection of p18, not by extracted words.
- route-bs-privileges (19–22): "mode bit" p20, "ring" p22 (the historical Ring 0/3 example). OK.
- route-bs-syscall-boundary (23–27): "system call" pp23–27, "stack" p27 (separate stacks), "read" p26 (stub). OK.
- route-bs-linux-example (28–34): "0x80" pp29–30, "sys_alarm" pp30–31, "errno" pp28–29, "alarm" pp28–31. OK.
- route-bs-os-structures (35–44): "microkernel" pp36/41/**44** (the S.44 NT correction the angle claims is textually present), "nt" pp35–44, "ms-dos" pp38–39, "unix" pp35–38, "bsd" pp38+40. The done_when's "S.42–44" NT qualification range checks out (nt on 42/43/44, microkernel on 44). OK.
- resource-bs-vocabulary (p46): "dma", "synchronous", "asynchronous" all present — exactly the named-not-explained terms the row claims. OK.

Full per-page text: `scripts/02_structure-page-text.txt`.

## Check D — duplicates and dangling references

- Duplicate `locator` strings among the 7 sibling routes of the single
  (source_id, unit_id) group: none. Duplicate `angle_detail` strings: none
  (each carries a unique leading sentence; the shared provenance tail is the
  plan's own wording, present in the original package).
- Dangling `route_id` references across all 8 stage resources: none; each
  stage's `material_ref.route_id` equals its own `route_id` and names its
  topical route (stage order = route order = page-range order).
- `knowledge_node_id` / `covers`: all 7 ids resolve in the unit's
  `knowledge_map.nodes` in `unit.yaml` (the validator resolves them there
  too — plan_rigor.py:426–437). No dangling knowledge references.
- Unit artifacts exist: `knowledge/notes/systems/note-bs-os-basics-{reference,exercise-bank,self-test}.md`;
  `workspace-bs-foundations` exists with its outputs.
- References into the module from outside: only its own workspace files
  (`work/active/workspace-bs-foundations/`). No other tree location cites
  its routes, stages or unit.

## Validator triage

`.venv/bin/python tools/validate.py --compact` in the clone:
**0 errors, 1468 warnings** tree-wide
(`generated/reports/validation-report.md`, generated 2026-10-24T13:25).

**Zero warnings touch this module** — by path (`curriculum/modules/module-hu-betriebssysteme`)
and by every id it owns (`unit-bs-*`, `route-bs-*`, `stage-bs-*`,
`knowledge-bs-*`, `note-bs-os-*`, `source-bs-hu-*`, `study-map-bs-*`,
`bs-hu-prior`). Nothing to triage.

Cross-checks that this is a true clean bill, not a blind spot:

- The run's per-module warning counts reproduce the two earlier C2 sessions
  exactly (m2-statistik 481, aml 31), so this run saw the same tree state they
  saw. (`module-hu-amls` at 135 is the adjacent *skipped archived* module —
  different module.)
- Positive control: calling the validator's own `locator_binding_findings` on
  this module's real routes returns NONE; injecting a broadcast locator and a
  vault/locator mismatch into a copy makes it fire
  (ROUTE-LOCATOR-DUPLICATE / ROUTE-VAULT-LOCATOR-MISMATCH). The machinery is
  live for this data and silent on it.
- Shape prediction: the 7 `read` rows are route-bound via `material_ref`
  (the shape RESOURCE-SCOPE-UNBOUND punishes is absent), and the 1 direct row
  is `kind: reference`, which the validator exempts (plan_rigor.py:569,591,
  per the AML session's verified reading).

## Notes and limitations

- The SAR logo on every page header extracts as glyph codes (`/g54 /g92 …`,
  fontTools warning about a CFF Type1 font). Extraction noise only; it does
  not affect content anchors and is not module data.
- I ran no pytest, no `make check`, no `make system-check` (Ground rules);
  the validator plus targeted scripts are the whole evidence base.
- No fix package was prepared (`module-plan-import --check` not run): the
  prompt allows evidence only, and with 0 defects there is nothing to fix.

## Verdict

`module-hu-betriebssysteme` is clean: material identity verified end to end
(live bytes = audit hash = manifest hash), plan data content-identical to its
generating package, every locator inside the real page count, every content
claim anchored in extracted text (one diagram-only caveat recorded above),
no duplicates, no dangling references, zero validator warnings. Nothing for
Claude's verification pass to confirm beyond re-running the scripts; nothing
for Aram to decide.

# C2 fix packages — module-hu-aml (item L2-15, 2026-10-24)

Prepared under Aram's authorization to act on critique point 1 by preparing
`module-plan-import --check` fix packages only. **Nothing was applied**: every
check below reports `mode: check` and `canonical_files_written: 0`, and the
clone's git tree carries only the new untracked workspace folder (no commits,
no pushes).

Everything here fixes only the two defects the verdicts confirm:

- **F1** (`C2/module-hu-aml/CLAUDE-VERDICT.md`, "CONFIRMED, with a
  correction"): three `source-murphy-pml1` rows in
  `unit-aml-exam-prep/study-map.yaml` anchor printed page numbers, exactly 30
  less than PDF pages. The verdict's fix: write both numbers ("p. 372
  (pdf p. 402)"), not just the converted one.
- **F2** (same verdict, "CONFIRMED"; `L1-234-CLAUDE-VERDICT.md` agrees): 31
  `RESOURCE-SCOPE-UNBOUND` rows in the same map — unmigrated critique-point-1
  debt; the bound 2026-09-11 rewrite (`AML-exam-plan-final-2026-09-11-r2`)
  was never applied, while its 9 exam-prep routes did land in the live source
  map.

## Where

Prepared in the C2 clone `~/los-glm-C2-2026-10/repository` (branch
`takeover/complete-and-install-2026-10-23` at `a2e2d49d`, clean, never
pushed), in `work/active/workspace-aml-l2-15-2026-10-24/`, and copied here to
`packages/`:

| file | what it is |
|---|---|
| `package-f1-printed-page-anchors.yaml` | F1: the three locator texts |
| `package-f2-bind-exam-prep-rows.yaml` | F2: 17 `material_ref` bindings |
| `package-f1f2-combined.yaml` | both, pre-merged into one batch |
| `check-f1-printed-page-anchors.json` | F1 `--check` output (ok, 0 writes) |
| `check-f2-bind-exam-prep-rows.json` | F2 `--check` output (ok, 0 writes) |
| `check-f1f2-combined.json` | combined `--check` output (ok, 0 writes) |
| `coverage-audit-l2-15.md` | the `plan_contract.coverage_audit` document |

Both standalone packages and the combined one were checked against the clone
as-is (base `a2e2d49d`):

```
F1:       ok=true  mode=check  canonical_files_written=0
          package sha256:691ca48d1648047f4c434bb9ed00e6664226e97e94592333d84bc1c18ea60bcd
F2:       ok=true  mode=check  canonical_files_written=0
          package sha256:307efe637345c7f1093edf656cdafbced8a3d6965d3b8c92636159c240a17993
combined: ok=true  mode=check  canonical_files_written=0
          package sha256:81dad7d6f0f86e5a947ff35635b949d99421e84910123adcdfc71f0a8f637412
```

All three affect exactly one canonical file:
`curriculum/modules/module-hu-aml/units/unit-aml-exam-prep/study-map.yaml`
(`route_counts` before/after 265/265; exam-prep routes 9/9; no source registry
changes).

## Package F1 — printed-page anchors

Compact `unit_revisions` shape: full resources arrays for
`stage-aml-foundations-repair`, `stage-aml-linear-optimization-repair` and
`stage-aml-neural-transformer-loop`; inside each, only the `source-murphy-pml1`
row's `locator` changes. Six substitutions, each asserted to hit exactly once,
e.g. `§11.2.2 p. 372 (the objective…` → `§11.2.2 p. 372 (pdf p. 402; the
objective…`, and `p. 519` → `p. 519 = pdf p. 549` for the inner sub-anchors.

I re-verified all 14 sub-anchors against `pml1.pdf` (860 pp.) in the clone on
2026-10-24 with the clone's own pypdf: pdf pp. 402, 410, 307, 319, 328, 331,
548, 549, 551, 556, 557, 558, 559, 562 each print the claimed printed number
in its own page header (constant +30 offset). The corrected spans also agree
independently with the live route
`route-f426a3cf4e1b48b8f1c408d3`, which already carries
`§8.1.3 pdf pp. 307-310, §8.3 pdf pp. 319-321, §8.4.6 pdf pp. 328-331, §15.4
pdf pp. 548-555, §15.5 pdf pp. 556-562`.

## Package F2 — binding the unbound rows

The unapplied r2 plan is **not** a binding patch — it is a full September-dated
replacement map (9 restructured stages, new sitting-gate stage, no
`knowledge_node_id`, rows added and dropped), so importing it wholesale is a
product decision the verdicts do not confirm, and its calendar is long past.
The faithful fix is a binding pass over the live 46-row map, porting r2's
route-fit decisions where they land on live rows.

Mechanics: 17 of the 31 warned rows gain
`material_ref: {route_id: …, inherit: [angle, angle_detail]}` to the route
whose declared span already carries the row's material. Each row keeps its
reviewed `label`, `source_id` and `locator` as an explicit stage-specific
override (the designed override path in
`tools/learning_os/domain/material_refs.py`), so no wording is lost or
rewritten; each row additionally gains its route's angle and angle_detail.
Every binding was asserted programmatically against the target row's
`source_id` and locator head before writing. Bindings, by route:

- `route-9be11f4c735b1fab72ff7fd5` (VL 01–11 decks) — 6 rows
- `route-b3c9cda951cabf0f92743436` (Übung 02–11 + Bonusblätter 01–04) — 6 rows
- `route-5f890476996a6d9847807cc6` (Übung 10 slides 2–3) — 3 rows
- `route-53277505603f22eedc9d81b7` (Géron Ch 3/11/14/16) — 2 rows
- `route-9b89cb595b8b44604cd30acf` (D2L Ch 11 five sections) — 3 rows
- (sums to 17; exact per-row listing in `coverage-audit-l2-15.md`)

**Proof of the warning delta.** Running the validator's own unbound-row rule
(`plan_rigor.py::_check_row_scope`: non-`reference` rows are clean iff they
carry a unit-owned route binding or their exact `(source_id, locator)` equals a
declared exam-prep route pair) over the staged states:

```
live:             31 unbound non-reference rows
F1 staged:        31   (F1 touches no binding)
F2 staged:        14   (the 17 bindings clear exactly their 17 warned rows)
combined staged:  14
```

The same script verified that no staged row differs from its live form beyond
the added `material_ref` key, and that the staged F2 map survives the
repository's own `expand_map` (which `--check` runs internally).

## The 14 rows left unbound, and why

Fixing only the confirmed defect does not include inventing routes or
re-typing rows; these need Aram's call (each is listed in the coverage audit):

- **9 knowledge-note menu rows** (mock/artifact menus, no `source_id`) name
  vault notes, not materials; no exam-prep route can carry them. The r2 plan
  kept the same rows unbound — the 09-11 pass did not consider them bindable
  either.
- **`Primer_Linear_Algebra.pdf`** (calibration) is named by no exam-prep route.
- **geron Ch 4 'Training Models'** (foundations) is outside
  `route-53277505603f22eedc9d81b7`'s declared span (Ch 3/11/14/16), so binding
  it there would mis-declare — the exact broadcast class C2 exists to catch.
  It needs its own route.
- **The two "owning module record plus Übung 10 slide 2" rows** (final repair,
  taper) name `module.yaml` as material; no route carries a vault record.
- **"Unused Übung/Bonusblatt and per-lecture mock items"** (final repair)
  names two banks, one of which (the mocks) has no route.

## Apply-order caveat (for the landing session)

The two standalone packages are both cut against base `a2e2d49d` and overlap
on the three F1 stages' full resources arrays (the import mechanism replaces a
stage's resources array wholesale; there is no row-level patch for study-map
resources). So neither applies cleanly after the other unchanged: apply the
**combined** package, or apply one and re-cut the other against the resulting
map. The combined package carries both edits in one transaction and checked
clean.

## Assumptions and scope notes

- The verdicts' F1 spot-checks (§11.2.2→402, §8.3→319) were re-verified by me
  directly; the remaining 12 sub-anchors were verified by my own pypdf run
  today (listed above), agreeing with the L2-7 report's 9/9 and the verdict's
  correction.
- `plan_contract.checks` six attestations are made on the L2-7 measurements,
  re-verified for the touched rows in this clone (basis stated in the audit's
  Completeness section).
- The F3 observations (prose-compressed route locators, MIT quiz file, d2l /
  Jurafsky externals) are not defects per the verdicts and are untouched; the
  binding of `route-b3c9cda951cabf0f92743436` rows inherits that route's own
  compressed locator only as route metadata, while every bound row keeps its
  own reviewed locator text.
- F1 was implemented as the verdict prescribes (both numbers in the row text)
  rather than by binding the Murphy rows to `route-f426a3cf4e1b48b8f1c408d3`;
  either would clear the printed-page inconsistency, and the verdict names the
  text form. The Murphy rows are left unbound in F2 for exactly this reason.
- Coverage audit lives at
  `work/active/workspace-aml-l2-15-2026-10-24/outputs/coverage-audit-l2-15.md`
  in the clone (snapshot-bound `work/active/`, as the gate requires) and is
  copied beside the packages here.

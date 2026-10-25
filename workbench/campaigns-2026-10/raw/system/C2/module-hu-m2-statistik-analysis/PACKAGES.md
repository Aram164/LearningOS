# PACKAGES — M2 critique-point-1 fix packages (item L2-16, 2026-10-25)

Prepared under Aram's authorization: acting on critique point 1 by preparing
`module-plan-import --check` fix packages in the C2 clone, **never applied**.
Fix scope was limited to the defects confirmed by
`C2/module-hu-m2-statistik-analysis/CLAUDE-VERDICT.md`,
`L1-234-CLAUDE-VERDICT.md` and `C2/module-hu-m2-statistik-analysis/RECHECK-80.md`;
for chapters 3–7, each resource is bound to the stages it serves, as chapters
1 and 2 already are. Nothing was applied, nothing committed, nothing pushed.

## 1. Where things are

- Clone: `~/los-glm-C2-2026-10/repository` at `a2e2d49d`
  (`takeover/complete-and-install-2026-10-23`), working tree clean — the only
  additions are untracked files under
  `work/active/workspace-m2-l2-16-packages-2026-10-25/` (builder + audits).
- This folder (`packages/`): the four plan packages and their full `--check`
  reports (`p1…p4-check-report.json`), plus `audits/` (the coverage audits the
  packages' `plan_contract.coverage_audit` fields point at, and the builder
  that generates everything deterministically).
- The audits must sit inside the clone at
  `work/active/workspace-m2-l2-16-packages-2026-10-25/outputs/` for the
  contract gate (they do, untracked); workbench copies are in `audits/`.

## 2. The four packages, all `--check` green

| Pkg | File (`packages/`) | sha256 (file) | Fixes | `--check` |
|---|---|---|---|---|
| P1 | `package-p1-ch03-07-binding.yaml` | `sha256:c1ef82d6…be6dc9170` | the 472 unbound ch03–ch07 stage rows → route-bound | ok, changes present, files_checked 11 |
| P2 | `package-p2-aml-l09-locator.yaml` | `sha256:aeedc7e0…c8de74aa3` | RECHECK-80 F1: absent deck name in `route-b3e5bcb8f3813cbc477ac799` | ok, changes present, files_checked 3 |
| P3 | `package-p3-ingmath2-pages.yaml` | `sha256:2cfc4b25…1a43d6160f` | RECHECK-80 F2: printed-page anchors on the three IngMath2 routes | ok, changes present, files_checked 3 |
| P4 | `package-p4-rehearsal-binding.yaml` | `sha256:a9732cba…22816171a5` | the 9 prose rows of unit-m2-combined-exam-rehearsal → route-bound | ok, changes present, files_checked 3 |

Full sha256s (and the exact `--check` invocations) are in §6. Each check ran
against the clone at `a2e2d49d` with materials mounted; each report carries
`expected_snapshot`, `expected_revisions`, `expected_write_paths` and
`expected_write_sha256` for the reviewed apply.

What each package would write on apply (from its check report):

- **P1** — `units/unit-m2-analysis-ch03…ch07/{unit.yaml,study-map.yaml}`
  (10 files). Placements 86/69/129/127/61 before and after per unit; triage
  unchanged; `uncovered_knowledge_nodes` empty; the only unplaced routes are
  the 8 never-placed ones (§4). Verified independently of the gate: expanding
  all 472 `material_ref` rows against the live source map reproduces each
  original row plus exactly `route_id` and `source_id` (0 content mismatches).
- **P2** — `source-map.yaml` + `operations/transactions/lineage.yaml` (the
  Phase-B ledger). One locator changed; the five l15 stage rows that inherit
  it update at load. Claim evidence anchored: quote from
  `VL 09-neural-networks.pdf` p. 2, classification `anchored`, `matched: true`.
- **P3** — `source-map.yaml` + lineage ledger. Three locators changed; three
  quotes anchored (pp. 78, 161, 222 of `IngMath2_Aufgaben.pdf`), all matched.
- **P4** — rehearsal `unit.yaml` + `study-map.yaml`. Placements 11 → 11,
  triage unchanged, no uncovered nodes.

## 3. Decisions, with reasons

1. **The binding rule is the one ch01/ch02 already implement, derived, not
   invented.** A stage binds a route exactly when the route's `covers` names
   the stage's knowledge id. Verified mechanically on ch01 (25 actual = 25
   derived) and ch02 (71 = 71), then applied to ch03–ch07: every one of the
   472 rows already sits on a stage its route's covers names (0 deviations),
   and every row matches exactly one declared route by (label, locator) —
   0 unmatched, 0 ambiguous. So P1 is a pure rebind: no resource moves, no
   route edits, no source-map write at all.
2. **P1 inherits only fields exactly equal to the route's** (`label`,
   `source_id`, `locator`, `angle`, `angle_detail`, plus `vault_path` where
   the row has one — measured: angle/angle_detail equal on all 472,
   vault_path equal or both-absent). The effective teaching content is
   provably unchanged; the package adds ownership, nothing else.
3. **P2's corrected locator** is
   `lecture-slides/VL 08-feedforward-neural-network.pdf; lecture-slides/VL 09-neural-networks.pdf`.
   Two changes were required, not one: the wrong filename (`VL 09-training-…`
   exists nowhere; the real deck is `VL 09-neural-networks.pdf`, the name
   module-hu-aml binds for the same deck) and the separator ("and" → ";"),
   because a locator with two `.pdf` tokens is unresolvable by design — the
   semicolon two-file form is the module's own convention for deliberate
   two-file routes. The corrected locator resolves to exactly the two real
   decks; the route's title/angle/angle_detail/covers are untouched.
4. **P3's corrected locators** state each page in the module's `PDF p. N`
   house style and keep the printed number as a `(printed p. N)`
   cross-reference (the house style the validator's own page parser strips
   before reading pages). All 28 section anchors were re-measured this
   session at printed + 3 (RECHECK-80 F2's six plus the other 22 the three
   locators name). Two mechanical constraints shaped the wording: the file
   token needs the provenance paren the ch03 IngMath2 route already carries —
   `IngMath2_Aufgaben.pdf (312 pp, Voß, TU Hamburg 1991):` — because the bare
   colon form resolves to zero files today; and chapter groups are joined by
   commas, not semicolons, because a semicolon puts the reader into the
   strict multi-file branch, which then narrows the quote-verifiable page
   span to the first group.
5. **P4 binds each of the 9 rows to the unit's one declared route for its
   source** (6 routes, 9 rows, one route per source — the only non-inventive
   mapping; rows keep their stage-specific label/locator/angle prose as
   overrides, `source_id` is inherited). Recorded deviation, also in the
   audit: the unit's routes carry coarse covers (`knowledge-m2-joint-blueprint`,
   `knowledge-m2-joint-simulation`) that predate the mock-one/mock-two/repair
   stage split, so the ch01/ch02 covers-derived placement rule does not
   reproduce these nine placements mechanically. The binding rests on the
   validator's own remediation text for this exact warning ("bind the
   resource to a declared route for this unit") and one-route-per-source
   uniqueness. Covers are not edited. This is the one package where the
   mapping is judgment, not derivation — flagged so the reviewer attacks it
   first.

## 4. New finding, measured but NOT fixed (needs Aram)

**The ch03 IngMath2 route has the same printed-page-anchor defect as F2.**
`route-an-ch03-analysisdrillblaetterext-5` cites Kap. 10 sections as bare
`p. N` printed numbers; measured this session: §10.1 p. 2 → PDF p. 5,
§10.2 p. 8 → 11, §10.3 p. 16 → 19, §10.4 p. 35 → 38 (headings found on the
expected pages, printed numbers visible on them). Same class, same +3
offset, but RECHECK-80 F2 names only the ch05/ch06/ch07 routes, and Aram's
scope rule says fix only what the named verdicts confirm — so it is recorded
here and left unchanged. The one-command repair would mirror P3's ch05 shape.

## 5. Out of scope (explicitly)

- **8 never-placed routes, 14 (route, stage) pairs**: `route-an-ch03/04/05/
  06/07-henningdierks` and `route-an-ch03/05/06-wrathofmath` declare `covers`
  but have no stage row in any generated or current map. Adding resources for
  them is new scope, not repair; P1 leaves them unplaced (the check reports
  show them as the only `unplaced_routes`).
- The 5 ATTACH-LOCAL-ABSENT and 1 HYGIENE-VIEWS clone-wide warnings (noise,
  self-explained), all warnings of other modules, F3-class cosmetic locator
  prose (§2.4 name drift — confirmed cosmetic by the verdict), and the
  unverifiable scanned file `Bestimmt_Scan.pdf`.
- Any apply, any commit, any push.

## 6. Reproduce

```bash
cd ~/los-glm-C2-2026-10/repository
PKG=<workbench>/C2/module-hu-m2-statistik-analysis/packages
.venv/bin/python tools/los.py module-plan-import module-hu-m2-statistik-analysis \
  --file "$PKG/package-p1-ch03-07-binding.yaml" \
  --file-sha256 sha256:c1ef82d6daaf0f394741ffd1113d0932fa2da493d159e75a5d14381be6dc9170 \
  --check --json > "$PKG/p1-check-report.json"
# P2: --file-sha256 sha256:aeedc7e0fed28b079a5d5cbbcf6cb49f4079ecccd49e23aa3df5c24c8de74aa3
# P3: --file-sha256 sha256:2cfc4b25d384e9d3b2628e428d785fa9530fbacfd4239f0a0f1bd51a43d6160f
# P4: --file-sha256 sha256:a9732cba4b2f3f08a17050cc2b460da3f0229d426b18995391fe5d1f8270e5e1
```

The builder (`audits/build_packages.py`, also at
`work/active/workspace-m2-l2-16-packages-2026-10-25/build_packages.py` in the
clone) regenerates packages + audits deterministically; its count assertions
(472 bindings, 9 bindings) and quote-prefix asserts fire on drift.

## 7. Gotchas for the landing session

- **The claim-evidence `ref:` field cannot carry a spaced `material://` URI
  in a plan file under `work/`**: the material-integrity sweep reads every
  YAML under the canonical trees (which include `work/`) and its bare URI
  regex truncates at whitespace — a spaced URI in any non-`vault_path`-style
  field becomes an E MATERIAL-MISSING on a path nobody wrote. The evidence
  exception (`in_evidence`) covers only `work/complaints/`. Keep plan
  packages outside the clone (the `--file` path is not confined to the repo)
  or quote/field-shape the URI into a delimited form.
- **A `.md` file at the workspace root** (`work/active/<ws>/*.md`) raises
  HYGIENE-UNFILED; the audits belong in an `outputs/` (or `scratch/`,
  `inputs/`) subfolder, matching the l06 precedent.
- **Semicolons in a locator mean multi-file** to the quote reader, and a
  bare `File.pdf:` colon defeats material resolution; single-file locators
  with prose use the `File.pdf (…):` form and comma separators.
- The IngMath2 book's printed→PDF offset is uniformly +3 across the whole
  cited span; the strang/TUM/AS-Ana1 anchors elsewhere are correct as they
  stand (RECHECK-80 §3) — do not re-anchor those.

## 8. Assumptions

- ASSUMPTION: the pypdf text extraction is faithful for the four evidence
  pages; the digests of all three evidence files match the registered
  materials manifest (checked directly), and the gate's own `matched: true`
  verdicts re-verified every quote against the same extraction path.
- ASSUMPTION: the workspace `outputs/` generated plans remain the originals
  per CAMPAIGNS.md C2; the F1/P2 origin conclusion (original defect, not
  damage) is RECHECK-80's, not re-derived here.
- The 9-row P4 mapping is a judgment call (§3.5) — it is the one place a
  reviewer may reasonably decide differently.

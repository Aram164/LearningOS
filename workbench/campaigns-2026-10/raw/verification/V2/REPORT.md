# V2 — the Obsidian UI's on-screen rendering

Verification campaign V1–V5, batch V2 (GLM 5.8 Flash). Evidence and failing
tests only; no fixes, no pushes. Written 2026-10-25.

## Base

Pinned and verified by `git rev-parse HEAD` after `checkout --detach`:

- Core `fb73b0f9c65de0f7a74c6d6e6b65ba74115a2e46` — clone at
  `~/los-glm-V2-2026-10/repository` (venv installed, pins untouched)
- UI `f7dbc1f7607157d5c1c2edb84a14e6a26ab89f94` — clone at
  `~/los-glm-V2-2026-10/obsidian-ui` (`npm install` clean)

Bundle freshness: `node build.mjs` in the clone reproduced `plugin/main.js`
byte-identical (sha256 `50020395e82e22defc48418d0de5c28b6a5954ce` before and
after; `git status --porcelain` clean), so mounting views through the tracked
bundle genuinely exercises the pinned `src/`. jsdom was **not** needed: the
shipped `El` stub plus `tests/dashboard/browser-dom.js` covers every assertion.

## Reading route

1. `CAMPAIGN.md` ground rules; UI `CLAUDE.md` (rules 2, 12, 13), `DESIGN.md`,
   `ARCHITECTURE.md`.
2. Harness: `tests/harness.js`, `tests/fixture-workspace.js`,
   `tests/source-module-loader.js`, `tests/test-fixture-workspace.js`, then the
   shipped suites' mount pattern (`tests/dashboard/support.js`, `browser-dom.js`,
   `render-focus.js`).
3. View sources: all of `src/views/` (14 registered leaves — `DiagnosticsView`
   shares `review-view.ts`), the home/atlas/abilities features they delegate to,
   `src/components.ts`, `src/accessibility/button-group.ts`,
   `src/manifest-store.ts` (`ready`/`stale` semantics).
4. Fixture data: `fixture-vault/generated/manifest.json` — it contains exactly
   the cases the atlas assertions need (a question targeting a `derives`
   relation the registry never authored; a two-edge prerequisite chain).
5. Probes `probe1`–`probe6` (in `probes/`, run one node process at a time from
   the clone; logs in `logs/`).

## Results per item

Every assertion V2 lists; HELD = behaviour asserted in the campaign was
observed, with the probe that holds it up.

| # | Assertion (CAMPAIGN.md V2) | Result | Evidence |
|---|---|---|---|
| 1 | Every leaf in `src/views/` mounts against `fixture-vault/` | HELD | probe1: all 14 view types (18 mounts incl. deep states) render; 0 unmountable views, so **no mounting coverage gaps** |
| 2 | Home shows one resumable focus | HELD | probe5: exactly one `.los-continue` card naming resume-pointer stage "Conditional probability and Bayes" and its module |
| 3 | Home: short Today list / short Continue elsewhere list | HELD | probe5: Today ≤ 4 rows, Continue elsewhere ≤ 5 (the render slices at 4/5) |
| 4 | No primary view is a bare list of links (rule 13) | HELD | probe5: all eight destinations carry static copy beyond their clickable elements; probe1's renders show sections/headers throughout |
| 5 | Record references are typed chips or actions | HELD | probe5: every Home clickable is a labelled action; every chip carries a `los-t-<type>` class |
| 6 | Exactly one filled primary action on Home | HELD | probe5: exactly one `los-btn--cta`, on the Continue card |
| 7 | Every view renders with the CLI unavailable (rule 2) | HELD | probe2A: all 16 mounts (14 types) render with every `runLos` call failing; Home still shows fixture content |
| 8 | Every view with a stale manifest shows its state, no throw (rule 2) | HELD | probe2B: after a good load, all views re-render with "Showing the last validated view." banner |
| 9 | Every view with a missing manifest shows its empty state, no throw (rule 2) | HELD | probe2C: from a fresh start, all views render empty states ("Projection unavailable", "No open modules", "No unit is waiting", "Prospective catalog is sealed", …) |
| 10 | No view throws on a missing optional field | HELD | probe3: stripped `estimate_minutes`, `criteria`, `resources`, `concept_ids`, `scope`, `status`, `objective`, `next_action`, `deadline`, `aliases`, `summary`, `role`, `authorship`, relation `context`, relation `source`→null, etc.; all 15 mounts render |
| 11 | Every interactive element has an accessible name | HELD | probe4: name sweep over every control (button/input/select/textarea/summary/role=button) in all 15 mounts; 0 unnamed; plus 0 inaccessible click-only containers |
| 12 | Button groups are keyboard-navigable | HELD | probe4: 19 groups across the app move focus on arrow keys and keep it inside the group (2 Abilities groups use documented non-roving schemes — see Observations) |
| 13 | Atlas DOM: orphaned question is a non-clickable row reading "— no longer authored" | HELD | probe6: `note-fixture-question-stale` renders a `div.los-atlas-question-row.is-orphaned` reading "Recorded on Bayes theorem derives Frequentist inference — no longer authored", no click listener |
| 14 | Atlas DOM: the depth remainder is counted on screen | HELD | probe6: "+ 1 more prerequisite · beyond depth 1"; expanding names exactly "Probability"; open state says "counted, never dropped" |
| 15 | Atlas DOM: inspector shows both sentences of one strict row | HELD | probe6: selected `concept-bayes--requires--concept-bedingte-wahrscheinlichkeit` row shows canonical "Bayes theorem requires Conditional probability." AND the study-order sentence in one row |
| 16 | Atlas DOM: the Domains lens renders | HELD | probe6: rail, search, per-domain counts, note rows, and the "Notes & shelves" variant tab pressed |

## Findings

None. Every probe exits 0 on the pin; there are no failing tests because there
is nothing that fails. Per the campaign's category rules: no test failed, no
contract line was violated, and no authored content was missing (absence
counting is out of V2's scope).

## Coverage gaps

None for mounting — the harness mounted all 14 registered leaves, including the
deep states (module detail, unit with stage, project detail, library detail,
atlas concept, Domains lens, abilities).

## Untested scope

- Real-browser behaviour: CSS/token rendering, actual focus rings, hit-testing,
  pointer/pan/zoom of the abilities camera (`viewport.ts` is wired but the stub
  cannot drag or wheel). DOM semantics were asserted; pixels were not.
- `Tab` leaves the group / Enter activates (rule: DESIGN.md components): native
  `<button>` behaviour the El stub cannot simulate; only the arrow-key roving
  layer is asserted.
- Interaction journeys (writes, session end, gateway recovery, library
  filtering): outside V2's rendering scope, and already exercised by the
  shipped `tests/dashboard/` suites, which were not re-run here (single-file
  process rule; the full dashboard suite was not run).
- `SuggestModal` surfaces (global search) — rendering covered via probe1 only
  through their hosts; the modal probe pipeline of the shipped suites was not
  duplicated.

## Observations (no contract line violated; recorded for Aram)

1. **Navigator shows no unavailability signal on a missing manifest**
   (probe2C). With no prior data, `manifestFreshness` renders nothing (it only
   fires in the stale/`ready` case), and the Navigator is pure chrome with no
   empty state of its own. Rule 2's requirement — render fully with the CLI
   unavailable — is met; this is a visibility note, not a violation.
2. **Two Abilities groups deliberately do not use roving arrow focus**
   (probe4). "Ability camera" is Tab-reachable; arrow keys pan the canvas as its
   region aria-label states. "Loaded abilities in preparation order" implements
   per-card spatial navigation along preparation edges (ArrowRight = nearest
   dependent). DESIGN.md's arrow-key clause covers segmented selection groups;
   neither group is one, so this is recorded, not attacked.
3. **`reloadStore()` throws after rendering when a refresh fails**
   (`src/main.ts:510`); the event-driven refresh path catches and notifies it.
   Probes follow the app's own catch-and-continue path. Consistent with the
   store's retain-last-valid-snapshot contract.

## ASSUMPTIONS

- The fixture's stale question is stale *because* `concept-bayes--derives--concept-frequentist-inference` is absent from `fixture-vault/generated/manifest.json` `relations` (verified by direct JSON inspection) and `relationByIdentity` keys relations exactly as `${from}--${type}--${to}` (verified in `src/features/atlas/questions.ts:60`).
- "Every interactive element" is operationalized as native controls plus
  `role=button`/`summary`; accessible name as aria-label / title / text /
  placeholder (probe4 header comment records the exact rule).
- "Short" Today/Continue lists are taken from the render code's own slices
  (`focus.ts:218` slice(0,2)+review row, slice(0,4); `elsewhere.ts:116`
  slice(0,5)); the probes assert the on-screen counts stay within those bounds.
- The two bundled suites that already guard pieces of this scope
  (`navigation-review-atlas.js:641` orphan-row text; `shelving-resilience.js:189`
  offline Home) were read, not re-run; my probes are independent of them.

## Command transcript

One node process at a time, cwd `~/los-glm-V2-2026-10/obsidian-ui`, no xdist:

```
node <V2>/probes/probe1-mount-all-views.js     # exit 0 — 18 mounts, all render
node <V2>/probes/probe2-rule2-states.js        # exit 0 — 2A/2B/2C all pass
node <V2>/probes/probe3-optional-fields.js     # exit 0 — 15 mounts, no throw
node <V2>/probes/probe4-accessibility.js       # exit 0 — names + 19 keyboard groups
node <V2>/probes/probe5-home-rule13.js         # exit 0 — Home shape + rule 13
node <V2>/probes/probe6-atlas-dom.js           # exit 0 — orphan/remainder/inspector/domains
```

Full outputs in `logs/*.log`. Probes live in `probes/` (`common.js` shared
helpers). No finding folders: zero findings.

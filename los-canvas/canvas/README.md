# LearningOS Testing Canvas

An isolated, disposable test bench for LearningOS Core and the Obsidian UI.
It exists to answer one question with measurements instead of arguments:

> **If an AI agent is the librarian and the human only consumes through the
> UI, does this system behave the way its operator contract says it does —
> and where does it fail to?**

Everything here is synthetic. The operator's real tree is never opened.

## Layout

```
LearningOS/repository/      clone of the Core repo, with its own .venv
LearningOS/obsidian-ui/     clone of the UI repo
canvas/                     the harness
  lib/canvaslib.py          world builder + gateway driver
  lib/runner.py             the small report runner
  t01_entry_points.py       every OPERATOR.md "Start here" row
  t02_filing_journey.py     one complete filing session, costed
  t03_adversarial.py        21 probes that try to make the system misbehave
  t04_consumption_seam.py   what a UI-only consumer can see
  t05_masters_promotion.py  workflow 27: can an agent promote a module?
  t06_term_boundary.py      workflow 24: what can the agent do at a boundary?
  t07_ui_consumes_canvas.py the UI consuming a canvas world, at runtime
  bootstrap.sh              rebuild the clones, the venv and node_modules
  run-all.sh                run all seven suites
worlds/                     every synthetic world the suite built
reports/                    JSON + Markdown per suite, and FINDINGS.md
```

## Running it

```bash
./canvas/bootstrap.sh     # only on a fresh checkout of this harness
./canvas/run-all.sh       # 78 cases across seven suites
```

Each suite builds its own fresh worlds; re-running is safe (world
directories are recreated). The clone's own suite, for faithfulness:

```bash
cd LearningOS/repository && .venv/bin/python -m pytest -q
```

**One caveat:** the paired Core↔UI contract tests shell out to Node + Ajv
against the *sibling* UI checkout, and `node_modules` is gitignored. An
isolated UI clone therefore needs it copied in, or those tests fail with
`Cannot find package 'ajv'` — a clone artifact, not a system defect:

```bash
cp -R /path/to/obsidian-ui/node_modules LearningOS/obsidian-ui/node_modules
```

## The rules the harness holds itself to

1. **Isolation.** The only paths written are under this directory. The
   operator's checkout is cloned, never built in.
2. **Synthetic data.** Worlds come from the system's own characterization
   fixture (`tests/scenario_fixtures.py:rich_world`) plus synthetic content
   the suites add. No operator data is used.
3. **Writes go through the gateway.** Every canonical write is a sealed
   `GatewayEnvelopeV2` applied with `los capability`. The only direct file
   writes are in the fail-closed probes, where corrupting a file *is* the
   adversarial act.
4. **Refusals are results.** A probe that ends with the system refusing is a
   pass. A probe that ends with the system doing the wrong thing is recorded
   as a finding with the exact output, not smoothed over.
5. **No claim without a number.** Every assertion in `FINDINGS.md` is
   traceable to a case in `reports/`.

## The findings

See [`../reports/FINDINGS.md`](../reports/FINDINGS.md).

Short version:

* **F-01 (high).** An agent can author the scope authority that workflow 23
  declares a human must supply. Measured as a five-rung ladder: rungs A–D
  are refused (structural guards), rung E — extend a map by one stage of the
  agent's own devising — is **accepted**.
* **F-02 (low-medium).** The resume screen names the requirement twice
  under two labels; the label "Requirement" carries the concept, which the
  write path refuses. (The id is on the same screen, under "Next".)
* **F-03 (medium-low).** A note body carrying its own frontmatter yields a
  note with two frontmatter blocks; validation passes and the published
  summary becomes the stray YAML.
* **F-04 (low).** `material://…#fragment` is accepted by the write path and
  warned by the validator — two resolvers, two answers.
* **Correction.** The UI *does* render a note's provenance bindings. The seam
  is the body (2.5 % of corpus text is reachable from the app), not the
  audit trail.
* **F-05 (high).** Workflow 27's `official-academic` verification is a
  *shape* check. The canvas promoted a Master's module on a URL that cannot
  resolve. Every other gate on that path is real.
* **F-06 (positive).** Workflow 24's human steps are enforced by *absence of
  capability*: no capability can retire a workspace or dispose of a garden
  seed, so the agent cannot sweep the Garden at a term boundary.

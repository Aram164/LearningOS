# G8 source-binding coverage audit — module-job-python-engineering — 2026-11-10

Canonical audit destination: `work/active/python-plan-2026-11-02/outputs/g8-coherence-2026-11-10-coverage-audit.md`. Draft package remains outside Core. Reviewer: Codex, 2026-11-10.

Scope: only the current source map, the listed affected units and their existing resource rows. This is a binding repair, not a new syllabus or a source-quality evaluation. Existing material labels, URLs, locators, stage order, exercises, triage and progress are preserved. Local artifact pointers become reference pointers. Source-less exercises remain practise. New material routes explicitly use unassessed depth and unevaluated scope.

## Local

Every target row with a local material URI was opened: notebook cell source without execution, cited PDF page spans, and the local SHELF Markdown. Authored notes/stage guides were opened only to establish pointer identity; their contents are unchanged. No Stratum sibling code was inspected. The exact inventory below retains each row and locator, including duplicate uses. Material hashes and read scopes are in the external `local-material-observations.json` and `local-evidence.json`; admission evidence is carried in this package.

| Unit / stage / index | Item | Local target | Disposition |
|---|---|---|---|
| unit-job-python-engineering-fluency / stage-python-00-mechanism-diagnostic / 0 | Cold diagnostic stage-0-names-and-identity.ipynb | `material://source-python-depth-drills/stage-0-names-and-identity.ipynb` | preserved deferred; bound route |
| unit-job-python-engineering-fluency / stage-python-00-mechanism-diagnostic / 1 | Cold diagnostic stage-1-functions-as-objects.ipynb | `material://source-python-depth-drills/stage-1-functions-as-objects.ipynb` | preserved deferred; bound route |
| unit-job-python-engineering-fluency / stage-python-00-mechanism-diagnostic / 2 | Cold diagnostic stage-2-scope-and-closures.ipynb | `material://source-python-depth-drills/stage-2-scope-and-closures.ipynb` | preserved deferred; bound route |
| unit-job-python-engineering-fluency / stage-python-00-mechanism-diagnostic / 3 | Cold diagnostic stage-3-decorators.ipynb | `material://source-python-depth-drills/stage-3-decorators.ipynb` | preserved deferred; bound route |
| unit-job-python-engineering-fluency / stage-python-00-mechanism-diagnostic / 4 | Cold diagnostic stage-4-classes-as-objects.ipynb | `material://source-python-depth-drills/stage-4-classes-as-objects.ipynb` | preserved deferred; bound route |
| unit-job-python-engineering-fluency / stage-python-00-mechanism-diagnostic / 5 | Cold diagnostic stage-5-imports-and-registration.ipynb | `material://source-python-depth-drills/stage-5-imports-and-registration.ipynb` | preserved deferred; bound route |
| unit-job-python-engineering-fluency / stage-python-00-mechanism-diagnostic / 6 | Cold diagnostic stage-6-data-model-and-dunders.ipynb | `material://source-python-depth-drills/stage-6-data-model-and-dunders.ipynb` | preserved deferred; bound route |
| unit-job-python-engineering-fluency / stage-python-00-mechanism-diagnostic / 7 | Cold diagnostic stage-7-generators-and-iterators.ipynb | `material://source-python-depth-drills/stage-7-generators-and-iterators.ipynb` | preserved deferred; bound route |
| unit-job-python-engineering-fluency / stage-python-00-mechanism-diagnostic / 8 | Cold diagnostic stage-8-interfaces-and-dispatch.ipynb | `material://source-python-depth-drills/stage-8-interfaces-and-dispatch.ipynb` | preserved deferred; bound route |
| unit-job-python-engineering-fluency / stage-python-repair-mechanism-gaps / 9 | Fluent Python, opened at the chapter a miss names | `material://source-fluent-python/fluent-python.pdf` | preserved deferred; bound route |
| unit-job-python-engineering-fluency / stage-python-repair-mechanism-gaps / 10 | Effective Python, opened at the item a miss names | `material://source-slatkin-effective-python/effective-python.pdf` | preserved deferred; bound route |
| unit-job-python-engineering-fluency / stage-python-repair-mechanism-gaps / 11 | Cross-cutting shelf index | `material://source-python-depth-drills/SHELF.md` | preserved deferred; bound route |
| unit-job-python-engineering-fluency / stage-python-14-packaging-environments-maturin-and-the-python-to-rust / 0 | Required core — note-python-intermediate-roadmap.md | `knowledge/notes/programming/note-python-intermediate-roadmap.md` | reference pointer |
| unit-job-python-engineering-fluency / stage-python-14-packaging-environments-maturin-and-the-python-to-rust / 2 | Local material — note-programming-toolbox-bootcamp.md | `knowledge/notes/programming/note-programming-toolbox-bootcamp.md` | reference pointer |
| unit-job-python-engineering-fluency / stage-python-14-packaging-environments-maturin-and-the-python-to-rust / 3 | Local material — effective-python.pdf | `material://source-slatkin-effective-python/effective-python.pdf` | preserved deferred; bound route |
| unit-job-python-engineering-fluency / stage-python-16-api-design-boundaries-and-refactoring / 1 | Effective Python — interfaces, composition, and maintainability | `material://source-slatkin-effective-python/effective-python.pdf` | preserved deferred; bound route |

## Linked

Opened every URL in the affected rows at its primary owner on 2026-11-10. The table gives exactly what was checked; opening a landing page does not claim that a full video or future code lab was completed. No link or material was silently removed.

| URL | Opened evidence and limits |
|---|---|
| https://arxiv.org/abs/2603.03589 | Opened arXiv author/title/abstract; identifies the graph compiler, heterogeneous backends and prototype. Local PDF backs exact section quotations below. No sibling code inspected. |
| https://docs.python.org/3/howto/logging-cookbook.html | Opened official page and topic/API sections on 2026-11-10. Preserved the original unpinned URL; no installed-version or execution claim. |
| https://docs.python.org/3/library/asyncio.html | Opened official page and topic/API sections on 2026-11-10. Preserved the original unpinned URL; no installed-version or execution claim. |
| https://docs.python.org/3/library/graphlib.html | Opened official page and topic/API sections on 2026-11-10. Preserved the original unpinned URL; no installed-version or execution claim. |
| https://docs.python.org/3/tutorial/errors.html | Opened official page and topic/API sections on 2026-11-10. Preserved the original unpinned URL; no installed-version or execution claim. |
| https://github.com/HypothesisWorks/hypothesis | Opened primary README: strategies, generated edge cases and shrinking example. No particular future strategy implementation was selected or executed. |
| https://github.com/cosmicpython/book | Opened authors’ book repository and contents: domain model, abstractions, service layer, TDD, and the code submodule. No full code trace asserted. |
| https://github.com/encode/httpx | Opened primary README: sync/async APIs, transport dependency, timeouts and source/tests entries. No future request trace or runtime behavior was claimed verified. |
| https://github.com/hynek/structlog | Opened primary README: function/dictionary transformations and structured logging, plus src/structlog and tests entries. Processor runtime tracing remains the deferred lab. |
| https://github.com/networkx/networkx/blob/main/networkx/algorithms/dag.py | Opened primary source, topological_generations docstring and generator body. The future learner trace through corresponding tests remains deferred. |
| https://github.com/pydantic/pydantic | Opened primary project README and pydantic/pydantic-core/tests tree entries. Detailed validation-path tracing remains a deferred learner lab, not an operator claim. |
| https://github.com/pytest-dev/pluggy | Opened primary README hook specification, implementations, registration and invocation example. No future change or test was invented. |
| https://github.com/pytest-dev/pytest/blob/main/CONTRIBUTING.rst | Opened primary contributing guide: bug reports, reproductions, tests and feature contributions. A future small merged change remains the learner’s choice. |
| https://packaging.python.org/en/latest/tutorials/packaging-projects/ | Opened official tutorial: src package layout, pyproject, build backends, distribution artifacts. No package was built or uploaded. |
| https://people.csail.mit.edu/matei/papers/2015/sigmod_spark_sql.pdf | Opened author-hosted paper, abstract and §4 pp. 4–5: Catalyst trees, transformation rules, logical and physical planning. No claim of equivalence to Stratum. |
| https://skrub-data.org/stable/reference/data_ops.html | Opened official data_ops reference and its DataOp/skb API index. No assertion about an installed skrub version. |
| https://www.cosmicpython.com/book/preface.html | Opened author preface and contents: testable business logic, domain modelling, repository and service-layer chapters. |

## Completeness

- Existing module unit order and every affected stage/resource position are unchanged. All resource rows survive; only binding fields and truthful pointer kinds change.
- Every original material, exercise, URL, note pointer, artifact and deferred item remains reachable. Source selections stay as authored; new reference-only dispositions use scope_sources, not invented learner choices.
- Current/prior boundaries remain as authored. Historical article dates and the original Polars 1.x notebook warnings remain visible; no compatibility or current-version claim was inferred.
- Duplicate uses remain separate placement rows. New source/unit/material/locator duplicates share one route and preserve their complete node union. Existing unrelated routes remain byte-for-byte equal as parsed data.
- Rich-route covers point only at the pre-existing stage knowledge node, verified to exist in the unit. Evidence is limited to that factual topic binding. No new knowledge node, concept relation, source evaluation, mastery or assessment was invented.
- Local notebook quotation is unsupported; its explicit fallback is registered-manifest binding after opening the cells. Plain Markdown uses the new strict line-range quote support and therefore needs that Core fix before preflight/apply.
- Detailed future code walkthroughs, video playback, code execution, learning outcomes and quality ranking remain unassessed. This audit asserts only the declared bounded content checks above, not completion of the learner’s activities.
- Preflight, source-intake apply, audit installation, gateway apply, receipt verification, warning ratchet and hosted acceptance are not performed by this drafting agent.

Counts: 40 affected placements; 33 placements bound; 7 artifact pointers correctly typed; 33 new routes across 1 existing units.

Exact-target review: New routes distinguish verified material addresses from the unchanged study placement locators and wording. File-wide PDF bounds describe reference availability, with the placement retaining any existing condition or deferred action. Four unselected routes for Batchelder, pytest, Python typing and uv complete the already-declared reference scope. The original unit remains paused and its placements are unchanged.

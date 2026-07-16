# Chat 4: PPDS Project — ML Data Provenance (mlprov) Step-by-Step Plan

*Generated: 22 April 2026 (KW 17) | Built from mlprov repo + Praxisplan + Chat 1/2/3 plans*
*Updated: 10 Jun 2026 (KW 24) — sklearn sprint section added (the current plan); KW 23 table + Phase 3 superseded*
*Status: 7/20 tests green (Phase 1 + partial Phase 2 done). Remaining work = sklearn sprint M.3.0–M.3.8. Deadline: 15 Jul 2026.*

---

## Step ID Convention

All steps in this plan use the prefix **M** (Mlprov). Reference format: **M.{Phase}.{Step#}**

| ID | Meaning | Example |
|---|---|---|
| M.1.0.1 | Phase 1, Step 0.1 (clone and orient) | "Completed M.1.0.1" |
| M.2.2.2 | Phase 2, Step 2.2 (merge/join with provenance) | "Working on M.2.2.2" |
| M.4.3.1 | Phase 4, Step 3.1 (GroupFairness impl) | "Starting M.4.3.1" |
| M.6.5 | Phase 6, Step 5 (submit) | "M.6.5 done!" |

**Python prerequisite steps** use prefix **PY**: PY.01 (FP Ch 1) through PY.14 (FP Ch 18).

**When updating SEMESTER-STATUS.md:** write step IDs exactly as above. This chat (the brain) uses them to track dependencies.

**⚠️ Critical prereq note:** FP Ch. 14 (Inheritance, PY.08) is needed before Phase 1 begins. Prioritize reading at least the "Subclassing Built-In Types" section of Ch. 14 alongside Ch. 1 and Ch. 11, even if the full chapter comes later in the reading sequence.

> **Optional supplement:** [TU Python-for-ML Sheet 2](https://github.com/mahmutoezmen/Python-for-ML-Course/tree/main/2.%20Sheet) — covers inheritance, NumPy, performance, and plotting in Python. Directly relevant to ProvDataFrame (subclassing pd.DataFrame) and the NumPy operations mlprov must track. Do before or during Phase 1.

---

## Why This Plan Exists

The PPDS mlprov project is not a "build a classifier" project — it's a **software engineering and data systems** challenge. You're building a library that wraps pandas, NumPy, and scikit-learn to track *provenance* (which rows from which source tables contributed to each output row) through an entire ML pipeline. This requires deep understanding of Python's object model (inheritance, special methods, monkey-patching), pandas internals, and the sklearn API contract — skills you're building in parallel via Fluent Python and the Bootcamp.

The danger is twofold: (1) starting without enough Python OOP fluency and fighting the language instead of the problem, or (2) implementing each operator in isolation without understanding how provenance propagates through the pipeline as a whole. This plan threads the needle: it maps each implementation phase to the Python and theory prerequisites you need *before* starting, and shows how each phase builds on the previous one.

**Job synergy:** mlprov is provenance tracking for ML pipelines — the same domain as Stratum and mlinspect. Engineering patterns here (instrumenting sklearn, DAG traversal, pipeline introspection) transfer directly to your job. See **Chat 6** (Plans/crosscutting/job/Chat6_Job_Onboarding_Plan.md) for the dedicated job onboarding plan.

---

## The Project at a Glance

**What:** Build `mlprov` — a drop-in replacement for `pandas`, `numpy`, and `sklearn` that tracks row-level provenance through ML pipelines. Then use that provenance to detect data leakage, answer GDPR queries, and assess group fairness.

**Core idea:** Every DataFrame operation (select, project, join, transform) produces output rows that originate from specific input rows. mlprov tracks this mapping as a *provenance DataFrame* where each row stores which source-table rows contributed to it. When you later ask "which training rows influenced this prediction?", provenance gives you the answer.

**Deliverables:**

| Component | Purpose | Key Files |
|-----------|---------|-----------|
| `ProvDataFrame` | pandas DataFrame wrapper with provenance | `mlprov/pandas/_wrappers.py` |
| Loaders | Provenance-aware `read_csv`, etc. | `mlprov/pandas/_loaders.py` |
| ProvenanceMixin | Shared interface for provenance-bearing objects | `mlprov/_prov_mixin.py` |
| MLProvManager | Singleton storing all provenance artifacts | `mlprov/_prov_manager.py` |
| sklearn wrappers | Provenance-aware `fit`, `predict`, `score` | `mlprov/sklearn/` |
| NumPy wrappers | Provenance-aware array operations | `mlprov/numpy/` |
| DataLeakage | Detect train/test data leakage via provenance | `mlprov/prov_analysis/` |
| GDPRCompliance | "Have I been trained on this row?" queries | `mlprov/prov_analysis/` |
| GroupFairness | Recover sensitive attributes for fairness analysis | `mlprov/prov_analysis/` |
| DuckDB backend | Performance optimization for joins/selections | `mlprov/` (your design) |
| Documentation | Code docs + performance report | — |
| Presentation | Final project presentation | — |

**Grading criteria:** Supported operators/libraries, correctness (tests pass), performance vs. vanilla pandas/sklearn, number of provenance applications, code quality.

---

## How This Project Connects to Your Other Courses

This project sits at the intersection of data systems (PPDS/DBT), ML systems (AMLS), and ML theory (AML). The table below shows where each phase draws from — these are concrete connections, not abstract ones.

| Project Phase | AML/SaD Theory (Chat 1) | AMLS Systems Theory (Chat 2) | Python Skills (Bootcamp + FP) | Job synergy (→ Chat 6) |
|---|---|---|---|---|
| **Phase 1: Core Infrastructure** | — | L01–L02: ML lifecycle, where data prep fits in the stack | FP Ch. 1 (data model: `__repr__`, `__getitem__`), Ch. 11 (Pythonic objects), Ch. 14 (inheritance) | Same patching pattern as Stratum (JK.3.1) |
| **Phase 2: Data Operations** | SaD 03: joins/merges in data analysis context | L10: data cleaning, feature transforms — the system pipeline view of what you're instrumenting | FP Ch. 2 (sequences), Ch. 3 (dicts), pandas API fluency | Same ops as skrub DataOps (JK.2) |
| **Phase 3: ML Pipeline Integration** | Block I: logistic regression (the model you'll wrap). Block D: train/test split (what your provenance tracks across). | L10–L11: the full ML pipeline from data prep → model selection. Your wrappers instrument this pipeline. | FP Ch. 9 (decorators — wrapping functions), Ch. 13 (protocols/ABCs — sklearn estimator interface) | Same adapter pattern as Stratum (JK.3.4) |
| **Phase 4: Provenance Applications** | Block A (SaD 01): precision/recall vocabulary for fairness metrics. Block D: train/test leakage = "test rows in training set" | L12: LIME, SHAP, SliceLine, fairness constraints, EU AI Act — your GDPR/fairness analyses are the provenance-based version of what L12 teaches | Set operations, DataFrame merging, index manipulation | mlinspect is the academic ancestor of Stratum (JK.0.3) |
| **Phase 5: DuckDB Optimization** | — | L03: operator selection (choosing the fastest backend). L09: caching, indexing, compression. L05: data-parallel execution. | SQL via DuckDB Python API, DataFrame ↔ SQL translation | Same thesis as Stratum: replace slow ops with faster backends (JK.3.3) |

---

## Prerequisite Dependency Graph

```
BOOTCAMP (KW 17–18)
  Python fluency, venv, pytest, Docker basics, git
  │
  ├──────────────────────────────────────────────────────────────┐
  ▼                                                              │
FP Ch. 1 (data model) + Ch. 11 (Pythonic objects)               │
  │                                                              │
  ▼                                                              │
FP Ch. 14 (inheritance) + FP Ch. 6 (references, mutability)     │
  │                                                              │
  ▼                                                              │
PHASE 1: Core Infrastructure (KW 19–20)                         │
  ProvDataFrame, read_csv, ProvenanceMixin, MLProvManager        │
  Needs: pandas API (read_csv, DataFrame basics)                 │
         Python inheritance + special methods                    │
         pytest from Bootcamp                                    │
  │                                                              │
  ▼                                                              │
PHASE 2: Data Operations (KW 21–22)                             │
  __getitem__ (projection/selection), merge/join + provenance    │
  Needs: Phase 1 (ProvDataFrame exists)                          │
         pandas indexing deep knowledge                          │
         FP Ch. 2 (sequences — __getitem__ protocol)             │
         Set operations for provenance propagation               │
  │                                                              │
  ├──────────────────────────────────┐                           │
  ▼                                  ▼                           │
PHASE 3: ML Pipeline Integration   FP Ch. 9 (decorators)        │
  (KW 23–24)                        FP Ch. 13 (protocols/ABCs)  │
  NumPy wrappers, sklearn wrappers,  │                           │
  fit/predict/score + provenance     │                           │
  Needs: Phase 2 (data ops work)     │                           │
         sklearn API (Chat 1 Block I │                           │
         + Praxisplan Phase 2 KW 19) │                           │
         Chat 2 Block B–C (optional, │                           │
         deepens understanding)      │                           │
  │                                  │                           │
  ├──────────────────────────────────┘                           │
  ▼                                                              │
PHASE 4: Provenance Applications (KW 24–26)                     │
  DataLeakage, GDPRCompliance, GroupFairness                     │
  Needs: Phase 3 (MLProvManager populated with provenance)       │
         Chat 1 Block D (train/test split — why leakage matters)│
         Chat 2 Block G (fairness, L12 — arrives KW 28, late!)  │
         Understanding of set intersection (leakage detection)  │
  │                                                              │
  ▼                                                              ▼
PHASE 5: DuckDB Optimization (KW 26–28) ◄─── Chat 2 Block B (compilation,
  Replace slow pandas joins/selections       operator selection, rewrites)
  with SQL via DuckDB                        Chat 2 Block E (caching,
  Needs: Phase 2+ working correctly          indexing, compression)
         SQL basics (from DBT, if taken)     Chat 6 JK.3.3: Stratum's
         DuckDB Python API                   optimizer does exactly this
  │
  ▼
PHASE 6: Polish + Submit (KW 28–29)
  Code cleanup, documentation, presentation
  Needs: All phases working
         All tests passing
```

**The critical path** runs through Phases 1–3. Phase 1 (infrastructure) must be solid before anything else works — a buggy `ProvDataFrame` will cascade into every later phase. Phase 3 (sklearn integration) is the most technically demanding because you need to understand how sklearn's `fit`/`predict`/`score` contract works and intercept it cleanly. Phase 4 (applications) is where the project becomes interesting and earns its points.

**The Python OOP dependency** is the thing that can block you earliest. Phases 1–2 rely heavily on `__getitem__`, `__repr__`, inheritance, and special methods. If Fluent Python Ch. 1, 11, 14 aren't done by KW 19, you'll fight the language instead of solving the problem.

---

## 🎯 KW 24 SKLEARN SPRINT (Jun 10) — THE CURRENT PLAN (supersedes the KW 23 table below)

> **Added 2026-06-10 (KW 24), grounded by running the test suite and reading every sklearn skeleton + test file.** Verified state: **7 tests pass, 13 fail** (+ `test_fairness.py` needs `fairlearn` — it's in `mlprov_env`, only missing outside it). Done: utils ✅, loaders ✅, ndarray ✅, DataFrame init+projection ✅. **Everything remaining funnels through sklearn**, and it's more tractable than the old plan suggested — the skeleton has already made the hard design decisions for you.

### What the skeleton already decided (stale plan assumptions — corrected)

1. **Wrapper strategy is chosen: subclassing (approach a).** Every sklearn skeleton class is `class X(orig_sklearn.X, ProvenanceEstimator)`. The old "decide between subclass/generic wrapper/monkey-patch" step (3.1.2) is dead. **Consequence: PY.10 (decorators) is NOT a prerequisite anymore.** PY.11 (ABCs) is a light optional read — the ABCs are already written in `_prov_mixin.py`.
2. **The provenance model is table-id based** (not the generic model described in Phase 1 below): `provenance` is a plain pandas DataFrame whose **column name = global table id** (string, from `MLProvManager().get_next_table_id()`) and values = source row indices. Every *genuine* new table (a `DataFrame.__init__` or `ndarray.__new__` without `provenance=`) consumes a fresh id and registers itself via `register_input_table`. **Derived results must NOT consume a new id** — they carry the input's provenance forward.
3. **All required transformers are row-preserving** (SimpleImputer, OneHotEncoder, StandardScaler, label_binarize, ColumnTransformer): output row i comes from input row i, so **provenance passes through unchanged**. The implementation pattern for *every* transform is identical:
   `result_wo_prov = orig.transform(...)` → wrap as `ndarray(result_wo_prov, provenance=X.provenance)` → return. No joins, no set logic. This is ~5 small variations of one function.
4. **Why manual re-wrapping is needed at every step:** sklearn's internal `check_array` validation converts inputs to plain numpy → provenance is stripped *inside* sklearn. You can't make it flow implicitly; you re-attach it on the way out. That's the whole trick.
5. **`train_test_split` wrapping (old step 3.2.4) is NOT in the test suite.** The tests load pre-split `adult_train.csv`/`adult_test.csv`. Don't build it unless a test demands it.

### One real design fix before sklearn: derived-frame construction

`DataFrame.__init__` *always* mints a new table id and registers an input table — even for frames derived from operations. The `__getitem__` list-branch calls `DataFrame(x)` and then overwrites `.provenance`, leaving a phantom id + bogus registry entry. **Fix first** (everything else builds on it): honor a `provenance=` kwarg in `DataFrame.__init__` (mint a new id ONLY when none is given — same pattern `ndarray.__new__` already uses correctly).

### Known bugs in `pandas/_wrappers.py __getitem__` (blocks `test_dataframe_selection`)

- bool-mask branch: `result` is never assigned the filtered *data* (`result = None` → `AttributeError`). Need `super().__getitem__(key)` → derived DataFrame → filtered provenance.
- provenance filter is right in spirit: `self.provenance[mask].reset_index(drop=True)` keeps original source indices as *values* — the test expects `{"0": [1, 3]}`, NOT re-numbered.
- list-of-cols branch: `super(self)` → `super()`; and use the new derived-construction path instead of `DataFrame(x)` + overwrite.

### The sprint, in dependency order (each step = one green test file)

Run from `Project/`: `source mlprov_env/bin/activate && pytest test/<target> -x`

| # | Step | Target test | Files | What to do | Gotchas | Est. |
|---|---|---|---|---|---|---|
| 1 | **M.3.0 Fix DataFrame derive + `__getitem__`** | `test_pandas/test_dataframe.py` | `pandas/_wrappers.py`, `_prov_mixin.py` | provenance kwarg in `__init__`; fix 3 bugs above | `df["age"] > 30` yields an mlprov `Series` (via `_constructor_sliced`) — the `OrigSeries` isinstance branch catches it. Don't reset provenance *values* | 1.5h |
| 2 | **M.3.1 ScoreResult** | `test_score_result.py` | `_prov_mixin.py` | `__init__`: store `test_predictions`, `test_labels` as attrs (they're already prov-ndarrays). Don't touch `__new__` | float subclass: `__init__` must not call `super().__init__(score)` weirdly — just set attrs | 0.5h |
| 3 | **M.3.2 Mixin + manager state** | — (enables 5–7) | `_prov_mixin.py`, `_prov_manager.py` | `ProvenanceClassifier.__init__`: replace `raise` with `pass`/registration. Manager: add dicts keyed by `id(obj)`: classifier→(train_X, train_y), classifier→test_X, score→(preds, labels) | conftest `reset()` must clear the new dicts too | 1h |
| 4 | **M.3.3 Row-preserving transformers** | `test_sklearn/impute`, `test_sklearn/preprocessing` | `impute/_simple_imputer.py`, `preprocessing/simple.py` | One shared helper: call orig method, wrap result as `ndarray(result, provenance=X.provenance)`. `fit_transform` = same. `label_binarize`: result provenance = `y.provenance` | OneHotEncoder may return sparse — tests do `allclose` on dense; densify (`.toarray()`) before wrapping. StandardScaler gets a *DataFrame* in its test — read `.provenance` generically | 2.5h |
| 5 | **M.3.4 ColumnTransformer (+Pipeline)** | `test_sklearn/compose` | `compose/_column_transformer.py` | Same pass-through pattern: orig `fit_transform`, wrap with input provenance. `Pipeline` subclass stays `pass` — its steps are already prov-aware *from the outside* | Nested Pipeline inside ColumnTransformer runs sklearn-internally (provenance stripped inside) — fine, you re-attach at the CT boundary | 1.5h |
| 6 | **M.3.5 load_iris + DecisionTreeClassifier** | `test_sklearn/test_tree` | `datasets/_base.py`, `tree/_decision_tree_classifier.py` | `load_iris`: wrap `.data` and `.target` as fresh prov-ndarrays (ids 0,1). `fit`: record (X,y) in manager, return self. `predict`: orig predict → wrap with `X.provenance`, record X as test data. `score`: predict → accuracy → `ScoreResult(acc, preds, y)`, record in manager | `score` skeleton calls `predict` not `score` — compute accuracy yourself or call orig score separately. Iris: data gets id "0", target id "1", test ndarray id "2" — creation ORDER matters | 2h |
| 7 | **M.3.6 Manager getters** | `test_prov_manager/test_get_provenance.py` | `_prov_manager.py` | Implement the 6 `get_*` methods from the dicts of step 3. `get_source_tables_for_classifier_and_eval`: map table-id → registered input table for every id appearing in the classifier's + score's provenance columns | Test asserts *types*: training data back as `pd.DataFrame` (mlprov), labels as `ndarray` — return the stored originals, not copies | 1.5h |
| 8 | **M.3.7 Full pipeline green** | `test_full_pipeline_prov.py` | debugging only | Run both tests; chase provenance breaks through the nested Pipeline/CT chain | `nested_feature_transformation.fit_transform(test_data)` re-fits — that's what the test does; provenance must still be `{"1": …}` | 2h |
| 9 | **M.4.x Analyses (Fairness is GRADED — it has a test)** | `test_prov_analysis/test_fairness.py` | `prov_analysis/Fairness.py`, then `DataLeakage.py`, `DataUsage.py` | Fairness: use test-data provenance to index back into the source table (id from provenance column) → recover `sensitive_columns` ("sex") for exactly the test rows → `fairlearn.metrics.MetricFrame(metrics=…, y_true=test_labels, y_pred=predictions, sensitive_features=recovered)` | This is the ONE place provenance does real work (recovering a dropped column). `fairlearn` already in `mlprov_env`. DataLeakage = provenance-set intersection train∩test; DataUsage = which source rows of table_id were used | 3h |
| 10 | **M.3.8 Example pipelines** | `test_example_pipelines.py` | `example_pipelines/` | These exec *vanilla* pandas/sklearn scripts (not mlprov) — failures are env/deps (scikeras, sentence_transformers), likely green in `mlprov_env` already. Verify, don't build | Run them FIRST — may already pass on your machine | 1h |

**Total: ~17h core (steps 1–8) + ~4h analyses/verify.** That's dramatically less than the old "~30h+ for Phases 3–4" estimate, because the test surface is narrower than the generic phase plan assumed.

### Week mapping (fits §7 of SEMESTER-STATUS)

- **KW 24 (now, seminar owns priority):** steps 1–4 in ~3 slots of 2h. Even just step 1+2 keeps momentum.
- **KW 25 (seminar delivered Jun 18):** steps 5–7.
- **KW 26:** steps 8–9 → **full suite green ~3 weeks before the deadline.**
- **KW 27–28:** DataLeakage/DataUsage polish, docstrings, perf note, presentation. DuckDB stays CUT unless everything is green with time to spare.
- **KW 29:** submit before Jul 15.

### Triage rules (updated)

1. Green test > clean code. The graded surface is the test suite.
2. If a week slips: cut DataLeakage/DataUsage *implementations* last-resort only — Fairness has a test, it is NOT cuttable.
3. Steps 1–3 are the foundation of everything after — never skip ahead past a red `test_dataframe.py`.
4. sklearn week needs **no new PY chapters** — PY.10/11 are now optional enrichment, not blockers.

---

## ⚠️ KW 23 RE-BASELINE — Test-Driven Catch-Up Plan — ⚠️ SUPERSEDED by KW 24 sprint above (reference only)

> **Added 2026-06-03 (KW 23). SUPERSEDED 2026-06-10 by the KW 24 SKLEARN SPRINT above — follow that instead.** Historical context: at KW 23 the repo was believed 0% implemented; by Jun 5 Phase 1 + partial Phase 2 were verified done, and the KW 24 audit re-scoped the remaining work around the actual test suite. The table below over-estimates the sklearn block (assumed PY.10/11 prereqs + generic wrapper design work that the skeleton already settled).

**Strategy: let the provided test suite be the spec.** The graded surface is almost certainly "does it pass the tests." Implement in dependency order so each step unblocks the next, and run the matching test file as your definition of done. Existing test files (your checklist):

`test/utils/test_utils.py` · `test/test_loaders.py` · `test/test_pandas/test_dataframe.py` · `test/test_numpy/test_ndarray.py` · `test/test_score_result.py` · `test/test_sklearn/{impute,preprocessing,compose,test_tree}/…` · `test/test_prov_manager/test_get_provenance.py` · `test/test_prov_analysis/test_fairness.py` · `test/test_full_pipeline_prov.py` · `test/test_example_pipelines.py`

| KW | Target tests to turn green | Implement (skeleton files to fill) | PY prereq | Hours |
|----|---------------------------|-------------------------------------|-----------|-------|
| **23** (now) | `test_utils`, `test_loaders` | `utils/_utils.py`; `_prov_mixin.py` (ProvenanceMixin); `_prov_manager.py` singleton skeleton; `pandas/_loaders.py` (`read_csv` + provenance init) | PY.01/02/08 ✅ done | ~5h |
| **24** | `test_pandas/test_dataframe` | `pandas/_wrappers.py`: `__getitem__` (projection = cols unchanged, selection = filter prov rows), `merge`/join (ref both source tables), `concat` | **PY.03** (sequences/`__getitem__`) — do first | ~6h |
| **25** | `test_numpy/test_ndarray`, `test_score_result` | `numpy/_wrappers.py`; `ScoreResult` in `_prov_mixin.py` | — | ~8h |
| **26** | `test_sklearn/*` (impute, preprocessing, compose, tree, pipeline) | `sklearn/impute/_simple_imputer.py`, `preprocessing/simple.py`, `compose/_column_transformer.py`, `tree/_decision_tree_classifier.py`, `pipeline/_pipeline.py` — wrap `fit`/`transform`/`predict` to record data used | **PY.10** (decorators), **PY.11** (protocols/ABCs) | ~10h |
| **27** | `test_prov_manager/test_get_provenance`, `test_full_pipeline_prov` | finish `_prov_manager.py` (full provenance chain: training/test data + predictions + source tables) | — | ~9h |
| **28** | `test_prov_analysis/test_fairness`, then `test_example_pipelines` | `prov_analysis/Fairness.py` (group fairness via provenance join), `DataLeakage.py` (train/test prov overlap), `DataUsage.py`; wire `example_pipelines/` | — | ~9h |
| **29** | full `pytest` green | docstrings, type hints, perf note, zip + **submit Jul 15** | — | ~4h |

**Triage rules if a week slips:** (1) a passing test is worth more than a clean one — get green first, refactor never. (2) `DataLeakage`/`DataUsage` analyses (Phase 4) are the most cuttable if forced — but `Fairness` has a test, so it's likely graded; do it. (3) DuckDB optimization (old Phase 5) is **cut** unless everything else is green with time to spare — it was a stretch goal, not a requirement. (4) Protect these hours by flexing AMLS internal dates with the team, not by skipping mlprov days.

**First action this week:** `cd "Plans/ML/mlprov/PPDS ML Data Provenance/Project" && source mlprov_env/bin/activate && pytest -x` to see the first failing test, then implement upward from `utils` + `loaders`.

---

## Revised Timeline (KW 19 – KW 29) — ⚠️ SUPERSEDED (reference only; the current plan is the KW 24 SKLEARN SPRINT at the top)

The Praxisplan schedules mlprov `read_csv` at KW 20. This plan keeps that timing but adds a "Phase 0" orientation step in KW 19 — reading the repo, understanding the test suite, and sketching your architecture. Starting with code in KW 19 without understanding the full provenance model is how you end up rewriting Phase 1 in KW 22.

| KW | Dates | Project Focus | Theory Arriving / Python Skills That Week | Hours |
|----|-------|--------------|------------------------------------------|-------|
| **19** | May 5–11 | **Phase 0 + Phase 1 start**: Clone repo, read README thoroughly, run existing tests, understand provenance representation (the DataFrame-of-row-indices model). Sketch `ProvDataFrame` architecture. Start `read_csv` loader. | FP Ch. 14 (inheritance) — needed for ProvDataFrame extending DataFrame. Praxisplan: sklearn API basics (KW 19). Job starts May 5 (see Chat 6) — first week is orientation, low conflict with mlprov. | ~5h |
| **20** | May 12–18 | **Phase 1 finish**: Complete `read_csv` + other loaders with provenance initialization. Implement `ProvenanceMixin` interface. Set up `MLProvManager` singleton. Pass `test_loaders.py`. | FP Ch. 9 (decorators) — useful for wrapper patterns. Chat 1 Block F+G (probability, distributions — background). | ~6h |
| **21** | May 19–25 | **Phase 2a start**: Implement `__getitem__` for projection (column selection) and selection (row filtering) on `ProvDataFrame`. Provenance must propagate correctly: selecting rows = filtering provenance rows; selecting columns = provenance unchanged. | FP Ch. 2 (sequences, `__getitem__` protocol). Chat 1 Block H (regularization) + Block J (SGD) — background for later. AMLS L05 (data-parallel exec — background). **DBT kill-switch decision end of this week.** | ~6h |
| **22** | May 26 – Jun 1 | **Phase 2b**: Implement `merge`/`join` with provenance propagation. This is the hardest data operation: a join combines rows from two tables, so the output provenance must reference row indices from *both* source tables. | Chat 1 Block K (trees, SVM — background). Chat 2 Block C (parameter servers, Adam — background). If taking DBT: relational algebra joins are exactly what you're instrumenting. | ~7h |
| **23** | Jun 2–8 | **Phase 3a**: Implement NumPy wrappers (provenance-aware array operations). Start sklearn wrappers: `fit`, `predict`, `score` that record which data was used. | Chat 1 **Block L start** (neural networks — background, but the forward-pass concept maps to pipeline flow). Chat 2 Block D (LLMs — background). FP Ch. 13 (protocols/ABCs — sklearn's estimator interface uses this pattern). | ~7h |
| **24** | Jun 9–15 | **Phase 3b + Phase 4a**: Complete sklearn wrappers. `MLProvManager` now stores full provenance chain. Start **DataLeakage** detection: check if train/test provenance sets overlap. | Chat 1 Block L finish (backprop — background). Chat 1 Block D (train/test split — directly relevant: leakage = provenance intersection ≠ ∅). | ~8h |
| **25** | Jun 16–22 | **Phase 4b**: Implement **GDPRCompliance** ("have I been trained on row X?"). Start **GroupFairness** (recover sensitive attributes via provenance join). | Chat 1 Block M (CNNs — background). Chat 2 Block E (HW, quantization — background). AMLS Project Task 1.3 running in parallel — manage time carefully. | ~7h |
| **26** | Jun 23–29 | **Phase 4c + Phase 5 start**: Finish GroupFairness. Pass all `test_prov_manager` and `test_full_pipeline_prov.py` tests. Profile performance bottlenecks. Start DuckDB integration for joins and selections. | Chat 2 **Block F** (L10: data cleaning, feature transforms — you already BUILT the instrumentation for this, now you understand the systems theory behind it). **Block F L11: model selection, augmentation.** | ~8h |
| **27** | Jun 30 – Jul 6 | **Phase 5 continue**: DuckDB optimization for hot-path operations (joins, selections). Run performance benchmarks: mlprov overhead vs. vanilla pandas/sklearn. | Chat 2 **Block G** (L12: fairness, LIME, SHAP, SliceLine — your GroupFairness analysis IS the provenance-based version of what L12 teaches). | ~7h |
| **28** | Jul 7–13 | **Phase 6**: Code cleanup, docstrings, type hints. Write performance report. Prepare presentation. Final test run. | Chat 2 Block H (model serving — background). AMLS Project also finalizing this week — split time carefully. | ~8h |
| **29** | Jul 14–15 | **Submit** (deadline Jul 15). Final checks, zip, upload. | — | ~2h |

**Total project hours: ~71h** (within budget, leaving margin for debugging and iteration)

### Why This Timeline Works

The timeline is driven by two constraints: (1) your Python OOP skills need to be ready before Phase 1, and (2) the AMLS project runs in parallel with the same deadline. The Praxisplan already coordinates these — this plan follows that coordination and adds the prerequisite detail.

The key synergy: **sklearn API knowledge flows both ways.** You learn sklearn in Praxisplan Phase 2 (KW 19) for the AMLS project, and immediately use that knowledge to build sklearn wrappers in mlprov (KW 23–24). The AMLS project teaches you what `fit`/`predict`/`score` *do*; mlprov teaches you what they do *internally* and how to intercept them.

---

## Phase-by-Phase Detailed Plan

### PHASE 1: Core Infrastructure (KW 19–20, ~11 hours)

**What you're building:** The foundation — `ProvDataFrame` (a pandas DataFrame subclass that carries provenance), `ProvenanceMixin` (the shared interface), `MLProvManager` (the global registry), and provenance-aware loaders (`read_csv`).

**Why this is foundational:** Every later phase builds on `ProvDataFrame`. If your provenance representation is wrong here, you'll rewrite everything later. Spend extra time understanding the provenance model before coding.

#### Theory Prerequisites

| Prerequisite | Source | What you need from it | When it's ready |
|---|---|---|---|
| Python data model (`__repr__`, `__getitem__`, `__len__`) | FP Ch. 1 | ProvDataFrame needs custom special methods to behave like a DataFrame while carrying extra state | ✓ KW 17 (Bootcamp/FP) |
| Inheritance in Python | FP Ch. 14 | ProvDataFrame subclasses `pd.DataFrame`. You need to understand `super()`, MRO, and when to override vs. extend. | KW 20 |
| Object references, mutability | FP Ch. 6 | Provenance DataFrames are mutable objects passed by reference. You need to understand aliasing to avoid provenance corruption when two variables point to the same ProvDataFrame. | ✓ KW 16 |
| Singleton pattern | Python docs / FP Ch. 9 | MLProvManager is a singleton. You need to understand class-level state and why a singleton is appropriate here (global provenance registry). | KW 20 |
| pandas `read_csv`, DataFrame basics | Praxisplan Phase 2, sklearn docs | You need to understand what `pd.read_csv` returns and how DataFrames work before wrapping them. | KW 19 |
| pytest | Bootcamp Day 5 | The test suite is your specification. `test_loaders.py` tells you exactly what `read_csv` must do. | ✓ KW 18 |

#### Bootcamp Prerequisites (already covered — just verify)

- [ ] Can create a Python class with `__init__`, `__repr__`, `__getitem__` — *Bootcamp + FP Ch. 1*
- [ ] Can use pytest: run tests, read assertions, write simple test functions — *Bootcamp Day 5*
- [ ] Can use git: clone repo, create branch, commit — *Bootcamp Day 3-4*
- [ ] Can create and activate a virtual environment — *Bootcamp Day 3*

#### The Provenance Model (understand this before writing code)

Provenance is stored as a DataFrame where:
- Each **row** corresponds to one output row of the operation
- Each **column** corresponds to one source input table
- Each **cell** contains the row index from that source table that contributed to this output row

Example: If you read a CSV file "customers.csv" with 5 rows, the provenance is:

```
   customers
0         0
1         1
2         2
3         3
4         4
```

After filtering rows 1, 3: provenance becomes `{1, 3}` — you keep only those provenance rows.

After joining `customers` with `orders`, the provenance has two columns:

```
   customers  orders
0          0       0
1          0       2
2          1       1
3          3       3
```

This representation is the heart of everything. Master it before coding.

#### Step-by-Step

| Step | What to do | Time | Theory link |
|------|-----------|------|-------------|
| 1.0.1 | **Clone and orient.** Clone the mlprov repo. Read the full README. Run `pip install -e .` in a venv. Run the existing test suite — note which tests exist and what they expect. Draw a diagram of the module structure (`mlprov/pandas/`, `mlprov/sklearn/`, `mlprov/numpy/`, `mlprov/prov_analysis/`). | 1.5h | — |
| 1.0.2 | **Read the test files.** Before writing ANY code, read `test_loaders.py`, `test_sklearn.py`, `test_prov_manager.py`, `test_full_pipeline_prov.py`, and `test_example_pipelines.py`. These are your specification. Write down what each test expects. | 1.5h | — |
| 1.1.1 | **Implement `ProvenanceMixin`.** This is the interface (likely an ABC or protocol) that any provenance-bearing object must implement. It should expose methods like `get_provenance()`, `set_provenance()`. Read the provided `_prov_mixin.py` skeleton carefully. | 1h | FP Ch. 13 (protocols/ABCs). The mixin pattern is how sklearn's `BaseEstimator` works too — same idea. |
| 1.1.2 | **Implement `ProvDataFrame`.** Subclass `pd.DataFrame` (this is tricky — pandas DataFrames have a complex `__init__`). Store provenance as an internal attribute. Override `__repr__` to show provenance info. Ensure slicing and copying preserve provenance. | 2h | FP Ch. 1 (data model), Ch. 14 (inheritance). The `_metadata` class attribute in pandas tells DataFrame which custom attributes to propagate through operations. |
| 1.1.3 | **Implement `read_csv` loader.** Wrap `pd.read_csv` to return a `ProvDataFrame` with initial provenance (identity mapping: row i comes from source row i). Register the loaded table in `MLProvManager`. | 1.5h | This is your first taste of "wrapping a library call and adding instrumentation" — exactly what Stratum does with its patching. |
| 1.1.4 | **Implement `MLProvManager` singleton.** Global registry that stores: (a) which tables were loaded, (b) provenance for each operation, (c) which data was used for training/testing. Must support `get_training_data_for_classifier()` and `get_test_data_for_classifier()`. | 1.5h | FP Ch. 9 (decorators — the singleton decorator pattern). |
| 1.1.5 | **Pass `test_loaders.py`.** Run tests. Debug. Ensure provenance is correctly initialized for loaded data. | 1h | pytest from Bootcamp. |

**⟷ Cross-wire to Job (Chat 6, JK.3.1):** Stratum's `_patching.py` uses the same pattern as your `mlprov/pandas/__init__.py` — intercepting library calls and routing through a custom wrapper. Stratum patches for *optimization*, you patch for *provenance tracking*. See Chat 6 Phase 3 for the full Stratum internals deep-dive.

**⟷ Cross-wire to AMLS L01–L02 (Chat 2, Block A):** AMLS L01 introduces the ML lifecycle — data acquisition → preparation → training → serving. Your mlprov library instruments this entire lifecycle. `read_csv` = data acquisition. The operations you'll add in Phase 2 = data preparation. The sklearn wrappers in Phase 3 = training. Understanding where provenance fits in this lifecycle is the conceptual foundation.

---

### PHASE 2: Data Operations with Provenance (KW 21–22, ~13 hours)

**What you're building:** Provenance-aware versions of pandas' core data operations — column selection (projection), row filtering (selection), and merge/join. These are the operations that *transform* provenance.

**Why this is hard:** Each operation transforms both the data AND the provenance in a specific way. Getting the provenance propagation rules right requires thinking about what "which source rows contributed to this output row" means after each operation. Joins are especially tricky because they combine rows from multiple tables.

#### Theory Prerequisites

| Prerequisite | Source | What you need from it | When it's ready |
|---|---|---|---|
| `__getitem__` protocol | FP Ch. 2 (sequences) | pandas uses `__getitem__` for both `df['col']` (projection) and `df[mask]` (selection). You must override it and handle both cases while propagating provenance. | KW 17 |
| pandas indexing (`loc`, `iloc`, boolean masks) | Praxisplan Phase 2 / pandas docs | You need to understand how pandas implements row/column selection before you can wrap it. | KW 19 |
| Relational algebra: selection, projection, join | DBT (if taken), or learn standalone | Selection σ = row filter. Projection π = column filter. Join ⋈ = combine tables on key. Your provenance rules map 1:1 to relational algebra semantics. | KW 21 (DBT Block A) |
| Set operations | Python basics | Provenance propagation uses set union (joins) and subset (selections). | ✓ |

#### Provenance Propagation Rules (the core logic)

| Operation | Data effect | Provenance effect |
|-----------|------------|-------------------|
| **Projection** `df[['col1', 'col2']]` | Keep selected columns | **Provenance unchanged** — you still have the same rows, just fewer columns |
| **Selection** `df[df['age'] > 30]` | Keep rows matching condition | **Filter provenance rows** — keep only the provenance entries for rows that survived the filter |
| **Merge/Join** `df1.merge(df2, on='key')` | Combine rows from two tables | **Combine provenance** — each output row's provenance references rows from BOTH source tables. If row 2 of `df1` joins with row 5 of `df2`, output provenance = {df1: 2, df2: 5} |
| **Concatenation** `pd.concat([df1, df2])` | Stack rows | **Stack provenance** — rows from df1 keep their provenance, rows from df2 keep theirs |
| **GroupBy + Agg** `df.groupby('key').mean()` | Aggregate rows | **Union provenance** — each group's output row's provenance = union of all source rows in that group |

#### Step-by-Step

| Step | What to do | Time | Theory link |
|------|-----------|------|-------------|
| 2.1.1 | **Implement projection.** Override `__getitem__` for column selection (`df[['col1', 'col2']]` and `df['col']`). Data: delegate to `pd.DataFrame.__getitem__`. Provenance: copy unchanged. Return a new `ProvDataFrame` with the same provenance. | 2h | FP Ch. 2: `__getitem__` can receive a string, list, or slice. You need to dispatch correctly. This is the same pattern pandas itself uses. |
| 2.1.2 | **Implement selection (row filtering).** Override `__getitem__` for boolean mask filtering (`df[df['age'] > 30]`). Data: delegate to pandas. Provenance: filter to keep only the rows that survived. Handle index resets carefully — provenance indices must stay aligned with data indices. | 2.5h | This is relational algebra's σ (selection). If you're taking DBT, you're studying the formal version of exactly what you're implementing. |
| 2.1.3 | **Test projection + selection.** Write comprehensive tests: project single column, multiple columns; select with simple and compound conditions; chain project then select; chain select then project. Verify provenance is correct in each case. | 1.5h | — |
| 2.2.1 | **Understand pandas merge internals.** Before implementing, study how `pd.merge` works: inner/left/right/outer join, the `on` parameter, what happens to indices. Use a small example (3 rows × 3 rows) and manually compute the provenance for each join type. | 1h | If taking DBT: this is ⋈ (natural join). The provenance propagation for joins is exactly the "lineage" concept from database provenance theory (Buneman et al.). |
| 2.2.2 | **Implement merge/join with provenance.** Override `merge` (or create a provenance-aware wrapper). For each output row of the join, compute which source rows from *both* input tables contributed. This means your provenance DataFrame now has columns for *all* source tables encountered so far. | 3h | This is the hardest data operation. Same conceptual operation as Stratum's IR join nodes (see Chat 6, JK.3.2). |
| 2.2.3 | **Implement concat with provenance.** Wrap `pd.concat`. Stack provenance DataFrames. Handle the case where the two inputs have different source tables in their provenance (fill with NaN/None for missing sources). | 1h | — |
| 2.2.4 | **Pass all data operation tests.** Run your tests + any provided test files that cover data operations. Debug edge cases: empty DataFrames, duplicate indices, multi-key joins. | 2h | — |

**⟷ Cross-wire to DBT (Chat 5):** If you're taking DBT, the relational algebra you study in Block A (σ, π, ⋈, ∪) maps directly to the provenance propagation rules above. Selection σ filters provenance. Projection π leaves provenance unchanged. Join ⋈ combines provenance from two tables. This is one of the few real synergies between DBT and the rest of your semester — provenance tracking is essentially "which tuples from which base relations contributed to this derived tuple," which is a database theory concept.

**⟷ Cross-wire to AMLS L10 (Chat 2, Block F):** The data operations you're instrumenting (filter, join, transform) are exactly the "data preparation" step in the ML lifecycle that AMLS L10 covers. When you study L10 in KW 26, you'll already have built the instrumentation layer for these operations. L10 asks "how should the system handle data cleaning?"; you'll know the answer because you built it.

---

### PHASE 3: ML Pipeline Integration (KW 23–24, ~15 hours) — ⚠️ superseded by the KW 24 sklearn sprint at the top (kept for background reading; note: wrapper strategy + train_test_split assumptions are stale)

**What you're building:** Provenance-aware wrappers for NumPy and scikit-learn. After this phase, a user can run a complete ML pipeline (`read_csv` → `train_test_split` → `fit` → `predict` → `score`) using `mlprov` as a drop-in for pandas/sklearn, and `MLProvManager` will know which source rows were used for training, testing, and prediction.

**Why this is the technical crux:** sklearn's API contract (`BaseEstimator`, `fit`/`predict`/`score`) is well-defined but has hidden complexity. You need to intercept each method, record which data was passed, track provenance through the pipeline, and store everything in `MLProvManager` — all without breaking the sklearn contract (downstream code should not notice the wrapper).

#### Theory Prerequisites

| Prerequisite | Source | What you need from it | When it's ready |
|---|---|---|---|
| sklearn API: `fit`, `predict`, `score`, `Pipeline`, `train_test_split` | Praxisplan Phase 2 (KW 19) + AML exercises | You must deeply understand the estimator contract before you can wrap it. `fit(X, y)` trains. `predict(X)` infers. `score(X, y)` evaluates. Pipelines chain estimators. | ✓ KW 19 |
| Logistic regression concept | Chat 1, Block I (AML L05) | Your test pipelines will likely use logistic regression. Understanding what `fit` does (find weights via optimization) helps you understand what provenance *means* for training. | KW 20–21 |
| Train/test split | Chat 1, Block D (AML L02, SaD 11) | `train_test_split` is the operation that creates the train/test boundary — the exact boundary your DataLeakage analysis will check in Phase 4. | ✓ KW 17 |
| Decorators and closures | FP Ch. 9 | Your sklearn wrappers may use decorators to intercept `fit`/`predict` calls. Understanding closures is essential for wrapping methods cleanly. | KW 20 |
| Protocols and ABCs | FP Ch. 13 | sklearn's `BaseEstimator` is an ABC-like pattern. Your wrappers need to honor the same interface. | KW 21 |

#### Step-by-Step

| Step | What to do | Time | Theory link |
|------|-----------|------|-------------|
| 3.1.1 | **Implement NumPy wrappers.** Wrap NumPy operations that appear in typical ML pipelines (array creation from DataFrames, matrix operations, indexing). The key challenge: when a ProvDataFrame is converted to a NumPy array (via `.values` or `np.array(df)`), the provenance must transfer. | 2h | NumPy internals from Praxisplan KW 22 (broadcasting, vectorization). The `__array__` protocol controls how objects convert to NumPy arrays. |
| 3.1.2 | **Design sklearn wrapper strategy.** Decide your approach: (a) subclass each sklearn estimator (e.g., `ProvLogisticRegression(LogisticRegression)`), or (b) write a generic wrapper class that wraps any estimator, or (c) monkey-patch sklearn estimators at import time. Read the test files to see which approach they expect. | 1h | FP Ch. 14 (inheritance vs. composition). Stratum uses approach (c) — see Chat 6, JK.3.4 for the adapter pattern. The mlprov tests likely expect approach (a) or (b). |
| 3.2.1 | **Implement `fit` wrapper.** Wrap `fit(X, y)` to: (a) call the original `fit`, (b) record in `MLProvManager` which data (with provenance) was used for training. The provenance of X tells you which source rows went into training. | 2.5h | Chat 1 Block I: `fit` for logistic regression finds weights β by minimizing a loss function. Your wrapper doesn't change this — it just records which data was used. |
| 3.2.2 | **Implement `predict` wrapper.** Wrap `predict(X)` to: (a) call the original `predict`, (b) record which data (with provenance) was used for inference. | 1.5h | — |
| 3.2.3 | **Implement `score` wrapper.** Wrap `score(X, y)` to: (a) call the original `score`, (b) record which test data (with provenance) was used for evaluation. This is critical for Phase 4: DataLeakage needs to compare training provenance vs. testing provenance. | 1.5h | Chat 1 Block D: the score is computed on test data. The entire point of train/test split is that they don't overlap — DataLeakage checks this via provenance. |
| 3.2.4 | **Implement `train_test_split` wrapper.** Wrap sklearn's `train_test_split` to: (a) perform the split, (b) correctly split provenance along with data. If rows 0,2,4 go to train and 1,3 go to test, their provenance must follow. | 2h | This is the operation that creates the train/test boundary. Getting provenance right here is essential for DataLeakage detection. |
| 3.2.5 | **Wire up MLProvManager.** Ensure that after a full pipeline run (`read_csv` → `train_test_split` → `fit` → `predict` → `score`), `MLProvManager` can answer: "What were the training data?" and "What were the test data?" with full provenance (back to source CSVs). | 2h | — |
| 3.2.6 | **Pass `test_sklearn.py`.** Run tests. Debug. Pay special attention to provenance alignment after train_test_split — index handling is the #1 source of bugs here. | 2.5h | — |

**⟷ Cross-wire to AMLS Project (Chat 3):** In the AMLS project, you're *using* `fit`/`predict`/`score` to build a classifier. In mlprov, you're *wrapping* `fit`/`predict`/`score` to track provenance. The AMLS project teaches you the user's perspective; mlprov teaches you the system's perspective. This dual understanding is exactly what an ML systems engineer needs.

**⟷ Cross-wire to Job (Chat 6, JK.3.4):** Stratum's adapters (`RustyStringEncoder`, `RustyOneHotEncoder`) are structurally identical to your mlprov wrappers — same sklearn interface interception, different purpose (Rust acceleration vs. provenance tracking). See Chat 6 Phase 3 for details.

---

### PHASE 4: Provenance Applications (KW 24–26, ~15 hours)

**What you're building:** Three concrete analyses that demonstrate the value of provenance tracking: DataLeakage detection, GDPR compliance queries, and GroupFairness assessment.

**Why this is where points are earned:** Phases 1–3 build the infrastructure; Phase 4 builds the applications that make the infrastructure useful. These analyses are also directly relevant to AMLS L12 (fairness, explainability) and to real-world ML governance — the "Data Governance" in your project title.

#### Theory Prerequisites

| Prerequisite | Source | What you need from it | When it's ready |
|---|---|---|---|
| Train/test data leakage concept | Chat 1, Block D (AML L02, SaD 11) | Data leakage = test data appearing in training data. Your provenance makes this checkable: if provenance(train) ∩ provenance(test) ≠ ∅, you have leakage. | ✓ KW 17 |
| GDPR "right to be forgotten" | Chat 2, Block G (AMLS L12) + general knowledge | GDPR requires knowing which models were trained on a specific individual's data. Provenance answers this directly: trace from a source row to all models that used it. | KW 28 (late! — but the concept is intuitive) |
| Fairness metrics (statistical parity, equalized odds) | Chat 2, Block G (AMLS L12 slides) | GroupFairness checks whether model performance differs across demographic groups. Provenance is needed because sensitive attributes (race, gender) are typically *removed* from the pipeline — provenance lets you recover them by joining back to the source. | KW 28 (late! — implement from test specs first) |
| Precision, recall, FPR | Chat 1, Block A (SaD 01) | Fairness metrics often compare precision/recall across groups. You need to know what these metrics mean. | ✓ KW 17 |

#### Step-by-Step

| Step | What to do | Time | Theory link |
|------|-----------|------|-------------|
| 4.1.1 | **Implement DataLeakage detection.** Logic: (a) get training data provenance from `MLProvManager`, (b) get test data provenance, (c) compute set intersection of source row indices, (d) if intersection is non-empty, report which rows leaked. | 3h | Chat 1 Block D: leakage is the cardinal sin of ML evaluation. Your provenance makes it detectable automatically — without provenance, you'd have to manually audit the pipeline. |
| 4.1.2 | **Test DataLeakage.** Write tests: (a) clean pipeline with no leakage → detection reports clean, (b) deliberately introduce leakage (same rows in train and test) → detection catches it, (c) subtle leakage via joins (row appears in training through a join with a table that's also used in testing). | 2h | — |
| 4.2.1 | **Implement GDPRCompliance.** Logic: given a source row index (e.g., "customer #42"), trace through all provenance to find: which training sets included this row, which models were trained on those sets. This is the "right to explanation" and "right to erasure" use case. | 2.5h | AMLS L12 discusses GDPR and EU AI Act. The provenance approach is: instead of re-running pipelines to check if a row was used, query the provenance graph directly. This is orders of magnitude faster. |
| 4.2.2 | **Test GDPRCompliance.** Write tests: (a) a row that IS in training data → report which models, (b) a row that is NOT in training data → report clean, (c) a row that enters training indirectly through a join → still detected. | 1.5h | — |
| 4.3.1 | **Implement GroupFairness.** Logic: (a) use provenance to join test predictions back to source data that contains sensitive attributes (e.g., gender, age group), (b) compute per-group metrics (accuracy, FPR, recall), (c) report disparities. The key insight: sensitive attributes were *removed* from the ML pipeline (as is common practice), but provenance lets you recover them for analysis. | 3h | AMLS L12: SliceLine finds problematic data subgroups. Your GroupFairness analysis does the same thing, but using provenance to recover the group labels that were deliberately removed from the pipeline. |
| 4.3.2 | **Test GroupFairness.** Write tests with a pipeline where gender is dropped before training, but GroupFairness can still compute per-gender metrics by joining back through provenance. | 1.5h | — |
| 4.3.3 | **Pass `test_prov_manager.py` (extended).** Run all provenance analysis tests. Debug edge cases: empty provenance, multi-hop provenance chains, models trained on joined data. | 1.5h | — |

**⟷ Cross-wire to AMLS L12 (Chat 2, Block G):** This phase is the provenance-based counterpart of what AMLS L12 teaches. L12 covers model debugging (SliceLine: find problematic data slices), fairness (statistical parity, equalized odds), and explainability (LIME, SHAP). Your GroupFairness analysis is SliceLine-from-provenance: instead of searching for bad slices, you define the slices via sensitive attributes recovered through provenance. When you study L12 in KW 28, you'll already have implemented the provenance approach — the lecture gives you the theoretical framework and alternative methods.

**⟷ Cross-wire to AMLS Project Task 1.4 (Chat 3):** The AMLS project's explainability task asks "does the model attend to the right features?" Your GroupFairness analysis asks "does the model perform equally across demographic groups?" Different questions, same critical mindset: don't trust the model blindly, interrogate its behavior. The AMLS project uses saliency maps (model-level explanation); mlprov uses provenance (data-level explanation). Together they cover both sides of ML debugging.

---

### PHASE 5: DuckDB Performance Optimization (KW 26–28, ~12 hours)

**What you're building:** Replace the slowest pandas operations (joins, selections, aggregations) with SQL queries executed by DuckDB. The goal is to reduce mlprov's overhead so provenance tracking is nearly free.

**Why DuckDB:** DuckDB is an embedded analytical database (like SQLite, but column-oriented and optimized for analytics). It can operate directly on pandas DataFrames with zero-copy via Apache Arrow. For join-heavy workloads, DuckDB is often 10–100× faster than pandas. Since provenance tracking involves many index lookups and joins, DuckDB is a natural fit.

#### Theory Prerequisites

| Prerequisite | Source | What you need from it | When it's ready |
|---|---|---|---|
| SQL basics (SELECT, JOIN, WHERE, GROUP BY) | DBT (if taken), or self-study | DuckDB uses standard SQL. Your provenance joins become SQL JOINs. | KW 21 (DBT Block A) or learn ad-hoc |
| Operator selection / cost-based optimization | Chat 2, Block B (AMLS L03) | Choosing between pandas and DuckDB for each operation is a form of operator selection — pick the backend with lower cost. | KW 19 |
| Caching, indexing | Chat 2, Block E (AMLS L09) | DuckDB uses columnar storage, indexes, and compression. Understanding why it's faster than pandas requires knowing these concepts. | KW 25 |
| Benchmarking methodology | Chat 6, JK.4 (Benchmarking) | You need to measure the speedup properly: warm-up runs, multiple iterations, varying input sizes. | KW 20+ |

#### Step-by-Step

| Step | What to do | Time | Theory link |
|------|-----------|------|-------------|
| 5.1.1 | **Profile current performance.** Run your full pipeline tests with profiling (`cProfile` or `line_profiler`). Identify the 3 hottest operations. Hypothesis: `merge`/`join` with provenance propagation is the bottleneck. | 2h | Chat 6, JK.1D (profiling tools) + JK.4 (benchmarking). Use `py-spy` for flame graphs if you've set it up. |
| 5.1.2 | **Set up DuckDB.** `pip install duckdb`. Learn the basic API: `duckdb.sql("SELECT * FROM df")` where `df` is a pandas DataFrame — DuckDB can query pandas DataFrames directly. Test with a simple join. | 1h | — |
| 5.2.1 | **Replace join provenance computation with DuckDB.** The provenance propagation for joins (computing which source rows from both tables contribute to each output row) is a join-heavy operation itself. Translate it to SQL: `SELECT a.row_idx AS left_prov, b.row_idx AS right_prov FROM left_prov a JOIN right_prov b ON a.join_key = b.join_key`. | 3h | Chat 2 Block B (AMLS L03): the compiler chooses between local vs. distributed join algorithms. You're choosing between pandas join vs. DuckDB join — same decision at a smaller scale. |
| 5.2.2 | **Replace selection provenance with DuckDB.** For row filtering, translate the boolean mask operation to a SQL WHERE clause. This may or may not be faster — profile to check. | 2h | — |
| 5.3.1 | **Run benchmarks.** Compare: (a) vanilla pandas/sklearn (no provenance), (b) mlprov with pandas backend, (c) mlprov with DuckDB backend. Vary input sizes (1k, 10k, 100k rows). Report: overhead of provenance tracking, speedup from DuckDB. Use `pytest-benchmark` or `hyperfine`. | 2.5h | Chat 6, JK.4.5 (benchmarking checklist): warm-up, multiple iterations, median + stddev, varying input sizes. |
| 5.3.2 | **Document performance results.** Create a performance report: tables + plots showing overhead and speedup. This is a grading criterion. | 1.5h | — |

**⟷ Cross-wire to Job (Chat 6, JK.3.3):** Stratum's core thesis is "replace slow Plans/Programming/python/Python/pandas operations with optimized backends." Your DuckDB optimization is the same idea at a simpler scale — finding operator-level bottlenecks and replacing them with faster implementations. See Chat 6 Phase 3 for how Stratum's optimizer automates what you do manually here.

**⟷ Cross-wire to AMLS L03 (Chat 2, Block B):** AMLS L03 covers operator selection — the compiler choosing the fastest implementation for each operation (local vs. distributed, dense vs. sparse). Your pandas-vs-DuckDB decision is a manual version of this: you profile, find the slow operation, and select a faster backend. L03 automates this; you do it by hand. Understanding both perspectives makes you a stronger systems thinker.

---

### PHASE 6: Polish and Submit (KW 28–29, ~8 hours)

#### Step-by-Step

| Step | What to do | Time |
|------|-----------|------|
| 6.1 | **Code cleanup.** Remove dead code, add docstrings to all public methods, add type hints (at minimum for function signatures). Follow PEP 8. | 2h |
| 6.2 | **Final test run.** Run the complete test suite. Fix any failing tests. Add edge-case tests you discovered during development. Aim for high coverage of the core provenance logic. | 2h |
| 6.3 | **Write documentation.** README update: how to install, how to use, what operators are supported, what provenance applications are available. Architecture overview: a diagram showing the module structure and data flow. | 2h |
| 6.4 | **Prepare presentation.** Structure: (a) problem statement (why provenance?), (b) architecture, (c) demo of provenance applications, (d) performance results. Keep slides minimal — the demo is the centerpiece. | 1.5h |
| 6.5 | **Submit.** Final git push. Verify the repo is clean. Submit before July 15 — not on July 15. | 0.5h |

---

## The 6 Theory → Practice Moments (When Theory Clicks)

1. **Python data model → ProvDataFrame (Phase 1, KW 19):** FP Ch. 1's `__getitem__`, `__repr__`, `__len__` are exactly what you implement to make ProvDataFrame behave like a real DataFrame. The theory is alive.

2. **Inheritance → Wrapping pandas/sklearn (Phase 1+3, KW 19–24):** FP Ch. 14's discussion of when to subclass vs. compose is the design decision you face: should ProvDataFrame *be* a DataFrame (inheritance) or *have* a DataFrame (composition)? The answer shapes your entire architecture.

3. **Train/test split → DataLeakage detection (Phase 4, KW 24):** AML L02's bias-variance discussion explains *why* train/test separation matters. Your DataLeakage detection enforces it automatically via provenance. The theory says "don't let test data leak into training"; your code checks this for any pipeline.

4. **Relational algebra → Provenance propagation (Phase 2, KW 21–22):** If you're taking DBT, the σ/π/⋈ operations you study formally are the exact operations you instrument for provenance. The join provenance rule (output row references rows from both input tables) is the relational algebra definition of join lineage.

5. **AMLS L12 fairness → GroupFairness analysis (Phase 4, KW 25–26):** AMLS L12 teaches fairness metrics and SliceLine (finding problematic data subgroups). Your GroupFairness analysis is the provenance-based approach: recover sensitive attributes that were removed from the pipeline and compute per-group metrics. Same goal, different technique.

6. **AMLS L03 operator selection → DuckDB optimization (Phase 5, KW 26–28):** AMLS L03 teaches how ML systems choose between operator implementations. You do this manually: profile pandas operations, find the slow ones, replace them with DuckDB. The theory automates what you do by hand — understanding both makes the concept concrete.

---

## Risk Assessment and Buffers

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Subclassing pd.DataFrame is tricky** | High | High (blocks everything) | Read pandas docs on "Subclassing pandas Data Structures" carefully. Use `_metadata` class attribute to propagate custom attributes. Test early with a minimal subclass. |
| **Provenance alignment breaks after operations** | High | High | Use small examples (3–5 rows) and manually verify provenance after each operation. Write tests before implementation (TDD). Index management is the #1 bug source. |
| **sklearn wrapper doesn't honor estimator contract** | Medium | High (blocks Phase 4) | Study `sklearn.utils.estimator_checks` — sklearn has a test suite for estimator compliance. Run it against your wrappers. |
| **AMLS project eats all your time** | Medium | High | Both projects have the same deadline (Jul 15). The AMLS project is worth exam bonus points; PPDS is a course grade. Coordinate weekly: if one project falls behind, adjust the other. |
| **DuckDB integration adds complexity without enough speedup** | Medium | Low | Phase 5 is an optimization — it makes the grade better but isn't required for correctness. If time is tight, skip DuckDB and focus on test coverage + documentation. |
| **Team coordination overhead (if PPDS is a team project)** | Medium | Medium | Define clear interfaces between team members. Agree on the provenance representation early (Phase 1) so everyone builds on the same foundation. |

**Buffer strategy:** KW 28 is the buffer week. If Phases 1–4 are done by KW 26, you have two full weeks for DuckDB + polish. If Phase 3 slips to KW 25, compress Phase 5 to a lightweight profiling exercise and focus on correctness + documentation.

---

## What This Chat Does NOT Cover (Handled Elsewhere)

| Topic | Where it lives | Why not here |
|-------|---------------|-------------|
| Python basics, venv, git, Docker, pytest | **Bootcamp Chat** (Plans/Programming/python/Programming-Toolbox-Bootcamp.md) | Already covered. This plan assumes those skills. |
| AML/SaD theory (bias-variance, classification, NNs) | **Chat 1** (Plans/ML/foundations/Chat1_Foundations_AML_SaD_Plan.md) | This plan references Chat 1 blocks as prerequisites. |
| AMLS systems theory (compilation, parallelism, lifecycle) | **Chat 2** (Plans/ML/systems/Chat2_AMLS_Theory_Plan.md) | This plan references Chat 2 blocks for cross-wires. |
| AMLS Project (AI Image Detection) | **Chat 3** (Plans/ML/systems/Chat3_AMLS_Project_Plan.md) | Separate project, same deadline. Coordinate time. |
| Stratum/skrub deep dive, polars, benchmarking, C++, Rust | **Chat 6** (Plans/crosscutting/job/Chat6_Job_Onboarding_Plan.md) | Dedicated job onboarding. This plan notes synergies via JK step IDs. |
| DBT theory (relational algebra, normalization) | **Chat 5** (if opened) | Noted as cross-wire for Phase 2 joins. |

---

## Weekly Checklist Template

Use this at the end of each week to track progress:

```
### KW __ Check-in
- [ ] Phase/step(s) completed this week: ___
- [ ] Tests passing: ___ / ___ (list which test files)
- [ ] Provenance verified on small example: yes/no
- [ ] AMLS project coordination: any time conflicts?
- [ ] Hours spent this week: ___
- [ ] Blockers for next week: ___
- [ ] Theory I used this week: ___
- [ ] Chat 6 (Job) synergy noted: ___
```

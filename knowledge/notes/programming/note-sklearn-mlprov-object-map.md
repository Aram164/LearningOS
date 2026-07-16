---
id: note-sklearn-mlprov-object-map
type: note
title: "Sklearn → mlprov Object Map — every object you must touch, one page each"
created: "2026-07-11"
role: reference
state: evolving
authorship: mixed
concepts: [concept-scikit-learn, concept-data-provenance]
sources: []
---

> **Migration note (2026-07-17, Stage 2):** body preserved verbatim from
> `Plans/Libraries/sklearn/Sklearn-mlprov-Object-Map.md` (legacy tree).

# Sklearn → mlprov Object Map — every object you must touch, one page each

> **Created:** 2026-06-12 (KW 24), after Hour 1 of the crash plan. Companion to `Plans/Libraries/sklearn/Sklearn-5h-Crash-Plan.md`.
> **Scope:** the EXACT objects in the mlprov test surface. Nothing else exists for this project.

## The two rules (memorize these, everything below is an instance)

1. **Row-preserving transform rule:** every tested transformer keeps row i as row i. So: `output.provenance = input.provenance`. Always. No exceptions in this test suite.
2. **Bookkeeping rule:** classifiers don't transform — they *remember*. `fit`/`predict`/`score` call the original sklearn method, then record (in `MLProvManager`) which prov-objects were involved.

That's the entire conceptual content of "sklearn integration." Eight objects, two rules.

## ⚠️ Ordering correction: ColumnTransformer is NOT first

CT *contains* the leaf transformers — in `test_column_transformer.py` its `transformers=[...]` list holds **mlprov's** `SimpleImputer` and `OneHotEncoder`, so CT's `fit_transform` will crash on their `NotImplementedError` until the leaves work. Implementation order is forced: **leaves (M.3.3) → CT (M.3.4) → classifier (M.3.5)**. CT only *looks* first because it's the outermost object in the example pipelines.

---

## Tier A — Leaf transformers (sprint M.3.3) — rule 1 only

### 1. `SimpleImputer` — fills missing values
[API doc](https://scikit-learn.org/stable/modules/generated/sklearn.impute.SimpleImputer.html) · [guide](https://scikit-learn.org/stable/modules/impute.html) · skeleton: `mlprov/sklearn/impute/_simple_imputer.py` · test: `test/test_sklearn/impute/`

```python
import numpy as np
from sklearn.impute import SimpleImputer
imp = SimpleImputer(missing_values=np.nan, strategy='mean')
imp.fit([[7,2,3],[4,np.nan,6],[10,5,9]])     # learns column means → imp.statistics_
imp.transform([[np.nan,2,3],[4,np.nan,6],[10,np.nan,9]])  # fills with FITTED stats
```
**Shape:** (3,3) in → (3,3) out. **Provenance:** = input's. **Implement:** `transform`, `fit_transform` (2 methods, same 2-line pattern).

### 2. `StandardScaler` — z-scores columns
[API doc](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html) · skeleton: `preprocessing/simple.py` · test: `test_standard_scaler`

```python
from sklearn.preprocessing import StandardScaler
sc = StandardScaler()
sc.fit_transform([[1.],[2.],[10.],[5.]])     # learns mean_/scale_, transforms
sc.transform([[1.],[2.],[3.],[5.]])          # TRAIN stats applied to TEST rows
```
**Gotcha:** its test feeds a *mlprov DataFrame*, not an ndarray — read `.provenance` off whatever comes in. **Implement:** `transform(X, copy=None)`, `fit_transform`.

### 3. `OneHotEncoder` — categories → indicator columns
[API doc](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html) · [guide §encoding](https://scikit-learn.org/stable/modules/preprocessing.html#encoding-categorical-features) · test: `test_one_hot_encoder`

```python
from sklearn.preprocessing import OneHotEncoder
enc = OneHotEncoder(handle_unknown='ignore')
enc.fit([['Male',1],['Female',3],['Female',2]])
enc.categories_                  # [['Female','Male'], [1,2,3]] → 2+3 = 5 output cols
out = enc.transform([['Female',1],['Male',4]])
out                              # ← SPARSE matrix! unseen '4' → all-zero block
out.toarray()                    # densify BEFORE wrapping as prov-ndarray
```
**Columns explode, rows don't** → provenance unchanged. **Implement:** `transform` (+ `.toarray()` densify), `fit_transform`.

### 4. `label_binarize(y, classes)` — labels → 0/1 column
[API doc](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.label_binarize.html) · test: `test_label_binarize`

```python
from sklearn.preprocessing import label_binarize
label_binarize(['yes','no','no','yes'], classes=['yes','no'])  # [[0],[1],[1],[0]]
```
A *function*, not a class — no fit state. Skeleton already computes `result_wo_prov`; you wrap it with `y.provenance`. One line of real work.

---

## Tier B — Containers (sprint M.3.4) — rule 1 at the boundary

### 5. `ColumnTransformer` — routes column subsets to different transformers, hstacks results
[API doc](https://scikit-learn.org/stable/modules/generated/sklearn.compose.ColumnTransformer.html) · [guide](https://scikit-learn.org/stable/modules/compose.html#columntransformer-for-heterogeneous-data) · [⭐ the mixed-types example](https://scikit-learn.org/stable/auto_examples/compose/plot_column_transformer_mixed_types.html) — read this one, it IS your test pipeline annotated

```python
# vanilla version of your compose test:
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
X = np.array([[0., np.nan, 'Male'], [1., 1., 'Female']], dtype=object)
ct = ColumnTransformer(transformers=[
    ('imputing', SimpleImputer(missing_values=np.nan, strategy='mean'), slice(0, 1)),
    ('onehot',   OneHotEncoder(handle_unknown='ignore'),               slice(2)),
])
ct.fit_transform(X).shape    # (2, k) — 2 rows in, 2 rows out. Always.
```
Each sub-transformer sees only its columns; outputs glued side-by-side. Rows never change → **wrap CT's final output with CT's input provenance.** You do NOT manage the inner transformers' provenance — sklearn shreds it internally anyway (check_array); only the boundary matters. **Implement:** `transform`, `fit_transform`.

### 6. `Pipeline` — chains steps; output of step n = input of step n+1
[guide](https://scikit-learn.org/stable/modules/compose.html#pipeline-chaining-estimators) · skeleton: `pipeline/_pipeline.py` — **already done: `pass` is the implementation.** Pipeline just calls each step's `fit_transform`/`fit`/`predict` in order; since the steps are mlprov subclasses, provenance flows step-to-step *outside* sklearn's internals. Implement nothing; understand why nothing is needed.

---

## Tier C — Classifier side (sprint M.3.5) — rule 2

### 7. `load_iris` → 8. `DecisionTreeClassifier` (+ `ScoreResult`)
[load_iris](https://scikit-learn.org/stable/modules/generated/sklearn.datasets.load_iris.html) · [DecisionTreeClassifier](https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html) · [tree guide (usage part only)](https://scikit-learn.org/stable/modules/tree.html) · tests: `test_tree/`, `test_score_result.py`, `test_prov_manager/`

```python
from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier
import numpy as np
iris = load_iris()                      # .data (150,4), .target (150,)
clf = DecisionTreeClassifier().fit(iris.data, iris.target)
preds = clf.predict([[4.3,1.6,0.3,0.5],[5.3,1.2,0.5,1.3]])
clf.score(iris.data, iris.target) == np.mean(clf.predict(iris.data) == iris.target)  # True
```
**Provenance rules (all bookkeeping):**

| Method | sklearn part | mlprov part |
|---|---|---|
| `load_iris()` | call orig | wrap `.data` → prov-ndarray (id "0"), `.target` → prov-ndarray (id "1") — creation ORDER fixes the ids |
| `fit(X, y)` | orig fit | record `(X, y)` for this classifier in `MLProvManager`; return `self` |
| `predict(X)` | orig predict | record X as test data; return prov-ndarray with `X.provenance` |
| `score(X, y)` | predict + accuracy | return `ScoreResult(acc, test_predictions=…, test_labels=y)`; record in manager |

`ScoreResult` = a `float` subclass that smuggles two prov-ndarrays along with the number. Test: `test_score_result.py` (30-min win, zero sklearn knowledge needed).

---

## Three example pipelines, smallest → real

1. **Two-liner (rule 1 felt):** `SimpleImputer().fit_transform(X)` on the 3×3 array above. One object, one provenance pass-through.
2. **Container (rule 1 at boundary):** the CT snippet above — vanilla first, then imagine where the single provenance attach happens (answer: once, at CT's return).
3. **The real thing (both rules):** `test_full_pipeline_prov.py::test_simplified_adult_complex_prov` — read it top to bottom *now* that you know every object in it: read_csv → label_binarize → CT(Pipeline(impute→onehot), scaler) → DecisionTreeClassifier → score. Every line is Tier A/B/C above. This test is the project.

## Further reading, ranked (beyond the crash plan's links)

1. [Mixed-types ColumnTransformer example](https://scikit-learn.org/stable/auto_examples/compose/plot_column_transformer_mixed_types.html) ⭐ — your test pipeline, official, annotated. 15 min.
2. [Compose guide](https://scikit-learn.org/stable/modules/compose.html) — Pipeline + CT sections only. 20 min.
3. [Glossary: estimator / transformer / predictor](https://scikit-learn.org/stable/glossary.html#term-estimator) — when a term is fuzzy, look it up here, not in blog posts. Reference, not reading.
4. Already in LEARNING-RESOURCES §8: Hettinger (done ✅), numpy/pandas subclassing guides — re-skim `__array_finalize__` right before Tier C, since `predict` returns must come out as prov-ndarrays.

# Sklearn 5-Hour Crash Plan — mlprov Edition

> **Created:** 2026-06-11 (KW 24) · **For:** absolute sklearn beginner → able to execute the Chat4 KW 24 SKLEARN SPRINT
> **Verified state at creation:** suite 7 pass / 13 fail, unchanged since Jun 10 audit.
> **Principle:** you are NOT learning sklearn-the-library. You are learning the ~15% of it that the mlprov test suite exercises. Your own test files are the textbook — every exercise below reproduces one of them in *vanilla* sklearn first, so when you then write the provenance wrapper, the only new thing is the wrapping.

**Explicitly OUT of scope (do not spend minutes here):** model selection, cross-validation, GridSearch, the algorithm zoo (SVM, ensembles, clustering), metrics beyond accuracy, feature selection, sklearn datasets beyond `load_iris`. None of it is tested.

**Setup (5 min):** `cd "Plans/ML/mlprov/PPDS ML Data Provenance/Project" && source mlprov_env/bin/activate && python` — work in the REPL or a scratch notebook. Keep two terminals: one REPL, one for `pytest`.

---

## Hour 1 — The estimator contract (the one mental model)

**Goal:** internalize: *everything in sklearn is an object with `fit`; `fit` learns state and returns `self`; `transform`/`predict` apply that state to whatever you pass next.*

**Read (~35 min):**

| Link | What to take from it |
|---|---|
| [Getting Started](https://scikit-learn.org/stable/getting_started.html) | The whole page. Sections "Fitting and predicting," "Transformers and pre-processors," "Pipelines." Ignore cross-validation + parameter search sections. |
| [Developing scikit-learn estimators](https://scikit-learn.org/stable/developers/develop.html) — skim §"Different objects" + §"Estimators" only | This is the *contract you are subclassing against*. Estimator vs Transformer vs Predictor; why `fit` returns `self`; trailing-underscore convention (`mean_`, `categories_`) = "learned in fit." 15 min, skim, don't study. |

**Do (~25 min, REPL):**

```python
from sklearn.preprocessing import StandardScaler
import numpy as np

X_train = np.array([[1.], [2.], [10.], [5.]])   # ← same data as test_standard_scaler
sc = StandardScaler()
out = sc.fit(X_train)
out is sc                # True — fit returns self. THE convention.
sc.mean_, sc.scale_      # state learned by fit, stored on the object

X_test = np.array([[1.], [2.], [3.], [5.]])
sc.transform(X_test)     # applies TRAIN statistics to TEST data
sc.fit_transform(X_train)  # fit + transform in one call
```

**Checkpoint question (answer without running):** if you call `sc.transform(X_test)`, whose mean is subtracted — train's or test's? *(Train's. That asymmetry is the whole reason `fit`/`transform` are separate methods — and it's exactly why, in mlprov, `transform`'s output carries the provenance of its INPUT argument, not of the fitted data. Compare: `test_standard_scaler` expects fit_transform(train)→`{"0": …}` but transform(test)→`{"1": …}`.)*

---

## Hour 2 — Your four transformers, test data as textbook

**Goal:** reproduce every expected output in `test/test_sklearn/impute/` and `test/test_sklearn/preprocessing/` using vanilla sklearn.

**Reference docs (open in tabs, read the top + Examples section only):**

| Class | API doc | Guide |
|---|---|---|
| `SimpleImputer` | [API](https://scikit-learn.org/stable/modules/generated/sklearn.impute.SimpleImputer.html) | [Imputation guide §](https://scikit-learn.org/stable/modules/impute.html) |
| `OneHotEncoder` | [API](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html) | [Preprocessing guide § encoding](https://scikit-learn.org/stable/modules/preprocessing.html#encoding-categorical-features) |
| `StandardScaler` | [API](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html) | [Preprocessing guide § standardization](https://scikit-learn.org/stable/modules/preprocessing.html#standardization-or-mean-removal-and-variance-scaling) |
| `label_binarize` | [API](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.label_binarize.html) | — |

**Do (~45 min):** copy each test's input into the REPL with plain numpy and match the asserted outputs.

```python
import numpy as np
from sklearn.impute import SimpleImputer

# from test_simple_imputer.py:
X = np.array([[7, 2, 3], [4, np.nan, 6], [10, 5, 9]])
y = np.array([[np.nan, 2, 3], [4, np.nan, 6], [10, np.nan, 9]])
imp = SimpleImputer(missing_values=np.nan, strategy='mean')
imp.fit(X)
imp.statistics_          # column means of X — learned state
imp.transform(y)         # y's NaNs filled with X's stats → matches the test's expected array
```

```python
from sklearn.preprocessing import OneHotEncoder
# from test_simple.py:
X = np.array([['Male', 1], ['Female', 3], ['Female', 2]], dtype=object)
enc = OneHotEncoder(handle_unknown='ignore')
enc.fit(X)
enc.categories_          # [['Female','Male'], [1,2,3]] → explains the 5 output columns
out = enc.transform([['Female', 1], ['Male', 4]])
type(out)                # ← sparse matrix, NOT ndarray!
out.toarray()            # matches the test; note the all-zero block for unseen '4' (handle_unknown='ignore')
```

**The three things to actually understand here:**
1. Why `transform(y)` output equals *y's shape* with *X's statistics* → in mlprov, output provenance = `y.provenance`.
2. `OneHotEncoder` returns **sparse** by default → your wrapper must densify (`.toarray()`) before wrapping as prov-`ndarray`, or the test's `allclose` fails.
3. `label_binarize(y, classes=['yes','no'])` is a *function*, not an estimator — its wrapper just wraps the return with the input's provenance (the skeleton already computes `result_wo_prov` for you).

---

## Hour 3 — Composition: `Pipeline` + `ColumnTransformer`

**Goal:** understand how data flows through nested compositions — this is `test_full_pipeline_prov.py`'s structure.

**Read (~20 min):**

| Link | What to take |
|---|---|
| [Pipelines & composite estimators guide](https://scikit-learn.org/stable/modules/compose.html) | §Pipeline (chaining: each step's output is the next step's input; `fit_transform` cascades) and §ColumnTransformer (different transformers to different column subsets, outputs h-stacked). Skip caching/FeatureUnion. |
| [Example: ColumnTransformer with mixed types](https://scikit-learn.org/stable/auto_examples/compose/plot_column_transformer_mixed_types.html) ⭐ | This official example is *almost line-for-line* the adult_complex pipeline in your tests (impute+onehot on categoricals, scale on numerics, classifier on top). Read it as "my test suite, annotated." |

**Do (~40 min, vanilla sklearn on your real data):**

```python
import os, pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

train = pd.read_csv("example_pipelines/adult_complex/adult_train.csv", na_values='?', index_col=0)

cat = Pipeline([('impute', SimpleImputer(strategy='most_frequent')),
                ('encode', OneHotEncoder(handle_unknown='ignore'))])
ct = ColumnTransformer([('categorical', cat, ['education', 'workclass']),
                        ('numeric', StandardScaler(), ['age', 'hours-per-week'])])
out = ct.fit_transform(train)
out.shape                # rows preserved (22792, ...) ← THE provenance-relevant fact
```

**The subclass-stripping experiment (10 min — the most important 10 minutes of the day):**

```python
from mlprov.numpy import ndarray as prov_ndarray
X = prov_ndarray([[1.], [2.], [10.], [5.]])
X.provenance             # there it is
from sklearn.preprocessing import StandardScaler
res = StandardScaler().fit_transform(X)
type(res)                # plain numpy.ndarray — provenance GONE
```

sklearn's internal `check_array` validation converts everything to plain numpy. **This is why every mlprov wrapper follows one pattern: call the original method, then re-attach the input's provenance to the result.** Once you've watched it vanish, the entire sprint design is obvious.

---

## Hour 4 — The classifier side: fit / predict / score

**Goal:** everything `_decision_tree_classifier.py` and `ScoreResult` need.

**Read (~15 min):** [Decision Trees guide](https://scikit-learn.org/stable/modules/tree.html) — intro + classification section only (you need *usage*, not split-criterion theory; that's Block K's job later). [`DecisionTreeClassifier` API](https://scikit-learn.org/stable/modules/generated/sklearn.tree.DecisionTreeClassifier.html) — just `fit`/`predict`/`score` signatures.

**Do (~45 min):**

```python
from sklearn.datasets import load_iris
from sklearn.tree import DecisionTreeClassifier
import numpy as np

iris = load_iris()
X, y = iris.data, iris.target          # (150,4), (150,) — your wrapper gives these ids "0" and "1"
clf = DecisionTreeClassifier()
clf.fit(X, y)                           # returns self
preds = clf.predict([[4.3, 1.6, 0.3, 0.5], [5.3, 1.2, 0.5, 1.3]])  # test's exact rows
acc_manual = np.mean(clf.predict(X) == y)
clf.score(X, y) == acc_manual           # True — score IS accuracy for classifiers
```

Then study the explicit-parent-call pattern the skeleton uses (no `super()` in the hot path — deliberate, avoids MRO surprises with the mixin):

```python
result_wo_prov = orig_tree.DecisionTreeClassifier.predict(self, X)   # ← calling the PARENT's method on self
```

**Wrap-up reading (10 min):** re-read `test_get_provenance.py` top to bottom. You now know every sklearn call in it. What's left is pure bookkeeping: `fit` records (X, y) in `MLProvManager`, `predict` records X as test data, `score` returns a `ScoreResult` float-subclass carrying prov-ndarrays. No sklearn knowledge needed — just dicts keyed by `id(obj)`.

---

## Hour 5 — Cash it in: first green sklearn test (sprint M.3.3, imputer slice)

**Goal:** `pytest test/test_sklearn/impute -x` → green. Independent of the M.3.0 pandas fix (the imputer test uses only ndarrays).

1. Open `mlprov/sklearn/impute/_simple_imputer.py`. Implement:
   - `transform(self, X)`: `result = orig_impute.SimpleImputer.transform(self, X)` → `return ndarray(result, provenance=X.provenance)`
   - `fit_transform(self, X, y=None)`: same with `fit_transform`, provenance from `X`.
2. Run the test. If the provenance assert fails on a *copy vs reference* issue, pass `X.provenance` directly (the tests use `assert_frame_equal`, identity is fine).
3. Green? Commit. Then, if energy remains, `StandardScaler` + `OneHotEncoder` (remember `.toarray()`) are the same pattern — that's the rest of M.3.3.

**End-of-day definition of done:** imputer test green (8/20), the stripping experiment understood, and you can state from memory what `fit` / `transform` / `fit_transform` / `predict` / `score` each do and return.

---

## Optional video track (only if reading stalls — total ≤ 50 min, watch at 1.5×)

| Resource | Use |
|---|---|
| [Data School — Machine learning in Python with scikit-learn](https://www.youtube.com/playlist?list=PL5-da3qGB5ICeMbQuqbbCOQWcS6OYBr5A) (Kevin Markham, 11 videos) | Video 4 ("Getting started with iris") + video 5 (model training / fit-predict pattern) only. Calm, precise API walkthroughs. |
| [calmcode — scikit-learn course](https://calmcode.io/course/scikit-learn/introduction) (10 short videos) | #3 Models, #4 Scale, #5 Pipeline — ~12 min total, the fastest visual intro to estimator + pipeline mechanics. (Made on an old sklearn version; the API contract is unchanged.) |

## After the 5 hours — where this connects

- Sprint table: `Plans/ML/mlprov/Chat4_PPDS_mlprov_Plan.md` → "KW 24 SKLEARN SPRINT". You'll have pre-paid steps M.3.3–M.3.5 conceptually; M.3.0 (pandas `__getitem__`) is still the next *implementation* priority after the imputer win.
- Deeper theory for what `DecisionTreeClassifier.fit` actually computes → Block K, `Plans/ML/foundations/reference/AML-SaD_Master_Wiring.md` §2-C (later; not needed to ship mlprov).
- For the eventual Fairness step: [fairlearn MetricFrame user guide](https://fairlearn.org/main/user_guide/assessment/index.html) — bookmark, don't read yet.

"""Empirical pandas/polars aggregation contention prober."""
import inspect, json, sys
import pandas as pd
import polars as pl

print("pandas", pd.__version__, "| polars", pl.__version__)

# canonical concept -> (pandas name, polars name)
CONCEPTS = [
    # from stratum _AGG_METHODS
    ("sum",        "sum",        "sum"),
    ("mean",       "mean",       "mean"),
    ("count",      "count",      "count"),
    ("min",        "min",        "min"),
    ("max",        "max",        "max"),
    ("median",     "median",     "median"),
    ("std",        "std",        "std"),
    ("var",        "var",        "var"),
    ("first",      "first",      "first"),
    ("last",       "last",       "last"),
    ("prod",       "prod",       "product"),
    ("size",       "size",       "len"),
    ("nunique",    "nunique",    "n_unique"),
    ("sem",        "sem",        "sem"),
    # AGG_FUNCS
    ("agg",        "agg",        "agg"),
    ("aggregate",  "aggregate",  "agg"),
    # near-neighbours worth mapping
    ("any",        "any",        "any"),
    ("all",        "all",        "all"),
    ("quantile",   "quantile",   "quantile"),
    ("skew",       "skew",       "skew"),
    ("kurt",       "kurt",       "kurtosis"),
    ("idxmin",     "idxmin",     "arg_min"),
    ("idxmax",     "idxmax",     "arg_max"),
    ("mode",       "mode",       "mode"),
    ("value_counts","value_counts","value_counts"),
    ("describe",   "describe",   "describe"),
    ("len_rowcount","__none__",  "len"),
]

pdf = pd.DataFrame({"g": ["a","a","a","b"], "x": [1, None, 3, 4]})
pldf = pl.DataFrame({"g": ["a","a","a","b"], "x": [1, None, 3, 4]})

SURFACES = {
    "pd.DataFrame":       pdf,
    "pd.Series":          pdf["x"],
    "pd.DataFrameGroupBy": pdf.groupby("g"),
    "pd.SeriesGroupBy":   pdf.groupby("g")["x"],
    "pl.DataFrame":       pldf,
    "pl.Series":          pldf["x"],
    "pl.GroupBy":         pldf.group_by("g", maintain_order=True),
}

def sig(obj, name):
    try:
        return str(inspect.signature(getattr(obj, name)))
    except Exception:
        return "<no signature>"

rows = []
for canon, pdname, plname in CONCEPTS:
    row = {"concept": canon, "pd_name": pdname, "pl_name": plname}
    for sname, sobj in SURFACES.items():
        nm = pdname if sname.startswith("pd.") else plname
        if nm == "__none__":
            row[sname] = None
            continue
        has = hasattr(sobj, nm)
        row[sname] = {"present": has, "sig": sig(sobj, nm) if has else None} if has else {"present": False}
    rows.append(row)

print(json.dumps(rows, indent=1, default=str))

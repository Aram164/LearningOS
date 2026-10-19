"""Emit markdown presence tables straight from live introspection."""
import pandas as pd, polars as pl, inspect, warnings
warnings.simplefilter("ignore")

D = {"g": ["a","a","a","b"], "x": [1,None,3,4], "y":[10,20,20,40]}
pdf, pldf = pd.DataFrame(D), pl.DataFrame(D)
S = {
  "pdDF": pdf, "pdSer": pdf["x"],
  "plDF": pldf, "plSer": pldf["x"],
  "pdDFG": pdf.groupby("g"), "pdSerG": pdf.groupby("g")["x"],
  "plGB": pldf.group_by("g", maintain_order=True),
}

# (concept, pandas name, polars name)
CONCEPTS = [
 ("sum","sum","sum"), ("mean","mean","mean"), ("count","count","count"),
 ("min","min","min"), ("max","max","max"), ("median","median","median"),
 ("std","std","std"), ("var","var","var"), ("first","first","first"),
 ("last","last","last"), ("prod","prod","product"), ("size","size","len"),
 ("nunique","nunique","n_unique"), ("sem","sem","sem"),
 ("any","any","any"), ("all","all","all"), ("quantile","quantile","quantile"),
 ("skew","skew","skew"), ("kurt","kurt","kurtosis"),
 ("idxmin","idxmin","arg_min"), ("idxmax","idxmax","arg_max"),
 ("mode","mode","mode"), ("value_counts","value_counts","value_counts"),
 ("describe","describe","describe"),
 ("agg","agg","agg"), ("aggregate","aggregate","agg"),
]

def kind(obj, nm):
    """P = property/attribute, M = callable method, . = absent"""
    if not hasattr(obj, nm):
        return "."
    a = getattr(type(obj), nm, None)
    if isinstance(a, property) or not callable(getattr(obj, nm)):
        return "P"
    return "M"

def sg(obj, nm):
    try:
        return str(inspect.signature(getattr(obj, nm)))
    except Exception:
        return "-"

print("### DF / Series surface\n")
print("| concept | pandas | polars | pdDF | pdSer | plDF | plSer |")
print("|---|---|---|---|---|---|---|")
for c, p, q in CONCEPTS:
    print(f"| {c} | `{p}` | `{q}` | {kind(S['pdDF'],p)} | {kind(S['pdSer'],p)} | {kind(S['plDF'],q)} | {kind(S['plSer'],q)} |")

print("\n### GroupBy surface\n")
print("| concept | pandas | polars | pdDFG | pdSerG | plGB |")
print("|---|---|---|---|---|---|")
for c, p, q in CONCEPTS:
    print(f"| {c} | `{p}` | `{q}` | {kind(S['pdDFG'],p)} | {kind(S['pdSerG'],p)} | {kind(S['plGB'],q)} |")

print("\n### Signatures (GroupBy)\n")
for c, p, q in CONCEPTS:
    a = sg(S["pdDFG"], p) if hasattr(S["pdDFG"], p) else "ABSENT"
    b = sg(S["plGB"], q) if hasattr(S["plGB"], q) else "ABSENT"
    print(f"{c:14} pd {a}\n{'':14} pl {b}")

print("\n### polars GroupBy full method inventory")
print(sorted(m for m in dir(pl.dataframe.group_by.GroupBy) if not m.startswith("_")))
print("\n### pandas DataFrameGroupBy agg-ish inventory")
inv = [m for m in dir(S["pdDFG"]) if not m.startswith("_")]
print(sorted(inv))

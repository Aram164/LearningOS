"""Semantic-effect probes: run each present method on an identical fixture."""
import pandas as pd, polars as pl, warnings
warnings.simplefilter("ignore")

DATA = {"g": ["a", "a", "a", "b"], "x": [1, None, 3, 4], "y": [10, 20, 20, 40]}
pdf = pd.DataFrame(DATA)
pldf = pl.DataFrame(DATA)

def show(label, fn):
    try:
        r = fn()
        t = type(r).__name__
        sh = getattr(r, "shape", None)
        print(f"--- {label}\n    type={t} shape={sh}\n{r}\n")
    except Exception as e:
        print(f"--- {label}\n    RAISES {type(e).__name__}: {str(e)[:220]}\n")

print("="*70, "\nA. DF/SERIES SURFACE\n", "="*70)
for m_pd, m_pl in [("sum","sum"),("count","count"),("nunique","n_unique"),
                   ("prod","product"),("size","len"),("median","median"),
                   ("std","std"),("mean","mean"),("describe","describe")]:
    show(f"pandas DataFrame.{m_pd}()",  lambda m=m_pd: getattr(pdf, m)() if m!="size" else pdf.size)
    show(f"polars DataFrame.{m_pl}()",  lambda m=m_pl: getattr(pldf, m)() if m!="len" else len(pldf))
    show(f"pandas Series.{m_pd}()",     lambda m=m_pd: getattr(pdf['x'], m)() if m!="size" else pdf['x'].size)
    show(f"polars Series.{m_pl}()",     lambda m=m_pl: getattr(pldf['x'], m)())

print("="*70, "\nB. GROUPBY SURFACE\n", "="*70)
g_pd = pdf.groupby("g")
g_pl = pldf.group_by("g", maintain_order=True)
for m_pd, m_pl in [("sum","sum"),("count","count"),("size","len"),("nunique","n_unique"),
                   ("first","first"),("last","last"),("all","all"),("median","median"),
                   ("quantile","quantile"),("mean","mean")]:
    if m_pd == "quantile":
        show("pandas gb.quantile(0.5)", lambda: g_pd.quantile(0.5))
        show("polars gb.quantile(0.5)", lambda: g_pl.quantile(0.5))
        continue
    show(f"pandas gb.{m_pd}()", lambda m=m_pd: getattr(g_pd, m)())
    show(f"polars gb.{m_pl}()", lambda m=m_pl: getattr(g_pl, m)())

print("="*70, "\nC. NULL EDGE first/last\n", "="*70)
n_pd = pd.DataFrame({"g":["a"]*4, "x":[None,10,20,None]})
n_pl = pl.DataFrame({"g":["a"]*4, "x":[None,10,20,None]})
show("pandas gb.first()", lambda: n_pd.groupby("g").first())
show("pandas gb.last()",  lambda: n_pd.groupby("g").last())
show("polars gb.first()", lambda: n_pl.group_by("g", maintain_order=True).first())
show("polars gb.last()",  lambda: n_pl.group_by("g", maintain_order=True).last())
show("polars gb.first(ignore_nulls=True)", lambda: n_pl.group_by("g", maintain_order=True).first(ignore_nulls=True))

print("="*70, "\nD. AGG SPEC GRAMMAR\n", "="*70)
show("pandas gb.agg('sum')",        lambda: g_pd.agg("sum"))
show("polars gb.agg('sum')",        lambda: g_pl.agg("sum"))
show("pandas gb.agg(['sum','mean'])", lambda: g_pd.agg(["sum","mean"]))
show("polars gb.agg(['sum','mean'])", lambda: g_pl.agg(["sum","mean"]))
show("pandas gb.agg({'x':'sum'})",  lambda: g_pd.agg({"x":"sum"}))
show("polars gb.agg({'x':'sum'})",  lambda: g_pl.agg({"x":"sum"}))
show("pandas gb.agg(lambda s: s.max()-s.min())", lambda: g_pd.agg(lambda s: s.max()-s.min()))
show("polars gb.agg(lambda ...)",   lambda: g_pl.agg(lambda s: s.max()-s.min()))
show("pandas gb.agg(x_sum=('x','sum'))", lambda: g_pd.agg(x_sum=("x","sum")))
show("polars gb.agg(x_sum=pl.col('x').sum())", lambda: g_pl.agg(x_sum=pl.col("x").sum()))
show("pandas df.agg('sum')",  lambda: pdf.agg("sum"))
show("pandas s.agg('sum')",   lambda: pdf['x'].agg("sum"))
show("pandas s.agg(['sum','mean'])", lambda: pdf['x'].agg(["sum","mean"]))
show("polars df.agg exists?", lambda: pldf.agg)
show("pandas df.agg('sum', axis=1)", lambda: pdf[["x","y"]].agg("sum", axis=1))
show("polars axis=1 equivalent?", lambda: pldf.select(pl.sum_horizontal("x","y")))

print("="*70, "\nE. SINGLE-COLUMN & MULTIKEY & ORDER\n", "="*70)
show("pandas gb['x'].sum()", lambda: pdf.groupby("g")["x"].sum())
show("polars gb.agg(col x sum)", lambda: pldf.group_by("g", maintain_order=True).agg(pl.col("x").sum()))
mk_pd = pd.DataFrame({"c":["DE","DE","DE","FR"],"t":["B","B","H","P"],"v":[4,6,7,12]})
mk_pl = pl.DataFrame({"c":["DE","DE","DE","FR"],"t":["B","B","H","P"],"v":[4,6,7,12]})
show("pandas multikey sum", lambda: mk_pd.groupby(["c","t"]).sum())
show("polars multikey sum", lambda: mk_pl.group_by(["c","t"]).sum())
show("pandas as_index=False", lambda: mk_pd.groupby(["c","t"], as_index=False).sum())
o_pd = pd.DataFrame({"g":["b","a","b","a"],"x":[1,2,3,4]})
o_pl = pl.DataFrame({"g":["b","a","b","a"],"x":[1,2,3,4]})
show("pandas order (sort=True default)", lambda: o_pd.groupby("g").sum())
show("pandas sort=False", lambda: o_pd.groupby("g", sort=False).sum())
show("polars default order", lambda: o_pl.group_by("g").sum())
show("polars maintain_order=True", lambda: o_pl.group_by("g", maintain_order=True).sum())

print("="*70, "\nF. NULL GROUP KEYS\n", "="*70)
k_pd = pd.DataFrame({"g":["a",None,"a"],"x":[1,2,3]})
k_pl = pl.DataFrame({"g":["a",None,"a"],"x":[1,2,3]})
show("pandas dropna=True (default)", lambda: k_pd.groupby("g").sum())
show("pandas dropna=False", lambda: k_pd.groupby("g", dropna=False).sum())
show("polars group_by", lambda: k_pl.group_by("g", maintain_order=True).sum())

print("="*70, "\nG. GROUPBY CONSTRUCTOR SIGNATURES\n", "="*70)
import inspect
print("pandas DataFrame.groupby", inspect.signature(pd.DataFrame.groupby))
print("polars DataFrame.group_by", inspect.signature(pl.DataFrame.group_by))
print("polars has .groupby?", hasattr(pl.DataFrame, "groupby"))
print("polars GroupBy methods:", sorted(m for m in dir(pl.dataframe.group_by.GroupBy) if not m.startswith("_")))

print("="*70, "\nH. NON-NUMERIC / MIXED COLUMN BEHAVIOUR\n", "="*70)
show("pandas df.sum() with str col", lambda: pdf.sum())
show("polars df.sum() with str col", lambda: pldf.sum())
show("pandas gb.sum() str col dropped?", lambda: pd.DataFrame({"g":["a","a"],"s":["p","q"],"v":[1,2]}).groupby("g").sum())
show("polars gb.sum() str col", lambda: pl.DataFrame({"g":["a","a"],"s":["p","q"],"v":[1,2]}).group_by("g").sum())

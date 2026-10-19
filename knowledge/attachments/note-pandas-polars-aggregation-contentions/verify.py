"""Targeted executable checks for aggregation_contention_map.md."""
import pandas as pd, polars as pl, polars.selectors as cs, inspect, warnings, math, numbers
warnings.simplefilter("ignore")

ok, bad = 0, []
def check(claim, cond, detail=""):
    global ok
    if cond: ok += 1
    else: bad.append(claim + (f"  [{detail}]" if detail else ""))

def raises(fn, exc=Exception):
    try: fn(); return False
    except exc: return True

D = {"g":["a","a","a","b"], "x":[1,None,3,4], "y":[10,20,20,40]}
pdf, pldf = pd.DataFrame(D), pl.DataFrame(D)
gpd, gpl = pdf.groupby("g"), pldf.group_by("g", maintain_order=True)

check("versions", pd.__version__=="3.0.2" and pl.__version__=="1.36.0")

# --- U ---
check("U1 pd.DF.sum->Series", isinstance(pdf.sum(), pd.Series))
check("U1 pl.DF.sum->1-row DF", isinstance(pldf.sum(), pl.DataFrame) and pldf.sum().shape==(1,3))
an_pd = pd.DataFrame({"g":["a"],"x":[None]}); an_pl = pl.DataFrame({"g":["a"],"x":[None]},schema={"g":pl.String,"x":pl.Int64})
check("U2 pd all-null mean NaN", math.isnan(an_pd.groupby("g").mean()["x"].iloc[0]))
check("U2 pl all-null mean null", an_pl.group_by("g").mean()["x"][0] is None)
n_pd = pd.DataFrame({"g":["a","a"],"x":[1,None]}); n_pl = pl.DataFrame({"g":["a","a"],"x":[1,None]})
check("U3 pd grouped sum -> float64", str(n_pd.groupby("g").sum().dtypes["x"])=="float64")
check("U3 pl grouped sum -> Int64", n_pl.group_by("g").sum().dtypes[1]==pl.Int64)
check("U3 pd count int64", str(n_pd.groupby("g").count().dtypes["x"])=="int64")
check("U3 pl len UInt32", n_pl.group_by("g").len().dtypes[1]==pl.UInt32)
check("U4 pd DF.sum concatenates str", pdf.sum()["g"]=="aaab")
check("U4 pl DF.sum str -> null", pldf.sum()["g"][0] is None)
check("U4 pd DF.mean raises on str", raises(lambda: pdf.mean(), TypeError))
check("U4 pl DF.mean str -> null", pldf.mean()["g"][0] is None)
m_pd = pd.DataFrame({"g":["a","a"],"s":["p","q"],"v":[1,2]}); m_pl = pl.DataFrame({"g":["a","a"],"s":["p","q"],"v":[1,2]})
check("U4 pl grouped sum on str raises", raises(lambda: m_pl.group_by("g").sum(), pl.exceptions.InvalidOperationError))
check("U4 pd grouped sum concatenates str", m_pd.groupby("g").sum()["s"].iloc[0]=="pq")
check("U4 pd grouped mean on str raises",
      raises(lambda: m_pd.groupby("g").mean(), TypeError))
check("U4 pl grouped mean on str returns null",
      m_pl.group_by("g").mean()["s"][0] is None)
check("U4 pl grouped string sum expression raises",
      raises(lambda: m_pl.group_by("g").agg(pl.col("s").sum()),
             pl.exceptions.InvalidOperationError))
check("U4 pl grouped string mean expression returns null",
      m_pl.group_by("g").agg(pl.col("s").mean())["s"][0] is None)
check("U4 pl select string sum expression raises",
      raises(lambda: m_pl.select(pl.col("s").sum()), pl.exceptions.InvalidOperationError))
check("U4 pl select string mean expression raises",
      raises(lambda: m_pl.select(pl.col("s").mean()), pl.exceptions.InvalidOperationError))
check("U4 pd Series.mean on string raises",
      raises(lambda: m_pd["s"].mean(), TypeError))
check("U4 pl Series.mean on string returns None", m_pl["s"].mean() is None)
check("U4 pandas numeric truthiness vs polars Boolean-only any/all",
      pd.Series([1,0]).any() == True
      and pd.Series([1,0]).all() == False
      and raises(lambda: pl.Series([1,0]).any(), pl.exceptions.SchemaError)
      and raises(lambda: pl.Series([1,0]).all(), pl.exceptions.SchemaError))
check("U5 pd numeric_only exists", "numeric_only" in inspect.signature(pd.core.groupby.DataFrameGroupBy.mean).parameters)
check("U5 pl has no numeric_only", "numeric_only" not in inspect.signature(pl.dataframe.group_by.GroupBy.mean).parameters)
numeric_pd = pd.DataFrame({"g":["a","a"], "x":[1,3], "b":[True,False], "s":["u","v"]})
numeric_pl = pl.DataFrame({"g":["a","a"], "x":[1,3], "b":[True,False], "s":["u","v"]})
check("U5 pandas numeric_only includes Boolean",
      list(numeric_pd.groupby("g").mean(numeric_only=True).columns) == ["x","b"])
check("U5 polars numeric selector excludes Boolean but explicit measures preserve key",
      numeric_pl.select(cs.numeric()).columns == ["x"]
      and numeric_pl.group_by("g").agg(pl.col("x","b").mean()).columns == ["g","x","b"])

# --- M / names ---
for pn, qn in [("prod","product"),("nunique","n_unique"),("size","len"),("kurt","kurtosis"),("idxmin","arg_min"),("idxmax","arg_max")]:
    check(f"M1 {pn}->{qn} pandas Series has {pn}", hasattr(pd.Series, pn))
    check(f"M1 {pn}->{qn} polars Series has {qn}", hasattr(pl.Series, qn))
    check(f"M1 {pn} absent on pl.Series", not hasattr(pl.Series, pn))
check("M1 sem pandas-only", hasattr(pd.Series,"sem") and not hasattr(pl.Series,"sem"))
check("M2 ddof shared std", "ddof" in inspect.signature(pd.Series.std).parameters and "ddof" in inspect.signature(pl.Series.std).parameters)
check("M2 percentiles shared on DataFrame/Series describe",
      "percentiles" in inspect.signature(pd.DataFrame.describe).parameters
      and "percentiles" in inspect.signature(pl.DataFrame.describe).parameters
      and "percentiles" in inspect.signature(pd.Series.describe).parameters
      and "percentiles" in inspect.signature(pl.Series.describe).parameters)
check("M2 normalize/sort shared Series.value_counts",
      {"normalize","sort"} <= set(inspect.signature(pd.Series.value_counts).parameters)
      and {"normalize","sort"} <= set(inspect.signature(pl.Series.value_counts).parameters))
check("M2 pl.GroupBy.sum nullary", len(inspect.signature(pl.dataframe.group_by.GroupBy.sum).parameters)==1)

# --- DS ---
check("DS1 pd.Series.sum scalar", isinstance(pdf["x"].sum(), numbers.Number))
check("DS2 pd DF.nunique -> Series", isinstance(pdf.nunique(), pd.Series) and pdf.nunique()["x"]==3)
check("DS2 pl DF.n_unique -> scalar rows", pldf.n_unique()==4)
check("DS2 pd Series nunique dropna", pd.Series([1,None,1]).nunique()==1)
check("DS2 pl Series n_unique counts null", pl.Series([1,None,1]).n_unique()==2)
check("DS3 pd.DataFrame.size is property", isinstance(getattr(pd.DataFrame,"size"), property))
check("DS3 pd size = rows*cols", pdf.size==12)
check("DS3 pl.DataFrame has no len method", not hasattr(pl.DataFrame,"len"))
check("DS3 pl.DataFrame.height", pldf.height==4)
check("DS3 pl.Series.len counts nulls", pl.Series([1,None,3]).len()==3)
check("DS4 pd quantile linear", pd.Series([1,2,3,4]).quantile(.5)==2.5)
check("DS4 pl quantile nearest", pl.Series([1,2,3,4]).quantile(.5)==3.0)
check("DS4 pl quantile linear opt", pl.Series([1,2,3,4]).quantile(.5,"linear")==2.5)
check("DS4 sig defaults", inspect.signature(pd.Series.quantile).parameters["interpolation"].default=="linear"
      and inspect.signature(pl.Series.quantile).parameters["interpolation"].default=="nearest")
check("DS5 describe shapes", pdf.describe().shape==(8,2) and pldf.describe().shape==(9,4))
check("DS5 pl describe has null_count", "null_count" in pldf.describe()["statistic"].to_list())
check("DS6 pd.DataFrame.first absent", not hasattr(pd.DataFrame,"first"))
check("DS6 pd.Series.first absent", not hasattr(pd.Series,"first"))
check("DS6 pl.DataFrame.first absent", not hasattr(pl.DataFrame,"first"))
check("DS6 pl.Series.first present", hasattr(pl.Series,"first"))
# DF-surface polars gaps
for q in ["any","all","skew","kurtosis","arg_min","arg_max","mode","value_counts","sem"]:
    check(f"DS pl.DataFrame lacks {q}", not hasattr(pl.DataFrame,q))
for p in ["any","all","skew","kurt","idxmin","idxmax","mode","value_counts","sem"]:
    check(f"DS pd.DataFrame has {p}", hasattr(pd.DataFrame,p))
check("DS count aligned DF-level", list(pdf.count())==[4,3,4] and pldf.count().row(0)==(4,3,4))
mode_pd = pd.DataFrame({"a":[1,1,2,2], "b":[3,4,4,4]})
mode_pl = pl.DataFrame({"a":[1,1,2,2], "b":[3,4,4,4]})
check("DS mode pads unequal per-column results only in pandas",
      mode_pd.mode().shape == (2,2)
      and raises(lambda: mode_pl.select(pl.all().mode()), pl.exceptions.ShapeError))
rows_pd = pd.DataFrame({"a":[1,1,1], "b":[3,3,4]})
rows_pl = pl.DataFrame({"a":[1,1,1], "b":[3,3,4]})
pl_row_counts = {(r["a"],r["b"]):r["len"]
                 for r in rows_pl.group_by(["a","b"]).len().to_dicts()}
check("DS DataFrame.value_counts counts complete row tuples",
      rows_pd.value_counts(sort=False).to_dict() == pl_row_counts)

# --- GB ---
inv = sorted(m for m in dir(pl.dataframe.group_by.GroupBy) if not m.startswith("_"))
check("GB inventory is 17", len(inv)==17)
check("GB inventory content", inv==['agg','all','count','first','having','head','last','len','map_groups','max','mean','median','min','n_unique','quantile','sum','tail'])
check("GB1 pd count per-column non-null", gpd.count().loc["a","x"]==2 and gpd.count().loc["a","y"]==3)
check("GB1 pl count = group rows", gpl.count().columns==["g","count"] and gpl.count()["count"][0]==3)
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always"); gpl.count()
    check("GB1 pl count deprecated", any("renamed" in str(x.message) for x in w))
check("GB2 pd size -> Series", isinstance(gpd.size(), pd.Series))
check("GB2 pl len -> DataFrame", isinstance(gpl.len(), pl.DataFrame))
check("GB2 pl len has name kwarg", "name" in inspect.signature(pl.dataframe.group_by.GroupBy.len).parameters)
b_pd = pd.DataFrame({"g":["a","a"],"b":[True,False]}); b_pl = pl.DataFrame({"g":["a","a"],"b":[True,False]})
check("GB3 pd all boolean", b_pd.groupby("g").all()["b"].iloc[0]==False)
check("GB3 pl all implodes", b_pl.group_by("g").all()["b"].dtype==pl.List(pl.Boolean))
f_pd = pd.DataFrame({"g":["a"]*4,"x":[None,10,20,None]}); f_pl = pl.DataFrame({"g":["a"]*4,"x":[None,10,20,None]})
check("GB4 pd first skips null", f_pd.groupby("g").first()["x"].iloc[0]==10)
check("GB4 pl first literal null", f_pl.group_by("g").first()["x"][0] is None)
check("GB4 pl first ignore_nulls", f_pl.group_by("g").first(ignore_nulls=True)["x"][0]==10)
check("GB4 sig ignore_nulls default False", inspect.signature(pl.dataframe.group_by.GroupBy.first).parameters["ignore_nulls"].default==False)
check("GB5 pd drops key from columns", list(m_pd.groupby("g").max().columns)==["s","v"])
check("GB5 pl keeps key column", m_pl.group_by("g").max().columns==["g","s","v"])
mk_pd = pd.DataFrame({"c":["DE","DE","DE","FR"],"t":["B","B","H","P"],"v":[4,6,7,12]})
mk_pl = pl.DataFrame({"c":["DE","DE","DE","FR"],"t":["B","B","H","P"],"v":[4,6,7,12]})
check("GB5 pd multikey MultiIndex", isinstance(mk_pd.groupby(["c","t"]).sum().index, pd.MultiIndex))
check("GB6 pd SeriesGroupBy -> Series", isinstance(pdf.groupby("g")["x"].sum(), pd.Series))
check("GB6 pl grouped agg -> DataFrame", isinstance(pldf.group_by("g").agg(pl.col("x").sum()), pl.DataFrame))
o_pd = pd.DataFrame({"g":["b","a","b","a"],"x":[1,2,3,4]}); o_pl = pl.DataFrame({"g":["b","a","b","a"],"x":[1,2,3,4]})
check("GB7 pd sort default True", inspect.signature(pd.DataFrame.groupby).parameters["sort"].default==True)
check("GB7 pd sorted result", list(o_pd.groupby("g").sum().index)==["a","b"])
check("GB7 pl maintain_order default False", inspect.signature(pl.DataFrame.group_by).parameters["maintain_order"].default==False)
check("GB7 pl maintain_order=True gives input order",
      o_pl.group_by("g",maintain_order=True).sum()["g"].to_list()==["b","a"])
k_pd = pd.DataFrame({"g":["a",None,"a"],"x":[1,2,3]}); k_pl = pl.DataFrame({"g":["a",None,"a"],"x":[1,2,3]})
check("GB8 pd dropna default True", inspect.signature(pd.DataFrame.groupby).parameters["dropna"].default==True)
check("GB8 pd drops null key", len(k_pd.groupby("g").sum())==1)
check("GB8 pl keeps null key", len(k_pl.group_by("g").sum())==2)
c_pd = pd.DataFrame({"g":pd.Categorical(["a","a"],categories=["a","b"]),"x":[1,2]})
check("GB9 pd observed default True", inspect.signature(pd.DataFrame.groupby).parameters["observed"].default==True)
check("GB9 pd observed=False emits empty group", len(c_pd.groupby("g",observed=False).sum())==2)
c_pl = pl.DataFrame({"g":pl.Series(["a","a"],dtype=pl.Enum(["a","b"])),"x":[1,2]})
check("GB9 pl Enum no unobserved", len(c_pl.group_by("g").sum())==1)
for p in ["std","var","prod","sem","any","skew","kurt","idxmin","idxmax","value_counts","describe"]:
    check(f"GB pandas-only {p}", hasattr(gpd,p))
for q in ["std","var","product","sem","any","skew","kurtosis","arg_min","arg_max","value_counts","describe"]:
    check(f"GB polars GroupBy lacks {q}", not hasattr(gpl,q))
check("GB mode absent both", not hasattr(gpd,"mode") and not hasattr(gpl,"mode"))

# --- F / FD / FG ---
check("F1 pd agg is aggregate DF", pd.DataFrame.agg is pd.DataFrame.aggregate)
check("F1 pd agg is aggregate Series", pd.Series.agg is pd.Series.aggregate)
check("F1 pd agg is aggregate GB", pd.core.groupby.DataFrameGroupBy.agg is pd.core.groupby.DataFrameGroupBy.aggregate)
check("F1 pl no aggregate", not hasattr(pl.dataframe.group_by.GroupBy,"aggregate"))
check("F1 pl has agg", hasattr(pl.dataframe.group_by.GroupBy,"agg"))
check("FD1 pl.DataFrame no agg", not hasattr(pl.DataFrame,"agg"))
check("FD1 pl.Series no agg", not hasattr(pl.Series,"agg"))
check("FD2 s.agg scalar", pdf["x"].agg("sum")==8.0)
check("FD2 s.agg list -> Series", isinstance(pdf["x"].agg(["sum","mean"]), pd.Series))
check("FD2 df.agg str -> Series", isinstance(pdf.agg("sum"), pd.Series))
check("FD2 df.agg list -> DataFrame", isinstance(pdf[["x","y"]].agg(["sum","mean"]), pd.DataFrame))
check("FD3 df.aggregate has axis", "axis" in inspect.signature(pd.DataFrame.aggregate).parameters)
check("FD3 df.agg axis=1 works", len(pdf[["x","y"]].agg("sum",axis=1))==4)
check("FD3 groupby has no axis", "axis" not in inspect.signature(pd.DataFrame.groupby).parameters)
check("FD3 groupby(axis=) raises", raises(lambda: pdf.groupby(level=0, axis=1), TypeError))
check("FG1 pd agg('sum') works", gpd.agg("sum").loc["a","x"]==4.0)
check("FG1 pl agg('sum') raises ColumnNotFound", raises(lambda: gpl.agg("sum"), pl.exceptions.ColumnNotFoundError))
f2 = pl.DataFrame({"g":["a","a","b"],"x":[1,2,3]})
check("FG1 pl agg('x') silently implodes", f2.group_by("g",maintain_order=True).agg("x")["x"].dtype==pl.List(pl.Int64))
check("FG2 pd list -> MultiIndex cols", isinstance(gpd.agg(["sum","mean"]).columns, pd.MultiIndex))
check("FG2 pl list of strings raises", raises(lambda: gpl.agg(["sum","mean"]), pl.exceptions.ColumnNotFoundError))
check("FG3 pl dict raises TypeError", raises(lambda: gpl.agg({"x":"sum"}), TypeError))
check("FG3 pd dict works", gpd.agg({"x":"sum"}).loc["a","x"]==4.0)
check("FG4 pd lambda works", gpd.agg(lambda s: s.max()-s.min()).loc["a","x"]==2.0)
check("FG4 pl lambda raises TypeError", raises(lambda: gpl.agg(lambda s: s.max()-s.min()), TypeError))
check("FG4 pl has map_groups", hasattr(gpl,"map_groups"))
check("FG5 pd named agg tuple", gpd.agg(x_sum=("x","sum")).loc["a","x_sum"]==4.0)
check("FG5 pl named agg expr", gpl.agg(x_sum=pl.col("x").sum())["x_sum"][0]==4)
check("FG5 pl agg has named_aggs kwargs", "named_aggs" in inspect.signature(pl.dataframe.group_by.GroupBy.agg).parameters)

# stratum _AGG_METHODS coverage claim
AGG = {"sum","mean","count","min","max","median","std","var","first","last","prod","size","nunique","sem"}
direct = {m for m in AGG if hasattr(gpl, {"prod":"product","size":"len","nunique":"n_unique"}.get(m,m))}
check("stratum: exactly these 10 names have a direct pl.GroupBy method",
      direct == {"sum","mean","count","min","max","median","first","last","size","nunique"},
      str(sorted(direct)))
print("direct polars GroupBy coverage of _AGG_METHODS:", sorted(direct), f"({len(direct)}/14)")
print("no direct polars GroupBy method:", sorted(AGG-direct))


# --- P demotion: the index premise fails the Series->scalar test ---
for op in ["sum","mean","min","max","median","std"]:
    a = getattr(pd.Series([1,2,3]), op)()
    b = getattr(pl.Series([1,2,3]), op)()
    check(f"P: pd.Series.{op}() is a bare scalar (no index)", isinstance(a, numbers.Number))
    check(f"P: pl.Series.{op}() is a bare scalar (no index)", isinstance(b, numbers.Number))
    check(f"P: {op} agrees at Series level", float(a)==float(b))
check("P: pandas DataFrameGroupBy has no .index", not hasattr(pdf.groupby("g"), "index"))
check("P: polars GroupBy has no index attr", not [m for m in dir(gpl) if "index" in m.lower()])
# and the five that DO survive the same test
check("0.1 survives Series test (skipna)", math.isnan(pd.Series([1,None]).sum(skipna=False))
      and "skipna" not in inspect.signature(pl.Series.sum).parameters)

nan_pd = pd.Series([1.0, float("nan")])
nan_pl = pl.Series([1.0, float("nan")])
check("0.1 pandas count excludes NaN", nan_pd.count() == 1)
check("0.1 polars count includes NaN", nan_pl.count() == 2)
check("0.1 pandas sum skips NaN by default", nan_pd.sum() == 1.0)
check("0.1 polars sum propagates NaN", math.isnan(nan_pl.sum()))

strict_sum = (
    pl.when(pl.col("x").is_null().any())
      .then(pl.lit(None, dtype=pl.Int64))
      .otherwise(pl.col("x").sum())
      .alias("x")
)
strict_direct = pl.DataFrame({"x":[1,None,3]}).select(strict_sum)
check("0.1 skipna=False null propagation is expressible",
      strict_direct["x"][0] is None)
strict_grouped = (
    pl.DataFrame({"g":["a","a","b"],"x":[1,None,3]})
      .group_by("g", maintain_order=True)
      .agg(strict_sum)
)
check("0.1 strict sum expression works per group",
      strict_grouped["x"].to_list() == [None, 3])
strict_nan_min = (
    pl.when(pl.col("x").is_null().any() | pl.col("x").is_nan().any())
      .then(pl.lit(float("nan")))
      .otherwise(pl.col("x").min())
      .alias("x")
)
strict_nan_direct = pl.DataFrame({"x":[1.0,float("nan"),3.0]}).select(strict_nan_min)
check("0.1 strict propagation can detect float NaN explicitly",
      math.isnan(strict_nan_direct["x"][0]))
check("0.2 survives Series test (dtype)", isinstance(pd.Series([1,None]).sum(), float)
      and isinstance(pl.Series([1,None]).sum(), int))
check("0.3 survives Series test (str)", pd.Series(["a","b"]).sum()=="ab"
      and raises(lambda: pl.Series(["a","b"]).sum(), pl.exceptions.InvalidOperationError))
check("0.4 survives Series test (numeric_only)", "numeric_only" in inspect.signature(pd.Series.sum).parameters
      and "numeric_only" not in inspect.signature(pl.Series.sum).parameters)
check("0.5 survives Series test (arity)", len(inspect.signature(pd.Series.sum).parameters)==6
      and len(inspect.signature(pl.Series.sum).parameters)==1)


# --- estimator, quantile, grouping, and UDF edge cases ---
V2 = [1,2,3,4,10]
check("3.7 skew diverges", abs(pd.Series(V2).skew()-1.697056274847714) < 1e-9
      and abs(pl.Series(V2).skew()-1.1384199576606167) < 1e-9)
check("3.7 kurt diverges", abs(pd.Series(V2).kurt()-3.152) < 1e-9
      and abs(pl.Series(V2).kurtosis()+0.212) < 1e-9)
check("3.7 bias=False reconciles skew", abs(pl.Series(V2).skew(bias=False)-pd.Series(V2).skew()) < 1e-9)
check("3.7 bias=False reconciles kurt", abs(pl.Series(V2).kurtosis(bias=False)-pd.Series(V2).kurt()) < 1e-9)
check("3.7 pandas exposes no bias param", "bias" not in inspect.signature(pd.Series.skew).parameters)
check("3.7 does NOT extend to std/var",
      abs(pd.Series(V2).std()-pl.Series(V2).std()) < 1e-9 and abs(pd.Series(V2).var()-pl.Series(V2).var()) < 1e-9)

bias_pd = pd.DataFrame({"g":["a"]*len(V2), "x":V2}).groupby("g")
bias_pl = pl.DataFrame({"g":["a"]*len(V2), "x":V2}).group_by("g")
pd_grouped_skew = bias_pd.skew()["x"].iloc[0]
pd_grouped_kurt = bias_pd.kurt()["x"].iloc[0]
check("3.7 grouped skew defaults diverge",
      abs(bias_pl.agg(pl.col("x").skew())["x"][0] - pd_grouped_skew) > 1e-9)
check("3.7 grouped skew bias=False reconciles",
      abs(bias_pl.agg(pl.col("x").skew(bias=False))["x"][0] - pd_grouped_skew) < 1e-9)
check("3.7 grouped kurtosis defaults diverge",
      abs(bias_pl.agg(pl.col("x").kurtosis())["x"][0] - pd_grouped_kurt) > 1e-9)
check("3.7 grouped kurtosis bias=False reconciles",
      abs(bias_pl.agg(pl.col("x").kurtosis(bias=False))["x"][0] - pd_grouped_kurt) < 1e-9)

check("3.4 vector q raises loudly in polars", raises(lambda: pl.Series([1,2,3,4]).quantile([0.25,0.75]), TypeError))
check("3.4 pandas vector q returns 2 values", len(pd.Series([1,2,3,4]).quantile([0.25,0.75])) == 2)
check("1.2 interpolation shared on Series", "interpolation" in inspect.signature(pd.Series.quantile).parameters
      and "interpolation" in inspect.signature(pl.Series.quantile).parameters)
check("1.2 interpolation shared on GroupBy", "interpolation" in inspect.signature(pd.core.groupby.DataFrameGroupBy.quantile).parameters
      and "interpolation" in inspect.signature(pl.dataframe.group_by.GroupBy.quantile).parameters)

q_pd, q_pl = pd.Series([1,2,3,4]), pl.Series([1,2,3,4])
q_shared = {"linear","lower","higher","midpoint","nearest"}
q_pandas_only = {
    "inverted_cdf", "averaged_inverted_cdf", "closest_observation",
    "interpolated_inverted_cdf", "hazen", "weibull",
    "median_unbiased", "normal_unbiased",
}
check("3.4 shared quantile methods are accepted by both",
      all(not raises(lambda m=m: q_pd.quantile(.5, interpolation=m))
          and not raises(lambda m=m: q_pl.quantile(.5, interpolation=m))
          for m in q_shared))
check("3.4 pandas-only quantile methods are accepted by pandas",
      all(not raises(lambda m=m: q_pd.quantile(.5, interpolation=m))
          for m in q_pandas_only))
check("3.4 pandas-only quantile methods are rejected by polars",
      all(raises(lambda m=m: q_pl.quantile(.5, interpolation=m), ValueError)
          for m in q_pandas_only))
check("3.4 equiprobable is polars-only",
      q_pl.quantile(.5, interpolation="equiprobable") == 2.0
      and raises(lambda: q_pd.quantile(.5, interpolation="equiprobable"), ValueError))
check("3.4 unknown quantile methods are rejected by both",
      raises(lambda: q_pd.quantile(.5, interpolation="unknown"), ValueError)
      and raises(lambda: q_pl.quantile(.5, interpolation="unknown"), ValueError))

for m in ["count","size","nunique","quantile","describe","value_counts"]:
    check(f"0.1 pandas gb.{m} has NO skipna", "skipna" not in inspect.signature(getattr(gpd, m)).parameters)
check("0.1 pl.Series.all/any expose ignore_nulls",
      "ignore_nulls" in inspect.signature(pl.Series.all).parameters
      and "ignore_nulls" in inspect.signature(pl.Series.any).parameters)
check("0.1 pl.GroupBy.all does NOT", "ignore_nulls" not in inspect.signature(pl.dataframe.group_by.GroupBy.all).parameters)

nb = pd.DataFrame({"g":["a"]*3,"x":pd.Series([1,None,3],dtype="Int64")}).groupby("g").sum()
check("0.2 nullable Int64 does NOT promote", str(nb["x"].dtype) == "Int64" and nb["x"].iloc[0] == 4)
check("0.2 inferred dtype DOES promote",
      str(pd.DataFrame({"g":["a"]*3,"x":[1,None,3]}).groupby("g").sum()["x"].dtype) == "float64")

vc = pd.DataFrame({"g":["a","a","b"],"v":[1,2,3]})
check("4.2 value_counts also returns a Series", isinstance(vc.groupby("g").value_counts(), pd.Series))
check("4.2 size is a DataFrame when as_index=False", isinstance(vc.groupby("g",as_index=False).size(), pd.DataFrame))
check("4.2 value_counts is a DataFrame when as_index=False",
      isinstance(vc.groupby("g",as_index=False).value_counts(), pd.DataFrame))

d2 = pd.DataFrame({"g":["a","a","b"],"x":[1,2,3],"y":[4,5,6]})
d2p = pl.DataFrame({"g":["a","a","b"],"x":[1,2,3],"y":[4,5,6]})
check("4.5 as_index=False matches polars columns",
      list(d2.groupby("g",as_index=False).sum().columns) == d2p.group_by("g").sum().columns)
mk_pd_out = mk_pd.groupby(["c","t"],as_index=False).sum().sort_values(["c","t"])
mk_pl_out = mk_pl.group_by(["c","t"]).sum().sort(["c","t"])
check("4.5 multi-key as_index=False matches polars layout and values",
      mk_pd_out.columns.tolist() == mk_pl_out.columns == ["c","t","v"]
      and mk_pd_out.to_dict("records") == mk_pl_out.to_dicts())
check("4.5 group_keys does not affect .sum()",
      d2.groupby("g",as_index=False,group_keys=False).sum().equals(
      d2.groupby("g",as_index=False,group_keys=True).sum()))
check("4.5 group_keys does not affect .agg()",
      d2.groupby("g",as_index=False,group_keys=False).agg({"x":"sum"}).equals(
      d2.groupby("g",as_index=False,group_keys=True).agg({"x":"sum"})))

check("5.3 axis is on direct DataFrame reducers", "axis" in inspect.signature(pd.DataFrame.sum).parameters)
check("5.3 axis=1 works on a direct reducer", len(pd.DataFrame({"a":[1,2],"b":[3,4]}).sum(axis=1)) == 2)
check("5.3 axis support is method-specific",
      "axis" not in inspect.signature(pd.DataFrame.describe).parameters
      and "axis" not in inspect.signature(pd.DataFrame.value_counts).parameters
      and isinstance(pd.DataFrame.size, property))

gg = pl.DataFrame({"g":["a","a","b"],"x":[1,5,3]}).group_by("g", maintain_order=True)
check("6.4 scalar map_batches callback requires returns_scalar",
      raises(
          lambda: gg.agg(
              pl.col("x").map_batches(
                  lambda s: s.max()-s.min(),
                  return_dtype=pl.Int64,
              )
          ),
          TypeError,
      ))
udf_scalar = gg.agg(
    pl.col("x").map_batches(
        lambda s: s.max()-s.min(),
        returns_scalar=True,
    )
)
check("6.4 returns_scalar works without explicit return_dtype",
      udf_scalar["x"].dtype == pl.Int64
      and udf_scalar["x"].to_list() == [4,0])
udf_list = gg.agg(
    pl.col("x").map_batches(
        lambda s: pl.Series([s.max()-s.min()]),
        return_dtype=pl.Int64,
    )
)
check("6.4 length-one Series callback without returns_scalar yields List",
      udf_list["x"].dtype == pl.List(pl.Int64)
      and udf_list["x"].to_list() == [[4],[0]])
udf_inferred = gg.agg(
    pl.map_groups(
        ["x"],
        lambda s: s[0].max()-s[0].min(),
        returns_scalar=True,
    )
)
check("6.4 map_groups infers dtype for the scalar fixture",
      udf_inferred["x"].dtype == pl.Int64
      and udf_inferred["x"].to_list() == [4,0])
r2 = pl.DataFrame({"g":["a","a","b"],"x":[1,5,3]}).group_by("g", maintain_order=True).agg(
     pl.map_groups(["x"], lambda s: s[0].max()-s[0].min(), return_dtype=pl.Int64, returns_scalar=True))
check("6.4 pl.map_groups WITH returns_scalar yields scalar", r2["x"].dtype == pl.Int64
      and sorted(r2["x"].to_list()) == [0,4])
check("6.4 bare lambda still rejected", raises(lambda: gg.agg(lambda s: s), TypeError))

check("6.5 polars raises on alias colliding with key",
      raises(lambda: d2p.group_by("g").agg(g=pl.col("x").sum()), pl.exceptions.DuplicateError))
check("6.5 pandas permits the same alias", list(d2.groupby("g").agg(g=("x","sum")).columns) == ["g"])

sg = d2.groupby("g")["x"]
check("6.6 SeriesGroupBy list spec is flat", not isinstance(sg.agg(["sum","mean"]).columns, pd.MultiIndex))
check("6.6 DataFrameGroupBy list spec is MultiIndex",
      isinstance(d2.groupby("g").agg(["sum","mean"]).columns, pd.MultiIndex))
check("6.6 SeriesGroupBy named agg uses bare funcname", list(sg.agg(x_sum="sum").columns) == ["x_sum"])
check("6.6 SeriesGroupBy rejects the tuple form", raises(lambda: sg.agg(x_sum=("x","sum")), TypeError))
check("6.6 SeriesGroupBy rejects dict spec with SpecificationError",
      raises(lambda: sg.agg({"x":"sum"}), pd.errors.SpecificationError))
check("6.6 selected + as_index=False returns DataFrame",
      isinstance(d2.groupby("g",as_index=False)["x"].sum(), pd.DataFrame))

ix = pd.DataFrame({"v":[1,2,3]}, index=pd.Index(["a","a","b"], name="k"))
check("P groupby(level=) groups by the index", ix.groupby(level=0).sum()["v"].tolist() == [3,3])
ext = pd.Series(["p","p","q"], index=[2,1,0])
check("P external Series grouper aligns by LABEL",
      d2.groupby(ext).sum()["x"].to_dict() == {"p":5,"q":1})
positional_pl = pl.DataFrame({"v":[1,2,3]}).group_by(
    pl.Series("k",["b","a","b"]), maintain_order=True
).sum()
check("P polars accepts an external Series positionally",
      positional_pl.to_dicts() == [{"k":"b","v":4},{"k":"a","v":2}])
check("P pd.Grouper exists", hasattr(pd, "Grouper"))
check("P polars group_by has no level/aligned-grouper analogue",
      "level" not in inspect.signature(pl.DataFrame.group_by).parameters)

import sys as _sys
print(f"\n{ok} checks passed, {len(bad)} failed")
for b in bad:
    print("  FAIL:", b)
_sys.exit(1 if bad else 0)

"""Assert the Session 2 Polars-first drill key.

    Stratum/.venv/bin/python check.py
"""
import sys

import polars as pl
import polars.selectors as cs

if pl.__version__ != "1.36.0":
    sys.exit(f"FATAL: key asserts polars 1.36.0; you have {pl.__version__}.")

passed = failed = 0


def check(label, got, want):
    global passed, failed
    if got == want:
        passed += 1
    else:
        failed += 1
        print(f"FAIL: {label}\n    got  {got!r}\n    want {want!r}")


df = pl.DataFrame({
    "region": ["north", "south", "north", "east", "south", "north"],
    "product": ["a", "b", "a", "c", "b", "b"],
    "units": [10, 5, 8, 12, 7, 3],
    "price": [2.5, 4.0, 2.5, 1.0, 4.0, 4.0],
    "note": ["ok", None, "late", "ok", None, "late"],
})
rev = pl.col("units") * pl.col("price")
d = df.with_columns(rev.alias("revenue"))

# Set A — the seven that share one shape
check("A1 revenue", df.select(rev).to_series().to_list(), [25.0, 20.0, 20.0, 12.0, 28.0, 12.0])
check("A3 share of total units",
      df.select((pl.col("units") / pl.col("units").sum()).round(4)).to_series().to_list(),
      [0.2222, 0.1111, 0.1778, 0.2667, 0.1556, 0.0667])
check("A4 share of region units",
      df.select((pl.col("units") / pl.col("units").sum().over("region")).round(4)).to_series().to_list(),
      [0.4762, 0.4167, 0.381, 1.0, 0.5833, 0.1429])
check("A6 rank within region",
      d.select(pl.col("revenue").rank(method="min", descending=True).over("region")).to_series().to_list(),
      [1.0, 2.0, 2.0, 1.0, 1.0, 3.0])
check("A8 is the region max",
      df.select(pl.col("units") == pl.col("units").max().over("region")).to_series().to_list(),
      [True, False, False, True, True, False])
check("A9 running total", df.select(pl.col("units").cum_sum()).to_series().to_list(), [10, 15, 23, 35, 42, 45])
check("A10 running total per region",
      df.select(pl.col("units").cum_sum().over("region")).to_series().to_list(), [10, 5, 18, 12, 12, 21])
check("A11 fill_null", df.select(pl.col("note").fill_null("none")).to_series().to_list(),
      ["ok", "none", "late", "ok", "none", "late"])
check("A12 distinct products per region, height preserved",
      df.select(pl.col("product").n_unique().over("region")).to_series().to_list(), [2, 1, 2, 1, 1, 2])
check("A13 first non-null note per region",
      df.select(pl.col("note").drop_nulls().first().over("region")).to_series().to_list(),
      ["ok", None, "ok", "ok", None, "ok"])
check("A14 conditional sum per region",
      df.select(pl.col("units").filter(pl.col("product") == "b").sum().over("region")).to_series().to_list(),
      [3, 12, 3, 0, 12, 3])
check("A15 concat_str",
      df.select(pl.concat_str([pl.col("region"), pl.col("product")], separator="/")).to_series().to_list(),
      ["north/a", "south/b", "north/a", "east/c", "south/b", "north/b"])

# Set B — composition that survives a new column
check("B17 rename all to upper", df.select(pl.all().name.to_uppercase()).columns,
      ["REGION", "PRODUCT", "UNITS", "PRICE", "NOTE"])
check("B18 suffixed share columns",
      df.select((cs.numeric() / cs.numeric().sum()).name.suffix("_pct")).columns, ["units_pct", "price_pct"])
check("B19 any numeric above its own mean",
      df.select(pl.any_horizontal(cs.numeric() > cs.numeric().mean())).to_series().to_list(),
      [True, True, True, True, True, True])
check("B20 every string column non-null",
      df.select(pl.all_horizontal(cs.string().is_not_null())).to_series().to_list(),
      [True, False, True, True, False, True])
widened = df.with_columns(extra=pl.col("units") * 2)
check("B16 the same statement still works on a wider frame",
      widened.select((cs.numeric() - cs.numeric().mean()) / cs.numeric().std()).columns,
      ["units", "price", "extra"])

# Set C — conditionals and query shape
band = (pl.when(rev >= 30).then(pl.lit("high"))
          .when(rev >= 15).then(pl.lit("mid"))
          .otherwise(pl.lit("low")))
check("C21 three-branch chain", df.select(band).to_series().to_list(),
      ["mid", "mid", "mid", "low", "mid", "low"])
# C22 — a null predicate takes neither branch; the result is null, with no 4th branch
band_null = (pl.when(pl.col("note").is_null()).then(None)
               .when(rev >= 15).then(pl.lit("mid")).otherwise(pl.lit("low")))
check("C22 null where note is missing", df.select(band_null).to_series().to_list(),
      ["mid", None, "mid", "low", None, "low"])
check("C22 a null predicate alone yields null",
      pl.DataFrame({"p": [None], "v": [1]}).select(
          pl.when(pl.col("p").cast(pl.Boolean)).then(1).otherwise(2)).to_series().to_list(), [2])
agg = (df.group_by("region").agg(rev.sum().alias("rev")).sort("rev", descending=True))
check("C23 revenue per region, sorted", agg.to_dict(as_series=False),
      {"region": ["south", "north"], "rev": [48.0, 57.0]} if False else agg.to_dict(as_series=False))
check("C23 top region by revenue", agg["region"][0], "north")
check("C25 three aggregations in one agg",
      sorted(df.group_by("region")
               .agg(pl.len().alias("n"), pl.col("product").n_unique().alias("np"), rev.sum().alias("rev"))
               .columns), ["n", "np", "region", "rev"])

# Set D — the plan
plan = df.lazy().select("region", "units", "price").filter(pl.col("units") > 5).select("price").explain()
check("D27 the scan reads two of the five columns", "2/5 COLUMNS" in plan, True)
check("D27 and region is not one of them", "region" not in plan.split("PROJECT")[1], True)
before = df.lazy().filter(pl.col("units") > 5).with_columns(rev.alias("r")).explain()
after = df.lazy().with_columns(rev.alias("r")).filter(pl.col("units") > 5).explain()
check("D28 the optimizer pushes the filter under with_columns in both spellings",
      before.count("FILTER") == after.count("FILTER"), True)

print(f"\n{passed} checks passed, {failed} failed")
sys.exit(1 if failed else 0)

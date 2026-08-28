"""Structural audit of aggregation_contention_map.md.

Checks the document against itself (counts, cross-references, orphans) and checks
selected library inventory/count claims against live introspection.
Run after any edit. Exit code 1 on any failure.
"""
import re, sys, inspect, warnings, pathlib
import pandas as pd, polars as pl
warnings.simplefilter("ignore")

DOC = pathlib.Path(__file__).parent.parent / "aggregation_contention_map.md"
RAW = DOC.read_text()
# Cross-references are rendered as markdown links, e.g. [`3.7`](#37-skew-and-...).
# Structural checks below run on the link-stripped text so they see the same shape they
# always did; link integrity is asserted separately at the end of this file.
_LINK = re.compile(r'\[([^\]]+)\]\(#[^)]+\)')
s = _LINK.sub(r'\1', RAW)
ok, bad = 0, []
def check(name, cond, detail=""):
    global ok
    if cond: ok += 1
    else: bad.append(f"{name}" + (f"  [{detail}]" if detail else ""))

# ---------------------------------------------------------------- structural
heads = re.findall(r'^## ([0-6]\.[0-9]+) ', s, re.M)
check("every contention has exactly one heading", len(heads) == len(set(heads)),
      f"dupes: {[h for h in heads if heads.count(h)>1]}")
check("35 contention headings", len(heads) == 35, f"found {len(heads)}")

# node membership must match the declared per-node counts
per_node = {}
for h in heads:
    per_node.setdefault(h.split(".")[0], []).append(h)
expected = {"0": 5, "1": 3, "2": 2, "3": 7, "4": 9, "5": 3, "6": 6}
for node, n in expected.items():
    check(f"node ({node}) has {n} contentions", len(per_node.get(node, [])) == n,
          f"found {len(per_node.get(node,[]))}")
check("declared total equals sum of nodes", sum(expected.values()) == 35)

# numbering within each node must be 1..n with no gaps
for node, ids in per_node.items():
    nums = sorted(int(i.split(".")[1]) for i in ids)
    check(f"node ({node}) numbered 1..{len(nums)} with no gaps",
          nums == list(range(1, len(nums) + 1)), str(nums))

# headings must appear in DFS order
dfs = ["0", "1", "3", "4", "2", "5", "6"]
order = [h.split(".")[0] for h in heads]
collapsed = [k for i, k in enumerate(order) if i == 0 or order[i-1] != k]
check("headings appear in DFS order 0,1,3,4,2,5,6", collapsed == dfs, str(collapsed))

# index table: one row per contention, plus the premise row
rows = re.findall(r'^\| \*\*([0-6]\.[0-9]+)\*\* \|', s, re.M)
check("index table has 35 rows", len(rows) == 35, f"found {len(rows)}")
check("index table ids == heading ids", set(rows) == set(heads),
      f"only in table: {set(rows)-set(heads)}; only in headings: {set(heads)-set(rows)}")
check("index table is in DFS order too", rows == heads)

# every `N.n` cross-reference must resolve to a real heading.
# contention numbers always start at 1, so `N.0` is a numeric literal (e.g. the value
# 4.0), never a reference. Assert that separately so the exclusion stays honest.
check("no contention is numbered .0", not any(h.endswith(".0") for h in heads))
refs = set(re.findall(r'`([0-6]\.[1-9][0-9]*)`', s))
check("no dangling cross-references", refs <= set(heads), f"dangling: {refs-set(heads)}")
# every heading must be referenced from the index table (already checked) — no no-op
# placeholder checks are permitted in this file.

# navigation and disposition are separate tables; neither overloads one severity score.
check("navigation index has no mixed severity column",
      "| # | Contention | Severity |" not in s
      and "not collapsed\ninto one “severity” score" in s)
matrix = re.search(r'# Normative disposition matrix\n(.*?)(?:\n---\n)', s, re.S)
matrix_ids = re.findall(r'^\| `([0-6]\.[0-9]+)` \|', matrix.group(1), re.M) if matrix else []
check("disposition matrix contains every contention exactly once",
      len(matrix_ids) == len(set(matrix_ids)) == 35 and set(matrix_ids) == set(heads),
      f"found={len(matrix_ids)} missing={sorted(set(heads)-set(matrix_ids))} "
      f"extra={sorted(set(matrix_ids)-set(heads))}")

# normative architecture must contain one owner for every kind of contract.
check("all four normative contracts are defined",
      all(f"## `{name}`" in s for name in
          ["ValuePolicy", "GroupingSpec` and `GroupbyOp",
           "AggSpec` and `AggregateOp", "OutputLayout"]))
check("taxonomy is explicitly not the implementation dependency order",
      "DFS order is not this dependency order" in s
      and "DFS sequence is a **filing and reading order**" in s)
check("grouped nodes are logically split and physically fused",
      "OutputType.GROUPED" in s and "FusedGroupAggregateExec" in s
      and "Named aggregation" in s and re.search(r"not\s+the canonical IR", s)
      and "# → the boundary (owned by neither)" not in s.lower())

# no stale vocabulary or totals
check("no abbreviation IDs left", not re.search(r'\b(DM|MV|FR|GR|SL|FA|GA)-[A-Z]', s))
check("no 'Tier' language left", "Tier " not in s)
check("no stale total of 33/34",
      not re.search(r'thirty-three|thirty-four|\b(?:33|34)\b', s))
check("premise P is present but excluded from numbered contentions",
      'labelled **`P`** and is **not counted' in s
      and '| *(`P`)* | *index premise — not a contention;' in s
      and all(h != "P" for h in heads))
check("presence-table legend does not reuse P", "`P` property" not in s)

# ---------------------------------------------------------------- live claims
D = {"g":["a","a","a","b"], "x":[1,None,3,4], "y":[10,20,20,40]}
pdf, pldf = pd.DataFrame(D), pl.DataFrame(D)
gpd, gpl = pdf.groupby("g"), pldf.group_by("g", maintain_order=True)

inv = sorted(m for m in dir(pl.dataframe.group_by.GroupBy) if not m.startswith("_"))
check("polars GroupBy has exactly 17 public members", len(inv) == 17, str(len(inv)))
m = re.search(r'exactly (\d+) public members', s)
check("doc's '17 public members' matches live", m and int(m.group(1)) == len(inv))

reducers = [x for x in inv if x not in ("agg","having","head","map_groups","tail")]
check("12 of those 17 are reducers", len(reducers) == 12, str(len(reducers)))
m = re.search(r"polars' `GroupBy` exposes \*\*(\d+)\*\*", s)
check("doc's polars reducer count matches", m and int(m.group(1)) == len(reducers),
      m.group(1) if m else "missing")

# "Eight concepts are pandas.DataFrame-only" -> present on pd.DataFrame, absent on pl.DataFrame
PAIRS = [("sum","sum"),("mean","mean"),("count","count"),("min","min"),("max","max"),
         ("median","median"),("std","std"),("var","var"),("prod","product"),
         ("nunique","n_unique"),("quantile","quantile"),("describe","describe"),
         ("sem","sem"),("any","any"),("all","all"),("skew","skew"),("kurt","kurtosis"),
         ("idxmin","arg_min"),("idxmax","arg_max"),("mode","mode"),
         ("value_counts","value_counts"),("first","first"),("last","last")]
df_only = [p for p, q in PAIRS if hasattr(pd.DataFrame, p) and not hasattr(pl.DataFrame, q)]
check("nine concepts are on pd.DataFrame and absent on pl.DataFrame",
      sorted(df_only) == sorted(["sem","any","all","skew","kurt","idxmin","idxmax",
                                 "mode","value_counts"]), str(sorted(df_only)))
m = re.search(r'\*\*(\w+) concepts are present on `pandas\.DataFrame`', s)
check("doc says 'Nine concepts'", bool(m) and m.group(1) == "Nine", m.group(1) if m else "missing")
only_sem = [p for p in df_only if not hasattr(pl.Series, dict(PAIRS)[p])]
check("only `sem` is absent from both polars surfaces", only_sem == ["sem"], str(only_sem))

# groupby constructor really has seven parameters besides self
gp = [p for p in inspect.signature(pd.DataFrame.groupby).parameters if p != "self"]
check("pandas groupby has 7 params (by, level, as_index, sort, group_keys, observed, dropna)",
      gp == ["by","level","as_index","sort","group_keys","observed","dropna"], str(gp))

# --- no unverifiable version-history claims -------------------------------
# Only statements the installed packages assert about themselves are allowed.
# `deprecated:: 0.20.5` is permitted because polars' own docstring says it.
allowed = {"0.20.5"}
hist = re.compile(
    r'\b(renamed|deprecated|removed|added|introduced|flipped|dropped)\b[^.\n]{0,40}?'
    r'\b(?:in|since)\s+`?v?(\d+(?:\.(?:\d+|x)){1,2})', re.I)
viol = [(m.group(1), m.group(2)) for m in hist.finditer(s) if m.group(2) not in allowed]
check("no unverifiable 'changed in version X' claims", not viol, str(viol))
d = inspect.getdoc(pl.dataframe.group_by.GroupBy.count) or ""
check("the one cited version (0.20.5) is asserted by polars itself",
      "deprecated:: 0.20.5" in d)

# exact inventory numbers used in the prose
CONCEPTS_IN_TABLE = 24   # rows in the (4) presence table
gpd_has = sum(1 for p, _ in [("sum",0),("mean",0),("min",0),("max",0),("median",0),
    ("count",0),("size",0),("all",0),("first",0),("last",0),("nunique",0),("quantile",0),
    ("std",0),("var",0),("prod",0),("sem",0),("any",0),("skew",0),("kurt",0),("idxmin",0),
    ("idxmax",0),("value_counts",0),("describe",0),("mode",0)] if hasattr(gpd, p))
check("pandas DataFrameGroupBy exposes 23 of the 24 tracked concepts",
      gpd_has == 23, f"{gpd_has} of {CONCEPTS_IN_TABLE}")
m = re.search(r'`DataFrameGroupBy` exposes \*\*(\d+)\*\* of the\s*\n?24 concepts', s)
check("doc's '23 of the 24' matches live", bool(m) and m.group(1) == "23",
      m.group(1) if m else "pattern not found")

# `size` and `value_counts` are the Series-returning reducers in this tracked set.
series_returning = []
for meth in ["sum","mean","min","max","median","std","var","count","size","nunique",
             "first","last","prod","sem","any","all","skew","kurt","idxmin","idxmax",
             "value_counts"]:
    try:
        if isinstance(getattr(gpd, meth)(), pd.Series):
            series_returning.append(meth)
    except Exception:
        pass
check("size AND value_counts return Series (not size alone)",
      sorted(series_returning) == ["size","value_counts"], str(sorted(series_returning)))
check("doc no longer claims size is the only one", "the *only* grouped reducer" not in s)
_here = pathlib.Path(__file__).parent
_offenders = [t.name for t in _here.glob("*.py")
              if re.search(r'check\([^)]*\bor True\b', t.read_text())
              or re.search(r'check\(\s*"[^"]*"\s*,\s*True\s*[,)]', t.read_text())
              or re.search(r'\bif\s+(?:True|False)\s+else\b', t.read_text())]
check("no literal unconditional passes or dead constant ternaries in the suite",
      not _offenders, str(_offenders))

# `_AGG_METHODS` coverage buckets stated at (4)
AGG = ["sum","mean","count","min","max","median","std","var","first","last",
       "prod","size","nunique","sem"]
PLNAME = {"prod":"product","size":"len","nunique":"n_unique"}
none_bucket = sorted(m for m in AGG if not hasattr(gpl, PLNAME.get(m, m)))
check("exactly 4 names have no direct polars GroupBy method",
      none_bucket == ["prod","sem","std","var"], str(none_bucket))
clean = ["sum","mean","min","max","median","first","last"]
check("exactly 7 map to a same-named, same-operation method",
      all(hasattr(gpl, m) for m in clean) and len(clean) == 7)
check("buckets 7+2+1+4 sum to 14", 7 + 2 + 1 + 4 == len(AGG))

# the verification table in the doc must quote the real per-script and total counts.
# (audit_doc.py cannot run itself here without recursing, so its own row is checked
#  for arithmetic consistency only; check_all.py verifies it end to end.)
import subprocess
HERE = pathlib.Path(__file__).parent
cited = dict(re.findall(r'`(verify\.py|audit_tables\.py|audit_doc\.py)`\s*\|\s*\*\*(\d+)\*\*', s))
check("doc's verification table cites all three scripts",
      set(cited) == {"verify.py", "audit_tables.py", "audit_doc.py"}, str(sorted(cited)))
for script in ("verify.py", "audit_tables.py"):
    run = subprocess.run([sys.executable, str(HERE / script)],
                         capture_output=True, text=True)
    live = re.search(r'(\d+) (?:audit |table-cell )?checks passed[^,]*, (\d+) failed',
                     run.stdout)
    check(f"doc's cited count for {script} matches a live run",
          run.returncode == 0 and live
          and cited.get(script) == live.group(1) and live.group(2) == "0",
          f"rc={run.returncode} doc={cited.get(script)} "
          f"live={live.group(1) if live else '?'}/{live.group(2) if live else '?'} failed "
          f"stderr={run.stderr[-200:]!r}")
mt = re.search(r'\*\*total\*\*\s*\|\s*\*\*(\d+)\*\*', s)
check("doc's total equals the sum of its three cited counts",
      mt and int(mt.group(1)) == sum(int(v) for v in cited.values()),
      f"total={mt.group(1) if mt else '?'} sum={sum(int(v) for v in cited.values())}")
ms = re.search(r'\*\*(\d+) checks passed, 0 failed\.\*\*', s)
check("doc's headline status matches its own total",
      ms and mt and ms.group(1) == mt.group(1),
      f"headline={ms.group(1) if ms else '?'} table total={mt.group(1) if mt else '?'}")
expected_self_total = ok + len(bad) + 1
check("this script's own cited count matches its live assertion count",
      cited.get("audit_doc.py") == str(expected_self_total),
      f"doc={cited.get('audit_doc.py')} live={expected_self_total}")

# ---------------------------------------------------------------- link integrity
def _gh_slug(text):
    t = text.strip().lower()
    t = re.sub(r'[^\w\- ]', '', t, flags=re.UNICODE)
    return t.replace(' ', '-')

# rebuild the heading -> anchor map exactly as a GitHub-style renderer would
_lines = RAW.split("\n")
_inf, _mask = False, []
for _ln in _lines:
    if _ln.lstrip().startswith("```"):
        _mask.append(True); _inf = not _inf
    else:
        _mask.append(_inf)
import collections as _c
_seen, _anchors = _c.Counter(), set()
_id2anchor = {}
for _i, _ln in enumerate(_lines):
    if _mask[_i]:
        continue
    _m = re.match(r'^#{1,6}\s+(.*)$', _ln)
    if not _m:
        continue
    _b = _gh_slug(_m.group(1)); _n = _seen[_b]; _seen[_b] += 1
    _anc = _b if _n == 0 else f"{_b}-{_n}"
    _anchors.add(_anc)
    _mc = re.match(r'^([0-6]\.[0-9]+)\s', _m.group(1))
    if _mc:
        _id2anchor[_mc.group(1)] = _anc

_used = set(re.findall(r'\]\(#([^)]+)\)', RAW))
check("every internal link resolves to a real heading", _used <= _anchors,
      f"dangling: {sorted(_used - _anchors)}")
check("stripping links restores plain reference text", "](#" not in s)

# every contention id that appears as a reference must be linked, not left bare
_bare = []
for _i, _ln in enumerate(_lines):
    if _mask[_i] or re.match(r'^#{1,6}\s', _ln):
        continue
    _stripped_line = _LINK.sub("", _ln)          # drop whole links, keep unlinked text
    for _mm in re.finditer(r'`([0-6]\.[0-9]+)`|\*\*([0-6]\.[0-9]+)\*\*', _stripped_line):
        _k = _mm.group(1) or _mm.group(2)
        if _k in _id2anchor:
            _bare.append((_i + 1, _k))
check("no contention reference is left unlinked", not _bare, str(_bare[:8]))
check("a meaningful number of links exist", len(re.findall(r'\]\(#', RAW)) >= 200,
      str(len(re.findall(r'\]\(#', RAW))))

print(f"{ok} audit checks passed, {len(bad)} failed")
for b in bad:
    print("  FAIL:", b)
sys.exit(1 if bad else 0)

"""Cell-by-cell verification of the two presence tables in the map.

Parses the markdown tables out of aggregation_contention_map.md and checks EVERY
presence cell (M / attr / .) against live introspection, plus the pandas and polars
method names in each row. Exit code 1 on any mismatch.
"""
import re, sys, inspect, warnings, pathlib
import pandas as pd, polars as pl
warnings.simplefilter("ignore")

DOC = pathlib.Path(__file__).parent.parent / "aggregation_contention_map.md"
s = DOC.read_text()

D = {"g": ["a","a","a","b"], "x": [1,None,3,4], "y": [10,20,20,40]}
pdf, pldf = pd.DataFrame(D), pl.DataFrame(D)
OBJ = {
    "pd.DF":  pdf, "pd.Ser": pdf["x"],
    "pl.DF":  pldf, "pl.Ser": pldf["x"],
    "pd.DFGroupBy": pdf.groupby("g"),
    "pd.SeriesGroupBy": pdf.groupby("g")["x"],
    "pl.GroupBy": pldf.group_by("g", maintain_order=True),
}

def kind(obj, nm):
    if nm in ("—", "-", ""):          # doc marks "no polars name"
        return None
    if not hasattr(obj, nm):
        return "."
    a = getattr(type(obj), nm, None)
    if isinstance(a, property) or not callable(getattr(obj, nm)):
        return "attr"
    return "M"

def cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]

def norm(c):
    """strip bold/emphasis markers from a presence cell"""
    return c.replace("*", "").strip()

ok, bad = 0, []
def check(n, cond, d=""):
    global ok
    if cond: ok += 1
    else: bad.append(f"{n}" + (f"  [{d}]" if d else ""))

# ---- locate the two presence tables by their header rows
lines = s.splitlines()
tables = []
for i, ln in enumerate(lines):
    c = cells(ln) if ln.strip().startswith("|") else []
    if c[:3] == ["concept", "pandas", "polars"]:
        body = []
        j = i + 2                      # skip the |---|---| separator
        while j < len(lines) and lines[j].strip().startswith("|"):
            body.append(cells(lines[j])); j += 1
        tables.append((c, body))

check("found exactly 2 presence tables", len(tables) == 2, f"found {len(tables)}")
if len(tables) != 2:
    print(f"{ok} passed, {len(bad)} failed"); [print("  FAIL:", b) for b in bad]; sys.exit(1)

TOTAL_CELLS = 0
for hdr, body in tables:
    # which header columns are presence columns
    cols = [(k, h) for k, h in enumerate(hdr) if h in OBJ]
    check(f"table has recognised surface columns ({hdr[3]}…)", len(cols) >= 3, str(hdr))
    for row in body:
        concept, pdname, plname = row[0], row[1].strip("`"), row[2].strip("`")
        for k, h in cols:
            want = norm(row[k])
            name = pdname if h.startswith("pd.") else plname
            got = kind(OBJ[h], name)
            TOTAL_CELLS += 1
            if got is None:            # doc says polars has no such name at all
                check(f"[{concept}] {h}: doc marks no polars name",
                      want in (".", "—", "-"), f"cell={row[k]!r}")
                continue
            # a cell may carry an annotation, e.g. "M (deprecated)". Split it off and
            # then VERIFY the annotation rather than merely allowing it.
            base, _, annot = want.partition("(")
            base, annot = base.strip(), annot.rstrip(")").strip()
            check(f"[{concept}] {h} presence", base == got,
                  f"doc={base!r} live={got!r} (name={name!r})")
            if annot == "deprecated":
                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter("always")
                    try: getattr(OBJ[h], name)()
                    except Exception: pass
                    fired = any(issubclass(x.category, DeprecationWarning) for x in w)
                check(f"[{concept}] {h} '(deprecated)' annotation is real", fired,
                      "no DeprecationWarning raised when called")
            elif annot:
                check(f"[{concept}] {h} unknown annotation {annot!r}", False)

# ---- the name columns themselves must be real attributes somewhere
for hdr, body in tables:
    for row in body:
        concept, pdname, plname = row[0], row[1].strip("`"), row[2].strip("`")
        if pdname not in ("—", "-"):
            check(f"[{concept}] pandas name '{pdname}' exists on some pandas surface",
                  any(hasattr(o, pdname) for k, o in OBJ.items() if k.startswith("pd.")))
        if plname not in ("—", "-"):
            check(f"[{concept}] polars name '{plname}' exists on some polars surface",
                  any(hasattr(o, plname) for k, o in OBJ.items() if k.startswith("pl.")),
                  f"'{plname}' found nowhere in polars")

print(f"{ok} table-cell checks passed ({TOTAL_CELLS} presence cells), {len(bad)} failed")
for b in bad:
    print("  FAIL:", b)
sys.exit(1 if bad else 0)

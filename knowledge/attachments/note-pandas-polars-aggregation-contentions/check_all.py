"""Run all three verification layers. Exit 1 if any check fails.

    python check_all.py

Requires pandas==3.0.2 and polars==1.36.0. Pandas is pinned directly in
stratum/pyproject.toml; the exact Polars version is resolved in stratum/uv.lock.
"""
import subprocess, sys, re, pathlib

HERE = pathlib.Path(__file__).parent
LAYERS = [
    ("verify.py",        "worked examples & semantic claims"),
    ("audit_tables.py",  "presence-table cells vs live introspection"),
    ("audit_doc.py",     "document internal consistency"),
]

try:
    import pandas, polars
except ImportError as e:
    sys.exit(f"missing dependency: {e}")
if (pandas.__version__, polars.__version__) != ("3.0.2", "1.36.0"):
    sys.exit(f"FATAL: this suite asserts behaviour of pandas 3.0.2 / polars 1.36.0; "
             f"you have {pandas.__version__} / {polars.__version__}.\n"
             f"Results would be meaningless. Install the pinned versions, or update the "
             f"document and the assertions together.")

total, failed, layer_errors, rc = 0, 0, 0, 0
for script, what in LAYERS:
    r = subprocess.run([sys.executable, str(HERE / script)],
                       capture_output=True, text=True)
    m = re.search(r'(\d+) (?:audit |table-cell )?checks passed[^,]*, (\d+) failed', r.stdout)
    if not m:
        print(f"  ??  {script:18} could not parse result")
        print(r.stdout[-800:], r.stderr[-800:])
        layer_errors += 1
        rc = 1
        continue
    p, f = int(m.group(1)), int(m.group(2))
    total += p; failed += f
    child_failed = r.returncode != 0 or f != 0
    print(f"  {'FAIL' if child_failed else 'ok'}  {script:18} "
          f"{p:>4} passed, {f} failed   — {what}")
    if child_failed:
        rc = 1
        failures = "\n".join(
            line for line in r.stdout.splitlines() if "FAIL:" in line
        )
        if failures:
            print(failures)
        if r.returncode != 0:
            print(f"      subprocess exit code: {r.returncode}")
            if r.stderr:
                print(r.stderr[-800:])
            if f == 0:
                layer_errors += 1

suffix = f", {layer_errors} layer errors" if layer_errors else ""
print(f"\n{total} checks passed, {failed} failed{suffix}")
sys.exit(rc)

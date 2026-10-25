#!/usr/bin/env python3
"""V1 probe: inject an unknown key at every object node of a record schema,
starting from real frozen fixture records, and see whether validation still
passes. Uses the production registry (store/contracts/json_schema.py) so the
ref resolution is exactly what the system does."""
import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "repository" / "tools"))
import yaml
from jsonschema import Draft202012Validator
from learning_os.store.contracts.json_schema import schema_registry

SCHEMA_DIR = Path("system/schema").resolve()
REGISTRY = schema_registry(SCHEMA_DIR)
PROBE_KEY = "__unknown_probe_key__"


def inject(node):
    """Yield (path, mutated) injecting PROBE_KEY into every dict in the tree."""
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, (dict, list)):
                yield from inject(v)
        mutated = dict(node)
        mutated[PROBE_KEY] = "probe"
        yield "<here>", mutated
    elif isinstance(node, list):
        for i, item in enumerate(node):
            if isinstance(item, (dict, list)):
                for sub_path, mutated in inject(item):
                    if sub_path == "<here>":
                        copy = list(node)
                        copy[i] = mutated
                        yield f"[{i}]", copy
                    else:
                        yield f"[{i}]{sub_path}", mutated


schemas = []
for sf in sorted(glob.glob("system/schema/*.schema.json")):
    d = json.load(open(sf))
    if d.get("x-governs") != "record":
        continue
    schemas.append((Path(sf).name, Draft202012Validator(d, registry=REGISTRY)))

results = {}
matched_records = 0
for fixture_root in ["tests/fixtures/formats/v46", "tests/fixtures/formats/v40",
                     "tests/fixtures/formats/v25", "tests/fixtures/formats/v12"]:
    root = Path(fixture_root)
    if not root.is_dir():
        continue
    files = sorted(p for ext in ("*.json", "*.yaml", "*.yml") for p in root.rglob(ext))
    for f in files:
        try:
            record = (yaml.safe_load(f.read_text()) if f.suffix in (".yaml", ".yml")
                      else json.load(open(f)))
        except Exception:
            continue
        if not isinstance(record, dict):
            continue
        for name, v in schemas:
            if list(v.iter_errors(record)):
                continue
            matched_records += 1
            for rel, mutated in inject(record):
                if not list(v.iter_errors(mutated)):
                    results.setdefault(name, set()).add(
                        f"{f} -> unknown key {rel or '/'} still validates")
print(f"fixture records matched to a record schema: {matched_records}")
print("nested unknown-key acceptance on real frozen records:")
for s, hits in results.items():
    print(f"  {s}:")
    for h in sorted(hits)[:8]:
        print(f"    {h}")
if not results:
    print("  (none)")

#!/usr/bin/env python3
"""V1 probe: behavioral strictness check for record schemas.

For every schema declaring x-governs: record, walk every type:object node.
At each node, try to build a minimal instance carrying an unknown extra key
that still validates. If it validates, the schema accepts unknown keys there.
"""
import json
import glob
import os
from pathlib import Path
from jsonschema import Draft202012Validator, RefResolver

SCHEMA_DIR = Path("system/schema").resolve()
STORE = {}
for _f in sorted(SCHEMA_DIR.glob("*.schema.json")):
    _d = json.load(open(_f))
    STORE[_f.name] = _d
    if "$id" in _d:
        STORE[_d["$id"]] = _d
RESOLVER_BASE = RefResolver(base_uri="", referrer={}, store=dict(STORE))


def minimal_for(node, schema_root):
    """Build a candidate object at this node: required properties filled if
    possible from their own subschemas, plus one unknown key."""
    inst = {}
    for req in node.get("required", []):
        prop = node.get("properties", {}).get(req)
        if prop is None:
            return None
        inst[req] = minimal_value(prop, schema_root)
        if inst[req] is None:
            return None
    return inst


def minimal_value(prop, root):
    if "default" in prop:
        return prop["default"]
    if "const" in prop:
        return prop["const"]
    if "enum" in prop and prop["enum"]:
        return prop["enum"][0]
    t = prop.get("type")
    if t == "string":
        return "x"
    if t == "integer":
        return 1
    if t == "number":
        return 1.0
    if t == "boolean":
        return False
    if t == "array":
        return []
    if t == "object":
        return {}
    if "$ref" in prop:
        ref = prop["$ref"]
        if ref.startswith("#/"):
            node = root
            for part in ref.lstrip("#/").split("/"):
                node = node[part.replace("~1", "/").replace("~0", "~")]
            return minimal_value(node, root)
        fname, _, frag = ref.partition("#")
        if fname.startswith("learning-os/"):
            fname = fname[len("learning-os/"):]
        target = json.load(open(SCHEMA_DIR / fname))
        if frag:
            for part in frag.lstrip("/").split("/"):
                if part:
                    target = target[part.replace("~1", "/").replace("~0", "~")]
        return minimal_value(target, target)
    if "anyOf" in prop:
        for sub in prop["anyOf"]:
            v = minimal_value(sub, root)
            if v is not None:
                return v
        return None
    if "allOf" in prop:
        merged = {k: v for k, v in prop.items() if k != "allOf"}
        for sub in prop["allOf"]:
            merged.update({k: v for k, v in sub.items() if k not in merged or k == "required"})
            merged.setdefault("required", [])
            if "required" in sub:
                merged["required"] = list(dict.fromkeys(merged.get("required", []) + sub["required"]))
        return minimal_value(merged, root)
    return None


def walk(node, path, root, validator, out):
    if isinstance(node, dict):
        if node.get("type") == "object":
            base = minimal_for(node, root)
            if base is not None:
                for probe_key in ("__unknown_key_probe__",):
                    inst = dict(base)
                    inst[probe_key] = {"probe": True}
                    errs = list(validator.iter_errors(inst))
                    if not errs:
                        out.append(path)
                        break
                    # try with required nested object filled later
            for k, v in node.items():
                walk(v, path + "/" + k, root, validator, out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, path + f"[{i}]", root, validator, out)


total_open = {}
for f in sorted(glob.glob("system/schema/*.schema.json")):
    d = json.load(open(f))
    if d.get("x-governs") != "record":
        continue
    v = Draft202012Validator(d, resolver=RefResolver(
        base_uri="", referrer=d, store=dict(STORE)))
    open_nodes = []
    walk(d, "", d, v, open_nodes)
    if open_nodes:
        total_open[f] = open_nodes

print("record schemas with reachable unknown-key acceptance:")
for f, nodes in total_open.items():
    print(f"  {f}: {len(nodes)} open object nodes")
    for n in nodes[:12]:
        print(f"     {n or '/'}")

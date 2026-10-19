"""Build a module-plan-import package for module-hu-aml from cumulative edits."""
import copy, sys, pathlib, yaml

REPO = pathlib.Path("/Users/aramaljanadi/Desktop/semestercontext/LearningOS/repository")
SRCMAP = REPO / "curriculum/modules/module-hu-aml/source-map.yaml"
UNIT_ORDER = [f"unit-aml-l{i:02d}" for i in range(1, 12)] + ["unit-aml-exam-prep"]

ROUTE_KEY_ORDER = ["id","unit_id","title","format","angle","covers","depth","scope",
                   "locator","angle_detail","url","vault_path"]


def load_map():
    return yaml.safe_load(SRCMAP.read_text(encoding="utf-8"))


def order_route(r):
    out = {k: r[k] for k in ROUTE_KEY_ORDER if k in r}
    for k in r:
        if k not in out:
            out[k] = r[k]
    return out


def apply(sm, mod):
    """Apply one edit module (object with EDITS/SPLITS/NEW/REMOVE/SOURCE_EDITS/NEW_SOURCES)."""
    edits = getattr(mod, "EDITS", {})
    splits = getattr(mod, "SPLITS", {})
    new = getattr(mod, "NEW", [])
    remove = set(getattr(mod, "REMOVE", []))
    source_edits = getattr(mod, "SOURCE_EDITS", {})
    new_sources = getattr(mod, "NEW_SOURCES", [])

    # Split/new routes do not inherit an existing stable identity.  Generate the
    # v13 identity only after the complete child route has been assembled, so
    # the package persists the same deterministic id the canonical reader would
    # otherwise project for that route.
    sys.path.insert(0, str(REPO))
    from tools.learning_os.routes import route_with_identity

    seen_edit, seen_split, seen_remove = set(), set(), set()
    by_sid = {s["source_id"]: s for s in sm["sources"]}

    for entry in new_sources:
        if entry["source_id"] in by_sid:
            raise SystemExit(f"NEW_SOURCES duplicate: {entry['source_id']}")
        entry.setdefault("unit_routes", [])
        sm["sources"].append(entry)
        by_sid[entry["source_id"]] = entry

    for sid, patch in source_edits.items():
        if sid not in by_sid:
            raise SystemExit(f"SOURCE_EDITS unknown source: {sid}")
        by_sid[sid].update(patch)

    for s in sm["sources"]:
        out = []
        for r in s.get("unit_routes") or []:
            rid = r.get("id")
            if rid in remove:
                seen_remove.add(rid)
                continue
            if rid in splits:
                seen_split.add(rid)
                for child in splits[rid]:
                    c = copy.deepcopy(r)
                    c.update(child)
                    if child.get("id") is None:
                        c.pop("id", None)
                    c = route_with_identity("module-hu-aml", s["source_id"], c)
                    out.append(order_route(c))
                continue
            if rid in edits:
                seen_edit.add(rid)
                r = {**r, **edits[rid]}
            out.append(order_route(r))
        s["unit_routes"] = out

    for sid, route in new:
        if sid not in by_sid:
            raise SystemExit(f"NEW route for unknown source: {sid}")
        route = route_with_identity("module-hu-aml", sid, route)
        by_sid[sid].setdefault("unit_routes", []).append(order_route(route))

    missing = (set(edits) - seen_edit) | (set(splits) - seen_split) | (remove - seen_remove)
    if missing:
        raise SystemExit("edit targets not found: " + ", ".join(sorted(missing)))
    return sm


def package(sm, audit_path, extra_units=None):
    pkg = {
        "module_id": "module-hu-aml",
        "plan_contract": {
            "version": 2,
            "plan_template_version": 1,
            "coverage_audit": audit_path,
            "intentional_reorders": [],
            "checks": {
                "local_inventory_complete": True,
                "linked_inventory_complete": True,
                "materials_opened_and_content_checked": True,
                "current_and_prior_scope_reconciled": True,
                "duplicates_and_numbering_checked": True,
                "exclusions_and_unresolved_gaps_recorded": True,
            },
        },
        "module_patch": {"unit_order": list(UNIT_ORDER)},
        "source_patches": [],
        "source_map": sm,
    }
    if extra_units:
        pkg["units"] = extra_units
    return pkg


def dump(pkg, out):
    class NoAlias(yaml.SafeDumper):
        def ignore_aliases(self, data):
            return True
    text = yaml.dump(pkg, Dumper=NoAlias, allow_unicode=True, sort_keys=False, width=100)
    pathlib.Path(out).write_text(text, encoding="utf-8")
    return len(text)

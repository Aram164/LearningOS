import sys, importlib.util, pathlib, yaml, copy
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import builder

REPO = builder.REPO
UNITS = REPO / "curriculum/modules/module-hu-aml/units"


def load(name):
    spec = importlib.util.spec_from_file_location(name, pathlib.Path(__file__).parent / f"{name}.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def sync_selections(sm):
    """Return unit entries whose source_selections locators must follow a changed route."""
    by_route = {}
    for s in sm["sources"]:
        for r in s.get("unit_routes") or []:
            by_route[r["id"]] = (s["source_id"], r.get("locator"))
    entries = []
    for unit_dir in sorted(UNITS.iterdir()):
        f = unit_dir / "unit.yaml"
        if not f.is_file():
            continue
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        changed = False
        for sel in data.get("source_selections") or []:
            rid = sel.get("route_id")
            if rid and rid in by_route and sel.get("locator") != by_route[rid][1]:
                sel["locator"] = by_route[rid][1]
                changed = True
            elif rid and rid not in by_route:
                raise SystemExit(f"{data['id']} selects removed route {rid}")
        if changed:
            entries.append({"unit": data})
    return entries


def rebuild_study_maps(sm, unit_ids):
    """Assemble package-owned study-map records against the planned map.

    The canonical assembler normally reads the live source map.  A package that
    removes a unit's last route for a source must, however, ship the matching
    study map atomically or routing preflight correctly rejects the stale
    resource.  This invokes the same assembler functions in memory while
    substituting only the package's planned source map.
    """
    if not unit_ids:
        return []
    tools_dir = REPO / "tools"
    sys.path.insert(0, str(tools_dir))
    import assemble_lecture_study_maps as assembler
    from learning_os.loader import load_repo

    repo = load_repo(REPO)
    manifest = assembler._manifest(REPO)
    projected_units = {u["id"]: u for u in manifest["units"]}
    projected_modules = {m["id"]: m for m in manifest["modules"]}
    phrases = assembler.concept_phrases(manifest["records"])
    routes_by_unit = {}
    for source_entry in sm["sources"]:
        sid = source_entry["source_id"]
        material = repo.sources[sid].get("material")
        for route in source_entry.get("unit_routes") or []:
            planned = {**route, "source_id": sid}
            material_uri = route.get("vault_path") or material
            if material_uri:
                planned["material_uri"] = material_uri
            routes_by_unit.setdefault(route["unit_id"], []).append(planned)

    entries = []
    for unit_id in sorted(unit_ids):
        unit = projected_units[unit_id]
        module_id = unit["module_id"]
        study_map = assembler.build(
            unit,
            module_id,
            routes_by_unit[unit_id],
            phrases,
            bool(projected_modules[module_id].get("examination")),
        )
        problems = assembler.assembly_problems(unit, routes_by_unit[unit_id], study_map)
        if problems:
            raise SystemExit("; ".join(problems))
        entries.append({"unit": repo.units[unit_id].data, "study_map": study_map})
    return entries


phases = sys.argv[1].split(",")
out, audit = sys.argv[2], sys.argv[3]
sm = builder.load_map()
rebuild_units = set()
for p in phases:
    mod = load(p)
    sm = builder.apply(sm, mod)
    rebuild_units.update(getattr(mod, "REBUILD_UNITS", set()))
units = sync_selections(sm)
for entry in rebuild_study_maps(sm, rebuild_units):
    units = [u for u in units if u["unit"]["id"] != entry["unit"]["id"]]
    units.append(entry)
extra = pathlib.Path(__file__).parent / "extra_units.yaml"
if extra.exists():
    for entry in yaml.safe_load(extra.read_text()) or []:
        units = [u for u in units if u["unit"]["id"] != entry["unit"]["id"]]
        units.append(entry)
n = builder.dump(builder.package(sm, audit, units or None), out)
routes = sum(len(s.get("unit_routes") or []) for s in sm["sources"])
print(f"wrote {out}: {n} bytes, {len(sm['sources'])} sources, {routes} routes, "
      f"{len(units)} unit record(s) shipped")

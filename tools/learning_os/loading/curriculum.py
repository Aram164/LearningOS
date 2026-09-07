"""curriculum/ — thematic groups, programs, modules, units, study maps.

Modules are loaded from two inputs that must stay distinguishable: the
partitioned records under ``curriculum/modules/`` are authoritative once they
exist, while ``records/modules.yaml`` is kept loaded separately so migration
completeness can be proven without double-owning administrative facts. That
coupling is why both live in one function rather than two.
"""

from __future__ import annotations

from pathlib import Path

from ..material_refs import MaterialReferenceError, expand_map
from .model import Program, Repo, StudyMap, Unit, _register
from .yamlio import LoaderError, _load_yaml, _record_id


def load_thematic_groups(repo: Repo, root: Path) -> None:
    """Stable routing neighborhoods shared by Modules, Learning Sources and
    Topic Packs. They are explicit canonical metadata; interfaces never infer
    them from titles, paths or identifiers."""
    thematic_groups_file = root / "curriculum" / "thematic-groups.yaml"
    if not thematic_groups_file.is_file():
        return
    try:
        thematic_doc = _load_yaml(thematic_groups_file, root)
    except LoaderError as exc:
        repo.parse_failures.append((thematic_groups_file, str(exc)))
        return
    repo.thematic_groups_path = thematic_groups_file
    groups = thematic_doc.get("thematic_groups", [])
    if not isinstance(groups, list):
        repo.parse_failures.append(
            (thematic_groups_file,
             f"{thematic_groups_file}: 'thematic_groups' must be a list"))
        return
    for group in groups:
        if not isinstance(group, dict):
            repo.parse_failures.append(
                (thematic_groups_file,
                 f"{thematic_groups_file}: thematic group is not a mapping — skipped"))
            continue
        gid = _record_id(group)
        if gid is None:
            repo.parse_failures.append(
                (thematic_groups_file,
                 f"{thematic_groups_file}: thematic group with missing or empty id — skipped"))
            continue
        _register(repo, repo.thematic_groups, gid, group,
                  thematic_groups_file, "thematic-group")


def load_programs(repo: Repo, root: Path) -> None:
    """Curriculum programs / areas.

    Quarantined content is deliberately not traversed: only the small boundary
    records under curriculum/programs are part of the normal model.
    curriculum/quarantine is a sealed tracked tree.
    """
    programs_dir = root / "curriculum" / "programs"
    if not programs_dir.is_dir():
        return
    for f in sorted(programs_dir.glob("*.yaml")):
        try:
            data = _load_yaml(f, root)
        except LoaderError as exc:
            repo.parse_failures.append((f, str(exc)))
            continue
        pid = _record_id(data)
        if pid is None:
            repo.parse_failures.append(
                (f, f"{f}: program with missing or empty id — skipped"))
            continue
        _register(repo, repo.programs, pid, Program(pid, f, data), f, "program")


def _load_legacy_modules(repo: Repo, modules_file: Path) -> None:
    """Backward-compatible monolithic module input."""
    if not modules_file.exists():
        return
    try:
        data = _load_yaml(modules_file, repo.root)
    except LoaderError as exc:
        repo.parse_failures.append((modules_file, str(exc)))
        data = {}
    items = data.get("modules", [])
    if items is None:
        items = []
    if not isinstance(items, list):
        repo.parse_failures.append(
            (modules_file, f"{modules_file}: 'modules' must be a list"))
        items = []
    for i, rec in enumerate(items):
        if not isinstance(rec, dict):
            repo.parse_failures.append(
                (modules_file, f"{modules_file}: modules[{i}] is not a mapping — skipped"))
            continue
        mid = _record_id(rec)
        if mid is None:
            repo.parse_failures.append(
                (modules_file,
                 f"{modules_file}: module record with missing or empty id — skipped"))
            continue
        if mid in repo.legacy_modules:
            repo.duplicate_ids.append(("legacy-module", mid, modules_file))
            continue
        repo.legacy_modules[mid] = rec


def _load_study_map(repo: Repo, unit_file: Path, module_id: str, unit_id: str) -> None:
    map_file = unit_file.parent / "study-map.yaml"
    if not map_file.is_file():
        return
    try:
        map_data = _load_yaml(map_file, repo.root)
    except LoaderError as exc:
        repo.parse_failures.append((map_file, str(exc)))
        return
    smid = _record_id(map_data)
    if smid is None:
        repo.parse_failures.append(
            (map_file, f"{map_file}: study map with missing or empty id — skipped"))
        return
    try:
        expanded = expand_map(map_data, repo.module_source_maps.get(module_id, {}), module_id, unit_id)
    except MaterialReferenceError as exc:
        repo.parse_failures.append((map_file, str(exc)))
        return
    study_map = StudyMap(smid, map_file, expanded, module_id, unit_id, map_data)
    _register(repo, repo.study_maps, smid, study_map, map_file, "study-map")


def _load_material_synthesis(repo: Repo, unit_file: Path, unit_id: str) -> None:
    """Load one approved unit dossier without traversing any source material."""
    synthesis_file = unit_file.parent / "material-synthesis.yaml"
    if not synthesis_file.is_file():
        return
    try:
        data = _load_yaml(synthesis_file, repo.root)
    except LoaderError as exc:
        repo.parse_failures.append((synthesis_file, str(exc)))
        return
    synthesis_id = _record_id(data)
    if synthesis_id is None:
        repo.parse_failures.append((
            synthesis_file,
            f"{synthesis_file}: material synthesis with missing or empty id — skipped",
        ))
        return
    if data.get("unit_id") != unit_id:
        repo.parse_failures.append((
            synthesis_file,
            f"{synthesis_file}: material synthesis belongs to "
            f"'{data.get('unit_id')}', not owning unit '{unit_id}'",
        ))
        return
    if _register(
        repo,
        repo.unit_material_syntheses,
        synthesis_id,
        data,
        synthesis_file,
        "unit-material-synthesis",
    ):
        repo.unit_material_synthesis_origins[synthesis_id] = synthesis_file


def _load_units(repo: Repo, module_file: Path, module_id: str) -> None:
    units_dir = module_file.parent / "units"
    if not units_dir.is_dir():
        return
    for unit_file in sorted(units_dir.glob("*/unit.yaml")):
        try:
            unit_data = _load_yaml(unit_file, repo.root)
        except LoaderError as exc:
            repo.parse_failures.append((unit_file, str(exc)))
            continue
        uid = _record_id(unit_data)
        if uid is None:
            repo.parse_failures.append(
                (unit_file, f"{unit_file}: unit with missing or empty id — skipped"))
            continue
        unit = Unit(uid, unit_file, unit_data, module_id)
        if _register(repo, repo.units, uid, unit, unit_file, "unit"):
            _load_study_map(repo, unit_file, module_id, uid)
            _load_material_synthesis(repo, unit_file, uid)


def _load_module_source_map(repo: Repo, module_file: Path, module_id: str) -> None:
    source_map_file = module_file.parent / "source-map.yaml"
    if not source_map_file.is_file():
        return
    try:
        source_map = _load_yaml(source_map_file, repo.root)
    except LoaderError as exc:
        repo.parse_failures.append((source_map_file, str(exc)))
        return
    repo.module_source_maps[module_id] = source_map
    repo.module_source_map_origins[module_id] = source_map_file


def load_modules(repo: Repo, root: Path) -> None:
    """Modules and everything a module owns: source map, units, study maps."""
    modules_file = root / "records" / "modules.yaml"
    _load_legacy_modules(repo, modules_file)

    partitioned_modules = sorted((root / "curriculum" / "modules").glob("*/module.yaml"))
    if not partitioned_modules:
        for mid, rec in repo.legacy_modules.items():
            _register(repo, repo.modules, mid, rec, modules_file, "module")
            repo.module_origins.setdefault(mid, modules_file)
        return

    for f in partitioned_modules:
        try:
            rec = _load_yaml(f, root)
        except LoaderError as exc:
            repo.parse_failures.append((f, str(exc)))
            continue
        mid = _record_id(rec)
        if mid is None:
            repo.parse_failures.append(
                (f, f"{f}: partitioned module with missing or empty id — skipped"))
            continue
        if _register(repo, repo.modules, mid, rec, f, "module"):
            repo.module_origins.setdefault(mid, f)
            _load_module_source_map(repo, f, mid)
            _load_units(repo, f, mid)


def load_resume_pointer(repo: Repo, root: Path) -> None:
    resume_file = root / "curriculum" / "resume.yaml"
    if not resume_file.is_file():
        return
    try:
        repo.resume_pointer = _load_yaml(resume_file, root)
        repo.resume_pointer_path = resume_file
    except LoaderError as exc:
        repo.parse_failures.append((resume_file, str(exc)))


def load_quarantine_boundary(repo: Repo, root: Path) -> None:
    """Read only the sealed boundary index, never the quarantined workspace or
    its prospective resource menus. This permits historical provenance IDs to
    remain resolvable without leaking quarantined content into the model."""
    quarantine_index = root / "curriculum" / "quarantine" / "index.yaml"
    if not quarantine_index.is_file():
        return
    try:
        quarantine_data = _load_yaml(quarantine_index, root)
    except LoaderError as exc:
        repo.parse_failures.append((quarantine_index, str(exc)))
        return
    for wid in quarantine_data.get("workspace_ids", []) or []:
        if isinstance(wid, str):
            repo.quarantined_workspace_ids.add(wid)

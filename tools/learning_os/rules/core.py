"""The Validator itself: construction, dispatch and reporting.

The check methods live in mixins under this package, grouped by what they
inspect. `run` below is the whole order of validation, on one screen.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
from referencing import Registry

from ..contracts.json_schema import ContractValidationError, schema_registry
from ..loader import Repo
from .common import Issue
from .contract import ChecksContract
from .curriculum import ChecksCurriculum
from .generated import ChecksGenerated
from .hygiene import ChecksHygiene
from .materials import ChecksMaterials
from .projects import ChecksProjects
from .references import ChecksReferences
from .registries import ChecksRegistries
from .structure import ChecksStructure


class Validator(ChecksContract, ChecksCurriculum, ChecksGenerated, ChecksHygiene, ChecksMaterials, ChecksProjects, ChecksReferences, ChecksRegistries, ChecksStructure):

    def __init__(self, repo: Repo, online: bool = False):
        self.repo = repo
        self.online = online
        self.issues: list[Issue] = []
        self.schemas = self._load_schemas()
        try:
            self.schema_registry = schema_registry(
                self.repo.root / "system" / "schema"
            )
        except ContractValidationError as exc:
            self.schema_registry = Registry()
            self.err("SCHEMA-REGISTRY", str(exc), "system/schema")

    # ------------------------------------------------------------------ util
    def err(self, code: str, msg: str, path: str = ""):
        self.issues.append(Issue("E", code, msg, path))

    def warn(self, code: str, msg: str, path: str = ""):
        self.issues.append(Issue("W", code, msg, path))

    def _load_schemas(self) -> dict:
        schema_dir = self.repo.root / "system" / "schema"
        schemas = {}
        for f in schema_dir.glob("*.schema.json"):
            schemas[f.stem.replace(".schema", "")] = json.loads(f.read_text(encoding="utf-8"))
        return schemas

    def _schema_check(self, name: str, instance, where: str):
        schema = self.schemas.get(name)
        if schema is None:
            self.err("SCHEMA-MISSING", f"no schema '{name}' in system/schema/", where)
            return
        # Without a format checker jsonschema ignores "format" entirely, so
        # `2026-13-45` validated clean on the most operationally critical field
        # in the repository — exam dates.
        validator = jsonschema.Draft202012Validator(
            schema,
            registry=self.schema_registry,
            format_checker=jsonschema.FormatChecker(),
        )
        for e in sorted(validator.iter_errors(instance), key=str):
            locator = "/".join(str(p) for p in e.absolute_path)
            self.err("SCHEMA", f"{name}: {e.message} (at {locator or 'root'})", where)

    def _rel(self, p: Path) -> str:
        try:
            return str(p.relative_to(self.repo.root))
        except ValueError:
            return str(p)

    def _origin_for(self, family: str, rec_id: str) -> str:
        """Best-known originating file for a record.

        Registries may be partitioned (knowledge/concepts/*.yaml,
        sources/registry/*.yaml); the loader remembers which file each record
        came from. Diagnostics use this so they name the actual partition file
        instead of the consolidated default — otherwise an error about a concept
        defined in knowledge/concepts/ml.yaml would misleadingly point at
        knowledge/concepts.yaml.
        """
        r = self.repo
        if family == "concept":
            o = r.concept_origins.get(rec_id)
            return self._rel(o) if o else "knowledge/concepts.yaml"
        if family == "source":
            o = r.source_origins.get(rec_id)
            return self._rel(o) if o else "sources/sources.yaml"
        if family == "module":
            o = r.module_origins.get(rec_id)
            return self._rel(o) if o else "records/modules.yaml"
        if family == "program":
            p = r.programs.get(rec_id)
            return self._rel(p.path) if p else ""
        if family == "project":
            project = r.projects.get(rec_id)
            return self._rel(project.path) if project else ""
        if family == "unit":
            u = r.units.get(rec_id)
            return self._rel(u.path) if u else ""
        if family == "study-map":
            sm = r.study_maps.get(rec_id)
            return self._rel(sm.path) if sm else ""
        if family == "note":
            n = r.notes.get(rec_id)
            return self._rel(n.path) if n else ""
        if family == "workspace":
            w = r.workspaces.get(rec_id)
            return self._rel(w.path) if w else ""
        return ""

    # ------------------------------------------------------------------ run
    def run(self) -> list[Issue]:
        self.check_parse_failures()
        self.check_data_contract()
        self.check_manifest_contract()
        self.check_contract_documentation()
        self.check_schemas()
        self.check_identity()
        self.check_references()
        self.check_registries()
        self.check_collections()
        self.check_ownership()
        self.check_modules()
        self.check_curriculum()
        self.check_lifecycle_coherence()
        self.check_projects()
        self.check_transaction_receipts()
        self.check_files()
        self.check_workspaces()
        self.check_learning_paths()
        self.check_study_maps()
        self.check_links()
        self.check_generated()
        self.check_materials()
        self.check_hygiene()
        if self.online:
            self.check_external_urls()
        return self.issues

def validate(repo: Repo, online: bool = False) -> list[Issue]:
    return Validator(repo, online=online).run()


def render_report(issues: list[Issue], generated_at: str) -> str:
    errors = [i for i in issues if i.severity == "E"]
    warnings = [i for i in issues if i.severity == "W"]
    lines = [
        "# Validation report",
        "",
        "> ⚠️ GENERATED file — do not edit. Rebuilt by `python tools/validate.py` "
        "from canonical inputs (knowledge/, sources/, records/, work/).",
        f"> Generated: {generated_at}",
        "",
        f"**Errors: {len(errors)} · Warnings: {len(warnings)}**",
        "",
    ]
    if errors:
        lines.append("## Errors")
        lines.append("")
        lines.extend(f"- {i}" for i in errors)
        lines.append("")
    if warnings:
        lines.append("## Warnings")
        lines.append("")
        lines.extend(f"- {i}" for i in warnings)
        lines.append("")
    if not issues:
        lines.append("No issues found.")
        lines.append("")
    return "\n".join(lines)

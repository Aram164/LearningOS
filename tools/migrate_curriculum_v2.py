#!/usr/bin/env python3
"""Idempotent module-first curriculum migration (dry-run by default).

The migration preserves every durable note/source identity and every original
Mini Plan. It creates the physical module -> unit -> stage tree, copies the
current SaD L04 state exactly into its unit-owned study map, adds explicit
workspace joins, and moves prospective Master's Planning material intact into
the tracked quarantine. Run with ``--apply`` to write; rerunning is safe.
"""

from __future__ import annotations

import argparse
import copy
import re
import shutil
import unicodedata
from pathlib import Path

import yaml

from learning_os.loader import FRONTMATTER_RE, load_repo, parse_frontmatter


ROOT = Path(__file__).resolve().parent.parent
TODAY = "2026-08-03"

PROGRAMS = [
    {
        "id": "program-bachelors", "type": "program", "title": "Bachelor’s",
        "kind": "academic", "status": "active", "default": True,
        "semester_bound": True,
        "description": "Current Bachelor’s execution and its semester history.",
        "semesters": [
            {"id": "semester-sose-2026", "title": "SoSe 2026",
             "status": "current", "order": 202601},
        ],
    },
    {
        "id": "program-skills", "type": "program", "title": "Skills",
        "kind": "skills", "status": "active", "default": False,
        "semester_bound": False,
        "description": "Long-running technical skills that are not semester-bound.",
        "semesters": [],
    },
    {
        "id": "program-thesis-projects", "type": "program",
        "title": "Thesis & projects", "kind": "projects", "status": "active",
        "default": False, "semester_bound": False,
        "description": "Bachelor thesis milestones and independently completable projects.",
        "semesters": [],
    },
    {
        "id": "program-masters-planning", "type": "program",
        "title": "Master’s Planning", "kind": "quarantine",
        "status": "quarantined", "default": False, "semester_bound": False,
        "description": "Prospective planning only; excluded from current work and default search.",
        "boundary_action": "Open Master’s Planning",
        "semesters": [],
    },
    {
        "id": "program-job-boundary", "type": "program", "title": "Job",
        "kind": "boundary", "status": "boundary-only", "default": False,
        "semester_bound": False,
        "description": "Hard confidentiality boundary. Job content never enters LearningOS.",
        "boundary_action": "Request explicit Job access",
        "semesters": [],
    },
]

MINI_PLANS = [
    ("module-hu-aml", "unit-aml-l02", None, 2, "AML Lecture 02 — k-Nearest Neighbors",
     "work/active/workspace-aml-exam-prep/inputs/AML_L02_Mini_Plan.md",
     "source-aml-ss26-lectures", "workspace-aml-exam-prep"),
    ("module-hu-aml", "unit-aml-l03", None, 3, "AML Lecture 03 — Linear Regression",
     "work/active/workspace-aml-exam-prep/inputs/AML_L03_Mini_Plan.md",
     "source-aml-ss26-lectures", "workspace-aml-exam-prep"),
    ("module-hu-aml", "unit-aml-l04", None, 4, "AML Lecture 04 — Non-linear Regression",
     "work/active/workspace-aml-exam-prep/inputs/AML_L04_Mini_Plan.md",
     "source-aml-ss26-lectures", "workspace-aml-exam-prep"),
    ("module-hu-aml", "unit-aml-l05", None, 5, "AML Lecture 05 — Logistic Regression",
     "work/active/workspace-aml-exam-prep/inputs/AML_L05_Mini_Plan.md",
     "source-aml-ss26-lectures", "workspace-aml-exam-prep"),
    ("module-hu-aml", "unit-aml-l06", None, 6, "AML Lecture 06 — Gradient Descent",
     "work/active/workspace-aml-exam-prep/inputs/AML_L06_Mini_Plan.md",
     "source-aml-ss26-lectures", "workspace-aml-exam-prep"),
    ("module-hu-aml", "unit-aml-l07", None, 7, "AML Lecture 07 — Linear Classifiers",
     "work/active/workspace-aml-exam-prep/inputs/AML_L07_Mini_Plan.md",
     "source-aml-ss26-lectures", "workspace-aml-exam-prep"),
    ("module-hu-m2-statistik-analysis", "unit-m2-sad-l01", "component-m2-sad", 1,
     "SaD Lecture 01 — Introduction",
     "work/active/workspace-m2-exam-prep/inputs/SaD_L01_Mini_Plan.md",
     "source-sad-ss26-lectures", "workspace-m2-exam-prep"),
    ("module-hu-m2-statistik-analysis", "unit-m2-sad-l02", "component-m2-sad", 2,
     "SaD Lecture 02 — Basic Concepts",
     "work/active/workspace-m2-exam-prep/inputs/SaD_L02_Mini_Plan.md",
     "source-sad-ss26-lectures", "workspace-m2-exam-prep"),
    ("module-hu-m2-statistik-analysis", "unit-m2-sad-l03", "component-m2-sad", 3,
     "SaD Lecture 03 — Correlation & Regression",
     "work/active/workspace-m2-exam-prep/inputs/SaD_L03_Mini_Plan.md",
     "source-sad-ss26-lectures", "workspace-m2-exam-prep"),
    ("module-hu-m2-statistik-analysis", "unit-m2-sad-l04", "component-m2-sad", 4,
     "SaD Lecture 04 — Probability & Naïve Bayes",
     "work/active/workspace-m2-exam-prep/inputs/SaD_L04_Mini_Plan.md",
     "source-sad-ss26-lectures", "workspace-m2-exam-prep"),
    ("module-hu-m2-statistik-analysis", "unit-m2-sad-l05", "component-m2-sad", 5,
     "SaD Lecture 05 — Combinatorics",
     "work/active/workspace-m2-exam-prep/inputs/SaD_L05_Mini_Plan.md",
     "source-sad-ss26-lectures", "workspace-m2-exam-prep"),
]

UNIT_SOURCE_SELECTIONS = {
    "unit-aml-l03": [
        {"source_id": "source-islp", "locator": "Chapter 3 §§3.1–3.3",
         "purpose": "Simple/multiple regression, fit assessment, and selected exercises"},
    ],
    "unit-aml-l04": [
        {"source_id": "source-islp",
         "locator": "§3.2; §7.1 only; §2.2.2; §§6.2.1–6.2.2",
         "purpose": "Multiple/polynomial regression, bias–variance, Ridge and Lasso; explicitly skip §§7.3–7.4 and §6.1"},
    ],
    "unit-m2-sad-l03": [
        {"source_id": "source-islp", "locator": "Chapter 3 via Regression Bridge §§2, 4 and 7",
         "purpose": "SaD-scoped regression bridge and wider post-exam depth"},
    ],
}

SOURCE_KEYWORDS = [
    ("3blue1brown", "source-3b1b-linear-algebra"),
    ("3b1b", "source-3b1b-linear-algebra"),
    ("islp", "source-islp"),
    ("cs229", "source-cs229-notes"),
    ("statquest", "source-statquest"),
    ("blitzstein", "source-blitzstein-hwang"),
    ("fahrmeir", "source-fahrmeir-statistik"),
    ("mml", "source-mml"),
    ("murphy", "source-murphy-pml1"),
    ("schaum", "source-schaums-probability"),
    ("openintro", "source-openintro-statistics"),
    ("kelleher", "source-kelleher-fmlpda"),
    ("kurzes tutorium", "source-kurzes-tutorium-statistik"),
    ("jbstatistics", "source-jbstatistics"),
]


def dump_yaml(data: dict) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100)


def slug(text: str) -> str:
    normal = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", normal.lower()).strip("-")[:48] or "stage"


def estimate_minutes(heading: str) -> int | None:
    match = re.search(r"~\s*([0-9]+(?:\.[0-9]+)?)\s*h", heading, re.I)
    if match:
        return max(1, round(float(match.group(1)) * 60))
    match = re.search(r"~\s*([0-9]+)\s*min", heading, re.I)
    return int(match.group(1)) if match else None


def source_for(line: str, source_ids: set[str]) -> str | None:
    folded = line.casefold()
    matches = [sid for key, sid in SOURCE_KEYWORDS if key in folded and sid in source_ids]
    return matches[0] if len(set(matches)) == 1 else None


def resource_from_line(line: str, source_ids: set[str]) -> dict:
    label = re.sub(r"^[-*]\s*|^\d+\.\s*", "", line).strip()
    folded = label.casefold()
    if "🎥" in label or "video" in folded or "playlist" in folded:
        kind = "watch"
    elif "📖" in label or any(k in folded for k in ("chapter", " ch ", "§")):
        kind = "read"
    elif "✍" in label or "exercise" in folded or "übung" in folded or "practice" in folded:
        kind = "practise"
    else:
        kind = "reference"
    resource = {"kind": kind, "label": label}
    sid = source_for(label, source_ids)
    if sid:
        resource["source_id"] = sid
    return resource


def parse_plan(root: Path, rel: str, unit_id: str, source_ids: set[str]) -> dict:
    path = root / rel
    text = path.read_text(encoding="utf-8")
    matches = list(re.finditer(r"^## Step\s+(\d+)\s+—\s+(.+)$", text, re.MULTILINE))
    stages = []
    for index, match in enumerate(matches):
        raw_heading = match.group(2).strip()
        title = re.sub(r"\s*\([^)]*(?:h|min)[^)]*\).*", "", raw_heading).strip()
        title = re.sub(r"\s*⭐.*", "", title).strip()
        body = text[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(text)]
        objective = next((p.strip() for p in re.split(r"\n\s*\n", body)
                          if p.strip() and not p.lstrip().startswith(("-", "#", "|"))),
                         f"Work through {title} within this unit's scope.")
        resource_lines = [line.strip() for line in body.splitlines()
                          if re.match(r"^(?:[-*]\s+|\d+\.\s+)", line.strip())]
        resources = [resource_from_line(line, source_ids) for line in resource_lines]
        stage_id = f"stage-{match.group(1).zfill(2)}-{slug(title)}"
        note_path = (f"curriculum/modules/{{module_id}}/units/{unit_id}/stages/"
                     f"{stage_id}/notes.md")
        stage = {
            "id": stage_id,
            "title": title,
            "status": "pending",
            "objective": objective,
            "done_when": [f"Explain and apply {title} without relying on the study map."],
            "exam_critical": "exam-critical" in raw_heading.casefold(),
            "scope_triage": "required-now",
            "resources": resources,
            "working_note": note_path,
            "attachments": [],
            "source_feedback": [],
        }
        estimate = estimate_minutes(raw_heading)
        if estimate:
            stage["estimate_minutes"] = estimate
        stages.append(stage)
    if not stages:
        stage_id = f"stage-01-{slug(unit_id.removeprefix('unit-'))}"
        stages = [{
            "id": stage_id, "title": "Work through the existing plan", "status": "pending",
            "objective": "Use the preserved source plan as the unit's scoped study script.",
            "done_when": ["Record the resulting work and evidence in this stage."],
            "scope_triage": "required-now", "resources": [],
            "working_note": (f"curriculum/modules/{{module_id}}/units/{unit_id}/stages/"
                             f"{stage_id}/notes.md"),
            "attachments": [], "source_feedback": [],
        }]
    return {
        "id": f"study-map-{unit_id.removeprefix('unit-')}",
        "type": "study-map", "unit_id": unit_id,
        "status": "ready", "current_stage": stages[0]["id"],
        "source_plan": {"path": rel, "provenance": "migrated-mini-plan"},
        "detours": [], "shelving": {"state": "none"}, "stages": stages,
    }


def artifact_ids(repo, prefix: str) -> dict:
    candidates = {
        "ultimate_reference": [prefix, prefix.replace("-l02", "-l02-knn-bias-variance"),
                               prefix.replace("-l03", "-l03-linear-regression"),
                               prefix.replace("-l04", "-l04-nonlinear-regression"),
                               prefix.replace("-l05", "-l05-logistic-regression"),
                               prefix.replace("-l06", "-l06-gradient-descent"),
                               prefix.replace("-l07", "-l07-linear-classifiers"),
                               prefix.replace("-l01", "-l01-introduction"),
                               prefix.replace("-l02", "-l02-descriptive-basics"),
                               prefix.replace("-l03", "-l03-correlation-regression"),
                               prefix.replace("-l04", "-l04-probability-bayes"),
                               prefix.replace("-l05", "-l05-combinatorics")],
        "exercise_bank": [f"{prefix}-exercise-bank"],
        "mock_exam": [f"{prefix}-mock-exam"],
    }
    found = {}
    for role, ids in candidates.items():
        for nid in ids:
            if nid in repo.notes:
                found[role] = nid
                break
    return found


def convert_l04(root: Path, module_id: str, unit_id: str) -> dict:
    old_path = root / "work/active/workspace-m2-exam-prep/paths/path-sad-l04-probability-bayes.yaml"
    old = yaml.safe_load(old_path.read_text(encoding="utf-8"))
    stages = []
    for old_stage in old["stages"]:
        stage = copy.deepcopy(old_stage)
        stage["resources"] = [
            {**resource, "kind": "practise" if resource.get("kind") == "practice"
             else resource.get("kind")}
            for resource in stage.get("resources", [])
        ]
        old_note = stage.pop("notes_path", None)
        stage["working_note"] = (
            f"curriculum/modules/{module_id}/units/{unit_id}/stages/{stage['id']}/notes.md")
        stage["attachments"] = []
        stage["source_feedback"] = []
        stage["scope_triage"] = "required-now"
        stage["_old_note"] = old_note
        stages.append(stage)
    return {
        "id": "study-map-m2-sad-l04-probability-bayes", "type": "study-map",
        "unit_id": unit_id, "status": old["status"],
        "current_stage": old["current_stage"],
        "source_plan": {"path": old["source_plan"], "provenance": "migrated-mini-plan"},
        "detours": [], "shelving": copy.deepcopy(old.get("shelving") or {"state": "none"}),
        "stages": stages,
    }


def note_backed_map(module_id: str, unit_id: str, title: str, note_id: str,
                    status: str = "ready", active: bool = False) -> dict:
    stage_id = f"stage-01-{slug(title)}"
    return {
        "id": f"study-map-{unit_id.removeprefix('unit-')}", "type": "study-map",
        "unit_id": unit_id, "status": "active" if active else status,
        "current_stage": stage_id,
        "source_plan": {"path": f"note://{note_id}", "provenance": "durable-note"},
        "detours": [], "shelving": {"state": "none"},
        "stages": [{
            "id": stage_id, "title": title, "status": "active" if active else "pending",
            "objective": f"Use the preserved {title} artifact as the scope and work record.",
            "done_when": ["Record concrete work or evidence without inferring mastery from the artifact."],
            "scope_triage": "required-now",
            "resources": [{"kind": "reference",
                           "label": f"Durable artifact {note_id}: {title}"}],
            "working_note": (f"curriculum/modules/{module_id}/units/{unit_id}/stages/"
                             f"{stage_id}/notes.md"),
            "attachments": [], "source_feedback": [],
        }],
    }


def make_unit(module_id: str, unit_id: str, kind: str, title: str, order: int,
              scope: str, status: str, workspace_ids: list[str], artifacts: dict | None = None,
              component_id: str | None = None, study_map: dict | None = None,
              scope_source: str | None = None, related: list[str] | None = None,
              source_selections: list[dict] | None = None) -> tuple[dict, dict | None]:
    unit = {
        "id": unit_id, "type": "unit", "module_id": module_id, "kind": kind,
        "title": title, "order": order, "scope": scope, "status": status,
        "scope_sources": ([{"source_id": scope_source, "authority": "slides"}]
                          if scope_source else []),
        "source_selections": source_selections or [],
        "artifacts": artifacts or {}, "workspace_ids": workspace_ids,
    }
    if component_id:
        unit["component_id"] = component_id
    if study_map:
        unit["current_study_map"] = study_map["id"]
    if related:
        unit["related_module_ids"] = related
    return unit, study_map


def source_maps(source_ids: set[str]) -> dict[str, list[dict]]:
    raw = {
        "module-hu-aml": [
            ("source-aml-ss26-lectures", "course-material", "Slides define lecture scope.", 0),
            ("source-islp", "spine", "Primary statistical-learning reading spine.", 1),
            ("source-cs229-notes", "derivation", "Derivations and probabilistic justification.", 2),
            ("source-statquest", "intuition", "Short intuitive refreshers.", 3),
        ],
        "module-hu-m2-statistik-analysis": [
            ("source-sad-ss26-lectures", "course-material", "SaD slides define lecture scope.", 0),
            ("source-sad-uebungen", "practice", "Course-aligned exercise sheets.", 1),
            ("source-blitzstein-hwang", "spine", "Probability explanations and derivations.", 2),
            ("source-fahrmeir-statistik", "reference", "German notation aligned with the exam.", 3),
            ("source-islp", "optional-depth", "Regression and ML bridge material.", 4),
        ],
        "module-skill-python": [
            ("source-python-depth-drills", "spine", "Authored staged depth ladder.", 0),
            ("source-fluent-python", "optional-depth", "Language-model depth and idioms.", 2),
            ("source-python-docs-classes-mro", "reference", "Official class and MRO reference.", 1),
        ],
    }
    maps = {
        mid: [{"source_id": sid, "role": role, "why": why, "priority": priority,
               "unit_routes": []}
              for sid, role, why, priority in entries if sid in source_ids]
        for mid, entries in raw.items()
    }
    routes = {
        ("module-hu-aml", "source-aml-ss26-lectures"): [f"unit-aml-l0{i}" for i in range(2, 8)],
        ("module-hu-aml", "source-islp"): ["unit-aml-l02", "unit-aml-l03", "unit-aml-l04"],
        ("module-hu-aml", "source-cs229-notes"): ["unit-aml-l03", "unit-aml-l05"],
        ("module-hu-m2-statistik-analysis", "source-sad-ss26-lectures"):
            [*[f"unit-m2-sad-l0{i}" for i in range(1, 6)], "unit-m2-sad-l06-l10"],
        ("module-hu-m2-statistik-analysis", "source-sad-uebungen"):
            [f"unit-m2-sad-l0{i}" for i in range(1, 6)],
        ("module-hu-m2-statistik-analysis", "source-islp"): ["unit-m2-sad-l03"],
    }
    for mid, entries in maps.items():
        for entry in entries:
            entry["unit_routes"] = routes.get((mid, entry["source_id"]), [])
    return maps


class Migration:
    def __init__(self, root: Path, apply: bool):
        self.root = root
        self.apply = apply
        self.actions: list[str] = []
        self.mappings: list[dict] = []

    def write(self, rel: str, content: str) -> None:
        path = self.root / rel
        current = path.read_text(encoding="utf-8") if path.is_file() else None
        if current == content:
            return
        self.actions.append(f"write {rel}")
        if self.apply:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

    def move(self, old: str, new: str) -> None:
        src, dst = self.root / old, self.root / new
        mapping = {"old": old, "new": new, "kind": "move"}
        if mapping not in self.mappings:
            self.mappings.append(mapping)
        if not src.exists() and dst.exists():
            return
        if not src.exists():
            raise SystemExit(f"migration: missing move source: {old}")
        if dst.exists():
            raise SystemExit(f"migration: move target already exists: {new}")
        self.actions.append(f"move {old} -> {new}")
        if self.apply:
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)

    def update_workspace(self, wid: str, refs: dict) -> None:
        path = self.root / "work" / "active" / wid / "CONTEXT.md"
        meta, body = parse_frontmatter(path.read_text(encoding="utf-8"), path)
        changed = False
        for key, value in refs.items():
            if meta.get(key) != value:
                meta[key] = value
                changed = True
        if changed:
            self.write(str(path.relative_to(self.root)),
                       "---\n" + dump_yaml(meta).rstrip() + "\n---\n\n" + body.lstrip("\n"))


def run(root: Path, apply: bool) -> Migration:
    migration = Migration(root, apply)
    before = load_repo(root)
    source_ids = set(before.sources)
    source_map_defs = source_maps(source_ids)

    for program in PROGRAMS:
        migration.write(f"curriculum/programs/{program['id']}.yaml", dump_yaml(program))

    modules: dict[str, dict] = {}
    units_by_module: dict[str, list[tuple[dict, dict | None]]] = {}
    for mid, legacy in before.legacy_modules.items():
        module = copy.deepcopy(legacy)
        module.update({"type": "module", "kind": "academic",
                       "area_id": "program-bachelors", "source_map": "source-map.yaml"})
        if mid == "module-hu-m2-statistik-analysis":
            module["components"] = [
                {"id": "component-m2-sad", "title": "Statistik und Datenanalyse",
                 "short_title": "SaD", "order": 1},
                {"id": "component-m2-analysis", "title": "Analysis",
                 "short_title": "Analysis", "order": 2},
            ]
        else:
            module.pop("components", None)
        modules[mid] = module

    for mid, uid, component, order, title, plan, scope_source, wid in MINI_PLANS:
        if uid == "unit-m2-sad-l04":
            study_map = convert_l04(root, mid, uid)
        else:
            study_map = parse_plan(root, plan, uid, source_ids)
            for stage in study_map["stages"]:
                stage["working_note"] = stage["working_note"].format(module_id=mid)
        prefix = "note-" + uid.removeprefix("unit-").replace("m2-", "")
        artifacts = artifact_ids(before, prefix)
        unit, study_map = make_unit(
            mid, uid, "lecture", title, order,
            f"The lecture as taught; the preserved Mini Plan is the single study script.",
            "active" if uid == "unit-m2-sad-l04" else "ready", [wid], artifacts,
            component_id=component, study_map=study_map, scope_source=scope_source,
            source_selections=[row for row in UNIT_SOURCE_SELECTIONS.get(uid, [])
                               if row["source_id"] in source_ids])
        units_by_module.setdefault(mid, []).append((unit, study_map))
        migration.mappings.append({"old": plan,
                                   "new": f"curriculum/modules/{mid}/units/{uid}/study-map.yaml",
                                   "kind": "retained-source-plan"})

    deep_map = note_backed_map("module-hu-m2-statistik-analysis", "unit-m2-sad-l06-l10",
                               "SaD L06–L10 probability and inference deep plan",
                               "note-sad-probability-inference-deep-plan")
    deep_unit = make_unit(
        "module-hu-m2-statistik-analysis", "unit-m2-sad-l06-l10", "lecture-cluster",
        "SaD L06–L10 — Probability & inference core", 6,
        "Intentionally clustered probability and inference sequence; do not split without scope evidence.",
        "ready", ["workspace-m2-exam-prep"],
        {"ultimate_reference": "note-sad-probability-inference-deep-plan"},
        component_id="component-m2-sad", study_map=deep_map,
        scope_source="source-sad-ss26-lectures")
    units_by_module.setdefault("module-hu-m2-statistik-analysis", []).append(deep_unit)
    units_by_module["module-hu-m2-statistik-analysis"].append(make_unit(
        "module-hu-m2-statistik-analysis", "unit-m2-analysis-exam-prep", "exam-block",
        "Analysis — exam preparation block", 100,
        "Analysis component preparation; a study map must be built from the component's taught scope.",
        "needs-map", ["workspace-m2-exam-prep"], component_id="component-m2-analysis"))

    amls_map = parse_plan(root, "work/active/workspace-amls-exam-prep/inputs/Chat2_AMLS_Theory_Plan.md",
                          "unit-amls-theory", source_ids)
    for stage in amls_map["stages"]:
        stage["working_note"] = stage["working_note"].format(module_id="module-hu-amls")
    units_by_module["module-hu-amls"] = [make_unit(
        "module-hu-amls", "unit-amls-theory", "exam-block", "AMLS theory preparation", 1,
        "Existing AMLS theory plan, retained as the unit's source plan.", "ready",
        ["workspace-amls-exam-prep"], study_map=amls_map)]

    algo_map = parse_plan(root, "work/active/workspace-algo2-exam-prep/inputs/Chat9_Algo2_Plan.md",
                          "unit-algo2-exam-prep", source_ids)
    for stage in algo_map["stages"]:
        stage["working_note"] = stage["working_note"].format(module_id="module-hu-algo2")
    units_by_module["module-hu-algo2"] = [make_unit(
        "module-hu-algo2", "unit-algo2-exam-prep", "exam-block", "Algo 2 oral exam preparation", 1,
        "Existing Algo 2 plan, retained as the unit's source plan.", "ready",
        ["workspace-algo2-exam-prep"], study_map=algo_map)]
    units_by_module["module-hu-ppds"] = [make_unit(
        "module-hu-ppds", "unit-ppds-mlprov-submission", "milestone", "mlprov project submission", 1,
        "Submitted mlprov project milestone; no mastery or completion is inferred from submission.",
        "paused", [])]
    units_by_module["module-hu-seminar-iug"] = [make_unit(
        "module-hu-seminar-iug", "unit-seminar-iug-portfolio", "exam-block",
        "Seminar portfolio and pending grade", 1,
        "Existing portfolio deliverables and administrative follow-up.", "paused", [])]

    modules["module-skill-python"] = {
        "id": "module-skill-python", "type": "module", "kind": "skill",
        "area_id": "program-skills", "title": "Python", "status": "active",
        "source_map": "source-map.yaml", "unit_order": [],
    }
    python_units = [
        ("unit-python-depth-drills", "Python depth drills", "note-python-depth-drills"),
        ("unit-python-intermediate-roadmap", "Python intermediate roadmap", "note-python-intermediate-roadmap"),
        ("unit-python-oop-scope", "Python OOP & scope repair", "note-python-oop-scope-repair-plan"),
    ]
    units_by_module["module-skill-python"] = []
    for order, (uid, title, note_id) in enumerate(python_units, 1):
        smap = note_backed_map("module-skill-python", uid, title, note_id)
        units_by_module["module-skill-python"].append(make_unit(
            "module-skill-python", uid, "topic", title, order,
            "Seeded from the existing roadmap without inferring completion.", "ready", [],
            {"ultimate_reference": note_id}, study_map=smap))

    modules["module-project-bachelor-thesis"] = {
        "id": "module-project-bachelor-thesis", "type": "module", "kind": "project",
        "area_id": "program-thesis-projects", "title": "Bachelor thesis", "status": "active",
        "source_map": "source-map.yaml", "unit_order": [],
    }
    thesis_stage = "stage-01-research-landscape-and-question-framing"
    thesis_map = {
        "id": "study-map-thesis-landscape", "type": "study-map",
        "unit_id": "unit-thesis-landscape", "status": "active",
        "current_stage": thesis_stage,
        "source_plan": {
            "path": "work/active/workspace-thesis-mle-medical/outputs/thesis-landscape-and-plan.md",
            "provenance": "operator",
        },
        "detours": [], "shelving": {"state": "none"},
        "stages": [{
            "id": thesis_stage, "title": "Research landscape and question framing",
            "status": "active",
            "objective": "Use the existing thesis landscape and brief to frame the next milestone.",
            "done_when": ["Record the concrete next research decision without inferring completion from the plan."],
            "scope_triage": "required-now",
            "resources": [{
                "kind": "reference", "label": "Existing thesis landscape and plan",
                "vault_path": "work/active/workspace-thesis-mle-medical/outputs/thesis-landscape-and-plan.md",
            }],
            "working_note": ("curriculum/modules/module-project-bachelor-thesis/units/"
                             "unit-thesis-landscape/stages/" + thesis_stage + "/notes.md"),
            "attachments": [], "source_feedback": [],
        }],
    }
    units_by_module["module-project-bachelor-thesis"] = [
        make_unit("module-project-bachelor-thesis", "unit-thesis-landscape", "milestone",
                  "Research landscape & question framing", 1,
                  "Landscape and planning milestone grounded in the active thesis workspace.",
                  "active", ["workspace-thesis-mle-medical"], study_map=thesis_map),
        make_unit("module-project-bachelor-thesis", "unit-thesis-experiments", "milestone",
                  "Experiment design & evaluation", 2,
                  "A later thesis milestone; scope is intentionally not invented.",
                  "needs-map", ["workspace-thesis-mle-medical"]),
    ]

    modules["module-foundation-ml-math-bridges"] = {
        "id": "module-foundation-ml-math-bridges", "type": "module", "kind": "foundation",
        "area_id": "program-skills", "title": "ML & mathematics bridges", "status": "active",
        "source_map": "source-map.yaml", "unit_order": [],
        "related_module_ids": ["module-hu-aml", "module-hu-m2-statistik-analysis"],
    }
    units_by_module["module-foundation-ml-math-bridges"] = [
        make_unit("module-foundation-ml-math-bridges", "unit-bridge-regression-sad-aml",
                  "bridge", "Regression — SaD × AML × ISLP", 1,
                  "Cross-module regression bridge with one primary owner and explicit related modules.",
                  "ready", ["workspace-aml-exam-prep", "workspace-m2-exam-prep"],
                  {"ultimate_reference": "note-regression-sad-aml-islp-bridge"},
                  related=["module-hu-aml", "module-hu-m2-statistik-analysis"]),
        make_unit("module-foundation-ml-math-bridges", "unit-bridge-aml-sad-master-wiring",
                  "bridge", "AML × SaD master wiring", 2,
                  "Cross-module concept and source wiring retained as a durable artifact.",
                  "ready", ["workspace-aml-exam-prep", "workspace-m2-exam-prep"],
                  {"ultimate_reference": "note-aml-sad-master-wiring"},
                  related=["module-hu-aml", "module-hu-m2-statistik-analysis"]),
    ]

    for mid, module in sorted(modules.items()):
        pairs = units_by_module.get(mid, [])
        pairs.sort(key=lambda pair: (pair[0]["order"], pair[0]["id"]))
        module["unit_order"] = [unit["id"] for unit, _ in pairs]
        migration.write(f"curriculum/modules/{mid}/module.yaml", dump_yaml(module))
        migration.write(f"curriculum/modules/{mid}/source-map.yaml", dump_yaml({
            "type": "module-source-map", "module_id": mid,
            "sources": source_map_defs.get(mid, []),
        }))
        for unit, study_map in pairs:
            base = f"curriculum/modules/{mid}/units/{unit['id']}"
            migration.write(f"{base}/unit.yaml", dump_yaml(unit))
            if study_map:
                clean_map = copy.deepcopy(study_map)
                for stage in clean_map["stages"]:
                    old_note = stage.pop("_old_note", None)
                    note_text = ""
                    if old_note and (root / old_note).is_file():
                        note_text = (root / old_note).read_text(encoding="utf-8")
                    migration.write(stage["working_note"], note_text)
                migration.write(f"{base}/study-map.yaml", dump_yaml(clean_map))

    migration.write("curriculum/resume.yaml", dump_yaml({
        "type": "resume-pointer", "module_id": "module-hu-m2-statistik-analysis",
        "unit_id": "unit-m2-sad-l04", "study_map_id": "study-map-m2-sad-l04-probability-bayes",
        "stage_id": "stage-event-spaces", "updated": TODAY,
    }))
    migration.write("curriculum/quarantine/index.yaml", dump_yaml({
        "type": "quarantine-index", "id": "quarantine-masters-planning",
        "workspace_ids": ["workspace-degree-planning"],
        "boundary_program_id": "program-masters-planning",
    }))

    migration.update_workspace("workspace-aml-exam-prep", {
        "program_ids": ["program-bachelors"], "module_ids": ["module-hu-aml"],
        "unit_ids": [f"unit-aml-l0{i}" for i in range(2, 8)],
    })
    migration.update_workspace("workspace-m2-exam-prep", {
        "program_ids": ["program-bachelors"], "module_ids": ["module-hu-m2-statistik-analysis"],
        "unit_ids": [*[f"unit-m2-sad-l0{i}" for i in range(1, 6)],
                     "unit-m2-sad-l06-l10", "unit-m2-analysis-exam-prep"],
    })
    migration.update_workspace("workspace-amls-exam-prep", {
        "program_ids": ["program-bachelors"], "module_ids": ["module-hu-amls"],
        "unit_ids": ["unit-amls-theory"],
    })
    migration.update_workspace("workspace-algo2-exam-prep", {
        "program_ids": ["program-bachelors"], "module_ids": ["module-hu-algo2"],
        "unit_ids": ["unit-algo2-exam-prep"],
    })
    migration.update_workspace("workspace-thesis-mle-medical", {
        "program_ids": ["program-thesis-projects"],
        "module_ids": ["module-project-bachelor-thesis"],
        "unit_ids": ["unit-thesis-landscape", "unit-thesis-experiments"],
    })

    migration.move("work/active/workspace-degree-planning",
                   "curriculum/quarantine/masters-planning/workspaces/workspace-degree-planning")
    migration.move("sources/collections/degree-module-anchors.yaml",
                   "curriculum/quarantine/masters-planning/sources/degree-module-anchors.yaml")

    if apply:
        original = root / "records/modules.yaml"
        backup = root / "migration/curriculum-v2/originals/records-modules.yaml"
        if not backup.exists():
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(original, backup)
            migration.actions.append("copy records/modules.yaml -> migration/curriculum-v2/originals/records-modules.yaml")
    elif not (root / "migration/curriculum-v2/originals/records-modules.yaml").exists():
        migration.actions.append("copy records/modules.yaml -> migration/curriculum-v2/originals/records-modules.yaml")

    mappings = {
        "migration": "curriculum-v2", "date": TODAY,
        "notes": "Original Mini Plans remain in place; quarantined material is moved intact.",
        "mappings": migration.mappings,
    }
    migration.write("migration/curriculum-v2/old-to-new.yaml", dump_yaml(mappings))
    report = [
        "# Curriculum v2 migration report", "",
        "> Mechanical, idempotent migration. No durable note body, source ID, concept ID, or relation ID was changed.", "",
        f"- Programs/boundaries: {len(PROGRAMS)}",
        f"- Modules: {len(modules)} ({len(before.legacy_modules)} academic + {len(modules) - len(before.legacy_modules)} universal)",
        f"- Units: {sum(len(v) for v in units_by_module.values())}",
        f"- Mini Plans converted: {len(MINI_PLANS)}",
        "- SaD L04 resume state: `stage-event-spaces` active (copied exactly)",
        "- Master’s Planning: tracked quarantine; boundary-only in the manifest",
        "- Job: never read or migrated", "",
        "## Rollback", "",
        "Switch back to `codex/learning-path-app-v1`, or revert this branch's migration commits. The original module registry is also preserved under `migration/curriculum-v2/originals/`.", "",
    ]
    migration.write("migration/curriculum-v2/report.md", "\n".join(report))
    return migration


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--apply", action="store_true", help="write the migration (default: dry-run)")
    parser.add_argument("--report", action="store_true", help="print all planned/applied actions")
    args = parser.parse_args()
    migration = run(Path(args.root).resolve(), args.apply)
    mode = "applied" if args.apply else "dry-run"
    print(f"curriculum-v2 migration {mode}: {len(migration.actions)} action(s)")
    if args.report:
        for action in migration.actions:
            print(f"- {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build the reviewed Polars/pandas session migration package.

The current 18-stage map is treated as source evidence.  The builder preserves
its resources, moves its stages into session-sized units, enriches every
resource with a learner-facing angle, and adds the missing Polars/Stratum labs.
It writes only review artifacts; the canonical write still goes through
``los module-plan-import``.
"""

from __future__ import annotations

import copy
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
MODULE_ID = "module-job-polars"
OLD_UNIT_ID = "unit-job-polars-pandas-fluency"
OLD_MAP_PATH = (
    ROOT
    / "curriculum/modules/module-job-polars/units/"
    "unit-job-polars-pandas-fluency/study-map.yaml"
)
PACKAGE_REL = (
    "work/active/workspace-job-polars-plan/outputs/"
    "polars-backend-session-migration.yaml"
)
AUDIT_REL = (
    "work/active/workspace-job-polars-plan/outputs/"
    "polars-backend-material-coverage-audit.md"
)
SUMMARY_REL = (
    "work/active/workspace-job-polars-plan/outputs/"
    "polars-backend-session-plan.md"
)


class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):  # noqa: ANN001
        return True


def dump_yaml(data: dict) -> str:
    return yaml.dump(
        data,
        Dumper=NoAliasDumper,
        sort_keys=False,
        allow_unicode=True,
        width=100,
    )


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def resource(
    resource_id: str,
    kind: str,
    label: str,
    locator: str,
    angle: str,
    angle_detail: str,
    *,
    scope: str = "required-now",
    url: str | None = None,
    vault_path: str | None = None,
    source_id: str | None = None,
    route_id: str | None = None,
) -> dict:
    row = {
        "id": resource_id,
        "kind": kind,
        "label": label,
        "locator": locator,
        "angle": angle,
        "angle_detail": angle_detail,
        "scope_triage": scope,
    }
    if url:
        row["url"] = url
    if vault_path:
        row["vault_path"] = vault_path
    if source_id:
        row["source_id"] = source_id
    if route_id:
        row["route_id"] = route_id
    return row


def practice(resource_id: str, label: str, exercise: str, evidence: str) -> dict:
    return resource(
        resource_id,
        "practise",
        label,
        exercise,
        "Produces executable evidence instead of familiarity from reading.",
        evidence,
    )


def official(
    resource_id: str,
    label: str,
    locator: str,
    url: str,
    angle: str,
    detail: str,
    *,
    scope: str = "required-now",
) -> dict:
    return resource(
        resource_id,
        "read" if scope != "reference-only" else "reference",
        label,
        locator,
        angle,
        detail
        + " The live page may describe a newer release, so execute each claim against Polars 1.36.0 "
        "or pandas 3.0.2 before treating it as backend policy.",
        scope=scope,
        url=url,
    )


def note_resource(
    resource_id: str,
    label: str,
    path: str,
    locator: str,
    angle: str,
    detail: str,
    *,
    scope: str = "required-now",
) -> dict:
    return resource(
        resource_id,
        "read" if scope != "reference-only" else "reference",
        label,
        locator,
        angle,
        detail,
        scope=scope,
        vault_path=path,
    )


def enrich_resource(row: dict, stage_title: str) -> dict:
    """Give every inherited resource a stage-specific, candid angle."""
    row = copy.deepcopy(row)
    label = str(row.get("label", "this resource"))
    locator = str(row.get("locator", "the named item"))
    source_id = row.get("source_id")
    url = str(row.get("url", ""))
    kind = row.get("kind")

    if source_id == "source-polars-definitive-guide":
        angle = "Polars-first explanation and worked examples for this stage."
        detail = (
            f"Use {locator} to build the native Polars model for {stage_title}; the book is an early-release "
            "edition, so confirm callable names and defaults against the pinned 1.36.0 environment."
        )
    elif source_id == "source-pydata-handbook":
        angle = "Historical pandas examples to turn into an explicit compatibility contract."
        detail = (
            f"Use {locator} to identify pandas behavior relevant to {stage_title}. The notebook predates "
            "pandas 3.0.2, so it generates test questions rather than serving as semantic authority."
        )
    elif source_id == "source-python-cheatsheets":
        angle = "Fast pandas API recall, not current semantic authority."
        detail = (
            f"Use the two-page 2017 sheet at {locator} to discover operations for {stage_title}; verify dtype, "
            "null, order, index, and failure behavior with pandas 3.0.2 fixtures."
        )
    elif source_id == "source-python-depth-drills":
        angle = "Python testing or dispatch mechanics that support backend implementation."
        detail = (
            f"Use only {locator} for the Python mechanism needed by {stage_title}. It strengthens implementation "
            "judgment but does not define dataframe semantics."
        )
    elif kind == "practise":
        angle = "Active retrieval and implementation evidence for this stage."
        detail = (
            f"Complete {locator} before consulting an answer. Record values, dtype/schema, cardinality, row order, "
            "missing-value behavior, warnings, and exceptions separately whenever they apply."
        )
    elif "docs.pola.rs" in url:
        angle = "Official Polars reference for the native operation."
        detail = (
            f"Read {locator} for {stage_title}, then run the example under Polars 1.36.0 because the live "
            "documentation can move ahead of Stratum's lockfile."
        )
    elif "pandas.pydata.org" in url:
        angle = "Official pandas reference for the observable oracle contract."
        detail = (
            f"Read {locator} for {stage_title} and encode the promised behavior in pandas 3.0.2 fixtures; "
            "unspecified behavior remains evidence, not a universal contract."
        )
    else:
        angle = "Supporting explanation or reference for this stage's implementation decision."
        detail = (
            f"Use {label} at {locator} only for {stage_title}; validate any library behavior in the pinned "
            "environment before it enters the parity policy."
        )
    row.setdefault("angle", angle)
    row.setdefault("angle_detail", detail)
    return row


TEXT_REPLACEMENTS = {
    "Session 2 schema task": "Session 4 schema task",
    "Session 3 filtering task": "Session 3 selection task",
    "Session 4 expression task": "Session 2 expression task",
    "Session 7 aggregation task": "Session 6 aggregation task",
    "Stage 9's corpus": "Session 7's join corpus",
    "Stage 9 semantic predictions": "Session 7 join-semantic predictions",
    "produced in Stage 9": "produced in Session 7",
    "Session 10 join lab": "Session 7 join lab",
    "Stage 1 model, Stage 15 parity rules": "Session 1 contract model, Session 8 lazy-plan rules",
}


def fix_text(value):  # noqa: ANN001
    if isinstance(value, str):
        for old, new in TEXT_REPLACEMENTS.items():
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [fix_text(item) for item in value]
    if isinstance(value, dict):
        return {key: fix_text(item) for key, item in value.items()}
    return value


def new_stage(
    stage_id: str,
    title: str,
    objective: str,
    done_when: list[str],
    concepts: list[str],
    resources: list[dict],
) -> dict:
    return {
        "id": stage_id,
        "number": 0,
        "title": title,
        "status": "pending",
        "objective": objective,
        "done_when": done_when,
        "exam_critical": False,
        "concepts": unique(["concept-python", *concepts]),
        "scope_triage": "required-now",
        "resources": resources,
        "working_note": "",
        "attachments": [],
        "source_feedback": [],
    }


def migrated_stage(old: dict, unit_id: str, concepts: list[str], title: str | None = None) -> dict:
    row = fix_text(copy.deepcopy(old))
    row.pop("estimate_minutes", None)
    row["status"] = "pending"
    if title:
        row["title"] = title
    row["concepts"] = unique(["concept-python", *concepts])
    row["resources"] = [enrich_resource(item, row["title"]) for item in row.get("resources", [])]
    if unit_id != OLD_UNIT_ID:
        legacy_note = row["working_note"]
        row["working_note"] = (
            f"curriculum/modules/{MODULE_ID}/units/{unit_id}/stages/{row['id']}/notes.md"
        )
        row["resources"].append(
            note_resource(
                f"resource-{row['id'][6:]}-migrated-guide",
                "Migrated authored stage guide",
                legacy_note,
                "Complete guide retained from the original monolithic plan",
                "Preserves the deeper mental model and traps written for the original stage.",
                "Read after the stage objective and before the closed-book drill. The guide remains at its "
                "original path as migration evidence while this session owns the active stage.",
                scope="helpful-now",
            )
        )
    return row


def material_book(
    resource_id: str,
    route_id: str,
    locator: str,
    angle: str,
    detail: str,
    *,
    scope: str = "required-now",
) -> dict:
    return resource(
        resource_id,
        "read",
        "Python Polars: The Definitive Guide",
        locator,
        angle,
        detail,
        scope=scope,
        source_id="source-polars-definitive-guide",
        route_id=route_id,
        vault_path=(
            "material://source-polars-definitive-guide/"
            "python-polars-the-definitive-guide.pdf"
        ),
    )


def build() -> tuple[dict, str, str]:
    old_map = yaml.safe_load(OLD_MAP_PATH.read_text(encoding="utf-8"))
    old = old_map["stages"]

    sessions: list[dict] = []

    def add_session(
        unit_id: str,
        title: str,
        scope: str,
        knowledge: list[tuple[str, str, str]],
        stages: list[dict],
        concepts: list[str],
    ) -> None:
        for number, stage in enumerate(stages, start=1):
            stage["number"] = number
            if not stage["working_note"]:
                stage["working_note"] = (
                    f"curriculum/modules/{MODULE_ID}/units/{unit_id}/stages/{stage['id']}/notes.md"
                )
            stage["resources"] = [enrich_resource(r, stage["title"]) for r in stage["resources"]]

        nodes = []
        for index, (node_id, node_title, summary) in enumerate(knowledge):
            node = {
                "id": node_id,
                "title": node_title,
                "summary": summary,
                "concept_ids": concepts,
            }
            if index:
                node["builds_on"] = [knowledge[index - 1][0]]
            nodes.append(node)

        used_sources = unique(
            [
                r["source_id"]
                for stage in stages
                for r in stage.get("resources", [])
                if r.get("source_id")
            ]
        )
        unit = {
            "id": unit_id,
            "type": "unit",
            "module_id": MODULE_ID,
            "kind": "topic",
            "title": title,
            "order": len(sessions) + 1,
            "scope": scope,
            "status": "ready",
            "knowledge_map": {
                "summary": scope,
                "nodes": nodes,
            },
            "scope_sources": [
                {"source_id": source_id, "authority": "reference"}
                for source_id in used_sources
            ],
            "source_selections": [],
            "current_study_map": (
                "study-map-job-polars-pandas-fluency"
                if unit_id == OLD_UNIT_ID
                else f"study-map-{unit_id[5:]}"
            ),
            "artifacts": {},
            "workspace_ids": [],
        }
        if unit_id == OLD_UNIT_ID:
            unit["working_note"] = (
                "curriculum/modules/module-job-polars/units/"
                "unit-job-polars-pandas-fluency/notes.md"
            )
        study_map = {
            "id": unit["current_study_map"],
            "type": "study-map",
            "plan_template_version": 1,
            "unit_id": unit_id,
            "status": "ready",
            "current_stage": stages[0]["id"],
            "source_plan": {"path": PACKAGE_REL, "provenance": "operator"},
            "detours": [],
            "stages": stages,
            "shelving": {"state": "none"},
        }
        sessions.append({"unit": unit, "study_map": study_map})

    # Session 1 keeps the existing unit and its two authored note paths.  That
    # makes the migration visible without deleting learner-facing evidence.
    s1a = migrated_stage(
        old[0],
        OLD_UNIT_ID,
        ["concept-dataframe-semantics", "concept-logical-ir"],
        "Backend contract, version lock, and divergence axes",
    )
    s1a["objective"] = (
        "Freeze pandas 3.0.2 and Polars 1.36.0 as the executable study environment, then use the "
        "eight divergence axes to specify operation behavior before translating any API."
    )
    s1a["done_when"][-1] = (
        "After Stage 2 creates the harness, backfill every divergence found here as a named executable case."
    )
    s1a["resources"].insert(
        0,
        practice(
            "resource-polars-version-lock",
            "Freeze the Stratum backend environment",
            "Exercise 0 - record pandas==3.0.2 from pyproject.toml and pandas 3.0.2 / Polars 1.36.0 from uv.lock",
            "The output is a small manifest plus one probe printing both runtime versions; a mismatch blocks "
            "semantic conclusions until resolved.",
        ),
    )
    s1b = migrated_stage(
        old[1],
        OLD_UNIT_ID,
        ["concept-dataframe-semantics", "concept-dispatch"],
        "Build the cumulative differential parity harness",
    )
    s1b["resources"].extend(
        [
            official(
                "resource-polars-testing-parametric",
                "Polars testing and parametric strategies",
                "Asserts; Parametric testing; dataframes strategy; profiles",
                "https://docs.pola.rs/api/python/stable/reference/testing.html",
                "Provides native equality assertions and generated dataframe cases.",
                "Use generated mixed dtypes, nulls, empty frames, duplicate keys, and boundary sizes; keep "
                "value, schema, order, exception, and warning comparisons as separate properties.",
            ),
            official(
                "resource-pandas-testing-frame-equal",
                "pandas.testing.assert_frame_equal",
                "Parameters controlling dtype, index, names, exactness, tolerances, and ordering",
                "https://pandas.pydata.org/docs/reference/api/pandas.testing.assert_frame_equal.html",
                "Defines the knobs that make normalization policy explicit rather than accidental.",
                "Create operation-specific comparison profiles; never use one blanket normalization policy.",
                scope="reference-only",
            ),
        ]
    )
    add_session(
        OLD_UNIT_ID,
        "Session 1 - Backend contracts and parity harness",
        "Specify observable pandas behavior at the operation boundary, target Polars 1.36.0, and create the "
        "cumulative executable harness used by every later session.",
        [
            (
                "knowledge-polars-version-contract",
                "Pinned backend contract",
                "Separate version facts, documented guarantees, executable observations, and Stratum policy.",
            ),
            (
                "knowledge-polars-divergence-axes",
                "Eight divergence axes",
                "Classify index, missingness, dtype, ordering, shape, context, key-cardinality, and failure differences.",
            ),
            (
                "knowledge-polars-parity-harness",
                "Differential parity harness",
                "Record comparable values, schemas, order, exceptions, warnings, and justified normalization.",
            ),
        ],
        [s1a, s1b],
        ["concept-dataframe-semantics", "concept-logical-ir", "concept-dispatch"],
    )

    s2a = migrated_stage(
        old[4],
        "unit-job-polars-expressions",
        ["concept-map-family", "concept-projection-family"],
        "Expression grammar, contexts, aliases, and sibling visibility",
    )
    s2a["objective"] = (
        "Make Polars expressions the default implementation language: construct reusable Expr trees, predict "
        "their schema and cardinality in select/with_columns/filter/group_by, and avoid pandas-style sequential "
        "assignment assumptions."
    )
    s2a["resources"].insert(
        0,
        material_book(
            "resource-polars-book-expressions",
            "route-polars-definitive-guide-s02",
            "Chapter 7 'Beginning Expressions', PDF viewer pages 178-207; Chapter 8, pages 208-253",
            "The local book's deepest continuous explanation of Expr construction and reuse.",
            "Work the examples in all four contexts and predict name, dtype, and cardinality before execution.",
        ),
    )
    s2b = new_stage(
        "stage-polars-expr-selectors-expansion",
        "Selectors and expression expansion",
        "Select columns by name and dtype without materializing schema-specific Python lists, and predict the "
        "expanded output columns before execution.",
        [
            "Implement select_dtypes-like inclusion/exclusion using polars.selectors and set operations.",
            "Use cs.expand_selector against three schemas and explain every expanded column.",
            "A schema-change test passes without editing the expression.",
        ],
        ["concept-map-family", "concept-projection-family"],
        [
            material_book(
                "resource-polars-book-selectors",
                "route-polars-definitive-guide-s02",
                "Chapter 10 'Selecting and Creating Columns', PDF viewer pages 279-296",
                "Worked selector examples tied to column creation and schema evolution.",
                "Contrast pl.col expressions with selectors and practice selector set algebra.",
            ),
            official(
                "resource-polars-expression-expansion",
                "Polars expression expansion",
                "Selectors; combining selectors with set operations; operator ambiguity; debugging selectors",
                "https://docs.pola.rs/user-guide/expressions/expression-expansion/",
                "Canonical explanation of one expression expanding into multiple output expressions.",
                "Use it to reason about selector resolution separately from runtime values.",
            ),
            practice(
                "resource-polars-selector-schema-drift",
                "Selector schema-drift lab",
                "Exercise 1 - implement include/exclude/subset against narrow, wide, and changed schemas",
                "Tests must prove which columns are selected, their order, empty-match behavior, and fit-time "
                "versus predict-time resolution.",
            ),
            note_resource(
                "resource-note-columnselectorop",
                "Stratum ColumnSelectorOp note",
                "knowledge/notes/data-systems/stratum/dataframe-ops/note-stratum-op-columnselectorop.md",
                "Node shape, fit-time schema resolution, and stored selected_columns",
                "Connects Polars selectors to Stratum's deferred selector contract.",
                "Distinguish a runtime Polars selector expression from a skrub selector resolved at fit and reused "
                "at predict time.",
            ),
        ],
    )
    s2c = new_stage(
        "stage-polars-expr-horizontal-conditional",
        "Horizontal logic, folds, conditionals, and literals",
        "Compose row-wise boolean/count expressions safely across dynamic column sets, including Kleene logic "
        "and Polars' requirement that every when/then branch be independently valid.",
        [
            "Write and test any/all/threshold predicates over a dynamic subset without Python row loops.",
            "Reimplement one horizontal helper with pl.fold and explain the accumulator dtype.",
            "A truth-table test covers true, false, null, NaN, empty subset, and invalid branch cases.",
        ],
        ["concept-map-family", "concept-dataframe-semantics"],
        [
            material_book(
                "resource-polars-book-horizontal",
                "route-polars-definitive-guide-s02",
                "Chapter 9 horizontal helpers, PDF viewer pages 262-277; Chapter 13 folds, pages 387-390",
                "Concrete progression from built-in horizontal helpers to general folds.",
                "Use the examples to derive boolean and counted-row predicates rather than memorizing helpers.",
            ),
            official(
                "resource-polars-folds",
                "Polars folds",
                "Basic example; initial accumulator; conditional folds; string folds",
                "https://docs.pola.rs/user-guide/expressions/folds/",
                "Explains the general expression reduction behind horizontal helpers.",
                "Pay special attention to accumulator type and dynamic expression expansion.",
            ),
            official(
                "resource-polars-when",
                "polars.when",
                "Branch validity, expression inputs, literals, and chained when/then/otherwise",
                "https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.when.html",
                "Makes the non-short-circuit branch contract explicit.",
                "Build a pandas mask/where case whose unselected branch would fail, then make every Polars branch valid.",
            ),
            practice(
                "resource-polars-horizontal-dropna-core",
                "Derive the dropna predicate core",
                "Exercise 2 - derive how='any', how='all', and thresh predicates over a dynamic subset",
                "The result is an Expr-producing helper plus a truth-table test; Session 3 integrates it into "
                "SelectionOp runtime argument handling.",
            ),
        ],
    )
    s2d = new_stage(
        "stage-polars-expr-assignmap-lowering",
        "Translate pandas assign into native expression trees",
        "Lower foldable pandas assign operations into a single Polars with_columns expression list while "
        "preserving sequential visibility and recognizing when opaque fallback is required.",
        [
            "Translate scalar, column-derived, overwrite, and sibling-dependent assign cases.",
            "Explain why sibling expressions in one with_columns call cannot see each other and stage dependencies when needed.",
            "Classify positional args, sequence constants, callable cases, and external operands as native, staged, or fallback.",
        ],
        ["concept-map-family", "concept-op-rewriting", "concept-dispatch"],
        [
            note_resource(
                "resource-note-assignmapop",
                "Stratum AssignMapOp note",
                "knowledge/notes/data-systems/stratum/dataframe-ops/note-stratum-op-assignmapop.md",
                "Complete note: foldability rules, ordered entries, leaf operands, and fallbacks",
                "Shows the exact logical contract the expression backend must consume.",
                "Trace how ColumnExpr leaves become backend expressions, then test sequential pandas assign visibility.",
            ),
            note_resource(
                "resource-note-assignop",
                "Stratum AssignOp fallback note",
                "knowledge/notes/data-systems/stratum/dataframe-ops/note-stratum-op-assignop.md",
                "Complete note: opaque fallback cases",
                "Defines the boundary where expression lowering must stop.",
                "Use it to make fallback an explicit supported outcome rather than an accidental implementation failure.",
                scope="helpful-now",
            ),
            practice(
                "resource-polars-assignmap-matrix",
                "AssignMap translation matrix",
                "Exercise 3 - 12 cases spanning constants, overwrites, dependencies, external operands, and invalid shapes",
                "Each row records pandas result, intended logical contract, Polars plan, and native/staged/fallback classification.",
            ),
        ],
    )
    add_session(
        "unit-job-polars-expressions",
        "Session 2 - Polars expression fluency",
        "Build and compose Polars expressions from intent, with explicit context, shape, schema, dependency, and "
        "failure reasoning before any backend operator clinic.",
        [
            ("knowledge-polars-expr-contexts", "Expression contexts", "Predict how one Expr behaves in select, with_columns, filter, and group_by."),
            ("knowledge-polars-expr-expansion", "Selectors and expansion", "Resolve schema-driven expression expansion without Python column loops."),
            ("knowledge-polars-expr-horizontal", "Horizontal and conditional logic", "Compose folds, horizontal predicates, literals, and valid branches."),
            ("knowledge-polars-expr-lowering", "Logical-to-Expr lowering", "Translate backend-neutral column expressions and identify explicit fallback boundaries."),
        ],
        [s2a, s2b, s2c, s2d],
        ["concept-map-family", "concept-projection-family", "concept-op-rewriting", "concept-dispatch"],
    )

    s3a = migrated_stage(
        old[3],
        "unit-job-polars-selection-backend",
        ["concept-selection-family", "concept-projection-family"],
        "Selection and projection contracts",
    )
    s3b = new_stage(
        "stage-polars-selection-head-tail-sample",
        "HEAD, TAIL, and SAMPLE runtime operands",
        "Implement and test selection operations whose parameters may be literals at planning time or OperandRef "
        "values resolved only during execution.",
        [
            "A case matrix covers default, zero, negative, oversized, empty-frame, and runtime-ref n for head and tail.",
            "Sample covers n versus fraction, replacement, shuffle, seed, runtime refs, and unsupported pandas options.",
            "Tests assert the intended randomness contract without requiring pandas and Polars to produce identical random rows.",
        ],
        ["concept-selection-family", "concept-dispatch", "concept-dataframe-semantics"],
        [
            note_resource(
                "resource-note-selectionop-head-tail-sample",
                "Stratum SelectionOp note",
                "knowledge/notes/data-systems/stratum/dataframe-ops/note-stratum-op-selectionop.md",
                "SelectionKind, args/kwargs/predicate fields, and physical method mapping",
                "Defines the logical payload and operator family before backend translation.",
                "Keep plan-time supports checks separate from process-time OperandRef resolution.",
            ),
            resource(
                "resource-selection-execs-case-study",
                "read",
                "Attached _selection_execs.py case study",
                "/Users/aramaljanadi/Downloads/_selection_execs.py: sample around line 118; duplicate handling around line 180; dropna around line 216",
                "The exact recent implementation that exposed the expression and runtime-operand gaps.",
                "Annotate the pandas contract, parameter translation, native Polars operation, fallback decision, and missing tests for each branch.",
            ),
            official("resource-pandas-head", "pandas DataFrame.head/tail", "head and tail parameters, defaults, negative n", "https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.head.html", "Defines the pandas oracle edge cases for prefix and suffix selection.", "Pair with executable tail probes and empty/oversized cases."),
            official("resource-polars-head", "Polars DataFrame.head/tail", "head and tail n behavior", "https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.head.html", "Defines the native Polars prefix operation.", "Probe negative and oversized n under 1.36.0 before deciding whether translation is direct."),
            official("resource-pandas-sample", "pandas DataFrame.sample", "n, frac, replace, weights, random_state, axis, ignore_index", "https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.sample.html", "Exposes the full pandas surface that the backend must classify.", "Separate supported semantic options from weights/axis features that lack a direct Polars mirror."),
            official("resource-polars-sample", "Polars DataFrame.sample", "n, fraction, with_replacement, shuffle, seed", "https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.sample.html", "Defines native sampling parameters and their names.", "Test reproducibility within a backend; do not assume cross-library RNG identity."),
            practice("resource-selection-head-tail-sample-matrix", "Selection parameter matrix", "Exercise 1 - implement 30 HEAD/TAIL/SAMPLE cases through literal and OperandRef paths", "Every cell is classified native, adapted, fallback, or unsupported and deposits an executable parity case."),
        ],
    )
    s3c = new_stage(
        "stage-polars-selection-duplicates",
        "DROP_DUPLICATES versus unique",
        "Translate pandas duplicate-removal semantics into Polars unique parameters while making keep, subset, "
        "order, and unsupported cases explicit.",
        [
            "A truth table covers keep='first', keep='last', keep=False, subset, nulls, NaNs, empty frames, and stable order.",
            "Parameter mapping is isolated and unit-tested independently of dataframe execution.",
            "List-column and version-sensitive limitations are recorded as policy rather than hidden by normalization.",
        ],
        ["concept-selection-family", "concept-dataframe-semantics"],
        [
            official("resource-pandas-drop-duplicates", "pandas DataFrame.drop_duplicates", "subset, keep, inplace, ignore_index", "https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.drop_duplicates.html", "Defines the duplicate-removal oracle including keep=False.", "Translate only the observable result contract; inplace is an API concern rather than a backend dataframe result."),
            official("resource-polars-unique", "Polars DataFrame.unique", "subset, keep, maintain_order", "https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.unique.html", "Provides native de-duplication plus explicit order control.", "Derive pandas keep values and make maintain_order a deliberate cost/semantics choice."),
            practice("resource-selection-duplicates-matrix", "Duplicate-removal compatibility matrix", "Exercise 2 - all keep/subset/order/null combinations on adversarial duplicates", "The mapping function and result tests must fail independently so argument bugs are distinguishable from engine behavior."),
        ],
    )
    s3d = new_stage(
        "stage-polars-selection-dropna",
        "DROPNA from selectors and horizontal expressions",
        "Implement pandas dropna behavior by combining runtime subset resolution, null/NaN predicates, horizontal "
        "logic, and threshold counting instead of assuming drop_nulls is equivalent.",
        [
            "A single implementation handles how='any', how='all', thresh, subset, and runtime OperandRef variants.",
            "Mixed float/string/integer/datetime cases distinguish null from NaN and match the agreed pandas contract.",
            "Invalid argument combinations and missing columns raise the intended exception class at the intended boundary.",
        ],
        ["concept-selection-family", "concept-map-family", "concept-dataframe-semantics"],
        [
            official("resource-polars-missing-data", "Polars missing data", "null and NaN; metadata; filling; NaN behavior", "https://docs.pola.rs/user-guide/expressions/missing-data/", "Explains why null and floating NaN require separate predicates.", "Use it to derive the predicate; drop_nulls alone cannot implement the pandas contract."),
            official("resource-polars-drop-nulls", "Polars DataFrame.drop_nulls", "subset selectors and null-only behavior", "https://docs.pola.rs/api/python/stable/reference/dataframe/api/polars.DataFrame.drop_nulls.html", "Provides the direct fast path for the subset of pandas behavior it truly matches.", "Document when the native call is safe and when a filter expression is required."),
            official("resource-pandas-dropna", "pandas DataFrame.dropna", "axis, how, thresh, subset, ignore_index", "https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.dropna.html", "Defines the oracle's argument interactions and failure surface.", "Probe how null sentinels and dtypes affect results under pandas 3.0.2."),
            note_resource("resource-note-missingmaskop", "Stratum MissingMaskOp note", "knowledge/notes/data-systems/stratum/dataframe-ops/note-stratum-op-missingmaskop.md", "Complete note: positive flag, call/method extraction, and Polars compilation", "Connects missing-value semantics to the reusable map-expression representation.", "Reuse the null/NaN predicate policy rather than embedding a second missingness definition in SelectionOp."),
            practice("resource-selection-dropna-implementation", "Rebuild DROPNA without AI", "Exercise 3 - close the attached file, derive the expression from the pandas contract, then compare", "The final result includes a small helper decomposition, truth table, runtime-ref tests, and a written explanation of every divergence."),
        ],
    )
    add_session(
        "unit-job-polars-selection-backend",
        "Session 3 - Selection backend clinic",
        "Use the attached SelectionOp implementation as a real backend clinic: resolve runtime operands, translate "
        "parameters, compose native Polars expressions, and make fallbacks and unsupported behavior explicit.",
        [
            ("knowledge-polars-selection-contract", "Selection versus projection", "Separate row restriction from column selection and preserve shape contracts."),
            ("knowledge-polars-runtime-operands", "Runtime operand resolution", "Distinguish plan-time support from process-time values."),
            ("knowledge-polars-selection-methods", "Method selection semantics", "Implement head, tail, sample, and duplicate removal with explicit mappings."),
            ("knowledge-polars-dropna-lowering", "Dropna expression lowering", "Compose selectors, missing predicates, horizontal logic, and thresholds."),
        ],
        [s3a, s3b, s3c, s3d],
        ["concept-selection-family", "concept-projection-family", "concept-map-family", "concept-dispatch", "concept-dataframe-semantics"],
    )

    add_session(
        "unit-job-polars-schema-missing-types",
        "Session 4 - Schema, dtypes, and missing values",
        "Predict and preserve schema, coercion, null/NaN, construction, I/O, and failure behavior across the pinned backends.",
        [
            ("knowledge-polars-schema-construction", "Construction and schema", "Build typed frames and distinguish eager values from lazy schema facts."),
            ("knowledge-polars-casting", "Casting and coercion", "Classify strict, permissive, widening, and failure behavior."),
            ("knowledge-polars-missing-model", "Null and NaN model", "Preserve or intentionally adapt pandas missing-value behavior by dtype."),
        ],
        [
            migrated_stage(old[2], "unit-job-polars-schema-missing-types", ["concept-dataframe-semantics"], "Construction, I/O, schema, and chunks"),
            migrated_stage(old[6], "unit-job-polars-schema-missing-types", ["concept-dataframe-semantics"], "Type promotion, coercion, and strictness"),
            migrated_stage(old[5], "unit-job-polars-schema-missing-types", ["concept-dataframe-semantics", "concept-map-family"], "Nulls, NaNs, and the missing-value model"),
        ],
        ["concept-dataframe-semantics", "concept-map-family"],
    )

    add_session(
        "unit-job-polars-order-text-time",
        "Session 5 - Ordering, text, and temporal operations",
        "Make row order and determinism explicit, then translate string and temporal namespace operations without "
        "assuming pandas accessor names or calendar conventions carry over.",
        [
            ("knowledge-polars-ordering", "Ordering and determinism", "Specify stable ties, null placement, and operations with undefined order."),
            ("knowledge-polars-text-temporal", "Text and temporal namespaces", "Translate accessor methods, parsing options, and calendar conventions."),
        ],
        [
            migrated_stage(old[7], "unit-job-polars-order-text-time", ["concept-dataframe-semantics"], "Ordering, sorting, and determinism"),
            migrated_stage(old[8], "unit-job-polars-order-text-time", ["concept-projection-family", "concept-dataframe-semantics"], "Strings, datetimes, and namespace translation"),
        ],
        ["concept-dataframe-semantics", "concept-projection-family"],
    )

    s6a = migrated_stage(old[9], "unit-job-polars-aggregation-windows", ["concept-aggregation", "concept-aggregation-family", "concept-dataframe-semantics"], "GroupBy aggregation, counting, and de-duplication")
    s6b = new_stage(
        "stage-polars-aggregation-signature-contract",
        "Aggregation signature and flag contract",
        "Preserve method-specific pandas aggregation flags through logical extraction and decide how each lowers to "
        "Polars, adapts, or falls back.",
        [
            "Build a signature matrix across Series, DataFrame, SeriesGroupBy, and DataFrameGroupBy for the operations Stratum captures.",
            "For every flag, identify its owner: group construction, aggregation call, result normalization, or unsupported API surface.",
            "Add at least one executable contention case for null policy, numeric_only, min_count, and result shape.",
        ],
        ["concept-aggregation", "concept-aggregation-family", "concept-logical-ir", "concept-dispatch"],
        [
            note_resource("resource-note-pandas-groupby-signatures", "pandas GroupBy signature reference", "knowledge/notes/data-systems/dataframe-semantics/note-pandas-groupby-signatures.md", "Complete note; targets pandas 3.0.2", "Inventory of the per-method flags Stratum's logical record must not erase.", "Turn the tables into a smaller backend support matrix and keep groupby kwargs distinct from aggregation-call kwargs."),
            note_resource("resource-note-aggregation-contentions", "pandas-Polars aggregation contention map", "knowledge/notes/data-systems/dataframe-semantics/note-pandas-polars-aggregation-contentions.md", "Complete note plus executable attachments; verified against pandas 3.0.2 and Polars 1.36.0", "The strongest local semantic evidence for this session.", "Run the attached probes before changing a contention; distinguish executable observations from architecture decisions."),
            note_resource("resource-note-aggregateop", "Stratum AggregateOp note", "knowledge/notes/data-systems/stratum/dataframe-ops/note-stratum-op-aggregateop.md", "Complete note: fused groupby extraction and OperandRef shifting", "Connects pandas signatures to the actual logical fields and graph rewrite.", "Trace a direct method and an agg-spec call through extraction before writing the physical implementation."),
            official("resource-polars-aggregation-guide", "Polars aggregation guide", "Basic aggregations; conditionals; filtering; nested grouping; sorting; parallelization", "https://docs.pola.rs/user-guide/expressions/aggregation/", "Shows native expression-based grouped aggregation patterns.", "Prefer expressions over Python iteration and predict whether each expression produces scalars or lists per group."),
            practice("resource-aggregation-support-matrix", "Aggregation backend support matrix", "Exercise 1 - 20 operation/flag combinations across grouped and ungrouped APIs", "Every row records logical fields, pandas 3.0.2 oracle, Polars 1.36.0 lowering, and native/adapt/fallback/unsupported status."),
        ],
    )
    s6c = migrated_stage(old[10], "unit-job-polars-aggregation-windows", ["concept-aggregation", "concept-aggregation-family", "concept-map-family"], "Windows and per-group transformations")
    add_session(
        "unit-job-polars-aggregation-windows",
        "Session 6 - Aggregation and windows",
        "Implement grouped reductions and same-cardinality window transforms while preserving flags, shape, order, "
        "and missing-value semantics.",
        [
            ("knowledge-polars-aggregation", "Grouped aggregation", "Compose reductions, conditional aggregations, and list outputs without Python loops."),
            ("knowledge-polars-aggregation-flags", "Aggregation flags", "Retain method-specific pandas options through extraction and lowering."),
            ("knowledge-polars-windows", "Window and transform parity", "Use Expr.over for same-cardinality grouped operations with explicit ordering."),
        ],
        [s6a, s6b, s6c],
        ["concept-aggregation", "concept-aggregation-family", "concept-map-family", "concept-logical-ir", "concept-dispatch"],
    )

    add_session(
        "unit-job-polars-joins-reshape",
        "Session 7 - Joins, concatenation, and reshaping",
        "Specify key cardinality, null matching, suffixes, coalescing, output order, and shape before lowering joins, "
        "concatenation, and reshape operations.",
        [
            ("knowledge-polars-join-semantics", "Join semantics", "Predict cardinality and key/null behavior for each join kind."),
            ("knowledge-polars-join-compatibility", "Join compatibility layer", "Translate pandas merge/join options into explicit Polars parameters or fallbacks."),
            ("knowledge-polars-reshape", "Concatenation and reshape", "Preserve schema, order, and eager/lazy constraints across concat, pivot, and unpivot."),
        ],
        [
            migrated_stage(old[11], "unit-job-polars-joins-reshape", ["concept-join-family", "concept-dataframe-semantics"], "Relational joins and key cardinality"),
            migrated_stage(old[12], "unit-job-polars-joins-reshape", ["concept-join-family", "concept-dispatch", "concept-dataframe-semantics"], "Build a pandas-Polars join compatibility layer"),
            migrated_stage(old[13], "unit-job-polars-joins-reshape", ["concept-join-family", "concept-projection-family"], "Concatenation and reshaping"),
        ],
        ["concept-join-family", "concept-dataframe-semantics", "concept-dispatch", "concept-projection-family"],
    )

    add_session(
        "unit-job-polars-lazy-udf-interop",
        "Session 8 - Lazy plans, UDF boundaries, and Arrow interop",
        "Read optimized plans, keep transformations expression-native, and recognize materialization, UDF, Arrow, "
        "chunk, and conversion boundaries that affect a physical backend.",
        [
            ("knowledge-polars-lazy-plans", "Lazy query plans", "Locate pushdowns, fusion opportunities, repeated scans, and premature collection."),
            ("knowledge-polars-udf-boundary", "Native expression versus UDF", "Rewrite common Python UDF patterns and declare irreducible fallbacks."),
            ("knowledge-polars-arrow-interop", "Arrow and conversion costs", "Reason about buffers, chunks, copies, and backend boundaries."),
        ],
        [
            migrated_stage(old[14], "unit-job-polars-lazy-udf-interop", ["concept-logical-ir", "concept-op-rewriting", "concept-operator-fusion"], "Lazy plans and optimizer literacy"),
            migrated_stage(old[15], "unit-job-polars-lazy-udf-interop", ["concept-map-family", "concept-dispatch"], "UDF fallbacks and native expression rewrites"),
            migrated_stage(old[16], "unit-job-polars-lazy-udf-interop", ["concept-dataframe-semantics"], "Arrow interop, chunks, and conversion costs"),
        ],
        ["concept-logical-ir", "concept-op-rewriting", "concept-operator-fusion", "concept-map-family", "concept-dispatch", "concept-dataframe-semantics"],
    )

    s9a = new_stage(
        "stage-polars-backend-trace-lifecycle",
        "Trace capture, logical rewrite, selection, and execution",
        "Follow one pandas call from captured DataOp through specialized logical IR and late physical backend "
        "selection, naming the semantic owner at every boundary.",
        [
            "Produce traces for SelectionOp, AssignMapOp, AggregateOp, and JoinOp using current Stratum files.",
            "For each trace, identify which facts exist at plan time and which require runtime inputs or fit-time schema.",
            "Explain why Stratum's DAG-level laziness and a Polars physical kernel are related but not identical abstractions.",
        ],
        ["concept-logical-ir", "concept-op-rewriting", "concept-dispatch"],
        [
            resource("resource-stratum-paper-architecture", "read", "stratum paper - architecture", "Sections 4.1-4.3, PDF viewer pages 4-5", "The authoritative system-level reason for logical operators and late physical selection.", "Trace the paper's declarative abstraction, operator lowering, and operator selection into the current repository; do not infer unimplemented behavior.", source_id="source-stratum-paper", route_id="route-stratum-paper-s09", vault_path="material://source-stratum-paper/stratum-paper.pdf"),
            note_resource("resource-note-extract-dataframe-op", "extract_dataframe_op dispatch map", "knowledge/notes/data-systems/stratum/note-stratum-extract-dataframe-op.md", "Complete frame-like branch dispatch map", "Shows exactly how generic Python operations become specialized dataframe IR.", "Reproduce four branches from a blank diagram and verify them against current source."),
            note_resource("resource-note-selectionop-loop", "SelectionOp logical note", "knowledge/notes/data-systems/stratum/dataframe-ops/note-stratum-op-selectionop.md", "Complete note", "First of four repeated implementation-loop anchors.", "Use the same checklist later for AssignMapOp, AggregateOp, and JoinOp."),
            practice("resource-backend-four-traces", "Four operator lifecycle traces", "Exercise 1 - capture -> rewrite -> support -> select -> resolve -> execute -> compare", "Each trace names inputs, logical fields, support decision, runtime resolutions, physical kernel, fallback, and parity tests."),
        ],
    )
    s9b = new_stage(
        "stage-polars-backend-decision-loop",
        "Apply the backend implementation decision loop",
        "Use one repeatable decision procedure for every physical operation: normalize the pandas contract, check "
        "support on raw logical fields, resolve runtime operands, choose native/adapt/fallback/unsupported, execute, "
        "and compare through the parity harness.",
        [
            "Write the decision loop as a review checklist and apply it to four operator families.",
            "Demonstrate one bug caused by resolving too early and one caused by checking support too late.",
            "Every fallback and unsupported case reports a reason tied to an observable contract dimension.",
        ],
        ["concept-dispatch", "concept-logical-ir", "concept-dataframe-semantics"],
        [
            resource("resource-depth-dispatch", "read", "Python Depth Drills - interfaces and dispatch", "Stage 8 guide and notebook; especially Q8.10 and Q8.11", "Practices the mechanism and judgment behind supports/cost registries and subclass dispatch.", "Use the two-key Selector drill as a miniature physical implementation registry, then compare it with Stratum's current dispatch.", source_id="source-python-depth-drills", route_id="route-python-depth-drills-s09", vault_path="material://source-python-depth-drills/stage-8-interfaces-and-dispatch.md"),
            note_resource("resource-note-joinop-loop", "JoinOp logical note", "knowledge/notes/data-systems/stratum/dataframe-ops/note-stratum-op-joinop.md", "Complete note", "Exercises the same loop on binary inputs, key flags, and chained joins.", "Classify every logical field before looking at the physical implementation."),
            practice("resource-backend-decision-table", "Physical backend decision table", "Exercise 2 - four families x normalize/support/resolve/classify/execute/verify", "The table is complete only when each cell cites code or an executable fixture and no capability is inferred from a method name."),
        ],
    )
    s9c = new_stage(
        "stage-polars-backend-family-transfer",
        "Transfer the loop across four logical families",
        "Implement or reconstruct one small Polars kernel in Selection, Map/Projection, Aggregation, and Join to "
        "prove expression fluency transfers beyond the motivating file.",
        [
            "Close the implementation and rebuild one bounded kernel per family from the logical contract and tests.",
            "Each kernel has adversarial tests and a declared fallback/unsupported surface.",
            "Review the four implementations for duplicated translation policy and extract only a proven shared helper.",
        ],
        ["concept-selection-family", "concept-map-family", "concept-aggregation-family", "concept-join-family", "concept-op-rewriting"],
        [
            note_resource("resource-note-assignmapop-loop", "AssignMapOp logical note", "knowledge/notes/data-systems/stratum/dataframe-ops/note-stratum-op-assignmapop.md", "Complete note", "Map-family transfer case for expression construction and fallback.", "Rebuild a foldable subset without reading the physical kernel, then compare."),
            note_resource("resource-note-aggregateop-loop", "AggregateOp logical note", "knowledge/notes/data-systems/stratum/dataframe-ops/note-stratum-op-aggregateop.md", "Complete note", "Aggregation-family transfer case for flags, grouping, and output shape.", "Use the contention probes as the semantic oracle rather than method-name similarity."),
            note_resource("resource-note-joinop-family-loop", "JoinOp logical note", "knowledge/notes/data-systems/stratum/dataframe-ops/note-stratum-op-joinop.md", "Complete note", "Join-family transfer case for binary inputs and cardinality.", "Make null equality and output order explicit before choosing Polars parameters."),
            practice("resource-four-family-rebuild", "Four-family rebuild-blind lab", "Exercise 3 - one bounded physical kernel in Selection, Map/Projection, Aggregation, and Join", "A kernel counts only after targeted tests pass and its unsupported/fallback surface is documented."),
        ],
    )
    s9d = new_stage(
        "stage-polars-backend-regression-policy",
        "Failure policy and regression gate",
        "Turn semantic decisions into maintainable regression tests that distinguish unsupported input, fallback, "
        "translation bugs, Polars execution errors, and intentional divergences.",
        [
            "Define a failure taxonomy and assert exception type/message only where the contract owns them.",
            "Parameter mapping, expression construction, engine execution, and normalized comparison can fail independently in tests.",
            "At least one generated test finds an edge case not present in the handwritten matrix.",
        ],
        ["concept-dataframe-semantics", "concept-dispatch"],
        [
            official("resource-polars-parametric-testing", "Polars parametric testing", "Strategies for columns, dataframes, dtypes, lists, profiles, and examples", "https://docs.pola.rs/api/python/stable/reference/testing.html", "Generates adversarial Polars inputs for regression discovery.", "Treat this API as unstable and pin it with the backend version; shrink failures into permanent hand-written regression cases."),
            resource("resource-depth-testing", "read", "Python Depth Drills SHELF - testing", "SHELF.md section 3a: pytest, pytest.raises, Hypothesis, test design", "Supplies the Python testing mechanics the dataframe plan previously assumed.", "Use parametrization for the explicit matrix and Hypothesis only where an invariant can be stated precisely.", source_id="source-python-depth-drills", route_id="route-python-depth-drills-s09", vault_path="material://source-python-depth-drills/SHELF.md"),
            practice("resource-regression-generated-case", "Generated-edge regression lab", "Exercise 4 - generate mixed schemas/nulls/sizes, shrink one failure, and promote it to a named case", "The permanent case records versions, raw input, pandas observation, Polars observation, classification, and chosen policy."),
        ],
    )
    add_session(
        "unit-job-polars-backend-loop",
        "Session 9 - Repeated Stratum backend implementation loop",
        "Repeat the full logical-to-physical workflow across Selection, Map/Projection, Aggregation, and Join so the "
        "skill transfers to new ML-pipeline operations rather than remaining tied to one file.",
        [
            ("knowledge-polars-stratum-lifecycle", "Stratum operation lifecycle", "Trace capture, logical rewrite, selection, runtime resolution, execution, and comparison."),
            ("knowledge-polars-implementation-decision", "Implementation decision loop", "Normalize, support-check, resolve, classify, execute, and verify."),
            ("knowledge-polars-family-transfer", "Cross-family transfer", "Apply expression and parity skills to four logical families."),
            ("knowledge-polars-regression-policy", "Regression and failure policy", "Turn semantic decisions into generated and named regression tests."),
        ],
        [s9a, s9b, s9c, s9d],
        ["concept-logical-ir", "concept-op-rewriting", "concept-dispatch", "concept-dataframe-semantics", "concept-selection-family", "concept-map-family", "concept-aggregation-family", "concept-join-family"],
    )

    s10a = migrated_stage(old[17], "unit-job-polars-capstone-transition", ["concept-logical-ir", "concept-dispatch", "concept-dataframe-semantics"], "Capstone - specify, implement, and prove a mirrored operation")
    s10b = new_stage(
        "stage-polars-capstone-property-stress",
        "Property and adversarial stress pass",
        "Stress the capstone across schema, missingness, cardinality, order, and failure boundaries, then turn every "
        "found counterexample into a durable named regression.",
        [
            "Generated tests span empty/wide frames, duplicate keys, mixed null/NaN, boundary sizes, and relevant dtypes.",
            "Every failure is classified as implementation bug, unsupported pandas surface, intentional divergence, or invalid test oracle.",
            "The final support matrix and normalization policy agree with the executable suite.",
        ],
        ["concept-dataframe-semantics", "concept-dispatch"],
        [
            official("resource-polars-testing-capstone", "Polars testing reference", "Frame/series asserts plus parametric strategies and profiles", "https://docs.pola.rs/api/python/stable/reference/testing.html", "Provides the capstone's native assertions and generated inputs.", "Pin strategy behavior and retain shrunk counterexamples as ordinary fixtures."),
            official("resource-pandas-testing-capstone", "pandas testing reference", "assert_frame_equal comparison controls", "https://pandas.pydata.org/docs/reference/api/pandas.testing.assert_frame_equal.html", "Makes the oracle comparison policy reviewable.", "Use operation-specific profiles instead of silently dropping index, dtype, or order differences."),
            practice("resource-capstone-stress-report", "Capstone stress report", "Exercise 1 - generated run plus named counterexample ledger", "The report lists versions, seed/profile, invariants, failures, classifications, and permanent regression IDs."),
        ],
    )
    s10c = new_stage(
        "stage-polars-version-transition-lab",
        "Version transition lab - 1.36 baseline versus newer Polars",
        "Keep the production study target on Polars 1.36.0 while rehearsing a controlled upgrade assessment for "
        "ordering, streaming, concat, explode, casting/coercion, and selector changes.",
        [
            "Run the capstone suite unchanged under the candidate version in an isolated environment.",
            "Produce a behavior delta table; no newer behavior is copied into the 1.36 contract without a Stratum dependency change.",
            "Classify each delta as API rename, documented semantic change, regression, or newly supported capability.",
        ],
        ["concept-dataframe-semantics", "concept-dispatch"],
        [
            official("resource-polars-upgrade-2", "Polars 2.0 upgrade guide", "Streaming default; ordering; concat strictness; explode; casting/coercion; selectors", "https://docs.pola.rs/releases/upgrade/2/", "Isolates future semantic changes from today's locked backend target.", "Read only after the 1.36 capstone passes; use the guide to choose delta probes, not as authority for current Stratum behavior.", scope="deferred"),
            official("resource-pandas-3-release", "pandas 3.0 release notes", "String dtype, Copy-on-Write, joins, GroupBy and compatibility changes", "https://pandas.pydata.org/docs/whatsnew/v3.0.0.html", "Explains the major-version oracle changes relevant to Stratum's pinned pandas 3.0.2.", "Confirm the lockfile patch release with probes; avoid importing post-3.0.2 behavior from stable docs.", scope="reference-only"),
            practice("resource-version-delta-matrix", "Backend version delta matrix", "Exercise 2 - run the same parity corpus in isolated baseline and candidate environments", "No production policy changes here; the output is an upgrade decision input with reproducible environments and exact failing cases."),
        ],
    )
    add_session(
        "unit-job-polars-capstone-transition",
        "Session 10 - Capstone and controlled version transition",
        "Implement one mirrored backend operation end to end, prove its contract with adversarial and generated "
        "tests, and keep future Polars-version assessment isolated from today's production baseline.",
        [
            ("knowledge-polars-capstone", "Mirrored-operation capstone", "Specify and implement one bounded physical operator from pandas contract to Polars kernel."),
            ("knowledge-polars-property-stress", "Property stress", "Search the semantic boundary and retain minimized regressions."),
            ("knowledge-polars-version-transition", "Controlled version transition", "Compare a candidate Polars release without mutating the locked contract."),
        ],
        [s10a, s10b, s10c],
        ["concept-logical-ir", "concept-dispatch", "concept-dataframe-semantics"],
    )

    # Rich local-material routes.  Stage resources remain the ordered learning
    # script; these routes are the complete, learner-facing material menu.
    book_locators = {
        1: "Chapters 1 and 3, PDF viewer pages 14-51 and 74-102",
        2: "Chapters 7-10, PDF viewer pages 178-306",
        3: "Chapters 10-11 and fold section, PDF viewer pages 279-326 and 387-390",
        4: "Chapters 4-6 and 12, PDF viewer pages 103-177 and 327-368",
        5: "Chapters 11-12, PDF viewer pages 307-368",
        6: "Chapter 13, PDF viewer pages 369-402",
        7: "Chapters 14-15, PDF viewer pages 403-457",
        8: "Chapters 5, 17, and 18, PDF viewer pages 122-143 and 503-591",
        9: "Selected implementation patterns in Chapters 7-14, PDF viewer pages 178-433",
        10: "Chapter 18 plus relevant operation chapters, PDF viewer pages 537-591 and the capstone's operation route",
    }
    pydata_locators = {
        1: "03.01-Introducing-Pandas-Objects.ipynb; 03.03-Operations-in-Pandas.ipynb",
        2: "03.03-Operations-in-Pandas.ipynb - index preservation and alignment sections",
        3: "'03.02-Data-Indexing-and-Selection.ipynb'; 03.04-Missing-Values.ipynb",
        4: "03.01-Introducing-Pandas-Objects.ipynb; 03.03-Operations-in-Pandas.ipynb; 03.04-Missing-Values.ipynb",
        5: "03.10-Working-With-Strings.ipynb; 03.11-Working-with-Time-Series.ipynb",
        6: "03.08-Aggregation-and-Grouping.ipynb",
        7: "03.06-Concat-And-Append.ipynb; 03.07-Merge-and-Join.ipynb; 03.09-Pivot-Tables.ipynb",
        8: "03.12-Performance-Eval-and-Query.ipynb; 01.07-Timing-and-Profiling.ipynb",
        9: "03.02-Data-Indexing-and-Selection.ipynb through 03.12-Performance-Eval-and-Query.ipynb",
        10: "03.00-Introduction-to-Pandas.ipynb plus the exact notebook for the capstone operation",
    }
    pydata_paths = {
        1: "03.01-Introducing-Pandas-Objects.ipynb",
        2: "03.03-Operations-in-Pandas.ipynb",
        3: "03.02-Data-Indexing-and-Selection.ipynb",
        4: "03.04-Missing-Values.ipynb",
        5: "03.10-Working-With-Strings.ipynb",
        6: "03.08-Aggregation-and-Grouping.ipynb",
        7: "03.07-Merge-and-Join.ipynb",
        8: "03.12-Performance-Eval-and-Query.ipynb",
        9: "03.00-Introduction-to-Pandas.ipynb",
        10: "03.00-Introduction-to-Pandas.ipynb",
    }
    cheat_panels = {
        1: "creating DataFrames, tidy data, and method chaining",
        2: "method chaining and make new variables",
        3: "subset observations, subset variables, and handling missing data",
        4: "creating DataFrames, logic, and handling missing data",
        5: "sorting, vector functions, and windows",
        6: "summarize data and group data",
        7: "reshaping data and combine data sets",
        8: "method chaining and vector functions",
        9: "method chaining, group data, and combine data sets",
        10: "method chaining, subset observations, summarize data, and combine data sets",
    }
    source_specs = {
        "source-polars-definitive-guide": {
            "role": "spine",
            "why": "Local Polars-first spine; expression chapters are promoted ahead of I/O and API catalogues.",
            "priority": 0,
            "format": "book",
        },
        "source-pydata-handbook": {
            "role": "reference",
            "why": "Local pandas example corpus used to generate oracle questions; it is too old to define pandas 3.0.2 semantics.",
            "priority": 2,
            "format": "code",
        },
        "source-python-cheatsheets": {
            "role": "reference",
            "why": "Two-page 2017 pandas operation index; retained for recall and explicitly demoted from semantic authority.",
            "priority": 3,
            "format": "documentation",
        },
        "source-python-depth-drills": {
            "role": "practice",
            "why": "Local testing, functions-as-objects, interfaces, and dispatch drills support backend engineering judgment.",
            "priority": 2,
            "format": "exercise",
        },
        "source-stratum-paper": {
            "role": "implementation",
            "why": "Authoritative architecture context for declarative DAGs, logical lowering, and late physical operator selection.",
            "priority": 0,
            "format": "paper",
        },
        "source-scalable-dataframe-systems-paper": {
            "role": "derivation",
            "why": "Formal dataframe model and algebra explain why pandas compatibility involves ordering, metadata, and more than relational values.",
            "priority": 1,
            "format": "paper",
        },
    }
    source_entries = []
    all_nodes = {
        entry["unit"]["id"]: [n["id"] for n in entry["unit"]["knowledge_map"]["nodes"]]
        for entry in sessions
    }
    used_by_unit = {
        entry["unit"]["id"]: {
            r["source_id"]
            for stage in entry["study_map"]["stages"]
            for r in stage["resources"]
            if r.get("source_id")
        }
        for entry in sessions
    }
    # The papers are useful architecture routes even where no inherited stage
    # used them; add them only to the genuinely relevant sessions.
    for uid in [OLD_UNIT_ID, "unit-job-polars-lazy-udf-interop", "unit-job-polars-backend-loop", "unit-job-polars-capstone-transition"]:
        used_by_unit[uid].add("source-stratum-paper")
    for uid in [OLD_UNIT_ID, "unit-job-polars-lazy-udf-interop", "unit-job-polars-backend-loop"]:
        used_by_unit[uid].add("source-scalable-dataframe-systems-paper")

    for source_id, spec in source_specs.items():
        routes = []
        for index, entry in enumerate(sessions, start=1):
            uid = entry["unit"]["id"]
            if source_id not in used_by_unit[uid]:
                continue
            if source_id == "source-polars-definitive-guide":
                title = f"Polars book - Session {index} route"
                locator = book_locators[index]
                angle = "Polars-native explanation and worked examples for this session."
                detail = "Read the named viewer pages after predicting the API shape; confirm examples against Polars 1.36.0 because the local book is an early-release edition."
                vault_path = "material://source-polars-definitive-guide/python-polars-the-definitive-guide.pdf"
                scope = "current"
                depth = "implementation"
            elif source_id == "source-pydata-handbook":
                title = f"Pandas handbook - Session {index} oracle prompts"
                locator = pydata_locators[index]
                angle = "Concrete pandas examples to convert into pinned executable contracts."
                detail = "The notebooks are old; use them to discover cases and index/alignment assumptions, then verify every relevant result under pandas 3.0.2."
                vault_path = "material://source-pydata-handbook/PythonDataScienceHandbook/notebooks/" + pydata_paths[index]
                scope = "prior-year"
                depth = "practice"
            elif source_id == "source-python-cheatsheets":
                title = f"Pandas cheat sheet - Session {index} operation index"
                locator = f"Pandas_cheatsheet.pdf, PDF viewer pages 1-2; panels: {cheat_panels[index]}"
                angle = "Quick operation recall before writing the pandas contract from memory."
                detail = "The sheet is from 2017 and omits modern dtype, Copy-on-Write, null, order, and failure behavior; it is never the semantic authority."
                vault_path = "material://source-python-cheatsheets/Pandas_cheatsheet.pdf"
                scope = "prior-year"
                depth = "orientation"
            elif source_id == "source-python-depth-drills":
                title = f"Python Depth Drills - Session {index} support route"
                locator = "stage-8-interfaces-and-dispatch.md, Q8.10-Q8.11; SHELF.md, sections 3a 'Testing' and 3c 'Performance'"
                angle = "Targeted Python mechanics for testable backend dispatch and measurement."
                detail = "Use only the named drills; this source improves implementation technique but does not define pandas or Polars behavior."
                vault_path = "material://source-python-depth-drills/stage-8-interfaces-and-dispatch.md"
                scope = "complementary"
                depth = "practice"
            elif source_id == "source-stratum-paper":
                title = f"stratum paper - Session {index} architecture route"
                locator = "Sections 4.1-4.3, PDF viewer pages 4-5; Section 1, viewer pages 1-2 for motivation"
                angle = "Connects dataframe exercises to Stratum's declarative DAG and late backend selection."
                detail = "Use the paper for architectural intent and verify current class/function details in the checkout; a vision claim is not implementation evidence."
                vault_path = "material://source-stratum-paper/stratum-paper.pdf"
                scope = "current"
                depth = "implementation"
            else:
                title = f"Scalable dataframe systems - Session {index} theory route"
                locator = "Sections 4.2-4.3, PDF viewer pages 5-7; Sections 5.1-5.2.3, viewer pages 10-12"
                angle = "Formalizes dataframe schema, ordering, metadata, and operator algebra behind compatibility decisions."
                detail = "Use the algebra to name semantic dimensions and optimizer constraints; it does not prescribe Stratum's exact supported API surface."
                vault_path = "material://source-scalable-dataframe-systems-paper/Towards Scalable Dataframe Systems.pdf"
                scope = "complementary"
                depth = "derivation"
            routes.append(
                {
                    "id": f"route-{source_id[7:]}-s{index:02d}",
                    "unit_id": uid,
                    "title": title,
                    "format": spec["format"],
                    "angle": angle,
                    "angle_detail": detail,
                    "covers": all_nodes[uid],
                    "depth": depth,
                    "scope": scope,
                    "locator": locator,
                    "vault_path": vault_path,
                }
            )
        if routes:
            source_entries.append(
                {
                    "source_id": source_id,
                    "role": spec["role"],
                    "why": spec["why"],
                    "priority": spec["priority"],
                    "unit_routes": routes,
                }
            )

    # Ensure source scope lists cover architecture routes that were added to the
    # complete menu even when the ordered stages use no source_id-bearing row.
    for entry in sessions:
        uid = entry["unit"]["id"]
        entry["unit"]["scope_sources"] = [
            {"source_id": source_id, "authority": "reference"}
            for source_id in source_specs
            if source_id in used_by_unit[uid]
        ]

    package = {
        "module_id": MODULE_ID,
        "plan_contract": {
            "version": 2,
            "plan_template_version": 1,
            "coverage_audit": AUDIT_REL,
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
        "module_patch": {
            "title": "Polars backend engineering with pandas semantics",
            "unit_order": [entry["unit"]["id"] for entry in sessions],
        },
        "source_patches": [],
        "source_map": {
            "type": "module-source-map",
            "module_id": MODULE_ID,
            "sources": source_entries,
        },
        "units": sessions,
        "workspace_updates": [],
    }

    audit = """# Polars backend plan - complete material coverage audit

Verified: 2026-09-03. Target environment: pandas 3.0.2 and Polars 1.36.0 from the current Stratum `pyproject.toml` and `uv.lock`.

## Local inventory

- **Existing learning map:** all 18 pending stages, 251 stage resources, and 18 authored working guides were inspected. Every stage/resource is preserved in the session migration. Session 1 retains its original paths; moved stages link back to the original authored guide while receiving a new owning-session working note.
- **Python Polars: The Definitive Guide:** 591-page early-release PDF opened and visually checked. Exact chapter starts were verified in viewer pages: Ch. 1 p.14, Ch. 2 p.52, Ch. 3 p.74, Ch. 4 p.103, Ch. 5 p.122, Ch. 6 p.144, Ch. 7 p.178, Ch. 8 p.208, Ch. 9 p.254, Ch. 10 p.279, Ch. 11 p.307, Ch. 12 p.327, Ch. 13 p.369, Ch. 14 p.403, Ch. 15 p.434, Ch. 16 p.458, Ch. 17 p.503, Ch. 18 p.537. Expression, selector, aggregation, join, lazy, extension, and Arrow routes use viewer-page ranges.
- **Python Data Science Handbook notebooks:** every pandas notebook 03.00-03.12 was enumerated and its markdown headings inspected. They cover objects/indexes, selection, alignment, missing values, concat, joins, grouping, pivots, strings, time series, and eval/query. Disposition: useful executable prompt corpus, but prior-version material; pandas 3.0.2 docs and probes remain authority.
- **Pandas cheat sheet:** both viewer pages visually inspected. Disposition: operation-recall index only; it is dated 2017 and cannot establish current semantics.
- **Python Depth Drills:** Stage 8 interfaces/dispatch and SHELF sections 3a testing and 3c performance inspected. Disposition: complementary implementation practice, not dataframe semantic authority.
- **stratum paper:** all eight pages available; architecture sections 4.1-4.3 on viewer pages 4-5 visually checked. Disposition: architecture authority for declarative DAGs, lowering, and physical selection; checkout remains authority for implemented details.
- **Towards Scalable Dataframe Systems:** 19-page PDF; dataframe model/algebra on viewer pages 5-7 and schema/order/metadata challenges on pages 10-12 inspected, including a visual check of Section 4.3. Disposition: derivation/mental-model depth.
- **User-authored notes:** `note-stratum-extract-dataframe-op`, SelectionOp, ColumnSelectorOp, MissingMaskOp, AssignMapOp/AssignOp, AggregateOp, JoinOp, pandas GroupBy signatures, and the executable pandas-Polars aggregation contention map are explicitly routed into the applicable stages.
- **Attached case study:** `/Users/aramaljanadi/Downloads/_selection_execs.py` was compared with the current Stratum selection implementation before redesign; SAMPLE, duplicate mapping, DROPNA expression construction, and OperandRef resolution drive Session 3.

## Linked inventory

Official pages were opened or checked on 2026-09-03 and routed by exact section, not by homepage: Polars expressions and contexts; migration from pandas; expression expansion/selectors; folds; `when`; missing data; casting and schemas; head/tail/sample/unique/drop_nulls; aggregation; windows; joins; lazy usage/optimizations/query plans; UDF guidance; testing/parametric strategies; pandas 3.0 release notes; and the corresponding pandas 3.0.2 operation/testing references.

The live Polars documentation may describe a release newer than Stratum's Polars 1.36.0. Every linked behavior therefore carries an explicit pinned-environment verification rule. The Polars 2.0 upgrade guide is deferred to Session 10 and cannot define the current backend contract.

The official `pola-rs/polars-benchmark` paired pandas/Polars queries are retained as an advanced capstone corpus by link, not copied, because some benchmark inputs are license-governed and the plan needs only selected translation exercises.

## Completeness sign-off

- The redesign preserves all existing learning/exercise resources and adds missing expression, selector, horizontal/fold, real SelectionOp, cross-family implementation-loop, and generated-testing exercises.
- No fixed stage durations were retained or invented. Sessions are bounded by outcomes and contain two to four stages each.
- pandas is an operation-level observable oracle, not a demand to reproduce every incidental quirk. Each backend case ends in native, adapted, fallback, unsupported, or intentional-divergence policy.
- The cumulative harness is owned by Session 1 and used in every later done-when. A new first-class LearningOS project/workspace was deliberately not created in this migration because project creation does not create a joined workspace atomically; that extra write would delay today's usable curriculum. Exercise code belongs in a learner-chosen Stratum scratch/test file and can be attached to the stage without modifying Stratum automatically.
- Existing stages were all pending, so no completion evidence is moved or rewritten. Original moved-stage guides remain at their old paths as migration evidence and are linked from the new owning stage.
- Excluded as non-fitting: plotting/visualization chapters, unrelated NumPy/Matplotlib/ML notebooks, generic Python drills outside testing/dispatch/performance, and copying third-party benchmark data.
- Unresolved but visible: live official docs can drift; every behavior must be probed in the pinned environment. Polars 2.0 remains a deferred transition exercise until Stratum changes its dependency.
"""

    rows = []
    for index, entry in enumerate(sessions, start=1):
        stage_lines = "\n".join(
            f"  {stage['number']}. {stage['title']}" for stage in entry["study_map"]["stages"]
        )
        rows.append(f"## {entry['unit']['title']}\n\n{entry['unit']['scope']}\n\n{stage_lines}")
    summary = """# Polars backend engineering - session plan

Purpose: become fluent enough in Polars expressions and semantics to implement and verify logical dataframe operations in Stratum's Polars physical backend, while using pandas 3.0.2 as an explicit operation-level oracle.

Start today with Session 1, then Session 2 before returning to the `_selection_execs.py` clinic in Session 3. The order is intentional: the expression language and parity harness are prerequisites for solving DROPNA, selector, and runtime-operand problems without copying an answer.

""" + "\n\n".join(rows) + "\n"
    return package, audit, summary


def main() -> None:
    package, audit, summary = build()
    (ROOT / AUDIT_REL).write_text(audit, encoding="utf-8")
    (ROOT / SUMMARY_REL).write_text(summary, encoding="utf-8")
    (ROOT / PACKAGE_REL).write_text(dump_yaml(package), encoding="utf-8")
    print(ROOT / PACKAGE_REL)


if __name__ == "__main__":
    main()

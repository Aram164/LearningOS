"""Derived Catalog Sidecar Compiler (Task C.2).

Compiles the live repository YAML graph (modules, units, study maps, sources, concepts)
into a single persistent SQLite database (.derived/catalog.sqlite3).
Supports execution as a pure derived-engine node.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from learning_os.domain.snapshot import Repo
from learning_os.store.derived.model import DERIVED_SUBSTRATE_FILES, NodeSpec
from learning_os.store.loading import load_repo
from spike_catalog_schema import init_catalog_db

CATALOG_NODE_ID = "derived.catalog.sqlite3"
CATALOG_FORMAT_VERSION = 1

CATALOG_PRODUCER_FILES = (
    "tools/learning_os/store/loading/curriculum.py",
    "tools/learning_os/store/loading/library.py",
    "tools/learning_os/store/loading/knowledge.py",
    "workbench/spikes/catalog-sqlite-2026-11-07/spike_catalog_schema.py",
    "workbench/spikes/catalog-sqlite-2026-11-07/spike_catalog_compiler.py",
    *DERIVED_SUBSTRATE_FILES,
)


def catalog_node_spec() -> NodeSpec:
    """Derived node specification for the catalog sidecar database."""
    return NodeSpec(
        id=CATALOG_NODE_ID,
        version=CATALOG_FORMAT_VERSION,
        producer_files=CATALOG_PRODUCER_FILES,
        direct_inputs=(),
    )


def compile_catalog(repo: Repo, con: Any) -> None:
    """Populate an open SQLite connection with all catalog entities from a Repo instance."""
    cur = con.cursor()
    cur.execute("PRAGMA defer_foreign_keys = ON;")

    # 1. Programs
    for prog_id, prog in repo.programs.items():
        data = getattr(prog, "data", prog) if not isinstance(prog, dict) else prog
        cur.execute(
            "INSERT OR REPLACE INTO programs VALUES (?, ?, ?, ?, ?)",
            (
                prog_id,
                data.get("title", prog_id),
                data.get("kind", ""),
                data.get("status", ""),
                json.dumps(data, sort_keys=True),
            ),
        )

    # 2. Modules
    for mod_id, mod in repo.modules.items():
        data = getattr(mod, "data", mod) if not isinstance(mod, dict) else mod
        thematic = json.dumps(data.get("thematic_group_ids", []))
        unit_order = json.dumps(data.get("unit_order", []))
        cur.execute(
            "INSERT OR REPLACE INTO modules VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                mod_id,
                data.get("title", mod_id),
                data.get("kind", ""),
                data.get("status", ""),
                data.get("area_id", ""),
                thematic,
                unit_order,
                json.dumps(data, sort_keys=True),
            ),
        )

    # 3. Units
    for unit_id, unit in repo.units.items():
        data = getattr(unit, "data", unit) if not isinstance(unit, dict) else unit
        cur.execute(
            "INSERT OR REPLACE INTO units VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                unit_id,
                data.get("module_id", ""),
                data.get("title", unit_id),
                data.get("kind", ""),
                data.get("status", ""),
                data.get("order", 0),
                data.get("scope", ""),
                json.dumps(data, sort_keys=True),
            ),
        )

    # 4. Concepts (before study map stage concepts)
    for c_id, conc in repo.concepts.items():
        data = getattr(conc, "data", conc) if not isinstance(conc, dict) else conc
        cur.execute(
            "INSERT OR REPLACE INTO concepts VALUES (?, ?, ?, ?)",
            (
                c_id,
                data.get("label", c_id),
                data.get("description", ""),
                json.dumps(data, sort_keys=True),
            ),
        )

    # 5. Sources
    for src_id, src in repo.sources.items():
        data = getattr(src, "data", src) if not isinstance(src, dict) else src
        thematic = json.dumps(data.get("thematic_group_ids", []))
        cur.execute(
            "INSERT OR REPLACE INTO sources VALUES (?, ?, ?, ?, ?, ?)",
            (
                src_id,
                data.get("title", src_id),
                data.get("type", ""),
                data.get("status", ""),
                thematic,
                json.dumps(data, sort_keys=True),
            ),
        )

    # 6. Study Maps & Stages
    for sm_id, sm in repo.study_maps.items():
        data = getattr(sm, "data", sm) if not isinstance(sm, dict) else sm
        stages = data.get("stages", [])
        crit_count = sum(1 for st in stages if st.get("exam_critical"))
        cur.execute(
            "INSERT OR REPLACE INTO study_maps VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                sm_id,
                data.get("unit_id", ""),
                data.get("status", ""),
                data.get("current_stage", ""),
                len(stages),
                crit_count,
                json.dumps(data, sort_keys=True),
            ),
        )
        for st in stages:
            st_id = st.get("id", "")
            cur.execute(
                "INSERT OR REPLACE INTO study_map_stages VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    st_id,
                    sm_id,
                    st.get("number", 0),
                    st.get("title", ""),
                    st.get("status", ""),
                    st.get("estimate_minutes", 0),
                    1 if st.get("exam_critical") else 0,
                ),
            )
            for cid in st.get("concepts", []):
                cur.execute(
                    "INSERT OR IGNORE INTO stage_concepts VALUES (?, ?)",
                    (st_id, cid),
                )

    con.commit()


def build_catalog_sidecar(root: Path, target_path: Path | None = None) -> Path:
    """Compile the entire repository catalog into target SQLite database."""
    if target_path is None:
        target_path = root / ".derived" / "catalog.sqlite3"

    target_path.parent.mkdir(parents=True, exist_ok=True)
    if target_path.exists():
        target_path.unlink()

    repo = load_repo(root)
    con = init_catalog_db(str(target_path))
    try:
        compile_catalog(repo, con)
    finally:
        con.close()

    return target_path

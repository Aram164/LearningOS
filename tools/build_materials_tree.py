#!/usr/bin/env python3
"""Materials tree builder — physical topic layout + system compatibility.

Physical layout — the ADR-007 subject taxonomy (human browsing):
    materials/
      mathematics/{analysis,probability-statistics,proof-craft,general}/
      optimization/    machine-learning/{classical,rl}/
      ml-systems/      data-systems/    algorithms/{structures}/
      software/{python,languages,tooling}/
      method-admin/
      _unsorted/                                <- intake, stays
      .flat/                                    <- HIDDEN: source-<id> symlinks

System compatibility: the registry keeps id-based URIs
(material://source-<id>/...). `.flat/` holds one symlink per registered source
folder pointing to its physical location; the loader's materials_root prefers
`.flat/` when present, so every URI resolves unchanged. The physical position
of a folder is presentation only — move a folder = edit PLACEMENT below,
re-run this script.

The script is idempotent:
  1. ensures every mapped source folder sits at its mapped path (finds it at
     the materials root or any previous mapped location and moves it);
  2. rebuilds .flat/ from scratch;
  3. rebuilds a SOURCES.md in each module folder: what lives here + which
     shared Books/other sources belong to this module (Aram's "external
     source list in the module subfolder").

Usage:  python3 tools/build_materials_tree.py   (from LearningOS/repository/)
"""
import os
from pathlib import Path
import shutil, sys

REPO = Path(__file__).resolve().parents[1]
MATERIALS = REPO.parent / "materials"

# slug (= source id without "source-") -> physical parent dir.
#
# ADR-007: the tree IS the subject taxonomy. No path names an era, a module or
# a format — those are projections, not storage. The old layout mixed all three
# (Foundations/ = "from my bachelor's", ML/AML = this semester's module code,
# Books/ = format first), so the same subject lived in two places depending on
# when it arrived.
#
# Move a folder = edit this map and re-run. Every material://source-<id>/… URI
# resolves through .flat/, so no reference cares where a folder physically sits.
PLACEMENT = {
    # ---------------------------------------------- mathematics/analysis
    "abbott-understanding-analysis":     "mathematics/analysis",
    "ableitinger-musterloesungen":       "mathematics/analysis",
    "analysis-drill-blaetter-extern":    "mathematics/analysis",
    "analysis-grundlagen-handouts":      "mathematics/analysis",
    "analysis-klausuren-extern":         "mathematics/analysis",
    "analysis-skript":                   "mathematics/analysis",
    "deitmar-uebungsbuch":               "mathematics/analysis",
    "forster-wessoly":                   "mathematics/analysis",
    "fritzsche-trainingsbuch":           "mathematics/analysis",
    "grieser-analysis1":                 "mathematics/analysis",
    "lebl-basic-analysis":               "mathematics/analysis",
    "mfnf-analysis1":                    "mathematics/analysis",
    "mit-18100a":                        "mathematics/analysis",
    "ross-elementary-analysis":          "mathematics/analysis",
    "rudin-principles":                  "mathematics/analysis",
    "stewart-calculus":                  "mathematics/analysis",
    "strang-calculus":                   "mathematics/analysis",
    "thomas-calculus":                   "mathematics/analysis",
    # -------------------------------- mathematics/probability-statistics
    "blitzstein-hwang":                  "mathematics/probability-statistics",
    "dekking-mips":                      "mathematics/probability-statistics",
    "fahrmeir-arbeitsbuch":              "mathematics/probability-statistics",
    "fahrmeir-statistik":                "mathematics/probability-statistics",
    "fau-klausur-ws1415":                "mathematics/probability-statistics",
    "openintro-statistics":              "mathematics/probability-statistics",
    "pitman-probability":                "mathematics/probability-statistics",
    "ross-first-course":                 "mathematics/probability-statistics",
    "sad-2025-recordings":               "mathematics/probability-statistics",
    "sad-klausuren-extern":              "mathematics/probability-statistics",
    "sad-ss26-lectures":                 "mathematics/probability-statistics",
    "schaums-probability":               "mathematics/probability-statistics",
    "swanson-principles-probability":    "mathematics/probability-statistics",
    "tijms-understanding-probability":   "mathematics/probability-statistics",
    # ------------------------------------------- mathematics/proof-craft
    "ohlbach-eisinger-beweise":          "mathematics/proof-craft",
    "velleman-how-to-prove-it":          "mathematics/proof-craft",
    # ----------------------------------------------- mathematics/general
    "labs-schreyer-mathe-informatiker":  "mathematics/general",
    # ---------------------------------------- machine-learning/classical
    "aml-ss26-lectures":                 "machine-learning/classical",
    "cs229-notes":                       "machine-learning/classical",
    "cs4780-homeworks":                  "machine-learning/classical",
    "csc411-notes":                      "machine-learning/classical",
    "esl":                               "machine-learning/classical",
    "geron-handson":                     "machine-learning/classical",
    "islp":                              "machine-learning/classical",
    "kelleher-fmlpda":                   "machine-learning/classical",
    "kroese-dsml":                       "machine-learning/classical",
    "murphy-pml1":                       "machine-learning/classical",
    "zacharski-data-mining":             "machine-learning/classical",
    # ----------------------------------------------- machine-learning/rl
    "sutton-barto-rl":                   "machine-learning/rl",
    # -------------------------------------------------- ml-systems/scale
    "amls-ss26-lectures":                "ml-systems/scale",
    "huyen-dmls":                        "ml-systems/scale",
    "mlsysbook-vol1":                    "ml-systems/scale",
    "mlsysbook-vol2":                    "ml-systems/scale",
    # --------------------------------------------- algorithms/structures
    "algo2-frankfurt-klausuren":         "algorithms/structures",
    "clrs":                              "algorithms/structures",
    "dms-grundwerkzeuge":                "algorithms/structures",
    "kleinberg-tardos":                  "algorithms/structures",
    "ottmann-widmayer":                  "algorithms/structures",
    # --------------------------------------------------- software/python
    "automate-boring-stuff":             "software/python",
    "fluent-python":                     "software/python",
    "pydata-handbook":                   "software/python",
    "python-cheatsheets":                "software/python",
    "python-depth-drills":               "software/python",
    "slatkin-effective-python":          "software/python",
    # ------------------------------------------------ software/languages
    "comprehensive-rust":                "software/languages",
    "rust-book":                         "software/languages",
    # -------------------------------------------------- software/tooling
    "hu-git-intro":                      "software/tooling",
    "progit":                            "software/tooling",
    # ------------------------------------------------------ method-admin
    "stupo-2015":                        "method-admin",
}

# Cross-subject reading pointers for each folder's SOURCES.md.
#
# Deliberately empty since ADR-007. This map used to answer "which shared books
# matter for module X" and was keyed by module folder (ML/AML, Math/SaD) — a
# semester-shaped question baked into permanent storage. Now that every source
# sits with its subject, "what lives here" is the folder itself, and the
# module/stage view is a projection over sources rather than a physical artifact.
MODULE_REFS: dict[str, list[str]] = {}


def _titles() -> dict:
    """source id -> title, from the registry (best effort)."""
    try:
        import yaml
    except ImportError:
        return {}
    out = {}
    files = [REPO / "sources" / "sources.yaml"]
    files += sorted((REPO / "sources" / "registry").glob("*.yaml"))
    for f in files:
        if not f.exists():
            continue
        data = yaml.safe_load(f.read_text()) or {}
        for rec in data.get("sources", []) or []:
            out[rec.get("id", "")] = rec.get("title", "")
    return out


def find_current(slug: str):
    """Locate the source folder: mapped spot, materials root (flat), or scan."""
    mapped = MATERIALS / PLACEMENT[slug] / slug
    if mapped.is_dir() and not mapped.is_symlink():
        return mapped
    for cand in (MATERIALS / f"source-{slug}", MATERIALS / slug):
        if cand.is_dir() and not cand.is_symlink():
            return cand
    for p in MATERIALS.rglob(slug):
        if p.is_dir() and not p.is_symlink() and ".flat" not in p.parts:
            return p
    return None


def main() -> int:
    missing = []
    # 1 — place folders
    for slug, parent in PLACEMENT.items():
        target = MATERIALS / parent / slug
        cur = find_current(slug)
        if cur is None:
            missing.append(slug)
            continue
        if cur != target:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(cur), str(target))
    # 2 — rebuild .flat compat layer
    #
    # Refresh in place rather than rmtree-then-recreate. materials/ is routinely
    # reached through mounts that permit writes and renames but forbid unlink
    # (network shares, container bind mounts, sync clients); a hard rmtree turns
    # that into a crash *after* step 1 has already moved folders, leaving the
    # tree re-homed but every material:// URI dangling. os.replace over an
    # existing symlink is atomic and needs no delete permission.
    flat = MATERIALS / ".flat"
    flat.mkdir(exist_ok=True)
    wanted = set()
    for slug, parent in PLACEMENT.items():
        target = MATERIALS / parent / slug
        if not target.is_dir():
            continue
        link = flat / f"source-{slug}"
        wanted.add(link.name)
        staged = flat / f".{link.name}.new"
        staged.unlink(missing_ok=True) if staged.is_symlink() else None
        staged.symlink_to(Path("..") / parent / slug)
        os.replace(staged, link)
    stale = sorted(p.name for p in flat.iterdir()
                   if p.is_symlink() and p.name not in wanted)
    if stale:
        print(f"  NOTE {len(stale)} stale .flat symlink(s) no longer in PLACEMENT; "
              f"remove by hand: {', '.join(stale[:5])}"
              f"{' …' if len(stale) > 5 else ''}")
    # 3 — SOURCES.md in every subject folder
    #
    # "What lives here" is what makes the tree browsable with no tooling at all
    # (README: a text editor and Git are enough to operate this forever), so it
    # is generated for every subject folder in PLACEMENT. The old version also
    # printed "shared library that lives elsewhere" per MODULE_REFS — a
    # module-shaped list that ADR-007 moved into projections; that half is gone,
    # this half is not.
    titles = _titles()
    folders: dict[str, list[str]] = {}
    for slug, parent in PLACEMENT.items():
        folders.setdefault(parent, []).append(slug)
    for parent, slugs in sorted(folders.items()):
        fdir = MATERIALS / parent
        if not fdir.is_dir():
            continue
        present = [s for s in sorted(slugs) if (fdir / s).is_dir()]
        if not present:
            continue
        lines = [f"# {parent} — sources", "",
                 "_Generated by tools/build_materials_tree.py — do not edit._", "",
                 f"{len(present)} registered source(s) in this folder. "
                 "Cite them as `material://source-<id>/…`, never by this path — "
                 "the path is presentation, the id is identity.", ""]
        for slug in present:
            title = titles.get(f"source-{slug}", "")
            lines.append(f"- `{slug}/`" + (f" — {title}" if title else ""))
        (fdir / "SOURCES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    # 4 — report
    stray = [p.name for p in MATERIALS.iterdir()
             if p.is_dir() and p.name.startswith("source-")]
    print(f"placed: {len(PLACEMENT) - len(missing)}/{len(PLACEMENT)}; "
          f"flat links: {len(list(flat.iterdir()))}")
    for s in missing:
        print(f"  WARN no folder found for: {s}")
    for s in stray:
        print(f"  WARN unmapped stray at root: {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

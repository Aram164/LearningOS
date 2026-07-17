#!/usr/bin/env python3
"""Materials tree builder — physical topic layout + system compatibility.

Physical layout (human browsing, Aram's taxonomy):
    materials/
      ML/{AML,AMLS}/{course,practice-extern}/
      Math/{Analysis,SaD}/{course,practice-extern,handouts}/
      CS-Theory/Algo2/practice-extern/
      Books/{analysis,stats,ml,algorithms}/     <- shared library: one book,
                                                   one place, many modules
      Programming/{python,git,rust}/
      Degree/
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
from pathlib import Path
import shutil, sys

REPO = Path(__file__).resolve().parents[1]
MATERIALS = REPO.parent / "materials"

# slug (= source id without "source-") -> physical parent dir
PLACEMENT = {
    # ---------------------------------------------------------------- ML/AML
    "aml-ss26-lectures":            "ML/AML/course",
    "cs4780-homeworks":             "ML/AML/practice-extern",
    # --------------------------------------------------------------- ML/AMLS
    "amls-ss26-lectures":           "ML/AMLS/course",
    # ---------------------------------------------------------- Math/Analysis
    "analysis-skript":              "Math/Analysis/course",
    "analysis-klausuren-extern":    "Math/Analysis/practice-extern",
    "analysis-drill-blaetter-extern": "Math/Analysis/practice-extern",
    "analysis-grundlagen-handouts": "Math/Analysis/handouts",
    # --------------------------------------------------------------- Math/SaD
    "sad-ss26-lectures":            "Math/SaD/course",
    "sad-2025-recordings":          "Math/SaD/course",
    "sad-klausuren-extern":         "Math/SaD/practice-extern",
    "fau-klausur-ws1415":           "Math/SaD/practice-extern",
    # --------------------------------------------------------- CS-Theory/Algo2
    "algo2-frankfurt-klausuren":    "CS-Theory/Algo2/practice-extern",
    # ---------------------------------------------------------- Books/analysis
    "abbott-understanding-analysis": "Books/analysis",
    "ableitinger-musterloesungen":  "Books/analysis",
    "deitmar-uebungsbuch":          "Books/analysis",
    "forster-wessoly":              "Books/analysis",
    "fritzsche-trainingsbuch":      "Books/analysis",
    "grieser-analysis1":            "Books/analysis",
    "lebl-basic-analysis":          "Books/analysis",
    "strang-calculus":              "Books/analysis",
    "mit-18100a":                   "Books/analysis",
    "rudin-principles":             "Books/analysis",
    "ross-elementary-analysis":     "Books/analysis",
    "thomas-calculus":              "Books/analysis",
    "labs-schreyer-mathe-informatiker": "Books/analysis",
    "mfnf-analysis1":               "Books/analysis",
    "velleman-how-to-prove-it":     "Books/analysis",
    "ohlbach-eisinger-beweise":     "Books/analysis",
    # ------------------------------------------------------------- Books/stats
    "blitzstein-hwang":             "Books/stats",
    "dekking-mips":                 "Books/stats",
    "fahrmeir-arbeitsbuch":         "Books/stats",
    "fahrmeir-statistik":           "Books/stats",
    "kroese-dsml":                  "Books/stats",
    "openintro-statistics":         "Books/stats",
    "pitman-probability":           "Books/stats",
    "ross-first-course":            "Books/stats",
    "schaums-probability":          "Books/stats",
    "tijms-understanding-probability": "Books/stats",
    "swanson-principles-probability": "Books/stats",
    # ---------------------------------------------------------------- Books/ml
    "esl":                          "Books/ml",
    "islp":                         "Books/ml",
    "geron-handson":                "Books/ml",
    "kelleher-fmlpda":              "Books/ml",
    "murphy-pml1":                  "Books/ml",
    "sutton-barto-rl":              "Books/ml",
    "zacharski-data-mining":        "Books/ml",
    "cs229-notes":                  "Books/ml",
    "csc411-notes":                 "Books/ml",
    "huyen-dmls":                   "Books/ml",
    "mlsysbook-vol1":               "Books/ml",
    "mlsysbook-vol2":               "Books/ml",
    # -------------------------------------------------------- Books/algorithms
    "dms-grundwerkzeuge":           "Books/algorithms",  # Dietzfelbinger/Mehlhorn/Sanders
    "clrs":                         "Books/algorithms",
    "ottmann-widmayer":             "Books/algorithms",
    "kleinberg-tardos":             "Books/algorithms",
    # ------------------------------------------------------------- Programming
    "fluent-python":                "Programming/python",
    "automate-boring-stuff":        "Programming/python",
    "pydata-handbook":              "Programming/python",
    "python-cheatsheets":           "Programming/python",
    "progit":                       "Programming/git",
    "hu-git-intro":                 "Programming/git",
    "rust-book":                    "Programming/rust",
    "comprehensive-rust":           "Programming/rust",
    # ------------------------------------------------------------------ Degree
    "stupo-2015":                   "Degree",
}

# module folder -> slugs of shared/elsewhere sources relevant to it
MODULE_REFS = {
    "ML/AML": ["esl", "islp", "geron-handson", "kelleher-fmlpda", "murphy-pml1",
               "sutton-barto-rl", "zacharski-data-mining", "cs229-notes",
               "csc411-notes"],
    "ML/AMLS": ["mlsysbook-vol1", "mlsysbook-vol2", "huyen-dmls"],
    "Math/Analysis": ["abbott-understanding-analysis", "ableitinger-musterloesungen",
                      "deitmar-uebungsbuch", "forster-wessoly", "fritzsche-trainingsbuch",
                      "grieser-analysis1", "lebl-basic-analysis", "strang-calculus",
                      "mit-18100a", "rudin-principles", "ross-elementary-analysis",
                      "thomas-calculus", "labs-schreyer-mathe-informatiker",
                      "mfnf-analysis1", "velleman-how-to-prove-it",
                      "ohlbach-eisinger-beweise"],
    "Math/SaD": ["blitzstein-hwang", "dekking-mips",
                 "fahrmeir-arbeitsbuch", "fahrmeir-statistik", "kroese-dsml",
                 "openintro-statistics", "pitman-probability", "ross-first-course",
                 "schaums-probability", "tijms-understanding-probability",
                 "swanson-principles-probability"],
    "CS-Theory/Algo2": ["clrs", "ottmann-widmayer", "kleinberg-tardos",
                        "dms-grundwerkzeuge"],
}


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
    flat = MATERIALS / ".flat"
    if flat.exists():
        shutil.rmtree(flat)
    flat.mkdir()
    for slug, parent in PLACEMENT.items():
        target = MATERIALS / parent / slug
        if target.is_dir():
            (flat / f"source-{slug}").symlink_to(Path("..") / parent / slug)
    # 3 — SOURCES.md per module folder
    titles = _titles()
    for module, refs in MODULE_REFS.items():
        mdir = MATERIALS / module
        if not mdir.is_dir():
            continue
        lines = [f"# {module.split('/')[-1]} — sources", "",
                 "_Generated by tools/build_materials_tree.py — do not edit._", "",
                 "## In this folder", ""]
        for sub in sorted(p for p in mdir.iterdir() if p.is_dir()):
            for src in sorted(p for p in sub.iterdir() if p.is_dir()):
                t = titles.get(f"source-{src.name}", "")
                lines.append(f"- `{sub.name}/{src.name}/`" + (f" — {t}" if t else ""))
        lines += ["", "## Shared library (lives elsewhere)", ""]
        for slug in refs:
            rel = Path(*[".."] * len(module.split("/"))) / PLACEMENT[slug] / slug
            t = titles.get(f"source-{slug}", slug)
            lines.append(f"- [{t}]({rel.as_posix()})")
        (mdir / "SOURCES.md").write_text("\n".join(lines) + "\n")
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

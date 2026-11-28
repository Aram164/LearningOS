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

Usage:  python3 tools/build_materials_tree.py [--apply]   (from LearningOS/repository/)

The bare command prints the plan and changes nothing: the materials tree has
no git history, so moves happen only with an explicit --apply.
"""
import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from learning_os.store.contracts.write_scopes import (  # noqa: E402
    WriteScopeError,
    guard_tool_output_path,
    path_segment,
    relative_path,
)
from learning_os.store.fs import atomic_write_text_exclusive, rename_noreplace  # noqa: E402

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
    "mml":                               "machine-learning/classical",
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
    "polars-definitive-guide":          "software/python",
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
    # ------------------------------- registered from Foundations/ (ADR-007 step 3)
    "algo2-hu-materials":                "algorithms/structures",
    "kleppmann-ddia":                    "data-systems/databases",
    "compiler-construction-shelf":       "software/languages",
    "cs-classics-shelf":                 "software/engineering",
    "git-handbook-archive":              "software/tooling",
    "scalable-dataframe-systems-paper":  "data-systems/architecture",
    "stratum-paper":                     "data-systems/architecture",
    "lineare-algebra-archive":           "mathematics/linear-algebra",
    "marsland-ml-algorithmic":           "machine-learning/classical",
    "mathe-vorkurse":                    "mathematics/general",
    "programming-language-books":        "software/languages",
    "systems-architecture-shelf":        "data-systems/architecture",
    "bs-hu-prior-slides":               "data-systems/architecture",
    "icop-hu-ws2627":                   "algorithms/structures",
    "blum-algorithmen-datenstrukturen":  "algorithms/structures",
    "korte-vygen":                      "optimization",
    "theoinfo-hu-archive":               "algorithms/complexity",
    "vorkurs-mathe-2022":                "mathematics/general",

    # ------------------------------------------- video sources (2026-09-11)
    #
    # Added when transcripts gave video a material layer for the first time
    # (tools/ingest_transcript.py). These folders hold `transcript/<id>.md`,
    # not the videos themselves: the captions are the addressable artifact,
    # the bytes are not ours and are not worth 2 GB of tree.
    #
    # Placement follows the source's subject exactly as a book's does — ADR-007
    # makes the tree the taxonomy, so a lecture series on linear algebra sits
    # beside the linear-algebra books, not in a "videos" bucket.
    "reducible-fft":                       "algorithms/complexity",
    "fiset-graph-theory":                  "algorithms/structures",
    "kit-algorithmen2":                    "algorithms/structures",
    "3b1b-neural-networks":                "machine-learning/classical",
    "cs229-2022-videos":                   "machine-learning/classical",
    "cs231n-2017-videos":                  "machine-learning/classical",
    "cs4780":                              "machine-learning/classical",
    "data-school-sklearn":                 "machine-learning/classical",
    "eecs498":                             "machine-learning/classical",
    "hinton-nnml":                         "machine-learning/classical",
    "karpathy-micrograd":                  "machine-learning/classical",
    "mit-6s191":                           "machine-learning/classical",
    "patrick-loeber-pytorch-cnn":          "machine-learning/classical",
    "3b1b-essence-of-calculus":            "mathematics/analysis",
    "henning-dierks":                      "mathematics/analysis",
    "professor-leonard":                   "mathematics/analysis",
    "wrath-of-math":                       "mathematics/analysis",
    "3b1b-linear-algebra":                 "mathematics/linear-algebra",
    "3b1b-bayes-theorem":                  "mathematics/probability-statistics",
    "brandon-foltz":                       "mathematics/probability-statistics",
    "jbstatistics":                        "mathematics/probability-statistics",
    "kurzes-tutorium-statistik":           "mathematics/probability-statistics",
    "statquest":                           "mathematics/probability-statistics",
    "zedstatistics":                       "mathematics/probability-statistics",
    "corey-schafer-oop":                   "software/python",
    "guo-cpython-internals":               "software/python",
    "hettinger-class-toolkit":             "software/python",
    "powell-python-expert":                "software/python",
}

# Cross-subject reading pointers for each folder's SOURCES.md.
#
# Deliberately empty since ADR-007. This map used to answer "which shared books
# matter for module X" and was keyed by module folder (ML/AML, Math/SaD) — a
# semester-shaped question baked into permanent storage. Now that every source
# sits with its subject, "what lives here" is the folder itself, and the
# module/stage view is a projection over sources rather than a physical artifact.
MODULE_REFS: dict[str, list[str]] = {}


def _titles(repo: Path) -> dict:
    """source id -> title, from the registry (best effort)."""
    try:
        import yaml
    except ImportError:
        return {}
    out = {}
    files = [repo / "sources" / "sources.yaml"]
    files += sorted((repo / "sources" / "registry").glob("*.yaml"))
    for f in files:
        if not f.exists():
            continue
        data = yaml.safe_load(f.read_text()) or {}
        for rec in data.get("sources", []) or []:
            out[rec.get("id", "")] = rec.get("title", "")
    return out


def find_current(slug: str, materials: Path):
    """Locate the source folder: mapped spot, materials root (flat), or scan."""
    mapped = materials / PLACEMENT[slug] / slug
    if mapped.is_dir() and not mapped.is_symlink():
        return mapped
    for cand in (materials / f"source-{slug}", materials / slug):
        if cand.is_dir() and not cand.is_symlink():
            return cand
    if not materials.is_dir() or materials.is_symlink():
        return None
    for dirpath, dirnames, _ in os.walk(materials, followlinks=False):
        current = Path(dirpath)
        next_dirs: list[str] = []
        for name in sorted(dirnames):
            candidate = current / name
            if name == ".flat" or candidate.is_symlink():
                continue
            if name == slug:
                return candidate
            next_dirs.append(name)
        dirnames[:] = next_dirs
    return None


def _competing_location(slug: str, materials: Path, target: Path) -> Path | None:
    """A live folder other than ``target`` that already claims ``slug`` (2D, CL-11).

    The existing ``.flat`` alias names where the registered folder is now,
    and a root-level folder is the pre-tree layout. When either is a live
    directory and something else already sits at the mapped place, adopting
    that occupant would repoint every ``material://source-<slug>/`` URI to it
    and strand the registered folder. ``find_current`` cannot tell the two
    apart, so ``_run`` asks here first.
    """
    link = materials / ".flat" / f"source-{slug}"
    candidates: list[Path] = []
    if link.is_symlink():
        candidates.append(link.parent / link.readlink())
    candidates += [
        cand for cand in (materials / f"source-{slug}", materials / slug)
        if not cand.is_symlink()
    ]
    resolved_target = os.path.realpath(target)
    for cand in candidates:
        if cand.is_dir() and os.path.realpath(cand) != resolved_target:
            return Path(os.path.normpath(cand))
    return None


def _stray_roots(materials: Path) -> list[str]:
    return sorted(p.name for p in materials.iterdir()
                  if p.is_dir() and p.name.startswith("source-"))


def _print_plan(materials: Path, moves: list, missing: list[str]) -> None:
    """The --apply preview. Read-only: no mkdir, move, link, or write."""
    print(f"plan for {materials} (dry run — pass --apply to act):")
    if moves:
        print(f"  moves ({len(moves)}):")
        for _slug, cur, target in sorted(moves):
            print(f"    {cur.relative_to(materials)} -> "
                  f"{target.relative_to(materials)}")
    else:
        print("  moves (0)")
    moved_slugs = {slug for slug, _, _ in moves}
    link_count = sum(
        1 for slug, parent in PLACEMENT.items()
        if slug not in missing
        and ((materials / parent / slug).is_dir() or slug in moved_slugs))
    flat = materials / ".flat"
    have = len(list(flat.iterdir())) if flat.is_dir() else 0
    print(f"  .flat links: {link_count} wanted ({have} present)")
    folders: dict[str, list[str]] = {}
    for slug, parent in PLACEMENT.items():
        folders.setdefault(parent, []).append(slug)
    rewrites = 0
    for parent, slugs in sorted(folders.items()):
        fdir = materials / parent
        present = [s for s in sorted(slugs)
                   if (fdir / s).is_dir() or s in moved_slugs]
        if fdir.is_dir() or any(s in moved_slugs for s in slugs):
            if present:
                rewrites += 1
    print(f"  SOURCES.md files to (re)write: {rewrites}")
    for s in missing:
        print(f"  WARN no folder found for: {s}")
    for s in _stray_roots(materials):
        print(f"  WARN unmapped stray at root: {s}")


def _undo_moves(done: list[tuple[Path, Path]]) -> int:
    """Restore already-moved folders without overwriting a reoccupied source."""
    stuck = []
    for cur, target in reversed(done):
        try:
            rename_noreplace(
                guard_tool_output_path(target, allow_existing_dir=True),
                guard_tool_output_path(cur),
            )
        except (OSError, WriteScopeError) as exc:
            stuck.append(f"{target} (belongs at {cur}): {exc}")
    if stuck:
        print("apply stopped; these folders could not be moved back — move them "
              "by hand: " + "; ".join(stuck), file=sys.stderr)
    elif done:
        print(f"apply stopped; moved {len(done)} folder(s) back",
              file=sys.stderr)
    else:
        print("apply stopped before any move", file=sys.stderr)
    return 1


def _refresh_aliases(materials: Path, flat: Path) -> set[str]:
    """Stage every alias and its predecessor before publishing any replacement."""
    if flat.is_symlink() or (flat.exists() and not flat.is_dir()):
        raise FileExistsError(f"refusing a non-directory alias root: {flat}")
    new_flat = not flat.is_dir()
    stage = Path(tempfile.mkdtemp(prefix=".flat-tmp-", dir=materials if new_flat else flat))
    wanted = set()
    prepared: list[tuple[Path, Path, Path | None]] = []
    published: list[tuple[Path, Path | None]] = []
    remove_stage = True
    try:
        for slug, parent in PLACEMENT.items():
            target = materials / relative_path(parent) / path_segment(slug)
            if not target.is_dir() or target.is_symlink():
                continue
            link = flat / f"source-{path_segment(slug)}"
            wanted.add(link.name)
            desired = Path("..") / parent / slug
            staged = stage / link.name
            if new_flat:
                staged.symlink_to(desired)
                continue
            previous = None
            if link.is_symlink():
                old_target = link.readlink()
                if old_target == desired:
                    continue
                previous = stage / f"previous-{link.name}"
                previous.symlink_to(old_target)
            elif link.exists():
                raise FileExistsError(f"refusing to replace a non-symlink alias: {link}")
            staged.symlink_to(desired)
            prepared.append((staged, link, previous))

        if new_flat:
            rename_noreplace(stage, flat)
            remove_stage = False

        for staged, link, previous in prepared:
            if previous is None:
                rename_noreplace(staged, link)
            else:
                if not link.is_symlink() or link.readlink() != previous.readlink():
                    raise FileExistsError(f"alias changed during layout apply: {link}")
                os.replace(staged, link)
            published.append((link, previous))
    except OSError as exc:
        failed = []
        for link, previous in reversed(published):
            try:
                if previous is None:
                    link.unlink()
                else:
                    os.replace(previous, link)
            except OSError as restore_error:
                failed.append(f"{link}: {restore_error}")
        if failed:
            remove_stage = False
            raise OSError(f"{exc}; could not restore aliases from {stage}: "
                          + "; ".join(failed)) from exc
        raise
    finally:
        if remove_stage:
            shutil.rmtree(stage, ignore_errors=True)
    return wanted


def _run(materials: Path, *, apply: bool) -> int:
    if not materials.is_dir():
        print(f"materials tree not found: {materials}", file=sys.stderr)
        return 1
    moves = []
    missing = []
    occupied = []
    for slug, parent in PLACEMENT.items():
        target = materials / relative_path(parent) / path_segment(slug)
        cur = find_current(slug, materials)
        if cur is None:
            missing.append(slug)
            continue
        if cur == target:
            registered = _competing_location(slug, materials, target)
            if registered is not None:
                occupied.append((target, registered))
            continue
        moves.append((slug, cur, target))
    if occupied:
        # Refuse before any move or alias change, in the plan run too: the
        # mapped place holds a folder that is not the registered one.
        for target, registered in occupied:
            print(f"refusing an occupied destination: {target} already exists, but "
                  f"the registered folder is {registered}; move one of them aside "
                  f"by hand, then re-run", file=sys.stderr)
        return 1
    if not apply:
        _print_plan(materials, moves, missing)
        return 0
    # 1 — preflight targets & place folders
    flat = materials / ".flat"
    if flat.is_symlink():
        print(f"refusing .flat symlink: {flat}", file=sys.stderr)
        return 1
    for _slug, cur, target in moves:
        if target.exists() or target.is_symlink():
            print(f"refusing move collision at {target} (already exists)", file=sys.stderr)
            return 1
        try:
            guard_tool_output_path(cur, allow_existing_dir=True)
            guard_tool_output_path(target)
        except WriteScopeError as exc:
            print(f"refusing move {cur} -> {target}: {exc}", file=sys.stderr)
            return 1
    done: list[tuple[Path, Path]] = []
    try:
        for _slug, cur, target in moves:
            target.parent.mkdir(parents=True, exist_ok=True)
            # Recheck both operands at the move. The rename refuses any late occupant.
            rename_noreplace(
                guard_tool_output_path(cur, allow_existing_dir=True),
                guard_tool_output_path(target),
            )
            done.append((cur, target))
        wanted = _refresh_aliases(materials, flat)
    except (OSError, WriteScopeError) as exc:
        print(f"cannot apply materials layout: {exc}", file=sys.stderr)
        return _undo_moves(done)
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
    titles = _titles(REPO)
    folders: dict[str, list[str]] = {}
    for slug, parent in PLACEMENT.items():
        folders.setdefault(parent, []).append(slug)
    for parent, slugs in sorted(folders.items()):
        fdir = materials / relative_path(parent)
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
        atomic_write_text_exclusive(
            fdir / "SOURCES.md",
            "\n".join(lines) + "\n",
            boundary=materials.resolve(),
            durable=False,
            error_factory=OSError,
        )
    # 4 — report
    print(f"placed: {len(PLACEMENT) - len(missing)}/{len(PLACEMENT)}; "
          f"flat links: {len(list(flat.iterdir()))}")
    for s in missing:
        print(f"  WARN no folder found for: {s}")
    for s in _stray_roots(materials):
        print(f"  WARN unmapped stray at root: {s}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """The tool's CLI surface (SPEC §7.4, PLAN D11)."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--apply", action="store_true",
        help="perform the moves and rewrites; without it, print the plan "
             "and change nothing")
    parser.add_argument(
        "--materials-root", type=Path, default=MATERIALS,
        help="materials tree to maintain (default: the sibling materials/ tree)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        # A caller-chosen tree must never be canonical data or a symlink path.
        materials_root = guard_tool_output_path(args.materials_root, allow_existing_dir=True)
    except WriteScopeError as exc:
        print(f"refusing --materials-root: {exc}", file=sys.stderr)
        return 2
    return _run(materials_root, apply=args.apply)


if __name__ == "__main__":
    sys.exit(main())

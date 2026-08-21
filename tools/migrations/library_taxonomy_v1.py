#!/usr/bin/env python3
"""ADR-007 steps 2–3: eight subject groups, and every source tagged into them.

    python tools/migrations/library_taxonomy_v1.py            # dry run (default)
    python tools/migrations/library_taxonomy_v1.py --apply

Idempotent: rerunning after --apply reports 0 actions.

WHY LINE-SURGERY RATHER THAN A YAML ROUND-TRIP
----------------------------------------------
The source registries carry 96 hand-written comments and every collection is
headed by curation provenance ("Migrated from legacy LEARNING-RESOURCES.md §3,
KW 24 curation"). ``yaml.safe_dump`` would silently delete all of it. Records are
uniformly shaped — ``  - id: source-x`` with fields at four spaces and
``thematic_group_ids`` written as a one-line flow sequence — so a single-line
replace/insert per record is both sufficient and provably non-destructive:
everything outside the touched lines stays byte-identical.

GROUP ID RENAMES
----------------
``cs-theory`` → ``algorithms`` and ``programming-languages`` → ``software``,
because both titles changed meaning under ADR-007 (CS Theory → Algorithms &
Computation; Programming Languages → Software & Languages). Keeping an id that
contradicts its own title is the drift this ADR exists to remove.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
G = "thematic-group-"

RENAMES = {f"{G}cs-theory": f"{G}algorithms",
           f"{G}programming-languages": f"{G}software"}

GROUPS = [
    ("mathematics", "Mathematics", 10,
     "Probability and statistics, analysis and calculus, linear algebra, "
     "discrete mathematics and proof craft."),
    ("optimization", "Optimization & Learning Theory", 20,
     "Convex, numerical and combinatorial optimization; statistical learning "
     "theory and kernel methods — the bridge between mathematics and learning."),
    ("machine-learning", "Machine Learning", 30,
     "Statistical and classical ML, deep learning, reinforcement learning, "
     "vision, and intuition-building explainers."),
    ("ml-systems", "ML Systems", 40,
     "Training and serving at scale, ML compilation, performance and "
     "parallelism, and data management for ML."),
    ("data-systems", "Data Systems", 50,
     "Databases, distributed systems, provenance and lineage, reliability and "
     "benchmarking."),
    ("algorithms", "Algorithms & Computation", 60,
     "Algorithms and data structures, complexity and computability, "
     "parameterized and approximation algorithms, experimental algorithmics."),
    ("software", "Software & Languages", 70,
     "Python craft and idiom, CPython internals, software engineering "
     "practice, languages and compilers, tooling and environment."),
    ("method-admin", "Method & Administration", 80,
     "Research method, degree regulations, and dataset catalogues — small, but "
     "everything needs a home or it becomes invisible."),
]

# Shelf → default groups. The three mixed shelves are resolved per source below.
SHELF_DEFAULTS = {
    "algorithms-bookshelf": ["algorithms"],
    "algorithms-lecture-series": ["algorithms"],
    "math-bookshelf": ["mathematics"],
    "math-lecture-series": ["mathematics"],
    "ml-bookshelf": ["machine-learning"],
    "ml-broaden-later": ["machine-learning"],
    "ml-explainers": ["machine-learning"],
    "ml-lecture-series": ["machine-learning"],
    "ml-systems-bookshelf": ["ml-systems"],
    "ml-systems-lecture-series": ["ml-systems"],
    "programming-bookshelf": ["software"],
    "programming-video-courses": ["software"],
    "python-internals-shelf": ["software"],
}

COLLECTION_GROUPS = dict(SHELF_DEFAULTS, **{
    "exam-practice-banks": ["mathematics", "machine-learning", "algorithms"],
    "papers-shelf": ["machine-learning", "data-systems"],
    "project-toolbox": ["machine-learning", "software", "data-systems"],
})

# Explicit calls: unshelved sources plus everything on a mixed shelf.
OVERRIDES: dict[str, list[str]] = {
    # — Optimization & Learning Theory: the cluster that was triple-tagged —
    "source-boyd-convex-optimization": ["optimization", "mathematics"],
    "source-nocedal-wright": ["optimization", "mathematics"],
    "source-bertsimas-tsitsiklis-lp": ["optimization", "algorithms"],
    "source-korte-vygen": ["optimization", "algorithms"],
    "source-schrijver-combinatorial-notes": ["optimization", "algorithms"],
    "source-williamson-shmoys": ["optimization", "algorithms"],
    "source-toussaint-optimization-script": ["optimization", "machine-learning"],
    "source-mohri-foundations-ml": ["optimization", "machine-learning"],
    "source-ssbd-understanding-ml": ["optimization", "machine-learning"],
    "source-schoelkopf-smola-lwk": ["optimization", "machine-learning"],
    "source-mueller-kernel-tutorial": ["optimization", "machine-learning"],
    "source-mit-18657": ["optimization", "mathematics"],
    "source-vershynin-hdp": ["mathematics", "optimization"],
    # — ML Systems —
    "source-cmu-10414": ["ml-systems", "machine-learning"],
    "source-mit-6172": ["ml-systems", "algorithms"],
    "source-stanford-cs149": ["ml-systems"],
    "source-gpu-mode-lectures": ["ml-systems"],
    "source-kirk-hwu-pmpp": ["ml-systems", "software"],
    "source-mlsysbook-vol1": ["ml-systems"],
    "source-mlsysbook-vol2": ["ml-systems"],
    "source-amls-prior-archives": ["ml-systems"],
    "source-mlinspect-debugging": ["ml-systems", "data-systems"],
    # — Data Systems —
    "source-cmu-15445": ["data-systems"],
    "source-mit-6824": ["data-systems"],
    "source-redbook": ["data-systems"],
    "source-kleppmann-ddia": ["data-systems", "software"],
    "source-google-sre-book": ["data-systems"],
    "source-jain-performance-analysis": ["data-systems"],
    "source-hogan-knowledge-graphs": ["data-systems"],
    "source-bermbach-csb": ["data-systems"],
    "source-abedjan-data-profiling": ["data-systems"],
    "source-duckdb-python-docs": ["data-systems", "software"],
    "source-buneman-why-where": ["data-systems"],
    # — Algorithms & Computation —
    "source-arora-barak": ["algorithms"],
    "source-cygan-parameterized": ["algorithms"],
    "source-mcgeoch-experimental-algorithmics": ["algorithms"],
    "source-mit-6006": ["algorithms"],
    "source-mit-6046j": ["algorithms"],
    "source-frankfurt-algo2-course": ["algorithms"],
    "source-algo2-frankfurt-klausuren": ["algorithms"],
    "source-mitzenmacher-upfal": ["mathematics", "algorithms"],
    # — Mathematics —
    **{sid: ["mathematics"] for sid in (
        "source-ableitinger-musterloesungen", "source-analysis-drill-blaetter-extern",
        "source-analysis-grundlagen-handouts", "source-analysis-klausuren-extern",
        "source-analysis-skript", "source-deitmar-uebungsbuch",
        "source-forster-wessoly", "source-fritzsche-trainingsbuch",
        "source-grieser-analysis1", "source-mit-18100a", "source-stewart-calculus",
        "source-swanson-principles-probability", "source-dekking-mips",
        "source-fahrmeir-arbeitsbuch", "source-fau-klausur-ws1415", "source-mit-1805",
        "source-ross-first-course", "source-schaums-probability", "source-stat110",
        "source-gallager-stochastic-processes", "source-papoulis-pillai",
        "source-sad-ss26-lectures", "source-sad-uebungen",
        "source-sad-klausuren-extern")},
    # — Machine Learning —
    **{sid: ["machine-learning"] for sid in (
        "source-aml-ss26-lectures", "source-d2l", "source-prince-udl",
        "source-geron-handson", "source-ng-coursera", "source-mit-6036",
        "source-cs229-problem-sets", "source-cs4780-homeworks", "source-caltech-lfd",
        "source-islp-community-solutions", "source-augmix", "source-grad-cam",
        "source-zeiler-fergus-occlusion", "source-belkin-double-descent",
        "source-pouyanfar-dl-survey", "source-mit-6034-quizzes",
        "source-berkeley-cs189")},
    # — Software & Languages —
    **{sid: ["software"] for sid in (
        "source-beazley-generator-tricks", "source-beazley-python-distilled",
        "source-coghlan-import-traps", "source-hettinger-class-toolkit",
        "source-hunner-iterator-protocol", "source-hypothesis-docs",
        "source-powell-python-expert", "source-pytest-docs",
        "source-rhodes-python-patterns", "source-viafore-robust-python",
        "source-python-depth-drills", "source-docker-get-started")},
    "source-cosmicpython-architecture-patterns": ["software", "data-systems"],
    "source-pierce-tapl": ["software", "algorithms"],
    "source-software-foundations": ["software", "algorithms"],
    "source-cornell-cs6120": ["software", "algorithms"],
    # ML tooling: reached for while doing ML, but it is software
    **{sid: ["machine-learning", "software"] for sid in (
        "source-pytorch-tutorials", "source-sklearn-user-guide",
        "source-torchvision-transforms-docs", "source-albumentations-docs",
        "source-timm", "source-captum", "source-fairlearn-docs",
        "source-google-colab")},
    # — Method & Administration —
    **{sid: ["method-admin"] for sid in (
        "source-prisma-method", "source-stupo-2015", "source-google-dataset-search",
        "source-kaggle-datasets", "source-data-gov", "source-awesome-ml-books")},
    "source-cs229-project-archive": ["method-admin", "machine-learning"],
}

ID_RE = re.compile(r"^(\s*)- id: (['\"]?)(source-[a-z0-9-]+)\2\s*$")
TG_RE = re.compile(r"^(\s*)thematic_group_ids:")
#: `thematic_group_ids` appears in BOTH styles in these registries — 36 records
#: use a block sequence and 13 use a flow sequence. Replacing only the key line
#: orphans the block's children into the next field and silently drops records
#: (this cost 58 of 228 sources on the first run). Always consume the whole block.
BLOCK_ITEM_RE = re.compile(r"^(\s*)- \S")


def groups_line(indent: str, names: list[str]) -> str:
    ids = ", ".join(G + n for n in names)
    return f"{indent}thematic_group_ids: [{ids}]\n"


def retag_registry(path: Path, assignment: dict[str, list[str]]) -> tuple[str, int]:
    """Replace or insert one thematic_group_ids line per source record."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    out: list[str] = []
    changed = 0
    i = 0
    while i < len(lines):
        match = ID_RE.match(lines[i])
        if not match:
            out.append(lines[i])
            i += 1
            continue

        list_indent, sid = match.group(1), match.group(3)
        field_indent = list_indent + "  "
        # The record runs until the next list item at the same indent, or EOF.
        end = i + 1
        while end < len(lines) and not ID_RE.match(lines[end]):
            if lines[end].strip() and not lines[end].startswith(field_indent):
                break
            end += 1

        record = lines[i:end]
        want = assignment.get(sid)
        if want:
            new_line = groups_line(field_indent, want)
            existing = [k for k, line in enumerate(record) if TG_RE.match(line)]
            if existing:
                start = existing[0]
                key_indent = len(TG_RE.match(record[start]).group(1))
                stop = start + 1
                while stop < len(record):
                    item = BLOCK_ITEM_RE.match(record[stop])
                    if not item or len(item.group(1)) <= key_indent:
                        break
                    stop += 1
                if record[start:stop] != [new_line]:
                    record[start:stop] = [new_line]
                    changed += 1
            else:
                record.insert(1, new_line)
                changed += 1
        out.extend(record)
        i = end
    return "".join(out), changed


def rename_group_ids(text: str) -> tuple[str, int]:
    total = 0
    for old, new in RENAMES.items():
        # Word-boundary guard so -cs-theory does not match inside another id.
        pattern = re.compile(re.escape(old) + r"(?![a-z0-9-])")
        text, n = pattern.subn(new, text)
        total += n
    return text, total


def render_groups_registry() -> str:
    lines = ["# The subject taxonomy (ADR-007). Groups are chosen to stay true for a\n",
             "# decade, not a semester: no group names an era, a module or a format.\n",
             "# Subgroups live in the shelves under sources/collections/.\n",
             "thematic_groups:\n"]
    for name, title, order, description in GROUPS:
        lines += [f"  - id: {G}{name}\n",
                  f"    title: {title}\n",
                  "    description: >-\n"]
        words, line = description.split(), "     "
        for word in words:
            if len(line) + len(word) + 1 > 76:
                lines.append(line + "\n")
                line = "     "
            line += " " + word
        lines.append(line + "\n")
        lines.append(f"    order: {order}\n")
    return "".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    from learning_os.loader import load_repo

    repo = load_repo(ROOT)
    shelf_of: dict[str, list[str]] = {}
    for cid, coll in repo.collections.items():
        data = coll.data if hasattr(coll, "data") else coll
        for entry in (data.get("entries") or []):
            if entry.get("source"):
                shelf_of.setdefault(entry["source"], []).append(cid)

    assignment: dict[str, list[str]] = {}
    unassigned: list[str] = []
    for sid in repo.sources:
        if sid in OVERRIDES:
            assignment[sid] = OVERRIDES[sid]
            continue
        groups: list[str] = []
        for shelf in shelf_of.get(sid, []):
            for name in SHELF_DEFAULTS.get(shelf, []):
                if name not in groups:
                    groups.append(name)
        if groups:
            assignment[sid] = groups
        else:
            unassigned.append(sid)

    actions = 0
    for path in sorted((ROOT / "sources").rglob("*.yaml")):
        original = path.read_text(encoding="utf-8")
        text, changed = (retag_registry(path, assignment)
                         if "collections" not in path.parts else (original, 0))
        if "collections" in path.parts:
            cid = path.stem
            want = COLLECTION_GROUPS.get(cid)
            if want:
                block = "thematic_group_ids:\n" + "".join(
                    f"  - {G}{n}\n" for n in want)
                text = re.sub(r"thematic_group_ids:\n(?:  - [^\n]*\n)+", block, text)
                if text != original:
                    changed += 1
        text, renamed = rename_group_ids(text)
        changed += renamed
        if text != original:
            actions += 1
            print(f"  {'wrote' if args.apply else 'would write'} "
                  f"{path.relative_to(ROOT)} ({changed} edit(s))")
            if args.apply:
                path.write_text(text, encoding="utf-8")

    registry = ROOT / "curriculum" / "thematic-groups.yaml"
    rendered = render_groups_registry()
    if registry.read_text(encoding="utf-8") != rendered:
        actions += 1
        print(f"  {'wrote' if args.apply else 'would write'} "
              f"{registry.relative_to(ROOT)} (8 groups)")
        if args.apply:
            registry.write_text(rendered, encoding="utf-8")

    for tree in ("curriculum", "projects", "knowledge", "work", "records"):
        for path in sorted((ROOT / tree).rglob("*")):
            if path.suffix not in {".yaml", ".yml", ".md"} or not path.is_file():
                continue
            if path == registry:
                continue
            original = path.read_text(encoding="utf-8")
            text, renamed = rename_group_ids(original)
            if renamed:
                actions += 1
                print(f"  {'wrote' if args.apply else 'would write'} "
                      f"{path.relative_to(ROOT)} ({renamed} id rename(s))")
                if args.apply:
                    path.write_text(text, encoding="utf-8")

    print(f"\n{'applied' if args.apply else 'dry-run'}: {actions} action(s); "
          f"{len(assignment)}/{len(repo.sources)} sources assigned")
    if unassigned:
        print(f"\n{len(unassigned)} source(s) reached no rule — assign explicitly:")
        for sid in sorted(unassigned):
            print(f"  {sid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

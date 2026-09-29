"""Paths, domain ordering and the skip/label tables the catalogue is built from."""

from __future__ import annotations

import re
import sys
from pathlib import Path

# One level deeper than the original script, so climb an extra parent.
TOOLS = Path(__file__).resolve().parent.parent


REPO = TOOLS.parent                      # LearningOS/repository


MATERIALS = REPO.parent / "materials"    # LearningOS/materials


HTML_ENABLED = "--html" in sys.argv


SOURCES = REPO / "sources"


SKIP_DIRS = {".flat", ".git", "__pycache__"}


SKIP_FILES = {".DS_Store", "INDEX.html", "README.md", "FILES.txt"}


HARD_SUPPORT_EXT = {"css", "js", "mjs", "cjs", "mts", "map", "scss", "sass",
                    "less", "woff", "woff2", "ttf", "otf", "eot", "ico", "sample"}


ASSET_DIRS = {"assets", "static", "_static", "_files", "fonts", "font", "css",
              "js", "img", "images", "_resources", "static_shared"}


ARCHIVE_RE = re.compile(r"(older|archive|deprecated|superseded|backup|previous"
                        r"|(?:^|[-_])old(?:[-_]|$))", re.I)


TYPE_LABEL = {"lecture": "Lecture", "book": "Book", "course": "Course",
              "paper": "Paper", "website": "Website", "video": "Video",
              "software": "Software", "documentation": "Docs", "other": "Other"}


DOMAIN_LABELS = {
    "ML": ("Machine Learning", "Machine-learning course materials, papers, notes"),
    "Math": ("Mathematics", "Mathematics — analysis, probability & statistics, drill"),
    "CS-Theory": ("CS Theory", "Algorithms & CS theory — structures, complexity, practice exams"),
    "Programming": ("Programming", "Software & languages — Python, Rust, Git, engineering refs"),
    "Optimization": ("Optimization", "Convex, combinatorial, learning theory"),
    "ML-Systems": ("ML Systems", "Scale, compilation, performance, data for ML"),
    "Data-Systems": ("Data Systems", "Databases, distributed, provenance, reliability"),
    "Method-Admin": ("Method & Admin", "Study method, degree admin, StuPO / regulations"),
    "Books": ("Books — reference library", "Textbooks grouped by field (analysis, stats, ml, algorithms)"),
    "Degree": ("Degree admin", "StuPO / regulations"),
    "Foundations": ("Foundations archive", "Undergrad / general reference — NOT registered sources, browse only"),
    "DegreePlanning": ("Degree planning — future-module anchors",
                       "Cross-module carrier books & courses registered for modules you'll take later (browse/plan)"),
    "Online": ("Online — other registered links", "Registered external sources not tied to a subject bucket"),
}


# Physical walk order: the current ADR-007 subject folders first, then the
# retained legacy tops (most are dissolved; Foundations/ still exists).
DOMAIN_ORDER = ["mathematics", "optimization", "machine-learning",
                "ml-systems", "data-systems", "algorithms", "software",
                "method-admin", "ML", "Math", "CS-Theory", "Programming",
                "Books", "Degree", "Foundations"]


# Physical top-level folder -> canonical display domain. ADR-007 dissolved the
# era/format/module-code folders into lowercase subject folders; both spellings
# map here so local and online sources share one section per subject. Books/
# keeps its own subfolder routing in tree.classify_source_node.
SUBJECT_DISPLAY_DOMAIN = {
    "mathematics": "Math",
    "optimization": "Optimization",
    "machine-learning": "ML",
    "ml-systems": "ML-Systems",
    "data-systems": "Data-Systems",
    "algorithms": "CS-Theory",
    "software": "Programming",
    "method-admin": "Method-Admin",
    "ML": "ML",
    "Math": "Math",
    "CS-Theory": "CS-Theory",
    "Programming": "Programming",
    "Degree": "Degree",
    "Foundations": "Foundations",
}


EXTRA_ONLINE_ORDER = ["DegreePlanning", "Online"]


COLLECTION_DOMAIN = {
    "ml-bookshelf": "ML", "ml-lecture-series": "ML", "ml-explainers": "ML",
    "ml-broaden-later": "ML", "papers-shelf": "ML",
    "ml-systems-bookshelf": "ML", "ml-systems-lecture-series": "ML",
    "math-bookshelf": "Math", "math-lecture-series": "Math",
    "algorithms-bookshelf": "CS-Theory", "algorithms-lecture-series": "CS-Theory",
    "programming-bookshelf": "Programming", "programming-video-courses": "Programming",
    "python-internals-shelf": "Programming", "project-toolbox": "Programming",
    "degree-module-anchors": "DegreePlanning",
}


LOW_PRIORITY_COLLECTIONS = {"degree-module-anchors"}


ONLINE_DOMAIN_OVERRIDE = {
    "source-caltech-lfd": "ML",
    "source-cs229-problem-sets": "ML",
    "source-islp-community-solutions": "ML",
    "source-mit-6034-quizzes": "ML",
    "source-mit-6006": "CS-Theory",
    "source-sad-uebungen": "Math",
}


MODULE_DOMAINS = {"ML", "Math", "CS-Theory", "Programming"}


BOOKS_SUBFOLDER_DOMAIN = {"analysis": "Math", "stats": "Math", "ml": "ML",
                          "algorithms": "CS-Theory"}


MODULE_LABEL = {"python": "Python", "git": "Git", "rust": "Rust"}


TYPE_GROUP = {"book": "Books", "course": "Courses & lectures", "lecture": "Courses & lectures",
              "video": "Videos", "paper": "Papers", "documentation": "Docs",
              "software": "Software", "website": "Websites", "other": "Other", "": "Other"}


TYPE_GROUP_ORDER = ["Books", "Courses & lectures", "Videos", "Papers", "Docs",
                    "Software", "Websites", "Other"]


SOURCES_DOMAIN_ORDER = ["ML", "Math", "CS-Theory", "Programming",
                        "Optimization", "ML-Systems", "Data-Systems",
                        "Method-Admin", "Degree", "Foundations",
                        "DegreePlanning", "Online"]


# Collections whose entries carry their own subject in `group:` map per entry
# instead of per file, so one multi-subject bank never misfiles a subject.
COLLECTION_GROUP_DOMAIN = {
    "exam-practice-banks": {"sad": "Math", "analysis": "Math", "aml": "ML",
                            "amls": "ML", "algo2": "CS-Theory"},
}


def ordered_display_domains(*maps) -> list[str]:
    """Render order: canonical domains first, then any extra domains present.

    The extras clause is the structural guarantee behind "every local source
    renders once": a future subject folder can never again be counted in the
    summary while missing from every section.
    """
    present: set[str] = set()
    for mapping in maps:
        present.update(mapping)
    extras = sorted(d for d in present if d not in SOURCES_DOMAIN_ORDER)
    return list(SOURCES_DOMAIN_ORDER) + extras

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
    "ML": ("Machine Learning", "AML + AMLS course materials (slides, exams, papers, notes)"),
    "Math": ("Mathematics", "Analysis (M2.1) + Statistik & Datenanalyse — Skript, slides, drill"),
    "CS-Theory": ("CS Theory", "Algo 2 / AlgoDat II — practice exams"),
    "Programming": ("Programming", "Python, Rust, Git working references"),
    "Books": ("Books — reference library", "Textbooks grouped by field (analysis, stats, ml, algorithms)"),
    "Degree": ("Degree admin", "StuPO / regulations"),
    "Foundations": ("Foundations archive", "Undergrad / general reference — NOT registered sources, browse only"),
    "DegreePlanning": ("Degree planning — future-module anchors",
                       "Cross-module carrier books & courses registered for modules you'll take later (browse/plan)"),
    "Online": ("Online — other registered links", "Registered external sources not tied to a subject bucket"),
}


DOMAIN_ORDER = ["ML", "Math", "CS-Theory", "Programming", "Books", "Degree", "Foundations"]


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


SOURCES_DOMAIN_ORDER = ["ML", "Math", "CS-Theory", "Programming", "Degree",
                        "Foundations", "DegreePlanning", "Online"]

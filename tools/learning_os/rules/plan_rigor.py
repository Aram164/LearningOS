"""Whether a plan actually tells you where to start and why this source.

A study map can satisfy every structural rule in this repository and still be
useless to read: `"Chapter 9"` of a 700-page book names no starting page, and a
row that says only *Fahrmeir — Statistik* does not say what Fahrmeir gives you
that OpenIntro does not. Structure was enforced; content was not
(`system/CRITIQUE-POINTS.md` §1, raised 2026-08-23).

These checks close that. They are warnings, not errors, for one reason: the
backfill is incremental by design — WORKFLOWS §6a repays visibility debt on
use, not in bulk — and a rule that blocks every commit until 2,268 rows are
rewritten would simply be switched off. `LOCATOR-ANGLE-FUSED` is the exception
and is an error, because it detects the *old* representation coming back after
it was deliberately removed.
"""

from __future__ import annotations

import re

# A locator is exact when it names a numbered division AND a page. Slides and
# videos are exempt from the page half: a deck locator names a file and a slide
# range, and a video locator names an episode — neither has pages to give.
_PAGE_RE = re.compile(
    r"(?:\bpp?\.\s*\d|\bS\.\s*\d|\bp\d|\bpages?\s+\d|\bslides?\s+\d"
    r"|\bfolien?\s+\d|\b§\s*\d|\bsections?\s+\d|\bchapters?\s+\d"
    r"|\bepisodes?\s+\d|\blectures?\s+\d|\bunits?\s+\d|\bAufgabe\s+\d"
    r"|\bHW\d|\bBlatt\s*\d)",
    re.IGNORECASE,
)
_PAGE_NUMBER_RE = re.compile(r"(?:\bpp?\.\s*\d|\bS\.\s*\d|\bp\d+\b|\bpages?\s+\d|\d+\s*(?:pages?|pp\.))",
                             re.IGNORECASE)

# A video, article or quiz has no pages and often no numbers: the exact address
# of a StatQuest episode is its title. A quoted title or a file name is
# therefore as precise as a page range, and must not be reported as vague.
_NAMED_ITEM_RE = re.compile(r"['\"“”„]|\b\S+\.(?:pdf|md|html?|ipynb|py|pptx?|docx?|tex|csv)\b",
                            re.IGNORECASE)

# What made the pre-2026-08 locators unusable was not the absence of numerals
# but the presence of a hedge: "Chapter 2 selections" and "Estimation
# selections" name a direction and leave the reader to find the material. For
# formats that have no pages, that hedge is the thing worth detecting.
_HEDGE_RE = re.compile(
    r"\b(?:selections?|selected|topic-matched|relevant|appropriate|matching"
    r"|as needed|assorted|various|related)\b", re.IGNORECASE)

# Formats whose locator must reach a page, not merely a chapter.
_PAGED_FORMATS = {"book", "paper"}
# Formats where a numbered division alone is a usable address.
_ADDRESSED_FORMATS = {"course", "documentation", "website", "exam", "solutions",
                      "exercise", "video", "course-material", "code"}

# The angle used to be appended to the locator after an em dash. An em dash
# alone cannot be the signal: `"Lecture 2 — Linear Regression and Gradient
# Descent"` is a legitimate locator that happens to name a titled lecture. What
# distinguishes the fusion is that the tail is a *sentence* — long, or
# terminated — rather than a title.
_EM_DASH_RE = re.compile(r"\s—\s")


def _looks_fused(locator: str) -> bool:
    """Sentence after the dash, and nothing addressable in it.

    A tail carrying any number is a continuation of the address — a second
    page range, a section list, a file name — never the angle, which is prose
    about why the material is worth opening.
    """
    for tail in _EM_DASH_RE.split(locator)[1:]:
        tail = tail.strip()
        if any(ch.isdigit() for ch in tail):
            continue
        if tail.endswith(".") or len(tail.split()) >= 8:
            return True
    return False


class ChecksPlanRigor:

    def check_plan_rigor(self) -> None:
        self._check_route_rigor()
        self._check_stage_resource_rigor()

    # ------------------------------------------------------------- routes
    def _check_route_rigor(self) -> None:
        r = self.repo
        for mid, source_map in r.module_source_maps.items():
            where = self._rel(r.module_source_map_origins[mid])
            for entry in source_map.get("sources", []) or []:
                sid = entry.get("source_id") if isinstance(entry, dict) else None
                for route in entry.get("unit_routes", []) or []:
                    if not isinstance(route, dict):
                        continue
                    self._check_one_route(sid, route, where)

    def _check_one_route(self, sid: str | None, route: dict, where: str) -> None:
        uid = route.get("unit_id")
        fmt = str(route.get("format") or "")
        locator = str(route.get("locator") or "").strip()
        label = f"source '{sid}' route to '{uid}'"

        if _looks_fused(locator):
            self.err(
                "LOCATOR-ANGLE-FUSED",
                f"{label} keeps the angle inside its locator "
                f"('{locator[:60]}…') — the angle belongs in `angle`",
                where,
            )

        if not locator and not route.get("url") and not route.get("vault_path"):
            self.warn("ROUTE-NO-TARGET",
                      f"{label} names no locator, url or vault_path", where)
        elif locator:
            needs_page = fmt in _PAGED_FORMATS
            has_page = bool(_PAGE_NUMBER_RE.search(locator))
            has_address = bool(_PAGE_RE.search(locator)
                               or _NAMED_ITEM_RE.search(locator))
            if needs_page and not has_page:
                self.warn(
                    "LOCATOR-VAGUE",
                    f"{label} is a {fmt} whose locator names no page range "
                    f"('{locator[:60]}') — give the chapter AND its PDF pages",
                    where,
                )
            elif fmt in _ADDRESSED_FORMATS and (_HEDGE_RE.search(locator)
                                                or not has_address):
                reason = ("hedges instead of naming the material"
                          if _HEDGE_RE.search(locator)
                          else "names no numbered division or titled item")
                self.warn(
                    "LOCATOR-VAGUE",
                    f"{label} {reason} ('{locator[:60]}')",
                    where,
                )

        if not str(route.get("angle") or "").strip():
            self.warn("ROUTE-ANGLE-MISSING",
                      f"{label} declares no angle", where)
        elif not str(route.get("angle_detail") or "").strip():
            self.warn(
                "ROUTE-ANGLE-DETAIL-MISSING",
                f"{label} has a one-line angle but no `angle_detail` for the "
                f"hover", where,
            )

    # ----------------------------------------------------- study-map rows
    def _check_stage_resource_rigor(self) -> None:
        r = self.repo
        for smid, study_map in r.study_maps.items():
            where = self._rel(study_map.path)
            for stage in study_map.data.get("stages", []) or []:
                if not isinstance(stage, dict):
                    continue
                for resource in stage.get("resources", []) or []:
                    if not isinstance(resource, dict):
                        continue
                    locator = str(resource.get("locator") or "")
                    if _looks_fused(locator):
                        self.err(
                            "LOCATOR-ANGLE-FUSED",
                            f"study map '{smid}' stage '{stage.get('id')}' keeps "
                            f"the angle inside a locator — rebuild it with "
                            f"tools/assemble_lecture_study_maps.py",
                            where,
                        )
                        return

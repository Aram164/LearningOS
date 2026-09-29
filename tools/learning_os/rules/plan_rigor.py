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

import hashlib
import json
import re

from ..materials_resolution import material_uri_authority, resolve_route_material_files, sha256_file


def angle_review_fingerprint(route: dict, stage: dict, resource: dict) -> str:
    """Bind a declared relation review to the actual route and placement.

    This attests to the relation between the descriptions, not to mastery or
    independently verified source content. Corrections additionally need
    inspected, content-bound material evidence.
    """
    payload = {
        "contract": "angle-review-v1",
        "route": route,
        "stage": {key: stage.get(key) for key in
                  ("id", "title", "objective", "knowledge_node_id")},
        "placement": {key: resource.get(key) for key in
                      ("route_id", "source_id", "kind", "locator", "angle",
                       "angle_detail", "scope_triage", "vault_path", "url")},
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()

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

# A hedge word inside a quoted title is part of the material's exact identity,
# not an instruction to the learner.  In particular, lecture titles such as
# "Bias/Variance, Regularization, and Model Selection" must not be confused
# with vague locators such as "selected chapters".
_QUOTED_TEXT_RE = re.compile(r"(['\"“”„]).*?\1")


def _has_unquoted_hedge(locator: str) -> bool:
    return bool(_HEDGE_RE.search(_QUOTED_TEXT_RE.sub("", locator)))

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
            module = r.modules.get(mid)
            if module is not None and module.get("status") == "archived":
                # Archived modules remain canonical so they can be restored,
                # but their source maps are historical rather than active
                # learning surfaces.  Re-activation makes the same warnings
                # visible again because the source bytes are left untouched.
                continue
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
            elif fmt in _ADDRESSED_FORMATS and (_has_unquoted_hedge(locator)
                                                or not has_address):
                reason = ("hedges instead of naming the material"
                          if _has_unquoted_hedge(locator)
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

    def _routes_by_id(self) -> dict[str, dict]:
        """Every rich route in the repository, by stable id."""
        index: dict[str, dict] = {}
        for source_map in self.repo.module_source_maps.values():
            for entry in source_map.get("sources", []) or []:
                if not isinstance(entry, dict):
                    continue
                for route in entry.get("unit_routes", []) or []:
                    if isinstance(route, dict) and isinstance(route.get("id"), str):
                        index[route["id"]] = {**route, "source_id": entry.get("source_id")}
        return index


    def _angle_review_current(self, route: dict, stage: dict, resource: dict) -> bool:
        review = resource.get("angle_review")
        if not isinstance(review, dict) \
                or not isinstance(review.get("kind"), str) \
                or review["kind"] not in {"refinement", "correction"} \
                or any(not isinstance(review.get(key), str) or not review[key].strip()
                       for key in ("reviewed_by", "reviewed_on", "rationale")):
            return False
        try:
            if review.get("fingerprint") != angle_review_fingerprint(route, stage, resource):
                return False
        except (TypeError, ValueError):
            return False
        if review["kind"] == "refinement":
            return True
        evidence = review.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            return False
        # Resolve only the named route. Evidence from a similarly named file
        # or a different source can never authorize a correction.
        try:
            files = {item.material_uri: item.path
                     for item in resolve_route_material_files(self.repo, route)}
            cache = getattr(self, "_angle_evidence_hashes", None)
            if cache is None:
                self._angle_evidence_hashes = cache = {}
            for item in evidence:
                if not isinstance(item, dict) or not isinstance(item.get("material_uri"), str) \
                        or not isinstance(item.get("locator"), str) \
                        or not item["locator"].strip():
                    return False
                uri = item["material_uri"]
                path = files.get(uri)
                # A broad course route can have no single file target. Its
                # correction must still name exact inspected bytes belonging
                # to that source's declared material authority. A route with
                # exact targets cannot substitute another file from the shelf.
                if not files:
                    source = self.repo.sources.get(route.get("source_id"), {})
                    authority = material_uri_authority(source.get("material"))
                    if not authority or material_uri_authority(uri) != authority:
                        return False
                    named = resolve_route_material_files(self.repo, {**route, "vault_path": uri})
                    path = next((f.path for f in named if f.material_uri == uri), None)
                if path is None:
                    return False
                if path not in cache:
                    cache[path] = sha256_file(path)
                if item.get("file_sha256") != cache[path]:
                    return False
        except (OSError, ValueError, AttributeError):
            return False
        return True


    def _check_row_angle(self, smid: str, stage: dict, resource: dict,
                         routes: dict[str, dict], where: str) -> None:
        """A stage row's angle against the route it claims to place.

        The angle a learner reads at session time lives on the row, not on the
        route, and the two drifted apart without anything noticing: an audit on
        2026-09-18 found 404 rows whose angle contradicts its own route, while
        `assemble_lecture_study_maps.py` — the documented path for structural
        plan revisions — regenerates none of them and would overwrite every one.
        The L04 UE3 repair is the shape of it: the row was corrected to
        "total-probability ... no posterior inversion" while its route still
        says "sensitivity/specificity" and still claims to cover Bayes.

        A warning, not an error, and deliberately not yet in the baseline: each
        row is either a legitimate per-placement refinement or an unrecorded
        correction, and only a human reading both can say which. Enforcement —
        a required supersession pointer to the synthesis assessment that
        justifies the difference — comes after that triage.
        """
        angle = str(resource.get("angle") or "").strip()
        route_id = resource.get("route_id")
        if not isinstance(route_id, str):
            ref = resource.get("material_ref")
            route_id = ref.get("route_id") if isinstance(ref, dict) else None
        route = routes.get(route_id) if isinstance(route_id, str) else None
        if "angle_review" in resource:
            if angle and route is not None and self._angle_review_current(route, stage, resource):
                return
            self.warn(
                "ANGLE-REVIEW-STALE",
                f"study map '{smid}' stage '{stage.get('id')}' has an invalid or stale "
                f"angle review for {route_id} — review the changed inputs again",
                where,
            )
            return
        if not angle or route is None:
            return
        route_angle = str(route.get("angle") or "").strip()
        if not route_angle or " ".join(angle.split()) == " ".join(route_angle.split()):
            return
        self.warn(
            "ANGLE-DIVERGES-FROM-ROUTE",
            f"study map '{smid}' stage '{stage.get('id')}' gives {route_id} an "
            f"angle its route does not carry ('{angle[:48]}…' vs "
            f"'{route_angle[:48]}…') — refine the route, or record which "
            f"synthesis assessment corrects it",
            where,
        )

    # ----------------------------------------------------- study-map rows
    def _stage_node_id(self, smid: str, stage: dict, unit_nodes: set[str] | None,
                       where: str) -> str | None:
        """The knowledge node a stage teaches: explicit key, else id convention.

        The assembler joins node to routes via `covers` and used to throw the
        key away at emission, so a later covers edit orphaned placements with
        nothing able to see it (2026-09-18: UE3 still placed on the L04 Bayes
        stage after its Bayes coverage was dropped). Stages that follow the
        `stage-<slug>` / `knowledge-<slug>` convention link back silently;
        only the unlinkable ones warn — the backfill is incremental, like
        every other rigor check in this file.
        """
        if unit_nodes is None:
            return None
        key = stage.get("knowledge_node_id")
        if isinstance(key, str) and key.strip():
            if unit_nodes is not None and key not in unit_nodes:
                self.warn(
                    "STAGE-NODE-UNLINKED",
                    f"study map '{smid}' stage '{stage.get('id')}' names node "
                    f"'{key}' absent from its unit's knowledge map — fix the "
                    f"key or the map",
                    where,
                )
                return None
            return key
        if unit_nodes is not None:
            stage_id = str(stage.get("id") or "")
            if stage_id.startswith("stage-"):
                inferred = "knowledge-" + stage_id[len("stage-"):]
                if inferred in unit_nodes:
                    return inferred
        self.warn(
            "STAGE-NODE-UNLINKED",
            f"study map '{smid}' stage '{stage.get('id')}' carries no "
            f"knowledge_node_id and its id matches no live node — name the "
            f"node the stage teaches",
            where,
        )
        return None

    def _check_row_node(self, smid: str, stage: dict, node_id: str,
                        resource: dict, routes: dict[str, dict], where: str) -> None:
        """A placed route against the node of the stage it sits on.

        A warning, not an error: the placement may be deliberate scaffolding
        (UE3's total-probability calculation is the denominator the Bayes
        stage inverts). A non-blank ``node_scaffold_note`` on the resource
        records that call and silences the warning; anything else must move
        or gain covers.
        """
        route_id = resource.get("route_id")
        if not isinstance(route_id, str):
            ref = resource.get("material_ref")
            route_id = ref.get("route_id") if isinstance(ref, dict) else None
        if not isinstance(route_id, str):
            return
        route = routes.get(route_id)
        if route is None:
            return
        covers = [str(node) for node in (route.get("covers") or [])]
        if node_id not in covers:
            note = resource.get("node_scaffold_note")
            if isinstance(note, str) and note.strip():
                return
            self.warn(
                "RESOURCE-NODE-ORPHAN",
                f"study map '{smid}' stage '{stage.get('id')}' teaches node "
                f"'{node_id}' but {route_id} no longer covers it — move the "
                f"placement, extend the route covers, or record "
                f"node_scaffold_note",
                where,
            )

    def _check_stage_resource_rigor(self) -> None:
        r = self.repo
        routes = self._routes_by_id()
        for smid, study_map in r.study_maps.items():
            where = self._rel(study_map.path)
            unit = r.units.get(study_map.unit_id)
            unit_nodes: set[str] | None = None
            if unit is not None and isinstance(unit.data.get("knowledge_map"), dict):
                # Units without a knowledge map (roadmaps, fluency drills)
                # have no nodes to link against; their stages stay unchecked
                # rather than warning once per stage about a map that by
                # design does not exist.
                unit_nodes = {
                    str(node.get("id"))
                    for node in (unit.data.get("knowledge_map") or {}).get("nodes", []) or []
                    if isinstance(node, dict) and node.get("id")
                }
            for stage in study_map.data.get("stages", []) or []:
                if not isinstance(stage, dict):
                    continue
                node_id = self._stage_node_id(smid, stage, unit_nodes, where)
                for resource in stage.get("resources", []) or []:
                    if not isinstance(resource, dict):
                        continue
                    self._check_row_angle(smid, stage, resource, routes, where)
                    if node_id is not None:
                        self._check_row_node(smid, stage, node_id, resource, routes, where)
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

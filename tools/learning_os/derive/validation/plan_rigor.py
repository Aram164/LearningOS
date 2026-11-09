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

import copy
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import PurePosixPath
from typing import Literal

from learning_os.domain.material_refs import (
    MATERIAL_FIELDS,
    MaterialReferenceError,
    expand_map,
    unit_routes,
)
from learning_os.domain.route_identity import route_with_identity
from learning_os.store.loading.yamlio import LoaderError, load_yaml
from learning_os.store.materials.resolution import (
    material_uri_authority,
    resolve_route_material_files,
    sha256_file,
)


def _fingerprint_payload(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                     separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def angle_review_fingerprint(route: dict, stage: dict, resource: dict) -> str:
    """Bind a declared relation review to the actual route and placement.

    This attests to the relation between the descriptions, not to mastery or
    independently verified source content. Corrections additionally need
    inspected, content-bound material evidence.

    The v2 payload binds the relation itself — route identity, its angle
    descriptions, coverage and material address, the stage's node, and the
    placement — but not prose titles or the stage objective: fixing a typo
    in a title is not a new relation, and making it one forced a whole
    stage's resources to be re-supplied just to re-bind a review.
    Fingerprints bound under v1 stay current (see
    ``_legacy_angle_review_fingerprint``); new binds use v2.
    """
    payload = {
        "contract": "angle-review-v2",
        "route": {key: route.get(key) for key in
                  ("id", "source_id", "angle", "angle_detail", "covers",
                   "locator", "url", "vault_path")},
        "stage": {key: stage.get(key) for key in
                  ("id", "knowledge_node_id")},
        "placement": {key: resource.get(key) for key in
                      ("route_id", "source_id", "kind", "locator", "angle",
                       "angle_detail", "scope_triage", "vault_path", "url")},
    }
    return _fingerprint_payload(payload)


def _legacy_angle_review_fingerprint(route: dict, stage: dict, resource: dict) -> str:
    """The v1 payload, kept only so already-bound reviews stay current."""
    payload = {
        "contract": "angle-review-v1",
        "route": route,
        "stage": {key: stage.get(key) for key in
                  ("id", "title", "objective", "knowledge_node_id")},
        "placement": {key: resource.get(key) for key in
                      ("route_id", "source_id", "kind", "locator", "angle",
                       "angle_detail", "scope_triage", "vault_path", "url")},
    }
    return _fingerprint_payload(payload)


def _route_by_id(source_map: dict | None, module_id: str, unit_id: str) -> dict:
    if not isinstance(source_map, dict):
        return {}
    return {str(route["id"]): route
            for route in unit_routes(source_map, module_id, unit_id)}


def _view_route_id(authored: dict, expanded: dict) -> str | None:
    route_id = expanded.get("route_id") or authored.get("route_id")
    if isinstance(route_id, str) and route_id:
        return route_id
    ref = authored.get("material_ref")
    if isinstance(ref, dict) and isinstance(ref.get("route_id"), str):
        return ref["route_id"]
    return None


def refresh_prose_only_angle_reviews(before_map: dict | None,
                                     before_source_map: dict | None,
                                     after_map: dict,
                                     after_source_map: dict | None,
                                     module_id: str, unit_id: str) -> dict:
    """Upgrade a still-current review's fingerprint to v2 on prose edits.

    A review bound under v1 (or v2) whose relation payload is unchanged —
    only prose the v2 payload excludes moved (stage title/objective, route
    title) — is transparently rebound to the v2 fingerprint. A relation
    change keeps the stored fingerprint, and the validator flags it stale.
    Returns a copy; maps that cannot be expanded are returned unchanged.
    """
    if not isinstance(before_map, dict) or not isinstance(after_map, dict):
        return after_map
    if not isinstance(after_map.get("stages"), list):
        return after_map
    try:
        before_expanded = expand_map(before_map, before_source_map or {},
                                     module_id, unit_id)
        after_expanded = expand_map(after_map, after_source_map or {},
                                    module_id, unit_id)
    except (MaterialReferenceError, TypeError, ValueError, KeyError):
        return after_map
    before_routes = _route_by_id(before_source_map, module_id, unit_id)
    after_routes = _route_by_id(after_source_map, module_id, unit_id)
    before_stages = {
        str(authored.get("id")): (authored, expanded)
        for authored, expanded in zip(before_map.get("stages") or [],
                                      before_expanded.get("stages") or [],
                                      strict=False)
        if isinstance(authored, dict) and isinstance(expanded, dict)
        and authored.get("id")
    }
    refreshed = copy.deepcopy(after_map)
    for authored_stage, expanded_stage, refreshed_stage in zip(
            after_map.get("stages") or [], after_expanded.get("stages") or [],
            refreshed.get("stages") or [], strict=False):
        if not isinstance(authored_stage, dict) or not isinstance(expanded_stage, dict):
            continue
        before_pair = before_stages.get(str(authored_stage.get("id")))
        if before_pair is None:
            continue
        before_authored_stage, before_expanded_stage = before_pair
        before_authored = before_authored_stage.get("resources") or []
        before_expanded_resources = before_expanded_stage.get("resources") or []
        for authored, expanded, target in zip(
                authored_stage.get("resources") or [],
                expanded_stage.get("resources") or [],
                refreshed_stage.get("resources") or [], strict=False):
            if not isinstance(authored, dict) or not isinstance(target, dict):
                continue
            review = target.get("angle_review")
            if not isinstance(review, dict):
                continue
            fingerprint = review.get("fingerprint")
            if not isinstance(fingerprint, str) or not fingerprint:
                continue
            index = next((i for i, row in enumerate(before_authored)
                          if isinstance(row, dict)
                          and authored.get("id") is not None
                          and row.get("id") == authored.get("id")), None)
            if index is None or index >= len(before_expanded_resources):
                continue
            before_authored_row = before_authored[index]
            before_expanded_row = before_expanded_resources[index]
            if not isinstance(before_authored_row, dict) \
                    or not isinstance(before_expanded_row, dict):
                continue
            before_route = before_routes.get(
                _view_route_id(before_authored_row, before_expanded_row) or "")
            after_route = after_routes.get(
                _view_route_id(authored, expanded) or "")
            if before_route is None or after_route is None:
                continue
            before_v2 = angle_review_fingerprint(
                before_route, before_expanded_stage, before_expanded_row)
            current_before = fingerprint in (before_v2, _legacy_angle_review_fingerprint(
                before_route, before_expanded_stage, before_expanded_row))
            after_v2 = angle_review_fingerprint(
                after_route, expanded_stage, expanded)
            current_after = fingerprint in (after_v2, _legacy_angle_review_fingerprint(
                after_route, expanded_stage, expanded))
            if current_before and not current_after and before_v2 == after_v2:
                review["fingerprint"] = after_v2
                if "material_ref" in target and "route_id" not in target:
                    route_id = _view_route_id(authored, expanded)
                    if route_id:
                        target["route_id"] = route_id
    return refreshed


def bind_angle_reviews(map_data: dict, source_map: dict | None,
                       module_id: str, unit_id: str) -> dict:
    """Fill the fingerprint of every ``angle_review`` that omits one.

    Mirrors ``bind_runtime_reviews`` (agent-cost D3): the fingerprint is a
    pure function of the route, stage and effective placement, so an author
    who declares a review in an imported map gets the value they would have
    computed for the placement they are importing. A ``material_ref`` row is
    expanded on a temporary copy exactly as the loader expands it, so the
    bound value is the one the validator recomputes. A fingerprint already
    present is kept as written, stale or not. Returns a copy.
    """
    if not isinstance(map_data, dict) or not isinstance(map_data.get("stages"), list):
        return map_data
    if not isinstance(source_map, dict):
        return map_data
    routes = {str(route["id"]): route
              for route in unit_routes(source_map, module_id, unit_id)}
    if not routes:
        return map_data
    bound = copy.deepcopy(map_data)
    for stage in bound.get("stages") or []:
        if not isinstance(stage, dict):
            continue
        for resource in stage.get("resources") or []:
            if not isinstance(resource, dict):
                continue
            review = resource.get("angle_review")
            if not isinstance(review, dict) or "fingerprint" in review:
                continue
            route_id = resource.get("route_id")
            ref = resource.get("material_ref")
            if not isinstance(route_id, str) and isinstance(ref, dict):
                route_id = ref.get("route_id")
            route = routes.get(route_id) if isinstance(route_id, str) else None
            if route is None:
                continue
            if isinstance(ref, dict) and "route_id" not in resource:
                # The expanded map is schema-validated and expansion pops
                # material_ref, so a reviewed compact row must also carry
                # its route_id at the top level (the live storage shape);
                # the fingerprint below binds that same placement.
                resource["route_id"] = route_id
            effective = dict(resource)
            if isinstance(ref, dict):
                for field in ref.get("inherit") or []:
                    owner = MATERIAL_FIELDS.get(field) if isinstance(field, str) else None
                    if owner is not None and owner in route:
                        effective[field] = copy.deepcopy(route[owner])
            review["fingerprint"] = angle_review_fingerprint(route, stage, effective)
    return bound

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


def _filename_present(name: str, locator: str) -> bool:
    # The substring test is necessary for the boundary match, so it never
    # changes the answer. It is here for cost: this runs once per route and
    # manifest name, and a fresh pattern per pair defeats re's cache — it was
    # ~70 % of a full validation on the live tree (2026-10-23).
    if name not in locator:
        return False
    return bool(re.search(r"(?<!\w)" + re.escape(name) + r"(?!\w)", locator))


def locator_binding_findings(module_id: str, source_id: str, routes: list[dict],
                              manifest_names: set[str]) -> list[tuple[str, str]]:
    """Authoring constraints over declared identities; no material bytes are read."""
    findings = []
    groups = defaultdict(list)
    names = {unicodedata.normalize("NFC", name).casefold() for name in manifest_names}
    for route in routes:
        vault = route.get("vault_path")
        if isinstance(vault, str) and vault.startswith("material://"):
            names.add(unicodedata.normalize("NFC", PurePosixPath(vault).name).casefold())
    for route in routes:
        locator = unicodedata.normalize("NFC", str(route.get("locator") or ""))
        rid = route_with_identity(module_id, source_id, route)["id"]
        if locator.strip():
            groups[(str(route.get("unit_id") or ""), " ".join(locator.split()))].append(rid)
        vault = route.get("vault_path")
        if not isinstance(vault, str) or not vault.startswith("material://"):
            continue
        own = unicodedata.normalize("NFC", PurePosixPath(vault).name).casefold()
        text = locator.casefold()
        if own and not _filename_present(own, text):
            others = sorted(name for name in names if name and name != own and _filename_present(name, text))
            if others:
                findings.append(("ROUTE-VAULT-LOCATOR-MISMATCH",
                                 f"route {rid} binds {own!r} but its locator names {others!r} without its own file"))
    for (unit, _), ids in sorted(groups.items()):
        if len(ids) >= 2:
            findings.append(("ROUTE-LOCATOR-DUPLICATE",
                             f"source {source_id!r}, unit {unit!r}: distinct rich routes share one locator: {', '.join(sorted(ids))}"))
    return findings


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
        if not r.module_source_maps:
            return
        manifest_names: set[str] = set()
        path = r.root / "records/materials-manifest.yaml"
        if path.is_file():
            try:
                manifest = load_yaml(path, r.root)
                manifest_names = {PurePosixPath(str(key)).name for key in (manifest.get("files") or {})}
            except LoaderError:
                pass  # MATERIALS-MANIFEST owns malformed inventory diagnostics.
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
                if not isinstance(entry, dict):
                    continue
                sid = entry.get("source_id")
                rich = [row for row in entry.get("unit_routes", []) or [] if isinstance(row, dict)]
                for code, message in locator_binding_findings(mid, str(sid or ""), rich, manifest_names):
                    self.err(code, message, where)
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
        for module_id, source_map in self.repo.module_source_maps.items():
            for entry in source_map.get("sources", []) or []:
                if not isinstance(entry, dict):
                    continue
                for route in entry.get("unit_routes", []) or []:
                    if isinstance(route, dict):
                        identified = route_with_identity(module_id, str(entry.get("source_id") or ""), route)
                        index[str(identified["id"])] = {**identified, "source_id": entry.get("source_id")}
        return index


    def _angle_review_current(
        self, route: dict, stage: dict, resource: dict
    ) -> Literal["current", "stale", "unverifiable"]:
        """How current a review is: stale needs re-review, unverifiable needs a mount.

        "current" — the review matches its inputs and, for a correction, the
        evidence bytes on disk. "stale" — malformed, fingerprint-mismatched,
        or contradicted by bytes that are present. "unverifiable" — the
        evidence file the correction cites is not here to hash: the materials
        tree is offline or the file is absent. That last case must never read
        as stale, because staleness is baseline-managed and would fail a run
        with no materials tree (CI) for content that never changed.
        """
        review = resource.get("angle_review")
        if not isinstance(review, dict) \
                or not isinstance(review.get("kind"), str) \
                or review["kind"] not in {"refinement", "correction"} \
                or any(not isinstance(review.get(key), str) or not review[key].strip()
                       for key in ("reviewed_by", "reviewed_on", "rationale")):
            return "stale"
        try:
            if review.get("fingerprint") not in (
                    angle_review_fingerprint(route, stage, resource),
                    _legacy_angle_review_fingerprint(route, stage, resource)):
                return "stale"
        except (TypeError, ValueError):
            return "stale"
        if review["kind"] == "refinement":
            return "current"
        evidence = review.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            return "stale"
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
                    return "stale"
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
                        return "stale"
                    named = resolve_route_material_files(self.repo, {**route, "vault_path": uri})
                    path = next((f.path for f in named if f.material_uri == uri), None)
                if path is None:
                    # The route's own files resolved but the evidence names
                    # something else: a wrong citation, not a missing drive.
                    if files:
                        return "stale"
                    return "unverifiable"
                if path not in cache:
                    try:
                        cache[path] = sha256_file(path)
                    except OSError:
                        return "unverifiable"
                if item.get("file_sha256") != cache[path]:
                    return "stale"
        except OSError:
            return "unverifiable"
        except (ValueError, AttributeError):
            return "stale"
        return "current"


    def _check_row_angle(self, smid: str, stage: dict, resource: dict,
                         routes: dict[str, dict], where: str, *,
                         material_route_id: str | None = None) -> None:
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
        route_id = material_route_id or resource.get("route_id")
        if not isinstance(route_id, str):
            ref = resource.get("material_ref")
            route_id = ref.get("route_id") if isinstance(ref, dict) else None
        route = routes.get(route_id) if isinstance(route_id, str) else None
        if "angle_review" in resource:
            if not angle or route is None:
                self.warn(
                    "ANGLE-REVIEW-STALE",
                    f"study map '{smid}' stage '{stage.get('id')}' has an invalid or stale "
                    f"angle review for {route_id} — review the changed inputs again",
                    where,
                )
                return
            state = self._angle_review_current(route, stage, resource)
            if state == "current":
                return
            if state == "unverifiable":
                self.warn(
                    "ANGLE-REVIEW-UNVERIFIED",
                    f"study map '{smid}' stage '{stage.get('id')}' has an angle review for "
                    f"{route_id} whose evidence bytes are not on this machine — re-run "
                    f"with the materials tree mounted to verify it",
                    where,
                )
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
                        resource: dict, routes: dict[str, dict], where: str, *,
                        material_route_id: str | None = None) -> None:
        """A placed route against the node of the stage it sits on.

        A warning, not an error: the placement may be deliberate scaffolding
        (UE3's total-probability calculation is the denominator the Bayes
        stage inverts). A non-blank ``node_scaffold_note`` on the resource
        records that call and silences the warning; anything else must move
        or gain covers.
        """
        route_id = material_route_id or resource.get("route_id")
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

    def _module_scope_index(self) -> dict[str, dict]:
        """Per module, declared sources and routes with their unit owners.

        A stage may teach only what its module adopted, so a resource is
        checked against the owning module's map, never against every route in
        the repository: a route another module declared is not this module's
        scope, and `references.py` already reports the ownership errors.
        """
        index: dict[str, dict] = {}
        for module_id, source_map in self.repo.module_source_maps.items():
            ids: dict[str, str] = {}
            pairs: set[tuple[str, str, str]] = set()
            sources: set[str] = set()
            for entry in source_map.get("sources", []) or []:
                if not isinstance(entry, dict):
                    continue
                source_id = str(entry.get("source_id") or "")
                sources.add(source_id)
                for route in entry.get("unit_routes", []) or []:
                    if not isinstance(route, dict):
                        continue
                    projected = route_with_identity(module_id, source_id, route)
                    route_id = projected.get("id")
                    unit_id = str(route.get("unit_id") or "")
                    if isinstance(route_id, str):
                        ids[route_id] = unit_id
                    pairs.add((unit_id, source_id, str(route.get("locator") or "")))
            index[module_id] = {"ids": ids, "pairs": pairs, "sources": sources}
        return index

    def _authored_route_bindings(self, study_map) -> dict[tuple[str, int], str]:
        """The route id an authored resource names, by (stage id, index).

        The loaded study map is *expanded*: `material_ref` is popped and its
        inherited fields are copied onto the resource
        (`domain/material_refs.expand_map`), so a compact row's route binding
        survives only in the authored bytes. The correspondence is by stage id
        and resource index — the same one `domain.material_refs.preserve_map_refs`
        uses — because expansion replaces a resource in place and never
        reorders or drops one.

        Only the `material_ref` spelling is collected here. A top-level
        `route_id` survives expansion unchanged, and `references.py` already
        checks it.
        """
        bindings: dict[tuple[str, int], str] = {}
        authored = study_map.authored_data
        if not isinstance(authored, dict):
            return bindings
        for stage in authored.get("stages", []) or []:
            if not isinstance(stage, dict):
                continue
            stage_id = str(stage.get("id") or "")
            for index, resource in enumerate(stage.get("resources", []) or []):
                if not isinstance(resource, dict):
                    continue
                if isinstance(resource.get("route_id"), str) and resource["route_id"]:
                    # Spelled at the top level as well: the expanded resource
                    # carries it, and `references.py` owns that verdict.
                    continue
                ref = resource.get("material_ref")
                route_id = ref.get("route_id") if isinstance(ref, dict) else None
                if isinstance(route_id, str) and route_id:
                    bindings[(stage_id, index)] = route_id
        return bindings

    def _check_row_scope(self, smid: str, stage: dict, resource: dict,
                         scope: dict, where: str, *, unit_id: str,
                         disposed_sources: set[str],
                         material_route_id: str | None = None,
                         module_id: str = "") -> None:
        """A stage resource must resolve to something the module adopted.

        A resource that names a route is bound, and the unknown-route and
        wrong-owner errors belong to `references.py`. A resource without a
        route has to match a route declared for its own unit: the same source
        at the same locator. Module adoption, unit disposition and a matching
        route are distinct facts, so the diagnostic names what is missing.

        A `reference` row is a pointer, and pointing outside the module's map
        is what it is for. `kind` is the row's meaning rather than a triage
        flag, so the exemption rests on it and not on `scope_triage` — a
        triage flag is one the writer of the row also sets.
        """
        if resource.get("kind") == "reference":
            return
        if resource.get("kind") == "practise" \
                and not resource.get("source_id") \
                and not resource.get("route_id") \
                and material_route_id is None \
                and not resource.get("url"):
            # A self-contained exercise or a stage-owned attachment prompt
            # adopts no external teaching material, so there is no source
            # for the module's map to bind. A practise row that names a
            # source, route or material:// path is still adopting material
            # and stays bound below (#94).
            vault_path = resource.get("vault_path")
            if not vault_path:
                return
            attachments = (
                f"curriculum/modules/{module_id}/units/{unit_id}"
                f"/stages/{stage.get('id')}/attachments/"
            )
            if isinstance(vault_path, str) and vault_path.startswith(attachments):
                return
        route_id = resource.get("route_id")
        if isinstance(route_id, str) and route_id:
            # `references.py` reports an unknown route (REF-ROUTE) and a
            # route owned by another unit (RESOURCE-ROUTE-OWNER) as errors.
            # The scope rule does not report the same thing twice.
            return
        if material_route_id is not None:
            if scope["ids"].get(material_route_id) == unit_id:
                return
            self.warn(
                "RESOURCE-SCOPE-ROUTE-UNDECLARED",
                f"study map '{smid}' stage '{stage.get('id')}' teaches route "
                f"'{material_route_id}' — the module's source map declares no "
                f"such route for unit '{unit_id}'; bind the resource to a "
                f"route declared for this unit",
                where,
            )
            return
        source_id = resource.get("source_id")
        locator = str(resource.get("locator") or "")
        if isinstance(source_id, str) and (unit_id, source_id, locator) in scope["pairs"]:
            return
        if not source_id:
            code = "RESOURCE-SCOPE-NO-SOURCE"
            reason = (
                "no source_id is named, so module adoption cannot be checked; "
                "name the source and bind the resource to a route for this unit"
            )
        elif source_id not in scope["sources"]:
            code = "RESOURCE-SCOPE-UNADOPTED"
            reason = (
                "the module's source map does not declare this source; adopt "
                "the source in that map and declare a route for this unit"
            )
        elif source_id not in disposed_sources:
            code = "RESOURCE-SCOPE-NO-DISPOSITION"
            reason = (
                "the module declares this source, but this unit has no recorded "
                "source disposition and no matching route; record it as selected, "
                "reference-only, or deferred with a reason, and bind this teaching "
                "resource to a route for this unit"
            )
        else:
            code = "RESOURCE-SCOPE-NO-ROUTE"
            reason = (
                "the unit's source disposition is recorded, but no route for "
                "this unit matches this source and locator; bind the resource "
                "to a declared route or review the missing route"
            )
        self.warn(
            code,
            f"study map '{smid}' stage '{stage.get('id')}' teaches "
            f"{source_id or 'material without a source'} at '{locator[:60]}' — "
            f"{reason}",
            where,
        )

    def _check_stage_resource_rigor(self) -> None:
        r = self.repo
        routes = self._routes_by_id()
        scope = self._module_scope_index()
        for smid, study_map in r.study_maps.items():
            where = self._rel(study_map.path)
            unit = r.units.get(study_map.unit_id)
            module_id = str(unit.data.get("module_id") or "") if unit is not None else ""
            disposed_sources = {
                row.get("source_id")
                for field in ("source_selections", "scope_sources")
                for row in (unit.data.get(field, []) or [])
                if isinstance(row, dict) and isinstance(row.get("source_id"), str)
            } if unit is not None else set()
            module = r.modules.get(module_id) if module_id else None
            # Archived modules keep their source maps as history, not as an
            # active learning surface, so their stages are not scope-checked.
            scope_for = None
            if module_id and not (module and module.get("status") == "archived"):
                scope_for = scope.get(module_id)
            authored_routes = self._authored_route_bindings(study_map)
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
                stage_id = str(stage.get("id") or "")
                for index, resource in enumerate(stage.get("resources", []) or []):
                    if not isinstance(resource, dict):
                        continue
                    self._check_row_angle(smid, stage, resource, routes, where,
                                          material_route_id=authored_routes.get((stage_id, index)))
                    if scope_for is not None:
                        self._check_row_scope(
                            smid, stage, resource, scope_for, where,
                            unit_id=study_map.unit_id, disposed_sources=disposed_sources,
                            material_route_id=authored_routes.get((stage_id, index)),
                            module_id=module_id,
                        )
                    if node_id is not None:
                        self._check_row_node(smid, stage, node_id, resource, routes, where,
                                             material_route_id=authored_routes.get((stage_id, index)))
                    locator = str(resource.get("locator") or "")
                    if _looks_fused(locator):
                        self.err(
                            "LOCATOR-ANGLE-FUSED",
                            f"study map '{smid}' stage '{stage.get('id')}' keeps "
                            f"the angle inside a locator — rebuild it with "
                            f"tools/assemble_lecture_study_maps.py",
                            where,
                        )
                        continue

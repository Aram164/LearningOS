"""Modules, curriculum tree, study maps and learning paths."""

from __future__ import annotations


class ChecksCurriculum:
    """Mixed into Validator; see rules/core.py."""
    def check_modules(self):
        for module in self.repo.modules.values():
            mid = module.get("id")
            where = self._origin_for("module", str(mid))
            attempts = module.get("attempts", []) or []
            # Coerce to str before comparing: the loader normalizes YAML dates to
            # ISO strings, but a bare-year int (date: 2026) would stay an int and
            # `sorted()` on mixed str/int raises TypeError. ISO-8601 strings sort
            # chronologically, so a uniform str view is a correct comparison key.
            dates = [str(a.get("date")) for a in attempts if a.get("date")]
            if dates != sorted(dates):
                self.err("MOD-ORDER", f"module '{mid}' attempt dates are not chronologically ordered",
                         where)
            for i, att in enumerate(attempts):
                if att.get("grade") is not None and att.get("result") != "passed" \
                        and module.get("status") != "completed":
                    self.err("MOD-GRADE",
                             f"module '{mid}' attempt[{i}] carries a grade but result is "
                             f"'{att.get('result')}' and module is not completed",
                             where)
                if att.get("result") == "registered" and i != len(attempts) - 1:
                    self.err("MOD-REGISTERED",
                             f"module '{mid}' attempt[{i}] is 'registered' but is not the latest attempt",
                             where)
            examination = module.get("examination") or {}
            sittings = examination.get("sittings", []) or []
            sitting_keys = [
                (int(row.get("termin", 0)), str(row.get("date", "")),
                 str(row.get("end_date") or row.get("date", "")))
                for row in sittings if isinstance(row, dict)
            ]
            if len(sitting_keys) != len(set(sitting_keys)):
                self.err("MOD-SITTING-DUP", f"module '{mid}' has duplicate examination sittings", where)
            for row in sittings:
                start = str(row.get("date", ""))
                end = str(row.get("end_date") or start)
                if start and end < start:
                    self.err("MOD-SITTING-RANGE",
                             f"module '{mid}' sitting ends before it starts ({start} to {end})", where)
            windows = examination.get("registration_windows", []) or []
            window_keys = [
                (str(row.get("opens", "")), str(row.get("closes", "")),
                 str(row.get("label", "")))
                for row in windows if isinstance(row, dict)
            ]
            if len(window_keys) != len(set(window_keys)):
                self.err("MOD-REGISTRATION-DUP",
                         f"module '{mid}' has duplicate registration windows", where)
            for row in windows:
                opens = str(row.get("opens", ""))
                closes = str(row.get("closes", ""))
                if opens and closes < opens:
                    self.err("MOD-REGISTRATION-RANGE",
                             f"module '{mid}' registration window closes before it opens "
                             f"({opens} to {closes})", where)

    def check_curriculum(self):
        """Cross-file invariants for the module-first operational tree."""
        r = self.repo
        if not r.programs and not r.units and not r.study_maps:
            return  # backward-compatible v1/synthetic repository
        defaults = [p.id for p in r.programs.values()
                    if p.data.get("default") and p.data.get("status") == "active"]
        if defaults != ["program-bachelors"]:
            self.err("PROGRAM-DEFAULT",
                     "the active/default program must be exactly program-bachelors",
                     "curriculum/programs")
        if "workspace-degree-planning" in r.workspaces:
            self.err("QUARANTINE-MASTERS",
                     "Master's Planning workspace is loaded as current work instead of quarantined",
                     self._origin_for("workspace", "workspace-degree-planning"))
        missing_legacy = sorted(set(r.legacy_modules) - set(r.modules))
        if missing_legacy:
            self.err("MODULE-MIGRATION",
                     "partitioned records do not cover legacy module ids: " + ", ".join(missing_legacy),
                     "records/modules.yaml")
        for mid, module in r.modules.items():
            where = self._origin_for("module", mid)
            if module.get("kind") == "academic":
                for field in ("institution", "semester"):
                    if not module.get(field):
                        self.err("MODULE-ACADEMIC", f"academic module '{mid}' lacks {field}", where)
            components = module.get("components", []) or []
            component_ids = [c.get("id") for c in components if isinstance(c, dict)]
            if len(component_ids) != len(set(component_ids)):
                self.err("COMPONENT-DUP", f"module '{mid}' has duplicate component ids", where)
            ordered = module.get("unit_order", []) or []
            owned_units = [u for u in r.units.values() if u.module_id == mid]
            actual = [u.id for u in owned_units]
            if set(ordered) != set(actual) or len(ordered) != len(actual):
                self.err("UNIT-ORDER",
                         f"module '{mid}' unit_order must contain every owned unit exactly once",
                         where)
            else:
                declared_orders = [unit.data.get("order") for unit in owned_units]
                # Schema validation reports a missing/non-integer order. Do not
                # let this semantic comparison turn the same bad input into an
                # exception that aborts the rest of validation.
                valid_orders = all(
                    isinstance(value, int) and not isinstance(value, bool)
                    for value in declared_orders
                )
                if valid_orders:
                    numeric_order = sorted(
                        owned_units,
                        key=lambda unit: (unit.data["order"], unit.id),
                    )
                    numeric_ids = [unit.id for unit in numeric_order]
                    order_values = [unit.data["order"] for unit in numeric_order]
                    if len(order_values) != len(set(order_values)):
                        self.err(
                            "UNIT-ORDER-DUP",
                            f"module '{mid}' unit order values must be unique",
                            where,
                        )
                    elif list(ordered) != numeric_ids:
                        self.err(
                            "UNIT-ORDER-MISMATCH",
                            f"module '{mid}' unit_order disagrees with unit order values",
                            where,
                        )
            source_map = r.module_source_maps.get(mid, {})
            joins = [(e.get("source_id"), e.get("role"))
                     for e in source_map.get("sources", []) or [] if isinstance(e, dict)]
            if len(joins) != len(set(joins)):
                self.err("SOURCE-MAP-DUP",
                         f"module '{mid}' repeats the same source-role join", where)
        for uid, unit in r.units.items():
            where = self._rel(unit.path)
            current = unit.data.get("current_study_map")
            owned = [sm.id for sm in r.study_maps.values() if sm.unit_id == uid]
            if len(owned) > 1:
                self.err("UNIT-MAP-MULTIPLE",
                         f"unit '{uid}' has more than one current study map: {owned}", where)
            if current and owned != [current]:
                self.err("UNIT-MAP-CURRENT",
                         f"unit '{uid}' current_study_map does not match its physical study map", where)
            if not current and owned:
                self.err("UNIT-MAP-UNDECLARED",
                         f"unit '{uid}' has a study-map.yaml but does not declare it", where)
            knowledge_nodes = [
                node for node in ((unit.data.get("knowledge_map") or {}).get("nodes", []) or [])
                if isinstance(node, dict)
            ]
            knowledge_ids = [node.get("id") for node in knowledge_nodes]
            if len(knowledge_ids) != len(set(knowledge_ids)):
                self.err("KNOWLEDGE-NODE-DUP",
                         f"unit '{uid}' knowledge-map node ids must be unique", where)
            known = set(knowledge_ids)
            for node in knowledge_nodes:
                for dependency in node.get("builds_on", []) or []:
                    if dependency not in known:
                        self.err("KNOWLEDGE-EDGE",
                                 f"unit '{uid}' knowledge node '{node.get('id')}' builds on unknown node '{dependency}'", where)

    def check_lifecycle_coherence(self):
        """A unit cannot be ready while every workspace that would do it is blocked.

        Algo 2 was, on 2026-08-08, four things at once: a `blocked` workspace
        saying "no study, next action none", a `ready` unit, a `ready` study map,
        and a `required-now` stage. Each file was individually valid — nothing
        compared them, so the repository asserted *do nothing* and *do this now*
        with equal confidence, and the UI could legitimately surface either.

        Administrative and operational state are allowed to disagree: the module
        stays `enrolled` because there was no university withdrawal. What is not
        allowed is two *operational* layers disagreeing about the same work.

        Scope is deliberately narrow — this fires only when the unit has at
        least one active workspace and EVERY one of them is blocked, which is
        what "sole execution context" means. A unit worked in two workspaces,
        one blocked, is ordinary and untouched.

        The audit suggested an explicit exception hatch. None is added yet: no
        real case needs one, and an unused escape route in a lifecycle rule is
        an invitation to silence the rule rather than fix the state. If one ever
        appears, an optional `lifecycle_exception` on the unit is the shape to
        add — with a schema bump, so the exception is itself declared.
        """
        r = self.repo
        active = r.active_workspaces()
        blocked = {w.id for w in active if w.status == "blocked"}
        if not blocked or not r.units:
            return
        maps_by_unit = {sm.unit_id: sm for sm in r.study_maps.values()}
        for uid, unit in sorted(r.units.items()):
            # Read the join from both sides: either declaration is enough to
            # count as a context, so a one-sided edit can only ever ADD an
            # unblocked context and relax this rule, never invent a failure.
            declared = set(unit.data.get("workspace_ids") or [])
            contexts = {w.id for w in active
                        if uid in (w.meta.get("unit_ids") or []) or w.id in declared}
            if not contexts or not contexts.issubset(blocked):
                continue
            names = ", ".join(sorted(contexts))
            if unit.data.get("status") in {"ready", "active"}:
                self.err("LIFECYCLE-BLOCKED-UNIT",
                         f"unit '{uid}' is '{unit.data.get('status')}' but every workspace "
                         f"that would carry it is blocked ({names}) — pause the unit, or "
                         f"unblock the workspace; the repository must not say both",
                         self._rel(unit.path))
            study_map = maps_by_unit.get(uid)
            # StudyMap is a plain record holder — no status property, unlike
            # Workspace and LearningPath. Read the field.
            map_status = study_map.data.get("status") if study_map is not None else None
            if map_status in {"ready", "active"}:
                self.err("LIFECYCLE-BLOCKED-MAP",
                         f"study map '{study_map.id}' is '{map_status}' but its unit's "
                         f"only execution context is blocked ({names}) — pause the map with "
                         f"the unit; its stages stay as the reinstatement plan",
                         self._rel(study_map.path))

    def check_study_maps(self):
        # The manifest publishes `stages` as a FLAT by-id index (ADR-006, fifth
        # addendum), so stage ids must be unique across the whole repository and
        # not merely inside one map: a reused id makes resolution ambiguous, and
        # a consumer holding only the id silently gets whichever map was
        # projected last.
        owners: dict[str, list] = {}
        for study_map in self.repo.study_maps.values():
            for stage in study_map.data.get("stages", []) or []:
                if isinstance(stage, dict) and stage.get("id"):
                    owners.setdefault(str(stage["id"]), []).append(study_map)
        for stage_id, maps in sorted(owners.items()):
            if len(maps) > 1:
                names = ", ".join(sorted(str(m.data.get("id")) for m in maps))
                self.err("MAP-STAGE-GLOBAL-DUP",
                         f"stage id '{stage_id}' is used by {len(maps)} study maps "
                         f"({names}); stages are indexed by id alone",
                         self._rel(maps[0].path))

        # Resource identity (ADR-009). A resource id names a teaching object, NOT
        # one citation of it. The same paper legitimately appears on several
        # stages — AMLS cites "Attention Is All You Need" from both L04 and L07 —
        # and that reuse is the point: feedback accumulates on the paper instead
        # of scattering across the plans that happen to mention it. So repeated
        # ids are legal; what must not vary is WHAT the id denotes. An id that
        # pointed at two different papers would make every judgment filed under
        # it ambiguous.
        #
        # Labels are deliberately excluded from the identity check: the same
        # paper is cited as "Hidden Technical Debt in Machine Learning Systems"
        # in L01 and "…in ML Systems" in L02. Same object, different wording —
        # normalizing that would be rewriting Aram's prose to satisfy a linter.
        res_uses: dict[str, list[tuple]] = {}
        for study_map in self.repo.study_maps.values():
            for stage in study_map.data.get("stages", []) or []:
                if not isinstance(stage, dict):
                    continue
                for resource in stage.get("resources", []) or []:
                    if isinstance(resource, dict) and resource.get("id"):
                        res_uses.setdefault(str(resource["id"]), []).append(
                            (study_map, stage.get("id"), resource))
        for resource_id, uses in sorted(res_uses.items()):
            if len(uses) < 2:
                continue
            where_list = ", ".join(sorted(
                f"{m.data.get('id')}/{sid}" for m, sid, _ in uses))
            for field in ("source_id", "url", "vault_path"):
                seen = {str(r.get(field)) for _, _, r in uses if r.get(field)}
                if len(seen) > 1:
                    self.err("RESOURCE-ID-CONFLICT",
                             f"resource id '{resource_id}' is used {len(uses)} times "
                             f"({where_list}) with different {field}: "
                             f"{', '.join(sorted(seen))}; one id must denote one object",
                             self._rel(uses[0][0].path))

        for study_map in self.repo.study_maps.values():
            where = self._rel(study_map.path)
            data = study_map.data
            stages = data.get("stages", []) or []
            if not isinstance(stages, list):
                continue
            ids = [s.get("id") for s in stages if isinstance(s, dict)]
            if len(ids) != len(set(ids)):
                self.err("MAP-STAGE-DUP", "study-map stage ids must be unique", where)
            current = data.get("current_stage")
            if current not in ids:
                self.err("MAP-CURRENT", f"current_stage '{current}' does not identify a stage", where)
            active = [s.get("id") for s in stages if isinstance(s, dict)
                      and s.get("status") == "active"]
            if data.get("status") == "active" and active != [current]:
                self.err("MAP-ACTIVE",
                         "an active study map must have exactly one active current stage", where)
            if data.get("status") != "active" and len(active) > 0:
                self.err("MAP-ACTIVE",
                         "a non-active study map may not contain an active stage", where)
            for stage in stages:
                if not isinstance(stage, dict):
                    continue
                note_ref = stage.get("working_note")
                if note_ref:
                    target = self.repo.root / str(note_ref)
                    expected_unit = study_map.path.parent.resolve()
                    try:
                        target.resolve().relative_to(expected_unit)
                    except (ValueError, OSError):
                        self.err("MAP-NOTE-OWNER",
                                 f"working note escapes owning unit: '{note_ref}'", where)
                    if not target.is_file():
                        self.err("MAP-NOTE-MISSING", f"working note does not exist: '{note_ref}'", where)
                if stage.get("completed") and stage.get("status") != "complete":
                    self.err("MAP-COMPLETED-DATE",
                             f"stage '{stage.get('id')}' has a completion date but is not complete", where)

                # A resource_id on feedback must resolve to a resource on the SAME
                # stage, and agree with the source that resource belongs to.
                # Otherwise the narrowing is a dangling pointer: it looks more
                # precise than source-level feedback while actually saying less
                # (ADR-009).
                stage_resources = {
                    str(r["id"]): r for r in (stage.get("resources", []) or [])
                    if isinstance(r, dict) and r.get("id")
                }
                for entry in stage.get("source_feedback", []) or []:
                    if not isinstance(entry, dict):
                        continue
                    rid = entry.get("resource_id")
                    if not rid:
                        continue
                    resource = stage_resources.get(str(rid))
                    if resource is None:
                        self.err("FEEDBACK-RESOURCE",
                                 f"stage '{stage.get('id')}' records feedback for resource "
                                 f"'{rid}', which is not a resource on that stage", where)
                        continue
                    declared = resource.get("source_id")
                    if declared and declared != entry.get("source_id"):
                        self.err("FEEDBACK-RESOURCE-SOURCE",
                                 f"stage '{stage.get('id')}' feedback for '{rid}' claims source "
                                 f"'{entry.get('source_id')}' but the resource belongs to "
                                 f"'{declared}'", where)
            stage_ids = set(ids)
            detour_ids: set[str] = set()
            for detour in data.get("detours", []) or []:
                did = detour.get("id")
                if did in detour_ids:
                    self.err("DETOUR-DUP", f"duplicate detour id '{did}'", where)
                detour_ids.add(did)
                for field in ("spawned_by_stage", "return_to_stage"):
                    if detour.get(field) not in stage_ids:
                        self.err("DETOUR-STAGE",
                                 f"detour '{did}' {field} does not resolve to a stage", where)

    def check_learning_paths(self):
        """Ordered-stage invariants that JSON Schema cannot express cleanly."""
        for learning_path in self.repo.learning_paths.values():
            where = self._rel(learning_path.path)
            data = learning_path.data
            stages = data.get("stages", []) or []
            if not isinstance(stages, list):
                continue  # schema reports the structural error
            ids = [s.get("id") for s in stages if isinstance(s, dict)]
            if len(ids) != len(set(ids)):
                self.err("PATH-STAGE-DUP", "learning path stage ids must be unique", where)
            current = data.get("current_stage")
            if current not in ids:
                self.err("PATH-CURRENT",
                         f"current_stage '{current}' does not identify a stage", where)
            active = [s.get("id") for s in stages if isinstance(s, dict)
                      and s.get("status") == "active"]
            if data.get("status") == "active":
                if active != [current]:
                    self.err("PATH-ACTIVE",
                             "an active path must have exactly one active stage, equal to current_stage",
                             where)
            elif len(active) > 1:
                self.err("PATH-ACTIVE", "a path may not have multiple active stages", where)
            for stage in stages:
                if not isinstance(stage, dict):
                    continue
                note_path = stage.get("notes_path")
                if note_path:
                    target = self.repo.root / str(note_path)
                    try:
                        target.resolve().relative_to(learning_path.path.parent.parent.resolve())
                    except (ValueError, OSError):
                        self.err("PATH-NOTE-OWNER",
                                 f"stage notes_path escapes owning workspace: '{note_path}'",
                                 where)
            proposal = (data.get("shelving") or {}).get("proposal_path") \
                if isinstance(data.get("shelving") or {}, dict) else None
            if proposal:
                target = self.repo.root / str(proposal)
                try:
                    target.resolve().relative_to(learning_path.path.parent.parent.resolve())
                except (ValueError, OSError):
                    self.err("PATH-SHELVE-OWNER",
                             f"shelving proposal escapes owning workspace: '{proposal}'",
                             where)

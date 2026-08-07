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
            actual = [u.id for u in r.units.values() if u.module_id == mid]
            if set(ordered) != set(actual) or len(ordered) != len(actual):
                self.err("UNIT-ORDER",
                         f"module '{mid}' unit_order must contain every owned unit exactly once",
                         where)
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

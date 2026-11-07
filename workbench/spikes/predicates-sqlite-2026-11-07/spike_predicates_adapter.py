"""Relational SQLite adapter for semantic predicates (Task B.3).

Provides `SqlPredicateEvaluator`, which evaluates all 27 semantic predicates
via SQLite queries, views, and temporary relational tables. Fully matches
the `evaluate(name, **inputs)` production interface and fail-closed contract.
"""

from __future__ import annotations

import re
import sqlite3
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from learning_os.domain.route_identity import ROUTE_ID_RE
from learning_os.domain.vocabulary import EVIDENCE_SCHEMES, ID_RE, RELATION_TYPES, UNIT_ID_RE
from learning_os.store.contracts.write_scopes import WriteScopeError, scope_matches

try:
    from .spike_predicates_schema import FACT_OWNER_ROWS, init_schema
    from .spike_predicates_views import init_views
except ImportError:
    from spike_predicates_schema import FACT_OWNER_ROWS, init_schema
    from spike_predicates_views import init_views

CONTRACT_VERSION: Final[int] = 3


@dataclass(frozen=True)
class PredicateMeta:
    name: str
    version: int
    authoritative_inputs: tuple[str, ...]
    authority: str
    description: str


def _sql_scope_match(target: object, pattern: object) -> int:
    """UDF for SQLite write-scope matching."""
    if not isinstance(target, str) or not isinstance(pattern, str):
        return 0
    try:
        return 1 if scope_matches(target, pattern) else 0
    except WriteScopeError:
        return 0


def _sql_regex_match(pattern: str, val: object) -> int:
    """UDF for regex matching."""
    if not isinstance(val, str):
        return 0
    return 1 if re.match(pattern, val) is not None else 0


class SqlPredicateEvaluator:
    """In-memory SQLite evaluator executing semantic predicates via SQL."""

    def __init__(self) -> None:
        self._conn = sqlite3.connect(":memory:")
        self._conn.row_factory = sqlite3.Row
        self._conn.create_function("scope_matches", 2, _sql_scope_match)
        self._conn.create_function("regex_match", 2, _sql_regex_match)
        init_schema(self._conn)
        init_views(self._conn)
        self._init_meta()

    def _init_meta(self) -> None:
        from learning_os.derive.semantics.predicates import PREDICATES as PROD_PREDICATES
        self.metadata: dict[str, PredicateMeta] = {
            name: PredicateMeta(
                name=p.name,
                version=p.version,
                authoritative_inputs=p.authoritative_inputs,
                authority=p.authority,
                description=p.description,
            )
            for name, p in PROD_PREDICATES.items()
        }

    @property
    def connection(self) -> sqlite3.Connection:
        return self._conn

    def evaluate(self, name: str, **inputs: object) -> object:
        """Evaluate a semantic predicate through SQLite queries."""
        import learning_os.derive.semantics.predicates as _p_mod
        if name not in self.metadata:
            # Check dynamic monkeypatch in PREDICATES
            if hasattr(_p_mod, "PREDICATES") and name in _p_mod.PREDICATES:
                entry = _p_mod.PREDICATES[name]
                if hasattr(entry, "function"):
                    return entry.function(**inputs)
            raise KeyError(f"unknown semantic predicate: {name!r}")

        handler = getattr(self, f"_eval_{name}", None)
        if handler is None:
            raise KeyError(f"unimplemented SQL evaluator for predicate: {name!r}")
        return handler(**inputs)

    # -------------------------------------------------------------------------
    # Predicate Handlers (All 27 evaluated via SQLite)
    # -------------------------------------------------------------------------

    def _eval_NeedsStudyMap(self, *, unit_status: object, module_status: object, has_study_map: object) -> bool:
        cur = self._conn.execute(
            """
            SELECT CASE
                WHEN :has_study_map != 0 THEN 0
                WHEN :module_status IS NULL OR :module_status NOT IN (SELECT term FROM vocabulary_terms WHERE category = 'studied_module_status') THEN 0
                WHEN :unit_status IS NOT NULL AND :unit_status IN (SELECT term FROM vocabulary_terms WHERE category = 'unit_status_without_obligation') THEN 0
                ELSE 1
            END
            """,
            {
                "has_study_map": 1 if has_study_map else 0,
                "module_status": str(module_status) if module_status is not None else None,
                "unit_status": str(unit_status) if unit_status is not None else None,
            },
        )
        return bool(cur.fetchone()[0])

    def _eval_NeedsScope(self, *, module_kind: object, module_status: object, unit_count: object, owned: object) -> bool:
        cur = self._conn.execute(
            """
            SELECT CASE
                WHEN :owned = 0 THEN 0
                WHEN :module_kind IS NULL OR :module_kind NOT IN (SELECT term FROM vocabulary_terms WHERE category = 'academic_module_kind') THEN 0
                WHEN :module_status IS NULL OR :module_status NOT IN (SELECT term FROM vocabulary_terms WHERE category = 'studied_module_status') THEN 0
                WHEN CAST(:unit_count AS INTEGER) <= 0 THEN 1
                ELSE 0
            END
            """,
            {
                "owned": 1 if owned else 0,
                "module_kind": str(module_kind) if module_kind is not None else None,
                "module_status": str(module_status) if module_status is not None else None,
                "unit_count": int(unit_count or 0) if isinstance(unit_count, (int, float)) else 0,
            },
        )
        return bool(cur.fetchone()[0])

    def _eval_ScopeAuthority(
        self,
        *,
        fact_kind: object,
        module_id: object = "",
        unit_id: object = "",
        workspace_id: object = "",
        note_id: object = "",
        program_id: object = "",
        source_id: object = "",
    ) -> str:
        cur = self._conn.execute(
            """
            SELECT template, req_module, req_unit, req_workspace, req_note, req_program, req_source
            FROM fact_owners
            WHERE fact_kind = :fact_kind
            """,
            {"fact_kind": str(fact_kind or "")},
        )
        row = cur.fetchone()
        if row is None:
            return "unknown"

        provided = {
            "module_id": str(module_id or ""),
            "unit_id": str(unit_id or ""),
            "workspace_id": str(workspace_id or ""),
            "note_id": str(note_id or ""),
            "program_id": str(program_id or ""),
            "source_id": str(source_id or ""),
        }
        req_checks = (
            (row["req_module"], "module_id"),
            (row["req_unit"], "unit_id"),
            (row["req_workspace"], "workspace_id"),
            (row["req_note"], "note_id"),
            (row["req_program"], "program_id"),
            (row["req_source"], "source_id"),
        )
        if any(req and not provided[field] for req, field in req_checks):
            return "unknown"

        return row["template"].format(**provided)

    def _eval_AllowedMutation(self, *, capability: object, target_path: object, scopes: object) -> bool:
        if not isinstance(capability, str) or not capability:
            return False
        if not isinstance(target_path, str) or not isinstance(scopes, Sequence):
            return False
        # Create temp table and run relational exists query with UDF
        with self._conn:
            self._conn.execute("CREATE TEMP TABLE IF NOT EXISTS _eval_scopes (pattern TEXT)")
            self._conn.execute("DELETE FROM _eval_scopes")
            valid_scopes = [(s,) for s in scopes if isinstance(s, str)]
            if not valid_scopes:
                return False
            self._conn.executemany("INSERT INTO _eval_scopes VALUES (?)", valid_scopes)
            cur = self._conn.execute(
                "SELECT EXISTS (SELECT 1 FROM _eval_scopes WHERE scope_matches(:target, pattern) = 1)",
                {"target": target_path},
            )
            return bool(cur.fetchone()[0])

    def _eval_ShelvingApproval(self, *, applied_items: object, approved_items: object) -> bool:
        if not applied_items or not approved_items:
            return False
        if not isinstance(applied_items, Sequence) or not isinstance(approved_items, Sequence):
            return False
        with self._conn:
            self._conn.execute("CREATE TEMP TABLE IF NOT EXISTS _eval_applied (item TEXT)")
            self._conn.execute("CREATE TEMP TABLE IF NOT EXISTS _eval_approved (item TEXT)")
            self._conn.execute("DELETE FROM _eval_applied")
            self._conn.execute("DELETE FROM _eval_approved")
            try:
                self._conn.executemany("INSERT INTO _eval_applied VALUES (?)", [(str(x),) for x in applied_items])
                self._conn.executemany("INSERT INTO _eval_approved VALUES (?)", [(str(x),) for x in approved_items])
            except Exception:
                return False
            # Relational anti-join: applied EXCEPT approved must be empty
            cur = self._conn.execute(
                "SELECT count(*) = 0 FROM (SELECT item FROM _eval_applied EXCEPT SELECT item FROM _eval_approved)"
            )
            return bool(cur.fetchone()[0])

    def _eval_CritiquePointActionable(self, *, status: object, authorized_in_session: object) -> str:
        cur = self._conn.execute(
            """
            SELECT CASE
                WHEN :status = 'open' THEN CASE WHEN :auth != 0 THEN 'actionable' ELSE 'deferred' END
                WHEN :status IN ('resolved', 'withdrawn') THEN 'closed'
                ELSE 'deferred'
            END
            """,
            {"status": str(status or ""), "auth": 1 if authorized_in_session else 0},
        )
        return str(cur.fetchone()[0])

    def _eval_MasteryDeclared(self, *, statement_kind: object) -> bool:
        cur = self._conn.execute(
            """
            SELECT CASE
                WHEN :kind IN (SELECT term FROM vocabulary_terms WHERE category = 'mastery_declaring_kind') THEN 1
                WHEN :kind IN (SELECT term FROM vocabulary_terms WHERE category = 'non_mastery_kind') THEN 0
                ELSE 1
            END
            """,
            {"kind": str(statement_kind or "")},
        )
        return bool(cur.fetchone()[0])

    def _eval_NoteChangeNeedsReview(self, *, change_kind: object) -> bool:
        cur = self._conn.execute(
            """
            SELECT CASE
                WHEN :kind IN (SELECT term FROM vocabulary_terms WHERE category = 'review_required_change') THEN 1
                WHEN :kind IN (SELECT term FROM vocabulary_terms WHERE category = 'review_free_change') THEN 0
                ELSE 1
            END
            """,
            {"kind": str(change_kind or "")},
        )
        return bool(cur.fetchone()[0])

    def _eval_EvidenceComplete(self, *, entries: object) -> bool:
        if not isinstance(entries, Sequence) or not entries:
            return False
        with self._conn:
            self._conn.execute("CREATE TEMP TABLE IF NOT EXISTS _eval_evidence (kind TEXT, ref TEXT, well_formed INTEGER)")
            self._conn.execute("DELETE FROM _eval_evidence")
            rows = []
            for e in entries:
                if not isinstance(e, Mapping):
                    return False
                kind = e.get("type")
                ref = e.get("ref")
                if not isinstance(kind, str) or not isinstance(ref, str) or not ref:
                    return False
                wf = 1 if (kind in ("derivation", "explanation", "implementation", "exercise", "exam", "external")
                           and ref.startswith(EVIDENCE_SCHEMES)) else 0
                rows.append((kind, ref, wf))
            self._conn.executemany("INSERT INTO _eval_evidence VALUES (?, ?, ?)", rows)

            # Query: all rows well_formed AND distinct count equals total count
            cur = self._conn.execute(
                """
                SELECT (min(well_formed) = 1) AND (count(*) = (SELECT count(DISTINCT kind || '::' || ref) FROM _eval_evidence))
                FROM _eval_evidence
                """
            )
            return bool(cur.fetchone()[0])

    def _eval_ClaimStale(
        self,
        *,
        read_contract_version: object,
        current_contract_version: object,
        read_revisions: object,
        current_revisions: object,
    ) -> bool:
        if read_contract_version != current_contract_version:
            return True
        if not isinstance(read_revisions, Mapping) or not isinstance(current_revisions, Mapping):
            return True
        if not read_revisions:
            return False

        with self._conn:
            self._conn.execute("CREATE TEMP TABLE IF NOT EXISTS _eval_read_revs (artifact TEXT, rev INTEGER)")
            self._conn.execute("CREATE TEMP TABLE IF NOT EXISTS _eval_curr_revs (artifact TEXT, rev INTEGER)")
            self._conn.execute("DELETE FROM _eval_read_revs")
            self._conn.execute("DELETE FROM _eval_curr_revs")
            try:
                self._conn.executemany("INSERT INTO _eval_read_revs VALUES (?, ?)", [(str(k), int(v)) for k, v in read_revisions.items()])
                curr_items = []
                for k in read_revisions:
                    if k in current_revisions:
                        curr_items.append((str(k), int(current_revisions[k])))
                self._conn.executemany("INSERT INTO _eval_curr_revs VALUES (?, ?)", curr_items)
            except (ValueError, TypeError):
                return True

            # Pure anti-join: exists any read artifact missing from current or having different revision
            cur = self._conn.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM _eval_read_revs r
                    LEFT JOIN _eval_curr_revs c ON r.artifact = c.artifact
                    WHERE c.artifact IS NULL OR c.rev != r.rev
                )
                """
            )
            return bool(cur.fetchone()[0])

    def _eval_SourceComplete(self, *, selection_state: object, locator_ok: object, deferral_reason: object = "") -> bool:
        cur = self._conn.execute(
            """
            SELECT CASE
                WHEN :state IN (SELECT term FROM vocabulary_terms WHERE category = 'selected_source_state')
                    THEN CASE WHEN :loc != 0 THEN 1 ELSE 0 END
                WHEN :state = 'deferred'
                    THEN CASE WHEN length(trim(COALESCE(:reason, ''))) > 0 THEN 1 ELSE 0 END
                ELSE 0
            END
            """,
            {
                "state": str(selection_state or ""),
                "loc": 1 if locator_ok else 0,
                "reason": str(deferral_reason) if isinstance(deferral_reason, str) else "",
            },
        )
        return bool(cur.fetchone()[0])

    def _eval_RouteValid(self, *, route_id: object, unit_id: object, source_id: object, locator: object) -> bool:
        if not all(isinstance(x, str) for x in (route_id, unit_id, source_id, locator)):
            return False
        cur = self._conn.execute(
            """
            SELECT CASE
                WHEN regex_match('^route-[0-9a-f]{24}$', :route_id) = 1
                 AND regex_match('^unit-[a-z0-9-]+$', :unit_id) = 1
                 AND regex_match('^[a-z0-9-]+$', :source_id) = 1
                 AND length(trim(:locator)) > 0
                THEN 1
                ELSE 0
            END
            """,
            {"route_id": route_id, "unit_id": unit_id, "source_id": source_id, "locator": locator},
        )
        return bool(cur.fetchone()[0])

    def _eval_RouteEvaluated(self, *, scope: object) -> bool:
        cur = self._conn.execute(
            """
            SELECT CASE
                WHEN :scope IN (SELECT term FROM vocabulary_terms WHERE category = 'route_scope')
                 AND :scope != 'unevaluated' THEN 1
                ELSE 0
            END
            """,
            {"scope": str(scope or "")},
        )
        return bool(cur.fetchone()[0])

    def _eval_StudyMapGrounded(
        self,
        *,
        template_version: object,
        resource_pairs: object,
        menu_pairs: object,
    ) -> bool:
        if type(template_version) is not int or template_version != 1:
            return False
        if not isinstance(resource_pairs, Sequence) or not isinstance(menu_pairs, Sequence):
            return False

        with self._conn:
            self._conn.execute("CREATE TEMP TABLE IF NOT EXISTS _eval_res (source_id TEXT, locator TEXT)")
            self._conn.execute("CREATE TEMP TABLE IF NOT EXISTS _eval_menu (source_id TEXT, locator TEXT)")
            self._conn.execute("DELETE FROM _eval_res")
            self._conn.execute("DELETE FROM _eval_menu")

            def _clean(rows: Sequence) -> list[tuple[str, str]] | None:
                out = []
                for r in rows:
                    if not isinstance(r, Sequence) or len(r) != 2:
                        return None
                    s, loc = r
                    if not isinstance(s, str) or not isinstance(loc, str):
                        return None
                    out.append((s, loc))
                return out

            c_res = _clean(resource_pairs)
            c_menu = _clean(menu_pairs)
            if c_res is None or c_menu is None:
                return False

            self._conn.executemany("INSERT INTO _eval_res VALUES (?, ?)", c_res)
            self._conn.executemany("INSERT INTO _eval_menu VALUES (?, ?)", c_menu)

            cur = self._conn.execute(
                "SELECT count(*) = 0 FROM (SELECT source_id, locator FROM _eval_res EXCEPT SELECT source_id, locator FROM _eval_menu)"
            )
            return bool(cur.fetchone()[0])

    def _eval_PlanTemplateCurrent(self, *, template_version: object) -> bool:
        if type(template_version) is not int:
            return False
        cur = self._conn.execute("SELECT CASE WHEN :ver = 1 THEN 1 ELSE 0 END", {"ver": template_version})
        return bool(cur.fetchone()[0])

    def _eval_RepoClean(self, *, error_count: object, new_or_grown_warnings: object) -> bool:
        cur = self._conn.execute(
            "SELECT CASE WHEN :err = 0 AND :warn = 0 THEN 1 ELSE 0 END",
            {"err": int(error_count or 0), "warn": int(new_or_grown_warnings or 0)},
        )
        return bool(cur.fetchone()[0])

    def _eval_SnapshotFresh(self, *, expected_snapshot: object, current_snapshot: object) -> bool:
        if not isinstance(expected_snapshot, str) or not isinstance(current_snapshot, str):
            return False
        cur = self._conn.execute(
            """
            SELECT CASE
                WHEN length(:exp) > 0 AND :exp = :curr THEN 1
                ELSE 0
            END
            """,
            {"exp": expected_snapshot, "curr": current_snapshot},
        )
        return bool(cur.fetchone()[0])

    def _eval_CanonicalWritePath(self, *, channel: object) -> bool:
        cur = self._conn.execute(
            "SELECT CASE WHEN :ch IN (SELECT term FROM vocabulary_terms WHERE category = 'canonical_write_channel') THEN 1 ELSE 0 END",
            {"ch": str(channel or "")},
        )
        return bool(cur.fetchone()[0])

    def _eval_WorkspaceMayCoordinate(self, *, claim_kind: object) -> bool:
        cur = self._conn.execute(
            "SELECT CASE WHEN :k IN (SELECT term FROM vocabulary_terms WHERE category = 'workspace_coordination_kind') THEN 1 ELSE 0 END",
            {"k": str(claim_kind or "")},
        )
        return bool(cur.fetchone()[0])

    def _eval_QuarantineExcluded(self, *, path: object) -> bool:
        if not isinstance(path, str) or not path or "\\" in path or "\x00" in path:
            return True
        if path.startswith("/") or path.startswith("Stratum/") or path == "Stratum":
            return True
        parts = path.split("/")
        if any(p in {"", ".", ".."} for p in parts):
            return True
        clean = "/".join(parts)
        cur = self._conn.execute(
            "SELECT CASE WHEN :path = 'curriculum/quarantine' OR :path LIKE 'curriculum/quarantine/%' THEN 1 ELSE 0 END",
            {"path": clean},
        )
        return bool(cur.fetchone()[0])

    def _eval_ExternalSibling(self, *, path: object) -> bool:
        if not isinstance(path, str) or not path:
            return True
        cur = self._conn.execute(
            """
            SELECT CASE
                WHEN :path LIKE '/%' OR :path = 'Stratum' OR :path LIKE 'Stratum/%' OR :path LIKE '%/../%' OR :path LIKE '../%' OR :path LIKE '%/..' THEN 1
                ELSE 0
            END
            """,
            {"path": path},
        )
        return bool(cur.fetchone()[0])

    def _eval_RelationMayApply(self, *, relation_type: object, from_id: object, to_id: object, inferred: object) -> bool:
        if inferred:
            return False
        if not all(isinstance(x, str) for x in (relation_type, from_id, to_id)):
            return False
        cur = self._conn.execute(
            """
            SELECT CASE
                WHEN :rel IN ('requires', 'builds-on', 'exemplifies', 'generalizes', 'contrasts-with')
                 AND regex_match('^[a-z0-9-]+$', :from_id) = 1
                 AND regex_match('^[a-z0-9-]+$', :to_id) = 1
                THEN 1
                ELSE 0
            END
            """,
            {"rel": relation_type, "from_id": from_id, "to_id": to_id},
        )
        return bool(cur.fetchone()[0])

    def _eval_DossierFresh(self, *, cached_hashes: object, current_hashes: object) -> bool:
        if not isinstance(cached_hashes, Mapping) or not cached_hashes:
            return False
        if not isinstance(current_hashes, Mapping) or not current_hashes:
            return False

        with self._conn:
            self._conn.execute("CREATE TEMP TABLE IF NOT EXISTS _eval_cached_h (k TEXT, v TEXT)")
            self._conn.execute("CREATE TEMP TABLE IF NOT EXISTS _eval_curr_h (k TEXT, v TEXT)")
            self._conn.execute("DELETE FROM _eval_cached_h")
            self._conn.execute("DELETE FROM _eval_curr_h")
            try:
                self._conn.executemany("INSERT INTO _eval_cached_h VALUES (?, ?)", [(str(k), str(v)) for k, v in cached_hashes.items()])
                self._conn.executemany("INSERT INTO _eval_curr_h VALUES (?, ?)", [(str(k), str(v)) for k, v in current_hashes.items()])
            except (ValueError, TypeError):
                return False

            cur = self._conn.execute(
                """
                SELECT (SELECT count(*) FROM (SELECT k, v FROM _eval_cached_h EXCEPT SELECT k, v FROM _eval_curr_h)) = 0
                   AND (SELECT count(*) FROM (SELECT k, v FROM _eval_curr_h EXCEPT SELECT k, v FROM _eval_cached_h)) = 0
                """
            )
            return bool(cur.fetchone()[0])

    def _eval_AttemptConsistent(self, *, attempt_termins: object, sitting_termins: object) -> bool:
        if not isinstance(attempt_termins, Sequence) or not isinstance(sitting_termins, Sequence):
            return False
        with self._conn:
            self._conn.execute("CREATE TEMP TABLE IF NOT EXISTS _eval_att (t INTEGER)")
            self._conn.execute("CREATE TEMP TABLE IF NOT EXISTS _eval_sit (t INTEGER)")
            self._conn.execute("DELETE FROM _eval_att")
            self._conn.execute("DELETE FROM _eval_sit")
            try:
                self._conn.executemany("INSERT INTO _eval_att VALUES (?)", [(int(t),) for t in attempt_termins])
                self._conn.executemany("INSERT INTO _eval_sit VALUES (?)", [(int(t),) for t in sitting_termins])
            except (ValueError, TypeError):
                return False

            cur = self._conn.execute(
                "SELECT count(*) = 0 FROM (SELECT t FROM _eval_att EXCEPT SELECT t FROM _eval_sit)"
            )
            return bool(cur.fetchone()[0])

    def _eval_NeedsSourceReview(self, *, reviewed: object, bytes_current: object) -> bool:
        if not isinstance(reviewed, bool) or not isinstance(bytes_current, bool):
            return False
        cur = self._conn.execute(
            "SELECT CASE WHEN :rev = 0 OR :curr = 0 THEN 1 ELSE 0 END",
            {"rev": 1 if reviewed else 0, "curr": 1 if bytes_current else 0},
        )
        return bool(cur.fetchone()[0])

    def _eval_RequiresHumanJudgment(self, *, decision_kind: object, rule_decidable: object) -> bool:
        if not isinstance(decision_kind, str) or not decision_kind:
            return False
        if not isinstance(rule_decidable, bool):
            return False
        cur = self._conn.execute(
            """
            SELECT CASE
                WHEN :kind IN (SELECT term FROM vocabulary_terms WHERE category = 'judgment_only') THEN 1
                WHEN :dec = 0 THEN 1
                ELSE 0
            END
            """,
            {"kind": decision_kind, "dec": 1 if rule_decidable else 0},
        )
        return bool(cur.fetchone()[0])

    def _eval_CurrentScopeAuthority(
        self,
        *,
        fact_kind: object,
        module_id: object = "",
        unit_id: object = "",
        workspace_id: object = "",
        note_id: object = "",
        program_id: object = "",
        source_id: object = "",
        superseded: object = (),
        replacement: object = "",
    ) -> str:
        owner = self._eval_ScopeAuthority(
            fact_kind=fact_kind,
            module_id=module_id,
            unit_id=unit_id,
            workspace_id=workspace_id,
            note_id=note_id,
            program_id=program_id,
            source_id=source_id,
        )
        if owner == "unknown":
            return "unknown"
        if isinstance(superseded, str):
            return "unknown"

        with self._conn:
            self._conn.execute("CREATE TEMP TABLE IF NOT EXISTS _eval_superseded (path TEXT)")
            self._conn.execute("DELETE FROM _eval_superseded")
            try:
                self._conn.executemany("INSERT INTO _eval_superseded VALUES (?)", [(str(p),) for p in superseded])
            except (ValueError, TypeError):
                return "unknown"

            # Check if static owner is retired
            cur = self._conn.execute("SELECT EXISTS (SELECT 1 FROM _eval_superseded WHERE path = :p)", {"p": owner})
            is_superseded = bool(cur.fetchone()[0])
            if not is_superseded:
                return owner

            # Owner is superseded. Check replacement
            if not isinstance(replacement, str) or not replacement:
                return "unknown"

            cur = self._conn.execute("SELECT EXISTS (SELECT 1 FROM _eval_superseded WHERE path = :p)", {"p": replacement})
            rep_is_superseded = bool(cur.fetchone()[0])
            if rep_is_superseded:
                return "unknown"

            return replacement


# Singleton instance for simple evaluation
_GLOBAL_EVALUATOR: SqlPredicateEvaluator | None = None


def get_evaluator() -> SqlPredicateEvaluator:
    global _GLOBAL_EVALUATOR
    if _GLOBAL_EVALUATOR is None:
        _GLOBAL_EVALUATOR = SqlPredicateEvaluator()
    return _GLOBAL_EVALUATOR


def evaluate_sql(name: str, **inputs: object) -> object:
    """Drop-in functional replacement for learning_os.derive.semantics.predicates.evaluate."""
    return get_evaluator().evaluate(name, **inputs)

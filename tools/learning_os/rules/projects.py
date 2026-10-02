"""First-class projects, workspaces and transaction receipts."""

from __future__ import annotations

import yaml

from ..errors import TransactionFailure
from ..loading.yamlio import UniqueKeySafeLoader
from ..revisions import load_revisions
from .advisories import workspace_neglect_issues
from .common import REQUIRED_WORKSPACE_SECTIONS, id_list_items
from .receipt_cache import receipt_file_issues


class ChecksProjects:
    """Mixed into Validator; see rules/core.py."""
    def check_projects(self):
        r = self.repo

        def project_file_resolves(value) -> bool:
            if not isinstance(value, str) or not value.strip():
                return False
            candidate = (r.root / value).resolve()
            try:
                candidate.relative_to(r.root.resolve())
            except ValueError:
                return False
            return candidate.exists()

        relation_ids: set[str] = set()
        for project_id, project in r.projects.items():
            data = project.data
            where = self._rel(project.path)
            for module_id in id_list_items(data.get("linked_module_ids")):
                if module_id not in r.modules or r.modules[module_id].get("compatibility_only"):
                    self.err("REF-MODULE",
                             f"project '{project_id}' references unknown active module '{module_id}'", where)
            for unit_id in id_list_items(data.get("unit_ids")):
                if unit_id not in r.units:
                    self.err("REF-UNIT",
                             f"project '{project_id}' references unknown unit '{unit_id}'", where)
            for workspace_id in id_list_items(data.get("workspace_ids")):
                if workspace_id not in r.workspaces:
                    self.err("REF-WORKSPACE",
                             f"project '{project_id}' references unknown workspace '{workspace_id}'", where)
            for group_id in id_list_items(data.get("thematic_group_ids")):
                if group_id not in r.thematic_groups:
                    self.err("REF-THEMATIC-GROUP",
                             f"project '{project_id}' references unknown thematic group '{group_id}'", where)
            root_uri = str(data.get("root_uri", ""))
            if root_uri:
                self._check_uri(root_uri, where)
            for row in data.get("files", []) or []:
                path = row.get("path") if isinstance(row, dict) else None
                if isinstance(path, str) and not path.startswith(("project://", "github://")):
                    candidate = (r.root / path).resolve()
                    try:
                        candidate.relative_to(r.root.resolve())
                    except ValueError:
                        self.err("PROJECT-FILE",
                                 f"project '{project_id}' file path escapes the repository: '{path}'", where)
                    else:
                        if not candidate.exists():
                            self.warn("PROJECT-FILE",
                                      f"project '{project_id}' file does not exist: '{path}'", where)

        for old_id, project_id in r.project_aliases.items():
            where = self._rel(r.project_aliases_path) if r.project_aliases_path else "projects/aliases.yaml"
            if project_id not in r.projects:
                self.err("REF-PROJECT",
                         f"project alias '{old_id}' targets unknown project '{project_id}'", where)
            if old_id in r.projects:
                self.err("PROJECT-ALIAS",
                         f"project alias '{old_id}' shadows a canonical project", where)

        resolvers = {
            "module": lambda value: value in r.modules and not r.modules[value].get("compatibility_only"),
            "source": lambda value: value in r.sources,
            "topic-pack": lambda value: value in r.collections
                and r.collections[value].get("collection_kind") == "topic-pack",
            "note": lambda value: value in r.notes,
            "file": project_file_resolves,
        }
        for relation in r.project_relations:
            relation_id = relation.get("id")
            where = self._rel(r.project_relations_path) if r.project_relations_path else "projects/relations/project-relations.yaml"
            if relation_id in relation_ids:
                self.err("PROJECT-REL-DUP", f"duplicate project relationship '{relation_id}'", where)
            relation_ids.add(str(relation_id))
            project_id = relation.get("from_project_id")
            if project_id not in r.projects:
                self.err("REF-PROJECT",
                         f"relationship '{relation_id}' references unknown project '{project_id}'", where)
            to_type = relation.get("to_type")
            target = relation.get("path") if to_type == "file" and relation.get("path") else relation.get("to_id")
            resolver = resolvers.get(to_type)
            if resolver is None or not resolver(target):
                self.err("PROJECT-REL-ENDPOINT",
                         f"relationship '{relation_id}' target does not resolve: {to_type} '{target}'", where)

    def check_workspaces(self):
        r = self.repo
        for ws in r.active_workspaces():
            where = self._rel(ws.path)
            for heading in REQUIRED_WORKSPACE_SECTIONS:
                if ws.section(heading) is None:
                    self.err("WS-SECTION",
                             f"workspace '{ws.id}' is missing required body section '## {heading}'",
                             where)
        non_standing = [w for w in r.active_workspaces() if not w.standing]
        if len(non_standing) > 7:
            self.warn("WS-COUNT",
                      f"{len(non_standing)} non-standing active workspaces (target 3-7; finish or "
                      "archive something first)")
        # Neglect signal: active non-standing workspace untouched (per Git) for 21+ days
        self.issues.extend(workspace_neglect_issues(r))

    def check_transaction_receipts(self):
        # DEFERRED (JF-13 rebuild, 2026-09-26): detection is here, but
        # rebuilding the ledgers from receipts stays unbuilt. Audited then:
        # 301 receipts, 63 without idempotency keys (idempotency is not
        # rebuildable from receipts alone), and one real chain hole
        # (unit/study-map-aml-l10 1→2 on 2026-08-22) that naive max-after
        # replay would launder. The unblocker is recording idempotency
        # keys on every receipt going forward, plus quarantine-token
        # enforcement on the commit path — a write-path change, not a
        # reader. Until then a rebuild tool would be a false recovery.
        directory = self.repo.root / "operations" / "transactions"
        if not directory.is_dir():
            return
        try:
            load_revisions(self.repo.root)
        except TransactionFailure as exc:
            self.err(
                "TRANSACTION-REVISIONS",
                str(exc),
                "operations/transactions/revisions.yaml",
            )
        # The idempotency ledger is replay's only memory: an unreadable one
        # fails closed at commit time, but validate stayed silent over it
        # (JF-13/L2). A missing file is fine (no gateway writes yet).
        from ..evidence import _load_idempotency_entries
        try:
            _load_idempotency_entries(self.repo.root)
        except TransactionFailure as exc:
            self.err(
                "TRANSACTION-IDEMPOTENCY",
                str(exc),
                "operations/transactions/idempotency.yaml",
            )
        receipt_file_issues(self)

    def check_ai_action_requests(self):
        from ..ai_actions.support import REQUEST_ID_PATTERN, REQUEST_ID_RE
        directory = self.repo.root / "operations" / "ai-actions" / "requests"
        if not directory.is_dir():
            return
        for path in sorted(directory.glob("*/request.yaml")):
            try:
                data = yaml.load(
                    path.read_text(encoding="utf-8"), Loader=UniqueKeySafeLoader,
                ) or {}
            except Exception as exc:  # noqa: BLE001 - report as validation issue
                self.err("AI-REQUEST-BUNDLE", f"cannot parse request bundle: {exc}",
                         self._rel(path))
                continue
            if not isinstance(data, dict):
                self.err("AI-REQUEST-BUNDLE", "request bundle must contain a mapping",
                         self._rel(path))
                continue
            request_id = data.get("id")
            # The projection publishes this id verbatim into the manifest,
            # whose schema only accepts the ai-request pattern: anything else
            # breaks every projection read while validating clean (JF-08).
            if not isinstance(request_id, str) or not REQUEST_ID_RE.fullmatch(request_id):
                self.err("AI-REQUEST-ID",
                         f"request id {request_id!r} does not match {REQUEST_ID_PATTERN!r}; "
                         "remove or rename the bundle so reads can publish the manifest",
                         self._rel(path))

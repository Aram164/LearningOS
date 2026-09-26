"""First-class projects, workspaces and transaction receipts."""

from __future__ import annotations

import time

import yaml

from ..errors import TransactionFailure
from ..githistory import GitHistoryError
from ..loading.yamlio import UniqueKeySafeLoader
from ..revisions import load_revisions
from .common import REQUIRED_WORKSPACE_SECTIONS


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
            for module_id in data.get("linked_module_ids", []) or []:
                if module_id not in r.modules or r.modules[module_id].get("compatibility_only"):
                    self.err("REF-MODULE",
                             f"project '{project_id}' references unknown active module '{module_id}'", where)
            for unit_id in data.get("unit_ids", []) or []:
                if unit_id not in r.units:
                    self.err("REF-UNIT",
                             f"project '{project_id}' references unknown unit '{unit_id}'", where)
            for workspace_id in data.get("workspace_ids", []) or []:
                if workspace_id not in r.workspaces:
                    self.err("REF-WORKSPACE",
                             f"project '{project_id}' references unknown workspace '{workspace_id}'", where)
            for group_id in data.get("thematic_group_ids", []) or []:
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
        for ws in non_standing:
            try:
                ts = self._git_last_commit_ts(ws.path.parent)
            except GitHistoryError as exc:
                self.err("GIT-HISTORY", f"cannot check workspace neglect: {exc}")
                break
            if ts is None:
                continue
            days = (time.time() - ts) / 86400
            if days >= 21:
                self.warn("WS-NEGLECT",
                          f"workspace '{ws.id}' untouched for {int(days)} days (per Git)")

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
        seen: set[str] = set()
        seen_keys: dict[str, str] = {}
        for path in sorted(directory.glob("transaction-*.yaml")):
            try:
                # `yaml.safe_load` is the pure-Python loader: 214 receipts cost
                # about a second of parsing on every validate, and every
                # canonical write validates. This is the loader the rest of the
                # repository already reads through — LibYAML when the C
                # extension is present, and the same duplicate-key rule, which
                # no current receipt trips. A file it refuses is reported below
                # as an unparseable receipt rather than raised.
                data = yaml.load(
                    path.read_text(encoding="utf-8"), Loader=UniqueKeySafeLoader,
                ) or {}
            except Exception as exc:  # noqa: BLE001 - report as validation issue
                self.err("TRANSACTION-RECEIPT", f"cannot parse receipt: {exc}", self._rel(path))
                continue
            self._schema_check("transaction-receipt", data, self._rel(path))
            transaction_id = data.get("id") if isinstance(data, dict) else None
            if transaction_id in seen:
                self.err("TRANSACTION-RECEIPT",
                         f"duplicate transaction receipt id '{transaction_id}'", self._rel(path))
            seen.add(transaction_id)
            # Two committed receipts sharing one idempotency key is genuinely
            # ambiguous: replay can prove at most one of them. Ledger loss
            # followed by key reuse produces exactly this (JF-13/L4).
            request = data.get("request") if isinstance(data, dict) else None
            key = request.get("idempotency_key") if isinstance(request, dict) else None
            if isinstance(key, str) and key:
                first = seen_keys.setdefault(key, self._rel(path))
                if first != self._rel(path):
                    self.err("TRANSACTION-RECEIPT",
                             f"duplicate idempotency key '{key}' also committed "
                             f"in {first}", self._rel(path))

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

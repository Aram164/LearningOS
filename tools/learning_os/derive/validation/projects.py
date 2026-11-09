"""First-class projects, workspaces and transaction receipts."""

from __future__ import annotations

import yaml

from learning_os.derive.validation.advisories import workspace_neglect_issues
from learning_os.derive.validation.receipt_cache import receipt_file_issues
from learning_os.derive.validation.revision_ledger import revision_ledger_issues
from learning_os.domain.failures import TransactionFailure
from learning_os.domain.validation import REQUIRED_WORKSPACE_SECTIONS
from learning_os.store.loading.yamlio import UniqueKeySafeLoader
from learning_os.store.revisions import load_revisions


class ChecksProjects:
    """Mixed into Validator; see rules/core.py."""
    def check_projects(self):
        r = self.repo
        canonical = {**dict.fromkeys(r.units, "unit"),
                     **dict.fromkeys(r.workspaces, "workspace"),
                     **{key: "module" for key, row in r.modules.items()
                        if not row.get("compatibility_only")}}
        shadowed = set(canonical)

        def remember_identities(value):
            if isinstance(value, dict):
                if isinstance(value.get("id"), str):
                    shadowed.add(value["id"])
                for child in value.values():
                    remember_identities(child)
            elif isinstance(value, list):
                for child in value:
                    remember_identities(child)

        for old_id, target_id in r.project_aliases.items():
            where = self._rel(r.project_aliases_path) if r.project_aliases_path else "projects/aliases.yaml"
            if target_id not in canonical:
                self.err("REF-PROJECT",
                         f"compatibility alias '{old_id}' targets unknown canonical owner '{target_id}'", where)
            if old_id == target_id or target_id in r.project_aliases:
                self.err("PROJECT-ALIAS",
                         f"compatibility alias '{old_id}' must be a direct owner redirect", where)
            if old_id in shadowed:
                self.err("PROJECT-ALIAS",
                         f"compatibility alias '{old_id}' shadows a canonical owner", where)

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
        from learning_os.store.evidence import load_idempotency_entries as _load_idempotency_entries
        try:
            _load_idempotency_entries(self.repo.root)
        except TransactionFailure as exc:
            self.err(
                "TRANSACTION-IDEMPOTENCY",
                str(exc),
                "operations/transactions/idempotency.yaml",
            )
        # Committed history against the live ledger: the receipt pass hands
        # back each receipt's cached revision claims, so this re-parses
        # nothing (system/VALIDATION.md, TRANSACTION-REVISION-*).
        revision_ledger_issues(self, receipt_file_issues(self))

    def check_ai_action_requests(self):
        from learning_os.store.ai_actions.support import REQUEST_ID_PATTERN, REQUEST_ID_RE
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

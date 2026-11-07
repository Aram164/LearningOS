"""Committed revision history against the live revision ledger.

The transaction service raises an artifact's revision only under the
operator lock, by exactly one, in the same atomic commit that writes the
receipt recording the step, and it never removes a ledger key — deleting
an artifact raises its revision too. So two things hold for every
committed receipt, and a tree that breaks either had its ledger moved
outside the gateway: a git stash, reset or checkout that took
``revisions.yaml`` back while the receipt stayed.

- **Floor** (``TRANSACTION-REVISION-FLOOR``): the live ledger stands at or
  above every revision a receipt recorded.
- **Uniqueness** (``TRANSACTION-REVISION-REUSED``): no two receipts record
  one artifact reaching the same revision. Once a later write advances the
  artifact past a rolled-back step the floor holds again; the duplicate
  claim is then the only trace the rollback leaves.

Replay already checks the floor for one receipt, when that receipt's
idempotency row is resubmitted (``store.evidence.verify_committed_evidence``).
A rollback takes the row with the ledger, so replay never looks.

A rollback that can no longer be undone is recorded, never hidden: an
entry in ``operations/revision-retirements.yaml`` names one transaction,
the claims of it that are retired, the cause, and who decided. A retired
claim leaves both checks; every other claim on the same artifact,
including any later one, stays in. A malformed file retires nothing.

Receipts are read once, by ``receipt_cache`` (cached per receipt); this
module re-parses none of them. The ledger is read after every receipt, so
a write landing mid-run can only raise it — never fake a floor violation.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

import yaml

from learning_os.domain.failures import TransactionFailure
from learning_os.store.layout import PathBoundaryError, read_text_inside
from learning_os.store.loading.yamlio import UniqueKeySafeLoader
from learning_os.store.revisions import load_revisions

if TYPE_CHECKING:
    from learning_os.derive.validation.receipt_cache import ReceiptClaims, ReceiptValidator

RETIREMENTS_RELATIVE = "operations/revision-retirements.yaml"
RETIREMENTS_SCHEMA = "artifact-revision-retirements"
LEDGER_RELATIVE = "operations/transactions/revisions.yaml"


def _retired_claims(validator: ReceiptValidator,
                    by_id: dict[str, list[ReceiptClaims]]) -> set[tuple[str, str]]:
    """The ``(transaction id, artifact)`` claims the retirement record retires.

    Every entry must name one committed receipt by id and only artifacts that
    receipt recorded; anything else is ``TRANSACTION-RETIREMENT`` and retires
    nothing. An absent file retires nothing and is not an error.
    """
    root = validator.repo.root
    path = root / RETIREMENTS_RELATIVE
    if not path.exists() and not path.is_symlink():
        return set()
    try:
        data = yaml.load(read_text_inside(root, path), Loader=UniqueKeySafeLoader)
    except (OSError, PathBoundaryError, yaml.YAMLError, UnicodeDecodeError) as exc:
        validator.err("TRANSACTION-RETIREMENT",
                      f"cannot read the revision retirements: {exc}", RETIREMENTS_RELATIVE)
        return set()
    mark = len(validator.issues)
    validator._schema_check(RETIREMENTS_SCHEMA, data, RETIREMENTS_RELATIVE)
    if len(validator.issues) != mark:
        # Fail closed: a record that does not match its contract exempts no
        # claim, so whatever it meant to cover is reported as well.
        return set()
    retired: set[tuple[str, str]] = set()
    for index, entry in enumerate(data["retirements"]):
        transaction_id = entry["transaction"]
        where = f"retirement {index} ({transaction_id})"
        receipts = by_id.get(transaction_id, [])
        if len(receipts) != 1:
            state = "is not a committed receipt" if not receipts \
                else f"names {len(receipts)} receipts"
            validator.err("TRANSACTION-RETIREMENT",
                          f"{where}: that transaction id {state}", RETIREMENTS_RELATIVE)
            continue
        recorded = receipts[0].revisions
        for artifact in entry["artifacts"]:
            if artifact not in recorded:
                validator.err("TRANSACTION-RETIREMENT",
                              f"{where}: the receipt records no revision for '{artifact}'",
                              RETIREMENTS_RELATIVE)
            elif (transaction_id, artifact) in retired:
                validator.err("TRANSACTION-RETIREMENT",
                              f"{where}: the claim on '{artifact}' is already retired",
                              RETIREMENTS_RELATIVE)
            else:
                retired.add((transaction_id, artifact))
    return retired


def revision_ledger_issues(validator: ReceiptValidator,
                           receipts: list[ReceiptClaims]) -> None:
    """Report receipts whose recorded revisions the live ledger contradicts.

    ``receipts`` arrive in sorted-path order from ``receipt_file_issues``,
    so which receipt each issue names is deterministic: the first holder of
    an artifact's highest claim for the floor, the later of a duplicate pair
    for reuse (whose message names the first).
    """
    by_id: dict[str, list[ReceiptClaims]] = defaultdict(list)
    for receipt in receipts:
        if isinstance(receipt.transaction_id, str):
            by_id[receipt.transaction_id].append(receipt)
    retired = _retired_claims(validator, by_id)

    first_claim: dict[tuple[str, int], str] = {}
    highest: dict[str, tuple[int, str]] = {}
    for receipt in receipts:
        for artifact, after in sorted(receipt.revisions.items()):
            if (receipt.transaction_id, artifact) in retired:
                continue
            first = first_claim.setdefault((artifact, after), receipt.rel)
            if first != receipt.rel:
                validator.err(
                    "TRANSACTION-REVISION-REUSED",
                    f"'{artifact}' revision {after} is recorded by this receipt and by "
                    f"{first}: the revision ledger was moved back between the two "
                    "transactions, so the later one committed against a state that had "
                    "lost the earlier one. Restore what the rolled-back transaction "
                    "wrote, or record its loss in " + RETIREMENTS_RELATIVE,
                    receipt.rel)
            best = highest.get(artifact)
            if best is None or after > best[0]:
                highest[artifact] = (after, receipt.rel)

    # Read only now, after every receipt: a commit landing mid-run raises
    # the ledger, so it cannot manufacture a violation.
    try:
        live = load_revisions(validator.repo.root)
    except TransactionFailure as exc:
        if not any(issue.code == "TRANSACTION-REVISIONS" for issue in validator.issues):
            validator.err("TRANSACTION-REVISIONS", str(exc), LEDGER_RELATIVE)
        return
    for artifact in sorted(highest):
        after, rel = highest[artifact]
        current = live.get(artifact, 0)
        if current >= after:
            continue
        state = "has no ledger entry" if artifact not in live else f"stands at {current}"
        validator.err(
            "TRANSACTION-REVISION-FLOOR",
            f"the revision ledger contradicts this receipt: '{artifact}' {state}, "
            f"below the revision {after} this transaction recorded. The ledger was "
            "moved back outside the gateway (a git stash, reset or checkout); restore "
            "the rolled-back ledger and writes if they still exist, or record the loss "
            "in " + RETIREMENTS_RELATIVE,
            rel)

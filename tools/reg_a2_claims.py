"""2A §7 regression a2: a new module claims owned territory by declaration."""
from pathlib import Path


def run(root: Path) -> None:
    (root / "operations/transactions/transaction-20260101-000000-001.yaml").write_text("x", encoding="utf-8")
    (root / "operations/transactions/lineage.yaml").write_text("x", encoding="utf-8")
    (root / "operations/ai-actions/requests/reg.json").write_text("x", encoding="utf-8")
    (root / "archive/inbox/2026/reg.md").write_text("x", encoding="utf-8")
    (root / "system/contracts/reg.yaml").write_text("x", encoding="utf-8")

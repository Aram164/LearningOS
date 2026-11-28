"""2A §7 regression a2: a new module claims owned territory by declaration."""
import argparse
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description="2A regression a2 (never merged).")


def run(root: Path) -> None:
    (root / "operations/transactions/transaction-20260101-000000-001.yaml").write_text("x", encoding="utf-8")
    (root / "operations/transactions/lineage.yaml").write_text("x", encoding="utf-8")
    (root / "operations/ai-actions/requests/reg.json").write_text("x", encoding="utf-8")
    (root / "archive/inbox/2026/reg.md").write_text("x", encoding="utf-8")
    (root / "system/contracts/reg.yaml").write_text("x", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)  # the claimed writes stay uncalled, as in round 7
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

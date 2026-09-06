"""Dependency-light exception types shared across Core layers.

Leaf packages may raise these errors without importing the transaction engine.
The public compatibility surface remains ``learning_os.transactions``; this
module exists to keep projection and validation code below orchestration in the
dependency graph.
"""

from __future__ import annotations

from pathlib import Path


class TransactionFailure(Exception):
    """A governed write failed and its canonical changes were rolled back."""


def unreadable_refusal(root: Path, failures: list[tuple[Path, str]], action: str) -> str:
    """Why a command will not answer, naming the files it could not read.

    A count is not a diagnosis. The operator's next move is to open the file
    that failed and repair its frontmatter, and they cannot find it from
    "3 records failed to parse" — so the refusal names the paths and what the
    loader actually said about each, the way every other refusal here does.
    """
    def where(path) -> str:
        try:
            return str(Path(path).relative_to(root))
        except (ValueError, TypeError):
            return str(path)

    shown = "; ".join(f"{where(path)}: {message}" for path, message in failures[:5])
    more = f"; and {len(failures) - 5} more" if len(failures) > 5 else ""
    return (f"cannot {action}: {len(failures)} file(s) could not be read, so the answer "
            f"would silently omit them — {shown}{more}")

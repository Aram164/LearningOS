"""Dependency-light exception types shared across Core layers.

Leaf packages may raise these errors without importing the transaction engine.
The public compatibility surface remains ``learning_os.transactions``; this
module exists to keep projection and validation code below orchestration in the
dependency graph.
"""

from __future__ import annotations


class TransactionFailure(Exception):
    """A governed write failed and its canonical changes were rolled back."""

"""Re-export of the practice-item extraction (P6 step 33).

The parser lives in the domain layer (`learning_os.domain.practice`) so the
store-side eligibility checks can share it without a store->derive import.
This module keeps the projection-side import path the plan documents.
"""

from learning_os.domain.practice import (  # noqa: F401
    PRACTICE_ROLES,
    Extraction,
    PracticeDiagnostic,
    PracticeItem,
    content_sha256,
    extract_items,
    normalize_field,
)

__all__ = [
    "PRACTICE_ROLES", "Extraction", "PracticeDiagnostic", "PracticeItem",
    "content_sha256", "extract_items", "normalize_field",
]

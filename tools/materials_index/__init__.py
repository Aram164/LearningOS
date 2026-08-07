"""Materials catalogue builder.

A view over what is physically on disk plus the registered sources — never
canonical. Split from a single 1,260-line script whose largest single item was
a 415-line HTML template; that template now lives alone in `page.py`, where it
can be read as markup rather than scrolled past as a string literal.
"""

from __future__ import annotations

from .cli import main

__all__ = ["main"]

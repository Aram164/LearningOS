"""Rebuild the two AML maps whose resource targets must be re-projected.

P4 rebuilt every lecture map but its package builder copied a source-level
material directory into five stage resources.  The canonical projection is
fail-closed: it emits a local target only when the route identifies one safe,
file-shaped locator.  Rebuilding L01-L02 through that same projector restores
the exact files and leaves multi-file menus without a misleading open target.
"""

EDITS = {}
REBUILD_UNITS = {"unit-aml-l01", "unit-aml-l02"}

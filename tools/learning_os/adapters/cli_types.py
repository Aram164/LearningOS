"""CLI converter registry (PLAN D2).

Maps request-schema ``x-los-cli.type`` names to the very converter
callables the old parser used, so the generated parser passes identical
function objects and ``contracts.payloads`` identity checks keep working.
"""

from __future__ import annotations

from collections.abc import Callable

from learning_os.store.contracts.payloads import json_object, sha256_value

CONVERTERS: dict[str, Callable] = {
    "str": str,
    "int": int,
    "float": float,
    "json_object": json_object,
    "sha256_value": sha256_value,
}

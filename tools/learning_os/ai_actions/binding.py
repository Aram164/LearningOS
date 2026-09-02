"""Hash-bound AI delivery reads shared by live apply and receipt replay."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, cast

import yaml

from .errors import DeliveryValidationError
from .support import _inside, _sha256_bytes
from .types import DeliveryRecord


def validated_sha256(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"sha256:[a-f0-9]{64}", value
    ):
        raise DeliveryValidationError(
            f"{label} must be sha256 followed by 64 lowercase hexadecimal digits"
        )
    return value


def read_bound_delivery(
    directory: Path,
    *,
    delivery_sha256: str,
    artifact_sha256: dict[str, Any],
) -> tuple[DeliveryRecord, dict[str, bytes]]:
    """Read the exact delivery and artifact bytes approved by V2."""
    expected_delivery = validated_sha256(
        delivery_sha256, label="delivery_sha256"
    )
    delivery_path = directory / "delivery.yaml"
    if not delivery_path.is_file() or delivery_path.is_symlink():
        raise DeliveryValidationError(
            "approved delivery record is missing or is not a regular file"
        )
    try:
        delivery_bytes = delivery_path.read_bytes()
    except OSError as exc:
        raise DeliveryValidationError(
            f"approved delivery record is unreadable: {exc}"
        ) from exc
    if _sha256_bytes(delivery_bytes) != expected_delivery:
        raise DeliveryValidationError(
            "approved delivery content hash does not match the imported delivery record"
        )
    try:
        delivery = yaml.safe_load(delivery_bytes.decode("utf-8", errors="strict"))
    except (UnicodeError, yaml.YAMLError) as exc:
        raise DeliveryValidationError(
            f"approved delivery record is unreadable: {exc}"
        ) from exc
    if not isinstance(delivery, dict):
        raise DeliveryValidationError("delivery.yaml must contain a mapping")

    operations = delivery.get("operations")
    if not isinstance(operations, list):
        raise DeliveryValidationError("delivery operations must be a list")
    refs: set[str] = set()
    for operation in operations:
        if not isinstance(operation, dict):
            raise DeliveryValidationError("each delivery operation must be a mapping")
        artifact_ref = operation.get("artifact_ref")
        if artifact_ref is not None:
            if not isinstance(artifact_ref, str) or not artifact_ref:
                raise DeliveryValidationError(
                    "delivery artifact_ref must be a non-empty relative path"
                )
            refs.add(artifact_ref)
    if not isinstance(artifact_sha256, dict):
        raise DeliveryValidationError("artifact_sha256 must be an object")
    if any(not isinstance(key, str) or not key for key in artifact_sha256):
        raise DeliveryValidationError(
            "artifact_sha256 keys must be non-empty artifact_ref strings"
        )
    supplied = set(artifact_sha256)
    if supplied != refs:
        raise DeliveryValidationError(
            "approved delivery artifact hashes must bind exactly every artifact_ref "
            f"(missing={sorted(refs - supplied)}, unexpected={sorted(supplied - refs)})"
        )
    artifacts: dict[str, bytes] = {}
    for artifact_ref in sorted(refs):
        expected = validated_sha256(
            artifact_sha256[artifact_ref],
            label=f"artifact_sha256[{artifact_ref}]",
        )
        artifact = _inside(directory, artifact_ref)
        if not artifact.is_file() or artifact.is_symlink():
            raise DeliveryValidationError(
                "approved delivery artifact is missing or is not a regular file: "
                f"{artifact_ref}"
            )
        try:
            content = artifact.read_bytes()
        except OSError as exc:
            raise DeliveryValidationError(
                f"approved delivery artifact is unreadable: {artifact_ref}: {exc}"
            ) from exc
        if _sha256_bytes(content) != expected:
            raise DeliveryValidationError(
                "approved delivery artifact content hash does not match "
                f"the imported bytes: {artifact_ref}"
            )
        artifacts[artifact_ref] = content
    return cast(DeliveryRecord, delivery), artifacts

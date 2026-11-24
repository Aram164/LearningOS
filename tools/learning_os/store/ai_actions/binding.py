"""Hash-bound AI delivery reads shared by live apply and receipt replay."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, cast

import yaml

from learning_os.domain.ai_errors import DeliveryBindingError, DeliveryValidationError
from learning_os.domain.ai_types import DeliveryRecord
from learning_os.store.ai_actions.support import inside as _inside
from learning_os.store.ai_actions.support import sha256_bytes as _sha256_bytes


def validated_sha256(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(
        r"sha256:[a-f0-9]{64}", value
    ):
        raise DeliveryValidationError(
            f"{label} must be sha256 followed by 64 lowercase hexadecimal digits"
        )
    return value


def _read_delivery_bundle(
    directory: Path,
    *,
    expected_delivery: str | None = None,
    expected_artifacts: dict[str, Any] | None = None,
) -> tuple[DeliveryRecord, dict[str, bytes], str, dict[str, str]]:
    """Read a regular-file delivery record and every referenced artifact once."""
    delivery_path = directory / "delivery.yaml"
    if not delivery_path.is_file() or delivery_path.is_symlink():
        raise DeliveryBindingError(
            "approved delivery record is missing or is not a regular file"
        )
    try:
        delivery_bytes = delivery_path.read_bytes()
    except OSError as exc:
        raise DeliveryBindingError(
            f"approved delivery record is unreadable: {exc}"
        ) from exc
    actual_delivery = _sha256_bytes(delivery_bytes)
    if expected_delivery is not None and actual_delivery != expected_delivery:
        raise DeliveryBindingError(
            "approved delivery content hash does not match the imported delivery record"
        )
    try:
        delivery = yaml.safe_load(delivery_bytes.decode("utf-8", errors="strict"))
    except (UnicodeError, yaml.YAMLError) as exc:
        raise DeliveryBindingError(
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
    if expected_artifacts is not None:
        if not isinstance(expected_artifacts, dict):
            raise DeliveryValidationError("artifact_sha256 must be an object")
        if any(not isinstance(key, str) or not key for key in expected_artifacts):
            raise DeliveryValidationError(
                "artifact_sha256 keys must be non-empty artifact_ref strings"
            )
        supplied = set(expected_artifacts)
        if supplied != refs:
            raise DeliveryBindingError(
                "approved delivery artifact hashes must bind exactly every artifact_ref "
                f"(missing={sorted(refs - supplied)}, unexpected={sorted(supplied - refs)})"
            )
    artifacts: dict[str, bytes] = {}
    artifact_hashes: dict[str, str] = {}
    for artifact_ref in sorted(refs):
        expected = (
            validated_sha256(
                expected_artifacts[artifact_ref],
                label=f"artifact_sha256[{artifact_ref}]",
            )
            if expected_artifacts is not None
            else None
        )
        artifact = _inside(directory, artifact_ref)
        if not artifact.is_file() or artifact.is_symlink():
            raise DeliveryBindingError(
                "approved delivery artifact is missing or is not a regular file: "
                f"{artifact_ref}"
            )
        try:
            content = artifact.read_bytes()
        except OSError as exc:
            raise DeliveryBindingError(
                f"approved delivery artifact is unreadable: {artifact_ref}: {exc}"
            ) from exc
        actual = _sha256_bytes(content)
        if expected is not None and actual != expected:
            raise DeliveryBindingError(
                "approved delivery artifact content hash does not match "
                f"the imported bytes: {artifact_ref}"
            )
        artifacts[artifact_ref] = content
        artifact_hashes[artifact_ref] = actual
    return cast(DeliveryRecord, delivery), artifacts, actual_delivery, artifact_hashes


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
    delivery, artifacts, _delivery_sha, _artifact_shas = _read_delivery_bundle(
        directory,
        expected_delivery=expected_delivery,
        expected_artifacts=artifact_sha256,
    )
    return delivery, artifacts


def read_delivery_for_preview(
    directory: Path,
) -> tuple[DeliveryRecord, dict[str, bytes], str, dict[str, str]]:
    """Read a delivery and measure exact byte digests without pre-bound hashes."""
    return _read_delivery_bundle(directory)

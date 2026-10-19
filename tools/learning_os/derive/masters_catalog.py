"""The Master Planning catalog: its location, sanitized read and validation.

Read-only. Planning writes stay in ``learning_os.app.admin.masters_planning``,
which uses these to check what it commits; the health report reads the
catalog through the same functions.
"""

from __future__ import annotations

import ipaddress
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import yaml

from learning_os.store.contracts.json_schema import validate_contract
from learning_os.store.loader import load_repo


class MastersPlanningError(ValueError):
    pass


_FORBIDDEN_KEYS = frozenset({
    "job", "employer", "credential", "credentials", "account", "account_id",
    "private_url", "secret", "token", "application_material", "contact_details",
})


# Hosts that are personal storage, not public course material (D15). Exact
# set, never a heuristic: anything login-only beyond these is the approver's
# call, and anything here is refused with the candidate named.
_PERSONAL_LINK_HOSTS = frozenset({
    "drive.google.com", "docs.google.com",
    "dropbox.com", "www.dropbox.com", "dl.dropboxusercontent.com",
    "onedrive.live.com", "1drv.ms",
    "localhost", "127.0.0.1", "0.0.0.0", "::1",
})


def assert_academic_only(value: Any, *, pointer: str = "") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            name = str(key).casefold().replace("-", "_")
            if name in _FORBIDDEN_KEYS:
                raise MastersPlanningError(
                    f"sanitized Master Planning input contains forbidden field at {pointer}/{key}"
                )
            assert_academic_only(child, pointer=f"{pointer}/{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_academic_only(child, pointer=f"{pointer}/{index}")


def _sanitized_file(
    root: Path,
    path: Path,
    *,
    label: str,
    required: bool,
) -> Path | None:
    """Resolve one exact sanitized file without following any indirection."""
    root = root.resolve()
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise MastersPlanningError(f"{label} escapes the repository") from exc
    cursor = root
    for index, component in enumerate(relative.parts):
        cursor = cursor / component
        if cursor.is_symlink():
            raise MastersPlanningError(f"{label} traverses a symlink")
        if index < len(relative.parts) - 1 and cursor.exists() \
                and not cursor.is_dir():
            raise MastersPlanningError(f"{label} parent is not a directory")
    if not cursor.exists():
        if required:
            raise MastersPlanningError(f"{label} is missing")
        return None
    if not cursor.is_file():
        raise MastersPlanningError(f"{label} is not a regular file")
    try:
        cursor.resolve(strict=True).relative_to(root)
    except (OSError, ValueError) as exc:
        raise MastersPlanningError(f"{label} escapes the repository") from exc
    return cursor


def read_yaml_object(root: Path, path: Path, *, label: str) -> dict[str, Any]:
    safe_path = _sanitized_file(root, path, label=label, required=True)
    assert safe_path is not None  # required=True
    try:
        value = yaml.safe_load(safe_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise MastersPlanningError(f"cannot read {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise MastersPlanningError(f"{label} must be an object")
    return value


def _catalog_link_problem(url: str) -> str | None:
    """Why a prospective-candidate URL is not catalogue material, if it is not.

    Academic-only admits public course URLs and refuses personal links (D15):
    anything that is not an http(s) URL with a public host. Exact checks only —
    scheme, host set, IP literal — so the refusal never depends on guessing
    whether an unknown host needs a login.
    """
    if not isinstance(url, str):
        return f"not a URL: {url!r}"
    try:
        parts = urlsplit(url)
    except ValueError:
        return f"not a parseable URL: {url}"
    if parts.scheme not in ("http", "https"):
        return f"scheme '{parts.scheme}' is not a public web link: {url}"
    host = (parts.hostname or "").casefold()
    if not host:
        return f"URL has no host: {url}"
    if host in _PERSONAL_LINK_HOSTS:
        return f"personal-storage host '{host}' is not catalogue material: {url}"
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return None
    return f"IP-literal host '{host}' is not catalogue material: {url}"


def validate_master_catalog(
    root: Path,
    value: dict[str, Any],
    *,
    planned_canonical_source_ids: set[str] | frozenset[str] = frozenset(),
) -> dict[str, Any]:
    assert_academic_only(value)
    try:
        validate_contract(root, "master-planning-catalog.schema.json", value)
    except ValueError as exc:
        raise MastersPlanningError(str(exc)) from exc
    module_ids = [row["id"] for row in value["candidate_modules"]]
    source_ids = [row["id"] for row in value["candidate_sources"]]
    if len(module_ids) != len(set(module_ids)):
        raise MastersPlanningError("Master Planning catalog has duplicate candidate module IDs")
    if len(source_ids) != len(set(source_ids)):
        raise MastersPlanningError("Master Planning catalog has duplicate candidate source IDs")
    source_set = set(source_ids)
    for module in value["candidate_modules"]:
        unknown = sorted(set(module["source_ids"]) - source_set)
        if unknown:
            raise MastersPlanningError(
                f"{module['id']} references unknown candidate sources: {unknown}"
            )
        if module["planning_state"] == "promoted" and not module.get("promoted_module_id"):
            raise MastersPlanningError(
                f"{module['id']} is promoted but has no canonical module mapping"
            )
        if module.get("promoted_module_id") and module["planning_state"] != "promoted":
            raise MastersPlanningError(
                f"{module['id']} has a canonical mapping but is not promoted"
            )
    for source in value["candidate_sources"]:
        titles = source.get("child_titles") or {}
        labels = source.get("identifiers") or {}
        for label in sorted(titles):
            if label not in labels:
                raise MastersPlanningError(
                    f"{source['id']} child_titles key '{label}' "
                    "has no matching identifiers label"
                )
        links = [source["url"]] if source.get("url") else []
        links += [address for address in labels.values() if isinstance(address, str)]
        for link in links:
            problem = _catalog_link_problem(link)
            if problem is not None:
                raise MastersPlanningError(f"{source['id']}: {problem}")
    repo = load_repo(root)
    for source in value["candidate_sources"]:
        canonical = source.get("canonical_source_id")
        if canonical and canonical not in repo.sources \
                and canonical not in planned_canonical_source_ids:
            raise MastersPlanningError(
                f"{source['id']} maps to unknown canonical source: {canonical}"
            )
    return value


def master_catalog_destination(root: Path) -> Path:
    return root / "curriculum" / "quarantine" / "masters-planning" / "catalog.yaml"


def load_master_catalog(root: Path) -> dict[str, Any] | None:
    path = master_catalog_destination(root)
    safe_path = _sanitized_file(
        root,
        path,
        label="Master Planning catalog",
        required=False,
    )
    if safe_path is None:
        return None
    return validate_master_catalog(
        root,
        read_yaml_object(root, safe_path, label="Master Planning catalog"),
    )

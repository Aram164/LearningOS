"""Reading files without deciding what they mean.

Every domain loader gets its bytes through here, which is why the defensive
posture is stated once: a file that cannot be parsed becomes a reported failure
and is skipped, never an exception that takes down the command the confused
operator ran first (`validate`).
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from yaml.constructor import ConstructorError

from ..pathing import PathBoundaryError, read_text_inside
from .vocabulary import FRONTMATTER_RE


class LoaderError(Exception):
    """Raised when a file cannot be parsed at all (structural failure)."""


# LibYAML accelerates scanning/composition; safe construction and our duplicate
# key checks remain the same. Pure Python remains supported on installations
# where PyYAML was built without the optional C extension.
_SafeLoader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


class UniqueKeySafeLoader(_SafeLoader):
    """SafeLoader that rejects duplicate explicit keys at every depth.

    Merge keys remain supported: an explicit key may intentionally override a
    merged default, while duplicate declarations in the same authored mapping
    are ambiguous and therefore structural failures.
    """

    def construct_mapping(self, node, deep=False):
        if not isinstance(node, yaml.MappingNode):
            return super().construct_mapping(node, deep=deep)
        seen = set()
        for key_node, _value_node in node.value:
            if key_node.tag == "tag:yaml.org,2002:merge":
                continue
            key = self.construct_object(key_node, deep=False)
            try:
                duplicate = key in seen
                seen.add(key)
            except TypeError as exc:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "found an unhashable mapping key",
                    key_node.start_mark,
                ) from exc
            if duplicate:
                raise ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key {key!r}",
                    key_node.start_mark,
                )
        return super().construct_mapping(node, deep=deep)


def _safe_yaml(text: str):
    return yaml.load(text, Loader=UniqueKeySafeLoader)


def _read_text(path: Path, root: Path, *, errors: str = "strict") -> str:
    try:
        return read_text_inside(root, path, errors=errors)
    except (OSError, PathBoundaryError) as exc:
        raise LoaderError(f"{path}: cannot read canonical file: {exc}") from exc


def _normalize(value):
    """YAML 1.1 auto-parses ISO dates; the schemas expect strings. Normalize
    recursively so the logical model is representation-independent."""
    # Fast path: primitive types
    t = type(value)
    if t is str or t is int or t is bool or value is None or t is float:
        return value

    # Fast path: exact collection types
    if t is dict:
        return {k: _normalize(v) for k, v in value.items()}
    if t is list:
        return [_normalize(v) for v in value]

    import datetime as _dt
    # Fast path: exact datetime types
    if t is _dt.date or t is _dt.datetime:
        return value.isoformat()

    # Slow path: subclass checks for custom YAML types/nodes
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    if isinstance(value, (_dt.date, _dt.datetime)):
        return value.isoformat()

    return value


def parse_frontmatter(text: str, path: Path) -> tuple[dict, str]:
    """Return (frontmatter dict, body) for a Markdown file."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        meta = _safe_yaml(m.group(1)) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - surfaced as issue upstream
        raise LoaderError(f"{path}: invalid YAML frontmatter: {exc}") from exc
    if not isinstance(meta, dict):
        raise LoaderError(f"{path}: frontmatter is not a mapping")
    return _normalize(meta), text[m.end():]


def _load_yaml(path: Path, root: Path) -> dict:
    text = _read_text(path, root)
    try:
        data = _safe_yaml(text)
    except yaml.YAMLError as exc:
        raise LoaderError(f"{path}: invalid YAML: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise LoaderError(f"{path}: top level must be a mapping")
    return _normalize(data)


def _load_registry(
    consolidated: Path, partition_dir: Path, key: str, *, root: Path
) -> tuple[list, list[Path], list[tuple[Path, str]]]:
    """Load a registry from its consolidated file and/or partition directory.

    Defensive (never assumes document shape): a malformed file or item is
    reported as a failure and skipped instead of crashing the load or letting
    non-mapping records into the model.
    """
    records: list = []
    origins: list[Path] = []
    failures: list[tuple[Path, str]] = []
    candidates: list[Path] = []
    if consolidated.exists():
        candidates.append(consolidated)
    if partition_dir.is_dir():
        candidates.extend(sorted(partition_dir.glob("*.yaml")))
    for f in candidates:
        try:
            data = _load_yaml(f, root)
        except LoaderError as exc:
            failures.append((f, str(exc)))
            continue
        items = data.get(key, [])
        if items is None:
            items = []
        if not isinstance(items, list):
            failures.append((f, f"{f}: '{key}' must be a list"))
            continue
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                failures.append((f, f"{f}: {key}[{i}] is not a mapping — skipped"))
                continue
            records.append(item)
            origins.append(f)
    return records, origins, failures


def _record_id(rec: dict) -> str | None:
    """The record's id if it is a non-empty string, else None (reject empties)."""
    rid = rec.get("id")
    if isinstance(rid, str) and rid.strip():
        return rid
    return None


def md_section(body: str, heading: str) -> str | None:
    """Return the text of a `## <heading>` body section, if present.

    Single implementation of Markdown ``## heading`` section extraction, shared
    by Workspace, Coordination, and the validator (previously duplicated in
    three places). A section runs from its heading to the next `## ` heading or
    end of document.
    """
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*$(.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(body)
    return m.group(1).strip() if m else None

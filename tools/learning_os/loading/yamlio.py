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

from .vocabulary import FRONTMATTER_RE


class LoaderError(Exception):
    """Raised when a file cannot be parsed at all (structural failure)."""


def _normalize(value):
    """YAML 1.1 auto-parses ISO dates; the schemas expect strings. Normalize
    recursively so the logical model is representation-independent."""
    import datetime as _dt
    if isinstance(value, (_dt.date, _dt.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    return value


def parse_frontmatter(text: str, path: Path) -> tuple[dict, str]:
    """Return (frontmatter dict, body) for a Markdown file."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as exc:  # pragma: no cover - surfaced as issue upstream
        raise LoaderError(f"{path}: invalid YAML frontmatter: {exc}") from exc
    if not isinstance(meta, dict):
        raise LoaderError(f"{path}: frontmatter is not a mapping")
    return _normalize(meta), text[m.end():]


def _load_yaml(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        # An unreadable file (replaced by a directory, permission denied) raises
        # before YAML parsing starts, so it used to bypass the parse-failure
        # mechanism and crash every command — including `validate`, the one a
        # confused user runs first.
        raise LoaderError(f"{path}: cannot read file: {exc.strerror or exc}") from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise LoaderError(f"{path}: invalid YAML: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise LoaderError(f"{path}: top level must be a mapping")
    return _normalize(data)


def _load_registry(
    consolidated: Path, partition_dir: Path, key: str
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
            data = _load_yaml(f)
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

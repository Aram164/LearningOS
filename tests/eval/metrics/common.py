"""Shared helpers for the evaluation scorers: id normalization, IO, heuristics."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

MATERIAL_PREFIXES = ("note-", "workspace-", "project-", "garden:", "inbox:", "stage:",
                     "arrival:")
STOP = {"the", "and", "that", "this", "with", "from", "into", "only", "same", "when",
        "what", "have", "their", "there", "they", "been", "does", "each", "every", "than",
        "then", "them", "these", "those", "which", "while", "would", "could", "should",
        "about", "after", "before", "because", "between", "both", "more", "most", "other",
        "over", "some", "such", "under", "very", "where", "your", "note", "notes"}


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"{path}:{number}: not JSON: {exc}") from exc
    return rows


def normalize_target(raw: str) -> str:
    """Map the many ways a consumer may name a record onto one id."""
    t = str(raw).strip().strip("`").strip()
    if not t:
        return ""
    t = t.split("#", 1)[0]
    for scheme in ("note://", "workspace://", "project://"):
        if t.startswith(scheme):
            t = t[len(scheme):]
    m = re.fullmatch(r"A(\d{2})", t)
    if m:
        return f"arrival:A{m.group(1)}"
    if t.startswith(("arrival:", "garden:", "inbox:", "stage:")):
        return t
    m = re.search(r"(?:^|/)knowledge/garden/([^/]+\.md)$", t)
    if m:
        return f"garden:{m.group(1)}"
    m = re.search(r"(?:^|/)work/inbox/([^/]+)$", t)
    if m:
        return f"inbox:{m.group(1)}"
    m = re.search(r"/stages/([^/]+)/notes\.md$", t)
    if m:
        return f"stage:{m.group(1)}"
    m = re.search(r"(?:^|/)(?:work/active|archive/workspaces)/([^/]+)/CONTEXT\.md$", t)
    if m:
        return m.group(1)
    m = re.search(r"(?:^|/)projects/registry/([^/]+)\.yaml$", t)
    if m:
        return m.group(1)
    m = re.search(r"(?:^|/)(note-[a-z0-9-]+)\.md$", t)
    if m:
        return m.group(1)
    m = re.search(r"eval-drop/(A\d{2})\.md$", t)
    if m:
        return f"arrival:{m.group(1)}"
    return t


def is_material(target: str) -> bool:
    return target.startswith(MATERIAL_PREFIXES)


def _words(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-zà-ÿ0-9²ᵀ/−\-]+", text.lower())
            if len(w) >= 4 and w not in STOP]


def mention_covered(mention: str, reason: str) -> bool:
    """HEURISTIC: at least half of a mention's content words appear (5-char
    prefix match) in the reason text."""
    words = _words(mention)
    if not words:
        return True
    hay = reason.lower()
    hits = sum(1 for w in words if w[:5] in hay)
    return hits * 2 >= len(words)


def keyword_hit(groups: list[list[str]], text: str) -> bool:
    """A point/claim matches when every substring of ANY group occurs."""
    low = text.lower()
    return any(all(k.lower() in low for k in group) for group in groups)


OUTDATED_WORDS = ("outdated", "superseded", "deprecated", "earlier", "older", "old note",
                  "wrong", "corrected", "no longer", "used to", "previous", "april", "june")


def flags_outdated(text: str, flags: list[str]) -> bool:
    low = text.lower()
    return bool(set(f.lower() for f in flags) & {"outdated", "superseded", "deprecated"}) or \
        any(w in low for w in OUTDATED_WORDS)


def world_ids(repo: Path) -> set[str]:
    """Every id a result may legitimately cite in a world repository."""
    ids: set[str] = {"coordination"}
    for p in (repo / "knowledge/notes").rglob("*.md"):
        ids.add(p.stem)
    for p in (repo / "knowledge/garden").glob("*.md"):
        ids.add("garden:" + p.name)
    for p in (repo / "work/inbox").glob("*"):
        if p.is_file():
            ids.add("inbox:" + p.name)
    for base in (repo / "work/active", repo / "archive/workspaces"):
        if base.is_dir():
            ids.update(p.name for p in base.iterdir() if p.is_dir())
    for p in (repo / "projects/registry").glob("*.yaml"):
        ids.add(p.stem)
    for p in (repo / "curriculum/modules").rglob("stages/*/notes.md"):
        ids.add("stage:" + p.parent.name)
    for p in (repo / "curriculum/modules").glob("*"):
        ids.add(p.name)
    for p in (repo / "curriculum/modules").rglob("unit.yaml"):
        ids.add(p.parent.name)
    for p in (repo / "curriculum/modules").rglob("study-map.yaml"):
        data = load_yaml(p) or {}
        if data.get("id"):
            ids.add(data["id"])
    for p in (repo / "sources/registry").glob("*.yaml"):
        for src in (load_yaml(p) or {}).get("sources", []) or []:
            ids.add(src["id"])
    for p in [repo / "knowledge/concepts.yaml"]:
        if p.is_file():
            for c in (load_yaml(p) or {}).get("concepts", []) or []:
                ids.add(c["id"])
    ids |= {f"arrival:A{n:02d}" for n in range(1, 31)}
    return ids


def resolvable(ref: str, ids: set[str], repo: Path | None) -> bool:
    """Whether a cited reference names something that exists in the world."""
    if normalize_target(ref) in ids:
        return True
    if repo is None:
        return False
    rel = str(ref).split("#", 1)[0].strip()
    if rel.startswith("material://"):
        return (repo.parent / "materials" / rel[len("material://"):]).exists()
    path = Path(rel) if rel.startswith("/") else repo / rel
    return bool(rel) and path.exists()

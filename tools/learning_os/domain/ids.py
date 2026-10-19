"""Canonical id kinds, parsing and validation (SPEC §8.1)."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass

from learning_os.domain.failures import MalformedId


@dataclass(frozen=True)
class IdKind:
    name: str
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class Digest:
    hex: str

    @classmethod
    def parse(cls, value: str) -> Digest:
        if not isinstance(value, str):
            raise MalformedId("digest", value)
        bare = value.removeprefix("sha256:")
        if re.fullmatch(r"[0-9a-f]{64}", bare) is None:
            raise MalformedId("digest", value)
        return cls(hex=bare)

    def prefixed(self) -> str:
        return f"sha256:{self.hex}"

    def bare(self) -> str:
        return self.hex


def _generic_pattern(prefix: str) -> re.Pattern[str]:
    return re.compile(f"^{prefix}-[a-z0-9]+(?:-[a-z0-9]+)*$")


_GENERIC_PREFIXES = (
    "module",
    "unit",
    "study-map",
    "stage",
    "route",
    "source",
    "concept",
    "note",
    "workspace",
    "program",
    "project",
    "ability",
    "detour",
    "component",
    "resource",
    "thematic-group",
    "proposal",
    "path",
    "knowledge",
)

KINDS: Mapping[str, IdKind] = {
    **{
        prefix: IdKind(prefix, _generic_pattern(prefix))
        for prefix in _GENERIC_PREFIXES
    },
    "transaction": IdKind(
        "transaction", re.compile(r"^transaction-\d{8}-\d{6}-\d{3}$")),
    "goal": IdKind(
        "goal",
        re.compile(
            r"^(?:lineage-stale|study-map-obligation|evidence-superseded|claims-needing-review|claims-audit|repeated-question-gap|inspection-without-dossier|reviewer-correction-pattern):\S+$"
        ),
    ),
    "digest": IdKind(
        "digest", re.compile(r"^(?:sha256:)?[0-9a-f]{64}$")),
    "material-uri": IdKind(
        "material-uri", re.compile(r"^material://source-[^/]+/.+$")),
    "material-path": IdKind(
        "material-path",
        re.compile(
            # \Z, not $, in the dot-dot guard: $ also matches before a
            # trailing newline, but "..\n" is one segment, not a ".." one.
            r"^(?!/)(?!materials/)(?!.*(?:^|/)\.\.(?:/|\Z)).+$",
            re.DOTALL,
        ),
    ),
}


def parse(kind: str, value: object) -> str | Digest:
    if kind == "digest":
        return Digest.parse(value)
    id_kind = KINDS[kind]
    if not isinstance(value, str) or id_kind.pattern.fullmatch(value) is None:
        raise MalformedId(kind, value)
    return value


def is_valid(kind: str, value: object) -> bool:
    try:
        parse(kind, value)
    except MalformedId:
        return False
    return True

#!/usr/bin/env python3
"""Validate the structured Job learning plans against the world they point at.

The Job surface has good machinery — transactional writes, a revision ledger,
receipts with per-file hashes, an auditable read boundary, computed drift
detection on notes.  Almost none of it reached ``Job/plans/``.  Plans were
stored, displayed and round-tripped safely, but never *checked*, so the same
three classes of error kept reappearing in review after review: paths that no
longer resolve, references to files that moved, and links to nothing.

Those are not carelessness.  They are the errors a system catches for notes and
did not catch for plans.  This script is the missing gate.  It asserts, for
every stage of every plan:

* every Stratum path named in the anchor prose resolves in the checkout;
* every declared ``component`` resolves;
* every ``vault_path`` resolves, and any Job-relative one sits inside the read
  allowlist that ``safe_job_path`` would enforce at open time;
* every concept id exists in the LearningOS concept registry;
* and, for any stage carrying a commit stamp, whether its components have moved
  since — the same question ``notes/stratum/`` has always been asked.

Run it from anywhere::

    python3 tools/check_job_plans.py            # human-readable report
    python3 tools/check_job_plans.py --json     # machine-readable
    python3 tools/check_job_plans.py --quiet    # findings only

Exit codes: ``0`` clean, ``1`` findings, ``2`` the check could not run.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPOSITORY_ROOT / "tools"))

try:
    import yaml
except ImportError:  # pragma: no cover - environment problem, not a finding
    print("check_job_plans: pyyaml is not installed (try: make setup)", file=sys.stderr)
    raise SystemExit(2) from None

from learning_os.commands.job_boundary import (  # noqa: E402
    READABLE_ROOTS,
    JobDashboardError,
    component_freshness,
    job_root,
    stratum_component_changed,
    validate_stratum_components,
)

#: Tokens that are unambiguously source paths rather than prose.  Deliberately
#: narrow: the anchors are sentences, and a greedy pattern would report every
#: hyphenated word as a broken path.  Extensions only — a bare `optimizer/ir`
#: in prose is a gesture at a package, not a claim this script can adjudicate.
SOURCE_TOKEN = re.compile(
    r"(?:[\w.\-]+/)*[\w.\-]+\.(?:py|rs|toml|pyi|so)(?![\w])"
)

#: The vault root is the parent of the LearningOS repository's parent, i.e. the
#: directory that holds both `LearningOS/` and `Job/`.  `vault_path` values are
#: written relative to it.
VAULT_ROOT = REPOSITORY_ROOT.parent.parent


class Finding:
    """One thing that is wrong, addressed to whoever has to fix it."""

    __slots__ = ("track", "stage", "kind", "detail")

    def __init__(self, track: str, stage: str, kind: str, detail: str) -> None:
        self.track = track
        self.stage = stage
        self.kind = kind
        self.detail = detail

    def as_dict(self) -> dict:
        return {"track": self.track, "stage": self.stage, "kind": self.kind, "detail": self.detail}

    def __str__(self) -> str:
        return f"{self.track} / {self.stage}\n    {self.kind}: {self.detail}"


def _concept_ids(repository_root: Path) -> set[str]:
    path = repository_root / "knowledge" / "concepts.yaml"
    if not path.is_file():
        return set()
    ids: set[str] = set()

    def walk(value: object) -> None:
        if isinstance(value, dict):
            identifier = value.get("id")
            if isinstance(identifier, str):
                ids.add(identifier)
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(yaml.safe_load(path.read_text(encoding="utf-8")))
    return ids


def _check_stage(
    *,
    track_id: str,
    stage: dict,
    stratum: Path,
    vault_root: Path,
    concepts: set[str],
    findings: list[Finding],
    freshness_counts: Counter,
) -> None:
    stage_id = str(stage.get("id") or "<unnamed stage>")
    context = stage.get("job_context") or {}
    anchor = str(context.get("read_only_anchor") or "")

    def report(kind: str, detail: str) -> None:
        findings.append(Finding(track_id, stage_id, kind, detail))

    # 1. Every source path the anchor prose names must resolve.  This is the
    #    check that would have caught the repo-root-relative shorthand, the
    #    vault-prefixed path, and the bare module names.
    for token in dict.fromkeys(SOURCE_TOKEN.findall(anchor)):
        token = token.rstrip(".,;:")
        try:
            validate_stratum_components(token)
        except JobDashboardError as exc:
            report("unsafe anchor path", str(exc))
            continue
        if (stratum / token).exists():
            continue
        shorthand = stratum / "stratum" / token
        if shorthand.exists():
            report(
                "anchor path is shorthand",
                f"{token!r} does not resolve; it is repo-root-relative as "
                f"'stratum/{token}'",
            )
        else:
            report("anchor path does not resolve", f"{token!r} is not in the Stratum checkout")

    # 2. Declared components are pathspecs handed to `git diff`.  A component
    #    that does not resolve makes the diff silently empty, which reads as
    #    `current` — the one wrong answer this whole mechanism exists to avoid.
    raw_declared = [
        str(item).strip()
        for item in (context.get("component") or [])
        if str(item).strip()
    ]
    try:
        declared = validate_stratum_components(raw_declared)
    except JobDashboardError as exc:
        report("unsafe component", str(exc))
        declared = []
    for component in declared:
        if not (stratum / component).exists():
            report(
                "component does not resolve",
                f"{component!r} is not in the checkout, so drift for it would read as clean",
            )

    verified = str(context.get("verified_against") or "").strip()
    if verified and not declared:
        report(
            "stamp with nothing to check",
            f"verified_against is {verified!r} but no component is declared",
        )

    # 3. Resources: a path that does not resolve, or one the read boundary
    #    would refuse to open, is a dead link with extra steps.
    for resource in stage.get("resources") or []:
        if not isinstance(resource, dict):
            continue
        vault_path = str(resource.get("vault_path") or "").strip()
        if not vault_path:
            continue
        label = str(resource.get("label") or vault_path)
        if not (vault_root / vault_path).exists():
            report("vault_path does not resolve", f"{vault_path!r} ({label})")
            continue
        parts = Path(vault_path).parts
        if parts and parts[0] == "Job":
            inner = parts[1] if len(parts) > 1 else ""
            if inner not in READABLE_ROOTS:
                report(
                    "vault_path is outside the read allowlist",
                    f"{vault_path!r} ({label}) — safe_job_path would refuse it; "
                    f"allowed roots are {', '.join(sorted(READABLE_ROOTS))}",
                )

    # 4. A concept id that is not in the registry cannot participate in
    #    coverage, so tagging with it is indistinguishable from not tagging.
    if concepts:
        for concept in stage.get("concepts") or []:
            concept = str(concept).strip()
            if concept and concept not in concepts:
                report("concept is not registered", f"{concept!r} is not in knowledge/concepts.yaml")

    # 5. Drift, computed the same way the note surface computes it.
    revision = verified.split()[0] if verified else ""
    changed = stratum_component_changed(stratum, revision, declared) if declared else None
    label = component_freshness("", changed, stamped=bool(declared)) if declared else ""
    freshness_counts[label or "no source anchor"] += 1
    if label == "drifting":
        report(
            "anchor has drifted",
            f"{', '.join(declared)} moved since {verified}",
        )


def run(repository_root: Path) -> tuple[list[Finding], Counter, int]:
    root = job_root(repository_root)
    stratum = root / "stratum"
    plans_dir = root / "plans"
    if not plans_dir.is_dir():
        # Job is a quarantined sibling tree that is deliberately never pushed,
        # so CI and any fresh clone see no plans at all. That is absence, not
        # failure — reporting it as a finding would train everyone to ignore
        # this check on the one surface where it runs for real.
        return [], Counter(), 0

    concepts = _concept_ids(repository_root)
    findings: list[Finding] = []
    freshness_counts: Counter = Counter()
    stage_count = 0

    for path in sorted(plans_dir.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        track_id = str(data.get("id") or path.stem)
        for stage in data.get("stages") or []:
            if not isinstance(stage, dict):
                continue
            stage_count += 1
            _check_stage(
                track_id=track_id,
                stage=stage,
                stratum=stratum,
                vault_root=VAULT_ROOT,
                concepts=concepts,
                findings=findings,
                freshness_counts=freshness_counts,
            )
    return findings, freshness_counts, stage_count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="emit findings as JSON")
    parser.add_argument("--quiet", action="store_true", help="print findings only, no summary")
    args = parser.parse_args(argv)

    findings, freshness, stage_count = run(REPOSITORY_ROOT)

    if not stage_count and not args.json:
        if not args.quiet:
            print("no Job plans beside this repository — nothing to check.")
        return 0

    if args.json:
        print(json.dumps({
            "ok": not findings,
            "stages": stage_count,
            "findings": [finding.as_dict() for finding in findings],
            "freshness": dict(freshness),
        }, indent=2))
        return 1 if findings else 0

    if findings:
        print(f"{len(findings)} finding(s) across {stage_count} stages:\n")
        for finding in findings:
            print(f"  {finding}\n")
    elif not args.quiet:
        print(f"{stage_count} stages checked — no findings.")

    if not args.quiet:
        print("Anchor freshness:")
        for label in ("current", "drifting", "stale", "unverified", "no source anchor"):
            if label in freshness:
                print(f"  {freshness[label]:4}  {label}")
        unstamped = freshness.get("unverified", 0)
        if unstamped:
            print(
                f"\n  {unstamped} stage(s) name Stratum source but carry no commit stamp.\n"
                "  Add `verified_against: <sha> (YYYY-MM-DD)` to a stage's job_context\n"
                "  once you have read it against the checkout, and drift will be\n"
                "  reported for it from then on."
            )

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())

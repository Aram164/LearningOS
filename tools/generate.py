#!/usr/bin/env python3
"""Learning OS v3 generator (BUILD-SPEC Step 5).

    python tools/generate.py            # rebuild all generated outputs
    python tools/generate.py --shadow-derived [--json]
                                        # proof-phase shadow comparison (no writes)
    python tools/generate.py --shadow-manifest [--json]
                                        # proof-phase manifest comparison (no writes)
    python tools/generate.py --shadow-all [--json]
                                        # one guarded verdict for all migrated projections

Produces, deterministically except timestamps: generated/manifest.json,
concept-index.md, source-index.md (incl. per-lecture and per-concept selector
views), module-view.md, coordination-view.md, backlinks.json, reports/health.md.

Generated files are gitignored, carry a warning header, and are never canonical
inputs. Delete generated/ at any time; this command rebuilds everything.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from learning_os.contracts.manifest_contract import ManifestContractError  # noqa: E402
from learning_os.derived.model import DerivedError  # noqa: E402
from learning_os.genout import generate_all, write_outputs  # noqa: E402
from learning_os.genout.derived_generation import (  # noqa: E402
    BACKLINKS_SEMANTIC_ID,
    CONCEPT_MAP_BODY_ID,
    DEPENDENCY_REPORT_BODY_ID,
    compare_shadow_generation,
)
from learning_os.genout.manifest_derived import (  # noqa: E402
    compare_shadow_manifest,
)
from learning_os.genout.projection_verification import verify_shadow_projections  # noqa: E402
from learning_os.githistory import GitHistoryError  # noqa: E402
from learning_os.learning_runtime import RuntimeInputError  # noqa: E402
from learning_os.loader import load_repo  # noqa: E402
from learning_os.transactions import TransactionFailure  # noqa: E402

_NODE_ARTIFACTS = (
    (BACKLINKS_SEMANTIC_ID, "backlinks.json"),
    (CONCEPT_MAP_BODY_ID, "concept-map.md"),
    (DEPENDENCY_REPORT_BODY_ID, "dependency-report.md"),
)


def _describe_event(event) -> str:
    if event.status == "hit":
        return "hit"
    if event.reason == "cache-miss":
        return "rebuilt (cold)"
    if event.reason == "node-key-changed-output-same":
        return "rebuilt-output-unchanged"
    return "rebuilt-output-changed"


def _shadow_main(root: Path, *, as_json: bool) -> int:
    """Compare shadow generation against legacy builders (never writes)."""
    import json

    repo = load_repo(root)
    trace: list = []
    comparison = compare_shadow_generation(repo, trace=trace)
    by_node = {event.node: event for event in trace}
    if as_json:
        print(json.dumps({
            "equivalent": comparison.equivalent,
            "artifacts": dict(comparison.artifacts),
            "nodes": {
                node_id: (
                    {"status": "hit"}
                    if by_node[node_id].status == "hit"
                    else {"status": "rebuilt",
                          "output_changed": by_node[node_id].reason
                          != "node-key-changed-output-same"}
                )
                for node_id, _artifact in _NODE_ARTIFACTS
            },
        }, indent=2, sort_keys=True))
        return 0 if comparison.equivalent else 1
    if comparison.equivalent:
        print("shadow generation: exact")
    else:
        mismatched = sorted(name for name, ok in comparison.artifacts.items() if not ok)
        print(f"shadow generation: MISMATCH ({', '.join(mismatched)})")
    print()
    for node_id, artifact in _NODE_ARTIFACTS:
        print(artifact)
        print(f"  semantic: {_describe_event(by_node[node_id])}")
        print()
    total = len(comparison.artifacts)
    matched = sum(1 for ok in comparison.artifacts.values() if ok)
    print(f"{matched}/{total} artifacts byte-identical")
    return 0 if comparison.equivalent else 1


def _shadow_manifest_main(root: Path, *, as_json: bool) -> int:
    """Compare the shadow manifest against build_manifest (never writes)."""
    import json

    repo = load_repo(root)
    trace: list = []
    comparison = compare_shadow_manifest(repo, None, trace=trace)
    by_node = {event.node: event for event in trace}
    if as_json:
        print(json.dumps({
            "equivalent": comparison.equivalent,
            "artifact": "manifest.json",
            "legacy_sha256": comparison.legacy_sha256,
            "shadow_sha256": comparison.shadow_sha256,
            "nodes": {
                node_id: (
                    {"status": "hit"}
                    if by_node[node_id].status == "hit"
                    else {"status": "rebuilt",
                          "output_changed": by_node[node_id].reason
                          != "node-key-changed-output-same"}
                )
                for node_id in sorted(by_node)
            },
        }, indent=2, sort_keys=True))
        return 0 if comparison.equivalent else 1
    if comparison.equivalent:
        print("shadow manifest: exact")
    else:
        print("shadow manifest: MISMATCH (manifest.json)")
    print()
    for node_id in sorted(by_node):
        print(f"  {node_id}: {_describe_event(by_node[node_id])}")
    print()
    print(f"manifest.json sha256:{comparison.shadow_sha256}")
    return 0 if comparison.equivalent else 1


def _shadow_all_main(root: Path, *, as_json: bool) -> int:
    """Machine-owned coordination; never publishes generated views."""
    import json

    try:
        report = verify_shadow_projections(root)
    except (TransactionFailure, DerivedError, ManifestContractError,
            RuntimeInputError, GitHistoryError, OSError) as exc:
        report = {"status": "refused", "equivalent": False, "reason": str(exc),
                  "published": False}
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"projection verification: {report['status']}")
        if "reason" in report:
            print(report["reason"])
        else:
            print(f"snapshot: {report['snapshot_id']}")
            for name, artifact in report["artifacts"].items():
                print(f"  {name}: {'exact' if artifact['equal'] else 'MISMATCH'}")
            if not report["same_publication"]:
                print("publication metadata does not describe one state")
    return {"verified": 0, "mismatch": 1, "refused": 2}[report["status"]]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None,
                        help="repository root (default: parent of tools/)")
    parser.add_argument("--shadow-derived", action="store_true",
                        help="compare derived shadow generation against the legacy "
                             "builders without writing (exit nonzero on mismatch)")
    parser.add_argument("--shadow-manifest", action="store_true",
                        help="compare the shadow manifest graph against "
                             "build_manifest() without writing "
                             "(exit nonzero on mismatch)")
    parser.add_argument("--shadow-all", action="store_true",
                        help="verify all migrated projections under one snapshot; "
                             "updates disposable cache only, never publishes views")
    parser.add_argument("--json", action="store_true",
                        help="machine-readable shadow report "
                             "(requires a shadow mode)")
    args = parser.parse_args()

    if args.json and not (args.shadow_derived or args.shadow_manifest or args.shadow_all):
        parser.error("--json requires --shadow-derived, --shadow-manifest, or --shadow-all")
    if sum((args.shadow_derived, args.shadow_manifest, args.shadow_all)) > 1:
        parser.error("choose one shadow mode")

    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parent.parent
    if args.shadow_all:
        return _shadow_all_main(root, as_json=args.json)
    if args.shadow_derived:
        return _shadow_main(root, as_json=args.json)
    if args.shadow_manifest:
        return _shadow_manifest_main(root, as_json=args.json)
    repo = load_repo(root)
    try:
        outputs = generate_all(repo)
    except TransactionFailure as exc:
        print(f"generation refused: {exc}")
        return 2
    except RuntimeInputError as exc:
        # Hard rule 1 sends every canonical repair through this command, so it
        # is the one place a runtime inconsistency must not arrive as a stack
        # trace. `los` already answers these as one handled line; the rebuild
        # printed forty and left the projection unwritten.
        print(f"generation refused: {exc}")
        return 1
    write_outputs(repo, outputs)
    for rel in sorted(outputs):
        print(f"wrote generated/{rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

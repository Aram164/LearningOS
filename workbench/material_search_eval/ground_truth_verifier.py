#!/usr/bin/env python3
"""Independent Ground Truth Verifier for LearningOS Material Search Evaluation.

Verifies that every question entry in questions_dev.yaml and questions_heldout.yaml:
1. Points to an existing cached text file: generated/text-cache/<sha256>/pp-<page>.txt.
2. The recorded evidence_quote is an exact (NFC-normalized, whitespace-collapsed) substring of the text.
3. If has_route=True, the referenced unit_id and route_id exist in LearningOSRepo and resolve to that source file.
4. Identifies which questions have routes vs unmapped vs unanswerable.
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

import yaml

# Add tools/ to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from learning_os.store.loading import load_repo
from learning_os.domain.material_refs import unit_routes
from learning_os.store.materials.resolution import resolve_route_material_files, sha256_file


def norm(text: str) -> str:
    n = unicodedata.normalize("NFC", text)
    return " ".join(n.split()).lower()


def verify_file(yaml_path: Path, repo, cache_dir: Path) -> dict:
    if not yaml_path.exists():
        return {"error": f"File not found: {yaml_path}"}

    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    results = {
        "file": str(yaml_path.name),
        "total_questions": len(data),
        "answerable": 0,
        "unanswerable": 0,
        "with_route": 0,
        "without_route": 0,
        "verified_quotes": 0,
        "failed_quotes": 0,
        "route_verified": 0,
        "route_failed": 0,
        "failures": [],
    }

    for q in data:
        qid = q.get("id")
        status = q.get("expected_status")
        targets = q.get("targets", [])

        if status == "unanswerable":
            results["unanswerable"] += 1
            continue

        results["answerable"] += 1
        for t in targets:
            sha = t.get("source_sha256")
            page = t.get("physical_page")
            quote = t.get("evidence_quote")
            has_route = t.get("has_route")
            route = t.get("route")

            # 1. Verify text file and quote
            page_file = cache_dir / sha / f"pp-{page:04d}.txt"
            if not page_file.exists():
                results["failed_quotes"] += 1
                results["failures"].append(f"[{qid}] Page file missing: {page_file}")
                continue

            txt = page_file.read_text(encoding="utf-8", errors="ignore")
            if norm(quote) in norm(txt):
                results["verified_quotes"] += 1
            else:
                results["failed_quotes"] += 1
                results["failures"].append(
                    f"[{qid}] Quote not found in {page_file.name}: '{quote[:30]}...'"
                )

            # 2. Verify route if claimed
            if has_route and route:
                results["with_route"] += 1
                unit_id = route.get("unit_id")
                route_id = route.get("route_id")
                unit = repo.units.get(unit_id)
                if not unit:
                    results["route_failed"] += 1
                    results["failures"].append(f"[{qid}] Unit not found in repo: {unit_id}")
                    continue
                sm = repo.module_source_maps.get(unit.module_id)
                routes = unit_routes(sm, unit.module_id, unit.id) if sm else []
                matching = [r for r in routes if r.get("id") == route_id]
                if not matching:
                    results["route_failed"] += 1
                    results["failures"].append(f"[{qid}] Route {route_id} not in unit {unit_id}")
                    continue

                files = resolve_route_material_files(repo, matching[0])
                file_shas = [sha256_file(Path(f.path)).removeprefix("sha256:") for f in files]
                if sha in file_shas:
                    results["route_verified"] += 1
                else:
                    results["route_failed"] += 1
                    results["failures"].append(
                        f"[{qid}] Route file SHA mismatch: expected {sha[:8]}, got {file_shas}"
                    )
            else:
                results["without_route"] += 1

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Ground Truth question files.")
    parser.add_argument("--dev-only", action="store_true", help="Verify only questions_dev.yaml")
    args = parser.parse_args()

    cache_dir = REPO_ROOT / "generated/text-cache"
    if not cache_dir.exists():
        print(f"Error: Text cache directory missing at {cache_dir}", file=sys.stderr)
        return 1

    print(f"Loading LearningOS repository from {REPO_ROOT}...")
    repo = load_repo(REPO_ROOT)

    files_to_check = [SCRIPT_DIR / "questions_dev.yaml"]
    if not args.dev_only:
        files_to_check.append(SCRIPT_DIR / "questions_heldout.yaml")

    all_passed = True
    for f in files_to_check:
        res = verify_file(f, repo, cache_dir)
        print(f"\nVerification Results for {res['file']}:")
        print(f"  Total questions: {res['total_questions']}")
        print(f"  Answerable: {res['answerable']} | Unanswerable: {res['unanswerable']}")
        print(
            f"  With Route: {res['with_route']} | Without Route (unmapped): {res['without_route']}"
        )
        print(
            f"  Verified Quotes: {res['verified_quotes']}/{res['verified_quotes'] + res['failed_quotes']}"
        )
        print(f"  Verified Routes: {res['route_verified']}/{res['with_route']}")
        if res["failures"]:
            all_passed = False
            print(f"  FAILURES ({len(res['failures'])}):")
            for fail in res["failures"]:
                print(f"    - {fail}")
        else:
            print("  ALL GROUND TRUTH CHECKS PASSED.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

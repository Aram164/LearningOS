"""Cross-layer projection contract for thematic Modules and Library navigation."""

from __future__ import annotations

import json

import yaml

from learning_os.genout import generate_all
from learning_os.loader import load_repo
from learning_os.rules import Validator


def _write_navigation_fixture(root):
    curriculum = root / "curriculum"
    curriculum.mkdir(exist_ok=True)
    (curriculum / "thematic-groups.yaml").write_text(
        yaml.safe_dump({
            "thematic_groups": [
                {
                    "id": "thematic-group-machine-learning",
                    "title": "Machine Learning",
                    "description": "Models and ML systems.",
                    "order": 10,
                },
                {
                    "id": "thematic-group-mathematics",
                    "title": "Mathematics",
                    "description": "Quantitative foundations.",
                    "order": 20,
                },
            ]
        }, sort_keys=False),
        encoding="utf-8",
    )

    modules_path = root / "records" / "modules.yaml"
    modules = yaml.safe_load(modules_path.read_text(encoding="utf-8"))
    modules["modules"][0]["thematic_group_ids"] = [
        "thematic-group-machine-learning"
    ]
    modules_path.write_text(yaml.safe_dump(modules, sort_keys=False), encoding="utf-8")

    (root / "sources" / "collections" / "demo-reading.yaml").write_text(
        yaml.safe_dump({
            "title": "Demo reading",
            "collection_kind": "catalogue",
            "thematic_group_ids": ["thematic-group-mathematics"],
            "description": "A broad source catalogue.",
            "entries": [{"source": "source-demo-book", "why": "Reference."}],
        }, sort_keys=False),
        encoding="utf-8",
    )
    (root / "sources" / "collections" / "demo-pack.yaml").write_text(
        yaml.safe_dump({
            "title": "Demo pack",
            "collection_kind": "topic-pack",
            "thematic_group_ids": ["thematic-group-machine-learning"],
            "purpose": "Prepare one bounded comparison.",
            "description": "A narrow, manually ordered collection.",
            "entries": [
                {"source": "source-demo-book", "group": "first", "why": "Start here."}
            ],
        }, sort_keys=False),
        encoding="utf-8",
    )


def test_manifest_projects_stable_thematic_navigation_metadata(mini_repo):
    _write_navigation_fixture(mini_repo)
    manifest = json.loads(
        generate_all(load_repo(mini_repo), generated_at="T1")["manifest.json"]
    )

    assert [group["id"] for group in manifest["thematic_groups"]] == [
        "thematic-group-machine-learning",
        "thematic-group-mathematics",
    ]
    [module] = [row for row in manifest["modules"] if row["id"] == "module-demo"]
    assert module["thematic_group_ids"] == ["thematic-group-machine-learning"]

    [source] = [row for row in manifest["records"] if row["id"] == "source-demo-book"]
    # Source placement is computed in the core from explicit module/collection
    # membership. Interfaces receive the result and never infer from names/paths.
    assert source["thematic_group_ids"] == [
        "thematic-group-machine-learning",
        "thematic-group-mathematics",
    ]


def test_topic_packs_are_distinct_ordered_records_with_explicit_purpose(mini_repo):
    _write_navigation_fixture(mini_repo)
    manifest = json.loads(
        generate_all(load_repo(mini_repo), generated_at="T1")["manifest.json"]
    )

    assert [pack["id"] for pack in manifest["topic_packs"]] == ["demo-pack"]
    pack = manifest["topic_packs"][0]
    assert pack["type"] == "topic-pack"
    assert pack["purpose"] == "Prepare one bounded comparison."
    assert pack["thematic_group_ids"] == ["thematic-group-machine-learning"]
    assert pack["entries"] == [
        {"source": "source-demo-book", "group": "first", "why": "Start here."}
    ]

    catalogue = next(row for row in manifest["records"] if row["id"] == "demo-reading")
    assert catalogue["type"] == "collection"
    assert catalogue["collection_kind"] == "catalogue"
    assert catalogue not in manifest["topic_packs"]


def test_validator_rejects_unknown_thematic_group_references(mini_repo):
    _write_navigation_fixture(mini_repo)
    modules_path = mini_repo / "records" / "modules.yaml"
    modules = yaml.safe_load(modules_path.read_text(encoding="utf-8"))
    modules["modules"][0]["thematic_group_ids"] = ["thematic-group-does-not-exist"]
    modules_path.write_text(yaml.safe_dump(modules, sort_keys=False), encoding="utf-8")

    issues = Validator(load_repo(mini_repo)).run()
    assert any(issue.code == "REF-THEMATIC-GROUP" for issue in issues)


def test_real_repository_navigation_projection_is_complete(repo_root):
    manifest = json.loads(
        generate_all(load_repo(repo_root), generated_at="T1")["manifest.json"]
    )
    assert [group["title"] for group in manifest["thematic_groups"]] == [
        "Machine Learning",
        "Mathematics",
        "CS Theory",
        "Programming Languages",
        "Data Systems",
    ]
    assert all(module["thematic_group_ids"] for module in manifest["modules"])
    sources = [row for row in manifest["records"] if row.get("type") == "source"]
    assert sources and all(source["thematic_group_ids"] for source in sources)
    assert manifest["topic_packs"]
    assert all(pack["purpose"] and pack["entries"] for pack in manifest["topic_packs"])

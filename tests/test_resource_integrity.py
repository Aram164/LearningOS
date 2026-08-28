"""Adversarial and production-level resource target integrity.

These checks deliberately use independent filesystem and URL oracles instead
of restating the projection implementation.  They protect the boundary that
turns canonical source routing into an Open button in the interface.
"""

from __future__ import annotations

import json
import random
import re
import string
from pathlib import Path
from urllib.parse import urlparse

import pytest

from learning_os.genout import generate_all
from learning_os.genout.materials import _safe_material_locator
from learning_os.loader import load_repo

_FILE_SHAPED = re.compile(r"^[^./][^/]*\.[^./]+$")


def _is_file_shaped(value) -> bool:
    if not isinstance(value, str):
        return False
    name = value.strip().split("?", 1)[0].split("#", 1)[0]
    return bool(_FILE_SHAPED.fullmatch(name.replace("\\", "/").rsplit("/", 1)[-1]))


def _is_safe_web_url(value) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme.lower() in {"http", "https"} and bool(parsed.netloc)


def test_material_locator_fuzz_accepts_one_file_and_refuses_hostile_compounds():
    """A deterministic mutation corpus guards the file-vs-prose boundary."""
    rng = random.Random(20260823)
    extensions = (".pdf", ".ppt", ".pptx", ".md", ".ipynb")
    page_suffixes = ("", " (1 page)", " (81 pages)", " (4 pp)", " (12 pp.)")

    for _ in range(1_000):
        parts = []
        for _ in range(rng.randint(1, 4)):
            alphabet = string.ascii_letters + string.digits + " _-"
            part = "".join(
                rng.choice(alphabet)
                for _ in range(rng.randint(2, 24))
            ).strip()
            parts.append(part or "lecture")
        exact = "/".join(parts) + rng.choice(extensions)
        assert _safe_material_locator(exact + rng.choice(page_suffixes)) == exact

        other = "/other/second" + rng.choice(extensions)
        mutations = (
            "/" + exact,
            "../" + exact,
            exact.replace("/", "\\", 1) if "/" in exact else exact + "\\escape",
            exact + "; open something",
            exact + "\nsecond line",
            exact + " + " + other,
            exact + " through " + other,
            exact + "/child",
        )
        assert all(_safe_material_locator(value) is None for value in mutations)


@pytest.mark.full_repo
def test_real_stage_open_targets_are_files_or_safe_websites(repo_root: Path):
    """Every production stage target exposed as exact work must be usable."""
    manifest = json.loads(
        generate_all(load_repo(repo_root), generated_at="RESOURCE-INTEGRITY")[
            "manifest.json"
        ]
    )
    learning_root = repo_root.parent
    unique_resources = {
        json.dumps(
            [
                resource.get("label"),
                resource.get("source_id"),
                resource.get("material_path"),
                resource.get("vault_path"),
                resource.get("url"),
            ],
            ensure_ascii=False,
        ): resource
        for stage in manifest.get("stages", [])
        if isinstance(stage, dict)
        for resource in stage.get("resources", []) or []
        if isinstance(resource, dict)
    }

    for resource in unique_resources.values():
        material_path = resource.get("material_path")
        if material_path:
            assert _is_file_shaped(material_path), resource
            assert resource.get("material_exists") is True, resource
            assert (learning_root / material_path).is_file(), resource

        vault_path = resource.get("vault_path")
        if isinstance(vault_path, str) \
                and not vault_path.lower().startswith("material://") \
                and _is_file_shaped(vault_path):
            assert (repo_root / vault_path).is_file(), resource

        url = resource.get("url")
        if url:
            assert _is_safe_web_url(url), resource

    aml_l11 = next(
        resource for resource in unique_resources.values()
        if resource.get("label") == "Current L11 Transformers lecture deck"
    )
    assert aml_l11["material_path"].endswith("VL 11-transformers.pdf")
    assert (learning_root / aml_l11["material_path"]).is_file()

from tools.legacy_exit_review import (
    _is_job_boundary,
    _mapping_for,
    _normalise_old_path,
    _path_is_within,
    _superseded_by,
)


def test_directory_mapping_covers_descendants_but_not_lookalikes():
    assert _path_is_within("Plans/area/file.md", "Plans/area")
    assert _path_is_within("Plans/area", "Plans/area")
    assert not _path_is_within("Plans/area-copy/file.md", "Plans/area")


def test_longest_migration_mapping_wins():
    rows = [
        {"old_path": "Plans/area", "new_path": "broad"},
        {"old_path": "Plans/area/specific.md", "new_path": "exact"},
    ]
    assert _mapping_for("Plans/area/specific.md", rows)["new_path"] == "exact"


def test_legacy_prefix_is_normalised_for_post_cutover_rows():
    assert _normalise_old_path("legacy/Plans/area") == "Plans/area"


def test_job_items_are_held_at_the_boundary():
    assert _is_job_boundary("Plans/archive/BIFOLD-DEEM-Job-Plan.md")
    assert _is_job_boundary("Plans/Libraries/skrub/Stratum-Optimizer.md")
    assert not _is_job_boundary("Plans/Math/analysis/AN_Source-Crosswalk.md")


def test_known_v2_mechanics_have_explicit_replacements():
    assert _superseded_by("Masters-Planning/tools/check_system.py") == "tools/validate.py"
    assert _superseded_by("Plans/LearningOS_v3_Spec/ARCHITECTURE.md") == "system/"

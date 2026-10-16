"""Canonical YAML and front-matter serialization for authored files."""

from __future__ import annotations

import yaml


class _NoAliasSafeDumper(yaml.SafeDumper):
    """Keep authored YAML deterministic even when an input package uses anchors."""

    def ignore_aliases(self, data):  # noqa: ANN001 - PyYAML callback signature
        return True


def _dump_yaml(data: dict) -> str:
    return yaml.dump(data, Dumper=_NoAliasSafeDumper, sort_keys=False,
                     allow_unicode=True, width=100)


def _render_frontmatter(meta: dict, body: str) -> str:
    return "---\n" + _dump_yaml(meta).rstrip() + "\n---\n\n" + body.lstrip()


def _dump_study_map(study_map, data: dict) -> str:
    from learning_os.domain.material_refs import preserve_map_refs

    return _dump_yaml(preserve_map_refs(study_map, data))

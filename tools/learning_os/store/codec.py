"""Canonical YAML and front-matter serialization for authored files."""

from __future__ import annotations

import yaml


class _NoAliasSafeDumper(yaml.SafeDumper):
    """Keep authored YAML deterministic even when an input package uses anchors."""

    def ignore_aliases(self, data):  # noqa: ANN001 - PyYAML callback signature
        return True


def dump_yaml(data: dict) -> str:
    return yaml.dump(data, Dumper=_NoAliasSafeDumper, sort_keys=False,
                     allow_unicode=True, width=100)


def render_frontmatter(meta: dict, body: str) -> str:
    return "---\n" + dump_yaml(meta).rstrip() + "\n---\n\n" + body.lstrip()


def dump_study_map(study_map, data: dict) -> str:
    from learning_os.domain.material_refs import preserve_map_refs

    return dump_yaml(preserve_map_refs(study_map, data))

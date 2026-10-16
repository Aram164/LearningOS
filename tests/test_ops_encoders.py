"""Shared JSON encoders (P6-02 Task 1, PLAN 6.A.1 OD4a)."""

from __future__ import annotations

import dataclasses
import json
import re
import sys
from pathlib import Path

from learning_os.ops import encoders, handlers  # noqa: F401  (registration side effect)
from learning_os.ops.proposal import Result
from learning_os.ops.registry import REGISTRY

ROOT = Path(__file__).resolve().parent.parent

PAYLOAD = {"z": "café ☃", "a": [3, 1, {"b": "ü"}]}


class _FakeStdout:
    def __init__(self, tty: bool) -> None:
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


def test_dumps_unescaped():
    assert encoders.dumps_unescaped(PAYLOAD) == json.dumps(
        PAYLOAD, ensure_ascii=False
    )


def test_dumps_compact():
    assert encoders.dumps_compact(PAYLOAD) == json.dumps(
        PAYLOAD, ensure_ascii=False, separators=(",", ":")
    )


def test_dumps_indented():
    assert encoders.dumps_indented(PAYLOAD) == json.dumps(
        PAYLOAD, ensure_ascii=False, indent=2
    )


def test_dumps_ascii():
    assert encoders.dumps_ascii(PAYLOAD) == json.dumps(PAYLOAD)


def test_dumps_sorted():
    assert encoders.dumps_sorted(PAYLOAD) == json.dumps(
        PAYLOAD, ensure_ascii=False, sort_keys=True
    )


def test_dumps_indented_sorted():
    assert encoders.dumps_indented_sorted(PAYLOAD) == json.dumps(
        PAYLOAD, ensure_ascii=False, indent=2, sort_keys=True
    )


def test_dumps_layout_sorted(monkeypatch):
    monkeypatch.setattr(sys, "stdout", _FakeStdout(True))
    assert encoders.dumps_layout_sorted(PAYLOAD) == json.dumps(
        PAYLOAD, indent=2, sort_keys=True, ensure_ascii=False
    )
    monkeypatch.setattr(sys, "stdout", _FakeStdout(False))
    assert encoders.dumps_layout_sorted(PAYLOAD) == json.dumps(
        PAYLOAD, separators=(",", ":"), sort_keys=True, ensure_ascii=False
    )


def test_no_dumps_definitions_remain():
    pattern = re.compile(r"def _dumps_")
    hits = []
    base = ROOT / "tools/learning_os"
    for path in sorted(base.rglob("*.py")):
        if pattern.search(path.read_text(encoding="utf-8")):
            hits.append(str(path.relative_to(ROOT)))
    assert hits == []


def test_encode_json_matches_original_dumps_forms(monkeypatch):
    assert encoders.encode_json(PAYLOAD, "ascii") == json.dumps(PAYLOAD)
    assert encoders.encode_json(PAYLOAD, "compact") == json.dumps(
        PAYLOAD, ensure_ascii=False, separators=(",", ":")
    )
    assert encoders.encode_json(PAYLOAD, "indented") == json.dumps(
        PAYLOAD, ensure_ascii=False, indent=2
    )
    assert encoders.encode_json(PAYLOAD, "indented_sorted") == json.dumps(
        PAYLOAD, ensure_ascii=False, indent=2, sort_keys=True
    )
    assert encoders.encode_json(PAYLOAD, "sorted") == json.dumps(
        PAYLOAD, ensure_ascii=False, sort_keys=True
    )
    assert encoders.encode_json(PAYLOAD, "unescaped") == json.dumps(
        PAYLOAD, ensure_ascii=False
    )
    monkeypatch.setattr(sys, "stdout", _FakeStdout(True))
    assert encoders.encode_json(PAYLOAD, "layout_sorted") == json.dumps(
        PAYLOAD, indent=2, sort_keys=True, ensure_ascii=False
    )
    monkeypatch.setattr(sys, "stdout", _FakeStdout(False))
    assert encoders.encode_json(PAYLOAD, "layout_sorted") == json.dumps(
        PAYLOAD, separators=(",", ":"), sort_keys=True, ensure_ascii=False
    )


def test_result_has_no_json_dumps_field():
    assert "json_dumps" not in {f.name for f in dataclasses.fields(Result)}


EXPECTED_JSON_FORMATS = {
    "ability.candidate.append": ('ascii',),
    "ability.context": ('compact',),
    "ai-action.delivery.apply": ('indented',),
    "atlas.context": ('unescaped',),
    "atlas.question.save": ('unescaped',),
    "backup.manifest": ('indented',),
    "capture.create": ('unescaped',),
    "cli.ai-action-append-slices": ('indented',),
    "cli.ai-action-import-delivery": ('indented',),
    "cli.ai-action-list": ('indented',),
    "cli.ai-action-prepare": ('indented',),
    "cli.ai-action-status": ('indented',),
    "cli.ai-action-validate-delivery": ('indented',),
    "cli.atlas-context": ('unescaped',),
    "cli.backup-manifest": ('indented',),
    "cli.backup-verify": ('indented',),
    "cli.bootstrap": ('compact', 'layout_sorted'),
    "cli.capabilities": ('compact', 'layout_sorted'),
    "cli.dossier": ('compact',),
    "cli.goal": ('ascii',),
    "cli.health-report": ('indented',),
    "cli.inbox-list": ('layout_sorted',),
    "cli.inbox-read": ('compact',),
    "cli.inspect": ('compact', 'layout_sorted'),
    "cli.intelligence-scan": ('layout_sorted',),
    "cli.legacy-archive-inspect": ('indented',),
    "cli.legacy-archive-status": ('indented',),
    "cli.masters-planning-dashboard": ('indented',),
    "cli.module-list": ('layout_sorted',),
    "cli.note-analysis-prepare": ('indented',),
    "cli.note-read": ('compact',),
    "cli.observe": ('ascii',),
    "cli.operations": ('indented',),
    "cli.plan-edit-context": ('compact',),
    "cli.plan-template": ('unescaped',),
    "cli.program-list": ('layout_sorted',),
    "cli.project-list": ('layout_sorted',),
    "cli.related": ('layout_sorted',),
    "cli.resume": ('layout_sorted',),
    "cli.runtime-session": ('sorted',),
    "cli.search": ('compact', 'layout_sorted'),
    "cli.semantic": ('layout_sorted',),
    "cli.session-end": ('indented',),
    "cli.status": ('layout_sorted',),
    "cli.unit-list": ('compact', 'layout_sorted'),
    "collection.entry.revise": ('indented',),
    "concept.relations.change": ('unescaped',),
    "coordination.section.revise": ('unescaped',),
    "detour.create": ('unescaped',),
    "detour.resolve": ('unescaped',),
    "garden.seed.create": ('unescaped',),
    "health.report": ('indented',),
    "inbox.content": ('compact',),
    "inbox.list": ('layout_sorted',),
    "inbox.resolve": ('ascii',),
    "learner.ability-observation.append": ('ascii',),
    "learner.observation.append": ('ascii',),
    "learner.stage-result.append": ('ascii',),
    "legacy.archive.inspect": ('indented',),
    "legacy.archive.lock.publish": ('indented',),
    "legacy.archive.status": ('indented',),
    "lineage.restamp": ('sorted',),
    "masters-planning.catalog.update": ('indented',),
    "masters-planning.comparison.publish": ('indented',),
    "masters-planning.dashboard": ('indented',),
    "material.context": ('compact',),
    "material.span": ('compact',),
    "module.attempt.record": ('unescaped',),
    "module.materials.compact": ('compact',),
    "module.plan.import": ('indented', 'indented_sorted', 'unescaped'),
    "module.sitting.update": ('unescaped',),
    "note.analysis.save": ('unescaped',),
    "note.analysis.save_batch": ('unescaped',),
    "note.content": ('compact',),
    "note.create": ('unescaped',),
    "note.evidence.add": ('unescaped',),
    "note.revise": ('unescaped',),
    "note.search": ('compact', 'layout_sorted'),
    "operator.bootstrap": ('compact', 'layout_sorted'),
    "path.attachment.add": ('unescaped',),
    "path.note.write": ('unescaped',),
    "path.progress.update": ('unescaped',),
    "plan.edit-context": ('compact',),
    "plan.template": ('unescaped',),
    "project.create": ('unescaped',),
    "project.inspect": ('compact', 'layout_sorted'),
    "project.list": ('layout_sorted',),
    "project.update": ('unescaped',),
    "review.apply": ('unescaped',),
    "review.prepare": ('unescaped',),
    "route.patch": ('compact',),
    "runtime.session": ('sorted',),
    "source.feedback.record": ('unescaped',),
    "source.intake.record": ('indented',),
    "source.record.revise": ('indented',),
    "stage.attachment.add": ('unescaped',),
    "stage.note.write": ('unescaped',),
    "stage.progress.update": ('unescaped',),
    "unit.map.import": ('unescaped',),
    "unit.material-synthesis.publish": ('indented',),
    "unit.note.append": ('unescaped',),
    "unit.plan.revise": ('indented_sorted', 'unescaped'),
    "unit.source-selection.set": ('unescaped',),
    "workspace.next-action.update": ('unescaped',),
}


def test_registrations_declare_measured_json_formats():
    actual = {
        name: entry.json_formats
        for name, entry in REGISTRY.items()
        if entry.json_formats
    }
    assert actual == EXPECTED_JSON_FORMATS
    assert REGISTRY["cli.validate"].json_formats == ()
    assert REGISTRY["cli.generate"].json_formats == ()

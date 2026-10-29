"""Shared JSON encoders (P6-02 Task 1, PLAN 6.A.1 OD4a)."""

from __future__ import annotations

import dataclasses
import json
import re
import sys
from pathlib import Path

from learning_os.app import encoders, handlers  # noqa: F401  (registration side effect)
from learning_os.app.proposal import Result
from learning_os.app.registry import REGISTRY

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

    "atlas.question.save": ('unescaped',),

    "capture.create": ('unescaped',),
    "ai-action.append-slices": ('indented',),
    "ai-action.delivery.import": ('indented',),
    "ai-action.list": ('indented',),
    "ai-action.prepare": ('indented',),
    "ai-action.status": ('indented',),
    "ai-action.delivery.validate": ('indented',),
    "atlas.context": ('unescaped',),
    "backup.manifest": ('indented',),
    "backup.verify": ('indented',),

    "capabilities.read": ('compact', 'layout_sorted'),
    "dossier.read": ('compact',),
    "goal.decide": ('ascii',),




    "intelligence.scan": ('layout_sorted',),



    "module.list": ('layout_sorted',),
    "note.analysis.prepare": ('indented',),

    "learner.observe": ('ascii',),
    "operations.read": ('indented',),


    "program.list": ('layout_sorted',),

    "related.read": ('layout_sorted',),
    "resume.read": ('layout_sorted',),


    "semantic.query": ('layout_sorted',),
    "session.end": ('indented',),
    "status.read": ('layout_sorted',),
    "unit.list": ('compact', 'layout_sorted'),
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
    "project.inspect": ('compact', 'layout_sorted'),
    "project.list": ('layout_sorted',),
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
    # Formatting is a transport policy, never per-operation metadata.
    assert all(not hasattr(entry, "json_formats") for entry in REGISTRY.values())
    assert {f.name for f in dataclasses.fields(Result)} == {
        "payload", "proposal", "diagnostic_failed", "human_view", "gesture"}

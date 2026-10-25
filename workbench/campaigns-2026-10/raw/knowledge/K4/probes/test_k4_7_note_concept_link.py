"""K4 probe 7 — a note names a concept id that is then removed.

Concepts have no write capability: removing one is direct authoring (Aram's
act), simulated here by editing the fixture registry. The question the batch
asks: does validation name the NOTE that still carries the dangling
`concepts` link? Probed twice:

- the validator directly (los validate), which must report REF-CONCEPT
  naming the note id;
- an unrelated gateway write, whose staged canonical validation must refuse
  and name the same note while the link dangles.

The control restores the concept and re-runs the write to prove the refusal
was the dangling link, not the operation.
"""
import subprocess
import sys

import yaml
from gateway_helpers import approved_v2_call
from repo_builders import LOS

REGISTRY = "registry-concept-relations"


def _write_linked_note(root, concept_ids):
    (root / "knowledge/notes/mathematics/note-k4-linked.md").write_text(
        "---\nid: note-k4-linked\ntype: note\ntitle: Linked note\n"
        "created: 2026-10-25\nrole: synthesis\n"
        f"concepts: [{', '.join(concept_ids)}]\n---\n\nBody prose.\n",
        encoding="utf-8")


def _remove_concept(root, concept_id):
    path = root / "knowledge/concepts.yaml"
    data = yaml.safe_load(path.read_text())
    data["concepts"] = [c for c in data["concepts"] if c["id"] != concept_id]
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def _restore_concept(root, concept_id):
    path = root / "knowledge/concepts.yaml"
    data = yaml.safe_load(path.read_text())
    data["concepts"].append({"id": concept_id, "label": "Variance",
                             "aliases": ["Varianz"]})
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))


def _validate(root):
    return subprocess.run([sys.executable, str(LOS), "--root", str(root), "validate"],
                          capture_output=True, text=True, timeout=120)


def _add_edge(root, key):
    return approved_v2_call(root, capability="concept.relations.change",
                            payload={"change": {"operations": [
                                {"action": "add", "new": {
                                    "from": "concept-variance",
                                    "type": "requires",
                                    "to": "concept-expected-value"}}]}},
                            artifact_ids=[REGISTRY], idempotency_key=key)


def test_validator_names_the_note_for_a_removed_concept(mini_repo):
    _write_linked_note(mini_repo, ["concept-expected-value", "concept-variance"])
    _remove_concept(mini_repo, "concept-variance")
    result = _validate(mini_repo)
    assert result.returncode != 0, result.stdout + result.stderr
    combined = result.stdout + result.stderr
    assert "note-k4-linked" in combined
    assert "concept-variance" in combined


def test_gateway_write_refuses_and_names_the_note_while_the_link_dangles(mini_repo):
    _write_linked_note(mini_repo, ["concept-expected-value", "concept-variance"])
    _remove_concept(mini_repo, "concept-variance")
    before = (mini_repo / "knowledge/concept-relations.yaml").read_bytes()
    result = _add_edge(mini_repo, "k4-dangling-write")
    assert result.returncode != 0, result.stdout + result.stderr
    combined = result.stdout + result.stderr
    assert "note-k4-linked" in combined
    assert (mini_repo / "knowledge/concept-relations.yaml").read_bytes() == before


def test_restoring_the_concept_releases_the_same_write(mini_repo):
    _write_linked_note(mini_repo, ["concept-expected-value", "concept-variance"])
    _remove_concept(mini_repo, "concept-variance")
    _restore_concept(mini_repo, "concept-variance")
    result = _add_edge(mini_repo, "k4-restored-write")
    assert result.returncode == 0, result.stdout + result.stderr
    relations = yaml.safe_load(
        (mini_repo / "knowledge/concept-relations.yaml").read_text())["relations"]
    assert {"from": "concept-variance", "type": "requires",
            "to": "concept-expected-value"} in relations

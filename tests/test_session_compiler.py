import pytest
from learning_os.loader import load_repo
from pathlib import Path
import json

from learning_os.genout.session_compiler import _compile_sessions

@pytest.fixture
def repo():
    return load_repo(Path('.'))

def test_compiler_yields_evidence_when_unseen(repo, monkeypatch):
    # Mock the reading of learner-interpretations.json
    def mock_read_text(self):
        if "learner-interpretations.json" in str(self):
            return json.dumps({"interpretations": {"req-sad-l08-clt-distinguish": {"status": "unseen"}}})
        return self._original_read_text()
    
    Path._original_read_text = Path.read_text
    monkeypatch.setattr(Path, "read_text", mock_read_text)
    
    sessions = _compile_sessions(repo)
    assert len(sessions) == 1
    session = sessions[0]
    
    assert session["current_status"] == "unseen"
    assert len(session["steps"]) == 2
    
    roles = [s["role"] for s in session["steps"]]
    assert "explanation" in roles
    assert "independent evidence" in roles
    
    # Assert rejected
    assert len(session["rejected_alternatives"]) > 0

def test_compiler_yields_guided_practice_when_fragile(repo, monkeypatch):
    def mock_read_text(self):
        if "learner-interpretations.json" in str(self):
            return json.dumps({"interpretations": {"req-sad-l08-clt-distinguish": {"status": "fragile"}}})
        return self._original_read_text()
    
    Path._original_read_text = Path.read_text
    monkeypatch.setattr(Path, "read_text", mock_read_text)
    
    sessions = _compile_sessions(repo)
    assert len(sessions) == 1
    session = sessions[0]
    
    assert session["current_status"] == "fragile"
    assert len(session["steps"]) == 2
    
    roles = [s["role"] for s in session["steps"]]
    assert "guided practice" in roles
    assert "evidence task" in roles


"""Architecture documentation fails visibly on ownership, reference or graph drift."""

from __future__ import annotations

from pathlib import Path

import pytest
import system_map as sm

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def mapped_repo(tmp_path):
    def put(relative, text):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    put("pyproject.toml", '''[[tool.importlinter.contracts]]
name = "layers"
type = "layers"
containers = ["learning_os"]
layers = ["app", "domain"]
''')
    put("tools/learning_os/app/main.py", "from learning_os.domain import rules\ndef run(): pass\n")
    put("tools/learning_os/domain/rules.py", "def evaluate(): pass\n")
    put("tests/test_rule.py", "def test_rule(): pass\n")
    put("system/adr/ADR-001-demo.md", "# decision\n")
    for identifier, path, symbol in (("app", "app/main.py", "run"),
                                      ("domain", "domain/rules.py", "evaluate")):
        put(f"system/developer/components/{identifier}.md", f'''# {identifier}

## Purpose
Own {identifier}.
## Owned paths
- `tools/learning_os/{path}`
## Entry points
- `tools/learning_os/{path}::{symbol}`
## Depends on and used by
<!-- system-map:begin name=edges -->
<!-- system-map:end -->
## Invariants
- Preserve the owning boundary. Pinning: `tests/test_rule.py::test_rule`.
## Pinning tests
- `tests/test_rule.py::test_rule`
## Binding ADRs
- `system/adr/ADR-001-demo.md`
''')
    for name, block in (("CODEMAP", "index"), ("C4", "components")):
        put(f"system/developer/{name}.md", f"# {name}\n<!-- system-map:begin name={block} -->\n<!-- system-map:end -->\n")
    put("system/developer/FLOWS.md", "<!-- system-map:symbol tools/learning_os/app/main.py::run -->\n")
    assert sm.check(tmp_path, write=True) == []
    return tmp_path


def test_real_map_owns_every_module_and_matches_source():
    assert sm.check(ROOT) == []
    assert (ROOT / "system/developer/FLOWS.md").read_text().count("sequenceDiagram") == 4


def test_generation_is_idempotent_and_check_does_not_write(mapped_repo):
    before = {p: p.read_bytes() for p in mapped_repo.rglob("*") if p.is_file()}
    assert sm.check(mapped_repo) == []
    assert sm.check(mapped_repo, write=True) == []
    assert before == {p: p.read_bytes() for p in before}


@pytest.mark.parametrize("change,expected", [
    ("unowned", "expected one owner"),
    ("overlap", "expected one owner"),
    ("empty_glob", "owned path matches nothing"),
    ("entry", "missing entry point"),
    ("test", "missing pinning test"),
    ("adr", "missing ADR"),
    ("flow", "missing flow symbol"),
    ("stale", "stale edges"),
    ("duplicate_block", "generated block names"),
    ("layer", "layer violation"),
    ("long_page", "exceeds 80 lines"),
    ("heading", "expected headings"),
    ("path", "missing named path"),
])
def test_negative_controls(mapped_repo, change, expected):
    root = mapped_repo
    page = root / "system/developer/components/app.md"
    text = page.read_text()
    if change == "unowned":
        (root / "tools/learning_os/app/new.py").write_text("# new\n")
    elif change == "overlap":
        (page.parent / "duplicate.md").write_text(text)
    elif change == "empty_glob":
        page.write_text(text.replace("## Entry points", "- `tools/learning_os/app/nope.py`\n\n## Entry points"))
    elif change in {"entry", "test", "adr"}:
        old, new = {"entry": ("main.py::run", "main.py::missing"),
                    "test": ("test_rule.py::test_rule", "test_rule.py::missing"),
                    "adr": ("ADR-001-demo.md", "ADR-999-gone.md")}[change]
        page.write_text(text.replace(old, new))
    elif change == "flow":
        (root / "system/developer/FLOWS.md").write_text(
            "<!-- system-map:symbol tools/learning_os/app/main.py::missing -->\n")
    elif change == "stale":
        page.write_text(text.replace("Depends on: `domain`.", "Depends on: none."))
    elif change == "duplicate_block":
        page.write_text(text + "\n<!-- system-map:begin name=edges -->\n<!-- system-map:end -->\n")
    elif change == "layer":
        (root / "tools/learning_os/domain/rules.py").write_text(
            "from learning_os.app import main\ndef evaluate(): pass\n")
    elif change == "long_page":
        page.write_text(text + "\n" * 81)
    elif change == "heading":
        page.write_text(text.replace("## Purpose", "## Missing"))
    elif change == "path":
        path = root / "system/developer/CODEMAP.md"
        path.write_text(path.read_text() + "\n`tools/nonexistent.py`\n")
    assert any(expected in error for error in sm.check(root))


@pytest.mark.parametrize("reference,expected", [
    ("", "exactly one reference"),
    ("<!-- system-map:participant P component:missing -->", "invalid participant"),
    ("<!-- system-map:participant P external:undeclared -->", "invalid participant"),
    ("<!-- system-map:participant P tools/learning_os/app/main.py::gone -->", "invalid participant"),
])
def test_flow_participants_resolve_to_symbols_components_or_declared_externals(
        mapped_repo, reference, expected):
    (mapped_repo / "system/developer/FLOWS.md").write_text(
        "## Flow\n" + reference + "\n```mermaid\nsequenceDiagram\n"
        "  participant P as pipeline\n```\n")
    assert any(expected in error for error in sm.check(mapped_repo))


def test_symbol_reference_cannot_read_outside_checkout(mapped_repo):
    assert not sm.symbol_exists(mapped_repo, "../outside.py::run")

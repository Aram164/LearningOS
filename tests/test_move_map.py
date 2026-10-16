"""Mechanical move tool (Phase 6 OD9, 6.0.2)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "tools" / "move_map.py"


def _git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-c", "user.name=Move Test",
         "-c", "user.email=test@example.invalid",
         "-c", "commit.gpgsign=false", *args],
        cwd=root, text=True, capture_output=True, check=True)
    return proc.stdout


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "main")
    _write(root, "tools/learning_os/__init__.py", "")
    _write(root, "tests/test_consumer.py", "VALUE = 0\n")
    _write(root, "pyproject.toml", '[project]\nname = "tiny"\n')
    return root


def _commit(root: Path) -> None:
    _git(root, "add", ".")
    _git(root, "commit", "-m", "base")


def _run(root: Path, map_text: str, *flags: str) -> subprocess.CompletedProcess:
    map_path = root / "MAP.yaml"
    map_path.write_text(map_text, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(TOOL), "--map", str(map_path), *flags],
        cwd=root, text=True, capture_output=True)


def _status(root: Path) -> str:
    return _git(root, "status", "--porcelain")


def test_module_move_with_absolute_and_relative_importers(tmp_path):
    root = _repo(tmp_path)
    _write(root, "tools/learning_os/oldmod.py", "VALUE = 1\n")
    _write(root, "tools/learning_os/bar/__init__.py", "")
    _write(root, "tools/learning_os/use_abs.py",
           "from learning_os.oldmod import VALUE\nimport learning_os.oldmod\n")
    _write(root, "tools/learning_os/use_rel.py",
           "from .oldmod import VALUE as REL_VALUE\n")
    _write(root, "tests/test_consumer.py",
           "from learning_os.oldmod import VALUE\n")
    _commit(root)
    result = _run(root, "moves:\n"
                  "  - from: tools/learning_os/oldmod.py\n"
                  "    to: tools/learning_os/bar/oldmod.py\n", "--apply")
    assert result.returncode == 0, result.stderr
    assert not (root / "tools/learning_os/oldmod.py").exists()
    assert (root / "tools/learning_os/bar/oldmod.py").read_text(
        encoding="utf-8") == "VALUE = 1\n"
    assert (root / "tools/learning_os/use_abs.py").read_text(
        encoding="utf-8") == (
            "from learning_os.bar.oldmod import VALUE\n"
            "import learning_os.bar.oldmod\n")
    assert (root / "tools/learning_os/use_rel.py").read_text(
        encoding="utf-8") == (
            "from learning_os.bar.oldmod import VALUE as REL_VALUE\n")
    assert (root / "tests/test_consumer.py").read_text(
        encoding="utf-8") == "from learning_os.bar.oldmod import VALUE\n"
    assert "files moved: 1" in result.stdout


def test_package_move(tmp_path):
    root = _repo(tmp_path)
    _write(root, "tools/learning_os/pkg/__init__.py", "")
    _write(root, "tools/learning_os/pkg/mod.py", "X = 2\n")
    _write(root, "tools/learning_os/use_pkg.py",
           "from learning_os.pkg.mod import X\n")
    _write(root, "tests/test_consumer.py", "import learning_os.pkg.mod\n")
    _commit(root)
    result = _run(root, "moves:\n"
                  "  - from: tools/learning_os/pkg/\n"
                  "    to: tools/learning_os/newpkg/\n", "--apply")
    assert result.returncode == 0, result.stderr
    assert (root / "tools/learning_os/newpkg/mod.py").exists()
    assert (root / "tools/learning_os/use_pkg.py").read_text(
        encoding="utf-8") == "from learning_os.newpkg.mod import X\n"
    assert (root / "tests/test_consumer.py").read_text(
        encoding="utf-8") == "import learning_os.newpkg.mod\n"
    assert "files moved: 2" in result.stdout


def test_relative_import_inside_moved_module(tmp_path):
    root = _repo(tmp_path)
    _write(root, "tools/learning_os/a.py", "A = 1\n")
    _write(root, "tools/learning_os/b.py",
           "from .a import A\nfrom . import a\n")
    _write(root, "tools/learning_os/sub/__init__.py", "")
    _commit(root)
    result = _run(root, "moves:\n"
                  "  - from: tools/learning_os/b.py\n"
                  "    to: tools/learning_os/sub/b.py\n", "--apply")
    assert result.returncode == 0, result.stderr
    assert (root / "tools/learning_os/sub/b.py").read_text(
        encoding="utf-8") == (
            "from learning_os.a import A\nfrom learning_os import a\n")


def test_layers_token_rewrite(tmp_path):
    root = _repo(tmp_path)
    _write(root, "tools/learning_os/oldmod.py", "VALUE = 1\n")
    _write(root, "tools/learning_os/bar/__init__.py", "")
    _write(root, "pyproject.toml",
           "[tool.importlinter]\n"
           'layers = ["alpha : oldmod : beta", "oldmod | gamma"]\n'
           'other = "oldmod"\n')
    _commit(root)
    result = _run(root, "moves:\n"
                  "  - from: tools/learning_os/oldmod.py\n"
                  "    to: tools/learning_os/bar/oldmod.py\n", "--apply")
    assert result.returncode == 0, result.stderr
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert '"alpha : bar : beta"' in text
    assert '"bar | gamma"' in text
    assert 'other = "oldmod"' in text


def test_refusal_on_match_in_recorded(tmp_path):
    root = _repo(tmp_path)
    _write(root, "tools/learning_os/oldmod.py", "VALUE = 1\n")
    _write(root, "tools/learning_os/bar/__init__.py", "")
    _write(root, "tests/scenarios/recorded/case.json",
           '{"module": "learning_os.oldmod"}\n')
    _commit(root)
    map_text = ("moves:\n"
                "  - from: tools/learning_os/oldmod.py\n"
                "    to: tools/learning_os/bar/oldmod.py\n")
    (root / "MAP.yaml").write_text(map_text, encoding="utf-8")
    before = _status(root)
    result = _run(root, map_text, "--apply")
    assert result.returncode == 2
    assert "tests/scenarios/recorded/case.json" in result.stderr
    assert (root / "tools/learning_os/oldmod.py").exists()
    assert _status(root) == before


def test_refusal_when_destination_exists(tmp_path):
    root = _repo(tmp_path)
    _write(root, "tools/learning_os/oldmod.py", "VALUE = 1\n")
    _write(root, "tools/learning_os/bar/__init__.py", "")
    _write(root, "tools/learning_os/bar/oldmod.py", "VALUE = 9\n")
    _commit(root)
    map_text = ("moves:\n"
                "  - from: tools/learning_os/oldmod.py\n"
                "    to: tools/learning_os/bar/oldmod.py\n")
    (root / "MAP.yaml").write_text(map_text, encoding="utf-8")
    before = _status(root)
    result = _run(root, map_text, "--apply")
    assert result.returncode == 2
    assert "already exists" in result.stderr
    assert _status(root) == before


def test_check_changes_nothing(tmp_path):
    root = _repo(tmp_path)
    _write(root, "tools/learning_os/oldmod.py", "VALUE = 1\n")
    _write(root, "tools/learning_os/bar/__init__.py", "")
    _write(root, "tools/learning_os/use_abs.py",
           "from learning_os.oldmod import VALUE\n")
    _commit(root)
    map_text = ("moves:\n"
                "  - from: tools/learning_os/oldmod.py\n"
                "    to: tools/learning_os/bar/oldmod.py\n")
    map_path = root / "MAP.yaml"
    map_path.write_text(map_text, encoding="utf-8")
    before = _status(root)
    result = subprocess.run(
        [sys.executable, str(TOOL), "--map", str(map_path), "--check"],
        cwd=root, text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert "learning_os.oldmod" in result.stdout
    assert "files moved: 1" in result.stdout
    assert _status(root) == before
    assert (root / "tools/learning_os/oldmod.py").exists()


def test_unmoved_imports_stay_byte_identical(tmp_path):
    root = _repo(tmp_path)
    _write(root, "tools/learning_os/oldmod.py", "VALUE = 1\n")
    _write(root, "tools/learning_os/stays.py", "S = 1\n")
    _write(root, "tools/learning_os/bar/__init__.py", "")
    untouched = "import os\nfrom learning_os.stays import S\nfrom .stays import S as S2\n"
    _write(root, "tools/learning_os/untouched.py", untouched)
    _commit(root)
    result = _run(root, "moves:\n"
                  "  - from: tools/learning_os/oldmod.py\n"
                  "    to: tools/learning_os/bar/oldmod.py\n", "--apply")
    assert result.returncode == 0, result.stderr
    assert (root / "tools/learning_os/untouched.py").read_bytes() == (
        untouched.encode("utf-8"))

"""Learning OS v3 tooling package.

Loader, validator and generator for the authored repository.
See system/BUILD-SPEC.md Steps 3-5; rules in system/VALIDATION.md.
"""

import sys as _sys
from importlib.metadata import PackageNotFoundError as _PackageNotFoundError
from importlib.metadata import version as _distribution_version
from pathlib import Path as _Path

if _sys.version_info < (3, 12):  # noqa: UP036 - the guard exists for older interpreters
    # pyproject.toml declares requires-python >= 3.12. Without this guard an
    # older interpreter (a CI image, an agent VM) dies on `import tomllib`
    # deep in the import chain, which reads as "the CLI cannot run here" and
    # sends the operator back to re-deriving state from files.
    raise ImportError(
        f"LearningOS needs Python >= 3.12; this is {_sys.version.split()[0]}. "
        "Use the project venv (`make setup`), or build one outside the "
        "repository: `uv venv --python 3.12 ~/losvenv && uv pip install "
        "--python ~/losvenv/bin/python PyYAML 'jsonschema>=4' pypdf`, then run "
        "the tool with ~/losvenv/bin/python."
    )


def _declared_version() -> str:
    """Read the one package version declared by ``pyproject.toml``.

    A source checkout has the declaration beside ``tools/``.  An installed
    wheel does not, so distribution metadata is the packaging-safe fallback;
    setuptools derives that metadata from the same declaration.
    """
    pyproject = _Path(__file__).resolve().parents[2] / "pyproject.toml"
    if pyproject.is_file():
        import tomllib

        with pyproject.open("rb") as stream:
            project = tomllib.load(stream).get("project", {})
        value = project.get("version") if isinstance(project, dict) else None
        if isinstance(value, str) and value.strip():
            return value.strip()
        raise RuntimeError(f"{pyproject} has no non-empty project.version")
    try:
        return _distribution_version("learningos-core")
    except _PackageNotFoundError as exc:
        raise RuntimeError(
            "learningos-core version is unavailable: pyproject.toml and installed "
            "package metadata are both missing"
        ) from exc


__version__ = _declared_version()


def _check_deps() -> None:
    """Fail fast with a human instruction instead of a mid-run traceback."""
    problems = []
    try:
        import yaml  # noqa: F401
    except ImportError:
        problems.append("pyyaml is not installed")
    try:
        import jsonschema as _js
        if not hasattr(_js, "Draft202012Validator"):
            problems.append("jsonschema is too old (need >= 4)")
    except ImportError:
        problems.append("jsonschema is not installed")
    if problems:
        _sys.stderr.write(
            "learning_os: cannot run — " + "; ".join(problems) + ".\n"
            "Fix with:  make setup   (creates .venv and installs pyproject.toml)\n"
            "Or directly:  python3 -m pip install -e \".[dev]\"\n"
            "(add --break-system-packages if pip refuses on a system Python)\n")
        raise SystemExit(2)


_check_deps()

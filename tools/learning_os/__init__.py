"""Learning OS v3 tooling package.

Loader, validator and generator for the authored repository.
See system/BUILD-SPEC.md Steps 3-5; rules in system/VALIDATION.md.
"""

import sys as _sys
import tomllib as _tomllib
from importlib.metadata import PackageNotFoundError as _PackageNotFoundError
from importlib.metadata import version as _distribution_version
from pathlib import Path as _Path


def _declared_version() -> str:
    """Read the one package version declared by ``pyproject.toml``.

    A source checkout has the declaration beside ``tools/``.  An installed
    wheel does not, so distribution metadata is the packaging-safe fallback;
    setuptools derives that metadata from the same declaration.
    """
    pyproject = _Path(__file__).resolve().parents[2] / "pyproject.toml"
    if pyproject.is_file():
        with pyproject.open("rb") as stream:
            project = _tomllib.load(stream).get("project", {})
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

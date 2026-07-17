"""Learning OS v3 tooling package.

Loader, validator and generator for the authored repository.
See system/BUILD-SPEC.md Steps 3-5; rules in system/VALIDATION.md.
"""

import sys as _sys

__version__ = "0.1.0"


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
            "Fix with:  python3 -m pip install --upgrade pyyaml \"jsonschema>=4\"\n"
            "(add --break-system-packages if pip refuses on a system Python)\n")
        raise SystemExit(2)


_check_deps()

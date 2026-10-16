"""CLI tool passthrough handlers (SPEC (cy) R6).

No PLAN area owns the repository's own tools, so the subprocess and
in-process passthroughs live here. Each handler returns the child's
exact streams and exit in the ``CommandOutput`` carrier; the CLI
pipeline prints them verbatim and nothing else.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from learning_os.ops.context import OpContext
from learning_os.ops.projection import _publish
from learning_os.ops.proposal import CommandOutput, Result
from learning_os.ops.registry import register

TOOLS = Path(__file__).resolve().parent.parent.parent.parent


@register("cli.validate", kind="tool")
def validate_command(ctx: OpContext, req: dict) -> Result:
    """Delegate to tools/validate.py, capturing its exact output."""
    extra = ["--online"] if req.get("online") else []
    proc = subprocess.run(
        [sys.executable, str(TOOLS / "validate.py"), *extra,
         "--root", str(ctx.root)],
        capture_output=True, text=True)
    return Result({}, command_output=CommandOutput(
        stdout=proc.stdout, stderr=proc.stderr,
        exit_code=proc.returncode))


@register("cli.generate", kind="porcelain")
def generate_command(ctx: OpContext, req: dict) -> Result:
    """Publish generated/manifest.json in-process (R6 form b)."""
    _publish(ctx.root)
    return Result({}, command_output=CommandOutput(
        stdout="published generated/manifest.json (atomic contract snapshot)\n",
        stderr="", exit_code=0))

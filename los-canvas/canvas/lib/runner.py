"""A very small test runner for the canvas.

The canvas is not a pytest suite: the point is to record *what the operator
saw*, so each case returns a dictionary of observations and the runner
writes both JSON (machine) and Markdown (human) reports.
"""

from __future__ import annotations

import json
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass
class Case:
    name: str
    intent: str          # what an operator would be trying to do
    fn: Callable[[], dict]
    tags: list[str] = field(default_factory=list)


@dataclass
class Outcome:
    case: Case
    ok: bool
    detail: dict
    seconds: float
    error: str | None = None


def approx_tokens(text: str) -> int:
    """Rough token count. Good enough to compare reads against each other."""
    return max(1, len(text) // 4)


def run_cases(cases: list[Case], out_dir: Path, title: str) -> list[Outcome]:
    out_dir.mkdir(parents=True, exist_ok=True)
    outcomes: list[Outcome] = []
    for case in cases:
        start = time.perf_counter()
        try:
            detail = case.fn() or {}
            ok = bool(detail.pop("ok", True))
            error = None
        except Exception as exc:                      # noqa: BLE001
            detail = {"traceback": traceback.format_exc()[-2000:]}
            ok = False
            error = f"{type(exc).__name__}: {exc}"
        elapsed = time.perf_counter() - start
        outcomes.append(Outcome(case, ok, detail, elapsed, error))
        flag = "PASS" if ok else "FAIL"
        print(f"[{flag}] {case.name} ({elapsed:.1f}s)")
        if error:
            print(f"       {error}")
    (out_dir / f"{title}.json").write_text(
        json.dumps([{
            "name": o.case.name,
            "intent": o.case.intent,
            "tags": o.case.tags,
            "ok": o.ok,
            "seconds": round(o.seconds, 2),
            "error": o.error,
            "detail": o.detail,
        } for o in outcomes], indent=2, sort_keys=False), encoding="utf-8")
    write_markdown(out_dir / f"{title}.md", title, outcomes)
    return outcomes


def write_markdown(path: Path, title: str, outcomes: list[Outcome]) -> None:
    passed = sum(1 for o in outcomes if o.ok)
    lines = [f"# {title}", "",
             f"**{passed}/{len(outcomes)} passed.**", ""]
    for o in outcomes:
        lines.append(f"## {'PASS' if o.ok else 'FAIL'} — {o.case.name}")
        lines.append("")
        lines.append(f"*Intent:* {o.case.intent}")
        lines.append("")
        if o.error:
            lines.append(f"*Error:* `{o.error}`")
            lines.append("")
        for key, value in o.detail.items():
            if key == "traceback":
                continue
            rendered = value if isinstance(value, str) else json.dumps(value, indent=1)
            if len(rendered) > 1200:
                rendered = rendered[:1200] + "\n… (truncated)"
            lines.append(f"**{key}**")
            lines.append("")
            lines.append("```")
            lines.append(rendered)
            lines.append("```")
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")

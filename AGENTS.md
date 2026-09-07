# AI operator entry point

Read and obey [`system/OPERATOR.md`](system/OPERATOR.md). Discover capabilities
with `python tools/los.py capabilities --compact --json`; bootstrap a task with
`python tools/los.py bootstrap --compact`. Read one capability's complete
definition with `python tools/los.py capabilities NAME --json`. Do not recursively scan the repository or
sibling code repositories such as `Stratum/` to infer application state.

Codex reads this file as **planner and reviewer, not executor**: it plans and
challenges, Claude Code implements. The full role is in `AGENTS.md` at the
`semestercontext/` root, which Codex loads only when started from there.

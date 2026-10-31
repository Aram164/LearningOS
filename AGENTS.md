# AI task entry points

For code, architecture, contracts, tests or documentation changes, start with
[`system/DEVELOPER.md`](system/DEVELOPER.md). For operating learner state, use
the operator route below. Audience selects reading order, never an exemption
from relevant binding rules.

To answer a question without changing anything, run
.venv/bin/python tools/agent_run.py --catalog --root . and use what it lists;
reads cannot change a record, so they need nothing else read first. Before any
write, read and obey [`system/OPERATOR.md`](system/OPERATOR.md). Discover capabilities
with `.venv/bin/python tools/los.py capabilities --compact --json`; start with the entry
read OPERATOR.md names for the task — a named route or stage starts with its
focused `plan-edit-context` read, an open question with `bootstrap --brief`.
Read one capability, command or task with `.venv/bin/python tools/los.py
capabilities NAME --json`; NAME may be a capability id, a CLI command, or a task id.
Do not recursively scan the repository or
sibling code repositories such as `Stratum/` to infer application state.
When operating learner records, run the named entry read first. Do not
precede it with directory listings, `--help` probes, or whole-document
reads unless that entry fails or the task crosses the scope it declares.
Code, architecture, contract, test and documentation changes still start
at `system/DEVELOPER.md` and inspect code as that route requires.

No agent has a standing role here: Aram assigns planning, reviewing and
implementing per task. Workspace-wide guidance for plans and reviews is in
`AGENTS.md` at the `semestercontext/` root.

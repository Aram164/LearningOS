# Agent plans

## Run a multi-step agent plan

Multi-step agent work runs through `tools/agent_run.py PLAN --root ROOT`.
A single focused read may remain a direct `los` call.

1. Build a disposable fixture root for write examples; never run fixture
   writes against the learner root.
2. Author a plan with a stable `session_id`, explicit unique `key` on every
   log step, and `depends_on` naming earlier steps only.
3. Optionally set `read_workers` (1-4, default 1), `deadline_s`
   (default 120) and `report_max_bytes` (default 65536).
4. Run the runner; exit 0 means all steps ok, 3 a step failed or was
   blocked, 2 an invalid plan.
5. Expand a bounded report through the `full_report` artifact path it
   prints; the artifact holds complete step outputs and receipts.

Writes stay serial and session-bound. Dependent reads wait for the shared
projection-readiness service; unknown projections refuse rather than guess.

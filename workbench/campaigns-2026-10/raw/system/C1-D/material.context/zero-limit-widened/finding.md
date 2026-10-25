# material.context: an explicit `--limit 0` is silently widened to a full page of 20

**Capability:** `material.context` (handler `material_context`,
`tools/learning_os/app/handlers/materials.py:1199`)
**Test:** `test_zero_limit_widened.py` (clone path while hunting:
`tests/test_c1d_material_context_zero_limit.py`) — fails on base main
`d6c47790`. Severity: minor (no data damage; a declared refusal never fires).

## Command

```
los material-context "density worked example" --limit 0
```

(direct CLI on a repo with one matching analysis note; the same payload value
reaches the handler through a V2 query envelope.)

## Observed (verbatim pytest tail)

```
E       AssertionError: --limit 0 returned 1 item(s) (total=1); the request contract bounds the page size to 1..20 and _window_values refuses out-of-range limits, but material_context's 'or 20' fallback widens an explicit zero to a full maximum page instead of refusing it
E       assert (0 != 0 or not [{'origin': 'analysis-note', 'id': 'note-context-density-pp001-003', ...}])
FAILED tests/test_c1d_material_context_zero_limit.py::test_zero_limit_is_refused_not_silently_widened
1 failed in 0.23s
```

Exit code 0, a full result page (capped at 20 items when more match).

## Expected

`--limit 0` must be refused. Which line says so:

- `system/schema/requests/material.context.schema.json`, property `limit`:
  "page size from 1 to 20 items";
- the shared window helper the handler itself calls next,
  `_window_values` (`tools/learning_os/app/handlers/_shared.py:126-133`):
  "offset must be nonnegative and limit between 1 and {maximum}" — the same
  rule `inbox.content` applies to its `req["limit"]` verbatim.

## Root cause

`tools/learning_os/app/handlers/materials.py:1204-1206` — the fallback runs
*before* the range check:

```python
offset, limit = _window_values(
    req.get("offset") or 0, req.get("limit") or 20,
    req.get("expected_snapshot"), 20)
```

An explicit `0` is falsy, so `req.get("limit") or 20` substitutes the maximum
and `_window_values` sees a perfectly valid `20`. The declared refusal site
(`bad-window`) is unreachable for `limit=0` — a refusal site that is declared
but never witnessed. `limit=None` (omitted) is fine: the gateway namespace
applies the CLI default of 5 (`payload_to_namespace_from_schema`), so only the
explicit zero is affected.

## Suggested fix

Read the page size without the truthiness fallback —
`limit = req.get("limit") if req.get("limit") is not None else 20` (or
`_window_values(req.get("limit") or 20 → max(req.get("limit") or 0, ...))`
style) — so an explicit `0` reaches the 1..20 check and refuses with
`{operation}.bad-window`, matching `inbox.content` and the request schema's
"from 1 to 20 items".

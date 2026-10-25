# Finding: `module.create` accepts an id that already exists as a legacy-registry canonical identity

Capability: `module.create` (batch C1-A)
Reproduction: `test_legacy_identity_clash.py` (this folder). Status on base
`main` (`d6c4779029e366718b71bda158d2aa8f9da1db39`): **fails** — the bug is
present. It passes once the declared refusal exists.

## The command

```
los module-create --file <package with module.id = module-legacy-clash> --check
```

on a synthetic repository where `records/modules.yaml` carries a legacy record
with `id: module-legacy-clash` and no partitioned module of that id exists
(the test renames the mini fixture's legacy record; see the test file for the
exact fixture). The V2 apply was probed the same way and also succeeded.

## Observed (verbatim, from the focused pytest run and the probe)

`--check` exits 0:

```json
{"ok":true,"check":true,"mode":"check","capability":"module.create",
 "module_id":"module-legacy-clash","files_checked":2,
 "reviewed_file_sha256":"sha256:16df4e28f46324d62e2bab84ed8aeab1ddfcc005b64c0e8c0b86eb7efa02a7bd",
 "changes":"present","module_listing":{"listed":true, ...},
 "expected_write_paths":["curriculum/modules/module-legacy-clash/module.yaml",
                         "curriculum/modules/module-legacy-clash/source-map.yaml"], ...}
```

The apply then exits 0 and writes `curriculum/modules/module-legacy-clash/`.
Afterwards the tree loads and validates clean, but the identity exists twice:
once as the partitioned record, once in the frozen legacy registry — and the
loader registers only the partitioned one, so the legacy record's facts (for
example its `attempts`) are shadowed and invisible to every view.

## Expected, and which line says so

Refusal. `system/contracts/capabilities.yaml`, `module.create` invariants:

> the destination must not exist: an existing canonical identity or file is
> refused, because an absent revision entry cannot prove absence

A legacy registry record is a canonical identity: the loader reads it
(`records/modules.yaml` is a loaded, validated input) and the validator's
`MODULE-MIGRATION` rule treats every legacy id as an owned module that the
partitioned records must cover. The handler's own docstring
(`tools/learning_os/app/handlers/plan.py:962`) says "It refuses an existing
destination" and `_creation_destination_problems` (same file) says "Only the
filesystem can say whether the identity is already taken" — that reasoning is
incomplete: the loaded registry also knows.

## Root cause

`tools/learning_os/app/handlers/plan.py:940-957` —
`_creation_destination_problems` checks only
`curriculum/modules/<module_id>/module.yaml` and the module directory on the
filesystem (called at `plan.py:1033`). It never consults the loaded registry,
although `ctx.repo()` is available in the same handler (`plan.py:1051`) and
`repo.legacy_modules` holds exactly those ids
(`tools/learning_os/store/loading/curriculum.py:81-111, 206-232` — once any
partitioned module exists, legacy records are loaded into
`repo.legacy_modules` only, and a matching new partitioned record shadows
them). The validator cannot catch the collision either:
`tools/learning_os/derive/validation/curriculum.py:79-83` (`MODULE-MIGRATION`)
only requires every legacy id to be *covered* by a partitioned record — a
duplicate satisfies it.

## Reachability (honest scoping)

In the live tree at `d6c47790`, all six ids in `records/modules.yaml` already
have partitioned modules, so today those specific ids are refused by the
filesystem check. The gap is reachable in any tree where a legacy record is
not yet partitioned: restored or historical snapshots, partially migrated
branches, future legacy records, and every synthetic fixture (the tests use
one). The declared refusal is still only half-implemented, and the fix is
cheap.

## Suggested fix

In `module_create`, after the existing filesystem check (or inside
`_creation_destination_problems` with the loaded repo passed in), also refuse
when `module_id` resolves in the loaded registry — concretely when
`module_id in ctx.repo().legacy_modules` (and defensively when
`module_id in ctx.repo().modules`), with the same
`module.create.already-exists` refusal site and a message naming
`records/modules.yaml` as the clashing identity. That makes the code match
the invariant's "existing canonical identity or file" wording: the filesystem
proves file absence, the loaded registry proves identity absence, and each
covers the half the other cannot.

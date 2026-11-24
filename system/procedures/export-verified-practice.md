---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Verify and export a practice item

Use **Atlas → Practice → Load practice items**, or the practice section
of a note inspector. Open the authored note to review the answer. Select
the method and primary evidence, preview the exact verification and
confirm it. The following receipt is from the synthetic fixture. It
exercises the same gateway capability under test approval.

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world_practice)" && export PY="$LOS_REPO/.venv/bin/python" H="$LOS_REPO/tests/procedure_helpers"
```

```scrut
$ "$PY" "$H/los-practice-fixture" prepare
Prepared four synthetic arithmetic items.
```

```scrut
$ "$PY" "$H/los-practice-fixture" attest 1
note-practice-bank#A1 source-matched
```

## Check, apply and sync

Initialize a separate practice vault. Read the action for the selected
item and verify the exact destination in the plan before applying. An
unchanged replay keeps the existing file byte-for-byte.

```scrut
$ export VAULT="$TMPDIR/learnkit-practice" PLAN="$TMPDIR/learnkit-plan.json" EXPORT="$LOS_REPO/tools/export_learnkit.py"
```

```scrut
$ "$PY" "$EXPORT" --root "$LOS_FX" --vault "$VAULT" --init
{"status": "initialized", "vault_id": "*"} (glob)
```

```scrut
$ "$PY" "$EXPORT" --root "$LOS_FX" --vault "$VAULT" --check --item 'note-practice-bank#A1' --out "$PLAN"
{"status": "planned", "actions": ["create"], "out": "*"} (glob)
```

```scrut
$ "$PY" -c 'import json, os; p=json.load(open(os.environ["PLAN"])); [item]=p["items"]; assert len(p["source_content_hashes"][item["item_id"]])==64; print(item["item_id"], item["action"])'
note-practice-bank#A1 create
```

```scrut
$ "$PY" "$EXPORT" --root "$LOS_FX" --vault "$VAULT" --apply "$PLAN"
{"status": "applied", "created": 1, "kept": 0}
```

```scrut
$ "$PY" "$EXPORT" --root "$LOS_FX" --vault "$VAULT" --apply "$PLAN"
{"status": "applied", "created": 0, "kept": 1}
```

In the separate practice vault, run LearnKit sync in `simple-compat`
and open the reviewer. Verify that the new item appears once. An export
refusal should record item ID, check action, snapshot and error. Review
history and scheduling are inspected in LearnKit.

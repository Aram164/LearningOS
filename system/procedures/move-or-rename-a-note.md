---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Move or rename a note (WORKFLOWS §14)

Executable transcript of moving one note to a new bucket: the ID is
preserved, explicit path links are repaired (the fixture holds none, so
the count is measured at zero), ID-based references stay unchanged, and
generated artifacts are rebuilt and validated. No approved capability
moves a note path, so the move below runs only in this disposable
transcript fixture. `tests/test_procedures.py` runs it with Scrut;
`<REPO>` comes from the `LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Measure the explicit path links

```scrut
$ grep -rn "note-demo\.md" --include="*.yaml" --include="*.md" --include="*.json" . | grep -v "^\./knowledge/notes/mathematics/note-demo.md" | grep -v "^\./generated/" | wc -l | tr -d ' '
0
```

## Move the note to its new bucket

```scrut
$ mkdir -p knowledge/notes/statistics && mv knowledge/notes/mathematics/note-demo.md knowledge/notes/statistics/note-demo.md && echo moved
moved
```

## The ID is preserved

```scrut
$ grep -n "^id: note-demo$" knowledge/notes/statistics/note-demo.md
2:id: note-demo
```

## ID-based references stay unchanged

```scrut
$ grep -rn "ultimate_reference: note-demo" curriculum/ | sort
curriculum/modules/module-demo/units/unit-demo-l01/unit.yaml:20:  ultimate_reference: note-demo
curriculum/modules/module-demo/units/unit-demo-l02/unit.yaml:18:  ultimate_reference: note-demo
```

## The move validates clean

```scrut
$ (set -o pipefail; los validate | tail -n 1)
0 error(s), 14 warning(s) — OK
```

## Rebuild the generated artifacts

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

## The note resolves by ID at its new path

```scrut
$ los inspect note-demo | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["id"], d["domain"], d["path"])'
note-demo statistics knowledge/notes/statistics/note-demo.md
```

## The old path is gone

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-demo.md --absent
```

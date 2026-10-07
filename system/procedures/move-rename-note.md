---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Move or rename a note (WORKFLOWS §14)

Executable transcript of changing one note's path: a rename that
breaks the filename-id match fails validation (see M-05), while a
move that keeps the filename validates, keeps the id resolving at
the new path, and rebuilds cleanly. `tests/test_procedures.py` runs
it with Scrut; `<REPO>` comes from the `LOS_REPO` environment
variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## The id resolves at the old path

```scrut
$ los inspect note-demo-analysis | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["id"], d["path"])'
note-demo-analysis knowledge/notes/mathematics/note-demo-analysis.md
```

## Record the current bytes

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-demo-analysis.md --sha256 ecd673fe86ebb2952d5efaf15ee8c4dc49f2f10c3710b795f3b8b0cafd23330c
```

## No canonical file links the old path

```scrut
$ test -z "$(grep -rn "knowledge/notes/mathematics/note-demo-analysis.md" knowledge sources curriculum records work operations)" && echo no-links
no-links
```

## A rename that breaks the filename-id match fails validation (M-05)

```scrut
$ mv knowledge/notes/mathematics/note-demo-analysis.md knowledge/notes/mathematics/note-variance-analysis.md
```

```scrut
$ (set -o pipefail; los validate | tail -n 1)
1 error(s), 10 warning(s) — FAIL
[1]
```

```scrut
$ los validate | grep -c "FILE-NAME"
1
```

## Rename it back

```scrut
$ mv knowledge/notes/mathematics/note-variance-analysis.md knowledge/notes/mathematics/note-demo-analysis.md
```

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-demo-analysis.md --sha256 ecd673fe86ebb2952d5efaf15ee8c4dc49f2f10c3710b795f3b8b0cafd23330c
```

## Move it with its filename intact

```scrut
$ mkdir -p knowledge/notes/reference && mv knowledge/notes/mathematics/note-demo-analysis.md knowledge/notes/reference/note-demo-analysis.md
```

## The bytes moved unchanged

```scrut
$ $H/los-assert-file knowledge/notes/reference/note-demo-analysis.md --sha256 ecd673fe86ebb2952d5efaf15ee8c4dc49f2f10c3710b795f3b8b0cafd23330c
```

## The old path is gone

```scrut
$ $H/los-assert-file knowledge/notes/mathematics/note-demo-analysis.md --absent
```

## The id resolves at the new path

```scrut
$ los inspect note-demo-analysis | $LOS_REPO/.venv/bin/python -c 'import json,sys; d = json.load(sys.stdin); print(d["id"], d["path"])'
note-demo-analysis knowledge/notes/reference/note-demo-analysis.md
```

## Rebuild generated outputs

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

## Validate

```scrut
$ los validate | tail -n 1
0 error(s), 9 warning(s) — OK
```

---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Generate indexes and reports (WORKFLOWS §12)

Executable transcript of the documented generation: one command
produces the indexes, views, reports, backlinks, canvas, and health
report, each stating it is generated with its generator version and
canonical inputs, all gitignored. The validation report is the one
listed product the command does not write — it appears only after a
validation run (see M-04). `tests/test_procedures.py` runs it with
Scrut; `<REPO>` comes from the `LOS_REPO` environment variable the
test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Run the one documented command

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

## The manifest and indexes are there

```scrut
$ $H/los-assert-file generated/manifest.json --exists && $H/los-assert-file generated/concept-index.md --exists && $H/los-assert-file generated/source-index.md --exists
```

## The views and dependency report are there

```scrut
$ $H/los-assert-file generated/module-view.md --exists && $H/los-assert-file generated/coordination-view.md --exists && $H/los-assert-file generated/dependency-report.md --exists
```

## The maps, backlinks, canvas, and atlas are there

```scrut
$ $H/los-assert-file generated/concept-map.md --exists && $H/los-assert-file generated/backlinks.json --exists && $H/los-assert-file generated/nebula.md --exists && $H/los-assert-file generated/domain-atlas.md --exists && $H/los-assert-file generated/reading-room.md --exists && $H/los-assert-file generated/concept-canvas.canvas --exists
```

## The health report is there

```scrut
$ $H/los-assert-file generated/reports/health.md --exists
```

## The validation report is not among the products (M-04)

```scrut
$ $H/los-assert-file generated/reports/validation-report.md --absent
```

## A validation run is what writes it

```scrut
$ los validate | tail -n 1
0 error(s), 9 warning(s) — OK
```

```scrut
$ $H/los-assert-file generated/reports/validation-report.md --exists
```

## Generated files state they are generated

```scrut
$ grep -c "GENERATED file" generated/concept-index.md
1
```

## Generated files name the generator version

```scrut
$ grep -o "learning_os v[0-9.]*" generated/concept-index.md
learning_os v3.2.0
```

## Generated files name their canonical inputs

```scrut
$ grep -o "from: .*" generated/concept-index.md
from: knowledge/, sources/, curriculum/, records/, work/.
```

## The concept index lists aliases

```scrut
$ grep -c "Erwartungswert" generated/concept-index.md
1
```

## The source index links materials

```scrut
$ grep -c "material://" generated/source-index.md
1
```

## Generated outputs are gitignored

```scrut
$ git check-ignore generated/manifest.json && echo ignored
generated/manifest.json
ignored
```

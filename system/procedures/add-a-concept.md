---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Add a concept (WORKFLOWS §4)

Executable transcript of registering one concept: search labels and
aliases in both languages, confirm no equivalent exists, append the
stable id with its English label, German aliases, and one short
disambiguation, then rebuild and confirm the generated index carries
it. `tests/test_procedures.py` runs it with Scrut; `<REPO>` comes
from the `LOS_REPO` environment variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Search labels and aliases, both languages

```scrut
$ los search Erwartungswert | $LOS_REPO/.venv/bin/python -c 'import json,sys; print(sorted(r["id"] for r in json.load(sys.stdin)))'
['concept-expected-value']
```

```scrut
$ los search Variance | $LOS_REPO/.venv/bin/python -c 'import json,sys; print(sorted(r["id"] for r in json.load(sys.stdin)))'
['concept-variance', 'source-map-demo', 'unit-demo-l02']
```

## No equivalent concept exists

```scrut
$ los search Bayes | $LOS_REPO/.venv/bin/python -c 'import json,sys; print(json.load(sys.stdin))'
[]
```

## Append the stable id, label, aliases, and disambiguation

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; p = "knowledge/concepts.yaml"; d = yaml.safe_load(open(p)); d["concepts"].append({"id": "concept-bayes-rule", "label": "Bayes rule", "aliases": ["Satz von Bayes", "Bayes-Theorem"], "description": "Posterior from prior and likelihood."}); open(p, "w").write(yaml.safe_dump(d, sort_keys=False))'
```

## The registry carries the new concept

```scrut
$ $H/los-assert-file knowledge/concepts.yaml --sha256 15217d5b96475f4553d2319ebe1363b8529eacbd4ba2accd47876719feaeb42d
```

## Rebuild generated outputs

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

## The generated index carries the label

```scrut
$ grep -c "Bayes rule" generated/concept-index.md
2
```

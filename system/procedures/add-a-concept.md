---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Add a concept (WORKFLOWS §4)

Executable transcript of registering one concept: search both languages
for an existing equivalent, confirm the nearest neighbor is not one,
add the readable stable ID with its German alias and a short
disambiguation, and rebuild the generated outputs. No approved
capability writes the concept registry, so the registry edit below runs
only in this disposable transcript fixture. `tests/test_procedures.py`
runs it with Scrut; `<REPO>` comes from the `LOS_REPO` environment
variable the test sets.

## Build the fixture

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)" && export H=$LOS_REPO/tests/procedure_helpers
```

## Search the English label

1. search labels and aliases (both languages);
2. reuse an existing concept if semantically equivalent;
3. create a readable stable ID; label in English; add German terms as aliases;
4. add only short disambiguation if necessary — never a full explanation;
5. rebuild generated outputs.

```scrut
$ los search "sample mean"
[]
```

```scrut {output_stream: stderr}
$ los search "sample mean"
los: no record matches all 2 terms; per-term record hits: sample=0 mean=1
```

## Search the German alias

```scrut
$ los search "Stichprobenmittel"
[]
```

```scrut {output_stream: stderr}
$ los search "Stichprobenmittel"
los: no record matches all 1 term; per-term record hits: stichprobenmittel=0
```

## The nearest neighbor is not equivalent

```scrut
$ los inspect concept-expected-value
{"aliases":["Erwartungswert"],"deprecated":false,"id":"concept-expected-value","path":"knowledge/concepts.yaml","title":"Expected value","type":"concept"}
```

A sample mean is not the population expectation, so no existing concept
is reused.

## Add the readable stable ID with a short disambiguation

```scrut
$ $LOS_REPO/.venv/bin/python -c 'import yaml; p = "knowledge/concepts.yaml"; d = yaml.safe_load(open(p)); d["concepts"].append({"id": "concept-sample-mean", "label": "Sample mean", "aliases": ["Stichprobenmittel"], "description": "Mean of a finite sample; not the population expectation."}); open(p, "w").write(yaml.safe_dump(d, sort_keys=False)); print("added", d["concepts"][-1]["id"])'
added concept-sample-mean
```

## The addition validates clean

```scrut
$ (set -o pipefail; los validate | tail -n 1)
0 error(s), 10 warning(s) — OK
```

## Rebuild the generated outputs

```scrut
$ los generate
published generated/manifest.json (atomic contract snapshot)
```

## The index carries the new concept

```scrut
$ grep -n "Sample mean" generated/concept-index.md
10:**S:** [Sample mean](#sample-mean)
33:## Sample mean
```

## The registry resolves the new ID

```scrut
$ los inspect concept-sample-mean
{"aliases":["Stichprobenmittel"],"deprecated":false,"id":"concept-sample-mean","path":"knowledge/concepts.yaml","title":"Sample mean","type":"concept"}
```

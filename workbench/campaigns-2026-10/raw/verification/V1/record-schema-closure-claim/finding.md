# Finding: "Every record schema is `additionalProperties: false`" is false for two record schemas

**Document claim:** `system/developer/changing-contracts.md:7` —
"Every record schema is `additionalProperties: false`, and canonical records
carry no per-record version. That is strict by design, ..."

**Result: FALSE as written** (letter of the claim). The intent — records reject
unknown fields — holds at every root that is actually constrained; the universal
sentence is what fails.

## Evidence

The data contract defines its own record-schema set:
`data_contract.record_schemas()` (`tools/learning_os/store/contracts/data_contract.py:43-59`)
returns every schema under `system/schema/*.schema.json` that does not declare
`x-governs: artifact` — 36 schemas, matching `record_schemas: 36` in
`system/contracts/data-contract.yaml`. Two of them have **no root object
constraint at all**:

- `system/schema/learning-plan.schema.json` — root carries only
  `$schema/$id/title/x-governs/description/$defs` (no `type`, no
  `properties`, no `additionalProperties`). It is a definition library that
  other schemas `$ref` into.
- `system/schema/material-comparison-defs.schema.json` — same shape.

An object carrying arbitrary unknown keys therefore validates against them:

```
$ .venv/bin/python /…/V1/probes/probe_nested_open.py
fixture records matched to a record schema: 168
nested unknown-key acceptance on real frozen records:
  learning-plan.schema.json:
    tests/fixtures/formats/v12/curriculum/modules/module-demo/module.yaml -> unknown key <here> still validates
    …
  material-comparison-defs.schema.json:
    …
```

(`<here>` is the record root: a real frozen `module.yaml` plus one unknown
top-level key still validates.) Probe: `probes/probe_nested_open.py`, log
`logs/nested-open.log`. A static sweep (`logs/schema-strictness.log`) confirms
all other 34 record schemas reject unknown root keys.

## Failing test on the pin

`tests/test_v1_record_schema_closure.py` (registered in `tests/group_map.py`
"contracts" and `.github/shard-manifest.json`):

```
$ .venv/bin/python -m pytest tests/test_v1_record_schema_closure.py -q
…
AssertionError: changing-contracts.md:7 claims every record schema is
additionalProperties: false, but these record schemas accept unknown top-level
keys: {'learning-plan.schema.json': 'accepted an object with an unknown
top-level key', 'material-comparison-defs.schema.json': 'accepted an object
with an unknown top-level key'}
============================== 1 failed in 0.06s ===============================
```

## Assessment

- **Certainly wrong:** the universal sentence. Two of the 36 schemas the data
  contract itself classifies as record schemas are not
  `additionalProperties: false`; they are unconstrained at the root.
- **Mitigating (noted, not a fix):** both are `$defs` libraries — no record is
  *validated at their root* in production, so no stored record can acquire an
  unknown field through them. The doc could carve this out explicitly (e.g.
  "every record schema that validates a record root is closed; definition-only
  libraries are exempt"), but per campaign rules I changed nothing.
- Severity: low. It is a documentation-precision defect, not a data-integrity
  hole; the fingerprint gate (`record_schemas()`) still covers both files.

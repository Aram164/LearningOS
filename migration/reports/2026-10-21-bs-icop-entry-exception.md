# BS and ICOP module-entry exception

User explicitly approved applying the five reviewed files as a one-time exception to missing module/collection creation commands. Exact reply: Yes, apply the five reviewed files.

Reason: the current capability index has no module or collection creation command; module.plan.import requires an already canonical module. OPERATOR boundary 11 was not silently bypassed. The user reviewed the five-file draft before approval.

Scope: enrolled Bachelor module entries for WiSe 2026/27, source adoption metadata, and the ICOP reading shelf. No current-semester rollover or lecture/study plan was performed. BS reference slides were copied byte-identically from `/Users/aramaljanadi/Desktop/Huberlin /Betriebssysteme`; originals remain in place. The ICOP paper names come from the supplied screenshot and were not fetched.

Created files and SHA-256:

- `curriculum/modules/module-hu-betriebssysteme/module.yaml`: `d3da500bee659110a68e08aeebb98cf2da611b5cafbfb4152a7995bf614e748b` (previously absent).
- `curriculum/modules/module-hu-betriebssysteme/source-map.yaml`: `ad8fe592dadc57fd429a460ee052e0ce036b68ef926cbf22c5360c87a9c155ad` (previously absent).
- `curriculum/modules/module-hu-icop/module.yaml`: `c2910a1f779159cda42d5d25c082bcbe7a75b0a40830673a4f51798222c3d117` (previously absent).
- `curriculum/modules/module-hu-icop/source-map.yaml`: `6e846e6e9ef04f7a98357d677810fe2e2c2268d70b03331e4849e825f2753aee` (previously absent).
- `sources/collections/icop-reading.yaml`: `e8eb8dd444689f60e001726315dd551131fdcd3856d7d283d40742de0e65b2c6` (previously absent).

Source metadata and local-material attachments use the ordinary source.intake.record and source.record.revise gateways with transaction receipts. Physical placement follows tools/build_materials_tree.py; the materials manifest inventories exact local bytes. Scratch review package and the full copy/move receipts: `LearningOS/workbench/course-intake-2026-10-21/`.

Gateway receipts:

- `operations/transactions/transaction-20261021-002904-001.yaml`
- `operations/transactions/transaction-20261021-003114-001.yaml`
- `operations/transactions/transaction-20261021-005652-001.yaml`
- `operations/transactions/transaction-20261021-003133-001.yaml`
- `operations/transactions/transaction-20261021-002755-001.yaml`
- `operations/transactions/transaction-20261021-003056-001.yaml`

Final material verification: both books and both course-source bindings resolve to local files. All three recovered BS PDFs match their still-preserved Desktop originals by SHA-256.

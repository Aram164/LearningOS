# Full dossier payload for one screened material checksum

**Observed:** 2026-09-29, completing the Grinstead local attachment after the `source.record.revise` fix.

## Where the friction appeared

The new capability correctly found that attaching `material://source-grinstead-snell/grinstead.pdf` changed SaD L04's approved dossier basis. The only evidential change was the checksum for `route-fe8b4fbc40e7e85daf8ef25b`: a route-text token became the PDF's verified SHA-256. Grinstead's assessment was `screened`, had no evidence or comparison rows, and all 29 assessments and their judgments were preserved. Nevertheless, the request had to carry the entire replacement dossier: 32,555 bytes in the YAML package, 43,044 bytes in the check response, and 43,113 bytes in the sealed envelope. Receipt: [transaction-20260929-062735-001.yaml](../../../operations/transactions/transaction-20260929-062735-001.yaml).

## Why this is a complaint

Rechecking dossier freshness and refusing silent invalidation are valuable safeguards. Requiring the operator to reconstruct and transmit every unchanged assessment adds error surface and context cost without a corresponding review gain for this specific screened, evidence-free route. A deep-reviewed route or one cited in comparisons would need a substantive reviewed replacement.

## Smallest improvement to investigate

In `source.record.revise`, detect the narrow case where every changed route is screened and has no checksum-bearing evidence, analysis reference, or comparison. Show the old and new material checksums in the reviewed diff, then copy the existing dossier and update only its basis inside the guarded transaction. Preserve the current full replacement requirement for every other case. Test the Grinstead-shaped case and a deep-reviewed counterexample; keep the source/unit revision guards, byte/manifest checks, validation, and receipt.

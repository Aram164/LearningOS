# Generated-input validator rejects ordinary interrupt terminology

Observed 2026-10-23 while creating the initial BS setup through `note.analysis.save_batch`; Core HEAD `1d80aa03e674131a67bda37db04fce2d8076c62a` with unrelated dirty work preserved.

## Expected and observed

A source-grounded reference note used the English phrase “software generated” immediately followed by “/programmed interrupt” to distinguish two labels in the older BS slides. This is prose, not a repository path or dependency. The gateway refused with `VALIDATION_FAILED` and `E GEN-INPUT: canonical file depends on a generated artifact`, naming `knowledge/notes/systems/note-bs-os-basics-reference.md`.

The refused request was `request-reviewed-98c5525bbfc54204ade19b963e714cfb`, idempotency key `reviewed-f05ec67baf0848f88b8f8fb85c722539`; transaction and receipt were null. No note committed. The source of the classification is `_GENERATED_REF_RE` / `_references_generated` in `tools/learning_os/derive/validation/registries.py`. It matches the slash-separated prose fragment because it contains the directory word followed by slash and a letter. The actual input body contained no dependency on a derived artifact.

## Reproduction and bounded proof

Join the strings “software generated” and “/programmed interrupt” with no separator, then pass that body to `_references_generated`. The verified result is true; rephrased prose returns false, while a real local manifest path remains true. Place it in an otherwise valid new reference-analysis body and the gateway refuses as above. Rephrasing to “software generated interrupt beziehungsweise programmed interrupt” preserves the content and avoids the false classification.

Evidence is retained in the rejected envelope/body under `/private/tmp/bs-setup-main/` for this session. The final adopted note uses the unambiguous phrasing. This was a new-note experiment, not evidence about existing note corruption or lost writes.

## Smallest improvement and acceptance

Investigate recognizing actual local path references rather than every slash-separated occurrence of the directory word. Retain rejection of genuine derived-file inputs. Add one negative regression for this ordinary prose phrase and positive regressions for real paths in supported link/path forms. Do not weaken the generated-input ownership boundary or change canonical source content silently.

## Issue

Published after Aram directly approved the sanitized public report: https://github.com/Aram164/LearningOS/issues/11 (open). Duplicate search found only related closed issue #4. The GitHub connector returned 403; authenticated repository tooling published the exact approved sanitized body. Private paths, request identities and full local evidence stayed local.

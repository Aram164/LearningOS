# Focused discovery omits invocation details needed during material retrieval

Task: Sol cited-material compare on arena e20e8436b08bb5d46e3415b1ce2cba5e6e711df4, macOS/Python 3.14.4. x-compare-01 needed 25 command executions and 56,958 fresh input tokens, including five syntax/path refusals and one shell-glob recovery before a correct cited answer. Recorded errors include missing unit context for related material, three rejected PDF page forms, and a direct PDF path rooted in the checkout instead of its material sibling. The shell-glob error is separate from parser behavior. Separately, all three c-compare baselines tried unsupported material-context --query, received the positional-query usage refusal, and recovered. No canonical change or bypass occurred.

The focused capabilities material-span --json read on the repair tree identifies the operation, invariants and task, but gives no parser argument syntax. Owners inspected: tools/learning_os/app/handlers/reads.py::capabilities, tools/learning_os/store/contracts/verb_catalogue.py, and adapters' parser layer. Safety validation and bounded material reads are useful and must remain.

Investigate parser-derived minimal usage and conditional argument requirements through the existing focused capability read. Keep examples executable against the actual parser, avoid copied handwritten syntax or prompt matching, and preserve exact target/scope and material bounds. Freeze the failed commands as regression/recovery cases, then use a new preregistered retrieval comparison to measure refusal/command/token counts and correct cited locators. ASSUMPTION: richer focused discovery would reduce these errors; this campaign measures friction, not the effectiveness of the proposed remedy.

Proof retained externally: LearningOS/workbench/gemini-arena-2026-11-01/results-x/x-compare-01, evidence/material-span-capability.json, OBSERVATIONS.md and REPAIR-PLAN.md. This small single-run observation does not establish general parser usability or model superiority.

Issue: https://github.com/Aram164/LearningOS/issues/89

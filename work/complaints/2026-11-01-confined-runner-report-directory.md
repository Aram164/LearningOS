# Explicit runner report path conflicts with confined scratch

Task: Gemini/Sol comparison, plain-main compare baseline on Core c61c645d220aa2bbe84855222201936b5170cedb, gpt-6.1-sol/high, macOS, Python 3.14.4. c-compare-01 and c-compare-03 passed an explicit --report-dir beneath the run checkout's gitignored .venv scratch. The runner refused: “full report directory must be outside the selected data root”. Both recovered through direct CLI and completed; all command/token costs are retained.

Observed owner: tools/learning_os/app/agent_reporting.py::ReportStore.__init__. An explicit contained path is rejected, while its default tempfile directory honors TMPDIR in the same contained subtree. The campaign's approved write confinement requires temporary writes to remain there. The guard safely prevents uncontrolled canonical-root report placement, but the explicit/default mismatch adds failed calls without strengthening the actual boundary.

Smallest investigation: define one report-location rule for explicit and default paths; consider only the documented gitignored scratch subtree inside a checkout, with component/symlink checks and refusal before mutation. Keep private full-report, raw journal, checkpoint and digest verification. Prove both forms agree, canonical/symlink escapes refuse without writes, interruption retains evidence, and unavailable storage prevents commit. No implementation is authorized by this complaint alone.

Proof retained externally: LearningOS/workbench/gemini-arena-2026-11-01/results-c/c-compare-01 and c-compare-03 (finals, transcript, evidence, audit), OBSERVATIONS.md and REPAIR-PLAN.md. This is a confined experimental interaction, not a demonstrated failed live learner write. Local evidence is not assumed published with this note.

Issue: https://github.com/Aram164/LearningOS/issues/88

# Exploratory probes

These are the throwaway scripts that *found* the findings, kept because each
one reproduces a claim in `../../reports/FINDINGS.md` on its own, without the
rest of the harness.

| Script | What it establishes |
|---|---|
| `probe_frag.py` | The two resolvers for a `material://…#fragment` reference disagree: the seal-time materials check strips the fragment, the validator does not (F-04). |
| `probe_e1.py` … `probe_e1i.py` | The ladder from "no plan" to "an agent's own stage, installed" — the intermediate steps that produced rungs A–D of F-01. |
| `probe_channel.py` | The approval matrix: `codex`+gesture is refused, `ui`+gesture is admitted, `operator`+operator-approval is admitted (F-01, mechanism). |
| `probe_codex_msg.py` | The exact refusal text a codex-channel gesture gets. |

They are not part of `run-all.sh`; the codified versions live in
`t03_adversarial.py` (cases `e1b` and `g1`).

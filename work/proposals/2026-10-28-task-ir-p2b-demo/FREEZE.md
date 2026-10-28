# P2b demonstration freeze — 2026-10-28 (Gate 1)

Frozen before any live session ran. Any change after this file requires a
recorded protocol amendment and a rerun of affected demonstrations.

| Input | Frozen value |
|---|---|
| Scenario | P2-07 (patch via unique stage discovery), all three arms |
| Core | `/Users/aramaljanadi/Desktop/semestercontext/LearningOS/workbench/task-ir-p1-experiment/repository` at `e895758`; its `tools/` tree is byte-identical on the P2 branch (`git diff e895758 HEAD -- tools/` is empty) |
| UI | Not involved (no UI surface in this scenario) |
| Agent runner | Muse Code `1.4.14`, default model route (no `--model` override), default reasoning effort |
| Session shape | One `muse exec` headless session per arm, own UUID, `--workspace` set to the trial directory |
| Per-session limits | `--max-model-steps 40`; 900 s wall-clock kill; web tools disabled; approval bypassed only inside the disposable `/tmp` fixture (`--yolo`) |
| Fixtures | Built by frozen Core builders (`build_mini_repo` + `material_fixture`) into `/tmp/p2b-demo-{A,B,C}`; all three canonical fingerprints identical: `cd4e16ecdafac337f8b3dcd5af8ac4578d2fd1bef52c9b4650255b145aa6f104`; expected route `route-b2f1f80014860a929a3af0bc` |
| Prompts | `prompt-A.txt`, `prompt-B.txt`, `prompt-C.txt` in this directory; common head and review rule are one shared text, only the interface section differs. SHA-256 per arm recorded in `demo-trials.json` |
| Reviewer policy | Semantic criteria, identical wording in all prompts: target unit and stage route; only `angle` changes, to the exact task value; current snapshot. Check-record bytes are never compared across arms (protocol amendment, 2026-10-28) |
| New angle value | `P2 live demonstration angle` |
| Token accounting | Sum over `model_completed` events in the trial session's own `session.jsonl`, deduplicated by event identity; cache tokens reported as a subset of input, never added |
| Not authorized | The 108-session campaign, any P1 modification, P3 work |

Starting state per arm is recorded in `demo-trials.json` (trial directory,
fixture root, expected route, starting fingerprint, session UUID, prompt
hash). The state oracle from the P2a harness (angle applied, stable route id
materialization, all other route fields preserved, exactly one receipt) is
reused unchanged to judge each demonstration.

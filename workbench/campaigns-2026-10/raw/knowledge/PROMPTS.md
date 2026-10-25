# Prompts to paste into GLM 5.8 Flash

Use one fresh chat per prompt. Start only after STATUS.md says READY.
Aram pastes these; Codex verifies the results after all four reports exist.
Start each chat in /Users/aramaljanadi/Desktop/semestercontext/.
The packet is LearningOS/workbench/glm-knowledge-campaign/ relative to that folder.

## 1. K2 — real navigation, fresh operator chat

Read LearningOS/workbench/glm-knowledge-campaign/STATUS.md, then K2-COLDSTART.md only. If status is not READY, stop without running the campaign. Complete the cold-start phase and write K2/COLDSTART.md before opening CAMPAIGNS.md or implementation code. Then read CAMPAIGNS.md: the Ground rules and K2 only, and complete the scripted journeys on the pinned base. Use the system's public reads and preserve exact commands and outputs. Use a private local clone, never push it. Missing authored connections or evidence are counts, not bugs; never infer concepts, relations or tags. Write K2/REPORT.md, checkpoint as you go, and finish with signals/K2.done containing K2/REPORT.md. Report untested scope explicitly. Stop after K2.

## 2. K3 — UI projection, separate developer chat

Read LearningOS/workbench/glm-knowledge-campaign/STATUS.md and CAMPAIGNS.md: the Ground rules and K3 only. If status is not READY, stop without running the campaign. Do K3 on the pinned base with fixture data and focused node tests. Read the UI's CLAUDE.md, README.md and ARCHITECTURE.md, plus Core's DEVELOPER.md for its producer boundary. Keep every proposed bug tied to a failing test and its owning contract. Treat modules the loader cannot exercise as coverage gaps. Do not open the learner's vault, fix production code, push, or launch another chat. Write K3/REPORT.md and its reproductions, checkpoint as you go, and finish with signals/K3.done containing K3/REPORT.md. Stop after K3.

## 3. K1 — Core projections, fresh chat after K2

Read LearningOS/workbench/glm-knowledge-campaign/STATUS.md and CAMPAIGNS.md: the Ground rules and K1 only. If status is not READY, stop without running the campaign. Do K1 on the pinned base. Follow the developer route and read the existing focused tests before adding probes. Use synthetic fixtures and one pytest process at a time. Every proposed bug needs a test that fails on the base for the stated reason; preserve command output. Never infer or propose concept connections, fix production code, push, or launch another chat. Write K1/REPORT.md and reproductions, checkpoint as you go, and finish with signals/K1.done containing K1/REPORT.md. Stop after K1.

## 4. K4 — governed authoring, fresh chat after K1

Read LearningOS/workbench/glm-knowledge-campaign/STATUS.md and CAMPAIGNS.md: the Ground rules and K4 only. If status is not READY, stop without running the campaign. Do K4 on the pinned base through the real V2 gateway in a disposable fixture repository. Skip C1-C cases already marked probed; attack the read-only-reviewed cases specified for K4. One pytest process at a time. Every proposed bug needs a failing test, exact output, contract basis and source location. Do not change live learner records, fix production code, push, or launch another chat. Write K4/REPORT.md and reproductions, checkpoint as you go, and finish with signals/K4.done containing K4/REPORT.md. Stop after K4.

## Returning for verification

Once K1/REPORT.md, K2/REPORT.md, K3/REPORT.md and K4/REPORT.md exist,
tell Codex: "The Atlas campaign is done. Verify all four reports in
LearningOS/workbench/glm-knowledge-campaign/. Re-run the reproductions,
try to refute each diagnosis, and separate confirmed defects from missing
authored content and coverage gaps. Do not fix anything yet."

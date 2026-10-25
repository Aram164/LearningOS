# K2 phase A: operator navigation before the scripted audit

Do this phase before opening CAMPAIGNS.md or implementation/test code.
Read STATUS.md first; stop if it is not READY. Follow the operator reading
route in the assigned LearningOS repository. This phase supplies questions,
not a command sequence. Do not parse canonical YAML to answer them.

Use a private full clone of the live Core with `--no-hardlinks`, at
`/Users/aramaljanadi/los-glm-K2-2026-10/repository`. Use the code/docs revision
and learner-data snapshot specified in STATUS.md. Never push this clone.
Its sibling `materials` link must resolve to the real LearningOS materials
tree, read-only for this task. Do not overwrite an existing clone or link.
Create the clone's own Python 3.14 `.venv` and install the editable development
dependencies (`.venv/bin/python -m pip install -e '.[dev]'`). Do not run
`make setup` or `make hooks`, reuse the live venv, or alter the live checkout.
Environment setup is allowed before the navigation phase; record setup failures
separately from navigation failures.

Answer these through public system reads, choosing real IDs from those reads:

1. From a recorded study context, find a concept's prerequisites and one
   existing explanation. Show the supporting stage, concept and note IDs.
2. For an explicitly authored concept connection, show what row records it
   and what linked evidence is actually available.
3. Use a German alias published by the system to reach its concept. If an
   alias cannot be discovered through the read surface, report that limit.
4. Find a saved question and check that its target exists. Report an honest
   absence if the chosen scope has no saved question.
5. Follow an existing learning-material connection to an exact local page,
   preserving the source identity and the resolved locator.

For each question record the selected IDs, commands in order, wrong turns,
files read, result and bounded supporting output. Mark unsupported conclusions
ASSUMPTION. Distinguish no authored connection, no linked evidence and a saved
question. Never invent a connection or classify missing content as a bug.

Write `K2/COLDSTART.md` under this campaign, including any protocol deviation
(such as opening the later scripted spec early). Do not repair data or code.
Then read CAMPAIGNS.md's Ground rules and K2, and complete phase B's scripted
journeys in the same private clone. The final K2 report references both phases.

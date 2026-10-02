# Remote video examination: prove the benefit before adding a tool

**Observed:** 2026-09-28, while reviewing a proposed Gemini API pipeline for non-local video materials. No live Gemini API examination was run during this review.

## Where the friction appeared

The [video intake workflow](../../../system/WORKFLOWS.md) keeps videos as URLs and calls for Gemini Notebook examination only when a video is selected for study, followed by verification against the exact video and timestamps. The existing caption importer (`tools/ingest_transcript.py`) can make YouTube captions addressable, but a video with no caption track yields no transcript. The current [Analysis route](../../../curriculum/modules/module-hu-m2-statistik-analysis/source-map.yaml) labels video `1xsIpCa961w` as captionless and title-only; that label is recorded plan state, not a fresh check of video availability or content.

The proposed API command would address one public YouTube video at a time and might recover spoken and visual mathematical steps. Its benefit is still unmeasured. It would also add a command, tests, tool registration, and an external API dependency to operate. More importantly, a model-produced draft would not become source-bound durable evidence: analysis bindings in `tools/learning_os/commands/analysis.py` require registered local bytes, and remote route checksums in `tools/learning_os/materials_resolution.py` cover route metadata rather than current video content.

## Why this is a complaint

Building the command before a verified example risks maintaining another tool that does little more than the already prescribed Gemini Notebook workflow. It could make an unverified model summary look like a transcript or imply that a saved draft detects remote video changes. This is a design risk, not an observed failure of the Gemini API.

The existing boundaries provide real safety: remote content is fetched only through an explicit action, timestamp claims require a check against playback, and a URL-only source cannot masquerade as a locally resolved source analysis. Preserve those boundaries.

## Smallest follow-up to investigate

1. When this issue is resumed, confirm that `https://www.youtube.com/watch?v=1xsIpCa961w` is public, is the video named by the route, and remains relevant to the selected study task. Do not substitute another video silently.
2. Examine that one video through Gemini Notebook or a single manual Gemini API request. Keep the response as an unverified draft outside canonical LearningOS records. Do not generate a backlog or force 30-second transcript windows.
3. Open the exact video and check every claim proposed for use, especially proof steps, equations, and timestamps. Record each as verified, corrected, rejected, or still unverified, with the video time.
4. Compare what was verified with what the caption route and existing plan already provided. Record whether the examination recovered useful missing content and how much checking it required.
5. Only if the result is useful enough to repeat, review a bounded single-video command and its maintenance cost. A durable remote-source binding is a separate contract decision; do not infer it from a successful draft.

**Decision state:** Deferred for later examination. This note authorizes no implementation, canonical write, source evaluation, commit, or claim that the remote-video gap is solved.

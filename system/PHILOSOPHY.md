---
id: learning-os-philosophy
type: philosophy
status: draft
version: 1.0
date: 2026-07-16
---

# PHILOSOPHY — Why the Learning OS Exists

## 1. Personal context

I have ADHD and I am studying computer science with the long-term goal of becoming an ML Systems / Data Engineer.

My main difficulty is not a lack of interest.

It is the opposite.

I am highly interested in the subjects I study, and because of that I naturally try to see the whole picture. Technical subjects such as mathematics, statistics, machine learning, databases, compilers, runtimes, and data systems are built from many layers of abstraction. A formula in machine learning may depend on ideas from probability, analysis, optimization, linear algebra, or information theory. A systems concept may depend on compilers, databases, operating systems, or programming-language semantics.

When I encounter one concept, I often immediately see many possible connections and dependencies.

This is one of my strengths.

It is also one of the main reasons studying becomes overwhelming.

---

## 2. The problem I am trying to solve

Traditional study systems assume that learning is mostly linear:

1. read the lecture;
2. read one book;
3. write a summary;
4. solve exercises;
5. prepare for the exam.

That is rarely how I learn.

I often need to see the same concept through several different lenses before it becomes clear. One source may provide intuition. Another may provide the derivation. Another may explain the implementation. A lecture may show what is required for the course, while a book explains where the idea comes from.

I therefore collect:

- books;
- lecture series;
- slides;
- solved exercises;
- videos;
- papers;
- documentation;
- code;
- examples;
- discussions with AI.

This creates a large sea of material.

The more I collect, the harder it becomes to remember:

- what I already found;
- which source was useful;
- which source explained which part;
- where I saved something;
- which notes I already wrote;
- which prerequisite I was missing;
- whether I already worked through a similar question;
- how one topic connects to another.

The result is that much of my cognitive energy is spent reconstructing context instead of learning.

---

## 3. ADHD-related burdens

The system exists to reduce several recurring burdens.

### 3.1 Organizational overload

I am bad at consistently organizing many files, notes, books, links, and screenshots by hand.

Even when I understand something deeply, I may lose the note, forget the path, or save it in an inconsistent place.

The system should take responsibility for:

- naming;
- filing;
- linking;
- metadata;
- source registration;
- duplicate detection;
- retrieval indexes;
- workspace organization.

I should not have to act as my own librarian.

### 3.2 Scope explosion

Because I naturally see dependencies and connections, one topic can quickly expand into many others.

For example, a machine-learning formula may lead into:

- probability;
- likelihood;
- optimization;
- derivatives;
- convexity;
- information theory.

Some of these are necessary now.

Some are useful later.

Some are interesting but distracting.

The system should help distinguish:

- required now;
- helpful now;
- defer;
- reference only.

It should preserve the larger picture without forcing me to study the entire graph at once.

### 3.3 Re-searching

I often search for the same kinds of resources repeatedly.

I may remember that one book or video explained a concept well, but not which one.

The system should remember:

- which sources exist;
- what each source explains well;
- which perspective it provides;
- which sections are useful;
- what level it assumes;
- whether I personally found it helpful.

I should not repeatedly rebuild the same reading list.

### 3.4 Lost notes and weak handwriting

I often write long handwritten notes because writing helps me think.

My handwriting is difficult to read, and paper notes are easy to lose.

The system should preserve the original handwritten images, create faithful Markdown transcriptions, attach useful metadata, and place them in the correct location.

The transcription must preserve my reasoning.

It must not silently replace my thoughts with a generic AI explanation.

### 3.5 Context reconstruction

A major burden is having to reconstruct what I once understood.

A year later, I may encounter a formula or idea and vaguely remember that I already worked through it.

The system should be able to say:

- you already studied this;
- these are your relevant notes;
- this is the file path;
- these were the sources;
- these are the connected concepts;
- this was the question you were trying to answer.

The goal is that I rarely need to remember where something is stored.

### 3.6 Metacognitive uncertainty

It is easy to confuse:

- having seen a concept;
- having read about it;
- having written notes;
- actually understanding it.

For me, understanding means that I can:

1. derive it;
2. explain it clearly;
3. apply it flexibly.

The system should not treat file existence as proof of understanding.

---

## 4. The strengths the system should amplify

The system should not only compensate for weaknesses.

It should amplify the parts of ADHD that are valuable for technical learning.

### 4.1 Connection-making

I naturally connect ideas across subjects.

The system should make those connections durable and retrievable.

A concept from analysis should be linkable to statistics, machine learning, optimization, databases, or runtime systems without being duplicated.

### 4.2 Deep synthesis

My notes are often long because they combine:

- questions;
- explanations;
- derivations;
- examples;
- multiple sources;
- new connections;
- corrections to my earlier thinking.

These notes are not simple summaries.

They are evolving synthesis artifacts.

The system should preserve that richness instead of forcing one note per concept or one rigid template.

### 4.3 Curiosity-driven learning

I often learn by following a gap until the missing piece becomes clear.

The system should support this without letting the process become uncontrolled.

It should help identify the smallest useful next source or prerequisite.

### 4.4 Whole-picture understanding

I learn better when I can see where a concept fits.

The system should preserve both:

- the local scope of what I need now;
- the wider graph of how the idea connects to other knowledge.

---

## 5. The intended role of the system

The system should act primarily as an external organizational and contextual memory.

Its core responsibilities are:

- organize learning sources;
- evaluate sources by pedagogical role;
- build scoped source menus;
- retrieve prior notes;
- identify prerequisites;
- preserve concept connections;
- transcribe handwritten notes;
- attach metadata;
- route files;
- rebuild indexes;
- maintain a clean repository;
- support planning and study sessions.

Teaching is secondary.

Any capable AI can explain a topic.

The special value of this system is that it knows:

- what I have already studied;
- what I wrote;
- which sources helped;
- what I am currently trying to understand;
- how the new question connects to my existing knowledge.

---

## 6. The ideal interaction

The system should eventually support an interaction like this:

> I am learning concept X.

The system responds with:

- what I have already written about X;
- which concepts I should understand first;
- which sources are available;
- what each source does best;
- which source should be primary;
- which source offers a complementary perspective;
- which source should be used only if a specific gap remains.

I begin reading and asking questions.

If one question concerns something I worked through before, the system says:

> You already wrote about this. Read note Y at path Z.

I continue writing my own notes.

When I am finished, I provide handwritten pages or rough text.

The system:

- preserves the originals;
- transcribes them faithfully;
- adds only useful retrieval metadata;
- links the note to relevant concepts and sources;
- places it in the correct canonical location;
- updates generated indexes;
- leaves the meaning under my control.

Later, when I encounter the topic again, the system reconstructs the context automatically.

---

## 7. Ownership boundary

The system should be autonomous about mechanics.

It may handle:

- folder creation;
- filenames;
- IDs;
- metadata normalization;
- routing;
- indexing;
- backlinks;
- source registration;
- transcription;
- validation;
- generated views.

I remain the owner of meaning.

The system must ask before:

- changing my reasoning;
- rewriting a conceptual explanation;
- merging notes;
- deleting canonical knowledge;
- resolving ambiguity in my intended meaning;
- changing an architectural rule.

If it believes I am wrong, it should guide me with questions rather than silently replacing my conclusion.

---

## 8. Notes as living artifacts

My notes are part of building understanding.

They are not merely records created after learning is complete.

A note may:

- begin as rough handwriting;
- grow through several study sessions;
- combine multiple concepts;
- reference several sources;
- contain uncertainty;
- evolve as my understanding changes;
- remain useful across modules and years.

The system should keep notes flexible and extendable.

Metadata should provide retrieval cues only.

It should never force the note to fit a rigid classification.

---

## 9. Sources as teaching objects

A source is not valuable merely because it exists.

The system should remember what transformation the source helps produce.

Examples:

- intuitive first exposure;
- formal derivation;
- visual explanation;
- worked examples;
- implementation perspective;
- reference lookup;
- advanced depth.

The important question is:

> What does this source explain well, for whom, at what depth, and through which lens?

The system should personalize this over time based on my feedback.

---

## 10. Timeless design principles

The system should follow these principles:

1. Reduce organizational burden rather than create it.
2. Preserve user-authored meaning.
3. Prefer retrieval over remembering paths.
4. Prefer one canonical artifact over duplication.
5. Use concepts as retrieval anchors, not note containers.
6. Allow notes to contain many concepts.
7. Treat source evaluation as first-class knowledge.
8. Separate temporary work from durable knowledge.
9. Keep raw materials outside the default search space.
10. Generate indexes and reverse links from canonical data.
11. Keep metadata minimal and useful.
12. Let the system scale beyond semesters and university.
13. Preserve context, not just content.
14. Support the whole picture without overwhelming the current scope.
15. Spend computational effort so that the user can spend cognitive effort on understanding.

---

## 11. Mission

The mission of the system is:

> To externalize organization, source selection, prerequisite tracking, and context reconstruction so that I can focus on deriving, explaining, applying, and connecting technical ideas.

A longer formulation is:

> The system should maintain a living external model of what I have studied, what I understood, which sources helped, how concepts connect, and what I am currently trying to learn, so that I do not need to repeatedly remember, re-search, re-organize, or reconstruct context from scratch.

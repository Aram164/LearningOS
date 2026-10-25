'use strict';

/*
 * K3 area 7 — Questions (ADR-017 decision 4), against the pinned UI.
 *
 * A personal question is a `role: question` note with an `atlas_question`
 * block. Its lifecycle (`open` / `resolved`) is carried in the block's own
 * field and is NEVER folded into the note's `state`, which keeps meaning
 * rough/evolving/mature/deprecated. A saved question asserts nothing about
 * mastery; a relation question is not a concept question; and a question whose
 * target is gone keeps its target and shows the missing-target state.
 *
 * On the write side the UI resolves and reopens questions. Its payload carries
 * only the fields the caller names — never wording or target — because Core
 * preserves both (producer boundary: `atlas.question.save` invariants
 * "learner wording and original target are preserved"; new questions require
 * title, text and target and are refused a retarget).
 *
 * Owning contracts: `src/features/atlas/questions.ts` (read),
 * `src/views/atlas-view.ts` `setQuestionState`, `src/gateway-client.ts`
 * `saveAtlasQuestion`, ADR-017 decision 4, capabilities.yaml
 * `atlas.question.save`.
 *
 * Run: node tests/k3-questions.js
 */

const assert = require('node:assert/strict');
const path = require('node:path');
const { createSourceModuleLoader } = require('./source-module-loader');

const root = path.dirname(__dirname);
const notices = [];
class FakeItemView {
  constructor(leaf) { this.leaf = leaf; this.contentEl = {}; }
}
const load = createSourceModuleLoader(root, {
  obsidian: {
    ItemView: FakeItemView,
    Notice: class { constructor(message) { notices.push(message); } },
    Modal: class {},
    setIcon: () => {},
    TFile: class {},
  },
  electron: { webUtils: { getPathForFile: () => '' }, shell: { openExternal: () => {} } },
});

const questionsModule = load('src/features/atlas/questions.ts');
const {
  collectQuestions,
  openQuestions,
  questionDestination,
  questionsForConcept,
  questionsForRelation,
  targetSentence,
} = questionsModule;
const graphModule = load('src/features/atlas/graph.ts');
const { buildAtlasGraph } = graphModule;
const { AtlasView } = load('src/views/atlas-view.ts');

function storeOf({ records = [], relations = [], moduleEdges = [], modules = [] } = {}) {
  const byId = new Map(records.map((record) => [record.id, record]));
  return {
    get: (id) => byId.get(id) ?? null,
    of: (type) => records.filter((record) => record.type === type),
    modules: () => modules,
    moduleConceptEdges: () => moduleEdges,
    relations: () => relations,
  };
}
function concept(id, title) {
  return { id, type: 'concept', title };
}
function relation(from, type, to) {
  return { from, type, to, context: null, source: null };
}

const graph = buildAtlasGraph(storeOf({
  records: [concept('concept-a', 'Alpha'), concept('concept-b', 'Beta')],
  relations: [relation('concept-b', 'requires', 'concept-a')],
}));

/* Question notes. `state` at the top level is the NOTE's lifecycle
 * (rough/evolving/mature/deprecated); the question lifecycle lives only in
 * the atlas_question block. */
const noteRecords = [
  {
    id: 'note-q-concept', type: 'note', title: 'Why does Beta need Alpha?',
    summary: 'The body text of the question.', path: 'knowledge/notes/questions/note-q-concept.md',
    role: 'question',
    state: 'mature', // note lifecycle — NOT the question lifecycle
    atlas_question: {
      state: 'open',
      target: { concepts: ['concept-a', 'concept-b'] },
      answer_notes: ['note-answer-1'],
    },
  },
  {
    id: 'note-q-relation', type: 'note', title: 'Is the Beta–Alpha edge the right cut?',
    summary: '', path: 'knowledge/notes/questions/note-q-relation.md',
    role: 'question',
    atlas_question: {
      state: 'resolved',
      target: { from: 'concept-b', type: 'requires', to: 'concept-a' },
    },
  },
  // A question whose recorded target no longer exists: it keeps its target.
  {
    id: 'note-q-orphan', type: 'note', title: 'What happened to Gamma?',
    summary: '', path: 'knowledge/notes/questions/note-q-orphan.md',
    role: 'question',
    atlas_question: { state: 'open', target: { concepts: ['concept-gamma'] } },
  },
  // Not questions: no block, an unknown block state, and a malformed target.
  { id: 'note-plain', type: 'note', title: 'Plain note' },
  {
    id: 'note-q-unknown-state', type: 'note', title: 'Half a question',
    role: 'question', atlas_question: { state: 'mused', target: { concepts: ['concept-a'] } },
  },
  {
    id: 'note-q-empty-target', type: 'note', title: 'Aiming at nothing',
    role: 'question', atlas_question: { state: 'open', target: {} },
  },
];

const collected = collectQuestions(storeOf({ records: noteRecords }), graph);
assert.deepEqual(
  collected.map((question) => question.noteId),
  ['note-q-orphan', 'note-q-concept', 'note-q-relation'],
  'open questions first, then by title ("What…" < "Why…"); non-questions and malformed rows collect nothing',
);

/* ---------------------------------------------------------------------------
 * The lifecycle is the block's field, never the note's `state`.
 * ------------------------------------------------------------------------ */

const conceptQuestion = collected.find((question) => question.noteId === 'note-q-concept');
assert.equal(conceptQuestion.state, 'open',
  'the note says mature; the question says open — the note state was not folded in');
assert.equal(conceptQuestion.targetPresent, true);

const relationQuestion = collected.find((question) => question.noteId === 'note-q-relation');
assert.equal(relationQuestion.state, 'resolved');
assert.equal(relationQuestion.targetPresent, true,
  'the authored relation b requires a is present, so the relation question reads present');

/* Two notes differing ONLY in note-level `state` collect identically: the
 * question lifecycle cannot be reached through the note field. */
{
  const variants = [
    { ...noteRecords[0], id: 'note-v-a', state: 'rough' },
    { ...noteRecords[0], id: 'note-v-b', state: 'deprecated' },
    { ...noteRecords[0], id: 'note-v-c' },
  ];
  const rows = collectQuestions(storeOf({ records: variants }), graph);
  assert.deepEqual(
    rows.map((question) => [question.noteId, question.state]),
    [['note-v-a', 'open'], ['note-v-b', 'open'], ['note-v-c', 'open']],
  );
}

/* An unknown lifecycle value in the BLOCK is skipped, never guessed. */
assert.ok(!collected.some((question) => question.noteId === 'note-q-unknown-state'));

/* ---------------------------------------------------------------------------
 * Targets: a question keeps what it named, present or gone.
 * ------------------------------------------------------------------------ */

const orphan = collected.find((question) => question.noteId === 'note-q-orphan');
assert.equal(orphan.targetPresent, false,
  'the missing concept is a state to show, not an error and not a retarget');
assert.deepEqual(orphan.target.conceptIds, ['concept-gamma'],
  'the recorded target is kept exactly');

/* A removed relation makes its question's target absent, by identity. */
const afterRemoval = collectQuestions(storeOf({ records: [noteRecords[1]] }), buildAtlasGraph(storeOf({
  records: [concept('concept-a', 'Alpha'), concept('concept-b', 'Beta')],
  relations: [],
})));
assert.equal(afterRemoval[0].targetPresent, false,
  'a question on a removed relation keeps its target and reads missing');

/* ---------------------------------------------------------------------------
 * Scoping: a relation question is not a concept question, and vice versa.
 * ------------------------------------------------------------------------ */

assert.deepEqual(questionsForConcept(collected, 'concept-a').map((question) => question.noteId),
  ['note-q-concept']);
assert.deepEqual(questionsForConcept(collected, 'concept-b').map((question) => question.noteId),
  ['note-q-concept']);
assert.deepEqual(questionsForRelation(collected, 'concept-b--requires--concept-a').map((question) => question.noteId),
  ['note-q-relation']);
assert.deepEqual(questionsForRelation(collected, 'concept-a'), []);
assert.deepEqual(
  questionsForConcept(collected, 'concept-a').filter((question) => question.noteId === 'note-q-relation'),
  [],
  'the relation question never appears as a question about its endpoints',
);
assert.deepEqual(openQuestions(collected).map((question) => question.noteId),
  ['note-q-orphan', 'note-q-concept']);

/* Sentences and destinations. */
assert.equal(targetSentence(graph, conceptQuestion.target), 'Alpha and Beta');
assert.equal(
  targetSentence(graph, relationQuestion.target),
  'Beta requires Alpha',
  'a relation question reads as the authored sentence',
);
assert.equal(questionDestination(conceptQuestion.target), 'concept-a');
assert.equal(questionDestination(relationQuestion.target), 'concept-b');

/* ---------------------------------------------------------------------------
 * The write side: resolving carries only the fields the caller names.
 * ------------------------------------------------------------------------ */

const SNAPSHOT = `sha256:${'4'.repeat(64)}`;

(async () => {
  const calls = [];
  const runLos = (args, callback, stdin) => {
    const envelope = JSON.parse(stdin);
    calls.push({ args, envelope });
    callback(null, JSON.stringify({
      schema_version: 2,
      request_id: envelope.request_id,
      idempotency_key: envelope.idempotency_key,
      capability: envelope.capability,
      ok: true,
      replayed: false,
      transaction_id: 'tx-q',
      receipt_path: 'operations/transactions/tx-q/receipt.json',
      snapshot_after: SNAPSHOT,
      result: {},
      error: null,
    }), '');
  };
  const { GatewayClient } = load('src/gateway-client.ts');
  const gateway = new GatewayClient({ runLos, store: { snapshotId: SNAPSHOT } });
  const view = new AtlasView({}, {
    settings: {},
    store: {
      snapshotId: SNAPSHOT,
      stale: false,
      artifactGuard: (...ids) => Object.fromEntries(ids.filter(Boolean).map((id) => [id, 3])),
    },
    gateway,
    mutate: (action) => action(),
    nav: {},
  });
  view.render = () => {};

  await view.setQuestionState('note-q-concept', 'resolved');

  assert.equal(calls.length, 1);
  const envelope = calls[0].envelope;
  assert.equal(envelope.capability, 'atlas.question.save');
  assert.deepEqual(
    envelope.payload,
    { question: { id: 'note-q-concept', state: 'resolved' } },
    'resolving names the note and the new lifecycle state, and nothing else — Core preserves the wording and the target',
  );
  assert.deepEqual(envelope.expected_revisions, { 'note-q-concept': 3 },
    'the write is guarded against the question note itself');

  /* The passthrough carries a full creation payload untouched — concepts or a
   * relation tuple — so a creation affordance (or the CLI path sharing this
   * client) reaches Core exactly as authored. Writes are serialized, as the
   * app serializes them. */
  const conceptCreation = {
    id: 'note-q-new', title: 'Does Alpha motivate Beta?', text: 'Why?',
    target: { concepts: ['concept-a', 'concept-b'] },
  };
  await gateway.saveAtlasQuestion(conceptCreation);
  const relationCreation = {
    id: 'note-q-rel-new', title: 'Is this cut right?', text: 'Explain.',
    target: { from: 'concept-b', type: 'requires', to: 'concept-a' },
  };
  await gateway.saveAtlasQuestion(relationCreation);

  const [conceptEnvelope, relationEnvelope] = calls.slice(1).map((call) => call.envelope);
  assert.equal(conceptEnvelope.capability, 'atlas.question.save');
  assert.deepEqual(conceptEnvelope.payload, { question: conceptCreation });
  assert.deepEqual(relationEnvelope.payload, { question: relationCreation });

  console.log('K3 questions OK: lifecycle lives in the block, targets are kept, resolution rewrites nothing it was not given.');
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

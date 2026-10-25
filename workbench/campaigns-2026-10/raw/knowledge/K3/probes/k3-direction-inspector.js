'use strict';

/*
 * K3 area 4 — Direction (ADR-016 decision 3), against the pinned UI.
 *
 * Every visible strict arrow points prerequisite → dependent, and the
 * inspector carries both readings of the one authored row: the canonical
 * sentence (subject, verb, object — as authored) and the study-order sentence
 * (prerequisite first). Neither direction is inferred; the semantic layer
 * keeps the authored direction and states no order at all.
 *
 * Owning contracts: `src/features/atlas/graph.ts` (toEdge, sentences),
 * `src/features/atlas/narrative.ts` (relationSentences — the single source
 * the outline rows and inspector connection rows both render), ADR-016
 * decision 3.
 *
 * Run: node tests/k3-direction-inspector.js
 */

const assert = require('node:assert/strict');
const path = require('node:path');
const { createSourceModuleLoader } = require('./source-module-loader');

const root = path.dirname(__dirname);
const load = createSourceModuleLoader(root);
const graphModule = load('src/features/atlas/graph.ts');
const {
  buildAtlasGraph,
  canonicalSentence,
  studyOrderSentence,
  relationPhrase,
  strictPath,
  neighbourhood,
} = graphModule;
const { relationSentences } = load('src/features/atlas/narrative.ts');

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

function relation(from, type, to, context = null, source = null) {
  return { from, type, to, context, source };
}

/* A corpus with every strict type, every direction an author might write, and
 * a semantic edge whose authored direction would be convenient to reverse. */
const records = [
  concept('concept-prereq', 'Conditional probability'),
  concept('concept-dep', 'Logistic regression'),
  concept('concept-other-dep', 'Gradient descent'),
  concept('concept-base', 'Derivative'),
  concept('concept-semantic-a', 'Attention'),
  concept('concept-semantic-b', 'Softmax'),
];
const relations = [
  relation('concept-dep', 'requires', 'concept-prereq', 'the update step is a derivative'),
  relation('concept-other-dep', 'builds-on', 'concept-base', null),
  relation('concept-semantic-a', 'derives', 'concept-semantic-b', null),
  relation('concept-semantic-a', 'inspires', 'concept-prereq', null),
];
const graph = buildAtlasGraph(storeOf({ records, relations }));

/* ---------------------------------------------------------------------------
 * The arrow: on the strict layer, authoring reads subject → object and study
 * order runs the other way. One authored row, both renderings, no third value.
 * ------------------------------------------------------------------------ */

for (const edge of graph.edges) {
  if (edge.layer !== 'strict') continue;
  assert.equal(edge.prerequisiteId, edge.to,
    `${edge.id}: the authored object is the prerequisite`);
  assert.equal(edge.dependentId, edge.from,
    `${edge.id}: the authored subject is the dependent`);
  assert.equal(edge.studyFrom, edge.prerequisiteId,
    `${edge.id}: the arrow tail is the prerequisite`);
  assert.equal(edge.studyTo, edge.dependentId,
    `${edge.id}: the arrow head is the dependent`);
  assert.notEqual(edge.studyFrom, edge.studyTo);
}

/* And the placement agrees with the arrow: prerequisites are drawn left of the
 * focus, dependents right of it, in the same columns the arrows point
 * through. */
const focusDep = neighbourhood(graph, 'concept-dep');
assert.deepEqual(
  focusDep.nodes.map((node) => [node.concept.id, node.column]),
  [['concept-prereq', -1], ['concept-dep', 0]],
  'the prerequisite sits left of the focus, where the arrow tail is',
);
const focusPrereq = neighbourhood(graph, 'concept-prereq');
assert.deepEqual(
  focusPrereq.nodes.map((node) => [node.concept.id, node.column]),
  [['concept-prereq', 0], ['concept-dep', 1]],
  'the dependent sits right of the focus, where the arrow head is',
);

/* The derived path orders along the same arrows: every path edge goes from an
 * earlier layer to a later one. */
const derivedPath = strictPath(graph, 'concept-other-dep');
assert.equal(derivedPath.ok, true);
const layerOf = new Map();
derivedPath.layers.forEach((layer, index) => {
  for (const row of layer) layerOf.set(row.id, index);
});
for (const edge of derivedPath.edges) {
  assert.ok(layerOf.get(edge.studyFrom) < layerOf.get(edge.studyTo),
    `${edge.id}: the path walks tail to head, prerequisite first`);
}

/* ---------------------------------------------------------------------------
 * The two sentences, on one row.
 * ------------------------------------------------------------------------ */

const strictEdge = graph.relationByIdentity.get('concept-dep--requires--concept-prereq');

/* The canonical sentence is the authored claim, subject to object. */
assert.equal(
  canonicalSentence(graph, strictEdge),
  'Logistic regression requires Conditional probability',
);
/* The study sentence is the same row, read the other way. */
assert.equal(
  studyOrderSentence(graph, strictEdge),
  'Learn Conditional probability before Logistic regression',
);
/* The inspector row carries BOTH, in order, each terminated. */
assert.deepEqual(
  relationSentences(graph, strictEdge),
  [
    'Logistic regression requires Conditional probability.',
    'Learn Conditional probability before Logistic regression.',
  ],
  'one authored row, two readings, both carried',
);

/* A strict edge without context renders the same two sentences — context is
 * provenance, not part of the claim. (The second strict fixture has none.) */
const bareStrict = graph.relationByIdentity.get('concept-other-dep--builds-on--concept-base');
assert.deepEqual(relationSentences(graph, bareStrict).length, 2);
assert.match(relationSentences(graph, bareStrict)[0], /^Gradient descent builds on Derivative\.$/);
assert.match(relationSentences(graph, bareStrict)[1], /^Learn Derivative before Gradient descent\.$/);
assert.equal(relationPhrase('builds-on'), 'builds on');

/* A semantic relation keeps the authored direction and states no order —
 * reversing it would be the promotion decision 2 forbids. */
const semanticEdge = graph.relationByIdentity.get('concept-semantic-a--derives--concept-semantic-b');
assert.equal(semanticEdge.studyFrom, 'concept-semantic-a',
  'the semantic layer keeps the authored direction because it claims no order');
assert.equal(semanticEdge.prerequisiteId, null);
assert.equal(studyOrderSentence(graph, semanticEdge), null,
  'no study order is invented for a semantic relation');
assert.deepEqual(
  relationSentences(graph, semanticEdge),
  ['Attention derives Softmax.'],
  'one sentence only: the canonical one',
);

/* A relation type outside both vocabularies still renders under the authored
 * word, and still claims no order. */
const unknownEdge = graph.relationByIdentity.get('concept-semantic-a--inspires--concept-prereq');
assert.equal(unknownEdge.layer, 'unrecognized');
assert.equal(relationPhrase('inspires'), 'inspires', 'the authored verb is used as-is');
assert.deepEqual(
  relationSentences(graph, unknownEdge),
  ['Attention inspires Conditional probability.'],
);

/* The reverse authoring is a different row and a different order. If the
 * author writes `prerequisite builds-on dependent`, the arrow and the study
 * sentence follow THAT row — the interface never normalizes an authored
 * claim into the shape it finds more plausible. */
const reversedGraph = buildAtlasGraph(storeOf({
  records: [concept('concept-prereq', 'Conditional probability'), concept('concept-dep', 'Logistic regression')],
  relations: [relation('concept-prereq', 'requires', 'concept-dep')],
}));
const reversed = reversedGraph.relationByIdentity.get('concept-prereq--requires--concept-dep');
assert.equal(reversed.studyFrom, 'concept-dep');
assert.equal(reversed.studyTo, 'concept-prereq');
assert.deepEqual(
  relationSentences(reversedGraph, reversed),
  [
    'Conditional probability requires Logistic regression.',
    'Learn Logistic regression before Conditional probability.',
  ],
  'the interface renders what was authored, in both readings, without swapping ends',
);

console.log('K3 direction OK: strict arrows run prerequisite to dependent, the row carries both sentences, semantic rows claim none.');

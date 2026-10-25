'use strict';

/*
 * K3 areas 2 and 3 — the focused graph (ADR-016 decision 1) and the two
 * relation layers (decision 2), against the pinned UI.
 *
 * Area 2 (decision 1): the Atlas answers a question about one selected
 * concept. Depth 1 by default, deeper is explicit, and whatever a depth bound
 * excludes is counted and named, never silently dropped.
 *
 * Area 3 (decision 2): `requires`/`builds-on` alone order anything; the six
 * semantic types explain, may cycle, and never reorder a path. A type is never
 * promoted between layers.
 *
 * Owning contract: `src/features/atlas/graph.ts` (read model), ADR-016
 * decisions 1 and 2.
 *
 * Run: node tests/k3-focused-graph.js
 */

const assert = require('node:assert/strict');
const path = require('node:path');
const { createSourceModuleLoader } = require('./source-module-loader');

const root = path.dirname(__dirname);
const load = createSourceModuleLoader(root);
const graphModule = load('src/features/atlas/graph.ts');
const {
  SEMANTIC_RELATION_TYPES,
  STRICT_RELATION_TYPES,
  buildAtlasGraph,
  findStrictCycle,
  neighbourhood,
  relationLayer,
  strictPath,
} = graphModule;
const { conceptPlaneSlice } = load('src/features/atlas/presentation.ts');

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

/* ---------------------------------------------------------------------------
 * Area 3 first, on the vocabulary itself: only the strict layer orders.
 * ------------------------------------------------------------------------ */

assert.deepEqual([...STRICT_RELATION_TYPES].sort(), ['builds-on', 'requires']);
assert.deepEqual([...SEMANTIC_RELATION_TYPES].sort(), [
  'applies-in', 'contrasts-with', 'derives', 'equivalent-to', 'generalizes',
  'motivates',
]);

for (const type of STRICT_RELATION_TYPES) {
  assert.equal(relationLayer(type), 'strict', `${type} is strict`);
}
for (const type of SEMANTIC_RELATION_TYPES) {
  assert.equal(relationLayer(type), 'semantic', `${type} is semantic`);
}
// No promotion to make the graph look better connected; unknown stays unknown.
for (const type of ['requires-on', 'needs', 'implies', ' DERIVES', 'Derives']) {
  assert.equal(relationLayer(type), 'unrecognized', `"${type}" is promoted by nothing`);
}

/* The indexes never mix layers. */
const layerCorpus = buildAtlasGraph(storeOf({
  records: ['a', 'b', 'c', 'd', 'e'].map((key) => concept(`concept-${key}`, key.toUpperCase())),
  relations: [
    relation('concept-b', 'requires', 'concept-a'),
    relation('concept-c', 'builds-on', 'concept-b'),
    relation('concept-d', 'derives', 'concept-a'),
    relation('concept-e', 'motivates', 'concept-b'),
    relation('concept-a', 'trumps', 'concept-e'),
  ],
}));
for (const [key, edges] of layerCorpus.prerequisiteEdges) {
  for (const edge of edges) {
    assert.equal(edge.layer, 'strict', `prerequisiteEdges[${key}] carries only strict`);
  }
}
for (const [key, edges] of layerCorpus.dependentEdges) {
  for (const edge of edges) {
    assert.equal(edge.layer, 'strict', `dependentEdges[${key}] carries only strict`);
  }
}
for (const [key, edges] of layerCorpus.semanticEdges) {
  for (const edge of edges) {
    assert.equal(edge.layer, 'semantic', `semanticEdges[${key}] carries only semantic`);
  }
}
for (const [key, edges] of layerCorpus.unrecognizedEdges) {
  for (const edge of edges) {
    assert.equal(edge.layer, 'unrecognized', `unrecognizedEdges[${key}] carries only unknown types`);
  }
}

/* ---------------------------------------------------------------------------
 * Semantic edges never reorder the path lens (decision 2, on strictPath).
 *
 * One chain, twice: bare, and with every semantic type threaded across the
 * layers in the most order-suggesting arrangement available. The derived
 * layers must be identical, edge for edge.
 * ------------------------------------------------------------------------ */

const chainRecords = ['a', 'b', 'c', 'd', 'e'].map((key) => concept(`concept-${key}`, key.toUpperCase()));
const chainStrict = [
  relation('concept-c', 'requires', 'concept-b'),
  relation('concept-b', 'requires', 'concept-a'),
  relation('concept-e', 'builds-on', 'concept-c'),
  relation('concept-e', 'requires', 'concept-d'),
];
const chainSemantic = [
  relation('concept-d', 'derives', 'concept-a'),
  relation('concept-d', 'generalizes', 'concept-b'),
  relation('concept-e', 'contrasts-with', 'concept-a'),
  relation('concept-b', 'equivalent-to', 'concept-d'),
  relation('concept-a', 'applies-in', 'concept-e'),
  relation('concept-d', 'motivates', 'concept-c'),
];

const bare = buildAtlasGraph(storeOf({ records: chainRecords, relations: chainStrict }));
const threaded = buildAtlasGraph(storeOf({
  records: chainRecords, relations: [...chainStrict, ...chainSemantic],
}));

const barePath = strictPath(bare, 'concept-e');
const threadedPath = strictPath(threaded, 'concept-e');
assert.equal(barePath.ok, true);
assert.deepEqual(
  threadedPath.layers.map((layer) => layer.map((row) => row.id)),
  barePath.layers.map((layer) => layer.map((row) => row.id)),
  'six semantic threads across every layer reorder nothing',
);
assert.deepEqual(
  threadedPath.layers.map((layer) => layer.map((row) => row.id)),
  [['concept-a', 'concept-d'], ['concept-b'], ['concept-c'], ['concept-e']],
  'the layers are the strict chain: a and d are roots, e is last',
);
assert.deepEqual(
  threadedPath.edges.map((edge) => edge.id),
  barePath.edges.map((edge) => edge.id),
  'the path carries exactly the authored strict edges, none of the semantic ones',
);
assert.equal(threadedPath.total, barePath.total);
assert.deepEqual(
  strictAncestorsOf(threaded, 'concept-e'),
  strictAncestorsOf(bare, 'concept-e'),
);

function strictAncestorsOf(graph, focusId) {
  return graphModule.strictAncestors(graph, focusId).map((row) => row.id);
}

/* A semantic cycle is valid and blocks nothing. */
const semanticCycle = buildAtlasGraph(storeOf({
  records: [concept('concept-x', 'X'), concept('concept-y', 'Y'), concept('concept-z', 'Z')],
  relations: [
    relation('concept-x', 'contrasts-with', 'concept-y'),
    relation('concept-y', 'contrasts-with', 'concept-z'),
    relation('concept-z', 'contrasts-with', 'concept-x'),
    relation('concept-z', 'requires', 'concept-x'),
  ],
}));
assert.equal(findStrictCycle(semanticCycle), null, 'a semantic cycle is not a strict cycle');
assert.equal(strictPath(semanticCycle, 'concept-z').ok, true);

/* A strict cycle blocks; semantic edges around it change nothing about that. */
const strictCycle = buildAtlasGraph(storeOf({
  records: [concept('concept-x', 'X'), concept('concept-y', 'Y'), concept('concept-z', 'Z')],
  relations: [
    relation('concept-x', 'requires', 'concept-y'),
    relation('concept-y', 'requires', 'concept-z'),
    relation('concept-z', 'requires', 'concept-x'),
  ],
}));
const blocked = strictPath(strictCycle, 'concept-x');
assert.equal(blocked.ok, false);
assert.deepEqual(blocked.cycle, ['concept-x', 'concept-y', 'concept-z', 'concept-x']);

/* ---------------------------------------------------------------------------
 * Area 2 — the focused neighbourhood: depth 1 by default; exclusion counted
 * AND named.
 * ------------------------------------------------------------------------ */

const records = [
  concept('concept-a', 'Alpha'),
  concept('concept-b', 'Beta'),
  concept('concept-c', 'Gamma'),
  concept('concept-d', 'Delta'),
  concept('concept-e', 'Epsilon'),
  concept('concept-f', 'Zeta'),
  concept('concept-ghost', 'Ghost'),
];
// Chain a ← b ← c ← e plus a far sibling d under b, an unrelated f, and a
// ghost endpoint only an unrecognized type reaches.
const relations = [
  relation('concept-b', 'requires', 'concept-a'),
  relation('concept-c', 'requires', 'concept-b'),
  relation('concept-e', 'builds-on', 'concept-c'),
  relation('concept-d', 'requires', 'concept-b'),
  relation('concept-a', 'derives', 'concept-f'),
  relation('concept-a', 'mentions', 'concept-ghost'),
];
const graph = buildAtlasGraph(storeOf({ records, relations }));

/* Depth 1 is the default when the route carries no depth. */
const defaulted = neighbourhood(graph, 'concept-e');
assert.equal(defaulted.depth, 1, 'omitting depth means depth 1');
assert.deepEqual(
  neighbourhood(graph, 'concept-e', { depth: undefined }).depth,
  1,
  'an undefined depth option is also the default',
);

const depth1 = defaulted;
assert.deepEqual(
  depth1.nodes.map((node) => [node.concept.id, node.direction, node.column]),
  [
    ['concept-c', 'prerequisite', -1],
    ['concept-e', 'focus', 0],
  ],
  'at depth 1 the view shows the direct prerequisite and the focus',
);

/* What the bound excludes is named, with identity and label, and counted. */
assert.deepEqual(
  depth1.beyond.prerequisites.map((row) => [row.id, row.label]),
  [['concept-b', 'Beta']],
  'the prerequisite one hop past the bound is named, not counted alone',
);
assert.equal(depth1.beyond.total, depth1.beyond.prerequisites.length
  + depth1.beyond.dependents.length
  + depth1.beyond.semantic.length
  + depth1.beyond.unrecognized.length,
  'the total is the sum of the four named remainders');

/* Raising the bound consumes exactly the named remainder. */
const depth2 = neighbourhood(graph, 'concept-e', { depth: 2 });
assert.deepEqual(
  depth2.nodes.map((node) => [node.concept.id, node.distance]),
  [
    ['concept-b', 2],
    ['concept-c', 1],
    ['concept-e', 0],
  ],
);
assert.deepEqual(
  depth2.beyond.prerequisites.map((row) => row.id),
  ['concept-a'],
  'the bound now names the next hop instead',
);
const depth3 = neighbourhood(graph, 'concept-e', { depth: 3 });
assert.deepEqual(depth3.beyond.prerequisites, [],
  'at depth 3 the chain is exhausted and the remainder is empty and says so');

/* The dependent direction names and then consumes the same way. */
const fromRoot = neighbourhood(graph, 'concept-a');
assert.deepEqual(fromRoot.beyond.dependents.map((row) => row.id), ['concept-d', 'concept-c'],
  'dependents past the bound are named (sorted by label)');
assert.deepEqual(
  neighbourhood(graph, 'concept-a', { depth: 2 }).beyond.dependents.map((row) => row.id),
  ['concept-e'],
);
assert.deepEqual(
  neighbourhood(graph, 'concept-a', { depth: 3 }).beyond.dependents.map((row) => row.id),
  [],
  'depth 3 reaches them all, so the remainder is empty and says so',
);

/* A semantic neighbour the lens does not draw is named too (never dropped). */
assert.deepEqual(fromRoot.beyond.semantic.map((row) => row.id), ['concept-f']);
const semanticLens = neighbourhood(graph, 'concept-a', { includeSemanticNeighbours: true });
assert.deepEqual(
  semanticLens.nodes.filter((node) => node.direction === 'related').map((node) => node.concept.id),
  ['concept-f'],
);
assert.deepEqual(semanticLens.beyond.semantic, []);
/* And the semantic overlay reordered no strict column. */
assert.deepEqual(
  semanticLens.nodes.filter((node) => node.direction !== 'related').map((node) => node.concept.id),
  fromRoot.nodes.map((node) => node.concept.id),
  'turning the semantic layer on adds a band, it does not re-lane the strict graph',
);

/* An unrecognized type reaches the ghost; it is named, never drawn or walked. */
assert.deepEqual(fromRoot.beyond.unrecognized.map((row) => row.id), ['concept-ghost']);
const unrecognizedView = neighbourhood(graph, 'concept-a', { depth: 3 });
assert.deepEqual(
  unrecognizedView.nodes.map((node) => node.concept.id).sort(),
  ['concept-a', 'concept-b', 'concept-c', 'concept-d', 'concept-e'],
  'no depth bound ever pulls an unrecognized (or semantic) neighbour onto the graph',
);
assert.deepEqual(
  unrecognizedView.beyond.unrecognized.map((row) => row.id),
  ['concept-ghost'],
  'the unreachable neighbour is still named at every depth',
);
assert.equal(
  unrecognizedView.unrecognizedEdges.length,
  0,
  'an unrecognized edge both of whose ends are placed is still not drawn as a relation',
);

/* ---------------------------------------------------------------------------
 * The crowded-plane slice keeps the named remainder named (decision 1 applied
 * to presentation): omitting from the picture is not dropping from the view.
 * ------------------------------------------------------------------------ */

const hubRecords = [
  concept('concept-hub', 'Hub'),
  ...Array.from({ length: 40 }, (_, i) => concept(`concept-spoke-${String(i).padStart(2, '0')}`, `S${i}`)),
];
const hubGraph = buildAtlasGraph(storeOf({
  records: hubRecords,
  relations: hubRecords.slice(1).map((row) => relation('concept-hub', 'requires', row.id)),
}));
const hubView = neighbourhood(hubGraph, 'concept-hub');
const slice = conceptPlaneSlice(hubView);
assert.equal(slice.nodes.length + slice.omitted.length, hubView.nodes.length,
  'every concept is either drawn or in the named remainder — none vanish');
assert.ok(slice.omitted.length >= 35, 'the crowded plane bounds the picture');
assert.deepEqual(hubView.strictEdges.length, 40,
  'the text scope (strictEdges) is unshortened: the outline keeps all 40');
for (const node of slice.omitted) {
  assert.ok(node.concept.id && node.concept.label,
    'an omitted node is a full named concept, not a count');
}

/* Depth and lens junk at the read-model boundary is guarded upstream by the
 * route contract; the read model itself still refuses to throw on a junk
 * focus. */
const junkFocus = neighbourhood(graph, 'concept-not-in-registry');
assert.equal(junkFocus.focus.id, 'concept-not-in-registry');
assert.deepEqual(junkFocus.nodes.map((node) => node.concept.id), ['concept-not-in-registry']);

console.log('K3 focused graph OK: depth 1 default, remainders named and consumed, strict alone orders, semantic cycles pass.');

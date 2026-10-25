'use strict';

/*
 * K3 area 5 — Modules are lenses and evidence, never an axis (ADR-016
 * decision 5, restating ADR-015 decision 2 on this surface), against the
 * pinned UI.
 *
 * A module chip says where a concept is taught and opens the exact stage or
 * knowledge-node evidence that licenses the claim. No edge is ever derived
 * from shared module membership.
 *
 * Owning contract: `src/features/atlas/graph.ts` (modulesFor, evidenceFor,
 * bridges, and every edge index), ADR-016 decision 5.
 *
 * Run: node tests/k3-module-lenses.js
 */

const assert = require('node:assert/strict');
const path = require('node:path');
const { createSourceModuleLoader } = require('./source-module-loader');

const root = path.dirname(__dirname);
const load = createSourceModuleLoader(root);
const graphModule = load('src/features/atlas/graph.ts');
const {
  bridges,
  buildAtlasGraph,
  evidenceFor,
  moduleConceptKey,
  modulesFor,
} = graphModule;

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

/* A concept taught in two modules (the bridge), a concept taught in one, and
 * a module whose only edge is unevidenced — refused upstream and refused
 * here, because an unevidenced edge licenses no chip. */
const records = [
  concept('concept-shared', 'Shared concept'),
  concept('concept-solo', 'Solo concept'),
  concept('concept-b', 'Beta concept'),
];
const modules = [
  { id: 'module-zeta', type: 'module', title: 'Zeta course', is_actionable: false },
  { id: 'module-aml', type: 'module', title: 'Advanced Machine Learning', is_actionable: true },
  { id: 'module-quiet', type: 'module', title: 'Quiet module', is_actionable: false },
];
const knowledgeEvidence = [{ kind: 'knowledge-node', unit_id: 'unit-aml-11', node_id: 'node-shared' }];
const stageEvidence = [{
  kind: 'stage-concept',
  unit_id: 'unit-zeta-02',
  study_map_id: 'map-zeta-02',
  stage_id: 'stage-zeta-02-1',
}];
const moduleEdges = [
  { module_id: 'module-aml', concept_id: 'concept-shared', evidence: knowledgeEvidence },
  { module_id: 'module-zeta', concept_id: 'concept-shared', evidence: stageEvidence },
  { module_id: 'module-zeta', concept_id: 'concept-solo', evidence: [stageEvidence] },
  { module_id: 'module-aml', concept_id: 'concept-solo', evidence: knowledgeEvidence },
  { module_id: 'module-quiet', concept_id: 'concept-shared', evidence: [] },
];
/* Authored relations only ever involve the concepts — nothing from modules. */
const relations = [
  relation('concept-solo', 'requires', 'concept-shared'),
];
const graph = buildAtlasGraph(storeOf({ records, relations, moduleEdges, modules }));

/* ---------------------------------------------------------------------------
 * The chip's list: only evidenced modules, actionable first, then by label.
 * ------------------------------------------------------------------------ */

assert.deepEqual(
  modulesFor(graph, 'concept-shared').map((module) => module.id),
  ['module-aml', 'module-zeta'],
  'the actionable module sorts before the label-sorted rest; the unevidenced one never appears',
);
assert.deepEqual(
  modulesFor(graph, 'concept-solo').map((module) => module.id),
  ['module-aml', 'module-zeta'],
);
assert.deepEqual(modulesFor(graph, 'concept-b'), [],
  'a concept no module evidences has no chips');
assert.deepEqual(
  graph.modules.map((module) => module.id),
  ['module-aml', 'module-quiet', 'module-zeta'],
  'the module list itself keeps every module, actionable first then by label — but listing is not licensing',
);
assert.equal(graph.modules.find((module) => module.id === 'module-quiet').conceptCount, 0);

/* ---------------------------------------------------------------------------
 * The chip's promise: it opens the EXACT evidence that licenses the claim.
 * ------------------------------------------------------------------------ */

assert.deepEqual(evidenceFor(graph, 'module-aml', 'concept-shared'), knowledgeEvidence,
  'a knowledge-node chip opens the reviewed node it names');
assert.deepEqual(evidenceFor(graph, 'module-zeta', 'concept-shared'), stageEvidence,
  'a stage chip opens the exact stage the tag names');
assert.deepEqual(evidenceFor(graph, 'module-quiet', 'concept-shared'), [],
  'an unevidenced edge licenses no evidence and no chip');
assert.deepEqual(evidenceFor(graph, 'module-unknown', 'concept-shared'), []);

/* The evidence index is keyed exactly; nothing leaks between pairs. */
assert.deepEqual(graph.evidenceByModuleConcept.get(moduleConceptKey('module-aml', 'concept-shared')), knowledgeEvidence);
assert.deepEqual(graph.evidenceByModuleConcept.get(moduleConceptKey('module-zeta', 'concept-solo')), [stageEvidence]);

/* ---------------------------------------------------------------------------
 * Never an axis: shared module membership creates no edge of any layer.
 * ------------------------------------------------------------------------ */

/* The only edges on the graph are the authored relation rows. */
assert.deepEqual(
  graph.edges.map((edge) => edge.id),
  ['concept-solo--requires--concept-shared'],
  'one authored row is one edge; module evidence added none',
);

/* Every edge in every per-concept adjacency is an authored row; module
 * membership contributes none. */
const authoredIds = new Set(graph.edges.map((edge) => edge.id));
assert.deepEqual([...authoredIds], ['concept-solo--requires--concept-shared']);
for (const index of [
  graph.prerequisiteEdges, graph.dependentEdges, graph.semanticEdges, graph.unrecognizedEdges,
]) {
  for (const [conceptId, edges] of index) {
    for (const edge of edges) {
      assert.ok(authoredIds.has(edge.id),
        `adjacency[${conceptId}] carries only authored rows`);
    }
  }
}

/* A bridge is shared EVIDENCE, listed with its modules — and it is not a
 * relation between the modules either. */
const bridgeList = bridges(graph);
assert.deepEqual(
  bridgeList.map((bridge) => [bridge.concept.id, bridge.moduleCount]),
  [['concept-shared', 2], ['concept-solo', 2]],
);
for (const bridge of bridgeList) {
  for (const module of bridge.modules) {
    assert.ok(evidenceFor(graph, module.id, bridge.concept.id).length > 0,
      'every module a bridge lists carries its own evidence');
  }
}
/* And the module records themselves are untouched by bridging: no module
 * gains a relation-like field, and no module-to-module record exists. */
assert.deepEqual(Object.keys(graph.modules[0]).sort(), [
  'actionable', 'conceptCount', 'id', 'label', 'shortLabel', 'sortKey',
]);

/* Determinism: reordering the input rows changes no decision. */
const shuffled = buildAtlasGraph(storeOf({
  records: [...records].reverse(),
  relations: [...relations].reverse(),
  moduleEdges: [...moduleEdges].reverse(),
  modules: [...modules].reverse(),
}));
assert.deepEqual(modulesFor(shuffled, 'concept-shared').map((module) => module.id),
  modulesFor(graph, 'concept-shared').map((module) => module.id));
assert.deepEqual(evidenceFor(shuffled, 'module-zeta', 'concept-shared'), stageEvidence);
assert.deepEqual(bridges(shuffled).map((bridge) => bridge.concept.id),
  bridges(graph).map((bridge) => bridge.concept.id));

console.log('K3 module lenses OK: chips carry exact evidence, unevidenced edges license nothing, membership derives no edge.');

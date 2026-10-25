'use strict';

/*
 * K3 area 6 — Authoring (ADR-017 decisions 1 and 3), against the pinned UI.
 *
 * The relation editor must:
 * - build a `concept.relations.change` payload carrying the EXACT old row for
 *   replace and remove (Core matches old rows byte for byte; a projection
 *   null leaking into a row would break that match);
 * - work with no AI provider configured (ADR-017 decision 3 is an acceptance
 *   condition, not a preference);
 * - surface Core's refusals (duplicate, unknown endpoint, cycle) instead of
 *   swallowing them — the refusal keeps the draft on screen with the error
 *   shown against the form.
 *
 * Owning contracts: `src/features/atlas/relation-editor.ts` (rowOf, draftRow,
 * draftRefusal), `src/views/atlas-view.ts` (changeRelations — the one write,
 * refusal surfaced, draft kept), `src/gateway-client.ts`
 * (`changeConceptRelations`), Core `system/contracts/capabilities.yaml`
 * `concept.relations.change` (read-only: 1..50 explicit operations, exact
 * previous rows, atomic refusal on duplicates/unknown endpoints/cycles).
 *
 * Run: node tests/k3-authoring.js
 */

const assert = require('node:assert/strict');
const path = require('node:path');
const { createSourceModuleLoader } = require('./source-module-loader');

const root = path.dirname(__dirname);
const notices = [];
class FakeItemView {
  constructor(leaf) { this.leaf = leaf; this.contentEl = {}; }
}
class FakeNotice {
  constructor(message) { notices.push(message); }
}
const load = createSourceModuleLoader(root, {
  obsidian: {
    ItemView: FakeItemView,
    Notice: FakeNotice,
    Modal: class {},
    setIcon: () => {},
    TFile: class {},
  },
  electron: { webUtils: { getPathForFile: () => '' }, shell: { openExternal: () => {} } },
});

const editorModule = load('src/features/atlas/relation-editor.ts');
const {
  draftRefusal,
  draftRow,
  editDraft,
  newDraft,
  rowOf,
} = editorModule;
const graphModule = load('src/features/atlas/graph.ts');
const { buildAtlasGraph } = graphModule;
const { AtlasView } = load('src/views/atlas-view.ts');

const SNAPSHOT = `sha256:${'3'.repeat(64)}`;
const RELATION_REGISTRY = 'registry-concept-relations'; // as Core names it (atlas-view.ts)

/* ---------------------------------------------------------------------------
 * Fixtures
 * ------------------------------------------------------------------------ */

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

const graph = buildAtlasGraph(storeOf({
  records: [
    concept('concept-a', 'A'), concept('concept-b', 'B'), concept('concept-c', 'C'),
  ],
  relations: [
    relation('concept-a', 'requires', 'concept-b', 'the stored why', 'note-why'),
    relation('concept-b', 'requires', 'concept-c'),
  ],
}));
const documented = graph.relationByIdentity.get('concept-a--requires--concept-b');
const undocumented = graph.relationByIdentity.get('concept-b--requires--concept-c');

/* The gateway stub: captures every envelope, answers with the given outcome. */
function gatewayOf(responseFactory) {
  const calls = [];
  const runLos = (args, callback, stdin) => {
    const envelope = JSON.parse(stdin);
    calls.push({ args, envelope });
    const { failure = null, stdout = '' } = responseFactory(envelope);
    callback(failure, stdout, '');
  };
  const { GatewayClient } = load('src/gateway-client.ts');
  return { gateway: new GatewayClient({ runLos, store: { snapshotId: SNAPSHOT } }), calls };
}

function confirmation(envelope) {
  return JSON.stringify({
    schema_version: 2,
    request_id: envelope.request_id,
    idempotency_key: envelope.idempotency_key,
    capability: envelope.capability,
    ok: true,
    replayed: false,
    transaction_id: 'tx-k3',
    receipt_path: 'operations/transactions/tx-k3/receipt.json',
    snapshot_after: SNAPSHOT,
    result: {},
    error: null,
  });
}

function refusal(envelope, code, message) {
  return {
    failure: Object.assign(new Error('capability refused'), { code: 2 }),
    stdout: JSON.stringify({
      schema_version: 2,
      request_id: envelope.request_id,
      idempotency_key: envelope.idempotency_key,
      capability: envelope.capability,
      ok: false,
      replayed: false,
      transaction_id: null,
      receipt_path: null,
      snapshot_after: null,
      result: {},
      error: { code, message, retryable: false, details: {} },
    }),
  };
}

function viewOf(gateway) {
  // Deliberately NO AI provider configuration anywhere in settings: ADR-017
  // decision 3 makes manual authoring independent of AI, so the write must run
  // with settings that name no provider at all.
  const view = new AtlasView({}, {
    settings: {},
    store: {
      snapshotId: SNAPSHOT,
      stale: false,
      artifactGuard: (id) => ({ [id]: 7 }),
    },
    gateway,
    mutate: (action) => action(),
    nav: {},
  });
  view.render = () => {};
  return view;
}

/* ---------------------------------------------------------------------------
 * The row exactly as Core holds it: projection nulls dropped, never sent.
 * ------------------------------------------------------------------------ */

{
  const row = rowOf(undocumented);
  assert.deepEqual(row, { from: 'concept-b', type: 'requires', to: 'concept-c' });
  assert.deepEqual(Object.keys(row).sort(), ['from', 'to', 'type'],
    'an absent context/source is absent from the row, not an explicit null — Core matches old rows exactly');

  const full = rowOf(documented);
  assert.deepEqual(full, {
    from: 'concept-a', type: 'requires', to: 'concept-b',
    context: 'the stored why', source: 'note-why',
  });
}

/* An edit binds the exact previous row. */
assert.deepEqual(editDraft(documented).original, rowOf(documented));
assert.deepEqual(editDraft(undocumented).original, { from: 'concept-b', type: 'requires', to: 'concept-c' });

/* draftRow trims and drops empties the same way — the new row follows the
 * same discipline as the old one. */
assert.deepEqual(
  draftRow({ ...newDraft('concept-a', 'concept-b'), context: '  ', source: '  ' }),
  { from: 'concept-a', type: 'requires', to: 'concept-b' },
);
assert.deepEqual(
  draftRow({ ...newDraft('concept-a', 'concept-b'), context: ' why ', source: ' note-why ' }),
  { from: 'concept-a', type: 'requires', to: 'concept-b', context: 'why', source: 'note-why' },
);

/* ---------------------------------------------------------------------------
 * The UI-side refusals — the same three Core refuses, said before the write.
 * (Core re-validates; this exists so the answer arrives while the form is up.)
 * ------------------------------------------------------------------------ */

assert.match(draftRefusal(graph, { ...newDraft(), from: '', to: 'concept-a' }), /Choose the concept this claim is about/);
assert.match(draftRefusal(graph, { ...newDraft('concept-a'), from: 'concept-a', to: '' }), /Choose the concept at the other end/);
assert.match(draftRefusal(graph, { ...newDraft('concept-a', 'concept-a'), from: 'concept-a', to: 'concept-a' }), /cannot be connected to itself/);
assert.match(
  draftRefusal(graph, { ...newDraft('concept-a', 'concept-ghost'), from: 'concept-a', to: 'concept-ghost' }),
  /Both ends must be concepts that already exist/,
  'an unknown endpoint is refused before the write',
);
assert.match(
  draftRefusal(graph, { ...newDraft('concept-a', 'concept-b'), from: 'concept-a', to: 'concept-b' }),
  /already authored/,
  'a duplicate identity is refused before the write',
);

/* A strict add that closes a prerequisite loop. Chain b requires c; adding
 * c requires b would loop. */
assert.match(
  draftRefusal(graph, { ...newDraft('concept-c', 'concept-b'), from: 'concept-c', to: 'concept-b' }),
  /loop of prerequisites/,
);

/* An edit that REPLACES one row is evaluated against the graph the replacement
 * produces — reversing the only edge of a two-node chain must not be refused
 * as a loop (2026-09-05 audit, F11), and replacing a row with itself is not a
 * duplicate. */
{
  const reversal = editDraft(undocumented);
  reversal.from = 'concept-c';
  reversal.to = 'concept-b';
  assert.equal(draftRefusal(graph, reversal), null,
    'reversing the only edge of a chain is a legal replace, not a loop');
}

/* But an edit that would still close a loop through OTHER rows is refused. */
const loopGraph = buildAtlasGraph(storeOf({
  records: [concept('concept-x', 'X'), concept('concept-y', 'Y'), concept('concept-z', 'Z')],
  relations: [
    relation('concept-x', 'requires', 'concept-y'),
    relation('concept-y', 'requires', 'concept-z'),
  ],
}));
{
  // Replacing z requires x with z requires y leaves x requires y, y requires z,
  // z requires y — a loop through rows the edit did not touch.
  const closing = { ...newDraft('concept-z', 'concept-y'), from: 'concept-z', to: 'concept-y' };
  assert.match(draftRefusal(loopGraph, closing), /loop of prerequisites/);
}

/* A semantic loop is the author's to make: no cycle refusal off the strict
 * layer (the mirror image of the existing a requires b row). */
{
  const semantic = { ...newDraft('concept-b', 'concept-a'), type: 'contrasts-with', from: 'concept-b', to: 'concept-a' };
  assert.equal(draftRefusal(graph, semantic), null);
}

/* A malformed citation is refused; a well-shaped one is not. (The draft must
 * be otherwise legal: this one adds x requires z to the x→y→z chain, which
 * loops nothing.) */
{
  const base = { ...newDraft('concept-x', 'concept-z'), from: 'concept-x', to: 'concept-z' };
  assert.equal(draftRefusal(loopGraph, base), null, 'the base draft is legal');
  assert.match(draftRefusal(loopGraph, { ...base, source: 'not a note id' }),
    /source must be an existing note or source/);
  assert.equal(draftRefusal(loopGraph, { ...base, source: 'note-why' }), null);
}

/* ---------------------------------------------------------------------------
 * The write: exact operations, exact guard, and the refusal surfaced.
 * ------------------------------------------------------------------------ */

(async () => {
  /* A replace carries the exact old row and the exact new row. */
  {
    const { gateway, calls } = gatewayOf((envelope) => ({ stdout: confirmation(envelope) }));
    const view = viewOf(gateway);
    const operations = [{
      action: 'replace',
      old: { from: 'concept-b', type: 'requires', to: 'concept-c' },
      new: { from: 'concept-c', type: 'requires', to: 'concept-b' },
    }];
    await view.changeRelations(operations);

    assert.equal(calls.length, 1, 'one authored batch is exactly one capability call');
    const envelope = calls[0].envelope;
    assert.equal(envelope.capability, 'concept.relations.change');
    assert.deepEqual(envelope.payload, { change: { operations } },
      'the payload carries exactly the authored operations, old row included, byte for byte');
    assert.deepEqual(envelope.expected_revisions, { [RELATION_REGISTRY]: 7 },
      'the write is guarded against the relation registry artifact, as Core names it');
    assert.equal(envelope.expected_snapshot, SNAPSHOT);
    assert.equal(calls[0].args[0], 'capability', 'the V2 gateway command, not a positional CLI mutation');

    // Confirmed: the editor closes and the new connection is selected.
    assert.equal(view.editor, null);
    assert.equal(view.edgeId, 'concept-c--requires--concept-b');
    assert.equal(view.tab, 'connections');
  }

  /* A remove carries only the exact old row, and removes the selection. */
  {
    const { gateway, calls } = gatewayOf((envelope) => ({ stdout: confirmation(envelope) }));
    const view = viewOf(gateway);
    const operations = [{
      action: 'remove',
      old: { from: 'concept-a', type: 'requires', to: 'concept-b', context: 'the stored why', source: 'note-why' },
    }];
    await view.changeRelations(operations);
    assert.deepEqual(calls[0].envelope.payload, { change: { operations } },
      'the remove names the exact stored row, context and source included');
    assert.equal(view.edgeId, null, 'a removed connection selects nothing');
  }

  /* Core's refusal is surfaced, not swallowed: the draft stays, the error is
   * shown against the form, and the message is Core's own reason. The V2
   * code for a refused registry write is VALIDATION_FAILED (the transaction's
   * validation gate — duplicates, unknown endpoints, cycles); the complaint id
   * (REL-PREREQ-CYCLE) travels inside the message prose. */
  {
    const { gateway, calls } = gatewayOf((envelope) =>
      refusal(envelope, 'VALIDATION_FAILED', 'prerequisite cycle: concept-a -> concept-b -> concept-c -> concept-a'));
    const view = viewOf(gateway);
    view.editor = editDraft(undocumented);
    const operations = [{ action: 'add', new: { from: 'concept-c', type: 'requires', to: 'concept-a' } }];

    await assert.doesNotReject(
      () => view.changeRelations(operations),
      'a refusal is a state the author corrects, not an exception',
    );
    assert.notEqual(view.editor, null, 'the draft survives the refusal');
    assert.match(view.editor.error, /prerequisite cycle: concept-a/);
    assert.equal(calls.length, 1, 'exactly one attempt was made');
    assert.equal(view.edgeId, null, 'nothing was selected, because nothing was applied');
    assert.ok(notices.some((message) => message.includes('prerequisite cycle')),
      'the refusal also reaches the user, not only the form');
  }

  /* No AI anywhere in the authoring path: with no provider configured, the
   * batch runs and the only capability it names is the relations change. */
  {
    const { gateway, calls } = gatewayOf((envelope) => ({ stdout: confirmation(envelope) }));
    const view = viewOf(gateway);
    await view.changeRelations([{
      action: 'add',
      new: { from: 'concept-c', type: 'requires', to: 'concept-a', context: 'authored by hand' },
    }]);
    assert.deepEqual(
      calls.map((call) => call.envelope.capability),
      ['concept.relations.change'],
      'one call, no AI capability, no provider consulted',
    );
    assert.deepEqual(calls[0].envelope.payload.change.operations, [{
      action: 'add',
      new: { from: 'concept-c', type: 'requires', to: 'concept-a', context: 'authored by hand' },
    }]);
  }

  console.log('K3 authoring OK: exact old rows travel, no AI is in the path, Core refusals surface onto the kept draft.');
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

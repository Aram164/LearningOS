'use strict';

/*
 * K3 area 1 — Route state (ADR-016 decision 8), against the pinned UI.
 *
 * The route is `{ name: "atlas", concept?, module?, lens?, depth? }` and one
 * `lens` field carries every lens value. A stale deep link or a hand-edited
 * workspace file must fall back to the default rather than failing to open the
 * Atlas, and it must never throw.
 *
 * Owning contracts:
 * - `src/contracts/route-v1.ts` — `asAtlasLens` / `asAtlasDepth`, the sanctioned
 *   loose-to-strict crossing;
 * - `src/views/atlas-view.ts` `adopt()` — the consumer the route crosses into;
 * - ADR-016 decision 8 (unknown values fall back; one lens field).
 *
 * Run: node tests/k3-route-state.js
 */

const assert = require('node:assert/strict');
const path = require('node:path');
const { createSourceModuleLoader } = require('./source-module-loader');

const root = path.dirname(__dirname);

// The loader keeps the real import graph; only the Obsidian host is replaced.
// Every value is inert: modules use them inside functions, never at load time,
// except `extends ItemView`, which only needs a constructible class.
class FakeItemView {
  constructor(leaf) {
    this.leaf = leaf;
    this.contentEl = {};
  }
}
class FakeNotice {
  constructor(message) { this.message = message; }
}
const obsidian = {
  ItemView: FakeItemView,
  Notice: FakeNotice,
  Modal: class FakeModal {},
  setIcon: () => {},
  TFile: class FakeTFile {},
};

const load = createSourceModuleLoader(root, {
  obsidian,
  // `src/components.ts` (in the shell's import graph) imports `webUtils` for
  // file drag-out; it is host API used inside functions only.
  electron: { webUtils: { getPathForFile: () => '' }, shell: { openExternal: () => {} } },
});
const {
  asAtlasLens,
  asAtlasDepth,
  isAtlasLens,
  isAtlasDepth,
} = load('src/contracts/route-v1.ts');
const { AtlasView } = load('src/views/atlas-view.ts');

/* ---------------------------------------------------------------------------
 * The lens contract: one field, known values pass, unknown values fall back.
 * ------------------------------------------------------------------------ */

const KNOWN_LENSES = [
  'prerequisites', 'path', 'semantic', 'bridges', 'diagnostics', 'domains',
];
for (const lens of KNOWN_LENSES) {
  assert.equal(asAtlasLens(lens), lens, `lens ${lens} survives the crossing`);
  assert.equal(isAtlasLens(lens), true);
}

const UNKNOWN_LENSES = [
  undefined, null, '', 'PREREQUISITES', 'prerequisite', 'crossing', 'table',
  'graph', 'questions', 'symbol-sentinel', 0, 1, NaN, true, false, ['path'],
  { lens: 'path' }, () => 'path',
];
for (const junk of UNKNOWN_LENSES) {
  assert.equal(
    asAtlasLens(junk),
    'prerequisites',
    `lens ${String(typeof junk)}:${String(junk)} falls back to the default`,
  );
  assert.equal(isAtlasLens(junk), false);
}

/* ---------------------------------------------------------------------------
 * The depth contract: 1 and 2 are the whole domain; junk falls back to 1.
 * ------------------------------------------------------------------------ */

assert.equal(asAtlasDepth(1), 1);
assert.equal(asAtlasDepth(2), 2);
// Persisted state often carries strings; the crossing coerces them.
assert.equal(asAtlasDepth('1'), 1);
assert.equal(asAtlasDepth('2'), 2);

const UNKNOWN_DEPTHS = [
  undefined, null, 0, -1, 3, 99, 1.5, 2.01, NaN, Infinity, '0', '3', 'one',
  '', '2.5', true, [1], { depth: 1 },
];
for (const junk of UNKNOWN_DEPTHS) {
  assert.equal(
    asAtlasDepth(junk),
    1,
    `depth ${String(typeof junk)}:${String(junk)} falls back to 1`,
  );
  assert.equal(isAtlasDepth(junk), false);
}
assert.equal(isAtlasDepth(1), true);
assert.equal(isAtlasDepth(2), true);

/* ---------------------------------------------------------------------------
 * The view adopts route state through the same crossing.
 * ------------------------------------------------------------------------ */

function pluginOf() {
  return {
    settings: { atlasRecentConcepts: [] },
    store: {},
    gateway: {},
    nav: {},
  };
}

function viewOf() {
  const view = new AtlasView({}, pluginOf());
  view.render = () => {}; // render needs a DOM leaf; adopt() does not
  return view;
}

// An empty state opens the default: entry browser, prerequisites lens, depth 1.
{
  const view = viewOf();
  view.setState({});
  assert.deepEqual(view.getState(), {
    concept: null, module: null, lens: 'prerequisites', depth: 1,
  });
}

// A stale deep link: junk lens, junk depth, valid concept. The Atlas opens on
// its default lens and depth instead of failing.
{
  const view = viewOf();
  view.setState({ concept: 'concept-convexity', lens: 'crossing-table', depth: 'seven' });
  assert.deepEqual(view.getState(), {
    concept: 'concept-convexity', module: null, lens: 'prerequisites', depth: 1,
  });
}

// Known non-default values survive adoption.
{
  const view = viewOf();
  view.setState({
    concept: 'concept-convexity', module: 'module-aml', lens: 'diagnostics', depth: 2,
  });
  assert.deepEqual(view.getState(), {
    concept: 'concept-convexity', module: 'module-aml', lens: 'diagnostics', depth: 2,
  });
}

// A string depth from persisted Obsidian state coerces; an out-of-range one
// falls back.
{
  const view = viewOf();
  view.setState({ depth: '2' });
  assert.equal(view.getState().depth, 2);
  view.setState({ depth: '3' });
  assert.equal(view.getState().depth, 1);
}

// Unknown concept and module values are not strings and not null, so the view
// keeps what it had (the default null) instead of adopting garbage — and it
// does not throw.
{
  const view = viewOf();
  view.setState({ concept: 42, module: { id: 'module-aml' } });
  assert.equal(view.getState().concept, null);
  assert.equal(view.getState().module, null);

  view.setState({ concept: 'concept-a' });
  view.setState({ concept: ['concept-a'] });
  assert.equal(view.getState().concept, 'concept-a',
    'a non-string concept keeps the previous selection');
}

// `null` is meaningful: it is the entry browser, and it survives.
{
  const view = viewOf();
  view.setState({ concept: 'concept-a' });
  view.setState({ concept: null });
  assert.equal(view.getState().concept, null);
}

/* ---------------------------------------------------------------------------
 * One lens field, exactly four route fields.
 *
 * ADR-016 decision 8: one `lens` field carries all values even though the
 * shell splits them across two controls, because a second field would make
 * `lens=prerequisites` with `scope=diagnostics` expressible, and it means
 * nothing.
 * ------------------------------------------------------------------------ */

{
  const view = viewOf();
  view.setState({ lens: 'bridges' });
  const state = view.getState();
  assert.deepEqual(
    Object.keys(state).sort(),
    ['concept', 'depth', 'lens', 'module'],
    'the Atlas route state is exactly the four ADR-016 decision 8 fields',
  );
  assert.equal('scope' in state, false,
    'no second lens-ish field exists on the route state');
  assert.equal(state.lens, 'bridges');
}

// The adopted route state on the host is the same object shape the feature
// reads (ports.ts AtlasRouteState) — lens and depth are the coerced contract
// values, never the loose inputs.
{
  const view = viewOf();
  view.setState({ lens: 'semantic', depth: '1' });
  assert.deepEqual(view.state, {
    concept: null, module: null, lens: 'semantic', depth: 1,
  });
}

console.log('K3 route state OK: unknown lens/depth/concept values fall back to the defaults, never throw, and the lens is one field.');

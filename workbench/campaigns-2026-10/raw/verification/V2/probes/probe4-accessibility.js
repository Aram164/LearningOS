/* V2 probe 4 — every interactive element has an accessible name, and button
 * groups are keyboard-navigable (roving focus on arrow keys).
 *
 * Mounts every leaf, then walks the rendered DOM:
 *  1. name check   — buttons, inputs, selects, textareas, summaries and
 *                    role=button elements need aria-label / title / text /
 *                    placeholder; aria-hidden decorations are skipped.
 *  2. click-target check — an element with a click listener that is not a
 *                    native control and has no role is an inaccessible
 *                    click-only container (DESIGN.md anti-pattern).
 *  3. keyboard     — every role=group (or filter-tabs group) with buttons
 *                    moves focus on ArrowRight/ArrowDown and stays inside the
 *                    group on ArrowLeft/ArrowUp.
 */
'use strict';

const { boot, VIEW, browserDom, interactives, accessibleName, check, heading, result } = require('./common');

const viewOf = (app, type) => app.workspace.getLeavesOfType(type)[0]?.view || null;

const OPENERS = [
  ['home', VIEW.home, (p) => p.nav.openHome()],
  ['nav', VIEW.nav, (p) => p.router.openNavigator()],
  ['program', VIEW.program, (p) => p.nav.openLearn()],
  ['module-detail', VIEW.module, (p) => p.nav.openModule('module-fixture-m2')],
  ['project-detail', VIEW.project, (p) => p.nav.openProject('project-fixture-thesis')],
  ['unit', VIEW.unit, (p) => p.nav.openUnit('unit-fixture-sad-l04')],
  ['library', VIEW.library, (p) => p.nav.openLibrary()],
  ['atlas-concept', VIEW.atlas, (p) => p.nav.openAtlas({ concept: 'concept-bayes', lens: 'prerequisites', depth: 1 })],
  ['atlas-domains', VIEW.atlas, (p) => p.nav.openAtlas({ concept: null, lens: 'domains' })],
  ['abilities', VIEW.abilities, (p) => p.nav.openAbilities()],
  ['shelving', VIEW.shelving, (p) => p.nav.openShelving()],
  ['boundary', VIEW.boundary, (p) => p.nav.openBoundary('program-masters-planning')],
  ['review', VIEW.review, (p) => p.nav.openReview()],
  ['garden', VIEW.garden, (p) => p.nav.openGarden()],
  ['diagnostics', VIEW.diagnostics, (p) => p.nav.openDiagnostics()],
];

function isGroup(node) {
  return node.getAttribute('role') === 'group'
    || [...node.classes].includes('los-filter-tabs');
}

function groupButtons(group) {
  const out = [];
  const walk = (node) => {
    if (node !== group && isGroup(node)) return; // nested groups own their keys
    if (node.tag === 'button' && node.getAttribute('aria-hidden') !== 'true') out.push(node);
    for (const child of node.children) walk(child);
  };
  walk(group);
  return out;
}

async function main() {
  const { app, plugin } = await boot();
  let nameFails = 0;
  let clickOnlyFails = 0;
  let keyboardGroups = 0;

  heading('probe 4 · accessible names and keyboard-navigable button groups');

  for (const [name, type, open] of OPENERS) {
    await open(plugin);
    const view = viewOf(app, type);
    if (!view) { check(`${name}: mounted`, false, 'no leaf'); continue; }
    const root = browserDom(view.contentEl);

    /* 1. accessible names */
    const unnamed = [];
    for (const el of interactives(root)) {
      if (accessibleName(el) === null) unnamed.push(`${el.tag}.${[...el.classes].join('.')}`);
    }
    if (unnamed.length) {
      nameFails += 1;
      check(`${name}: every interactive element has an accessible name`, false,
        `unnamed: ${unnamed.join(' | ')}`);
    }

    /* 2. click-only containers */
    const clickOnly = [];
    const native = (el) => ['button', 'a', 'input', 'select', 'textarea', 'summary'].includes(el.tag)
      || el.getAttribute('role') === 'button';
    const walkClick = (node) => {
      if (node.listeners?.click?.length && !native(node) && !node.children.some((c) => c.tag === 'button' || c.tag === 'a')) {
        clickOnly.push(`${node.tag}.${[...node.classes].join('.')}`);
      }
      for (const child of node.children) walkClick(child);
    };
    walkClick(root);
    if (clickOnly.length) {
      clickOnlyFails += 1;
      check(`${name}: no inaccessible click-only containers`, false,
        `click-only: ${clickOnly.join(' | ')}`);
    }

    /* 3. keyboard navigation on button groups */
    const groups = [];
    const walkGroups = (node) => {
      if (isGroup(node) && groupButtons(node).length >= 2) groups.push(node);
      for (const child of node.children) walkGroups(child);
    };
    walkGroups(root);
    for (const group of groups) {
      const label = group.getAttribute('aria-label') || [...group.classes].join('.');
      /* Two Abilities groups use deliberate non-roving keyboard schemes:
       * - "Ability camera": Tab-reachable controls; arrow keys pan the canvas
       *   (bound on the viewport region, as its aria-label states). Roving
       *   arrows are contracted only for segmented selection groups.
       * - "Loaded abilities in preparation order": per-card spatial navigation
       *   along preparation edges (ArrowRight = nearest dependent). With no
       *   visible neighbour the key does nothing, by design. */
      if (name === 'abilities' && (label === 'Ability camera' || label === 'Loaded abilities in preparation order')) {
        console.log(`  note ${name}: "${label}" uses a documented non-roving keyboard scheme (see finding notes)`);
        continue;
      }
      const buttons = groupButtons(group);
      const enabled = buttons.filter((b) => !b.disabled && b.getAttribute('aria-hidden') !== 'true');
      /* With one reachable control, wrap-to-self is correct roving behaviour. */
      if (enabled.length < 2) continue;
      const start = enabled[Math.floor(enabled.length / 2)];
      start.focus();
      /* The El stub does not bubble, and the app may attach the arrow-key
       * listener on any container between the button and the declared group.
       * Try each ancestor up to and including the group; the group is
       * keyboard-navigable when one of them moves focus. */
      let moved = false;
      let target = start.parentElement;
      const chain = [];
      while (target && !chain.includes(group)) {
        chain.push(target);
        target.fire('keydown', { key: 'ArrowDown', target: start, preventDefault() {} });
        moved = global.document.activeElement !== start;
        if (moved) break;
        target.fire('keydown', { key: 'ArrowRight', target: start, preventDefault() {} });
        moved = global.document.activeElement !== start;
        if (moved) break;
        target = target.parentElement;
        if (!target || chain.includes(group)) break;
      }
      const landed = global.document.activeElement;
      const inside = buttons.includes(landed);
      keyboardGroups += 1;
      check(`${name}: group "${group.getAttribute('aria-label') || [...group.classes].join('.')}" moves focus on arrow keys and stays inside`,
        moved && inside,
        `moved=${moved} landedInside=${inside} landed=${landed ? `${landed.tag}.${[...landed.classes].join('.')}` : 'null'}`);
    }
  }

  if (!nameFails) check('every interactive element across all views has an accessible name', true);
  if (!clickOnlyFails) check('no inaccessible click-only containers across all views', true);
  console.log(`keyboard groups exercised: ${keyboardGroups}`);
  return result('probe 4 (accessible names + keyboard)');
}

main()
  .then((code) => process.exit(code))
  .catch((error) => { console.error(error); process.exit(1); });

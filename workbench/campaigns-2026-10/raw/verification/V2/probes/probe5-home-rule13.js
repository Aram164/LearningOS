/* V2 probe 5 — Home shape (rule 13, CLAUDE.md) and the no-bare-list rule.
 *
 * Asserts, against the fixture:
 *  - Home renders exactly one Continue card (the resumable focus) naming the
 *    resume pointer's stage, and it carries the ONLY filled (cta) action on
 *    the screen;
 *  - the Today list and the Continue elsewhere list are short (the render
 *    code slices at 4 and 5 rows);
 *  - record references on Home are typed chips or action buttons — no bare
 *    clickable with neither a label-bearing action nor a los-t- type class;
 *  - no primary view (the eight permanent destinations) is a bare list of
 *    links: each must carry static copy (headings/descriptions) outside its
 *    clickable elements.
 */
'use strict';

const { boot, VIEW, check, heading, result } = require('./common');

const viewOf = (app, type) => app.workspace.getLeavesOfType(type)[0]?.view || null;

function find(root, cls) { return root.find(cls); }

function isClickable(node) {
  return node.tag === 'button' || node.tag === 'a'
    || node.getAttribute('role') === 'button';
}

/* Static copy: a text-bearing element that is not itself a control and has no
 * control descendants... — no: a row div containing a strong + button IS copy
 * plus an action. "Bare list of links" means the view offers no non-interactive
 * text at all. Collect any non-control element with direct, non-empty text. */
function staticTextElements(root) {
  const out = [];
  const walk = (node) => {
    if (!isClickable(node) && node.text && String(node.text).trim()) out.push(node);
    for (const child of node.children) walk(child);
  };
  walk(root);
  return out;
}

function countButtons(root) {
  return root.find('los-btn').length;
}

const PRIMARY = [
  ['home', VIEW.home, (p) => p.nav.openHome()],
  ['modules', VIEW.module, (p) => p.nav.openModules()],
  ['learn', VIEW.program, (p) => p.nav.openLearn()],
  ['projects', VIEW.project, (p) => p.nav.openProjects()],
  ['library', VIEW.library, (p) => p.nav.openLibrary()],
  ['atlas', VIEW.atlas, (p) => p.nav.openAtlas({ concept: null, lens: 'prerequisites' })],
  ['garden', VIEW.garden, (p) => p.nav.openGarden()],
  ['review', VIEW.review, (p) => p.nav.openReview()],
];

async function main() {
  const { app, plugin } = await boot();

  heading('probe 5 · Home: one resumable focus, short lists, typed references');
  {
    await plugin.nav.openHome();
    const home = viewOf(app, VIEW.home);
    const root = home.contentEl;

    const continueCards = find(root, 'los-continue');
    check('home shows exactly one Continue card (one resumable focus)', continueCards.length === 1,
      `found ${continueCards.length}`);
    const cardText = continueCards[0] ? continueCards[0].allText() : '';
    check('the Continue card names the resume pointer stage', cardText.includes('Conditional probability and Bayes'),
      `card="${cardText.slice(0, 160)}"`);
    check('the Continue card names its module and unit', cardText.includes('Fixture Statistics & Analysis'),
      `card="${cardText.slice(0, 160)}"`);

    const ctas = find(root, 'los-btn--cta');
    check('exactly one filled (cta) action on Home, on the Continue card', ctas.length === 1
      && continueCards[0].contains(ctas[0]), `cta count=${ctas.length}`);

    const sections = find(root, 'los-section');
    const today = sections.find((s) => s.allText().includes('Today'));
    const elsewhere = sections.find((s) => s.allText().includes('Continue elsewhere'));
    check('home has a Today section and a Continue elsewhere section', Boolean(today && elsewhere),
      `sections=${sections.map((s) => s.allText().slice(0, 20)).join(' / ')}`);
    if (today) {
      const rows = find(today, 'los-home-row');
      check('Today list is short (at most 4 rows)', rows.length <= 4, `rows=${rows.length}`);
    }
    if (elsewhere) {
      const rows = find(elsewhere, 'los-home-row');
      check('Continue elsewhere list is short (at most 5 rows)', rows.length <= 5, `rows=${rows.length}`);
    }

    /* Record references are typed chips or actions: every clickable on Home
     * either carries a visible label (an action) or is a typed chip. A
     * clickable with an icon only and no name would fail probe 4's name sweep;
     * here we additionally require row actions to be real actions. */
    let untyped = 0;
    const walk = (node) => {
      if (isClickable(node)) {
        const labelled = node.allText().trim().length > 0;
        const typed = [...node.classes].some((c) => c.startsWith('los-t-'));
        if (!labelled && !typed) untyped += 1;
      }
      for (const child of node.children) walk(child);
    };
    walk(root);
    check('every record reference on Home is a labelled action or typed chip', untyped === 0,
      `unlabelled clickables=${untyped}`);

    const chips = find(root, 'los-chip');
    const untypedChips = chips.filter((c) => ![...c.classes].some((cls) => cls.startsWith('los-t-')));
    check('every chip anywhere on Home carries its record type class', untypedChips.length === 0,
      `${untypedChips.length} of ${chips.length} chips untyped`);
  }

  heading('probe 5 · rule 13: no primary view is a bare list of links');
  for (const [name, type, open] of PRIMARY) {
    await open(plugin);
    const view = viewOf(app, type);
    if (!view) { check(`${name}: mounted`, false, 'no leaf'); continue; }
    const root = view.contentEl;
    const buttons = countButtons(root);
    const staticText = staticTextElements(root);
    check(`${name}: carries static copy beyond its clickable elements (not a bare link list)`,
      staticText.length > 0, `buttons=${buttons} staticTextElements=${staticText.length}`);
  }

  return result('probe 5 (home shape + rule 13)');
}

main()
  .then((code) => process.exit(code))
  .catch((error) => { console.error(error); process.exit(1); });

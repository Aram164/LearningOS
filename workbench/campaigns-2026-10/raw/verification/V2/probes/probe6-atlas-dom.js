/* V2 probe 6 — the atlas DOM, against the fixture:
 *  1. an orphaned question (target relation not authored) is a non-clickable
 *     row reading "… — no longer authored";
 *  2. the depth remainder is counted on screen ("+ N more …", "beyond depth");
 *  3. the inspector shows BOTH sentences of one strict row;
 *  4. the Domains lens renders.
 */
'use strict';

const { boot, VIEW, waitFor, browserDom, check, heading, result } = require('./common');

const viewOf = (app, type) => app.workspace.getLeavesOfType(type)[0]?.view || null;
const tick = () => new Promise((resolve) => setImmediate(resolve));

async function main() {
  const { app, plugin } = await boot();

  heading('probe 6 · atlas entry: the orphaned question row');
  {
    await plugin.nav.openAtlas({ concept: null, lens: 'prerequisites' });
    const atlas = viewOf(app, VIEW.atlas);
    const root = browserDom(atlas.contentEl);
    const rows = root.find('los-atlas-question-row');
    const orphan = rows.find((row) => row.allText().includes('no longer authored'));
    check('an orphaned question renders a row reading "— no longer authored"', Boolean(orphan),
      `rows=${rows.length}: ${rows.map((r) => r.allText().slice(0, 60)).join(' | ')}`);
    if (orphan) {
      check('the orphaned question names what it was recorded on',
        orphan.allText().includes('Recorded on') && orphan.allText().includes('derives'),
        orphan.allText().slice(0, 200));
      check('the orphaned question is a div, not a button (non-clickable)',
        orphan.tag === 'div' && orphan.classes.has('is-orphaned') && !orphan.listeners.click,
        `tag=${orphan.tag} classes=${[...orphan.classes].join('.')} clickListeners=${(orphan.listeners.click || []).length}`);
    }
    const clickable = rows.filter((row) => row.allText().includes('no longer authored')
      && (row.tag === 'button' || (row.listeners.click || []).length));
    check('no orphaned question row is clickable', clickable.length === 0);
  }

  heading('probe 6 · focused graph: the depth remainder is counted on screen');
  {
    await plugin.nav.openAtlas({ concept: 'concept-bayes', lens: 'prerequisites', depth: 1 });
    const atlas = viewOf(app, VIEW.atlas);
    await waitFor(() => atlas.contentEl.find('los-atlas-remainder').length > 0);
    const root = browserDom(atlas.contentEl);
    const remainders = root.find('los-atlas-remainder');
    check('a depth-remainder card is rendered', remainders.length > 0);
    const remainderText = remainders.map((r) => r.allText()).join(' | ');
    check('the remainder is counted ("+ N more …")', /\+ 1 more (prerequisite|dependent)/.test(remainderText),
      remainderText.slice(0, 200));
    check('the remainder names the depth it lies beyond', remainderText.includes('beyond depth 1'),
      remainderText.slice(0, 200));
    /* Expanding names every counted concept. */
    const toggle = root.find('los-atlas-remainder-toggle')[0];
    toggle.fire('click');
    await tick();
    const expanded = root.find('los-atlas-remainder-item').map((r) => r.allText());
    check('expanding the remainder names the concepts it counted', expanded.length === 1
      && expanded[0] === 'Probability', expanded.join(' | '));
    check('the open remainder states "counted, never dropped"',
      root.find('los-atlas-remainder').map((r) => r.allText()).join(' ').includes('counted, never dropped'));
  }

  heading('probe 6 · inspector: both sentences of one strict row');
  {
    await plugin.nav.openAtlas({ concept: 'concept-bayes', lens: 'prerequisites', depth: 1 });
    const atlas = viewOf(app, VIEW.atlas);
    atlas.inspectEdge('concept-bayes--requires--concept-bedingte-wahrscheinlichkeit');
    await waitFor(() => atlas.contentEl.allText().includes('Selected connection'));
    const root = browserDom(atlas.contentEl);
    const inspector = root.find('los-atlas-connection').find(
      (row) => row.getAttribute('data-relation-id') === 'concept-bayes--requires--concept-bedingte-wahrscheinlichkeit');
    check('the inspector opens the selected strict connection', Boolean(inspector));
    if (inspector) {
      const text = inspector.allText();
      /* relationSentences for a strict edge: canonical + study order. */
      check('the strict row shows the canonical sentence',
        text.includes('Bayes theorem requires Conditional probability.'), text.slice(0, 260));
      check('the strict row also shows the study-order sentence',
        /Conditional probability is (a prerequisite|required before)/.test(text) || text.includes('before Bayes theorem'),
        text.slice(0, 260));
      check('both sentences appear in one row', (text.match(/\./g) || []).length >= 2, text.slice(0, 260));
    }
  }

  heading('probe 6 · the Domains lens renders');
  {
    await plugin.nav.openAtlas({ concept: null, lens: 'domains' });
    const atlas = viewOf(app, VIEW.atlas);
    await waitFor(() => atlas.contentEl.allText().includes('Knowledge domains'));
    const root = browserDom(atlas.contentEl);
    const text = root.allText();
    check('the Domains lens renders its rail and search',
      root.find('los-domain-rail').length > 0 && root.find('los-domain-search').length > 0,
      text.slice(0, 160));
    check('the Domains lens lists domains with counts',
      /Mathematics/.test(text) && /note/.test(text), text.slice(0, 200));
    check('the Domains lens opens a domain detail with notes',
      root.find('los-domain-note-row').length > 0 || root.find('los-domain-notes').length > 0,
      text.slice(0, 200));
    check('the variant switch marks Notes & shelves as active',
      root.find('los-filter-tab').some((t) => t.allText().includes('Notes & shelves')
        && t.getAttribute('aria-pressed') === 'true'));
  }

  return result('probe 6 (atlas DOM)');
}

main()
  .then((code) => process.exit(code))
  .catch((error) => { console.error(error); process.exit(1); });

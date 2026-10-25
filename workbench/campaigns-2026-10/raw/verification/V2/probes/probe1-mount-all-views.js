/* V2 probe 1 — mount every leaf in src/views/ against fixture-vault/.
 * Asserts each of the 14 registered leaves opens and renders real content,
 * including the deep states (module detail, unit with stage, project, library
 * detail, atlas concept, domains lens). One node process, no xdist. */
'use strict';

const { boot, VIEW, waitFor, check, heading, result } = require('./common');

const viewOf = (app, type) => app.workspace.getLeavesOfType(type)[0]?.view || null;

async function main() {
  const { app, plugin } = await boot();

  heading('probe 1 · every registered leaf mounts and renders content');

  const fixtures = {
    home: { open: () => plugin.nav.openHome() },
    nav: { open: () => plugin.router.openNavigator() },
    program: { open: () => plugin.nav.openLearn() },
    module_list: {
      type: VIEW.module,
      open: () => plugin.nav.openModules(),
      expect: 'Fixture', // group list names the fixture modules
    },
    module_detail: {
      type: VIEW.module,
      open: () => plugin.nav.openModule('module-fixture-m2'),
      expect: 'Fixture Statistics & Analysis',
    },
    project_list: { type: VIEW.project, open: () => plugin.nav.openProjects() },
    project_detail: {
      type: VIEW.project,
      open: () => plugin.nav.openProject('project-fixture-thesis'),
      expect: 'Thesis',
    },
    unit: {
      type: VIEW.unit,
      open: () => plugin.nav.openUnit('unit-fixture-sad-l04'),
      expect: 'Conditional probability and Bayes',
    },
    library: { type: VIEW.library, open: () => plugin.nav.openLibrary() },
    library_detail: {
      type: VIEW.library,
      open: () => plugin.nav.openLibraryHome('sources'),
    },
    atlas: {
      type: VIEW.atlas,
      open: () => plugin.nav.openAtlas({ concept: 'concept-bayes', lens: 'prerequisites', depth: 1 }),
      expect: 'Bayes',
    },
    atlas_domains: {
      type: VIEW.atlas,
      open: () => plugin.nav.openAtlas({ concept: null, lens: 'domains' }),
      expect: 'Notes', // Notes & shelves variant
    },
    abilities: {
      type: VIEW.abilities,
      open: () => plugin.nav.openAbilities(),
      expect: 'ability',
    },
    shelving: { type: VIEW.shelving, open: () => plugin.nav.openShelving() },
    boundary: {
      type: VIEW.boundary,
      open: () => plugin.nav.openBoundary('program-masters-planning'),
    },
    review: { type: VIEW.review, open: () => plugin.nav.openReview() },
    garden: { type: VIEW.garden, open: () => plugin.nav.openGarden() },
    diagnostics: { type: VIEW.diagnostics, open: () => plugin.nav.openDiagnostics() },
  };

  const mounted = [];
  const failed = [];

  for (const [name, spec] of Object.entries(fixtures)) {
    const type = spec.type || VIEW[name.replace(/_.*/, '')] || VIEW[name];
    let threw = null;
    try {
      await spec.open();
    } catch (error) {
      threw = error;
    }
    if (threw) {
      failed.push({ name, error: `${threw.message}` });
      check(`${name}: opens without throwing`, false, threw.stack || threw.message);
      continue;
    }
    const view = viewOf(app, type);
    if (!view) {
      failed.push({ name, error: 'no leaf of this type was opened' });
      check(`${name}: a leaf of type ${type} exists`, false, 'getLeavesOfType returned none');
      continue;
    }
    const text = view.contentEl.allText();
    const rendered = view.contentEl.children.length > 0 && text.length > 0;
    check(`${name}: renders content`, rendered,
      `children=${view.contentEl.children.length} text="${text.slice(0, 80)}"`);
    if (spec.expect) {
      check(`${name}: shows expected fixture content "${spec.expect}"`,
        text.includes(spec.expect), `text="${text.slice(0, 200)}"`);
    }
    mounted.push(name);
  }

  heading('probe 1 · summary');
  console.log(`mounted: ${mounted.length}, failed: ${failed.length}`);
  if (failed.length) {
    console.log('failed mounts:', JSON.stringify(failed, null, 2));
  }
  return result('probe 1 (mount all views)');
}

main()
  .then((code) => process.exit(code))
  .catch((error) => { console.error(error); process.exit(1); });

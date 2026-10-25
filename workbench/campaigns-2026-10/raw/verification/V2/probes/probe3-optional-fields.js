/* V2 probe 3 — no view throws on a missing optional field.
 *
 * Strips a set of optional projected fields at manifest-read time (the same
 * patch point support.js documents), then mounts every leaf and asserts a
 * render without a throw. A throw here is a finding: the projection readers
 * are supposed to treat absent optional data as absent.
 */
'use strict';

const { support, boot, VIEW, check, heading, result } = require('./common');

const viewOf = (app, type) => app.workspace.getLeavesOfType(type)[0]?.view || null;

const OPENERS = [
  ['home', VIEW.home, (p) => p.nav.openHome()],
  ['program', VIEW.program, (p) => p.nav.openLearn()],
  ['module-list', VIEW.module, (p) => p.nav.openModules()],
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

/* Optional fields, by where they live in the manifest. Deleting keys is the
 * honest simulation of a producer that omits them; `null` for fields the
 * schema allows explicitly null. */
function stripOptional(manifest) {
  const drop = (rows, keys) => {
    for (const row of rows || []) {
      if (!row || typeof row !== 'object') continue;
      for (const key of keys) delete row[key];
    }
  };
  drop(manifest.stages, ['estimate_minutes', 'criteria', 'resources', 'concept_ids']);
  drop(manifest.units, ['scope', 'status']);
  drop(manifest.modules, ['institution', 'code', 'exam', 'standing']);
  drop(manifest.projects, ['status', 'objective']);
  drop(manifest.workspaces ?? [], ['next_action', 'deadline', 'standing', 'objective', 'module_ids', 'unit_ids']);
  drop(manifest.academic_deadlines, ['label', 'title', 'kind', 'registration_state', 'module_id', 'modules']);
  drop(manifest.study_maps, ['current_stage']);
  drop(manifest.review_items, ['category', 'reason']);
  drop(manifest.topic_packs, ['purpose', 'summary', 'domain']);
  drop(manifest.garden_entries, ['summary', 'state']);
  drop(manifest.relations, ['context']);
  for (const relation of manifest.relations || []) relation.source = null;
  for (const record of manifest.records || []) {
    delete record.summary;
    delete record.aliases;
    delete record.authorship;
    delete record.role;
    delete record.state;
  }
}

async function main() {
  heading('probe 3 · no view throws on a missing optional field');
  const { app, plugin } = await boot({ patchManifest: stripOptional });
  for (const [name, type, open] of OPENERS) {
    let threw = null;
    try { await open(plugin); } catch (error) { threw = error; }
    const view = viewOf(app, type);
    const rendered = !threw && view && view.contentEl.children.length > 0
      && view.contentEl.allText().length > 0;
    check(`${name}: renders with optional fields absent`, rendered,
      threw ? String(threw.stack || threw).slice(0, 500) : 'no content rendered');
  }
  return result('probe 3 (missing optional fields)');
}

main()
  .then((code) => process.exit(code))
  .catch((error) => { console.error(error); process.exit(1); });

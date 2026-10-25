/* V2 shared helpers. Requires the pinned clone's own dashboard support so the
 * mount path, fixture and stub are exactly the ones the UI ships. */
'use strict';

const ROOT = '/Users/aramaljanadi/los-glm-V2-2026-10/obsidian-ui';
const support = require(`${ROOT}/tests/dashboard/support`);
const { browserDom } = require(`${ROOT}/tests/dashboard/browser-dom`);

const { boot, build, VIEW, waitFor } = support;

let failures = 0;
let group = '';
function check(name, condition, detail = '') {
  if (condition) { console.log(`  ok   ${name}`); return; }
  failures += 1;
  console.log(`  FAIL [${group}] ${name}${detail ? `\n       ${detail}` : ''}`);
}
function heading(title) { group = title; console.log(`\n${title}`); }
function result(label) {
  console.log(failures ? `\n${label}: ${failures} FAILURE(S)` : `\n${label}: all checks passed`);
  return failures ? 1 : 0;
}

/** Interactives whose accessible name is required. */
function interactives(root) {
  const out = [];
  const walk = (node) => {
    const tag = node.tag;
    const cls = [...node.classes];
    const isControl = tag === 'button' || tag === 'a' || tag === 'input'
      || tag === 'select' || tag === 'textarea'
      || node.getAttribute('role') === 'button'
      || (tag === 'summary');
    if (isControl) out.push(node);
    for (const child of node.children) walk(child);
  };
  walk(root);
  return out;
}

/** Accessible name per WCAG-ish approximation: text, aria-label, title,
 * placeholder, or value. aria-hidden controls are decorative and excluded. */
function accessibleName(el) {
  if (el.getAttribute('aria-hidden') === 'true') return null; // skip, not a failure
  const label = el.getAttribute('aria-label');
  if (label && String(label).trim()) return String(label).trim();
  const title = el.getAttribute('title');
  if (title && String(title).trim()) return String(title).trim();
  if (el.tag === 'input' || el.tag === 'textarea') {
    const placeholder = el.getAttribute('placeholder');
    if (placeholder && String(placeholder).trim()) return String(placeholder).trim();
    if (el.getAttribute('aria-labelledby')) return '(labelledby)';
  }
  const text = el.allText().trim();
  if (text) return text;
  return null;
}

/** Depth-first walk of the El tree. */
function walkAll(root, fn) {
  fn(root);
  for (const child of root.children) walkAll(child, fn);
}

module.exports = {
  ROOT, support, browserDom, boot, build, VIEW, waitFor,
  check, heading, result, interactives, accessibleName, walkAll,
};

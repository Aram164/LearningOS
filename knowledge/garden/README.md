# The Garden 🌱 (exploratory layer)

This folder is the **Garden** — the messy, low-friction half of the Learning OS,
the opposite of the strict canonical notes in `../notes/` ("the Fortress").

**Drop ideas here** as plain Markdown. No frontmatter, no concept links, no
validation, no filing rules. Sprinkle inline `#tags` (e.g. `#chaos`,
`#philosophy`, `#kernels`) if you want them grouped. Half-formed, cross-cutting,
"I don't yet know where this belongs" thoughts live here.

- **Exempt from `make check`.** Nothing here is validated, linked, or counted.
  Write freely and badly.
- **Not the inbox.** `../../work/inbox/` is a queue you *empty* by filing each
  item. The Garden is a place ideas are *allowed to sit and mature*. Use inbox
  for "file this now"; use the Garden for "let this gestate".
- **The Nebula.** Run `make views`; `../../generated/nebula.md` indexes every
  garden note by tag and shows which have sat longest — the ripest for a
  promote / keep / prune decision.
- **Harvest.** When an idea matures, say **"Harvest the Garden"**. Claude
  proposes proper frontmatter and moves the ripe ones into `../notes/` after
  your approval, then validates.

Full contract: `../../system/CLAUDE.md` §14. Keep files pure Markdown — stray
binaries (PDFs, slides, images) are still flagged and belong in `materials/`.

*(This README is ignored by the Nebula. Delete the `example-*.md` seed once you
have real sparks of your own.)*

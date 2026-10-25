# Finding: `garden.seed.create` can mint seeds its own readers never see

- **Capability:** `garden.seed.create` (CLI `garden-seed-create`).
- **Batch:** C1-C (family `garden`).
- **Base:** `d6c4779029e366718b71bda158d2aa8f9da1db39` (GitHub `origin/main`).
- **Reproduction:** `tests/test_c1c_garden_reserved_slug.py` in the clone
  (registered in `tests/group_map.py`, group `gateway`); fails on base. A
  copy is in this folder as `test_garden_invisible_reserved_slug.py`.

## The command

```
los capability garden.seed.create --payload-file <envelope; title "README",
                                                    text "An idea worth keeping. #meta">
los note-read garden-note-readme --limit 100
```

## What I observed, verbatim

The create succeeds and receipts the seed:

```
seed_path: knowledge/garden/readme.md      # file exists, receipt written, rc 0
```

The stable id the system itself derives for that file —
`garden_id(knowledge/garden, knowledge/garden/readme.md)` — is
`garden-note-readme`. Reading it back refuses:

```
los: INVALID_REQUEST: note not found: garden-note-readme
```

The seed is equally invisible to `note.search --type garden-note` and to the
Nebula projection: both project from `repo.garden_notes`, which `load_garden`
built with the meta-file skip. A seed the system just receipted as created
cannot be read, searched, or harvested by any Core surface.

## What I expected, and who says so

- `system/contracts/capabilities.yaml`, `garden.seed.create` invariants:
  **"original seed text is preserved"** — the write path preserves the bytes
  but leaves the seed outside every read surface the capability's own result
  points at (`seed_path` is the only handle it returns).
- `tools/learning_os/derive/garden.py` module docstring: "Their existence,
  identity, title, tags, and revision are **Core facts** and must remain
  available" — this seed's existence is not available to Core.
- `system/CLAUDE.md` §14: the harvest routine "reads **every** `.md` in
  `knowledge/garden/`" — the human routine would find it, but every
  capability surface (and the Nebula, "the only lens on the Garden") skips
  it, so nothing machine-driven ever surfaces it again.
- The asymmetry is the defect: the read side declares its admission rules
  (`tools/learning_os/store/loading/knowledge.py:111-113` — files whose
  `stem.lower() == "readme"`, dot- and underscore-prefixed names, and
  `transcriptions`/`syntheses` parents are meta), but the write side applies
  none of them (`_seed_slug`, `app/handlers/capture.py:53-71` maps any title
  or first line onto a filename with no reserved-name check).

Expected: `garden.seed.create` refuses a slug the garden reader will never
admit (`readme`, and the dot/underscore class it cannot generate but the
check should still name), with the same typed-refusal treatment
`note.create` gives its destination rules — or `load_garden` admits
`readme.md` files created by the capability. Today the refusal site simply
does not exist.

## Root cause

`tools/learning_os/app/handlers/capture.py:53-71` (`_seed_slug`) builds the
filename purely mechanically (`re.sub(r"[^a-z0-9]+", "-", source.lower())[:64]
or "garden-seed"`) and `garden_seed_create` writes it with no check against
the reader's meta-file conventions enforced one directory over in
`tools/learning_os/store/loading/knowledge.py:111-113` and honoured by
`project_garden_entries` (`derive/garden.py:74`), `note.content`'s garden
branch, and the manifest projection.

## Suggested fix

Refuse in `garden_seed_create` (after `_seed_slug`) any slug whose target
file `load_garden` would skip — concretely `slug.lower() == "readme"`, since
the slug grammar already excludes dot/underscore names — with a typed
refusal naming the reserved word and suggesting a different title. One
line of guard, one refusal site; the test asserts the invariant in both
directions (refuse, or create a seed the stable-id read can actually
return), so either honest shape passes. Severity: low-moderate — no data
loss (the file and its git history exist), but a receipted create whose
artifact is unreachable through every declared read capability, and a
silent divergence between the write path and the read path's admission
rules.

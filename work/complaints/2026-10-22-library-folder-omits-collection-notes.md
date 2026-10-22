# Library folder previews omit the collection's role and access notes

Observed 2026-10-22 while verifying the newly created Student Developer Pack source collection in the real Obsidian vault. Ownership: sibling `learningos-obsidian-ui` repository.

## Verified observation and impact

The ordinary Library folder browser reaches all 13 new entries, but selecting a source in that collection shows only provider, URL, registry ID and domain aliases. The collection's authored `group` and `why` are absent from the folder row and selected-item inspector. For these entries, `why` records useful access context such as a selected course bundle or a short offer window. A learner can choose Open online before encountering that context.

The context is preserved and accessible: clicking Source record opens source detail, whose Collections section displays it. This is an extra navigation step and loss of context in the preview, not data loss or an inaccessible source. No partner offer was redeemed during the check.

## Reproduction and UI proof

Environment: Obsidian 1.14.4 on macOS, Europe/Berlin. Installed build metadata records UI revision `ad9541744fb9324843c9fcb8fc20e6bfe9d0c16d` and bundle digest `sha256:078c5ab3bf3cd9dfe14431a764902a62631c2a091c5346f69e8e3d72cc25859c`; the installed file digest matches. Runtime identity was not independently checked in Diagnostics. Current UI source HEAD is `6e94753c1e44671bbaabac39347faa5aba0f4f13`.

1. Open Library → Catalogues → GitHub Student Developer Pack — learning sources.
2. Select Educative — course catalogue and GitHub student bundle once.
3. Observe the selected-item inspector: Details `Educative · educative.io`, Link, Registry ID, domain aliases, and actions Open online / Source record / Copy link. No collection role or access note is displayed.
4. Click Source record. Its Collections section displays `Learning platforms` followed by `Six-month selected bundle, over 70 courses; not unrestricted catalogue access.`

Core projection proof: `los inspect github-student-developer-pack --json` includes the entry's `group` and `why`. The collection was created through receipt `transaction-20261022-003423-001`, revision 1, on snapshot `sha256:7c478c4afd954c64973bce52d000f0f4e59d00c5f4f5c9a6f5521a7d5893e936`.

Specific source evidence: `src/features/library/finder-tree.ts`, function `shelfSources`, reduces entries to source records; `src/features/library/finder.ts`, function `renderEntryInspector`, displays source facts without contextual collection fields. `src/features/library/detail.ts` already renders `membership.group` and `membership.why` in source detail.

## Smallest improvement and acceptance

Carry the current collection's role and note into its folder preview, preserving their ownership by collection rather than treating them as a global source evaluation.

- Selecting a collection member makes that collection's authored group and why readable before opening its external URL.
- A source belonging to multiple collections shows the current collection's context, without copying one collection's note into another.
- Empty annotations do not create empty UI sections; source links, ordering and navigation continue working.
- A focused fixture covers distinct notes for the same source in two collections.

Scope limit: this was checked on one catalogue member in the real vault, then corroborated by the two render paths. It is not a general usability audit. No unrelated UI fix was implemented.

Filed: [learningos-obsidian-ui #3](https://github.com/Aram164/learningos-obsidian-ui/issues/3). Existing repository issues were searched first; none matched this preview gap.

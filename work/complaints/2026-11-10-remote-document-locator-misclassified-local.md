# Remote document filenames mistaken for local material bindings

G8 engineering-tools preflight on Core 9aeb032 refused a remote ripgrep `GUIDE.md` route with “local claim requires a verified quote” despite a source with no `material` binding and the exact remote URL. `_explicit_file` inferred local ownership from a filename in the locator alone.

The repair keeps remote HTTP(S) document filenames remote unless an explicit `material://` file or a current/previous source material binding says otherwise. Regression tests cover remote Markdown/HTML filenames and prove that an earlier local file still prevents a downgrade. Existing local file/digest/quote policy stays in force.

Acceptance: the exact remote document is classified remote-unanchored, while previous explicit local ownership still refuses existence-only external evidence. The 62-case exact-anchor suite passed; final paired acceptance is pending. GitHub issue: pending duplicate search and filing after the main work.

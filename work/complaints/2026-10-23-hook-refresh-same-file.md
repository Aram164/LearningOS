# Hook refresh copies canonical hooks onto themselves

Observed during the authorized final verification and installation, at Core
`95e788656efaeeff789df73a9d9f8d961e9c4bfd` on macOS.

`core.hooksPath` already names this checkout's `tools/hooks`. Therefore
`git rev-parse --git-path hooks` names the source directory, and `make hooks`
fails with three same-file `install` diagnostics and exit64. It never reaches
the sibling UI refresh. Existing `.git/hooks` files are unused old copies;
the active Core hook is the current canonical file. No guard was weakened.

Investigate an idempotent same-source/destination check in the recipe while
preserving permissions, stale-hook detection, worktree support and all gates.
Acceptance includes ordinary `.git/hooks`, an explicitly configured canonical
hook directory, and successful sibling refresh. Only the latter configuration
was reproduced here; no linked-worktree reproduction is claimed.

Filed after the correction landing:
[LearningOS#26](https://github.com/Aram164/LearningOS/issues/26).

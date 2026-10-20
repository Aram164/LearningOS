# Integration and exact-pair verification

`integration/scope-and-cleanup-2026-10-20` starts at Core `40d8afe` and
contains the cleanup review, the seven rebuilt scope fixes ending at
`9e762c3d`, and follow-up `2c804fb6`. Merge `a73053cb` brings the follow-up
into the combined branch. The published record and reproduction-script
repairs follow it.

The paired UI is `66ca47aa7cf3eb2201a6af939e54a05471fa8594`.
The cleanup and fix histories remain separate and readable. The integration
contains the final fix branch without another history rebuild.

## Certification procedure

From the primary Core checkout with its sibling UI and materials trees:

```sh
make system-check
.venv/bin/python tools/verified_pairs.py check
```

`system-check` includes the entire Core suite and the UI check, and stamps
only a clean exact pair. The authoritative local completion record is the
external `snapshots/final-system-check.json`, paired with its full log.
Its return code must be zero, `pair_unchanged` and `trees_clean` true, and its
Core/UI revisions must match the current branch and stamp. Do not commit or
switch branches during that command.

The previous `4665f0c0` run was terminated at 23%; it did not certify that
revision. The original five small commits have focused verification and the
scope-rule commit has a full-suite receipt on an identical tree. Those are
retained historical evidence, not a substitute for the final integration run.

## Publication

Publish each branch while its intended revision is checked out. Keep the
normal pre-push hook enabled. The rewritten fixing history requires a lease
against remote `6265f473790d4c29db6ba215e8b5305a9d261a2f`; an unexpected
remote change must stop publication. Publishing a review branch is distinct
from merging main or installing a release.

See [REPORT.md](REPORT.md) for final behavior, measurements and remaining
boundaries. The external completion receipt records publication and CI; this
file does not claim that an unfinished run or push has succeeded.

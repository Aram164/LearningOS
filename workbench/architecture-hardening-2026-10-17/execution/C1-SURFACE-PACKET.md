# C1 claim workflow surface packet — 18 October 2026

Status: **approved by Aram on 18 October 2026**, recorded at `2026-10-18T12:33:40.070403+00:00`. See [C1-SURFACE-APPROVAL.json](C1-SURFACE-APPROVAL.json) for the exact user reply and scope. The approval covers the exact five surface changes in [C1-SURFACE-PACKET.json](C1-SURFACE-PACKET.json), SHA256 `8e7781d6d10071e25eb0bc51cc0d068bbecffd51340946f1d82a7c107c31d2cf`. It does not approve a release, installation, publication, learner-content changes or independent acceptance.

- `cli.goal`: add `--authorize` for explicit intent and `--audit-file` for frozen audit authorization/closure.
- `request_schemas.goal.decide.schema.json`: the same two fields; authorization joins the existing mutually exclusive decision flags.
- `cli.route-patch`: add `--claim-evidence` for quotation/manifest evidence on material-identity changes or eligible rejudgments.
- `request_schemas.route.patch.schema.json`: the evidence object, including exact quote place/text and existing evidence alternatives.
- `catalog.commands.route.patch`: grant the additional atomic lineage-ledger write; the shared ledger artifact is guarded with the route's other owners.

The JSON contains every exact before/after surface object against Core `074f4717e14527798752de84b3c9c4e88348b658`. The source candidate remains uncommitted and unaccepted. The dated approval is recorded externally; candidate A11 baseline rows remain to be applied at authorized resumption. Implementation stays paused at the existing usage boundary.

Approval is required by FINAL-MIGRATION-CONTRACT.md §2 / C1, CONTINUE.md's explicit handoff boundary and the existing A11 ratchet in candidate `tests/test_arch_ratchets.py`. A dated approval for this packet allows only these five exact changed keys; C1 verification and all later gates remain required.

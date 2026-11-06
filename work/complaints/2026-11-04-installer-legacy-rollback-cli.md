# Installer CLI dropped --legacy-rollback (2026-11-04)

Task: final-preparation release installation (accepted-artifact install into the live vault).

Observation: `install.py --accepted-artifact ... --legacy-rollback DIR --dry-run`
refused with "legacy local installation requires --legacy-rollback DIRECTORY"
even though the flag was supplied. In `install.py`, `main()` parsed
`--legacy-rollback` but never passed it to `install_accepted_artifact`
(parameter defaulted to `None`). Function-level tests passed because they
call `install_accepted_artifact` directly; no CLI-wiring test existed.

Safety benefit retained: the refusal failed closed and preserved nothing
incorrectly; no bytes were written.

Fix: UI commit `67021d4` passes the resolved flag through and adds
`test_cli_passes_legacy_rollback_to_accepted_install`. The dry-run and real
accepted installs then succeeded against the hosted pair.

Issue: [Aram164/learningos-obsidian-ui#14](https://github.com/Aram164/learningos-obsidian-ui/issues/14)
— closed 2026-11-04 (fix: UI commit `67021d4`). Link added 2026-11-06 when the note
was committed.

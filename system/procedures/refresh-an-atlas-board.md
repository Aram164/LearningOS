---
defaults:
  environment:
    TZ: Europe/Berlin
---

# Open and refresh a managed Atlas board

This procedure targets the experimental pair from ADR-024. The transcript
uses the board controller with a synthetic vault port. The UI steps also
need host acceptance against the isolated Obsidian fixture.

## Open, close and refresh the board

In Atlas, select a scope and choose **Open board**. Move a managed card
or add a card and let Canvas save. Keep the Atlas pane open. **Refresh
board** refuses while a managed board is open, including a pop-out. Close
all managed boards, inspect the refresh preview, and confirm it. Reopen
the board. Compare the edited geometry and authored objects, and confirm
the refreshed managed content.

```scrut
$ eval "$($LOS_REPO/tests/procedure_helpers/los-fixture rich_world)"
```

```scrut
$ if [ -f "$LOS_REPO/../obsidian-ui/tests/test-atlas-boards.js" ]; then node "$LOS_REPO/../obsidian-ui/tests/test-atlas-boards.js"; else printf '%s\n' 'Atlas board controller proof requires the sibling UI checkout.'; fi
Atlas board* (glob)
```

In a paired checkout the driver asserts mismatched template refusal, a
refused refresh with managed Canvas open, a stale-preview refusal, retained
working geometry, and preservation of the accepted child target and portal
flag. A Core-only checkout reports that the UI is required. For a host
failure, record the scope, editor leaves including pop-outs, both file
digests and the refusal. Restore the working board and sidecar together.

"""Clock-derived validation advisories, computed live on every cached read.

`WS-NEGLECT` and `INBOX-STALE` depend on wall-clock age rather than on any
authored file's content: a release turns red with no authored change simply
because time passed. The status validation cache (#103) therefore serves
every other issue from the cache and recomputes these two live.

Both checks stay owned here once: the Validator's `check_workspaces` and
`check_files` delegate to these functions, so a full run and a cache hit
can never disagree on what the advisories say.
"""

from __future__ import annotations

import time

from ..githistory import GitHistoryError, last_commit_timestamp
from .common import DYNAMIC_ADVISORY_WARNINGS, Issue

#: Message prefix of the GIT-HISTORY error the neglect check raises when
#: history is unreadable. Hygiene raises GIT-HISTORY too, for a different
#: (cached) reason — the prefix is what tells the cache splice apart.
NEGLECT_GIT_HISTORY_PREFIX = "cannot check workspace neglect: "


def workspace_neglect_issues(repo) -> list[Issue]:
    """WS-NEGLECT warnings for workspaces untouched 21+ days (per Git).

    A GitHistoryError mid-loop answers the collected warnings plus the
    GIT-HISTORY error, exactly as the inlined check did; the live cache
    path takes this function's whole output, so a newly unreadable
    history still surfaces instead of serving a cached clean bill.
    """
    issues: list[Issue] = []
    non_standing = [w for w in repo.active_workspaces() if not w.standing]
    try:
        for ws in non_standing:
            ts = last_commit_timestamp(
                repo.root, str(ws.path.parent.relative_to(repo.root)))
            if ts is None:
                continue
            days = (time.time() - ts) / 86400
            if days >= 21:
                issues.append(Issue(
                    "W", "WS-NEGLECT",
                    f"workspace '{ws.id}' untouched for {int(days)} days (per Git)"))
    except GitHistoryError as exc:
        issues.append(Issue(
            "E", "GIT-HISTORY", f"{NEGLECT_GIT_HISTORY_PREFIX}{exc}"))
    return issues


def inbox_stale_issues(repo) -> list[Issue]:
    """INBOX-STALE warnings for inbox items older than 14 days."""
    issues: list[Issue] = []
    inbox = repo.root / "work" / "inbox"
    if inbox.is_dir():
        now = time.time()
        for path in sorted(inbox.iterdir()):
            if path.name.startswith("."):
                continue
            age_days = (now - path.stat().st_mtime) / 86400
            if age_days > 14:
                issues.append(Issue(
                    "W", "INBOX-STALE",
                    f"inbox item '{path.name}' is {int(age_days)} days old "
                    "(unrouted capture — the inbox should trend toward empty)"))
    return issues


def advisory_issues(repo) -> list[Issue]:
    """Both clock-derived advisories, in Validator.run order."""
    return inbox_stale_issues(repo) + workspace_neglect_issues(repo)


def is_live_advisory(issue: Issue) -> bool:
    """Whether the cache-hit path recomputes this issue live.

    The two dynamic codes, plus the neglect check's own GIT-HISTORY
    error — which shares its code with hygiene's unrelated one and is
    told apart by the message prefix this module constructs.
    """
    assert isinstance(issue, Issue)
    if issue.code in DYNAMIC_ADVISORY_WARNINGS:
        return True
    return (issue.code == "GIT-HISTORY"
            and issue.message.startswith(NEGLECT_GIT_HISTORY_PREFIX))

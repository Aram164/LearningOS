"""Positive fixture: membership test on str(exc) (SPEC §3.1 rule a)."""


def is_snapshot_error() -> bool:
    try:
        raise OSError("no snapshot here")
    except OSError as e:
        if "snapshot" in str(e):
            return True
    return False

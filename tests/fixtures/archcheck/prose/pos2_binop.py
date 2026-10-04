"""Positive fixture: rule (a) over + concatenations and pure f-strings (item 3(i))."""


def is_snapshot_error(stdout: str, stderr: str) -> bool:
    if "snapshot" in (stdout + stderr):
        return True
    return False


def is_snapshot_fstring(stdout: str, stderr: str) -> bool:
    if "snapshot" in f"{stdout}{stderr}":
        return True
    return False

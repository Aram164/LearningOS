"""Positive fixture: membership test on a wrapped message (rule a)."""


def failed(msg: str) -> bool:
    if "failed" in msg.lower():
        return True
    return False

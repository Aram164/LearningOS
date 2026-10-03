"""Positive fixture: string-method test on suspect text (rule b)."""


def is_flag(text: str) -> bool:
    if text.startswith("--"):
        return True
    return False

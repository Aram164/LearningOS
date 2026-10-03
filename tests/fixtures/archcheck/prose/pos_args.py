"""Positive fixture: membership tests on exception args (rule a)."""


def denied() -> bool:
    try:
        raise OSError("denied")
    except OSError as e:
        if "denied" in e.args:
            return True
    return False


def denied_first() -> bool:
    try:
        raise OSError("denied")
    except OSError as e:
        if "denied" in e.args[0]:
            return True
    return False

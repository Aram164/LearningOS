"""Negative fixture: %-formatting, .format and mixed + operands are not (i)."""


def has_code_percent(msg: str) -> bool:
    if "code" in "%s" % msg:  # noqa: UP031 - the % form is the point
        return True
    return False


def has_code_format(msg: str) -> bool:
    if "code" in "({})".format(msg):  # noqa: UP032 - the .format form is the point
        return True
    return False


def has_code_mixed(msg: str, suffix: str) -> bool:
    if "code" in msg + suffix:
        return True
    return False

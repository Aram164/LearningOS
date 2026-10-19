"""Negative fixture: typed handling without text matching."""


def classify(exc: OSError) -> str:
    try:
        raise exc
    except OSError as e:
        if e.errno == 2:
            return "missing"
        raise ValueError(f"bad: {e}") from e
    return "ok"

"""Negative fixture: formatting suspect text is not a decision."""


def describe(msg: str) -> str:
    return f"failure: {msg}"


def report(msg: str) -> None:
    print(f"has x: {'x' in msg}")

"""Negative fixture: tests used only in raise arguments are not decisions."""

import re


class WriteRefused(Exception):
    pass


def check(msg: str) -> None:
    if not msg:
        raise WriteRefused("empty message")
    raise WriteRefused("has x" if "x" in msg else "no x")


def check_prefix(msg: str) -> None:
    raise WriteRefused("starts" if msg.startswith("s") else "other")


def check_pattern(msg: str) -> None:
    raise WriteRefused("match" if re.search("s+", msg) else "other")

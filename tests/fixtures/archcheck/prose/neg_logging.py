"""Negative fixture: logging calls are not decisions."""

import logging


def note(msg: str) -> None:
    logging.info("failure: %s", msg)
    logging.error("matched: %s", "x" in msg)

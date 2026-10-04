"""Positive fixture: an A4 call through an import alias (SPEC §3.7 item 4)."""

from learning_os.loader import load_repo as lr


def open_repo(root):
    return lr(root)

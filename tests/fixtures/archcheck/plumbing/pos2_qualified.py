"""Positive fixture: qualified A4 calls (SPEC §3.7 item 4)."""

import support


def open_repo(root):
    return support.load_repo(root)


def fingerprint_repo(repo):
    return repo.canonical_fingerprint()

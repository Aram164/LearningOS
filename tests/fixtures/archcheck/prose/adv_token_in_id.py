"""Adversarial fixture: the word "snapshot" arrives via a user id.

The id may itself contain "snapshot", so matching the message text is still
a prose decision even though the token looks structural.
"""


def unit_failed(unit_id: str) -> bool:
    msg = f"unit {unit_id} failed"
    return "snapshot" in msg

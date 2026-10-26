"""Receipt authority and publication observation shared by all consumers."""
from __future__ import annotations

import functools
import json
from pathlib import Path
from typing import cast

import yaml

from learning_os.store.diagnostics.resolver import collect_authority
from learning_os.store.fingerprint import canonical_fingerprint
from learning_os.store.loading.yamlio import UniqueKeySafeLoader
from learning_os.store.manifest_identity import bytes_sha256, check_identity


def _stat(path: Path) -> tuple[int, ...]:
    try:
        s = path.stat()
        return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns
    except OSError:
        return ()


@functools.lru_cache(maxsize=32)
def _publication(root_text: str, manifest_stat: tuple[int, ...],
                 identity_stat: tuple[int, ...]) -> tuple[dict[str, object], dict[str, object]] | None:
    root = Path(root_text)
    try:
        raw = (root / "generated/manifest.json").read_bytes()
        identity = json.loads((root / "generated/manifest.identity.json").read_text())
        manifest = json.loads(raw)
        if not isinstance(manifest, dict) or not isinstance(identity, dict):
            return None
        if identity.get("manifest_sha256") != bytes_sha256(raw):
            return None
        generated = manifest.get("_generated")
        if not isinstance(generated, dict) or generated.get("snapshot_id") != identity.get("snapshot_id"):
            return None
        if _stat(root / "generated/manifest.json") != manifest_stat or _stat(root / "generated/manifest.identity.json") != identity_stat:
            return None
        return {"_generated": generated}, identity
    except (OSError, ValueError, TypeError):
        return None


def observe(root: Path, *, verify_current: bool = True) -> dict[str, object]:
    root = root.resolve()
    pair = _publication(str(root), _stat(root / "generated/manifest.json"),
                        _stat(root / "generated/manifest.identity.json"))
    reason = "projection-publication-pending"
    current = pair is not None
    if pair is not None and verify_current:
        manifest, identity = pair
        try:
            current, reason = check_identity(root, manifest, identity,
                                             live_snapshot="sha256:" + canonical_fingerprint(root))
        except (OSError, ValueError):
            current = False
            reason = "projection-not-verifiable"
    if not current or pair is None:
        return {"snapshot_id": None, "published": False, "reason": reason}
    return {"snapshot_id": pair[1]["snapshot_id"], "published": True, "reason": "ready"}


def _completed(root_text: str, receipt_path: str, snapshot_after: str,
               receipt_stat: tuple[int, ...], ledger_stat: tuple[int, ...]) -> bool:
    root = Path(root_text)
    path = root / receipt_path
    try:
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            return False
        with path.open() as stream:
            data: object = yaml.load(stream, Loader=UniqueKeySafeLoader)
        if not isinstance(data, dict) or data.get("snapshot_after") != snapshot_after:
            return False
        request = data.get("request")
        if not isinstance(request, dict):
            return False
        authority = collect_authority(root, request_id=str(request.get("request_id")),
            idempotency_key=str(request.get("idempotency_key")), capability=str(data.get("capability")))
        verified = authority.verified_receipt
        return bool(verified is not None and verified.get("_path") == receipt_path
                    and verified.get("snapshot_after") == snapshot_after
                    and _stat(path) == receipt_stat
                    and _stat(root / "operations/transactions/idempotency.yaml") == ledger_stat)
    except (OSError, ValueError, TypeError, yaml.YAMLError):
        return False


def receipt_completed(root: Path, receipt_path: str | None, snapshot_after: str | None) -> bool:
    root = root.resolve()
    if not receipt_path or not snapshot_after or Path(receipt_path).is_absolute():
        return False
    path = root / receipt_path
    if not path.resolve().is_relative_to(root):
        return False
    return _completed(str(root), receipt_path, snapshot_after, _stat(path),
                      _stat(root / "operations/transactions/idempotency.yaml"))


def dependency_ready(root: Path, required: list[dict[str, str | None]],
                     known: list[dict[str, str | None]], *,
                     completion_only: bool = False) -> tuple[bool, str]:
    signatures = [(r.get("receipt_path"), r.get("snapshot_after")) for r in required]
    if not completion_only and required:
        # Poll publication hints first. Receipt authority is checked fresh only
        # when a candidate projection could satisfy these dependencies.
        hint = observe(root, verify_current=False)
        if not hint["published"]:
            return False, str(hint["reason"])
        raw_positions = {(r.get("receipt_path"), r.get("snapshot_after")): i
                         for i, r in enumerate(known)}
        if not set(signatures).issubset(raw_positions):
            return False, "required-write-not-known"
        last = max(raw_positions[s] for s in signatures)
        if hint["snapshot_id"] not in {r.get("snapshot_after") for r in known[last:]}:
            return False, "projection-not-current"
    # One observation may mention the same receipt in both required and known.
    # Reuse only within this call; the next poll rechecks authority from disk.
    verified: dict[tuple[str | None, str | None], bool] = {}

    def completed(path: str | None, snapshot: str | None) -> bool:
        key = (path, snapshot)
        if key not in verified:
            verified[key] = receipt_completed(root, path, snapshot)
        return verified[key]

    for path, snapshot in signatures:
        if not completed(path, snapshot):
            return False, "receipt-missing-or-unbound"
    if completion_only or not required:
        return True, "ready"
    positions = {(r.get("receipt_path"), r.get("snapshot_after")): i for i, r in enumerate(known)
                 if completed(r.get("receipt_path"), r.get("snapshot_after"))}
    if not set(signatures).issubset(positions):
        return False, "required-write-not-known"
    latest = max(positions[s] for s in signatures)
    allowed = {r.get("snapshot_after") for r in known[latest:]
               if completed(r.get("receipt_path"), r.get("snapshot_after"))}
    obs = observe(root, verify_current=False)
    if not obs["published"]:
        return False, str(obs["reason"])
    return (True, "ready") if obs["snapshot_id"] in allowed else (False, "projection-not-current")


def settlement_ready(root: Path, receipt_path: str | None, snapshot_after: str | None) -> dict[str, object]:
    done = receipt_completed(root, receipt_path, snapshot_after)
    obs = observe(root)
    return {"write_completed": done, "current_snapshot_id": obs["snapshot_id"],
            "settled": bool(done and obs["published"]), "reason": obs["reason"]}


def strict_records(values: object) -> list[dict[str, str | None]]:
    if not isinstance(values, list):
        raise ValueError("dependencies must be a list")
    records = []
    for item in values:
        if not isinstance(item, dict) or set(item) != {"receipt_path", "snapshot_after"} or not all(isinstance(v, str) for v in item.values()):
            raise ValueError("each dependency requires receipt_path and snapshot_after")
        records.append(cast(dict[str, str | None], item))
    return records

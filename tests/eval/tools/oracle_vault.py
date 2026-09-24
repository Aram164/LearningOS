#!/usr/bin/env python3
"""Seal and open the private evaluation oracle.

    export LOS_EVAL_ORACLE_KEY='…'     # held by the campaign owner, never committed
    python tests/eval/tools/oracle_vault.py open  --out /some/dir/outside/the/repo
    python tests/eval/tools/oracle_vault.py seal  ORACLE_DIR
    python tests/eval/tools/oracle_vault.py check

The oracle (relation judgments, expected answers, scenario expectations, author
notes) is committed only as tests/eval/private/oracle.tar.gz.enc: a
deterministic tar.gz encrypted with `openssl enc -aes-256-cbc -pbkdf2 -iter
600000 -md sha256 -salt`, keyed by the environment variable
LOS_EVAL_ORACLE_KEY. tests/eval/private/oracle.manifest.json records the
SHA-256 of the plaintext archive so `open` and `check` can prove the
decryption is intact (CBC alone does not authenticate).

`open` refuses to extract inside the repository so plaintext cannot be
committed by accident. Consumer sessions are never given the key.
"""

from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIVATE = HERE.parent / "private"
REPO = HERE.parents[2]
SEALED = PRIVATE / "oracle.tar.gz.enc"
MANIFEST = PRIVATE / "oracle.manifest.json"
KEY_ENV = "LOS_EVAL_ORACLE_KEY"
OPENSSL = ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "600000", "-md", "sha256"]


def _key_env() -> dict:
    if not os.environ.get(KEY_ENV):
        raise SystemExit(f"oracle_vault: set {KEY_ENV} (the campaign owner holds the key)")
    return os.environ


def deterministic_tar(src: Path) -> tuple[bytes, list[str]]:
    buf = io.BytesIO()
    names = []
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:
            for path in sorted(p for p in src.rglob("*") if p.is_file()):
                rel = path.relative_to(src).as_posix()
                data = path.read_bytes()
                info = tarfile.TarInfo(name=f"oracle/{rel}")
                info.size, info.mtime, info.mode = len(data), 0, 0o644
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                tar.addfile(info, io.BytesIO(data))
                names.append(rel)
    return buf.getvalue(), names


def _inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(REPO)
        return True
    except ValueError:
        return False


def seal(src: Path) -> None:
    env = _key_env()
    if _inside_repo(src):
        raise SystemExit("oracle_vault: the plaintext oracle must live outside the repository")
    plain, names = deterministic_tar(src)
    PRIVATE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tar_path = Path(tmp) / "oracle.tar.gz"
        tar_path.write_bytes(plain)
        subprocess.run([*OPENSSL, "-salt", "-pass", f"env:{KEY_ENV}", "-in", str(tar_path),
                        "-out", str(SEALED)], check=True, env=env)
    MANIFEST.write_text(json.dumps({
        "sealed": dt.date.today().isoformat(),
        "plaintext_sha256": hashlib.sha256(plain).hexdigest(),
        "plaintext_bytes": len(plain),
        "files": names,
        "cipher": " ".join(OPENSSL) + " -salt",
        "key_env": KEY_ENV,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"sealed {len(names)} files → {SEALED.relative_to(REPO)}")


def decrypt() -> bytes:
    env = _key_env()
    proc = subprocess.run([*OPENSSL, "-d", "-pass", f"env:{KEY_ENV}", "-in", str(SEALED)],
                          capture_output=True, env=env)
    if proc.returncode != 0:
        raise SystemExit("oracle_vault: decryption failed (wrong key?)")
    expected = json.loads(MANIFEST.read_text(encoding="utf-8"))["plaintext_sha256"]
    if hashlib.sha256(proc.stdout).hexdigest() != expected:
        raise SystemExit("oracle_vault: decrypted archive does not match the manifest digest")
    return proc.stdout


def open_to(out: Path) -> None:
    if _inside_repo(out):
        raise SystemExit("oracle_vault: refusing to write the plaintext oracle inside the "
                         "repository; choose a directory outside it")
    plain = decrypt()
    out.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(plain), mode="r:gz") as tar:
        tar.extractall(out, filter="data")
    print(f"opened → {out / 'oracle'}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("seal")
    s.add_argument("src", type=Path)
    o = sub.add_parser("open")
    o.add_argument("--out", required=True, type=Path)
    sub.add_parser("check")
    args = parser.parse_args(argv)
    if args.cmd == "seal":
        seal(args.src)
    elif args.cmd == "open":
        open_to(args.out)
    else:
        decrypt()
        print("oracle_vault: sealed oracle decrypts and matches its manifest")
    return 0


if __name__ == "__main__":
    sys.exit(main())

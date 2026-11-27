"""Study-mode boundary enforcement and symlink-safe descriptor traversal (PLAN-D D1/D2).

Owns protected host-read subpaths, lexical anchor resolution against
``LOS_STUDY_FENCE_CORE`` / ``LOS_STUDY_FENCE_SCRATCH``, staged manifest
loading, and step-by-step ``O_NOFOLLOW`` traversal shared by Core gateway
reads, the broker, ``seal_envelope.py``, and ``study_launch.py``.
"""

from __future__ import annotations

import contextlib
import errno
import functools
import json
import os
import stat
import time
from collections.abc import Callable
from pathlib import Path

from learning_os.domain.failures import StudyFenceRefused
from learning_os.domain.validation import TEXT_CACHE_TOP_DIR
from learning_os.store.contracts.write_scopes import (
    WriteScopeError,
    guard_tool_output_path,
    path_segment,
)

_DIR_FD_EINVAL_ATTEMPTS = 4

STUDY_FENCE_CORE_ENV = "LOS_STUDY_FENCE_CORE"
STUDY_FENCE_SCRATCH_ENV = "LOS_STUDY_FENCE_SCRATCH"
STUDY_STAGED_MANIFEST_ENV = "LOS_STUDY_STAGED_MANIFEST"
READING_MEMORY_DIRNAME = "reading-memory"

# Bounded-read limits per input type. JSON envelopes/records align with the
# broker request cap; the staged manifest is a small index; generic study
# files (bound content/attachments) get a larger but still finite cap.
MAX_STUDY_JSON_BYTES = 8 * 1024 * 1024
MAX_STUDY_MANIFEST_BYTES = 1 * 1024 * 1024
MAX_STUDY_FILE_BYTES = 64 * 1024 * 1024

EXTERNAL_INPUT_PATH_KEYS: frozenset[str] = frozenset({
    "file",
    "body_file",
    "content_file",
    "attachment",
    "items_file",
    "drafts",
    "review_report",
})


def protected_reads(core: Path) -> list[Path]:
    """Subtrees holding raw materials, reading memory, raw-text caches, summaries, or AI requests."""
    resolved = Path(core).resolve()
    learningos = resolved.parent
    return [
        learningos / "materials",
        learningos / READING_MEMORY_DIRNAME,
        resolved / "generated" / TEXT_CACHE_TOP_DIR,
        resolved / "generated" / "material-search",
        resolved / "generated" / "material-outlines",
        resolved / "generated" / "derived-state",
        resolved / "knowledge" / "summaries",
        resolved / "operations" / "ai-actions" / "requests",
    ]


def protected_read_literals(core: Path) -> list[Path]:
    """Individual sensitive files never readable by sandboxed study agents."""
    resolved = Path(core).resolve()
    learningos = resolved.parent
    return [
        learningos / ".env",
    ]


def protected_read_targets(core: Path) -> list[Path]:
    """Combined closed subtrees and sensitive literal files."""
    return [*protected_reads(core), *protected_read_literals(core)]


def real_path(raw_path: Path | str, *, cwd: Path | None = None) -> Path:
    expanded = Path(raw_path).expanduser()
    if not expanded.is_absolute() and cwd is not None:
        expanded = cwd / expanded
    return Path(os.path.realpath(expanded))


def is_within(candidate: Path, base: Path) -> bool:
    real_candidate = Path(os.path.realpath(candidate))
    real_base = Path(os.path.realpath(base))
    return real_candidate == real_base or real_base in real_candidate.parents


def fd_open_flags(*, directory: bool) -> int:
    flags = os.O_RDONLY | os.O_NOFOLLOW
    if directory:
        flags |= os.O_DIRECTORY
    else:
        flags |= os.O_NONBLOCK
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    return flags


def find_real_ancestor(
    lex_path: Path, real_root: Path,
) -> tuple[Path, tuple[str, ...]] | None:
    """Match a lexical path onto ``real_root`` without traversing symlinks below it."""
    matched: Path | None = None
    if lex_path == real_root or real_root in lex_path.parents:
        matched = real_root
    else:
        root_str = str(real_root)
        for anc in reversed((lex_path, *lex_path.parents)):
            if str(anc) == "/":
                continue
            try:
                if os.path.realpath(anc) == root_str:
                    matched = anc
                    break
            except (OSError, ValueError):
                continue
    if matched is None:
        return None
    return matched, lex_path.relative_to(matched).parts


def open_dir_nofollow(dir_fd: int, part: str) -> int:
    """Open child directory ``part`` under ``dir_fd``, turning symlinks into ELOOP."""
    try:
        return os.open(part, fd_open_flags(directory=True), dir_fd=dir_fd)
    except OSError as exc:
        is_link = False
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            with contextlib.suppress(OSError):
                is_link = stat.S_ISLNK(os.lstat(part, dir_fd=dir_fd).st_mode)
        if exc.errno == errno.ELOOP or is_link:
            raise OSError(errno.ELOOP, "Refusing symlink parent target", part) from exc
        raise


def call_dir_fd_op[T](op: Callable[[], T]) -> T:
    """Retry a pinned dir_fd syscall transiently rejected with EINVAL mid-rmdir on Darwin."""
    # Concurrent rmdir on APFS briefly yields EINVAL on a pinned dir_fd before
    # reporting ENOENT on subsequent calls; retrying preserves O_NOFOLLOW guarantees.
    for _ in range(_DIR_FD_EINVAL_ATTEMPTS - 1):
        try:
            return op()
        except OSError as exc:
            if exc.errno != errno.EINVAL:
                raise
            time.sleep(0)
    return op()


def open_dir_chain_nofollow(
    base_path: Path,
    dir_parts: tuple[str, ...],
    *,
    create_missing: bool = False,
) -> int:
    """Open ``base_path/dir_parts`` step-by-step refusing every symlink with O_NOFOLLOW."""
    dir_flags = fd_open_flags(directory=True)
    try:
        dir_fd = os.open(base_path, dir_flags)
    except OSError as exc:
        is_link = False
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            with contextlib.suppress(OSError):
                is_link = stat.S_ISLNK(os.lstat(base_path).st_mode)
        if exc.errno == errno.ELOOP or is_link:
            raise OSError(errno.ELOOP, "Refusing symlink parent target", str(base_path)) from exc
        raise

    for raw_part in dir_parts:
        # ``..`` would climb out of ``base_path`` through the descriptor walk.
        part = path_segment(raw_part)
        try:
            next_fd = open_dir_nofollow(dir_fd, part)
        except FileNotFoundError:
            if not create_missing:
                os.close(dir_fd)
                raise
            try:
                call_dir_fd_op(functools.partial(os.mkdir, part, 0o755, dir_fd=dir_fd))
            except FileExistsError:
                pass
            except OSError:
                os.close(dir_fd)
                raise
            try:
                next_fd = open_dir_nofollow(dir_fd, part)
            except OSError:
                os.close(dir_fd)
                raise
        except OSError:
            os.close(dir_fd)
            raise
        os.close(dir_fd)
        dir_fd = next_fd
    return dir_fd


def _lexical_study_path(
    raw_path: str,
    *,
    cwd: Path | None = None,
    label: str = "file input",
) -> Path:
    if not isinstance(raw_path, str) or not raw_path.strip() or raw_path == "-" or "\x00" in raw_path:
        raise StudyFenceRefused(f"study mode requires a concrete path for {label}")
    expanded = Path(raw_path).expanduser()
    if not expanded.is_absolute():
        expanded = (cwd if cwd is not None else Path.cwd()) / expanded
    return Path(os.path.abspath(expanded))


def _match_study_anchor(
    raw_path: str,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path | None = None,
    label: str = "file input",
    allow_core: bool = True,
) -> tuple[Path, Path, tuple[str, ...]]:
    """Anchor a caller path onto scratch_dir or core_root without resolving sub-tree symlinks."""
    lex = _lexical_study_path(raw_path, cwd=cwd, label=label)
    real_core = Path(os.path.realpath(core_root))
    targets = protected_read_targets(real_core)
    protected = tuple(
        dict.fromkeys([*targets, *(Path(os.path.realpath(closed)) for closed in targets)])
    )

    candidates: list[Path] = []
    if scratch_dir is not None:
        real_scratch = Path(os.path.realpath(scratch_dir))
        for closed in protected:
            if real_scratch == closed or closed in real_scratch.parents:
                raise StudyFenceRefused(
                    f"study mode blocks {label} inside protected LearningOS tree: {real_scratch}"
                )
        candidates.append(real_scratch)
    if allow_core:
        candidates.append(real_core)

    for candidate_root in candidates:
        matched = find_real_ancestor(lex, candidate_root)
        if matched is None:
            continue
        _matched_anc, rel_parts = matched
        if any(part in ("", ".", "..") for part in rel_parts):
            raise StudyFenceRefused(f"study mode blocks invalid path traversal for {label}: {lex}")
        anchored = candidate_root.joinpath(*rel_parts) if rel_parts else candidate_root
        if candidate_root == real_core:
            for closed in protected:
                if anchored == closed or closed in anchored.parents:
                    raise StudyFenceRefused(
                        f"study mode blocks {label} inside protected LearningOS tree: {anchored}"
                    )
        return candidate_root, anchored, rel_parts

    try:
        real_target = real_path(raw_path, cwd=cwd)
    except (RuntimeError, ValueError, OSError) as exc:
        raise StudyFenceRefused(f"study mode cannot resolve {label} {raw_path!r}: {exc}") from exc
    for closed in protected:
        if real_target == closed or closed in real_target.parents:
            raise StudyFenceRefused(
                f"study mode blocks {label} inside protected LearningOS tree: {real_target}"
            )
    hint = (
        f" (write scratch files under $LOS_SCRATCH_DIR: {scratch_dir})"
        if scratch_dir is not None
        else ""
    )
    raise StudyFenceRefused(
        f"study mode blocks {label} outside the study boundary: {real_target}{hint}"
    )


def _open_study_dir_fd(
    real_root: Path,
    dir_parts: tuple[str, ...],
    *,
    label: str,
    anchored: Path,
    allow_missing: bool,
) -> int | None:
    try:
        return open_dir_chain_nofollow(real_root, dir_parts, create_missing=False)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise StudyFenceRefused(f"study mode blocks symlink in {label}: {anchored}") from exc
        if allow_missing and exc.errno == errno.ENOENT:
            return None
        if exc.filename == str(real_root):
            raise StudyFenceRefused(f"cannot access {label} root {real_root}: {exc}") from exc
        if exc.errno in (errno.ENOENT, errno.ENOTDIR):
            raise StudyFenceRefused(f"no such {label}: {anchored}") from exc
        raise StudyFenceRefused(f"cannot access {label} {anchored}: {exc}") from exc


def check_study_path(
    raw_path: str,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path | None = None,
    label: str = "file input",
    allow_core: bool = True,
) -> Path:
    """Enforce the study-mode read/write fence without traversing symlinks inside roots."""
    real_root, anchored, rel_parts = _match_study_anchor(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=allow_core,
    )
    if not rel_parts:
        if not allow_core:
            raise StudyFenceRefused(
                f"{label} target must be a file inside study scratch: {anchored}"
            )
        dir_fd = _open_study_dir_fd(
            real_root, (), label=label, anchored=anchored, allow_missing=True,
        )
        if dir_fd is not None:
            os.close(dir_fd)
        return anchored

    parent_fd = _open_study_dir_fd(
        real_root,
        rel_parts[:-1],
        label=label,
        anchored=anchored,
        allow_missing=True,
    )
    if parent_fd is not None:
        try:
            try:
                st = os.lstat(rel_parts[-1], dir_fd=parent_fd)
            except FileNotFoundError:
                pass
            except OSError as exc:
                raise StudyFenceRefused(f"cannot inspect {label} {anchored}: {exc}") from exc
            else:
                if stat.S_ISLNK(st.st_mode):
                    raise StudyFenceRefused(f"study mode blocks symlink in {label}: {anchored}")
                if not allow_core and stat.S_ISDIR(st.st_mode):
                    raise StudyFenceRefused(
                        f"{label} target must be a file, not a directory: {anchored}"
                    )
                if not allow_core and stat.S_ISREG(st.st_mode) and st.st_nlink > 1:
                    raise StudyFenceRefused(f"study mode blocks hardlink in {label}: {anchored}")
        finally:
            os.close(parent_fd)
    return anchored


def check_study_new_output_path(
    raw_path: str,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path | None = None,
    label: str = "output path",
    draft_path: str | None = None,
) -> Path:
    """Validate a new writable scratch path whose parent exists and whose leaf does not."""
    real_root, anchored, rel_parts = _match_study_anchor(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=False,
    )
    if not rel_parts:
        raise StudyFenceRefused(f"{label} target must be a file inside study scratch: {anchored}")
    if draft_path:
        try:
            _, anchored_draft, _ = _match_study_anchor(
                draft_path,
                core_root=core_root,
                scratch_dir=scratch_dir,
                cwd=cwd,
                label="draft",
                allow_core=True,
            )
        except StudyFenceRefused:
            anchored_draft = None
        if anchored_draft is not None and anchored == anchored_draft:
            raise StudyFenceRefused(
                f"{label} target must not replace the reviewed draft: {raw_path}"
            )

    parent_fd = _open_study_dir_fd(
        real_root,
        rel_parts[:-1],
        label=label,
        anchored=anchored,
        allow_missing=True,
    )
    if parent_fd is None:
        raise StudyFenceRefused(f"{label} directory does not exist: {anchored.parent}")
    try:
        try:
            st = os.lstat(rel_parts[-1], dir_fd=parent_fd)
        except FileNotFoundError:
            return anchored
        except OSError as exc:
            raise StudyFenceRefused(f"cannot inspect {label} {anchored}: {exc}") from exc
        if stat.S_ISLNK(st.st_mode):
            raise StudyFenceRefused(f"study mode blocks symlink in {label}: {anchored}")
        raise StudyFenceRefused(
            f"{label} target already exists; refusing to overwrite: {raw_path}"
        )
    finally:
        os.close(parent_fd)


def _read_regular_under_root(
    real_root: Path,
    rel_parts: tuple[str, ...],
    *,
    label: str,
    anchored: Path,
    require_existing: bool,
    max_bytes: int = MAX_STUDY_FILE_BYTES,
) -> bytes | None:
    if not rel_parts:
        raise StudyFenceRefused(f"no such {label}: {anchored}")
    parent_fd = _open_study_dir_fd(
        real_root,
        rel_parts[:-1],
        label=label,
        anchored=anchored,
        allow_missing=not require_existing,
    )
    if parent_fd is None:
        return None
    file_flags = fd_open_flags(directory=False)
    try:
        try:
            leaf_fd = os.open(rel_parts[-1], file_flags, dir_fd=parent_fd)
        except OSError as exc:
            if exc.errno == errno.ELOOP:
                raise StudyFenceRefused(f"study mode blocks symlink in {label}: {anchored}") from exc
            if exc.errno in (errno.ENOENT, errno.ENOTDIR):
                if not require_existing:
                    return None
                raise StudyFenceRefused(f"no such {label}: {anchored}") from exc
            raise StudyFenceRefused(f"cannot read {label} {anchored}: {exc}") from exc
    finally:
        os.close(parent_fd)

    try:
        st = os.fstat(leaf_fd)
    except OSError as exc:
        os.close(leaf_fd)
        raise StudyFenceRefused(f"cannot stat {label} {anchored}: {exc}") from exc
    if not stat.S_ISREG(st.st_mode):
        os.close(leaf_fd)
        raise StudyFenceRefused(f"no such {label}: {anchored}")
    if st.st_size > max_bytes:
        os.close(leaf_fd)
        raise StudyFenceRefused(
            f"{label} exceeds size limit ({max_bytes} bytes): {anchored}"
        )
    try:
        with os.fdopen(leaf_fd, "rb") as handle:
            data = handle.read(max_bytes + 1)
    except OSError as exc:
        raise StudyFenceRefused(f"cannot read {label} {anchored}: {exc}") from exc
    if len(data) > max_bytes:
        raise StudyFenceRefused(
            f"{label} exceeds size limit ({max_bytes} bytes): {anchored}"
        )
    return data


def read_study_file(
    raw_path: str,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path | None = None,
    label: str = "file input",
    allow_core: bool = True,
    max_bytes: int = MAX_STUDY_FILE_BYTES,
) -> tuple[Path, bytes]:
    """Validate and read a regular study file via O_NOFOLLOW descriptors."""
    real_root, anchored, rel_parts = _match_study_anchor(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=allow_core,
    )
    data = _read_regular_under_root(
        real_root,
        rel_parts,
        label=label,
        anchored=anchored,
        require_existing=True,
        max_bytes=max_bytes,
    )
    assert data is not None
    return anchored, data


def _read_staged_study_file(
    raw_path: str,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path | None = None,
    label: str = "file input",
    allow_core: bool = True,
) -> tuple[Path, bytes] | None:
    manifest_env = os.environ.get(STUDY_STAGED_MANIFEST_ENV)
    if not manifest_env:
        return None
    manifest_lex = Path(os.path.abspath(Path(manifest_env).expanduser()))
    manifest_dir = Path(os.path.realpath(manifest_lex.parent))
    manifest_bytes = _read_regular_under_root(
        manifest_dir,
        (manifest_lex.name,),
        label="staged study manifest",
        anchored=manifest_dir / manifest_lex.name,
        require_existing=True,
        max_bytes=MAX_STUDY_MANIFEST_BYTES,
    )
    assert manifest_bytes is not None
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise StudyFenceRefused(f"corrupt staged study manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise StudyFenceRefused("staged study manifest must be a JSON object")

    _real_root, anchored, _rel_parts = _match_study_anchor(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=allow_core,
    )
    entries = manifest.get("entries")
    if not isinstance(entries, dict):
        raise StudyFenceRefused("staged study manifest missing entries")
    rel_staged = entries.get(str(anchored))
    if not isinstance(rel_staged, str) or not rel_staged:
        return None
    rel_parts = Path(rel_staged).parts
    if not rel_parts or any(part in ("", ".", "..", "/") for part in rel_parts):
        raise StudyFenceRefused("invalid staged study entry path")
    staged_bytes = _read_regular_under_root(
        manifest_dir,
        rel_parts,
        label=label,
        anchored=anchored,
        require_existing=True,
    )
    assert staged_bytes is not None
    return anchored, staged_bytes


def read_study_or_staged_file(
    raw_path: str,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path | None = None,
    label: str = "file input",
    allow_core: bool = True,
) -> tuple[Path, bytes]:
    """Read a validated study input from the broker's host stage or via O_NOFOLLOW."""
    staged = _read_staged_study_file(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=allow_core,
    )
    if staged is not None:
        return staged
    return read_study_file(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=allow_core,
    )


def read_optional_study_or_staged_file(
    raw_path: str,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path | None = None,
    label: str = "file input",
    allow_core: bool = True,
) -> tuple[Path, bytes | None]:
    """Read a study input when it exists; return ``(anchored, None)`` only if missing."""
    staged = _read_staged_study_file(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=allow_core,
    )
    if staged is not None:
        return staged
    real_root, anchored, rel_parts = _match_study_anchor(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=allow_core,
    )
    data = _read_regular_under_root(
        real_root,
        rel_parts,
        label=label,
        anchored=anchored,
        require_existing=False,
    )
    return anchored, data


def walk_payload_paths(
    obj: object,
    *,
    on_path: Callable[[str, str], None],
) -> None:
    """Traverse a JSON payload and invoke ``on_path(path, key)`` for external input path keys."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in EXTERNAL_INPUT_PATH_KEYS:
                if isinstance(value, str):
                    on_path(value, str(key))
                elif isinstance(value, (list, tuple)):
                    for item in value:
                        if isinstance(item, str):
                            on_path(item, str(key))
                        elif item is not None:
                            raise StudyFenceRefused(f"study broker: {key} paths must be strings")
                elif value is not None:
                    raise StudyFenceRefused(f"study broker: {key} path must be a string")
            else:
                walk_payload_paths(value, on_path=on_path)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            walk_payload_paths(item, on_path=on_path)


def read_study_json_file(
    raw_path: str,
    *,
    core_root: Path,
    scratch_dir: Path | None,
    cwd: Path,
    label: str,
) -> str:
    """Validate and decode a UTF-8 JSON study input file via O_NOFOLLOW descriptors."""
    anchored, content = read_study_file(
        raw_path,
        core_root=core_root,
        scratch_dir=scratch_dir,
        cwd=cwd,
        label=label,
        allow_core=True,
        max_bytes=MAX_STUDY_JSON_BYTES,
    )
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StudyFenceRefused(f"study broker: cannot decode {label} {anchored}: {exc}") from exc


class RequestInputStager:
    """Copy validated study input files into a host-only immutable request dir."""

    def __init__(
        self,
        *,
        core_root: Path,
        scratch_dir: Path | None,
        cwd: Path,
        stage_dir: Path,
    ) -> None:
        self.core_root = core_root
        self.scratch_dir = scratch_dir
        self.cwd = cwd
        self.stage_dir = guard_tool_output_path(stage_dir, repo_root=core_root, allow_existing_dir=True)
        self.entries: dict[str, str] = {}

    def stage_path(self, raw_path: str, *, label: str, allow_core: bool = True) -> Path:
        anchored, data = read_optional_study_or_staged_file(
            raw_path,
            core_root=self.core_root,
            scratch_dir=self.scratch_dir,
            cwd=self.cwd,
            label=label,
            allow_core=allow_core,
        )
        if data is None:
            return anchored
        key = str(anchored)
        if key in self.entries:
            return anchored
        idx = len(self.entries)
        subdir = self.stage_dir / f"f{idx}"
        subdir.mkdir(mode=0o700)
        leaf_name = anchored.name or "input"
        staged_file = subdir / path_segment(leaf_name)
        fd = os.open(
            staged_file,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o400,
        )
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        self.entries[key] = f"f{idx}/{leaf_name}"
        return anchored

    def stage_payload_paths(self, obj: object) -> None:
        def _collect(raw_path: str, key: str) -> None:
            self.stage_path(raw_path, label=key, allow_core=True)

        walk_payload_paths(obj, on_path=_collect)

    def manifest_env(self) -> dict[str, str]:
        if not self.entries:
            return {}
        manifest_path = self.stage_dir / "manifest.json"
        fd = os.open(
            manifest_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o400,
        )
        payload = json.dumps({"entries": self.entries}, ensure_ascii=False).encode("utf-8")
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
        return {STUDY_STAGED_MANIFEST_ENV: str(manifest_path)}


def _open_local_parent_dir_fd(
    parent: Path,
    *,
    mkdir_parents: bool,
    scratch_dir: Path | None,
) -> int:
    lex_parent = Path(os.path.abspath(parent))
    if scratch_dir is not None:
        real_scratch = Path(os.path.realpath(scratch_dir))
        matched = find_real_ancestor(lex_parent, real_scratch)
        if matched is None:
            raise OSError(
                errno.EACCES,
                f"Refusing output outside study scratch ($LOS_SCRATCH_DIR={real_scratch})",
                str(parent),
            )
        _anc, rel_parts = matched
        if any(part in ("", ".", "..") for part in rel_parts):
            raise OSError(errno.EINVAL, "Refusing invalid local output directory", str(parent))
        base_path: Path = real_scratch
        tail_parts: tuple[str, ...] = rel_parts
    else:
        probe = lex_parent
        missing: list[str] = []
        while True:
            try:
                os.lstat(probe)
                break
            except FileNotFoundError:
                if probe.parent == probe:
                    raise
                missing.append(probe.name)
                probe = probe.parent
        for anc in (probe, *probe.parents):
            if anc.parent == anc:
                break
            if len(anc.parts) == 2 and anc.parts[1] in ("var", "tmp", "etc"):
                continue
            if anc.is_symlink():
                raise OSError(errno.ELOOP, "Refusing symlink parent target", str(anc))
        base_path = probe
        tail_parts = tuple(reversed(missing))

    if tail_parts and not mkdir_parents:
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), str(parent))

    return open_dir_chain_nofollow(base_path, tail_parts, create_missing=mkdir_parents)


def write_local_output_file(
    target_text: str,
    content: str,
    *,
    mkdir_parents: bool = False,
    exclusive: bool = False,
    scratch_dir: Path | None = None,
) -> None:
    """Write mediated broker output locally without following symlinks or hardlinks."""
    target = Path(target_text).expanduser()
    if target.name in ("", ".", ".."):
        raise OSError(errno.EINVAL, "Refusing invalid local output target", target_text)
    if target.is_symlink():
        raise OSError(errno.ELOOP, "Refusing symlink local output target", str(target))
    effective_scratch = scratch_dir
    if effective_scratch is None:
        scratch_env = os.environ.get(STUDY_FENCE_SCRATCH_ENV, "").strip()
        if scratch_env:
            effective_scratch = Path(scratch_env)
    if effective_scratch is None:
        try:
            target = guard_tool_output_path(target)
        except WriteScopeError as exc:
            raise OSError(errno.EACCES, str(exc), target_text) from exc
    parent_fd = _open_local_parent_dir_fd(
        target.parent,
        mkdir_parents=mkdir_parents,
        scratch_dir=effective_scratch,
    )
    file_flags = os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW
    if exclusive:
        file_flags |= os.O_EXCL
    if hasattr(os, "O_CLOEXEC"):
        file_flags |= os.O_CLOEXEC
    try:
        fd = call_dir_fd_op(
            functools.partial(os.open, target.name, file_flags, 0o644, dir_fd=parent_fd)
        )
    finally:
        os.close(parent_fd)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise OSError(errno.EINVAL, "Refusing non-regular local output target", str(target))
        if st.st_nlink > 1:
            raise OSError(errno.EMLINK, "Refusing hardlinked local output target", str(target))
        if not exclusive:
            os.ftruncate(fd, 0)
        handle = os.fdopen(fd, "w", encoding="utf-8")
    except BaseException:
        os.close(fd)
        raise
    with handle:
        handle.write(content)

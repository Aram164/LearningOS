"""Integrity of the external materials tree against its checksummed manifest.

``materials/`` is ~1.9 GB living outside every Git repository (CLAUDE.md §11),
and hundreds of ``material://`` references resolve into it. Without a record of
what belongs there, the repository cannot distinguish an unmounted drive from
actual data loss — both simply look like "the file isn't there".

``records/materials-manifest.yaml`` (built by ``tools/materials_manifest.py``)
is that record. The checks below are deliberately graded:

    referenced by a canonical record, and gone   ERROR    a link now lies
    referenced, but never inventoried            ERROR    unrestorable
    inventory drift nothing points at            warning  rebuild the manifest
    whole tree absent                            warning  drive is offline

Only presence and size are compared here — hashing 1.9 GB does not belong in a
pre-commit hook. ``python tools/materials_manifest.py --deep`` verifies content.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import yaml

from ..loading.yamlio import UniqueKeySafeLoader
from ..pathing import PathBoundaryError, read_text_inside, resolve_symlinks_inside
from .common import CANONICAL_TREES, _in_garden, _in_quarantine

# Material filenames legitimately contain spaces ("unser skript.pdf"), so a
# whitespace-delimited pattern silently truncates them. Delimited forms are
# matched first and removed from the text; only the remainder is scanned for
# bare URIs, which are whitespace-delimited by necessity.
MATERIAL_URI_DELIMITED = (
    re.compile(r"`material://([^`\n]+)`"),        # `material://…` code span
    re.compile(r"\]\(material://([^)\n]+)\)"),    # [text](material://…) link
    # `vault_path: material://…` — for a field whose whole contract is "one
    # material URI", the YAML scalar runs to the end of its line and is exactly
    # as delimited as a code span. Without this the bare pattern below truncates
    # at the first space and reports the reference missing under a filename
    # nobody wrote: a deck recorded as `lecture-slides/VL 01-Introduction.pdf`
    # fails as `lecture-slides/VL`.
    #
    # Only the pure carrier fields qualify. `locator` is prose that may *open*
    # with a URI and continue past it ("…/Velleman.pdf (569 pp); located by …"),
    # so it keeps the whitespace-delimited reading — the ambiguity is real and
    # is resolved by the field's contract, not by guessing at the value.
    re.compile(
        r"^[^\S\n]*(?:-[^\S\n]*)?(?:vault_path|material|material_uri|material_path)"
        r"[^\S\n]*:[^\S\n]*[\"']?material://([^\"'\n]+?)[\"']?[^\S\n]*$",
        re.MULTILINE,
    ),
)
MATERIAL_URI_BARE = re.compile(r"material://([^\s`)\]\"'<>,;]+)")

#: Report at most this many individual paths before collapsing to a count.
_MAX_LISTED = 10


class ChecksMaterials:
    """Mixed into Validator; see rules/core.py."""

    def check_materials(self):
        repo = self.repo
        manifest_path = repo.root / "records" / "materials-manifest.yaml"
        if not manifest_path.exists():
            self.warn("MATERIALS-MANIFEST",
                      "no records/materials-manifest.yaml — the external materials "
                      "tree has no durable inventory, so data loss there is "
                      "undetectable; build it with "
                      "`python tools/materials_manifest.py --build`",
                      "records/")
            return

        try:
            manifest = yaml.load(
                read_text_inside(repo.root, manifest_path),
                Loader=UniqueKeySafeLoader,
            ) or {}
        except (OSError, PathBoundaryError, yaml.YAMLError) as exc:
            self.err("MATERIALS-MANIFEST", f"unparseable manifest: {exc}",
                     "records/materials-manifest.yaml")
            return

        if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), dict):
            self.err(
                "MATERIALS-MANIFEST",
                "manifest must be a mapping with a 'files' mapping",
                "records/materials-manifest.yaml",
            )
            return

        recorded: dict = manifest["files"]

        # Two coordinate systems meet here. The manifest indexes the PHYSICAL
        # topic tree (Books/analysis/…), because that is what a backup restores.
        # `material://` URIs are id-based (source-<id>/…) and resolve through the
        # materials/.flat/ symlink farm. Referenced URIs must therefore be
        # translated to physical paths before the inventory can be consulted.
        physical = repo.learningos_root / "materials"
        if physical.is_symlink() or not physical.is_dir():
            self.warn("MATERIALS-OFFLINE",
                      f"materials tree not mounted at {physical} — "
                      f"{len(recorded)} inventoried file(s) unverified this run "
                      "(the manifest still records what belongs there)",
                      "records/materials-manifest.yaml")
            return

        referenced: set[str] = set()
        unresolvable: list[str] = []
        physical_form = 0
        for uri in sorted(self._referenced_materials()):
            resolved = self._physical_key(uri, physical)
            if resolved is None:
                unresolvable.append(uri)
                continue
            key, form = resolved
            if key is not None:
                referenced.add(key)
            physical_form += form == "physical"

        if physical_form:
            self.warn("MATERIAL-URI-FORM",
                      f"{physical_form} material:// reference(s) name the physical "
                      "topic path instead of the id-based material://source-<id>/… "
                      "form; they resolve today but will break silently the next "
                      "time build_materials_tree.py re-homes that folder",
                      "records/materials-manifest.yaml")

        for uri in unresolvable[:_MAX_LISTED]:
            self.err("MATERIAL-MISSING",
                     f"'material://{uri}' does not resolve to a file in the "
                     "materials tree (a missing file, or a stale .flat/ symlink "
                     "— rebuild with `python tools/build_materials_tree.py`)",
                     "records/materials-manifest.yaml")
        if len(unresolvable) > _MAX_LISTED:
            self.err("MATERIAL-MISSING",
                     f"… and {len(unresolvable) - _MAX_LISTED} further "
                     "unresolvable material reference(s)",
                     "records/materials-manifest.yaml")

        # A reference the inventory never captured cannot be restored from any
        # backup, because no backup was ever known to need it.
        # macOS hands back decomposed filenames (NFD), so the inventory — built
        # by walking the tree — records "Übung 02 .pdf" with a combining
        # diaeresis, while a URI copied out of a record or the projection is
        # composed (NFC). APFS resolves both to the same file, so the reference
        # verifies and then fails to match its own inventory entry: the same
        # name, reported as never inventoried. Compare on one normal form.
        unregistered = sorted(
            {_nfc(key) for key in referenced} - {_nfc(key) for key in recorded}
        )
        for rel in unregistered[:_MAX_LISTED]:
            self.err("MATERIAL-UNREGISTERED",
                     f"'{rel}' is referenced but absent from the materials "
                     "manifest — rebuild it "
                     "(`python tools/materials_manifest.py --build`)",
                     "records/materials-manifest.yaml")
        if len(unregistered) > _MAX_LISTED:
            self.err("MATERIAL-UNREGISTERED",
                     f"… and {len(unregistered) - _MAX_LISTED} further "
                     "referenced material(s) missing from the manifest",
                     "records/materials-manifest.yaml")

        missing_referenced: list[str] = []
        drifted: list[str] = []
        missing_unreferenced = 0
        for rel, want in recorded.items():
            if not isinstance(rel, str) or not isinstance(want, dict):
                self.err(
                    "MATERIALS-MANIFEST",
                    f"invalid inventory row: {rel!r}",
                    "records/materials-manifest.yaml",
                )
                continue
            try:
                path = resolve_symlinks_inside(physical, physical / rel)
            except PathBoundaryError:
                path = None
            if path is None or not path.is_file():
                if rel in referenced:
                    missing_referenced.append(rel)
                else:
                    missing_unreferenced += 1
                continue
            if path.stat().st_size != want.get("size"):
                drifted.append(rel)

        for rel in sorted(missing_referenced)[:_MAX_LISTED]:
            self.err("MATERIAL-MISSING",
                     f"'material://{rel}' is referenced by a canonical record "
                     "but is gone from the materials tree",
                     "records/materials-manifest.yaml")
        if len(missing_referenced) > _MAX_LISTED:
            self.err("MATERIAL-MISSING",
                     f"… and {len(missing_referenced) - _MAX_LISTED} further "
                     "referenced material(s) gone from disk",
                     "records/materials-manifest.yaml")

        if missing_unreferenced:
            self.warn("MATERIALS-DRIFT",
                      f"{missing_unreferenced} inventoried file(s) no longer on "
                      "disk and referenced by nothing — rebuild the manifest if "
                      "the removal was deliberate",
                      "records/materials-manifest.yaml")
        if drifted:
            shown = ", ".join(sorted(drifted)[:3])
            self.warn("MATERIALS-DRIFT",
                      f"{len(drifted)} inventoried file(s) changed size since the "
                      f"manifest was captured ({shown}"
                      f"{', …' if len(drifted) > 3 else ''}) — verify with "
                      "`python tools/materials_manifest.py --deep`",
                      "records/materials-manifest.yaml")

    # ------------------------------------------------------------------ util
    def _physical_key(self, uri_path: str, physical: Path) -> tuple[str | None, str] | None:
        """Translate a ``material://`` payload into (manifest key, uri form).

        The key is None for a folder-level reference — ``source.material`` names
        a whole source directory (``material://source-amls-ss26-lectures``), and
        the manifest indexes files. Resolving proves the directory is there,
        which is the whole integrity claim for that form.

        Canonical form is id-based — ``material://source-<id>/…`` resolved
        through the ``materials/.flat/`` symlink farm. A minority of references
        name the physical topic path directly; those are resolved too (this
        check is about data integrity, not URI style) but counted, because they
        bypass the indirection that lets the physical tree be reorganised.

        Returns None when the URI resolves to nothing — itself the finding.
        """
        for base, form in ((self.repo.materials_root, "id"), (physical, "physical")):
            try:
                resolved = resolve_symlinks_inside(physical, base / uri_path)
                relative = resolved.relative_to(physical)
                if resolved.is_dir():
                    return None, form
                if not resolved.is_file():
                    continue
                return relative.as_posix(), form
            except (OSError, PathBoundaryError, ValueError):
                continue
        return None

    def _referenced_materials(self) -> set[str]:
        """Every ``material://`` target named anywhere in the canonical trees.

        A regex sweep rather than a field walk: material URIs legitimately appear
        in source records, stage resources, note frontmatter and prose links, and
        a new carrier field should not silently escape the integrity check.
        """
        root = self.repo.root
        found: set[str] = set()
        for tree in CANONICAL_TREES:
            base = root / tree
            if not base.is_dir():
                continue
            for path in base.rglob("*"):
                if path.suffix.lower() not in {".md", ".yaml", ".yml"}:
                    continue
                if not path.is_file():
                    continue
                if _in_garden(root, path) or _in_quarantine(root, path):
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
                if "material://" not in text:
                    continue
                found |= _uris_in(text)
        found.discard("")
        return found


def _uris_in(text: str) -> set[str]:
    """Every material:// payload in one document, delimited forms first."""
    found: set[str] = set()
    for pattern in MATERIAL_URI_DELIMITED:
        for target in pattern.findall(text):
            found.add(_normalise(target))
        text = pattern.sub(" ", text)
    for target in MATERIAL_URI_BARE.findall(text):
        found.add(_normalise(target.rstrip(".,;:")))
    return found


def _nfc(value: str) -> str:
    """One Unicode normal form for filename comparison.

    Composed, because that is what a record written by a human or emitted by
    the projection carries; the decomposed spelling only ever arrives from a
    filesystem walk.
    """
    return unicodedata.normalize("NFC", str(value))


def _normalise(target: str) -> str:
    """Strip a trailing anchor/fragment and normalise separators."""
    return Path(target.split("#", 1)[0].strip()).as_posix().strip("/")

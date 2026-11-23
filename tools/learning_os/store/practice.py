"""The practice verification sidecar and its effective status (P6 step 34).

`knowledge/practice-index.yaml` is the only place verification lives; the
canonical note remains the only source of prompt and solution text, and no
solution text is ever copied into the sidecar. A stored status is a claim:
the effective status is recomputed from the current item bytes, the pinned
source files and the recorded proofs, and any gap makes the item ineligible
regardless of what the row says.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from learning_os.domain.failures import WriteRefused
from learning_os.domain.practice import (
    PracticeItem,
    content_sha256,
    extract_items,
)
from learning_os.domain.relations import binding_file_state
from learning_os.store.contracts.json_schema import load_standalone_validator
from learning_os.store.loading.yamlio import UniqueKeySafeLoader

SIDECAR_REL = "knowledge/practice-index.yaml"
ARTIFACT_ID = "registry-practice-index"
CHECKED_STATUSES = ("cross-checked", "source-matched", "confirmed")
METHOD_FOR_STATUS = {
    "source-matched": "official-source",
    "cross-checked": "independent-solve",
    "confirmed": "explicit-review",
}


def sidecar_path(root: Path) -> Path:
    return root / SIDECAR_REL


def load_sidecar(root: Path) -> dict:
    path = sidecar_path(root)
    if not path.exists():
        return {"items": []}
    data = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeySafeLoader)
    if not isinstance(data, dict) or not isinstance(data.get("items"), list):
        raise WriteRefused("practice index must be a mapping with an items list")
    validator = load_standalone_validator(
        root / "system/schema/practice-index.schema.json", format_checker=True)
    errors = sorted(validator.iter_errors(data), key=str)
    if errors:
        raise WriteRefused(f"practice-index: {errors[0].message}")
    return data


def dump_sidecar(data: dict) -> str:
    rows = sorted(data["items"], key=lambda row: row["item_id"].encode("utf-8"))
    return yaml.safe_dump({"items": rows}, sort_keys=False, allow_unicode=True)


def row_for(data: dict, item_id: str) -> dict | None:
    for row in data["items"]:
        if row["item_id"] == item_id:
            return row
    return None


@dataclass
class EffectiveItem:
    item: PracticeItem
    row: dict | None
    status: str
    reasons: list[str] = field(default_factory=list)

    @property
    def checked(self) -> bool:
        """Eligible as a verified item (export applies its own extra gates)."""
        return self.status in CHECKED_STATUSES and not self.reasons


def _proof_ok(row: dict) -> str | None:
    """Why the row's proofs do not support its status, or None."""
    status = row["status"]
    if status in ("unverified", "disputed"):
        return None
    method = METHOD_FOR_STATUS.get(status)
    proofs = [p for p in row.get("verifications") or [] if p.get("method") == method]
    if not proofs:
        return "missing proof"
    proof = proofs[-1]
    if status == "source-matched" and not proof.get("source_binding"):
        return "source-matched proof has no source binding"
    if status == "cross-checked" and not proof.get("comparison_sha256"):
        return "cross-checked proof has no comparison digest"
    return None


def effective_item(repo, note, item: PracticeItem) -> EffectiveItem:
    """One extracted item against its stored row, recomputed honestly."""
    data = load_sidecar(repo.root)
    row = row_for(data, item.item_id)
    if row is None:
        return EffectiveItem(item=item, row=None, status="unverified")
    reasons: list[str] = []
    current = content_sha256(item.item_id, item.prompt, item.solution)
    if row["content_sha256"] != current:
        reasons.append("content changed since verification")
    for binding in row.get("source_bindings") or []:
        if binding_file_state(repo.root, repo.materials_root, binding) != "ok":
            reasons.append("source file missing or changed")
            break
    proof_problem = _proof_ok(row)
    if proof_problem:
        reasons.append(proof_problem)
    status = row["status"]
    if reasons and status in CHECKED_STATUSES:
        status = "unverified"
    return EffectiveItem(item=item, row=row, status=status, reasons=reasons)


def note_items(repo, note) -> tuple[list[EffectiveItem], list[str]]:
    """(effective items, diagnostic reasons) for one canonical note."""
    extraction = extract_items(note.id, note.meta.get("role"), note.body)
    diagnostics = [f"{d.label or note.id}: {d.reason}" for d in extraction.diagnostics]
    return [effective_item(repo, note, item) for item in extraction.items], diagnostics


def verified_binding(repo, binding: dict) -> str | None:
    """Why a proposed source binding cannot be admitted, or None.

    Known source, current pinned digest, physical page bounds, and — when a
    quote is carried — the quote verbatim on that page (open item 2, via the
    existing span machinery: `pdf_page_text` over the pinned bytes).
    """
    if binding.get("source_id") not in repo.sources:
        return "binding names an unknown source"
    if binding_file_state(repo.root, repo.materials_root, binding) != "ok":
        return "binding file is missing or its digest changed"
    quote = (binding.get("quote") or "").strip()
    if not quote:
        return None
    rel = str(binding.get("material_relpath", ""))
    path = repo.materials_root / rel
    try:
        from learning_os.store.materials.pdf_text import pdf_page_text, pdf_reader

        reader = pdf_reader(path.read_bytes())
        if not 1 <= int(binding["page"]) <= len(reader.pages):
            return "binding page is outside the pinned file"
        page_text = pdf_page_text(reader, int(binding["page"]))
    except Exception as exc:  # extraction failure refuses, never passes
        return f"binding page could not be read: {exc}"
    from learning_os.domain.relations import normalize_quote

    if normalize_quote(quote) not in normalize_quote(page_text):
        return "quote does not appear verbatim on the pinned page"
    return None

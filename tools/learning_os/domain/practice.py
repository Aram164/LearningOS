"""Deterministic practice-item extraction (P6 step 33).

Lives in the domain layer so the store (sidecar eligibility) and the
derive projection can both parse without a layer violation.

Only `exercise-bank` and `mock-exam` notes yield items, and only in the four
dialects the saved X3 parser exercised (`parse_practice.py`): labeled details
with a Solution header, labeled details with an answer header, a mock-exam
question section with a separately keyed answer section, and timed/optional
exam keys. Item IDs are `<note-id>#<label>`; duplicate labels, ambiguous
pairings, orphan answers and unsupported markup produce deterministic
diagnostics and stay ineligible. There is no ordinal fallback and no
wholesale note conversion.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field

PRACTICE_ROLES = ("exercise-bank", "mock-exam")
LABEL = r"[A-Z]+[1-9][0-9]*"
_KEY_DIALECTS = {
    "# ANSWER KEY": "mock-keyed",
    "## Solutions and marking guide": "timed-exam",
}

_BOLD = re.compile(rf"^\*\*({LABEL})(?=[.)\s])", re.MULTILINE)
_AML_KEY = re.compile(rf"^(?:#{{2,4}}\s+|\*\*)({LABEL})(?=[.)\s])", re.MULTILINE)
_TIMED = re.compile(r"^### (Q[1-5])(?:\.| solution)", re.MULTILINE)
_FOLLOWUP_Q = re.compile(r"^([1-7])\. \*\*", re.MULTILINE)
_FOLLOWUP_A = re.compile(r"^([1-7])\. ", re.MULTILINE)
_DETAILS = re.compile(
    r"<details>\s*<summary>(solution|answer)</summary>\s*(.*?)\s*</details>",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class PracticeItem:
    item_id: str
    note_id: str
    label: str
    prompt: str
    solution: str
    kind: str  # 'flashcard' | 'worked'
    dialect: str


@dataclass(frozen=True)
class PracticeDiagnostic:
    note_id: str
    label: str | None
    reason: str


@dataclass
class Extraction:
    items: list[PracticeItem] = field(default_factory=list)
    diagnostics: list[PracticeDiagnostic] = field(default_factory=list)

    @property
    def eligible(self) -> bool:
        return not self.diagnostics


def normalize_field(text: str) -> str:
    """NFC, LF endings, outer whitespace trimmed; interior preserved."""
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n")).strip()


def content_sha256(item_id: str, prompt: str, solution: str) -> str:
    """The sidecar hash recipe (step 34): canonical JSON array, no spaces."""
    payload = json.dumps(
        [item_id, normalize_field(prompt), normalize_field(solution)],
        ensure_ascii=False, separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _kind(prompt: str, solution: str) -> str:
    collapsed_prompt = " ".join(normalize_field(prompt).split())
    collapsed_solution = " ".join(normalize_field(solution).split())
    return "flashcard" if "\n" not in normalize_field(prompt) \
        and "\n" not in normalize_field(solution) \
        and collapsed_prompt and collapsed_solution else "worked"


def _split_blocks(text: str, pattern: re.Pattern[str], prefix: str = "") -> dict[str, str]:
    matches = list(pattern.finditer(text))
    result: dict[str, str] = {}
    for i, match in enumerate(matches):
        label = prefix + match.group(1)
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = re.split(r"^#{1,2} |^---\s*$", text[match.start():end],
                         maxsplit=1, flags=re.MULTILINE)[0]
        result[label] = block.strip()
    return result


def _label_counts(text: str, pattern: re.Pattern[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for match in pattern.finditer(text):
        counts[match.group(1)] = counts.get(match.group(1), 0) + 1
    return counts


def _join_pairs(note_id: str, dialect: str,
                questions: dict[str, str], solutions: dict[str, str],
                out: Extraction) -> None:
    for label in sorted(set(questions) | set(solutions)):
        if label not in questions:
            out.diagnostics.append(PracticeDiagnostic(
                note_id, label, "orphan answer with no question"))
            continue
        if label not in solutions:
            out.diagnostics.append(PracticeDiagnostic(
                note_id, label, "question with no keyed answer"))
            continue
        prompt, solution = questions[label], solutions[label]
        if not prompt.strip() or not solution.strip():
            out.diagnostics.append(PracticeDiagnostic(
                note_id, label, "empty prompt or solution"))
            continue
        out.items.append(PracticeItem(
            item_id=f"{note_id}#{label}", note_id=note_id, label=label,
            prompt=prompt.strip(), solution=solution.strip(),
            kind=_kind(prompt, solution), dialect=dialect))


def _details(note_id: str, text: str, out: Extraction) -> None:
    counts = _label_counts(text, _BOLD)
    blocks = _split_blocks(text, _BOLD)
    for label, count in sorted(counts.items()):
        if count > 1:
            out.diagnostics.append(PracticeDiagnostic(
                note_id, label, "duplicate label"))
    for label, block in sorted(blocks.items()):
        if counts.get(label, 0) > 1:
            continue
        matches = list(_DETAILS.finditer(block))
        if not matches:
            if "[open]" not in block.splitlines()[0]:
                out.diagnostics.append(PracticeDiagnostic(
                    note_id, label, "labeled item has no details answer"))
            continue
        if len(matches) != 1:
            out.diagnostics.append(PracticeDiagnostic(note_id, label, "multiple details answers"))
            continue
        match = matches[0]
        prompt = block[:match.start()].strip()
        solution = match.group(2).strip()
        if not prompt or not solution or "<details>" in prompt:
            out.diagnostics.append(PracticeDiagnostic(
                note_id, label, "malformed question or key"))
            continue
        dialect = ("details-solution" if match.group(1).lower() == "solution"
                   else "details-answer")
        out.items.append(PracticeItem(
            item_id=f"{note_id}#{label}", note_id=note_id, label=label,
            prompt=prompt, solution=solution,
            kind=_kind(prompt, solution), dialect=dialect))


def _unique_blocks(note_id: str, text: str, pattern: re.Pattern[str],
                   out: Extraction, prefix: str = "") -> dict[str, str]:
    blocks = _split_blocks(text, pattern, prefix)
    for label, count in _label_counts(text, pattern).items():
        if count > 1:
            out.diagnostics.append(PracticeDiagnostic(note_id, prefix + label, "duplicate label"))
            blocks.pop(prefix + label)
    return blocks


def _aml(note_id: str, text: str, out: Extraction) -> None:
    before, after = text.split("# ANSWER KEY", 1)
    _join_pairs(note_id, "mock-keyed",
                _unique_blocks(note_id, before, _AML_KEY, out),
                _unique_blocks(note_id, after, _AML_KEY, out), out)


def _icop(note_id: str, text: str, out: Extraction) -> None:
    before, after = text.split("## Solutions and marking guide", 1)
    timed, optional, follow = before.partition("## Optional examiner follow-ups")
    scored, follow_key, sketches = after.partition("## Follow-up solution sketches")
    if bool(optional) != bool(follow_key):
        out.diagnostics.append(PracticeDiagnostic(note_id, None, "incomplete optional exam sections"))
        return
    questions = {**_unique_blocks(note_id, timed, _TIMED, out),
                 **_unique_blocks(note_id, follow, _FOLLOWUP_Q, out, "F")}
    solutions = {**_unique_blocks(note_id, scored, _TIMED, out),
                 **_unique_blocks(note_id, sketches, _FOLLOWUP_A, out, "F")}
    _join_pairs(note_id, "timed-exam", questions, solutions, out)


def extract_items(note_id: str, role: str | None, body: str) -> Extraction:
    """Extract one note's items; roles outside the practice set yield none."""
    out = Extraction()
    if role not in PRACTICE_ROLES:
        return out
    text = body or ""
    key_dialects = {_KEY_DIALECTS[line] for line in text.splitlines()
                    if line in _KEY_DIALECTS}
    if len(key_dialects) > 1:
        out.diagnostics.append(PracticeDiagnostic(note_id, None, "multiple key formats"))
    elif key_dialects == {"mock-keyed"}:
        _aml(note_id, text, out)
    elif key_dialects == {"timed-exam"}:
        _icop(note_id, text, out)
    elif _BOLD.search(text):
        _details(note_id, text, out)
    else:
        out.diagnostics.append(PracticeDiagnostic(
            note_id, None, "unsupported markup"))
    out.items.sort(key=lambda item: item.item_id.encode("utf-8"))
    out.diagnostics.sort(key=lambda d: (d.label or "", d.reason))
    return out

"""The contract gates: what this repository stores, and what it publishes.

Two different contracts with two different consumers, checked here together
because they fail for the same kind of reason — a shape changed and nothing
recorded that it had.


Every record schema is ``additionalProperties: false`` and no canonical record
carries a version, so editing a schema silently redefines what "valid" means for
data already on disk. Nothing recorded that the meaning had changed, which makes
the question "what format was this note written under, and what brings it
forward?" unanswerable a few years later.

``system/contracts/data-contract.yaml`` records the format version and a
fingerprint over the record schemas. This check compares the two on every run,
so a schema edit cannot land without a deliberate decision about existing data.
See tools/schema_contract.py for the reasoning and the bump procedure.
"""

from __future__ import annotations

import re

from ..contracts import data_contract

_LIVING_CONTRACT_DOCS = (
    "README.md",
    "system/OPERATOR.md",
    "system/CLAUDE.md",
    "system/WORKFLOWS.md",
    "system/ACCEPTANCE-TESTS.md",
    "system/contracts/manifest-contract.yaml",
    "tools/learning_os/commands/query.py",
)

# Historical ADRs and the data-contract history may name the versions that
# existed at an event. Living operator instructions must not: copied current
# versions became false repeatedly while every executable contract stayed green.
_STATIC_CONTRACT_VERSION = re.compile(
    r"\bmanifest(?:\s+contract)?\s+v\d+\b"
    r"|data-contract\.yaml`?\s+v\d+\b"
    r"|\(currently\s+v\d+\)",
    re.IGNORECASE,
)


class ChecksContract:
    """Mixed into Validator; see rules/core.py."""

    def check_data_contract(self):
        root = self.repo.root
        contract_path = root / "system" / "contracts" / "data-contract.yaml"
        schema_dir = root / "system" / "schema"
        if not schema_dir.is_dir():
            return

        if not contract_path.exists():
            self.warn("SCHEMA-CONTRACT-MISSING",
                      "no system/contracts/data-contract.yaml — the record "
                      "schemas have no declared version, so a schema change "
                      "cannot be distinguished from the format it replaced; "
                      "declare it with `python tools/schema_contract.py --bump "
                      "--note 'baseline'`",
                      "system/contracts/")
            return

        ok, message = data_contract.check(schema_dir, contract_path)
        if not ok:
            # One error, multi-line: the message names the exact next step.
            self.err("SCHEMA-CONTRACT-DRIFT", message.replace("\n", " "),
                     "system/contracts/data-contract.yaml")

    def check_manifest_contract(self):
        """The published projection has a declared version, and it is readable.

        Deliberately shallow. Proving the manifest still *matches* the contract
        means building it — too slow for a pre-commit hook, and already enforced
        where it belongs: `build_manifest` refuses to publish a drifted shape,
        so every generate, every `los.py --json`, and the whole test suite hit
        it. What is worth checking cheaply on every run is that the declaration
        itself has not gone missing or unparseable, because that is the one
        failure mode which would turn enforcement off everywhere at once.
        """
        from ..contracts.manifest_contract import ManifestContractError, load_contract

        try:
            load_contract(self.repo.root)
        except ManifestContractError as exc:
            self.err("MANIFEST-CONTRACT-UNREADABLE", str(exc).replace("\n", " "),
                     "system/contracts/manifest-contract.yaml")

    def check_perimeter(self):
        """What may exist at the two levels above this repository.

        ADR-014 declared the umbrella's shape; nothing enforced it, and the
        level is in no git index, so three loose books accumulated there
        unseen. Severity comes from the checker rather than being fixed here:
        an undeclared path is an error, while a stray already recorded in
        `pending_disposition` is a warning — the umbrella has no version
        control, so every disposition there is irreversible and belongs to the
        operator, not to a validation run.
        """
        from ..contracts import perimeter

        for issue in perimeter.check(self.repo.root):
            code = f"PERIMETER-{issue.code}"
            # Written as two explicit calls rather than one through a bound
            # name. `tests/test_contract_register.py` reads this source to
            # prove an `error` contract still reports errors, and a checker
            # whose severity is only decidable at runtime cannot be checked
            # that way — which would quietly reopen the hole this register was
            # built to close.
            if issue.severity == "E":
                self.err(code, issue.message, issue.path)
            else:
                self.warn(code, issue.message, issue.path)

    def check_tree_contract(self):
        """The directory skeleton on disk, and the prose that renders it.

        ARCHITECTURE §3.2 is a projection of the contract, so a documented tree
        that disagrees with disk is not a thing that can be true here — the
        block is generated. What remains checkable is the other direction: a
        directory nobody declared, and a block somebody hand-edited.
        """
        from ..contracts import tree_contract

        for issue in tree_contract.check(self.repo.root):
            code = f"TREE-{issue.code}"
            if issue.severity == "E":
                self.err(code, issue.message, issue.path)
            else:
                self.warn(code, issue.message, issue.path)

    def check_normative_corpus(self):
        """Every document under system/ is classified, and retirement is visible.

        The corpus grew to ~7,800 lines with nothing saying which parts of it
        bind (CRITIQUE-POINTS §3). Errors rather than warnings, because the
        failure mode is an agent reading a retired rule as current — which is
        indistinguishable from the rule being wrong.
        """
        from ..contracts import normative_corpus

        for issue in normative_corpus.check(self.repo.root):
            self.err(f"NORMATIVE-CORPUS-{issue.code}", issue.message, issue.path)

    def check_contract_documentation(self):
        """Living instructions point to contract owners instead of copying versions."""
        root = self.repo.root
        for relative in _LIVING_CONTRACT_DOCS:
            path = root / relative
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError as exc:
                self.err("CONTRACT-DOC-UNREADABLE", str(exc), relative)
                continue
            if relative == "system/contracts/manifest-contract.yaml":
                # The leading comments are living instructions; YAML history
                # below them is dated evidence and may name historical versions.
                header: list[str] = []
                for line in text.splitlines():
                    if line and not line.startswith("#"):
                        break
                    header.append(line)
                text = "\n".join(header)
            match = _STATIC_CONTRACT_VERSION.search(text)
            if match is None:
                continue
            line = text.count("\n", 0, match.start()) + 1
            self.err(
                "CONTRACT-DOC-STATIC-VERSION",
                f"living instructions copy '{match.group(0)}' on line {line}; "
                "point to the producer-owned contract file instead, so the "
                "documentation cannot lag the executable declaration",
                relative,
            )

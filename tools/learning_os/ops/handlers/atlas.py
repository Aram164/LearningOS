"""Atlas-area converted handlers (PLAN D4)."""

from __future__ import annotations

import json
from datetime import UTC

from jsonschema import Draft202012Validator, FormatChecker

from learning_os import abilities, observations
from learning_os.contracts.gateway import current_gateway_request
from learning_os.contracts.json_schema import validate_contract
from learning_os.domain.failures import WriteRefused
from learning_os.domain.suggest import suggest
from learning_os.learning_runtime import runtime_path
from learning_os.ops._legacy_plumbing import _snapshot
from learning_os.ops.context import OpContext
from learning_os.ops.proposal import Result, TransactionProposal
from learning_os.ops.registry import register
from learning_os.transactions import parse_expected_revisions


def _dumps_ability_context(payload: dict) -> str:
    """The exact ability-context encoder: compact, unsorted, unescaped."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _dumps_candidate(payload: dict) -> str:
    """The exact candidate encoder: default separators, escaped."""
    return json.dumps(payload)


def _on_commit_refused(errors: list) -> list[str]:
    """The exact commit-refusal lines: the first twelve engine issues, verbatim."""
    return list(errors[:12])


@register("ability.context", kind="porcelain")
def ability_context(ctx: OpContext, req: dict) -> Result:
    """Snapshot-bound ability horizon and focused expansion."""
    root = ctx.root
    try:
        if not 1 <= req["limit"] <= 50:
            raise WriteRefused(
                "ability-context limit must be 1..50",
                site=f"{ctx.operation}.bad-limit",
                gateway_message="los: ability-context limit must be 1..50",
                exit_code=2,
            )
        brief = req.get("brief", False)
        section = req.get("section")
        if brief and not req["ability_id"]:
            raise WriteRefused(
                "ability-context --brief needs a named ability",
                site=f"{ctx.operation}.brief-needs-id",
                gateway_message=(
                    "los: ability-context --brief needs a named ability"
                ),
                exit_code=2,
            )
        if section and not req["ability_id"]:
            raise WriteRefused(
                "ability-context --section needs a named ability",
                site=f"{ctx.operation}.section-needs-id",
                gateway_message=(
                    "los: ability-context --section needs a named ability"
                ),
                exit_code=2,
            )
        if brief and section:
            raise WriteRefused(
                "ability-context takes --brief or --section evidence, not both",
                site=f"{ctx.operation}.brief-and-section",
                gateway_message=(
                    "los: ability-context takes --brief or --section "
                    "evidence, not both"
                ),
                exit_code=2,
            )
        offset = req.get("offset", 0) or 0
        if offset < 0:
            raise WriteRefused(
                "ability-context offset must be nonnegative",
                site=f"{ctx.operation}.negative-offset",
                gateway_message=(
                    "los: ability-context offset must be nonnegative"
                ),
                exit_code=2,
            )
        if req["ability_id"] and offset and not section:
            raise WriteRefused(
                "ability-context --offset pages the global horizon or "
                "--section evidence, not a focused ability",
                site=f"{ctx.operation}.offset-needs-section",
                gateway_message=(
                    "los: ability-context --offset pages the global horizon "
                    "or --section evidence, not a focused ability"
                ),
                exit_code=2,
            )
        if brief and req["limit"] != 12:
            # 12 is the parser default: an explicit window on a single
            # summary is silently meaningless, so it refuses instead.
            raise WriteRefused(
                "ability-context --brief is one summary; page evidence with "
                "--section evidence",
                site=f"{ctx.operation}.brief-with-limit",
                gateway_message=(
                    "los: ability-context --brief is one summary; page "
                    "evidence with --section evidence"
                ),
                exit_code=2,
            )
        if offset and not req["expected_snapshot"]:
            raise WriteRefused(
                "continuation requires --expected-snapshot from the previous "
                "response",
                site=f"{ctx.operation}.offset-needs-snapshot",
                gateway_message=(
                    "los: continuation requires --expected-snapshot from the "
                    "previous response"
                ),
                exit_code=2,
            )
        snapshot = _snapshot(root, req["expected_snapshot"])
        repo = ctx.repo()
        if repo.parse_failures:
            raise WriteRefused(
                "ability-context refuses unreadable canonical records",
                site=f"{ctx.operation}.unreadable-records",
                gateway_message=(
                    "los: ability-context refuses unreadable canonical records"
                ),
                exit_code=2,
            )
        payload = abilities.ability_context(
            repo, focus=req["ability_id"], limit=req["limit"],
            offset=offset, brief=brief, section=section, snapshot=snapshot)
        if (req["ability_id"] is not None
                and req["ability_id"] not in repo.abilities
                and payload.get("state") == "unmapped"):
            # An unknown identity, not a known-but-unmapped ability.
            # The unmapped shape stays what the UI reads (its decoder
            # tolerates extra keys); the flag and suggestions say this
            # is a mistyped id and where to look next.
            payload["known_identity"] = False
            payload["suggestions"] = suggest(req["ability_id"], repo.abilities)
        result = {"schema_version": 1, "snapshot_id": snapshot,
                  "contract": "ability-context-v1", **payload}
        validate_contract(root, "ability-context.schema.json", result)
        rows = payload.get("abilities", [])
        if "ability" in payload:
            rows = [payload["ability"]]
        for row in rows:
            reasons, codes = row.get("reasons"), row.get("reason_codes")
            if not isinstance(reasons, list) or not isinstance(codes, list) \
                    or len(reasons) != len(codes):
                raise WriteRefused(
                    "ability-context reason_codes must be parallel to reasons",
                    site=f"{ctx.operation}.reasons-not-parallel",
                    gateway_message=(
                        "los: ability-context reason_codes must be parallel "
                        "to reasons"
                    ),
                    exit_code=2,
                )
        _snapshot(root, snapshot)
        return Result(
            {"schema_version": 1, "snapshot_id": snapshot, **result},
            json_dumps=_dumps_ability_context,
        )
    except (OSError, ValueError) as exc:
        raise WriteRefused(
            str(exc),
            gateway_message=f"los: {exc}",
            exit_code=2,
        ) from exc


@register("ability.candidate.append", kind="command")
def ability_candidate_append(ctx: OpContext, req: dict) -> Result:
    """Capture a tentative cross-ability connection; it never grants credit."""
    root = ctx.root
    if current_gateway_request() is None:
        raise WriteRefused(
            "ability candidates require GatewayEnvelopeV2",
            site=f"{ctx.operation}.gateway-required",
            gateway_message="los: ability candidates require GatewayEnvelopeV2",
            exit_code=2,
        )
    ctx.require_snapshot(req["expected_snapshot"])
    repo = ctx.repo()
    if (req["from_ability"] not in repo.abilities
            or req["to_ability"] not in repo.abilities
            or req["from_ability"] == req["to_ability"]
            or repo.abilities[req["from_ability"]].get("lifecycle") == "retired"
            or repo.abilities[req["to_ability"]].get("lifecycle") == "retired"):
        raise WriteRefused(
            "candidate endpoints must be two active abilities",
            site=f"{ctx.operation}.bad-endpoints",
            gateway_message=(
                "los: candidate endpoints must be two active abilities"
            ),
            exit_code=2,
        )
    if not req["source_ref"].startswith(
            ("conversation://", "note://", "project://")):
        raise WriteRefused(
            "candidate source-ref must identify the discovery",
            site=f"{ctx.operation}.bad-source-ref",
            gateway_message=(
                "los: candidate source-ref must identify the discovery"
            ),
            exit_code=2,
        )
    try:
        abilities.read_ability_candidates(repo)
        path = runtime_path(root, root / "knowledge/ability-candidates.jsonl")
        row = {
            "id": "ability-candidate-" + observations.new_hex(),
            "from": req["from_ability"], "to": req["to_ability"],
            "kind": req["kind"], "carries": req["carries"],
            "changes": req["changes"], "conditions": list(req["condition"]),
            "source_ref": req["source_ref"],
            "created_at": observations.now().astimezone(UTC).isoformat(),
            "state": "candidate",
        }
        schema = json.loads(
            (root / "system/schema/ability-candidate.schema.json").read_text())
        errors = sorted(Draft202012Validator(
            schema, format_checker=FormatChecker()).iter_errors(row), key=str)
        if errors:
            raise WriteRefused(
                f"ability candidate: {errors[0].message}",
                site=f"{ctx.operation}.candidate-schema-refused",
                gateway_message=f"los: ability candidate: {errors[0].message}",
                exit_code=2,
            )
        old = path.read_text(encoding="utf-8") if path.exists() else ""
        new = old + ("\n" if old and not old.endswith("\n") else "")
        new += json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n"
        try:
            expected_revisions = parse_expected_revisions(
                req.get("expected_revision"))
        except ValueError as exc:
            raise WriteRefused(
                str(exc),
                site=f"{ctx.operation}.bad-expected-revision",
                gateway_message=f"los: {exc}",
                exit_code=2,
            ) from exc
        return Result(
            {"ok": True, "candidate_id": row["id"]},
            proposal=TransactionProposal(
                capability="ability.candidate.append",
                writes={path: new},
                artifact_ids=["ability-candidates"],
                expected_revisions=expected_revisions,
            ),
            on_commit_refused=_on_commit_refused,
            json_dumps=_dumps_candidate,
        )
    except (OSError, ValueError) as exc:
        raise WriteRefused(
            str(exc),
            gateway_message=f"los: {exc}",
            exit_code=2,
        ) from exc

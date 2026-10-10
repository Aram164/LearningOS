"""Atlas-area converted handlers (PLAN D4)."""

from __future__ import annotations

import json

from learning_os import abilities
from learning_os.contracts.json_schema import validate_contract
from learning_os.domain.failures import WriteRefused
from learning_os.domain.suggest import suggest
from learning_os.ops._legacy_plumbing import _snapshot
from learning_os.ops.context import OpContext
from learning_os.ops.proposal import Result
from learning_os.ops.registry import register


def _dumps_ability_context(payload: dict) -> str:
    """The exact ability-context encoder: compact, unsorted, unescaped."""
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


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

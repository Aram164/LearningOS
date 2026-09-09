import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from learning_os.commands.support import (
    WriteRefused,
    _operator_lock,
    _root,
    _write_transaction,
)

def cmd_observation_append(args) -> int:
    """Append a learner observation to a workspace ledger."""
    root = _root(args)
    ws_dir = root / "work" / "active" / args.workspace
    if not ws_dir.is_dir():
        raise WriteRefused(f"Workspace {args.workspace} does not exist.")

    ledger_path = ws_dir / "observations.jsonl"
    
    with _operator_lock(root):
        # Read existing ledger if any
        content = ""
        if ledger_path.exists():
            content = ledger_path.read_text(encoding="utf-8")
        
        # Build observation
        obs = {
            "requirement": args.requirement,
            "activity": args.activity,
            "result": args.result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if args.assistance:
            obs["assistance"] = args.assistance
        if args.tags:
            obs["evidence_tags"] = args.tags.split(",")
        if args.context:
            obs["context"] = args.context
            
        new_line = json.dumps(obs) + "\n"
        new_content = content + new_line
        
        ledger_path.write_text(new_content, encoding="utf-8")
        
        print(f"Appended observation to {args.workspace}. (volatile state)")
        return 0

def register(subparsers):
    p = subparsers.add_parser("observation", help="Manage learner observations.")
    sp = p.add_subparsers(dest="obs_cmd", required=True)
    
    append_p = sp.add_parser("append", help="Append an observation.")
    append_p.add_argument("--workspace", required=True, help="Workspace ID (e.g. workspace-m2-exam-prep)")
    append_p.add_argument("--requirement", required=True, help="Requirement ID")
    append_p.add_argument("--activity", required=True, help="Activity ID or description")
    append_p.add_argument("--result", required=True, help="Result (e.g. correct, incorrect)")
    append_p.add_argument("--assistance", help="Assistance provided")
    append_p.add_argument("--tags", help="Comma separated evidence tags")
    append_p.add_argument("--context", help="Session or temporal context")
    append_p.set_defaults(func=cmd_observation_append)

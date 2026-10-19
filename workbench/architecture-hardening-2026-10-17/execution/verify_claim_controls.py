"""Focused source controls; this is not the C1 paired milestone gate."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
CORE=HERE/'candidate/repository'
commands=[
 ('types',['make','typecheck']),
 ('lint',['.venv/bin/ruff','check','tools','tests']),
 ('layers',['.venv/bin/lint-imports','--no-cache']),
 ('reachability',['.venv/bin/python','tools/code_reachability.py']),
 ('validation',['.venv/bin/python','tools/validate.py','--compact']),
 ('warning-baseline',['.venv/bin/python','tools/warning_baseline.py','--check']),
 ('ui-contract',['npm','--prefix','../obsidian-ui','run','contract:check']),
]
target=HERE/'receipts/claim-controls-details'
target.mkdir(exist_ok=False)
results={}
for name,argv in commands:
    proc=subprocess.run(argv,cwd=CORE,text=True,capture_output=True)
    (target/(name+'.stdout')).write_text(proc.stdout)
    (target/(name+'.stderr')).write_text(proc.stderr)
    results[name]={'exit':proc.returncode,'command':argv}
    print(name,proc.returncode,flush=True)
(target/'results.json').write_text(json.dumps(results,indent=2,sort_keys=True)+'\n')
print(json.dumps(results,indent=2),flush=True)
raise SystemExit(int(any(row['exit'] for row in results.values())))

"""Run all existing procedure transcripts and retain per-file audit evidence."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE = HERE / 'candidate/repository'
sys.path[:0] = [str(CORE / 'tools'), str(CORE / 'tests')]
import test_procedures as procedures


def main():
    target = HERE / 'receipts' / (sys.argv[1] if len(sys.argv) > 1 else 'claim-procedure-details')
    target.mkdir(exist_ok=False)
    os.environ['LOS_ARCH_AUDIT_DIR'] = str(target / 'population')
    os.environ['LOS_SITE_WITNESS_FILE'] = str(target / 'sites.jsonl')
    (target / 'sites.jsonl').touch()
    results = {}
    scrut = procedures._scrut_bin()
    for path in sorted((CORE / 'system/procedures').glob('*.md')):
        log = target / (path.stem + '.audit.jsonl')
        env = procedures._procedure_child_env(log_path=log, token='procedure-' + uuid.uuid4().hex)
        proc = subprocess.run([str(scrut), 'test', str(path)], cwd=CORE, env=env, text=True,
                              capture_output=True, timeout=600)
        (target / (path.stem + '.stdout')).write_text(proc.stdout)
        (target / (path.stem + '.stderr')).write_text(proc.stderr)
        error = None
        if proc.returncode == 0:
            try:
                procedures.check_render_purity_error(proc.stdout + proc.stderr)
                procedures._check_procedure_audit(path.name, log)
                procedures._persist_procedure_audit(path.stem, log)
            except Exception as exc:
                error = str(exc)
        results[path.name] = {'exit': proc.returncode, 'audit_error': error}
        print(path.name, proc.returncode, error or '', flush=True)
    (target / 'results.json').write_text(json.dumps(results, indent=2, sort_keys=True)+'\n')
    bad = {name: row for name, row in results.items() if row['exit'] or row['audit_error']}
    print(json.dumps({'transcripts': len(results), 'failed': bad}, indent=2), flush=True)
    return int(bool(bad))


if __name__ == '__main__':
    raise SystemExit(main())

"""Alternate baseline/candidate reads over the retained captured world."""
from __future__ import annotations

import io
import json
import math
import shutil
import statistics
import subprocess
import tarfile
import time
from pathlib import Path

from run_receipt import CORE, HERE

ORIGINAL = HERE.parents[2] / 'repository'
TARGET = HERE / 'performance/claim-reads'
PYTHON = CORE / '.venv/bin/python'


def main():
    TARGET.mkdir(parents=True, exist_ok=False)
    baseline = TARGET / 'baseline/repository'
    baseline.mkdir(parents=True)
    archive = subprocess.check_output(['git', 'archive', 'HEAD'], cwd=ORIGINAL)
    with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
        stream.extractall(baseline, filter='data')
    shutil.copytree(HERE / 'world/data', baseline, dirs_exist_ok=True)
    (baseline.parent / 'materials').symlink_to(HERE.parents[2] / 'materials', target_is_directory=True)
    unit = 'unit-m2-sad-l04'
    import yaml
    source_map = yaml.safe_load((CORE / 'curriculum/modules/module-hu-m2-statistik-analysis/source-map.yaml').read_text())
    routes = [r['id'] for s in source_map['sources'] for r in s.get('unit_routes', [])
              if r.get('unit_id') == unit and r.get('id')]
    ledger = yaml.safe_load((CORE / 'operations/transactions/lineage.yaml').read_text())
    recorded = [rid for rid in routes if 'covers:' + rid in ledger['records']]
    routes = recorded or routes
    if not routes:
        raise RuntimeError('captured target route is unavailable')
    commands = {
        'brief': ['plan-edit-context', unit, '--brief'],
        'route': ['plan-edit-context', unit, '--route-id', routes[0]],
        'dossier': ['dossier', unit, '--json'],
    }
    roots = {'baseline': baseline, 'candidate': CORE}
    samples = {}
    for name, args in commands.items():
        samples[name] = {'baseline': [], 'candidate': []}
        for warmup in range(2):
            for root in roots.values():
                proc = subprocess.run([str(PYTHON), str(root / 'tools/los.py'), '--root', str(root), *args], capture_output=True)
                if proc.returncode:
                    raise RuntimeError(proc.stderr.decode() + proc.stdout.decode())
        for index in range(20):
            order = ['baseline', 'candidate'] if index % 2 == 0 else ['candidate', 'baseline']
            for label in order:
                root = roots[label]
                started = time.perf_counter()
                proc = subprocess.run([str(PYTHON), str(root / 'tools/los.py'), '--root', str(root), *args], capture_output=True)
                elapsed = time.perf_counter() - started
                if proc.returncode:
                    raise RuntimeError(proc.stderr.decode() + proc.stdout.decode())
                samples[name][label].append({'seconds': elapsed, 'stdout_bytes': len(proc.stdout), 'stderr_bytes': len(proc.stderr)})
        print(name, 'complete', flush=True)
    summary = {}
    for name, variants in samples.items():
        rows = {}
        for label, measurements in variants.items():
            times = sorted(row['seconds'] for row in measurements)
            rows[label] = {'median_seconds': statistics.median(times), 'p95_seconds': times[math.ceil(len(times)*.95)-1],
                           'stdout_bytes': sorted({row['stdout_bytes'] for row in measurements})}
        rows['allowed_increase_seconds'] = max(rows['baseline']['p95_seconds']*.15, .1)
        rows['p95_increase_seconds'] = rows['candidate']['p95_seconds']-rows['baseline']['p95_seconds']
        rows['budget_met'] = rows['p95_increase_seconds'] <= rows['allowed_increase_seconds']
        summary[name] = rows
    report = {'commands': commands, 'samples': samples, 'summary': summary,
              'world': str(HERE / 'world'), 'baseline_source': str(baseline), 'candidate_source': str(CORE)}
    (TARGET / 'results.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()

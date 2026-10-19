"""Read-only real-material anchoring checks; excerpts stay outside Core."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE = HERE / 'candidate/repository'
sys.path.insert(0, str(CORE / 'tools'))

import yaml
from learning_os.app.claim_admission import admit_evidence, read_material_manifest
from learning_os.domain.verbatim import Quote, normalise
from learning_os.store.loader import load_repo
from learning_os.store.materials.anchors import AnchorReader, RouteMaterial
from learning_os.store.materials.pdf_text import pdf_page_text, pdf_reader
from learning_os.store.revisions import load_revisions
from learning_os.store.fingerprint import canonical_fingerprint


def main():
    repo = load_repo(CORE)
    mid, uid, rid = 'module-hu-m2-statistik-analysis', 'unit-m2-analysis-ch02', 'route-an-ch02-analysisskript'
    source = next(s for s in repo.module_source_maps[mid]['sources']
                  if any(isinstance(r, dict) and r.get('id') == rid for r in s.get('unit_routes', [])))
    row = next(r for r in source['unit_routes'] if isinstance(r, dict) and r.get('id') == rid)
    route = RouteMaterial(rid, source['source_id'], row.get('locator', ''), row.get('vault_path', ''), row.get('url', ''))
    reader = AnchorReader(repo, read_material_manifest(CORE))
    files = reader.materials(route).files
    file = next(f for f in files if f.material_uri.endswith('unser skript.pdf'))
    snapshot = reader.snapshot(file)
    page = pdf_page_text(pdf_reader(snapshot.content), 26)
    excerpt = ' '.join(page.split())[:280].strip()
    if len(normalise(excerpt)) < 40:
        raise RuntimeError('the observed place has no admissible short quotation')
    proof = reader.verify_quote(route, Quote(file.material_uri, excerpt, page=26))
    evidence = {'claim_id': 'covers:' + rid, 'evidence': [
        {'kind': 'quote', 'ref': file.material_uri, 'page': 26, 'text': excerpt}]}
    (HERE / 'receipts/real-material-external-evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+'\n')
    changes = {'locator': row['locator'] + '; geprüft: PDF p. 26'}
    before = canonical_fingerprint(CORE)
    results = {}
    for label in ['genuine', 'wrong-file', 'no-evidence']:
        args = [str(CORE / '.venv/bin/python'), str(CORE / 'tools/los.py'), '--root', str(CORE),
                'route-patch', uid, rid, '--changes', json.dumps(changes), '--check']
        if label != 'no-evidence':
            item = json.loads(json.dumps(evidence))
            if label == 'wrong-file':
                item['evidence'][0]['ref'] = 'material://source-analysis-skript/ana_inf_serie05.pdf'
            args += ['--claim-evidence', json.dumps(item, ensure_ascii=False)]
        started = time.perf_counter()
        proc = subprocess.run(args, cwd=CORE, capture_output=True, text=True)
        elapsed = time.perf_counter()-started
        (HERE / f'receipts/real-material-{label}.stdout').write_text(proc.stdout)
        (HERE / f'receipts/real-material-{label}.stderr').write_text(proc.stderr)
        results[label] = {'exit': proc.returncode, 'seconds': elapsed, 'stdout_bytes': len(proc.stdout)}
        if label == 'genuine':
            if proc.returncode:
                raise RuntimeError(proc.stderr + proc.stdout)
            report = json.loads(proc.stdout)
            assert report['claim_anchors'][0]['classification'] == 'anchored'
        elif label == 'wrong-file':
            assert proc.returncode == 1 and 'wrong file' in proc.stderr
        else:
            assert proc.returncode == 1 and 'without claim evidence' in proc.stderr
    assert canonical_fingerprint(CORE) == before
    shared = AnchorReader(repo, read_material_manifest(CORE))
    revisions = load_revisions(CORE)
    started = time.perf_counter()
    for index in range(20):
        admitted = admit_evidence(CORE, shared, f'covers:timing-{index}', route, route,
                                  evidence['evidence'], {}, revisions, positive=True)
        assert admitted.classification == 'anchored'
    elapsed = time.perf_counter()-started
    report = {'material': file.material_uri, 'material_sha256': snapshot.sha256,
              'manifest_path': snapshot.manifest_path, 'page': 26, 'quote_sha256': proof.quote_sha256,
              'canonical_unchanged': True, 'preflights': results,
              'twenty_shared_file_claims_seconds': elapsed, 'per_claim_seconds': elapsed/20,
              'unique_physical_files': 1, 'unique_pages': 1}
    (HERE / 'receipts/CLAIM-real-material-summary.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

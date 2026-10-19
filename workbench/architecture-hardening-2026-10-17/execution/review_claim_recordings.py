"""Retain every regeneration delta and flag outcome/authored-effect changes."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
BEFORE = HERE / 'recording-before-claim-slice'
AFTER = HERE / 'candidate/repository/tests/scenarios/recorded'
MISSING = {'missing': True}


def changes(old, new, path=()):
    if old == new:
        return []
    if isinstance(old, dict) and isinstance(new, dict):
        return [row for key in sorted(old.keys() | new.keys())
                for row in changes(old.get(key, MISSING), new.get(key, MISSING), path + (key,))]
    if isinstance(old, list) and isinstance(new, list) and len(old) == len(new):
        return [row for i, (a, b) in enumerate(zip(old, new, strict=True))
                for row in changes(a, b, path + (str(i),))]
    return [{'path': '.'.join(path), 'before': old, 'after': new}]


def steps(row):
    return row.get('steps', [row])


def main():
    results = {}
    added = []
    unexpected = []
    fields = Counter()
    for operation in sorted(path.name for path in BEFORE.iterdir() if path.is_dir()):
        for path in sorted((AFTER / operation).glob('*.json')):
            before_path = BEFORE / path.relative_to(AFTER)
            if not before_path.exists():
                added.append(str(path.relative_to(AFTER)))
                continue
            old, new = json.loads(before_path.read_text()), json.loads(path.read_text())
            delta = changes(old, new)
            if not delta:
                continue
            key = str(path.relative_to(AFTER))
            results[key] = delta
            for item in delta:
                fields[item['path']] += 1
            left, right = steps(old), steps(new)
            if len(left) != len(right):
                unexpected.append({'case': key, 'reason': 'step count changed'})
            for index, (a, b) in enumerate(zip(left, right)):
                for field in ['exit', 'outcome', 'canonical_changed']:
                    if a.get(field) != b.get(field):
                        unexpected.append({'case': key, 'step': index, 'field': field,
                                           'before': a.get(field), 'after': b.get(field)})
    report = {'changed_cases': len(results), 'added_cases': added,
              'outcome_or_authored_effect_differences': unexpected,
              'field_frequencies': dict(fields.most_common()), 'deltas': results}
    (HERE / 'receipts/CLAIM-recording-review.json').write_text(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False)+'\n')
    print(json.dumps({key: report[key] for key in ['changed_cases', 'added_cases', 'outcome_or_authored_effect_differences']}, indent=2))
    print('Full structured deltas retained outside candidate.')


if __name__ == '__main__':
    main()

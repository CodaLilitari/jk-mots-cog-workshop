"""Check original examples against both bundled retail name tables.

This is lexical availability validation, not compilation or game execution.
Run from any directory with Python 3; no network or third-party modules used.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json


def main():
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--skill', type=Path, default=here.parent / 'skill' / 'jk-mots-cog-workflow')
    ap.add_argument('--output', type=Path, help='Optional JSON receipt; contains relative example paths only')
    args = ap.parse_args()
    inspector = args.skill / 'scripts' / 'inspect_cog.py'
    spec = importlib.util.spec_from_file_location('cog_inspector', inspector)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = []
    for path in sorted(here.glob('*/*.cog')):
        for target in ('jk', 'mots'):
            expected = 0 if path.parent.name in ('shared', target) else 1
            result = module.inspect(path, target)
            assert result['has_symbols'] and result['has_code'], path.name
            assert not result['unknown_declarations'], path.name
            assert not result['messages_absent_from_target_registry'], path.name
            assert not result['warnings'], path.name
            assert result['availability_findings'] == expected, (path.name, target, result)
            if expected:
                expected_name = 'getcurinvweapon' if path.parent.name == 'jk' else 'getcurinvweapon2'
                assert [x['name'] for x in result['calls_absent_from_target_registry']] == [expected_name]
            rows.append({
                'path': path.relative_to(here.parent).as_posix(),
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'target': target,
                'intended_target': expected == 0,
                'absent_calls': [x['name'] for x in result['calls_absent_from_target_registry']],
                'absent_messages': result['messages_absent_from_target_registry'],
                'expected_findings': expected,
                'actual_findings': result['availability_findings'],
                'passed': True,
            })
    assert len(rows) == 12, 'The release expects six examples checked on two targets each'
    report = {
        'scope': 'Native/message spelling availability only; no syntax, loading, VM, retail or multiplayer execution.',
        'checks': len(rows),
        'intended_target_checks': sum(x['intended_target'] for x in rows),
        'expected_cross_target_rejections': sum(not x['intended_target'] for x in rows),
        'inspector_sha256': hashlib.sha256(inspector.read_bytes()).hexdigest(),
        'cases': rows,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'cases'}, indent=2))


if __name__ == '__main__':
    main()

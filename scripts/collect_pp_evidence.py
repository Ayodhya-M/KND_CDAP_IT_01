"""Run real checks and preserve reproducible progress-presentation evidence."""
import argparse
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs/evidence/2026-10-27'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('suite', choices=['eesi', 'backend', 'frontend'])
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    backend_python = ROOT / 'backend/.venv/Scripts/python.exe'
    if args.suite == 'frontend':
        command = ['cmd.exe', '/d', '/c', 'npm.cmd', 'run', 'build']
        directory = ROOT / 'frontend'
    else:
        selected = ['tests/test_eesi.py', 'tests/test_hies_data.py', 'tests/test_eesi_real.py'] if args.suite == 'eesi' else ['tests']
        command = [str(backend_python), '-m', 'pytest', *selected, '-v', '--tb=short', '--color=no',
                   f'--junitxml={OUTPUT / (args.suite + ".xml")}']
        directory = ROOT / 'backend'
    started = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    completed = subprocess.run(command, cwd=directory, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding='utf-8', errors='replace')
    (OUTPUT / f'{args.suite}.log').write_text(completed.stdout, encoding='utf-8')
    git = ['git', '-c', 'safe.directory=' + ROOT.as_posix()]
    revision = subprocess.check_output([*git, 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    branch = subprocess.check_output([*git, 'branch', '--show-current'], cwd=ROOT, text=True).strip()
    result = {'suite': args.suite, 'started_at': started.isoformat(), 'exit_code': completed.returncode,
              'revision': revision, 'branch': branch, 'command': command, 'scope': 'Software correctness, not empirical research validity.'}
    if args.suite != 'frontend':
        suites = ET.parse(OUTPUT / f'{args.suite}.xml').getroot()
        cases = list(suites.iter('testcase'))
        result.update(tests=len(cases), failures=len(list(suites.iter('failure'))),
                      errors=len(list(suites.iter('error'))), skipped=len(list(suites.iter('skipped'))))
    (OUTPUT / f'{args.suite}.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key not in ('command', 'scope')}))
    sys.exit(completed.returncode)


if __name__ == '__main__':
    main()

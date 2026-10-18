"""Reproduce PP1 calculation evidence without a database or web server."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'backend'))
from app.services.eesi import calculate, pilot_preview

root = Path(__file__).resolve().parents[1]
output = root / 'docs' / 'eesi' / 'pilot-evidence.json'
output.parent.mkdir(parents=True, exist_ok=True)
evidence = pilot_preview()
evidence['controlled_scenarios'] = [
    {'label': label, **calculate(salary, inflation, 107.635, 4.7)}
    for label, salary, inflation in [
        ('hand-worked midpoint', 50000, 32.6),
        ('lower salary, same economy', 25000, 32.6),
        ('higher salary, same economy', 100000, 32.6),
        ('higher inflation, same salary', 50000, 40),
    ]
]
output.write_text(json.dumps(evidence, indent=2), encoding='utf-8')
print(f'Wrote {output}: {len(evidence["rows"])} scores, {len(evidence["rejected"])} rejected')

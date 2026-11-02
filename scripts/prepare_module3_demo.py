"""Train and evaluate a local synthetic-only progress demonstration model."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'backend'))

import pandas as pd
from app.services.module3_export import build_pilot_export, FEATURE_COLUMNS, TARGET_COLUMN
from module3_ml.training import train_baseline
from module3_ml.evaluation import evaluate_heldout, write_evaluation_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--formula', choices=['economic', 'additive', 'interaction'], default='additive')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/module3_synthetic')
    args = parser.parse_args()
    destination = args.output
    if (destination / 'turnover_pipeline.joblib').exists():
        raise SystemExit('An artifact already exists here. Choose a new --output directory to preserve it.')
    rows = build_pilot_export(args.formula, employee_count=300)
    metadata = train_baseline(pd.DataFrame(rows), TARGET_COLUMN, FEATURE_COLUMNS, destination, eesi_column='EESI')
    metadata.update(dataset_kind='synthetic_pilot_only', source_rows=300,
                    source_sha256=hashlib.sha256((ROOT / 'pilot-data/module1_hr_pilot_300_employees.csv').read_bytes()).hexdigest())
    (destination / 'model_metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    report = evaluate_heldout(destination)
    report['limitations'].insert(0, 'Synthetic randomly generated attrition labels: metrics demonstrate software only, not real-world predictive validity.')
    write_evaluation_report(report, destination)
    print(json.dumps({'status': 'demo_ready', 'source_rows': 300, 'split': metadata['split'], 'eesi': metadata['eesi_integration']}))


if __name__ == '__main__':
    main()

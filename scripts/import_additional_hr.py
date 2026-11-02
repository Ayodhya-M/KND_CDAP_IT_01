"""Import only the supplied Sri Lanka synthetic workbook and prepare its demo model."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT))

from app.services.source_datasets import import_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workbook', type=Path, required=True)
    args = parser.parse_args()
    import pandas as pd
    notes = pd.read_excel(args.workbook, sheet_name='Read Me', header=None).astype(str)
    if 'AI-GENERATED SYNTHETIC' not in ' '.join(notes.to_numpy().ravel()).upper():
        raise ValueError('Workbook provenance changed; review before importing under the synthetic profile.')
    frame = pd.read_excel(args.workbook, sheet_name='50 Synthetic Records')
    if len(frame) != 50 or not frame['Country'].eq('Sri Lanka').all():
        raise ValueError('Expected the supplied 50 Sri Lanka synthetic scenarios.')
    results = [import_source('sl_synthetic', frame.to_dict(orient='records'), args.workbook.name,
        hashlib.sha256(args.workbook.read_bytes()).hexdigest(), len(frame))]
    output = ROOT / 'data/private/additional_sources_manifest.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps([{'id': result['id'], 'rows': result['record_count'], 'target': result['target'],
                       'eesi_available': result['eesi_available'], 'reused': result['reused']} for result in results]))


if __name__ == '__main__':
    main()

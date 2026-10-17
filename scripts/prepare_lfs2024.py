"""Usage: python scripts/prepare_lfs2024.py [--source path/to/official.csv]."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.services.eesi_real import build_real_summary

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--source", type=Path, default=ROOT / "data/private/lfs2024/source.csv")
args = parser.parse_args()
summary = build_real_summary(args.source, ROOT / "data/private/lfs2024/prepared.csv")
output = ROOT / "docs/eesi/lfs2024-aggregate.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(f"Prepared {summary['eligible_records']} employees from {summary['source_records']} respondents. Aggregate output: {output}")

"""Backend adapter for the separately testable Module 3 ML package."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ARTIFACT_DIRECTORY = PROJECT_ROOT / "artifacts" / "module3_synthetic"


def artifact_directory() -> Path:
    configured_path = os.getenv("MODULE3_ARTIFACT_DIR")
    return Path(configured_path) if configured_path else DEFAULT_ARTIFACT_DIRECTORY


def _metadata_path() -> Path:
    return artifact_directory() / "model_metadata.json"


def get_model_status() -> dict[str, Any]:
    metadata_path = _metadata_path()
    model_path = artifact_directory() / "turnover_pipeline.joblib"
    if not metadata_path.is_file() or not model_path.is_file():
        return {
            "model_available": False,
            "dataset_kind": "not_trained",
            "message": "No local Module 3 model artifact is available. Train a model before requesting predictions.",
        }
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return {
            "model_available": False,
            "dataset_kind": "invalid_artifact",
            "message": f"Module 3 metadata could not be read: {error}",
        }
    return {
        "model_available": True,
        "dataset_kind": "synthetic_pilot_only",
        "model_name": metadata.get("model_name"),
        "classes": metadata.get("classes", []),
        "feature_columns": metadata.get("feature_columns", []),
        "eesi_integration": metadata.get("eesi_integration", {}),
        'source_rows': metadata.get('source_rows'),
        'split': metadata.get('split'),
        "message": "Local synthetic-pilot model available. Outputs are technical evidence only.",
    }


def _prediction_function():
    root = str(PROJECT_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    from module3_ml.prediction import predict_employee

    return predict_employee


def predict_saved_model(record: dict[str, Any]) -> dict[str, Any]:
    validate_pilot_record(record)
    return _prediction_function()(record, artifact_directory())


def validate_pilot_record(record):
    """Reject invalid domain inputs before sklearn can impute or coerce them."""
    import math
    limits = {'Age': (14, 100), 'MonthlyIncome': (0, None), 'JobSatisfaction': (1, 4),
              'JobLevel': (1, 5), 'YearsAtCompany': (0, 100), 'EESI': (0, 100)}
    for field, (low, high) in limits.items():
        if field not in record:
            continue  # Saved feature contract handles absent/extra fields.
        value = record[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f'{field} must be a finite number.')
        if value < low or high is not None and value > high:
            raise ValueError(f'{field} is outside its valid range.')
        if field in ('Age', 'JobSatisfaction', 'JobLevel', 'YearsAtCompany') and int(value) != value:
            raise ValueError(f'{field} must be a whole number.')
    if 'OverTime' in record and record['OverTime'] not in ('Yes', 'No'):
        raise ValueError('OverTime must be Yes or No.')
    if 'Department' in record and (not isinstance(record['Department'], str) or not record['Department'].strip()):
        raise ValueError('Department is required.')


def load_evaluation_report() -> dict[str, Any]:
    report_path = artifact_directory() / "evaluation_report.json"
    if not report_path.is_file():
        raise FileNotFoundError("Evaluation report is unavailable. Run Module 3 evaluation after training.")
    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Evaluation report could not be read: {error}") from error

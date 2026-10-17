from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from .data import validate_training_data
from .exceptions import DataContractError
from .model import build_pipeline, save_artifact


def train_baseline(
    frame: pd.DataFrame,
    target_column: str,
    feature_columns: list[str],
    artifact_directory: str | Path,
    test_size: float = 0.2,
    random_seed: int = 42,
    eesi_column: str | None = None,
) -> dict:
    if not 0 < test_size < 1:
        raise DataContractError("test_size must be between 0 and 1.")
    diagnostics = validate_training_data(frame, target_column, feature_columns)
    if eesi_column and eesi_column not in feature_columns:
        raise DataContractError("EESI column must be included in feature columns when supplied.")

    clean_frame = frame.drop_duplicates().copy()
    if clean_frame[target_column].value_counts().min() < 2:
        raise DataContractError("Removing duplicate rows left too few examples for a stratified split.")
    features = clean_frame[feature_columns]
    target = clean_frame[target_column]
    try:
        train_features, test_features, train_target, test_target = train_test_split(
            features,
            target,
            test_size=test_size,
            random_state=random_seed,
            stratify=target,
        )
    except ValueError as error:
        raise DataContractError(
            f"Unable to create a stratified held-out split: {error}"
        ) from error

    pipeline = build_pipeline(train_features)
    pipeline.fit(train_features, train_target)
    artifact_path = Path(artifact_directory)
    heldout_frame = test_features.copy()
    heldout_frame[target_column] = test_target
    metadata = {
        "model_name": "LogisticRegression baseline",
        "model_configuration": {"max_iter": 1000, "random_state": 42},
        "target_column": target_column,
        "feature_columns": feature_columns,
        "classes": [str(value) for value in pipeline.named_steps["classifier"].classes_],
        "split": {
            "method": "stratified train/test split",
            "test_size": test_size,
            "random_seed": random_seed,
            "train_rows": int(len(train_features)),
            "heldout_rows": int(len(test_features)),
        },
        "eesi_integration": {
            "enabled": eesi_column is not None,
            "column": eesi_column,
            "status": "consumed as a supplied feature; Module 2 remains responsible for calculation",
            "formula_id": _single_metadata_value(clean_frame, "EESIFormulaId") if eesi_column else None,
            "formula_version": _single_metadata_value(clean_frame, "EESIFormulaVersion") if eesi_column else None,
        },
        "diagnostics": diagnostics,
    }
    save_artifact(pipeline, metadata, artifact_path)
    heldout_frame.to_csv(artifact_path / "heldout_test.csv", index=False)
    (artifact_path / "training_diagnostics.json").write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    return metadata


def _single_metadata_value(frame: pd.DataFrame, column: str) -> str | None:
    if column not in frame:
        return None
    values = frame[column].dropna().astype(str).unique().tolist()
    return values[0] if len(values) == 1 else None

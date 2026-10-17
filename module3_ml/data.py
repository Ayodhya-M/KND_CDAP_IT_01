from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pandas as pd

from .exceptions import DataContractError


def parse_feature_list(value: str) -> list[str]:
    features = [item.strip() for item in value.split(",") if item.strip()]
    if not features:
        raise DataContractError("At least one feature column must be supplied.")
    if len(features) != len(set(features)):
        raise DataContractError("Feature columns must not contain duplicates.")
    return features


def load_csv_dataset(dataset_path: str | Path) -> pd.DataFrame:
    path = Path(dataset_path)
    if not path.is_file():
        raise FileNotFoundError(
            f"Dataset not found: {path}. Supply an approved CSV file with --data."
        )
    try:
        return pd.read_csv(path)
    except (OSError, UnicodeDecodeError, pd.errors.ParserError) as error:
        raise DataContractError(f"Could not read CSV dataset '{path}': {error}") from error


def validate_training_data(
    frame: pd.DataFrame, target_column: str, feature_columns: Iterable[str]
) -> dict:
    features = list(feature_columns)
    missing_columns = [column for column in [target_column, *features] if column not in frame]
    if missing_columns:
        raise DataContractError(
            f"Dataset is missing required column(s): {', '.join(missing_columns)}."
        )
    if target_column in features:
        raise DataContractError("The target column cannot also be a predictor feature.")
    if frame.empty:
        raise DataContractError("Dataset contains no rows.")
    if frame[target_column].isna().any():
        raise DataContractError("Target column contains missing values; label these rows or remove them before training.")

    target_counts = frame[target_column].value_counts(dropna=False)
    if target_counts.size < 2:
        raise DataContractError("Target column must contain at least two classes for classification.")
    if target_counts.min() < 2:
        raise DataContractError("Every target class requires at least two rows for a stratified train/test split.")

    return {
        "rows": int(len(frame)),
        "columns": int(len(frame.columns)),
        "duplicate_rows": int(frame.duplicated().sum()),
        "missing_values_by_column": {
            column: int(count) for column, count in frame.isna().sum().items() if count
        },
        "data_types": {column: str(dtype) for column, dtype in frame.dtypes.items()},
        "target_distribution": {str(label): int(count) for label, count in target_counts.items()},
        "feature_columns": features,
        "target_column": target_column,
    }


def validate_prediction_record(record: dict, feature_columns: Iterable[str]) -> pd.DataFrame:
    if not isinstance(record, dict):
        raise DataContractError("Prediction input must be a JSON object.")
    features = list(feature_columns)
    missing_columns = [column for column in features if column not in record]
    unexpected_columns = sorted(set(record) - set(features))
    messages = []
    if missing_columns:
        messages.append(f"missing required field(s): {', '.join(missing_columns)}")
    if unexpected_columns:
        messages.append(f"unexpected field(s): {', '.join(unexpected_columns)}")
    if messages:
        raise DataContractError("Prediction input rejected: " + "; ".join(messages) + ".")
    return pd.DataFrame([{column: record[column] for column in features}])

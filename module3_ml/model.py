from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .exceptions import ModelArtifactError


MODEL_FILENAME = "turnover_pipeline.joblib"
METADATA_FILENAME = "model_metadata.json"


def build_pipeline(features: pd.DataFrame) -> Pipeline:
    numeric_columns = features.select_dtypes(include="number").columns.tolist()
    categorical_columns = [column for column in features.columns if column not in numeric_columns]
    transformers = []
    if numeric_columns:
        transformers.append(("numeric", Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]), numeric_columns))
    if categorical_columns:
        transformers.append(("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]), categorical_columns))
    if not transformers:
        raise ModelArtifactError("No usable feature columns were supplied.")
    return Pipeline([
        ("preprocessor", ColumnTransformer(transformers=transformers)),
        ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
    ])


def save_artifact(pipeline: Pipeline, metadata: dict, artifact_directory: str | Path) -> None:
    directory = Path(artifact_directory)
    directory.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, directory / MODEL_FILENAME)
    (directory / METADATA_FILENAME).write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def load_artifact(artifact_directory: str | Path) -> tuple[Pipeline, dict]:
    directory = Path(artifact_directory)
    model_path = directory / MODEL_FILENAME
    metadata_path = directory / METADATA_FILENAME
    if not model_path.is_file() or not metadata_path.is_file():
        raise ModelArtifactError(
            f"Model artifact is incomplete in '{directory}'. Run the training command first."
        )
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        pipeline = joblib.load(model_path)
    except (OSError, ValueError, TypeError) as error:
        raise ModelArtifactError(f"Could not load model artifact: {error}") from error
    return pipeline, metadata

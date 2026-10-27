from __future__ import annotations

from pathlib import Path

from .data import validate_prediction_record
from .model import load_artifact


def predict_employee(record: dict, artifact_directory: str | Path) -> dict:
    pipeline, metadata = load_artifact(artifact_directory)
    features = validate_prediction_record(record, metadata["feature_columns"])
    predicted_class = pipeline.predict(features)[0]
    probabilities = pipeline.predict_proba(features)[0]
    classes = [str(label) for label in pipeline.named_steps["classifier"].classes_]
    probability_by_class = {
        label: round(float(probability), 6) for label, probability in zip(classes, probabilities, strict=True)
    }
    return {
        "predicted_class": str(predicted_class),
        "class_probabilities": probability_by_class,
        "interpretation": "The predicted class is the model's estimated turnover label using the supplied employee features. It is not a retention recommendation.",
    }

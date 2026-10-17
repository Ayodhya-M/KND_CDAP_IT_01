from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

from .exceptions import DataContractError
from .model import load_artifact


def evaluate_heldout(artifact_directory: str | Path) -> dict:
    directory = Path(artifact_directory)
    pipeline, metadata = load_artifact(directory)
    heldout_path = directory / "heldout_test.csv"
    if not heldout_path.is_file():
        raise FileNotFoundError("Held-out test file is missing. Train the model before evaluating it.")
    heldout = pd.read_csv(heldout_path)
    target_column = metadata["target_column"]
    if target_column not in heldout:
        raise DataContractError("Held-out test data is missing the target column.")
    features = heldout[metadata["feature_columns"]]
    actual = heldout[target_column]
    predicted = pipeline.predict(features)
    classes = pipeline.named_steps["classifier"].classes_
    report = {
        "dataset_split": metadata["split"],
        "model_name": metadata["model_name"],
        "model_configuration": metadata["model_configuration"],
        "metrics": {
            "accuracy": float(accuracy_score(actual, predicted)),
            "precision_macro": float(precision_score(actual, predicted, average="macro", zero_division=0)),
            "recall_macro": float(recall_score(actual, predicted, average="macro", zero_division=0)),
            "f1_macro": float(f1_score(actual, predicted, average="macro", zero_division=0)),
        },
        "class_specific_results": classification_report(actual, predicted, output_dict=True, zero_division=0),
        "confusion_matrix": confusion_matrix(actual, predicted, labels=classes).tolist(),
        "confusion_matrix_labels": [str(label) for label in classes],
        "limitations": [
            "Results are valid only for the approved dataset and held-out split used for this run.",
            "No causal or retention recommendation should be inferred from this classifier.",
        ],
    }
    if len(classes) == 2:
        positive_index = 1
        probabilities = pipeline.predict_proba(features)[:, positive_index]
        try:
            report["metrics"]["roc_auc"] = float(roc_auc_score(actual, probabilities))
        except ValueError:
            report["metrics"]["roc_auc"] = None
            report["limitations"].append("ROC-AUC could not be calculated because the held-out set contains one class.")
    else:
        report["metrics"]["roc_auc"] = None
        report["limitations"].append("ROC-AUC is not reported for this multiclass baseline.")
    return report


def write_evaluation_report(report: dict, artifact_directory: str | Path) -> tuple[Path, Path]:
    directory = Path(artifact_directory)
    json_path = directory / "evaluation_report.json"
    markdown_path = directory / "evaluation_report.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    metrics = report["metrics"]
    metric_lines = "\n".join(f"- {name}: {value}" for name, value in metrics.items())
    markdown_path.write_text(
        "# Module 3 Evaluation Report\n\n"
        f"**Model:** {report['model_name']}\n\n"
        "## Held-out Split\n\n"
        f"- Method: {report['dataset_split']['method']}\n"
        f"- Training rows: {report['dataset_split']['train_rows']}\n"
        f"- Held-out rows: {report['dataset_split']['heldout_rows']}\n\n"
        "## Metrics\n\n"
        f"{metric_lines}\n\n"
        "## Confusion Matrix\n\n"
        f"Labels: {report['confusion_matrix_labels']}\n\n"
        f"{report['confusion_matrix']}\n\n"
        "## Limitations\n\n"
        + "\n".join(f"- {item}" for item in report["limitations"])
        + "\n",
        encoding="utf-8",
    )
    return json_path, markdown_path

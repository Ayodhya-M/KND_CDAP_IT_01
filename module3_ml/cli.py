from __future__ import annotations

import argparse
import json

from .data import load_csv_dataset, parse_feature_list
from .evaluation import evaluate_heldout, write_evaluation_report
from .exceptions import DataContractError, ModelArtifactError
from .prediction import predict_employee
from .training import train_baseline


def train_command(args: argparse.Namespace) -> None:
    frame = load_csv_dataset(args.data)
    metadata = train_baseline(
        frame=frame,
        target_column=args.target,
        feature_columns=parse_feature_list(args.features),
        artifact_directory=args.artifact_dir,
        test_size=args.test_size,
        random_seed=args.seed,
        eesi_column=args.eesi_column,
    )
    print(json.dumps({"status": "trained", "metadata": metadata}, indent=2))


def predict_command(args: argparse.Namespace) -> None:
    with open(args.record, encoding="utf-8") as input_file:
        record = json.load(input_file)
    print(json.dumps(predict_employee(record, args.artifact_dir), indent=2))


def evaluate_command(args: argparse.Namespace) -> None:
    report = evaluate_heldout(args.artifact_dir)
    json_path, markdown_path = write_evaluation_report(report, args.artifact_dir)
    print(json.dumps({"status": "evaluated", "report_json": str(json_path), "report_markdown": str(markdown_path), "metrics": report["metrics"]}, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Module 3 turnover prediction pipeline")
    commands = parser.add_subparsers(dest="command", required=True)
    train = commands.add_parser("train", help="Train a Logistic Regression baseline from an approved CSV")
    train.add_argument("--data", required=True, help="Approved CSV dataset path")
    train.add_argument("--target", required=True, help="Existing target column name")
    train.add_argument("--features", required=True, help="Comma-separated approved feature columns")
    train.add_argument("--artifact-dir", default="artifacts/module3", help="Local output directory; do not commit")
    train.add_argument("--test-size", type=float, default=0.2)
    train.add_argument("--seed", type=int, default=42)
    train.add_argument("--eesi-column", help="Optional supplied Module 2 EESI feature column")
    train.set_defaults(func=train_command)
    predict = commands.add_parser("predict", help="Predict a single employee from a JSON record")
    predict.add_argument("--artifact-dir", default="artifacts/module3")
    predict.add_argument("--record", required=True, help="JSON record matching the saved feature contract")
    predict.set_defaults(func=predict_command)
    evaluate = commands.add_parser("evaluate", help="Evaluate only the saved held-out test split")
    evaluate.add_argument("--artifact-dir", default="artifacts/module3")
    evaluate.set_defaults(func=evaluate_command)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except (DataContractError, ModelArtifactError, FileNotFoundError, json.JSONDecodeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()

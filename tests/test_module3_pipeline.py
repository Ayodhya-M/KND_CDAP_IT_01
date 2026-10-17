import tempfile
import unittest
from pathlib import Path

import pandas as pd
from sklearn.metrics import accuracy_score

from module3_ml.data import load_csv_dataset, validate_prediction_record
from module3_ml.evaluation import evaluate_heldout
from module3_ml.exceptions import DataContractError, ModelArtifactError
from module3_ml.model import load_artifact
from module3_ml.prediction import predict_employee
from module3_ml.training import train_baseline


def synthetic_test_frame():
    """Synthetic fixture for pipeline tests only; not research data or reported results."""
    return pd.DataFrame({
        "Age": [22, 24, 26, 28, 30, 32, 34, 36, 38, 40, 42, 44],
        "OverTime": ["Yes", "Yes", "No", "No", "Yes", "No", "Yes", "No", "Yes", "No", "Yes", "No"],
        "Attrition": ["Yes", "Yes", "No", "No", "Yes", "No", "Yes", "No", "Yes", "No", "Yes", "No"],
    })


class Module3PipelineTests(unittest.TestCase):
    def train_fixture(self, directory: Path):
        return train_baseline(synthetic_test_frame(), "Attrition", ["Age", "OverTime"], directory, test_size=0.25)

    def test_valid_employee_input_produces_supported_prediction(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            metadata = self.train_fixture(Path(temporary_directory))
            result = predict_employee({"Age": 31, "OverTime": "Yes"}, temporary_directory)
            self.assertIn(result["predicted_class"], metadata["classes"])
            self.assertEqual(set(result["class_probabilities"]), set(metadata["classes"]))

    def test_missing_and_unexpected_prediction_fields_are_rejected(self):
        with self.assertRaisesRegex(DataContractError, "missing required field"):
            validate_prediction_record({"Age": 31}, ["Age", "OverTime"])
        with self.assertRaisesRegex(DataContractError, "unexpected field"):
            validate_prediction_record({"Age": 31, "OverTime": "Yes", "Unknown": 1}, ["Age", "OverTime"])

    def test_saved_model_can_be_loaded(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            self.train_fixture(Path(temporary_directory))
            pipeline, metadata = load_artifact(temporary_directory)
            self.assertIsNotNone(pipeline)
            self.assertEqual(metadata["feature_columns"], ["Age", "OverTime"])

    def test_evaluation_uses_heldout_split_and_returns_square_matrix(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            self.train_fixture(Path(temporary_directory))
            report = evaluate_heldout(temporary_directory)
            pipeline, metadata = load_artifact(temporary_directory)
            heldout = pd.read_csv(Path(temporary_directory) / "heldout_test.csv")
            expected_accuracy = accuracy_score(
                heldout[metadata["target_column"]],
                pipeline.predict(heldout[metadata["feature_columns"]]),
            )
            labels = report["confusion_matrix_labels"]
            self.assertEqual(len(report["confusion_matrix"]), len(labels))
            self.assertTrue(all(len(row) == len(labels) for row in report["confusion_matrix"]))
            self.assertEqual(report["dataset_split"]["heldout_rows"], 3)
            self.assertEqual(report["metrics"]["accuracy"], expected_accuracy)

    def test_missing_model_artifact_is_clear(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            with self.assertRaises(ModelArtifactError):
                load_artifact(temporary_directory)

    def test_missing_dataset_and_eesi_feature_are_rejected(self):
        with self.assertRaises(FileNotFoundError):
            load_csv_dataset("does-not-exist.csv")
        with tempfile.TemporaryDirectory() as temporary_directory:
            frame = synthetic_test_frame()
            frame["EESI"] = [0.1, 0.2, 0.1, 0.2, 0.3, 0.2, 0.3, 0.2, 0.4, 0.3, 0.4, 0.3]
            frame["EESIFormulaId"] = "additive"
            frame["EESIFormulaVersion"] = "pp1-exploratory-v1"
            metadata = train_baseline(
                frame,
                "Attrition",
                ["Age", "OverTime", "EESI"],
                temporary_directory,
                test_size=0.25,
                eesi_column="EESI",
            )
            self.assertEqual(metadata["eesi_integration"]["formula_id"], "additive")
            self.assertEqual(metadata["eesi_integration"]["formula_version"], "pp1-exploratory-v1")
            with self.assertRaisesRegex(DataContractError, "missing required field"):
                predict_employee({"Age": 31, "OverTime": "Yes"}, temporary_directory)


if __name__ == "__main__":
    unittest.main()

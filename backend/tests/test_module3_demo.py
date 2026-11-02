import json

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.module3_export import build_pilot_export, FEATURE_COLUMNS
from app.services import module3_prediction


@pytest.fixture
def demo(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(module3_prediction.PROJECT_ROOT))
    from module3_ml.training import train_baseline
    from module3_ml.evaluation import evaluate_heldout, write_evaluation_report
    metadata = train_baseline(pd.DataFrame(build_pilot_export('additive', 300)), 'Attrition', FEATURE_COLUMNS, tmp_path, eesi_column='EESI')
    metadata.update(source_rows=300, dataset_kind='synthetic_pilot_only')
    (tmp_path / 'model_metadata.json').write_text(json.dumps(metadata))
    write_evaluation_report(evaluate_heldout(tmp_path), tmp_path)
    monkeypatch.delenv('MODULE3_ARTIFACT_DIR', raising=False)
    monkeypatch.setattr(module3_prediction, 'DEFAULT_ARTIFACT_DIRECTORY', tmp_path)
    return TestClient(app)


def test_saved_demo_predictions_and_evaluation(demo):
    status = demo.get('/api/v1/module3/prediction-status').json()
    assert status['model_available'] is True
    assert status['source_rows'] == 300
    rows = demo.get('/api/v1/module3/pilot-records').json()['records']
    assert len(rows) == len({row['employee_id'] for row in rows}) == 300
    assert 'Attrition' not in rows[0]['record']
    result = demo.post('/api/v1/module3/predict', json={'record': rows[0]['record']})
    assert result.status_code == 200
    assert set(result.json()['class_probabilities']) == {'Yes', 'No'}
    assert sum(result.json()['class_probabilities'].values()) == pytest.approx(1, abs=0.00001)
    report = demo.get('/api/v1/module3/evaluation').json()
    assert report['dataset_split']['train_rows'] == 240
    assert report['dataset_split']['heldout_rows'] == 60


@pytest.mark.parametrize('change', [{'Age': -1}, {'EESI': 101}, {'OverTime': 'invalid'}, {'Department': ''}, {'JobLevel': 1.5}])
def test_bad_prediction_domain_values(demo, change):
    row = demo.get('/api/v1/module3/pilot-records').json()['records'][0]['record']
    assert demo.post('/api/v1/module3/predict', json={'record': {**row, **change}}).status_code == 422

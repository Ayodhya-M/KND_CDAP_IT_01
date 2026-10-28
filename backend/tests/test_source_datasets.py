import copy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import source_datasets as sources


def workbook_rows():
    return [{'Age': 25 + index, 'Monthly_Base_Salary_LKR': 40000 + index * 5000,
        'Overtime_Hours_Per_Month': index % 15, 'Job_Satisfaction_1_5': index % 5 + 1,
        'Job_Level': 'Entry' if index % 2 else 'Senior', 'Tenure_Years': index / 2,
        'Department': 'IT' if index % 2 else 'Sales', 'Performance_Self_Rating_1_5': index % 5 + 1,
        'Promotions_Last_3_Years': index % 3, 'Monthly_Allowances_LKR': 1000,
        'Annual_Bonus_LKR': 12000, 'Monthly_Household_Expenses_LKR': 30000,
        'Monthly_Debt_Payments_LKR': 2000, 'Survey_Month': '2019-03',
        'Intention_To_Leave_12_Months': 'Yes' if index % 2 else 'No',
        'Gender': 'Excluded', 'District': 'Excluded', 'Financial_Worry_1_5': 5}
        for index in range(20)]


@pytest.fixture
def private_store(tmp_path, monkeypatch):
    original_root = sources.ROOT
    reference = sources.economic_reference()
    monkeypatch.syspath_prepend(str(original_root))
    monkeypatch.setattr(sources, 'ROOT', tmp_path)
    monkeypatch.setattr(sources, 'DATABASE', tmp_path / 'private/sources.sqlite3')
    monkeypatch.setattr(sources, 'MODEL_ROOT', tmp_path / 'artifacts/imported_sources')
    monkeypatch.setattr(sources, 'economic_reference', lambda: reference)
    return TestClient(app)


def test_workbook_source_preserves_meaning_and_omits_unneeded_fields(private_store):
    result = sources.import_source('sl_synthetic', workbook_rows(), 'source.xlsx', 'test-checksum', 20)
    assert result['target'] == 'Intention_To_Leave_12_Months'
    assert result['eesi_available'] is True
    assert result['split']['train_rows'] == 16
    assert result['split']['heldout_rows'] == 4
    dataset = sources.load_dataset(result['id'])
    row = dataset['records'][0]
    assert 'Gender' not in row and 'District' not in row and 'Financial_Worry_1_5' not in row
    assert 'Performance_Self_Rating_1_5' in row and 'Promotions_Last_3_Years' in row
    before = copy.deepcopy(dataset)
    analysis = private_store.post(f'/api/v1/source-data/{result["id"]}/records/{row["record_id"]}/analyse', json={})
    assert analysis.status_code == 200
    data = analysis.json()
    assert data['eesi'] is not None
    assert 'Intention_To_Leave_12_Months' not in data['inputs']
    scenario = sources.analyse(result['id'], row['record_id'], salary=500000)
    assert scenario['eesi']['scores']['additive'] < data['eesi']['scores']['additive']
    assert sources.load_dataset(result['id']) == before
    duplicate = sources.import_source('sl_synthetic', workbook_rows(), 'renamed.xlsx', 'other-container-hash', 20)
    assert duplicate['reused'] is True
    assert len(sources.list_datasets()) == 1


def test_ibm_source_cannot_be_reimported(private_store):
    with pytest.raises(ValueError, match='Unsupported source profile'):
        sources.import_source('ibm_benchmark', workbook_rows(), 'archive.zip', 'hash', 20)
    assert sources.list_datasets() == []


@pytest.mark.parametrize('changes', [{'Survey_Month': '2023-01'}, {'Job_Satisfaction_1_5': 6},
    {'Monthly_Base_Salary_LKR': float('inf')}, {'Intention_To_Leave_12_Months': 'Maybe'}])
def test_bad_source_values_fail_before_storage(private_store, changes):
    rows = workbook_rows()
    rows[0].update(changes)
    with pytest.raises(ValueError):
        sources.import_source('sl_synthetic', rows, 'source.xlsx', 'hash', 20)
    assert sources.list_datasets() == []


def test_missing_source_and_bad_scenario_are_clear_errors(private_store):
    assert private_store.get('/api/v1/source-data/missing/records').status_code == 404
    assert private_store.post('/api/v1/source-data/missing/records/missing/analyse', json={'salary': -1}).status_code == 422

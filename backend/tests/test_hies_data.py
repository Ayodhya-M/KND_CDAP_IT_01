import csv

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import hies_data


def synthetic_rows():
    rows = []
    for index in range(1, 101):
        row = {source: '0' for source, _ in hies_data.FIELDS.values()}
        row.update(SampleID=f'HIES19-{index:04}', SurveyMonth='2019-01',
                   EconomicReferenceMonth='2018-12', WagesMonthlyReported='50000',
                   ExtraEmploymentPayMonthlyReported='', BonusMonthlyEquivalent='',
                   TotalEmploymentIncomeMonthly='', HouseholdDebtPaymentsMonthlyReported='',
                   InflationYoYPercent='0.4', NCPI2013Base100='127.1', UnemploymentPercent='4.6')
        rows.append(row)
    return rows


@pytest.fixture
def local_store(tmp_path, monkeypatch):
    monkeypatch.setattr(hies_data, 'DATABASE', tmp_path / 'sample.sqlite3')
    monkeypatch.setattr(hies_data, 'PREPARED', tmp_path / 'sample.csv')
    return TestClient(app)


def write_sample(rows):
    with hies_data.PREPARED.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_empty_store_is_not_faked(local_store):
    result = local_store.get('/api/v1/eesi/hies').json()
    assert result['record_count'] == 0
    assert result['prepared_available'] is False
    assert local_store.post('/api/v1/eesi/hies/import-prepared').status_code == 404


def test_persistent_import_is_idempotent_and_preserves_missing(local_store):
    write_sample(synthetic_rows())
    for _ in range(2):
        response = local_store.post('/api/v1/eesi/hies/import-prepared')
        assert response.status_code == 200
        result = response.json()
        assert result['record_count'] == 100
        assert result['records'][0]['extra_pay'] is None
        assert result['records'][0]['household_debt_payments'] is None
        assert result['complete_income_count'] == 0
    assert local_store.get('/api/v1/eesi/hies').json()['record_count'] == 100


@pytest.mark.parametrize('failure', ['duplicate', 'nonfinite', 'wrong_month', 'missing_wage'])
def test_invalid_import_preserves_previous_sample(local_store, failure):
    rows = synthetic_rows()
    write_sample(rows)
    assert local_store.post('/api/v1/eesi/hies/import-prepared').status_code == 200
    if failure == 'duplicate':
        rows[1]['SampleID'] = rows[0]['SampleID']
    elif failure == 'nonfinite':
        rows[0]['WagesMonthlyReported'] = 'nan'
    elif failure == 'wrong_month':
        rows[0]['EconomicReferenceMonth'] = '2023-01'
    else:
        rows[0]['WagesMonthlyReported'] = ''
    write_sample(rows)
    assert local_store.post('/api/v1/eesi/hies/import-prepared').status_code == 422
    assert local_store.get('/api/v1/eesi/hies').json()['record_count'] == 100

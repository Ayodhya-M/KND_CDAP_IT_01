"""Software correctness checks; these do not establish scientific validity."""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.services.eesi import calculate
from app.services.eesi_formula_d import FormulaDConfig, calculate_formula_d, compare_dataset
from app.services import hies_data


INPUTS = dict(employee_wage=30000, ncpi=150, unemployment_rate=4.8,
              reference_income_2013=40000)


def score(**changes):
    return calculate_formula_d(**(INPUTS | changes))


def test_exact_formula_and_components():
    result = score()
    assert result['real_wage'] == 20000
    assert result['wage_inadequacy'] == .5
    assert result['normalized_unemployment'] == pytest.approx(.5)
    assert result['score'] == pytest.approx(50)
    assert sum(result['contributions'].values()) == result['score']
    assert result['inputs']['alpha'] == .5


def test_ncpi_and_wage_monotonicity():
    results = [score(ncpi=n) for n in (100, 150, 200, 1000)]
    assert all(a['real_wage'] > b['real_wage'] for a, b in zip(results, results[1:]))
    assert all(a['wage_inadequacy'] < b['wage_inadequacy'] for a, b in zip(results, results[1:]))
    assert score(employee_wage=0)['wage_inadequacy'] == 1


@pytest.mark.parametrize('wage', [40000, 80000, 1e308])
def test_threshold_and_above(wage):
    assert score(employee_wage=wage, ncpi=100)['wage_inadequacy'] == 0


def test_unemployment_monotonicity_and_clipping():
    results = [score(unemployment_rate=u)['score'] for u in (0, 4.5, 4.8, 5.1, 9, 1e308)]
    assert results[0] == results[1] < results[2] < results[3] == results[4] == results[5]


@pytest.mark.parametrize('alpha', [0, .5, 1])
@pytest.mark.parametrize('wage', [0, 1, 40000, 1e308])
@pytest.mark.parametrize('unemployment', [0, 4.5, 5.1, 1e308])
def test_score_bounds(alpha, wage, unemployment):
    assert 0 <= score(alpha=alpha, employee_wage=wage, unemployment_rate=unemployment)['score'] <= 100


@pytest.mark.parametrize('field', list(INPUTS) + ['alpha'])
@pytest.mark.parametrize('invalid', [None, 'nan', 'inf', '-inf', True, ''])
def test_invalid_numeric_values(field, invalid):
    with pytest.raises((ValueError, ValidationError)):
        score(**{field: invalid})


@pytest.mark.parametrize('changes', [dict(employee_wage=-1), dict(ncpi=0), dict(ncpi=-1),
    dict(reference_income_2013=0), dict(reference_income_2013=-1),
    dict(unemployment_rate=-1), dict(alpha=-.01), dict(alpha=1.01),
    dict(cpi_base_year=2021), dict(normalization_profile='lfs2024')])
def test_invalid_domains(changes):
    with pytest.raises(ValidationError):
        score(**changes)


@pytest.mark.parametrize('field', INPUTS)
def test_missing_required_inputs(field):
    values = INPUTS.copy()
    del values[field]
    with pytest.raises(ValidationError):
        calculate_formula_d(**values)


def test_large_finite_intermediate_and_overflow_error():
    assert score(employee_wage=1e308, ncpi=100)['real_wage'] == 1e308
    with pytest.raises(ValueError, match='finite numeric range'):
        score(employee_wage=1e308, ncpi=1e-300)


def test_alpha_endpoints():
    assert score(alpha=1)['score'] == 50
    assert score(alpha=0, unemployment_rate=5.1)['score'] == 100
    assert score(alpha=0, unemployment_rate=4.5)['score'] == 0


def test_no_threshold_is_disabled_not_zero():
    result = compare_dataset({'records': []}, FormulaDConfig())
    assert not result['enabled']
    assert result['records'] == []
    assert 'disabled' in result['message']
    assert result['metadata']['configuration']['reference_income_2013'] is None


def test_api_scenario_export_and_abc_regression(monkeypatch):
    client = TestClient(app)
    baseline = calculate(50000, 32.6, 107.635, 4.7)
    assert baseline['scores'] == pytest.approx({'economic': 50, 'additive': 50, 'interaction': 25})
    monkeypatch.setattr('app.routers.eesi.get_dataset', lambda: {'records': [
        dict(sample_id='TEST-1', survey_month='2019-02', economic_month='2019-01',
             salary=30000, cpi=150, unemployment=4.8)]})
    config = dict(reference_income_2013=40000, alpha=.5,
                  reference_income_source='Test fixture only', reference_income_justification='Boundary demonstration')
    response = client.post('/api/v1/eesi/formula-d/scenario', json=INPUTS | config)
    assert response.status_code == 200
    assert response.json()['score'] == pytest.approx(50)
    comparison = client.post('/api/v1/eesi/hies/formula-d', json=config)
    assert comparison.status_code == 200
    exported = client.post('/api/v1/eesi/hies/formula-d/export', json=config)
    assert exported.status_code == 200
    assert 'attachment' in exported.headers['content-disposition']
    assert exported.json() == comparison.json()
    assert exported.json()['records'][0]['score'] == response.json()['score']
    assert exported.json()['metadata']['configuration']['reference_income_source'] == 'Test fixture only'
    assert 'unvalidated' in exported.json()['metadata']['warning']
    assert client.post('/api/v1/eesi/hies/formula-d', json={}).json()['enabled'] is False
    assert calculate(50000, 32.6, 107.635, 4.7) == baseline
    assert set(hies_data.calculate_scenario(50000, 3, 130, 4.8)['scores']) == {'economic', 'additive', 'interaction'}


@pytest.mark.parametrize('changes', [{ 'employee_wage': None }, {'ncpi': 0}, {'alpha': 2}, {'reference_income_2013': None}])
def test_api_validation(changes):
    response = TestClient(app).post('/api/v1/eesi/formula-d/scenario', json=INPUTS | changes)
    assert response.status_code == 422
    assert response.json()['detail']


def test_api_missing_threshold():
    values = INPUTS.copy()
    del values['reference_income_2013']
    assert TestClient(app).post('/api/v1/eesi/formula-d/scenario', json=values).status_code == 422

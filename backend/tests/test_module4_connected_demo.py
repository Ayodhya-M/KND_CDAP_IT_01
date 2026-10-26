import csv
import json
from datetime import datetime, timezone, date
from uuid import uuid4

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import module3_prediction
from app.services.module3_export import build_pilot_export, FEATURE_COLUMNS, PILOT_ROOT
from app.module4.providers.base import ProviderMetadata, ProviderResultUnavailableError
from app.module4.providers.real_module2_provider import RealModule2Provider
from app.module4.providers.synthetic_demo_provider import SyntheticDemoModule3Provider
from app.module4.schemas.integration import Module1EmployeeContext, Module1EconomicContext
from app.module4.services.decision_service import RetentionDecisionService
from app.module4.services.what_if_simulator import WhatIfSimulator
from app.module4.schemas.simulation import WhatIfChanges


@pytest.fixture
def connected(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(module3_prediction.PROJECT_ROOT))
    from module3_ml.training import train_baseline
    rows = build_pilot_export('additive', employee_count=300)
    metadata = train_baseline(pd.DataFrame(rows), 'Attrition', FEATURE_COLUMNS, tmp_path, eesi_column='EESI')
    metadata['source_rows'] = 300
    (tmp_path / 'model_metadata.json').write_text(json.dumps(metadata))
    monkeypatch.delenv('MODULE3_ARTIFACT_DIR', raising=False)
    monkeypatch.setattr(module3_prediction, 'DEFAULT_ARTIFACT_DIRECTORY', tmp_path)
    row = rows[0]
    person = Module1EmployeeContext(id=uuid4(), upload_id=uuid4(), employee_id=row['EmployeeID'],
        age=row['Age'], salary=row['MonthlyIncome'], department=row['Department'],
        job_satisfaction=row['JobSatisfaction'], job_level=row['JobLevel'],
        overtime=row['OverTime'] == 'Yes', years_at_company=row['YearsAtCompany'],
        attrition=False, created_at=datetime.now(timezone.utc))
    with (PILOT_ROOT / 'module1_sri_lanka_macro_pilot_6_months.csv').open() as stream:
        macro = next(item for item in csv.DictReader(stream) if item['Date'].startswith(row['ObservationMonth']))
    economic = Module1EconomicContext(id=uuid4(), upload_id=uuid4(), indicator_month=date.fromisoformat(macro['Date']),
        inflation_rate=macro['Inflation_Rate_Percent'], cpi_index=macro['CPI_Index'], unemployment_rate=macro['Unemployment_Rate_Percent'])
    class Repository:
        def get_employee_context(self, *args, **kwargs): return person
        def get_employee_economic_context(self, *args): return economic
    module2 = RealModule2Provider(formula_identifier='additive')
    module2.metadata = ProviderMetadata('module2_calculated_pilot', 'synthetic_demo_integration', False)
    return RetentionDecisionService(Repository(), module2, SyntheticDemoModule3Provider()), person


def test_connected_model_recommendations_and_scenario(connected):
    service, person = connected
    before = person.model_dump()
    result = service.recommendations_for_employee(person.employee_id)
    assert result.metadata.data_mode == 'synthetic_demo_integration'
    assert 'Unclassified' in result.risk_level
    assert 'not SHAP' in result.metadata.disclaimer
    assert all(factor.feature_name in ('salary', 'overtime', 'job_satisfaction') for factor in result.important_risk_factors)
    scenario = WhatIfSimulator(service).simulate(person.employee_id, WhatIfChanges(salary=float(person.salary) * 1.1))
    assert person.model_dump() == before
    assert scenario.probability_difference == pytest.approx(100 * (scenario.simulated_turnover_probability - scenario.original_turnover_probability), abs=0.000001)
    assert scenario.simulated_turnover_probability != scenario.original_turnover_probability


def test_wrong_employee_version_fails_without_mock_fallback(connected):
    service, person = connected
    person.salary += 1
    with pytest.raises(ProviderResultUnavailableError, match='does not match'):
        service.recommendations_for_employee(person.employee_id)


def test_demo_query_composes_and_returns_connected_service(connected, monkeypatch):
    service, person = connected
    monkeypatch.setattr('app.module4.routers.recommendations.EmployeeRepository', lambda: service.employee_repository)
    response = TestClient(app).get(f'/api/v1/module4/employees/{person.employee_id}/recommendations?demo=true')
    assert response.status_code == 200
    assert response.json()['metadata']['module3_source'] == 'module3_synthetic_model'

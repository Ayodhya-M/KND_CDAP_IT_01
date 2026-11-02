"""Connect the saved synthetic model without inventing research risk bands."""
from app.module4.providers.base import ProviderMetadata, ProviderResultUnavailableError
from app.module4.providers.real_module3_provider import RealModule3Provider
from app.module4.schemas.integration import Module3RiskFactor
from app.services.module3_export import build_pilot_export
from app.services.module3_prediction import get_model_status, predict_saved_model


class SyntheticDemoModule3Provider:
    metadata = ProviderMetadata(source='module3_synthetic_model', data_mode='synthetic_demo_integration', is_mock=False)

    def get_prediction(self, employee, eesi_result):
        return self._predict(employee, eesi_result, require_source_match=True)

    def get_scenario_prediction(self, employee, eesi_result):
        return self._predict(employee, eesi_result, require_source_match=False)

    def _predict(self, employee, eesi_result, *, require_source_match):
        status = get_model_status()
        if not status.get('model_available') or status.get('source_rows') != 300:
            raise ProviderResultUnavailableError('Prepare the 300-person synthetic demo model before running integrated retention analysis.')
        record = RealModule3Provider.build_feature_record(employee, eesi_result)
        # Prevent applying a synthetic demonstration to unrelated employee data.
        rows = build_pilot_export(eesi_result.formula_identifier, employee_count=300)
        source = next((row for row in rows if row['EmployeeID'] == employee.employee_id), None)
        if source is None:
            raise ProviderResultUnavailableError('Synthetic demo mode supports PILOT employees only; HIES is a separate dataset.')
        if require_source_match and (any(record[key] != source[key] for key in record if key != 'EESI') or
                                     abs(record['EESI'] - source['EESI']) > 0.00001):
            raise ProviderResultUnavailableError('Select the matching 300-person synthetic HR dataset and its mapped economic context. This employee version does not match the demo source.')

        def sensitivities(person, prediction, model_status):
            baseline = RealModule3Provider.extract_positive_probability(prediction, 'Yes')
            probes = []
            if record['OverTime'] == 'Yes':
                probes.append(('overtime', person.overtime, {'OverTime': 'No'}))
            if record['JobSatisfaction'] is not None and record['JobSatisfaction'] <= 2:
                probes.append(('job_satisfaction', person.job_satisfaction, {'JobSatisfaction': 4}))
            if record['MonthlyIncome'] is not None and record['MonthlyIncome'] > 0:
                probes.append(('salary', float(person.salary), {'MonthlyIncome': record['MonthlyIncome'] * 1.1}))
            factors = []
            for name, value, change in probes:
                alternate = predict_saved_model({**record, **change})
                delta = baseline - RealModule3Provider.extract_positive_probability(alternate, 'Yes')
                if delta > 0.000001:
                    factors.append(Module3RiskFactor(feature_name=name, feature_value=value, contribution=delta))
            return factors

        adapter = RealModule3Provider(positive_class_label='Yes',
            risk_level_resolver=lambda probability: 'Unclassified (synthetic demo)',
            risk_factor_resolver=sensitivities)
        try:
            return adapter.get_prediction(employee, eesi_result)
        except (ValueError, RuntimeError) as error:
            raise ProviderResultUnavailableError(f'Synthetic prediction unavailable: {error}') from error

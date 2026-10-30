"""Separate, minimal source-aware Module 1 imports and downstream demo pipeline."""
import csv
import hashlib
import json
import math
import re
import sqlite3
import sys
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from app.services.eesi import calculate
from app.services.financial_burden import adjustment, extended_formulas
from app.services.hies_data import BOUNDS as HISTORICAL_BOUNDS

ROOT = Path(__file__).resolve().parents[3]
DATABASE = ROOT / 'data/private/module1_sources.sqlite3'
MODEL_ROOT = ROOT / 'artifacts/imported_sources'
SOURCE_VERSION = 'sl-synthetic-scenario-2019-v1'
SL_FEATURES = ['Age', 'Monthly_Base_Salary_LKR', 'Overtime_Hours_Per_Month',
               'Job_Satisfaction_1_5', 'Job_Level', 'Tenure_Years', 'Department',
               'Performance_Self_Rating_1_5', 'Promotions_Last_3_Years', 'EESI']
SL_SUPPORT = ['Monthly_Allowances_LKR', 'Annual_Bonus_LKR', 'Monthly_Household_Expenses_LKR',
              'Monthly_Debt_Payments_LKR', 'Survey_Month']
CONFIG = {
    'sl_synthetic': {'name': 'Sri Lanka synthetic scenarios · 50', 'kind': 'AI-generated synthetic examples',
        'currency': 'LKR', 'target': 'Intention_To_Leave_12_Months', 'target_label': 'Intention to leave within 12 months',
        'features': SL_FEATURES, 'salary': 'Monthly_Base_Salary_LKR', 'satisfaction': 'Job_Satisfaction_1_5',
        'satisfaction_max': 5, 'overtime': 'Overtime_Hours_Per_Month', 'overtime_reference': 0,
        'date_note': '2019 months are scenario labels, not actual survey collection dates.',
        'eesi_note': 'Calculated from base salary and historical economic context for the scenario month. Household expenses, allowances and debt are supporting fields, not formula inputs.',
        'warning': 'All 50 rows are AI-generated. Performance is self-rated. Intention to leave is not observed attrition. Metrics are software demonstrations, not research validation.'},
}


def finite(value, field, minimum=0, maximum=None):
    if isinstance(value, bool):
        raise ValueError(f'{field} must be numeric')
    try:
        number = float(value)
    except (ValueError, TypeError) as error:
        raise ValueError(f'{field} is missing or nonnumeric') from error
    if not math.isfinite(number) or number < minimum or maximum is not None and number > maximum:
        raise ValueError(f'{field} is outside its valid range')
    return number


def economic_reference():
    with (ROOT / 'data/reference/eesi/hies2019-economic-reference.csv').open(newline='') as stream:
        return {row['month']: row for row in csv.DictReader(stream)}


def source_eesi(row, reference):
    month = row['Survey_Month']
    if month not in reference:
        raise ValueError(f'No historical economic data for scenario month {month}')
    macro = reference[month]
    return calculate(row['Monthly_Base_Salary_LKR'], float(macro['inflation_yoy_percent']),
                     float(macro['ncpi_2013_100']), float(macro['unemployment_percent']),
                     bounds=HISTORICAL_BOUNDS, version=SOURCE_VERSION)


def validate_records(profile, records):
    if profile not in CONFIG:
        raise ValueError('Unsupported source profile. Only the Sri Lanka synthetic workbook is enabled.')
    config = CONFIG[profile]
    seen = set()
    cleaned = []
    reference = economic_reference() if profile == 'sl_synthetic' else {}
    for index, source in enumerate(records, 1):
        fields = [key for key in config['features'] if key != 'EESI'] + [config['target']]
        if profile == 'sl_synthetic':
            fields += SL_SUPPORT
        row = {}
        for field in fields:
            value = source.get(field)
            if field in ('Department', 'Job_Level', 'OverTime', config['target'], 'Survey_Month'):
                if value is None or not str(value).strip():
                    raise ValueError(f'Missing {field} in record {index}')
                row[field] = str(value).strip()
            else:
                row[field] = finite(value, field)
        if row[config['target']] not in ('Yes', 'No'):
            raise ValueError('Unsupported target label')
        if not 18 <= row['Age'] <= 100:
            raise ValueError('Import supports adult employee examples only')
        maximum = config['satisfaction_max']
        finite(row[config['satisfaction']], config['satisfaction'], 1, maximum)
        if row['Age'] % 1 or row[config['satisfaction']] % 1:
            raise ValueError('Age and satisfaction ratings must be whole numbers')
        if profile == 'sl_synthetic':
            if not re.fullmatch(r'2019-(0[1-9]|1[0-2])', row['Survey_Month']):
                raise ValueError('Expected a 2019 scenario label')
            finite(row['Performance_Self_Rating_1_5'], 'Performance', 1, 5)
            if row['Performance_Self_Rating_1_5'] % 1 or row['Promotions_Last_3_Years'] % 1:
                raise ValueError('Performance ratings and promotion counts must be whole numbers')
            row['EESI'] = source_eesi(row, reference)['scores']['additive']
        signature = json.dumps(row, sort_keys=True)
        if signature in seen:
            continue
        seen.add(signature)
        row['record_id'] = f'SL-SYN-{index:04}'
        cleaned.append(row)
    if len(cleaned) < 10:
        raise ValueError('Too few valid independent rows for a demo split')
    return cleaned


def import_source(profile, records, source_name, source_sha256, original_count):
    rows = validate_records(profile, records)
    content_hash = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    dataset_id = f'{profile}_{content_hash[:12]}'
    if DATABASE.is_file():
        try:
            existing = load_dataset(dataset_id)
            return {**dataset_summary(existing), 'reused': True}
        except KeyError:
            pass
    sys.path.insert(0, str(ROOT))
    import pandas as pd
    from module3_ml.training import train_baseline
    from module3_ml.evaluation import evaluate_heldout, write_evaluation_report
    destination = MODEL_ROOT / dataset_id
    if (destination / 'turnover_pipeline.joblib').exists():
        # A prior interrupted import may have left an artifact. Never overwrite it.
        destination = destination / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    config = CONFIG[profile]
    frame = pd.DataFrame(rows)
    if profile == 'sl_synthetic':
        frame['EESIFormulaId'] = 'additive'
        frame['EESIFormulaVersion'] = SOURCE_VERSION
    metadata = train_baseline(frame, config['target'], config['features'], destination,
                              eesi_column='EESI' if profile == 'sl_synthetic' else None)
    metadata.update(dataset_kind=config['kind'], dataset_id=dataset_id, source_sha256=source_sha256)
    (destination / 'model_metadata.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    report = evaluate_heldout(destination)
    report['limitations'].insert(0, config['warning'])
    write_evaluation_report(report, destination)
    dataset = {'id': dataset_id, 'profile': profile, 'source_file': Path(source_name).name,
               'source_sha256': source_sha256, 'content_sha256': content_hash,
               'source_rows': original_count, 'record_count': len(rows), 'records': rows,
               'model_path': str(destination.relative_to(ROOT)), 'metadata': metadata,
               'imported_at': datetime.now(timezone.utc).isoformat(), 'selection_seed': None}
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    if DATABASE.exists():
        backup = DATABASE.with_name(f'module1_sources-backup-{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")}.sqlite3')
        with closing(sqlite3.connect(DATABASE)) as original, closing(sqlite3.connect(backup)) as copy:
            original.backup(copy)
    with closing(sqlite3.connect(DATABASE)) as connection, connection:
        connection.execute('CREATE TABLE IF NOT EXISTS datasets (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        connection.execute('INSERT INTO datasets VALUES (?, ?)', (dataset_id, json.dumps(dataset, allow_nan=False)))
    return {**dataset_summary(dataset), 'reused': False}


def dataset_summary(dataset):
    config = CONFIG[dataset['profile']]
    return {key: value for key, value in {**config, **{k: dataset[k] for k in ('id', 'source_file', 'source_rows', 'record_count', 'imported_at')},
        'model_available': (ROOT / dataset['model_path'] / 'turnover_pipeline.joblib').is_file(),
        'split': dataset['metadata']['split'],
        'eesi_available': dataset['profile'] == 'sl_synthetic',
        'retained_fields': [key for key in dataset['records'][0] if key != 'record_id']}.items()
        if key not in ('salary', 'satisfaction', 'satisfaction_max', 'overtime', 'overtime_reference')}


def load_dataset(dataset_id):
    if not DATABASE.is_file():
        raise KeyError('Source dataset is not imported')
    with closing(sqlite3.connect(DATABASE)) as connection:
        result = connection.execute('SELECT payload FROM datasets WHERE id = ?', (dataset_id,)).fetchone()
    if result is None:
        raise KeyError('Source dataset is not imported')
    return json.loads(result[0])


def list_datasets():
    if not DATABASE.is_file():
        return []
    with closing(sqlite3.connect(DATABASE)) as connection:
        rows = connection.execute('SELECT payload FROM datasets ORDER BY id').fetchall()
    return [dataset_summary(json.loads(row[0])) for row in rows]


def record_choices(dataset_id):
    dataset = load_dataset(dataset_id)
    return [{'record_id': row['record_id'], 'month': row.get('Survey_Month')} for row in dataset['records']]


def analyse(dataset_id, record_id, salary=None):
    dataset = load_dataset(dataset_id)
    config = CONFIG[dataset['profile']]
    source = next((row for row in dataset['records'] if row['record_id'] == record_id), None)
    if source is None:
        raise KeyError('Source record was not found')
    row = dict(source)
    if salary is not None:
        row[config['salary']] = finite(salary, 'Scenario salary', 0.000001)
    reference = economic_reference() if dataset['profile'] == 'sl_synthetic' else {}
    def model_input(values):
        record = dict(values)
        if reference:
            record['EESI'] = source_eesi(record, reference)['scores']['additive']
        return {key: record[key] for key in config['features']}
    sys.path.insert(0, str(ROOT))
    from module3_ml.prediction import predict_employee
    from module3_ml.exceptions import ModelArtifactError
    model_path = (ROOT / dataset['model_path']).resolve()
    if not model_path.is_relative_to(MODEL_ROOT.resolve()):
        raise ModelArtifactError('Unexpected model path')
    prediction = predict_employee(model_input(row), model_path)
    baseline = prediction['class_probabilities']['Yes']
    probes = [('Compensation review', config['salary'], row[config['salary']] * 1.1),
              ('Supportive satisfaction discussion', config['satisfaction'], config['satisfaction_max']),
              ('Workload and overtime review', config['overtime'], config['overtime_reference'])]
    actions = []
    for title, field, alternative in probes:
        if row[field] == alternative:
            continue
        probe = predict_employee(model_input({**row, field: alternative}), model_path)
        change = 100 * (baseline - probe['class_probabilities']['Yes'])
        if change > 0.0001:
            actions.append({'title': title, 'sensitivity_pp': round(change, 4),
                'note': 'Temporary model-input sensitivity, not a causal intervention effect or validated employee risk.'})
    actions.sort(key=lambda action: action['sensitivity_pp'], reverse=True)
    with (model_path / 'evaluation_report.json').open(encoding='utf-8') as stream:
        report = json.load(stream)
    eesi = source_eesi(row, reference) if reference else None
    financial = adjustment(row, eesi['scores']) if eesi and dataset['profile'] == 'sl_synthetic' else None
    return {'dataset': dataset_summary(dataset), 'record_id': record_id,
        'inputs': {key: value for key, value in row.items() if key not in (config['target'], 'record_id', 'EESI')},
        'eesi': eesi,
        'financial_burden_adjustment': financial,
        'experimental_eesi': extended_formulas(eesi, financial) if financial else None,
        'prediction': {**prediction, 'target_label': config['target_label']},
        'recommendations': actions, 'evaluation': {'split': report['dataset_split'], 'metrics': report['metrics']},
        'scenario': salary is not None, 'saved_records_unchanged': True,
        'limitations': [config['warning'], config['date_note'], config['eesi_note']]}

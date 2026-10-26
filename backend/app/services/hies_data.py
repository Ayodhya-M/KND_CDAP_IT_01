"""Private local storage for the distinct HIES financial sample."""
import csv
import json
import math
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from app.services.eesi import calculate, FORMULAS

PRIVATE_ROOT = Path(__file__).resolve().parents[3] / 'data' / 'private'
DATABASE = PRIVATE_ROOT / 'hies2019_app.sqlite3'
PREPARED = PRIVATE_ROOT / 'hies2019_100' / 'eesi_inputs_100_clean.csv'
BOUNDS = {'inflation': (0.4, 6.2), 'cpi': (126.4, 135.0), 'unemployment': (4.5, 5.1)}
VERSION = 'hies2019-pp1-inputs-v1'


def calculate_scenario(salary, inflation, cpi, unemployment, reference_salary=50000):
    return calculate(salary, inflation, cpi, unemployment, reference_salary,
                     bounds=BOUNDS, version=VERSION)
FIELDS = {
    'salary': ('WagesMonthlyReported', True),
    'extra_pay': ('ExtraEmploymentPayMonthlyReported', False),
    'bonus_monthly': ('BonusMonthlyEquivalent', False),
    'total_income': ('TotalEmploymentIncomeMonthly', False),
    'household_food': ('HouseholdFoodMonthlyEquivalent', True),
    'household_nonfood': ('HouseholdNonfoodMonthlyEquivalentIncludingDebtPayments', True),
    'household_expenditure': ('HouseholdTotalRecordedExpenditureMonthlyEquivalent', True),
    'household_debt_payments': ('HouseholdDebtPaymentsMonthlyReported', False),
    'outstanding_debt_known': ('HouseholdOutstandingDebtKnownAmount', False),
    'inflation': ('InflationYoYPercent', True),
    'cpi': ('NCPI2013Base100', True),
    'unemployment': ('UnemploymentPercent', True),
}


def validate_rows(rows):
    if len(rows) != 100:
        raise ValueError('The prepared HIES sample must contain exactly 100 records.')
    cleaned, seen = [], set()
    for row in rows:
        sample_id = row.get('SampleID', '')
        if not re.fullmatch(r'HIES19-\d{4}', sample_id) or sample_id in seen:
            raise ValueError('Sample IDs must be valid and unique.')
        seen.add(sample_id)
        record = {'sample_id': sample_id}
        for name, (source, required) in FIELDS.items():
            value = row.get(source, '').strip()
            if not value:
                if required:
                    raise ValueError(f'{sample_id}: missing {source}.')
                record[name] = None
                continue
            try:
                number = float(value)
            except ValueError as error:
                raise ValueError(f'{sample_id}: invalid {source}.') from error
            if not math.isfinite(number) or (name != 'inflation' and number < 0):
                raise ValueError(f'{sample_id}: invalid {source}.')
            record[name] = number
        if record['salary'] <= 0 or record['cpi'] <= 0 or record['unemployment'] > 100:
            raise ValueError(f'{sample_id}: invalid salary or economic indicators.')
        survey = row.get('SurveyMonth', '')
        economic = row.get('EconomicReferenceMonth', '')
        if not re.fullmatch(r'2019-(0[1-9]|1[0-2])', survey):
            raise ValueError('Invalid survey month.')
        month = int(survey[-2:])
        expected = '2018-12' if month == 1 else f'2019-{month - 1:02}'
        if economic != expected:
            raise ValueError('Economic reference must match the previous calendar month.')
        record.update(survey_month=survey, economic_month=economic,
                      quality_flags=row.get('QualityFlags', '').split(';'))
        result = calculate(record['salary'], record['inflation'], record['cpi'], record['unemployment'],
                           bounds=BOUNDS, version=VERSION)
        record['scores'] = result['scores']
        cleaned.append(record)
    return cleaned


def import_prepared():
    with PREPARED.open(encoding='utf-8-sig', newline='') as stream:
        records = validate_rows(list(csv.DictReader(stream)))
    # Validation happens before opening the database; replace atomically so a
    # failed import cannot erase the previous valid sample.
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(DATABASE)) as connection, connection:
        connection.execute('CREATE TABLE IF NOT EXISTS hies_records (sample_id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        connection.execute('CREATE TABLE IF NOT EXISTS hies_import (id INTEGER PRIMARY KEY CHECK(id = 1), imported_at TEXT NOT NULL)')
        connection.execute('DELETE FROM hies_records')
        connection.executemany('INSERT INTO hies_records VALUES (?, ?)',
                               [(r['sample_id'], json.dumps(r, allow_nan=False)) for r in records])
        connection.execute('INSERT OR REPLACE INTO hies_import VALUES (1, ?)',
                           (datetime.now(timezone.utc).isoformat(),))
    return get_dataset()


def get_dataset():
    records, imported_at = [], None
    if DATABASE.is_file():
        with closing(sqlite3.connect(DATABASE)) as connection:
            records = [json.loads(row[0]) for row in connection.execute('SELECT payload FROM hies_records ORDER BY sample_id')]
            metadata = connection.execute('SELECT imported_at FROM hies_import WHERE id = 1').fetchone()
            imported_at = metadata[0] if metadata else None
    for record in records:
        result = calculate_scenario(record['salary'], record['inflation'], record['cpi'], record['unemployment'])
        record.update(scores=result['scores'], breakdown=result)
    return {
        'record_count': len(records), 'storage': 'private_local', 'imported_at': imported_at,
        'prepared_available': PREPARED.is_file(), 'records': records,
        'complete_income_count': sum(r['total_income'] is not None for r in records),
        'debt_payment_count': sum(r['household_debt_payments'] is not None for r in records),
        'formula_version': VERSION,
        'metadata': {'formulas': FORMULAS, 'bounds': BOUNDS, 'reference_salary': 50000,
                     'reference_period': 'December 2018-December 2019',
                     'cpi_base': 'NCPI 2013=100', 'score_scale': '0-100 exploratory index'},
        'note': '100-person HIES 2019 sample, separate from organizational HR. Candidate scores use wages and economic indicators only. Expenses and debt are household-level. Missing values are not zero.',
    }

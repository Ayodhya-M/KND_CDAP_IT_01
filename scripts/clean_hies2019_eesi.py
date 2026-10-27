"""Prepare the existing 100-person sample as auditable PP1 EESI inputs.

No imputation, personal/household attribution, final EESI score or app upload.
"""
import csv
import json
import sys
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / 'data/private/hies2019_100'
VERSION = 'hies2019-pp1-inputs-v1'
# Frozen from the complete published Dec 2018-Dec 2019 macro reference, not
# fitted separately to the selected 100 people. NCPI base is 2013=100.
BOUNDS = {'inflation': (0.4, 6.2), 'cpi': (126.4, 135.0), 'unemployment': (4.5, 5.1)}


def number(value):
    if value is None or not str(value).strip():
        return None
    try:
        result = Decimal(str(value).strip())
    except InvalidOperation as error:
        raise ValueError('Invalid financial number') from error
    if not result.is_finite() or result < 0:
        raise ValueError('Financial values must be finite and nonnegative')
    return result


def monthly_factor(category, code):
    code = int(code)
    if category == 'food' and 100 <= code < 2000:
        return Decimal(52) / 12, 'week'
    if category != 'nonfood':
        raise ValueError('Unknown expense category/code')
    if 3000 <= code < 3300:
        return Decimal(1) / 6, 'six_months'
    if (3300 <= code < 3340 or 3500 <= code < 3600 or
            code in (2421, 2422, 2609, 2610, 2611, 2612, 2613)):
        return Decimal(1) / 12, 'twelve_months'
    if 2000 <= code < 3000 or code in (3341, 3342) or 3400 <= code < 3500:
        return Decimal(1), 'month_or_monthly_average'
    raise ValueError(f'Unmapped expense code {code}')


def prior_month(year, month):
    if not 1 <= month <= 12:
        raise ValueError('Invalid survey month')
    return f'{year - 1}-12' if month == 1 else f'{year}-{month - 1:02}'


def load_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def write_csv(path, records):
    with path.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        for row in records:
            writer.writerow({key: '' if value is None else
                             format(value.quantize(Decimal('0.01')), 'f') if isinstance(value, Decimal)
                             else value for key, value in row.items()})


def prepare():
    people = load_csv(PRIVATE / 'wage_earners_100.csv')
    expenses = load_csv(PRIVATE / 'household_expenses.csv')
    ids = [row['SampleID'] for row in people]
    if len(ids) != 100 or len(set(ids)) != 100:
        raise ValueError('Expected exactly 100 unique sample IDs')
    observed = set()
    grouped = defaultdict(list)
    for row in expenses:
        signature = (row['SampleID'], row['Category'], row['ItemCode'])
        if signature in observed or row['SampleID'] not in ids:
            raise ValueError('Duplicate expense key or unknown sample ID')
        observed.add(signature)
        grouped[row['SampleID']].append(row)
    reference = load_csv(ROOT / 'data/reference/eesi/hies2019-economic-reference.csv')
    macro = {row['month']: row for row in reference}
    if len(macro) != len(reference):
        raise ValueError('Duplicate macro month')
    normalized, prepared = [], []
    for person in people:
        sample_id = person['SampleID']
        wage = number(person['WagesSalariesReported'])
        if wage is None or wage <= 0:
            raise ValueError('Missing positive wage')
        allowance = number(person['AllowancesReported'])
        annual_bonus = number(person['BonusReported'])
        bonus = None if annual_bonus is None else annual_bonus / 12
        full_income = None if allowance is None or bonus is None else wage + allowance + bonus
        totals = defaultdict(Decimal)
        payment = None
        if not grouped[sample_id]:
            raise ValueError('Missing household expenses')
        for row in grouped[sample_id]:
            value = number(row['ValueReported'])
            inkind = number(row['InKindValueReported'])
            if value is None:
                raise ValueError('Missing expense amount')
            if inkind is not None and inkind > value:
                raise ValueError('In-kind amount exceeds reported expense; review definitions')
            factor, period = monthly_factor(row['Category'], row['ItemCode'])
            monthly = value * factor
            totals[row['Category']] += monthly
            if row['Category'] == 'nonfood' and row['ItemCode'] == '3405':
                payment = monthly
            normalized.append({'SampleID': sample_id, 'Scope': 'household',
                               'Category': row['Category'], 'ItemCode': row['ItemCode'],
                               'SourcePeriod': period, 'MonthlyFactor': str(factor),
                               'ValueReportedLKR': value, 'MonthlyEquivalentLKR': monthly,
                               'InKindReportedLKR': inkind})
        year, month = int(person['SurveyYear']), int(person['SurveyMonth'])
        if year != 2019:
            raise ValueError('Unexpected survey year')
        income_month = prior_month(year, month)
        if income_month not in macro:
            raise ValueError('Missing economic reference month')
        economic = macro[income_month]
        debt = [number(value) for field, value in person.items() if field.startswith('Household_')]
        known_debt = sum((value for value in debt if value is not None), Decimal(0))
        # Missing lender amounts cannot establish that there is no outstanding debt.
        debt_complete = len(debt) == 10 and all(value is not None for value in debt)
        flags = []
        if allowance is None:
            flags.append('extra_employment_pay_missing')
        if bonus is None:
            flags.append('annual_bonus_missing')
        if payment is None:
            flags.append('debt_payment_not_reported')
        if not debt_complete:
            flags.append('outstanding_debt_incomplete')
        flags.extend(['household_costs_not_personal_costs', 'income_period_calendar_month_assumption'])
        prepared.append({
            'SampleID': sample_id, 'SurveyMonth': f'{year}-{month:02}',
            'EconomicReferenceMonth': income_month, 'Currency': 'LKR',
            'WagesMonthlyReported': wage,
            'ExtraEmploymentPayMonthlyReported': allowance,
            'BonusMonthlyEquivalent': bonus,
            'TotalEmploymentIncomeMonthly': full_income,
            'HouseholdFoodMonthlyEquivalent': totals['food'],
            'HouseholdNonfoodMonthlyEquivalentIncludingDebtPayments': totals['nonfood'],
            'HouseholdTotalRecordedExpenditureMonthlyEquivalent': totals['food'] + totals['nonfood'],
            'HouseholdDebtPaymentsMonthlyReported': payment,
            'HouseholdOutstandingDebtKnownAmount': known_debt,
            'HouseholdOutstandingDebtTotal': known_debt if debt_complete else None,
            'InflationYoYPercent': number(economic['inflation_yoy_percent']),
            'NCPI2013Base100': number(economic['ncpi_2013_100']),
            'UnemploymentPercent': number(economic['unemployment_percent']),
            'UnemploymentQuarter': economic['unemployment_quarter'],
            'CompleteEmploymentIncome': full_income is not None,
            'PersonalExpensesMonthly': None,
            'PersonalLoanRepaymentsMonthly': None,
            'FinalEESIReady': False,
            'QualityFlags': ';'.join(flags),
        })
    write_csv(PRIVATE / 'eesi_inputs_100_clean.csv', prepared)
    write_csv(PRIVATE / 'expenses_monthly_audit.csv', normalized)
    # Reuse current implemented candidate formulas, with a separate historical
    # reference. These scores deliberately do not claim to include expenses.
    sys.path.insert(0, str(ROOT / 'backend'))
    from app.services.eesi import calculate
    candidate_results = []
    for row in prepared:
        result = calculate(float(row['WagesMonthlyReported']), float(row['InflationYoYPercent']),
                           float(row['NCPI2013Base100']), float(row['UnemploymentPercent']),
                           bounds=BOUNDS, version=VERSION)
        candidate_results.append({
            'SampleID': row['SampleID'], 'EconomicReferenceMonth': row['EconomicReferenceMonth'],
            'SalaryInputLKR': row['WagesMonthlyReported'],
            'InflationYoYPercent': row['InflationYoYPercent'],
            'NCPI2013Base100': row['NCPI2013Base100'],
            'UnemploymentPercent': row['UnemploymentPercent'],
            'EconomicCandidateScore': Decimal(str(result['scores']['economic'])),
            'AdditiveCandidateScore': Decimal(str(result['scores']['additive'])),
            'InteractionCandidateScore': Decimal(str(result['scores']['interaction'])),
            'FormulaVersion': VERSION, 'IncludesHouseholdExpensesOrDebt': False,
        })
    write_csv(PRIVATE / 'eesi_existing_candidates_100.csv', candidate_results)
    report = {
        'records': len(prepared), 'unique_sample_ids': len(set(ids)),
        'expense_rows_validated': len(normalized),
        'macro_months_matched': len(prepared),
        'complete_employment_income_records': sum(r['CompleteEmploymentIncome'] for r in prepared),
        'reported_debt_payment_records': sum(r['HouseholdDebtPaymentsMonthlyReported'] is not None for r in prepared),
        'existing_candidate_records_calculated': len(candidate_results),
        'candidate_reference_bounds': BOUNDS,
        'candidate_reference_salary_lkr': 50000,
        'candidate_formula_version': VERSION,
        'candidate_scope': 'Existing economic/additive/interaction formulas using reported wages only. Extra pay, bonuses, expenses and debt are not included in these candidate scores. No finalized financial EESI.',
        'missing_value_counts': {field: sum(row[field] is None for row in prepared) for field in prepared[0]
                                 if any(row[field] is None for row in prepared)},
        'quality_flag_counts': dict(Counter(flag for row in prepared for flag in row['QualityFlags'].split(';'))),
        'outlier_policy': 'No winsorization, clipping, imputation or automatic outlier deletion. Positive high values retained.',
        'conversion': 'Weekly amounts * 52 / 12; six-month amounts / 6; annual amounts / 12. Averages are not actual cash flow.',
        'macro_alignment': 'Previous calendar month as an explicit PP1 assumption. Source also permits last four weeks; exact dates are unavailable. Quarterly unemployment repeated without interpolation. Retrospective, not real-time.',
        'double_counting': 'Debt payments are already part of nonfood total. Do not add them again. Outstanding debt is a stock and must not be subtracted as monthly expenditure. In-kind values are not added to reported values.',
        'readiness': 'Cleaned PP1 inputs with explicit missingness. Final personal-finance EESI remains unavailable without missing inputs, household allocation and formula definitions.',
        'questionnaire_pages': {'food': 'printed 9-14', 'nonfood': 'printed 15-20',
                                'income': 'printed 22', 'debt_stock': 'printed 28'},
    }
    (PRIVATE / 'cleaning_report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    result = prepare()
    print(json.dumps({key: result[key] for key in ('records', 'expense_rows_validated',
          'macro_months_matched', 'complete_employment_income_records', 'reported_debt_payment_records')}))

"""Display-only experiment for the Sri Lanka synthetic source; never a model input."""
import math

DISCLAIMER = ('Experimental adjustment using synthetic pilot data. '
              'The 70/30 weighting is a preliminary research assumption. '
              'This score has not been validated against actual employee financial stress.')
ASSUMPTION = ('Synthetic-data assumption: household expenses exclude debt repayments. '
              'This is not a verified fact about real employee spending. '
              'Household commitments are compared with one employee\'s income, not total household income.')
FIELDS = ('Monthly_Base_Salary_LKR', 'Monthly_Allowances_LKR',
          'Monthly_Household_Expenses_LKR', 'Monthly_Debt_Payments_LKR')


def adjustment(row, scores):
    """Return an unavailable result for unsafe inputs; never impute or mutate."""
    result = {'available': False, 'reason': None, 'original_formula': 'additive',
              'original_eesi': scores.get('additive'), 'total_monthly_income': None,
              'household_expenses': None, 'debt_repayments': None,
              'financial_commitments': None, 'burden_percentage': None,
              'burden_raw': None, 'burden_capped': None, 'debt_service_ratio': None,
              'adjusted_eesi': None, 'difference': None, 'comparisons': {},
              'survey_month': row.get('Survey_Month'),
              'disclaimer': DISCLAIMER, 'assumption': ASSUMPTION}
    try:
        values = {}
        for field in FIELDS:
            value = row.get(field)
            if isinstance(value, bool):
                raise ValueError(f'{field} must be a finite nonnegative number.')
            try:
                number = float(value)
            except (TypeError, ValueError, OverflowError):
                raise ValueError(f'{field} is missing or invalid.') from None
            if not math.isfinite(number) or number < 0:
                raise ValueError(f'{field} must be a finite nonnegative number.')
            values[field] = number
        income = values[FIELDS[0]] + values[FIELDS[1]]
        expenses, debt = values[FIELDS[2]], values[FIELDS[3]]
        commitments = expenses + debt
        result.update(total_monthly_income=income if math.isfinite(income) else None,
                      household_expenses=expenses, debt_repayments=debt,
                      financial_commitments=commitments if math.isfinite(commitments) else None)
        if not math.isfinite(income) or not math.isfinite(commitments):
            raise ValueError('Financial totals exceed the supported numeric range.')
        if income <= 0:
            raise ValueError('Total monthly income must be greater than zero.')
        for name in ('economic', 'additive', 'interaction'):
            score = scores.get(name)
            if score is None:
                continue
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= 100:
                raise ValueError(f'Original {name} score is invalid.')
        if scores.get('additive') is None:
            raise ValueError('Original Formula B score is unavailable.')
        raw = commitments / income
        dsr = debt / income
        if not math.isfinite(raw) or not math.isfinite(dsr):
            raise ValueError('Financial ratios exceed the supported numeric range.')
        burden = min(1.0, raw)
        comparisons = {name: {'original': scores[name],
                              'adjusted': 0.70 * scores[name] + 0.30 * (100 * burden)}
                       for name in ('economic', 'additive', 'interaction') if scores.get(name) is not None}
        for comparison in comparisons.values():
            comparison['difference'] = comparison['adjusted'] - comparison['original']
        main = comparisons['additive']
        result.update(available=True, burden_percentage=100 * burden,
                      burden_raw=raw, burden_capped=burden, debt_service_ratio=dsr,
                      adjusted_eesi=main['adjusted'], difference=main['difference'], comparisons=comparisons)
    except ValueError as error:
        result['reason'] = str(error)
    return result


def extended_formulas(eesi, financial):
    """B2/C2 reuse validated financial ratios; original EESI remains untouched."""
    result = {'available': False, 'reason': financial.get('reason'), 'scores': {},
              'differences': {}, 'contributions': {}}
    if not financial['available']:
        return result
    components = eesi.get('components', {})
    for key in ('inflation', 'cpi', 'unemployment', 'salary_exposure'):
        value = components.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
            result['reason'] = f'Normalized {key} is missing or invalid.'
            return result
    i, c, u, v = (components[key] for key in ('inflation', 'cpi', 'unemployment', 'salary_exposure'))
    f = financial['burden_capped']
    b2 = 100 * (i + c + u + v + f) / 5
    c2 = 100 * ((i + c + u) / 3) * ((v + f) / 2)
    result.update(available=True, reason=None, scores={'B2': b2, 'C2': c2},
                  differences={'B2_minus_B': b2 - eesi['scores']['additive'],
                               'C2_minus_C': c2 - eesi['scores']['interaction']},
                  contributions={
                      'B2': {'inflation': 20 * i, 'cpi': 20 * c, 'unemployment': 20 * u,
                             'salary_exposure': 20 * v, 'financial_burden': 20 * f},
                      'C2': {'inflation': 100 * i / 3 * ((v + f) / 2),
                             'cpi': 100 * c / 3 * ((v + f) / 2),
                             'unemployment': 100 * u / 3 * ((v + f) / 2)}})
    return result

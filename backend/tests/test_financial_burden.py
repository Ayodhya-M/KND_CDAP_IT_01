import copy

import pytest

from app.services.eesi import calculate
from app.services.financial_burden import adjustment, extended_formulas


def financial_row(**changes):
    return {**dict(Monthly_Base_Salary_LKR=40000, Monthly_Allowances_LKR=10000,
                   Annual_Bonus_LKR=120000, Monthly_Household_Expenses_LKR=20000,
                   Monthly_Debt_Payments_LKR=5000, Survey_Month='2019-03'), **changes}


def test_hand_calculation_and_original_formulas_unchanged():
    original = calculate(50000, 32.6, 107.635, 4.7)
    before = copy.deepcopy(original)
    row = financial_row()
    row_before = dict(row)
    result = adjustment(row, original['scores'])
    assert result['available']
    assert result['total_monthly_income'] == 50000
    assert result['financial_commitments'] == 25000
    assert result['burden_percentage'] == 50
    assert result['original_eesi'] == pytest.approx(50)
    assert result['adjusted_eesi'] == pytest.approx(50)
    assert result['difference'] == pytest.approx(0)
    assert result['comparisons']['interaction']['adjusted'] == pytest.approx(32.5)
    assert original == before == calculate(50000, 32.6, 107.635, 4.7)
    assert row == row_before
    assert original['scores'] == pytest.approx(dict(economic=50, additive=50, interaction=25))
    assert set(result['comparisons']) == {'economic', 'additive', 'interaction'}
    assert adjustment(financial_row(Annual_Bonus_LKR=None), original['scores']) == result


@pytest.mark.parametrize('field', ['Monthly_Base_Salary_LKR', 'Monthly_Allowances_LKR',
                                  'Monthly_Household_Expenses_LKR', 'Monthly_Debt_Payments_LKR'])
@pytest.mark.parametrize('value', [None, '', 'invalid', -1, float('nan'), float('inf'), True])
def test_missing_and_invalid_finances_are_not_imputed(field, value):
    result = adjustment(financial_row(**{field: value}), {'additive': 50})
    assert not result['available']
    assert result['reason']
    assert result['adjusted_eesi'] is None


def test_zero_income_overflow_and_missing_column():
    for row in [financial_row(Monthly_Base_Salary_LKR=0, Monthly_Allowances_LKR=0),
                financial_row(Monthly_Base_Salary_LKR=1e308, Monthly_Allowances_LKR=1e308)]:
        assert not adjustment(row, {'additive': 50})['available']
    row = financial_row()
    del row['Monthly_Allowances_LKR']
    assert not adjustment(row, {'additive': 50})['available']


def test_burden_cap_zero_commitments_and_missing_original():
    high = adjustment(financial_row(Monthly_Household_Expenses_LKR=100000), {'additive': 50})
    assert high['burden_percentage'] == 100
    assert high['adjusted_eesi'] == 65
    assert high['difference'] == 15
    low = adjustment(financial_row(Monthly_Household_Expenses_LKR=0, Monthly_Debt_Payments_LKR=0), {'additive': 50})
    assert low['adjusted_eesi'] == 35
    assert low['difference'] == -15
    assert not adjustment(financial_row(), {})['available']


def test_extensions_hand_worked_and_independent_of_7030():
    original = calculate(50000, 32.6, 107.635, 4.7)
    before = copy.deepcopy(original)
    # T=50,000, M=40,000 => F=.8; I=C=U=V=.5.
    finance = adjustment(financial_row(Monthly_Household_Expenses_LKR=35000), original['scores'])
    assert finance['burden_raw'] == pytest.approx(.8)
    assert finance['burden_capped'] == pytest.approx(.8)
    assert finance['debt_service_ratio'] == pytest.approx(.1)
    extended = extended_formulas(original, finance)
    assert extended['available']
    assert extended['scores'] == pytest.approx({'B2': 56, 'C2': 32.5})
    assert extended['differences'] == pytest.approx({'B2_minus_B': 6, 'C2_minus_C': 7.5})
    assert finance['adjusted_eesi'] == pytest.approx(59)
    for formula, parts in extended['contributions'].items():
        assert sum(parts.values()) == pytest.approx(extended['scores'][formula])
    assert original == before


@pytest.mark.parametrize('commitments', [0, 25000, 50000, 100000])
def test_extensions_bounded_and_capping_retains_raw(commitments):
    original = calculate(40000, 32.6, 107.635, 4.7)
    finance = adjustment(financial_row(Monthly_Household_Expenses_LKR=commitments,
                                      Monthly_Debt_Payments_LKR=0), original['scores'])
    assert finance['burden_raw'] == commitments / 50000
    assert finance['burden_capped'] == min(1, commitments / 50000)
    extended = extended_formulas(original, finance)
    assert all(0 <= score <= 100 for score in extended['scores'].values())


def test_extensions_invalid_inputs_and_ratio_overflow():
    original = calculate(50000, 32.6, 107.635, 4.7)
    financial = adjustment(financial_row(Monthly_Allowances_LKR=None), original['scores'])
    assert not extended_formulas(original, financial)['available']
    financial = adjustment(financial_row(), original['scores'])
    original['components']['inflation'] = None
    assert not extended_formulas(original, financial)['available']
    financial = adjustment(financial_row(Monthly_Base_Salary_LKR=1e-308, Monthly_Allowances_LKR=0,
                                        Monthly_Household_Expenses_LKR=1e308), {'additive': 50})
    assert not financial['available']

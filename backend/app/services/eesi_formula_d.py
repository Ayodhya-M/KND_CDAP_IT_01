"""Proposed real-wage index; deliberately separate from candidates A/B/C."""
import math
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


FORMULA_ID = 'real_wage'
VERSION = 'real-wage-hies2019-v1'
# These parameters belong ONLY to the HIES 2019 demonstration.
HIES2019_UNEMPLOYMENT = (4.5, 5.1)


class FormulaDConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')
    reference_income_2013: float | None = Field(default=None, gt=0, allow_inf_nan=False)
    alpha: float = Field(default=0.5, ge=0, le=1, allow_inf_nan=False)
    reference_income_source: str = ''
    reference_income_justification: str = ''
    cpi_base_year: Literal[2013] = 2013
    normalization_profile: Literal['hies2019'] = 'hies2019'

    @field_validator('reference_income_2013', 'alpha', mode='before')
    @classmethod
    def reject_boolean(cls, value):
        if isinstance(value, bool):
            raise ValueError('A finite number is required, not a boolean.')
        return value


class FormulaDInputs(FormulaDConfig):
    reference_income_2013: float = Field(gt=0, allow_inf_nan=False)
    employee_wage: float = Field(ge=0, allow_inf_nan=False)
    ncpi: float = Field(gt=0, allow_inf_nan=False)
    unemployment_rate: float = Field(ge=0, allow_inf_nan=False)

    @field_validator('employee_wage', 'ncpi', 'unemployment_rate', mode='before')
    @classmethod
    def reject_boolean_input(cls, value):
        return cls.reject_boolean(value)


def assumptions(config: FormulaDConfig) -> dict:
    return {
        'formula_id': FORMULA_ID, 'version': VERSION,
        'name': 'Formula D — Real-Wage Economic Exposure Index',
        'expression': '100 × (alpha × wage_gap + (1 − alpha) × normalized_unemployment)',
        'configuration': config.model_dump(),
        'cpi_base': 'National Consumer Price Index, 2013=100',
        'real_wage_units': 'monthly LKR at 2013 purchasing power',
        'normalization': {'profile': 'hies2019', 'unemployment_min': 4.5,
                          'unemployment_max': 5.1, 'source': 'User-specified HIES 2019 demonstration parameters'},
        'threshold_status': 'Illustrative threshold; no defensible benchmark established by this prototype.',
        'warning': 'Proposed, unvalidated research index. Not a validated psychological financial stress scale or turnover probability.',
        'assumptions': [
            'Nominal monthly employee wages are deflated using NCPI 2013=100.',
            'Reference income must use monthly 2013 purchasing-power LKR, not current nominal LKR.',
            'Wage inadequacy and unemployment are clipped to [0,1]; clipping can mask further changes.',
            'Alpha is an illustrative weight, not an empirically validated estimate.',
            'Household expenses, loans, allowances and inflation are not direct Formula D inputs.',
            'HIES records retain their existing previous-calendar-month economic alignment.',
            '2019 normalization must not be reused for other periods without a separate profile.',
        ],
    }


def calculate_formula_d(**values) -> dict:
    inputs = FormulaDInputs(**values)
    # Decimal avoids overflow in wage*100 before division for finite large wages.
    real_wage = float(Decimal(str(inputs.employee_wage)) * 100 / Decimal(str(inputs.ncpi)))
    if not math.isfinite(real_wage):
        raise ValueError('Derived real_wage exceeds the supported finite numeric range.')
    gap = max(0.0, min(1.0, 1 - real_wage / inputs.reference_income_2013))
    low, high = HIES2019_UNEMPLOYMENT
    unemployment = max(0.0, min(1.0, (inputs.unemployment_rate - low) / (high - low)))
    contributions = {'wage_inadequacy': 100 * inputs.alpha * gap,
                     'unemployment': 100 * (1 - inputs.alpha) * unemployment}
    return {'inputs': inputs.model_dump(), 'real_wage': real_wage,
            'wage_inadequacy': gap, 'normalized_unemployment': unemployment,
            'score': max(0.0, min(100.0, sum(contributions.values()))), 'contributions': contributions,
            'metadata': assumptions(inputs)}


def compare_dataset(dataset: dict, config: FormulaDConfig) -> dict:
    enabled = config.reference_income_2013 is not None
    return {
        'enabled': enabled,
        'message': 'Formula D is enabled with an illustrative threshold.' if enabled else
                   'Formula D is disabled: configure a positive monthly reference income in 2013 purchasing-power LKR.',
        'metadata': assumptions(config),
        'records': [dict(sample_id=row['sample_id'], survey_month=row['survey_month'],
                         economic_month=row['economic_month'], **calculate_formula_d(
                             **config.model_dump(), employee_wage=row['salary'],
                             ncpi=row['cpi'], unemployment_rate=row['unemployment']))
                    for row in dataset['records']] if enabled else [],
    }

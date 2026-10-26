"""Adapter from Module 1 contexts to Module 2's implemented EESI service."""

from decimal import Decimal

from app.module4.providers.base import ProviderMetadata, ProviderResultUnavailableError
from app.module4.schemas.integration import Module1EconomicContext, Module1EmployeeContext, Module2EESIResult
from app.services.eesi import BOUNDS, FORMULAS, VERSION, calculate
from app.services.eesi_real import REAL_BOUNDS, REAL_VERSION


SUPPORTED_FORMULA_IDS = frozenset(formula["id"] for formula in FORMULAS)
SUPPORTED_REFERENCE_PROFILES = frozenset({"pilot", "lfs2024"})


class RealModule2Provider:
    """Run real Module 2 arithmetic without choosing research policy.

    Module 2 has not yet approved a final formula or pressure thresholds. The
    formula must therefore be explicitly configured and the returned pressure
    classification is marked ``Unavailable`` rather than inferred here.
    """

    metadata = ProviderMetadata(source="module2", data_mode="integrated", is_mock=False)

    def __init__(self, *, formula_identifier: str | None, reference_profile: str = "pilot") -> None:
        self.formula_identifier = formula_identifier.strip() if formula_identifier else None
        self.reference_profile = reference_profile.strip().lower()

    def get_eesi_result(
        self,
        employee: Module1EmployeeContext,
        economic_context: Module1EconomicContext | None,
    ) -> Module2EESIResult:
        if self.formula_identifier is None:
            raise ProviderResultUnavailableError(
                "Module 2 real provider is unavailable: no EESI formula has been approved/configured"
            )
        if self.formula_identifier not in SUPPORTED_FORMULA_IDS:
            raise ProviderResultUnavailableError(
                f"Module 2 real provider is unavailable: unsupported EESI formula '{self.formula_identifier}'"
            )
        if self.reference_profile not in SUPPORTED_REFERENCE_PROFILES:
            raise ProviderResultUnavailableError(
                f"Module 2 real provider is unavailable: unsupported reference profile '{self.reference_profile}'"
            )
        if economic_context is None:
            raise ProviderResultUnavailableError(
                "Module 2 real provider is unavailable: employee has no mapped economic context"
            )

        salary = self._required_positive(employee.salary, "salary")
        inflation = self._required(economic_context.inflation_rate, "inflation_rate")
        cpi = self._required_positive(economic_context.cpi_index, "cpi_index")
        unemployment = self._required(economic_context.unemployment_rate, "unemployment_rate")
        bounds = REAL_BOUNDS if self.reference_profile == "lfs2024" else BOUNDS
        version = REAL_VERSION if self.reference_profile == "lfs2024" else VERSION

        try:
            calculation = calculate(
                salary=salary,
                inflation=inflation,
                cpi=cpi,
                unemployment=unemployment,
                bounds=bounds,
                version=version,
            )
        except ValueError as error:
            raise ProviderResultUnavailableError(
                f"Module 2 real provider could not calculate EESI: {error}"
            ) from error

        score = float(calculation["scores"][self.formula_identifier])
        if not 0 <= score <= 100:
            raise ProviderResultUnavailableError("Module 2 returned an EESI score outside its 0-100 contract")
        return Module2EESIResult(
            employee_id=employee.employee_id,
            eesi_score=score,
            economic_pressure_level="Unavailable",
            score_scale="0-100",
            formula_identifier=self.formula_identifier,
            formula_version=str(calculation["version"]),
            reference_profile=self.reference_profile,
        )

    @staticmethod
    def _required(value: Decimal | None, field_name: str) -> float:
        if value is None:
            raise ProviderResultUnavailableError(
                f"Module 2 real provider is unavailable: required {field_name} is missing"
            )
        return float(value)

    @classmethod
    def _required_positive(cls, value: Decimal | None, field_name: str) -> float:
        number = cls._required(value, field_name)
        if number <= 0:
            raise ProviderResultUnavailableError(
                f"Module 2 real provider is unavailable: required {field_name} must be greater than zero"
            )
        return number

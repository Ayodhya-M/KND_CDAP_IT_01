"""Read-only access to employee and mapped economic data owned by Module 1."""

from typing import Any
from uuid import UUID

from pydantic import ValidationError
from supabase import Client

from app.module4.schemas.integration import Module1EconomicContext, Module1EmployeeContext
from app.supabase_client import get_supabase_client


EMPLOYEE_COLUMNS = ",".join(
    (
        "id", "upload_id", "employee_id", "age", "gender", "salary", "department",
        "job_role", "job_level", "business_travel", "distance_from_home",
        "education_field", "marital_status", "overtime", "job_satisfaction",
        "environment_satisfaction", "work_life_balance", "total_working_years",
        "years_at_company", "join_date", "resignation_date", "observation_date",
        "attrition", "raw_data", "created_at",
    )
)
ECONOMIC_COLUMNS = ",".join(
    (
        "id", "upload_id", "indicator_month", "inflation_rate", "unemployment_rate",
        "cost_of_living_index", "cpi_index", "policy_interest_rate_percent",
        "usd_lkr_exchange_rate", "gdp_growth_rate_percent",
    )
)


class EmployeeRepositoryError(RuntimeError):
    """Base error for Module 1 read failures or invalid stored records."""


class EmployeeNotFoundError(EmployeeRepositoryError):
    """Raised when an employee context is required but does not exist."""


class AmbiguousEmployeeError(EmployeeRepositoryError):
    """Raised when an external employee ID occurs in more than one upload."""


class EmployeeRepository:
    """Translate Module 1 database rows into stable Module 4 schemas.

    A client can be injected for unit tests. Production code reuses the shared
    application Supabase client factory. Every query in this repository is
    read-only.
    """

    def __init__(self, client: Client | None = None) -> None:
        self._client = client or get_supabase_client()

    def get_employee_by_employee_id(
        self, employee_id: str, *, upload_id: UUID | str | None = None,
    ) -> Module1EmployeeContext | None:
        """Find an employee by external HR ID, optionally within one upload."""
        normalized_id = self._validate_employee_id(employee_id)
        try:
            query = (
                self._client.table("employee_records")
                .select(EMPLOYEE_COLUMNS)
                .eq("employee_id", normalized_id)
            )
            if upload_id is not None:
                query = query.eq("upload_id", str(upload_id))
            response = query.limit(2).execute()
        except Exception as error:
            raise EmployeeRepositoryError("Unable to read Module 1 employee data") from error

        rows = response.data or []
        if not rows:
            return None
        if len(rows) > 1:
            raise AmbiguousEmployeeError(
                f"Employee ID '{normalized_id}' occurs in multiple uploads; provide upload_id"
            )
        return self._employee_from_row(rows[0])

    def get_employee_context(
        self, employee_id: str, *, upload_id: UUID | str | None = None,
    ) -> Module1EmployeeContext:
        """Return validated employee context or raise a clear not-found error."""
        employee = self.get_employee_by_employee_id(employee_id, upload_id=upload_id)
        if employee is None:
            raise EmployeeNotFoundError(f"Employee ID '{employee_id.strip()}' was not found")
        return employee

    def get_employee_economic_context(self, employee_record_id: UUID | str) -> Module1EconomicContext | None:
        """Return the newest successfully mapped economic row for an internal UUID.

        This avoids ``integrated_records`` and follows the verified Module 1
        foreign keys through ``temporal_mappings``. A missing/unmapped context
        is represented by ``None``.
        """
        try:
            internal_id = str(UUID(str(employee_record_id)))
        except (TypeError, ValueError, AttributeError) as error:
            raise ValueError("employee_record_id must be a valid UUID") from error

        try:
            response = (
                self._client.table("temporal_mappings")
                .select(f"economic_indicators({ECONOMIC_COLUMNS})")
                .eq("employee_record_id", internal_id)
                .eq("mapping_status", "mapped")
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
        except Exception as error:
            raise EmployeeRepositoryError("Unable to read Module 1 economic mapping") from error

        rows = response.data or []
        if not rows or not rows[0].get("economic_indicators"):
            return None
        try:
            return Module1EconomicContext.model_validate(rows[0]["economic_indicators"])
        except ValidationError as error:
            raise EmployeeRepositoryError("Module 1 returned an invalid economic record") from error

    @staticmethod
    def _validate_employee_id(employee_id: str) -> str:
        if not isinstance(employee_id, str) or not employee_id.strip():
            raise ValueError("employee_id must be a non-empty external HR identifier")
        return employee_id.strip()

    @staticmethod
    def _employee_from_row(row: dict[str, Any]) -> Module1EmployeeContext:
        try:
            return Module1EmployeeContext.model_validate(row)
        except ValidationError as error:
            raise EmployeeRepositoryError("Module 1 returned an invalid employee record") from error

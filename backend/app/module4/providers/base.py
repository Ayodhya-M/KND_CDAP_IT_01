"""Replaceable provider contracts for upstream research modules."""

from dataclasses import dataclass
from typing import Protocol

from app.module4.schemas.integration import (
    Module1EconomicContext,
    Module1EmployeeContext,
    Module2EESIResult,
    Module3PredictionResult,
)


@dataclass(frozen=True)
class ProviderMetadata:
    """Describe the provenance of data returned by an integration provider."""

    source: str
    data_mode: str
    is_mock: bool


class ProviderResultUnavailableError(RuntimeError):
    """Raised when an upstream provider has no result for an employee."""


class Module2Provider(Protocol):
    """Contract that a mock or real Module 2 adapter must implement."""

    metadata: ProviderMetadata

    def get_eesi_result(
        self,
        employee: Module1EmployeeContext,
        economic_context: Module1EconomicContext | None,
    ) -> Module2EESIResult: ...


class Module3Provider(Protocol):
    """Contract that a mock or real Module 3 adapter must implement."""

    metadata: ProviderMetadata

    def get_prediction(self, employee: Module1EmployeeContext) -> Module3PredictionResult: ...

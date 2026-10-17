"""Proof-of-concept Module 4 recommendation endpoint."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from app.config import Settings, get_settings
from app.module4.providers.base import ProviderResultUnavailableError
from app.module4.providers.mock_module2_provider import MockModule2Provider
from app.module4.providers.mock_module3_provider import MockModule3Provider
from app.module4.providers.real_module2_provider import RealModule2Provider
from app.module4.providers.real_module3_provider import RealModule3Provider
from app.module4.repositories.employee_repository import (
    AmbiguousEmployeeError,
    EmployeeNotFoundError,
    EmployeeRepository,
    EmployeeRepositoryError,
)
from app.module4.schemas.decision_support import Module4RecommendationResponse
from app.module4.services.decision_service import RetentionDecisionService


router = APIRouter(prefix="/module4", tags=["Module 4 - Retention decision support"])
logger = logging.getLogger(__name__)


def build_module2_provider(settings: Settings):
    if settings.module2_provider == "real":
        return RealModule2Provider(
            formula_identifier=settings.module2_eesi_formula,
            reference_profile=settings.module2_reference_profile,
        )
    return MockModule2Provider()


def build_module3_provider(settings: Settings):
    if settings.module3_provider == "real":
        return RealModule3Provider(positive_class_label=settings.module3_positive_class_label)
    return MockModule3Provider()


def get_decision_service() -> RetentionDecisionService:
    """Compose configured providers without silently falling back to mocks.

    Mock remains the safe default. Selecting a real provider with an incomplete
    research contract produces a clear 503 response from that provider.
    """
    settings = get_settings()
    return RetentionDecisionService(
        employee_repository=EmployeeRepository(),
        module2_provider=build_module2_provider(settings),
        module3_provider=build_module3_provider(settings),
    )


@router.get(
    "/employees/{employee_id}/recommendations",
    response_model=Module4RecommendationResponse,
    summary="Generate configured retention decision support",
)
def employee_recommendations(
    employee_id: str,
    service: Annotated[RetentionDecisionService, Depends(get_decision_service)],
) -> Module4RecommendationResponse:
    """Use real Module 1 data with explicit upstream-provider provenance."""
    try:
        return service.recommendations_for_employee(employee_id)
    except EmployeeNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    except AmbiguousEmployeeError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except ProviderResultUnavailableError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    except ValidationError as error:
        logger.exception("Module 4 received mismatching or invalid integration data")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="An upstream Module 2 or Module 3 result did not match the employee context",
        ) from error
    except EmployeeRepositoryError as error:
        logger.exception("Module 4 could not read Module 1 data")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)) from error

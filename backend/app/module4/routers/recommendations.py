"""Proof-of-concept Module 4 recommendation endpoint."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from app.module4.providers.base import ProviderResultUnavailableError
from app.module4.providers.mock_module2_provider import MockModule2Provider
from app.module4.providers.mock_module3_provider import MockModule3Provider
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


def get_decision_service() -> RetentionDecisionService:
    """Compose the current development providers behind stable interfaces.

    Replace only this composition with real Module 2/3 adapters later; the
    decision-support services do not import or depend on the mock classes.
    """
    return RetentionDecisionService(
        employee_repository=EmployeeRepository(),
        module2_provider=MockModule2Provider(),
        module3_provider=MockModule3Provider(),
    )


@router.get(
    "/employees/{employee_id}/recommendations",
    response_model=Module4RecommendationResponse,
    summary="Generate mock-integrated retention decision support",
)
def employee_recommendations(
    employee_id: str,
    service: Annotated[RetentionDecisionService, Depends(get_decision_service)],
) -> Module4RecommendationResponse:
    """Use real Module 1 data with clearly labelled Module 2/3 mock fixtures."""
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

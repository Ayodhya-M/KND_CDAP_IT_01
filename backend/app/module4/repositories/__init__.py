"""Read-only repositories used by Module 4."""

from app.module4.repositories.employee_repository import (
    AmbiguousEmployeeError,
    EmployeeNotFoundError,
    EmployeeRepository,
    EmployeeRepositoryError,
)

__all__ = [
    "AmbiguousEmployeeError",
    "EmployeeNotFoundError",
    "EmployeeRepository",
    "EmployeeRepositoryError",
]

"""Provider abstractions for Module 2 and Module 3 integrations."""

from app.module4.providers.base import (
    Module2Provider,
    Module3Provider,
    ProviderMetadata,
    ProviderResultUnavailableError,
)

__all__ = [
    "Module2Provider",
    "Module3Provider",
    "ProviderMetadata",
    "ProviderResultUnavailableError",
]

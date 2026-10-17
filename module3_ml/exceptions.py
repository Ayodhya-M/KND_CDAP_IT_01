class DataContractError(ValueError):
    """Raised when input data does not meet the documented contract."""


class ModelArtifactError(RuntimeError):
    """Raised when a saved model artifact is missing or invalid."""

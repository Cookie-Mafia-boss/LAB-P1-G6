"""Custom exceptions used by the data layer."""


class DataLayerError(Exception):
    """Base exception for errors raised by the data layer."""


class DatabaseConnectionError(DataLayerError):
    """Raised when the application cannot connect to the database."""


class RecordNotFoundError(DataLayerError):
    """Raised when a requested food item does not exist."""


class DuplicateRecordError(DataLayerError):
    """Raised when an item with the same serial number already exists."""


class DataValidationError(DataLayerError):
    """Raised when data cannot be converted into a valid food item."""

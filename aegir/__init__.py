"""A minimal package to support configuration files without any additional work."""

from aegir.entry import ConfigEntry, check_attributes
from aegir.exceptions import (
    AegirException,
    ConfigurationError,
    ConfigurationKeyError,
    InvalidOperation,
    PathConflict,
)
from aegir.file import check_constructors, load, load_stream

__version__ = "1.0.2"

__all__ = (
    # Main API
    "ConfigEntry",
    "load",
    "load_stream",
    "check_constructors",
    "check_attributes",
    # Exceptions
    "AegirException",
    "ConfigurationKeyError",
    "PathConflict",
    "InvalidOperation",
    "ConfigurationError",
)

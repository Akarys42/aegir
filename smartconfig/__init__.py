"""A minimal package to support configuration files without any additional work."""

from smartconfig.entry import ConfigEntry, check_attributes
from smartconfig.exceptions import (
    ConfigurationError,
    ConfigurationKeyError,
    InvalidOperation,
    PathConflict,
    SmartconfigException
)
from smartconfig.file import check_constructors, load, load_stream

__version__ = "0.0.0-dev1"

__all__ = (
    # Main API
    "ConfigEntry", "load", "load_stream", "check_constructors", "check_attributes",

    # Exceptions
    "SmartconfigException", "ConfigurationKeyError", "PathConflict", "InvalidOperation", "ConfigurationError",
)

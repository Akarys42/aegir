"""A minimal package to support configuration files without any additional work."""

from smartconfig.entry import ConfigEntry
from smartconfig.exceptions import (
    ConfigurationError,
    ConfigurationKeyError,
    InvalidOperation,
    PathConflict,
    SmartconfigException
)
from smartconfig.file import load, load_stream

__version__ = "0.0.0-dev1"

__all__ = (
    # Main API
    "ConfigEntry", "load", "load_stream",

    # Exceptions
    "SmartconfigException", "ConfigurationKeyError", "PathConflict", "InvalidOperation", "ConfigurationError",
)

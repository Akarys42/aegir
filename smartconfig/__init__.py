"""A minimal package to support configuration files without any additional work."""

from smartconfig.entry import ConfigEntry
from smartconfig.exceptions import (
    ConfigurationError,
    ConfigurationKeyError,
    InvalidOperation,
    PathConflict,
    SmartconfigException
)
from smartconfig.file import load

__version__ = "0.0.0-dev1"

__all__ = (
    # Main API
    "ConfigEntry", "load",

    # Exceptions
    "SmartconfigException", "ConfigurationKeyError", "PathConflict", "InvalidOperation", "ConfigurationError",
)

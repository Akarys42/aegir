"""A minimal package to support configuration files without any additional work."""

from smartconfig.config_files import load
from smartconfig.entry import ConfigEntry
from smartconfig.exceptions import (
    ConfigurationKeyError,
    DuplicateConfiguration,
    InvalidOperation,
    MalformedYamlFile,
    SmartconfigException
)
from smartconfig.typehints import EntryType

__version__ = "0.0.0-dev1"

__all__ = (
    # Main API
    "ConfigEntry", "load",

    # Exceptions
    "SmartconfigException", "DuplicateConfiguration", "ConfigurationKeyError", "InvalidOperation",
    "MalformedYamlFile",

    # Typehinting
    "EntryType",
)

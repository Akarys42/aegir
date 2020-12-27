"""A minimal package to support configuration files without any additional work."""

__version__ = "0.0.0-dev1"

__all__ = (
    # Main API
    "ConfigEntry", "load_config_file",

    # Exceptions
    "SmartconfigBaseException", "DuplicateConfiguration", "ConfigurationKeyError", "InvalidOperation",
    "MalformedYamlFile",

    # Typehinting
    "EntryType",
)

from smartconfig.config_files import load_config_file
from smartconfig.entry import ConfigEntry
from smartconfig.exceptions import (
    ConfigurationKeyError,
    DuplicateConfiguration,
    InvalidOperation,
    MalformedYamlFile,
    SmartconfigBaseException
)
from smartconfig.typehints import EntryType

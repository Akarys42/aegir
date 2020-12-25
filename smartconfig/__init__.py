"""A minimal package to support configuration files without any additional work."""

__version__ = "0.0.0-dev1"

__all__ = (
    # Main API
    "ConfigEntry", "load_config_file",

    # Exceptions
    "SmartconfigBaseException", "DuplicateConfiguration", "ConfigurationKeyError", "InvalidOperation",
    "MalformedYamlFile",

    # Utilities
    "YamlLikeParser",

    # Typehinting
    "EntryType",
)

from smartconfig.configuration import ConfigEntry, load_config_file
from smartconfig.exceptions import (
    SmartconfigBaseException,
    DuplicateConfiguration,
    ConfigurationKeyError,
    InvalidOperation,
    MalformedYamlFile
)
from smartconfig.parser import YamlLikeParser
from smartconfig.typehints import EntryType

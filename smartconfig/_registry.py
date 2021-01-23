"""
Internal register used to reference entries.

Attributes:
    global_configuration: A mapping of dotted paths to a mapping of attribute names and its value.
    configuration_for_module: A mapping of dotted paths to the corresponding entry.
"""

from typing import Dict, Optional

import smartconfig
from smartconfig.typehints import EntryType, _EntryMappingRegistry
from .exceptions import ConfigurationError, ConfigurationKeyError

global_configuration: _EntryMappingRegistry = {}
configuration_for_module: Dict[str, "smartconfig.ConfigEntry"] = {}


def lookup_global_configuration(path: str, attribute: Optional[str]) -> EntryType:
    """
    Returns the `attribute` at the `path` in the global configuration.

    Args:
        path: The entry path to use.
        attribute: The attribute to look up. The whole entry mapping will be returned if None.

    Returns:
        The attribute or the whole entry mapping if `attribute` is None.

    Raises:
        ConfigurationKeyError: The path or the attribute doesn't exist, or the YAML object isn't an attribute mapping.
    """
    if path not in global_configuration:
        raise ConfigurationKeyError(f"No override exists for the path {path}.")

    if not attribute:
        entry = global_configuration[path]
    else:
        mapping = global_configuration[path]

        if not isinstance(mapping, dict):
            raise ConfigurationError(f"YAML object at path {path} is a set attribute, not an attribute mapping.")

        if attribute not in mapping:
            raise ConfigurationKeyError(f"No attribute {attribute} exists for the path {path}.")

        entry = mapping[attribute]

    # Use __get__ if the attribute is a descriptor
    if hasattr(entry, '__get__'):
        entry = entry.__get__()

    return entry

"""
Internal register used to reference entries.

Attributes:
    global_configuration: A mapping of dotted paths to a mapping of attribute names and its value.
    configuration_for_module: A mapping of dotted paths to the corresponding entry.
"""

from typing import Dict, Optional

import smartconfig
from smartconfig.typehints import EntryType, YAMLStructure, _EntryMapping
from .exceptions import ConfigurationError, ConfigurationKeyError

global_configuration: YAMLStructure = {}
configuration_for_module: Dict[str, "smartconfig.ConfigEntry"] = {}

mapping_cache: Dict[str, _EntryMapping] = {}


def _lookup_mapping(path: str) -> _EntryMapping:
    """
    Lookup a mapping node.

    Will try to use the mapping_cache when possible.

    Args:
         path: Dotted path of the mapping to lookup.

    Returns:
        The entry mapping at the requested path.

    Raises:
        ConfigurationKeyError: No override exists for this path.
    """
    if path in mapping_cache:
        return mapping_cache[path]

    current_node = global_configuration

    for node_name in path.split('.'):
        if not isinstance(current_node, dict):
            raise ConfigurationError(
                f"YAML object {node_name} on the path {path} is a set attribute, not an attribute mapping."
            )

        if node_name not in current_node:
            raise ConfigurationKeyError(f"No override exists for the path {path!r}.")

        current_node = current_node[node_name]

    mapping_cache[path] = current_node
    return current_node


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
    node = _lookup_mapping(path)

    if not attribute:
        entry = node
    else:
        mapping = node

        if not isinstance(mapping, dict):
            raise ConfigurationError(f"YAML object at path {path} is a set attribute, not an attribute mapping.")

        if attribute not in mapping:
            raise ConfigurationKeyError(f"No attribute {attribute} exists for the path {path}.")

        entry = mapping[attribute]

    # Use __get__ if the attribute is a descriptor
    if hasattr(entry, '__get__'):
        entry = entry.__get__()

    return entry

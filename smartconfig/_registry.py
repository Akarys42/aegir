"""
Internal register used to reference entries.

Attributes:
    global_configuration: A mapping of dot-delimited paths to a mapping of attribute names and their values.
    used_paths: A set of paths already containing an entry.
    overwritten_attributes: A set of paths that have been overwritten by a configuration file.
"""

from typing import Dict, Optional, Set, Union

import smartconfig
from smartconfig.typehints import EntryType, YAMLStructure, _EntryMapping
from .exceptions import ConfigurationError, ConfigurationKeyError

global_configuration: YAMLStructure = {}
used_paths: Set["smartconfig.ConfigEntry"] = set()
overwritten_attributes: Set[str] = set()

mapping_cache: YAMLStructure = {}


def _get_node(path: str) -> EntryType:
    """
    Retrieve the node located at `path` from the global configuration.

    Try to use the mapping_cache when possible.

    Args:
         path: The dot-delimited path to the node.

    Returns:
        The node at the requested path.

    Raises:
        ConfigurationError: A node along the path is not a mapping node.
        ConfigurationKeyError: The path does not exist.
    """
    if path in mapping_cache:
        return mapping_cache[path]

    current_node = global_configuration

    for node_name in path.split('.'):
        if not isinstance(current_node, dict):
            raise ConfigurationError(f"Cannot retrieve {path!r}: the YAML node {node_name!r} is not a mapping node.")

        if node_name not in current_node:
            raise ConfigurationKeyError(f"Cannot retrieve {path!r}: {node_name!r} does not exist.")

        current_node = current_node[node_name]

    mapping_cache[path] = current_node
    return current_node


def _unload_defaults(path: str) -> None:
    """
    Remove the default values of all child attributes at `path`.

    Args:
        path: The dot-delimited path to the parent node.
    """
    try:
        node = lookup_global_configuration(path, None)
    except (ConfigurationError, ConfigurationKeyError):
        return

    for attribute in node.copy():
        if attribute not in overwritten_attributes:
            node.pop(attribute)


def lookup_global_configuration(path: str, attribute: Optional[str]) -> Union[dict, EntryType]:
    """
    Return the `attribute` at the `path` in the global configuration.

    Args:
        path: The dot-delimited path to the parent of the attribute to find.
        attribute: The name of the attribute to find. If None, return a dictionary of all attributes under the path.

    Returns:
        The value of the attribute or a dictionary of all child attributes if `attribute` is None.

    Raises:
        ConfigurationError: A node along the path is not a mapping node.
        ConfigurationKeyError: The path or the attribute doesn't exist, or the path does not consist of mapping nodes.
    """
    node = _get_node(path)

    if not attribute:
        entry = node
    else:
        mapping = node

        if not isinstance(mapping, dict):
            raise ConfigurationError(f"Cannot retrieve {attribute!r}: YAML node at {path!r} is not a mapping node.")

        if attribute not in mapping:
            raise ConfigurationKeyError(f"Cannot retrieve {attribute!r}: attribute does not exist at {path!r}.")

        entry = mapping[attribute]

    # Use __get__ if the attribute is a descriptor
    if hasattr(entry, '__get__'):
        entry = entry.__get__()

    return entry

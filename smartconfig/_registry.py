"""
Internal register used to reference entries.

Attributes:
    global_configuration: The full configuration loaded from the YAML file along with all default values for entries.
    used_paths: A set of paths already containing an entry.
    overwritten_attributes: A set of paths that have been overwritten by a configuration file.
    mapping_cache: A mapping of dot-delimited paths to their corresponding mappings in the config.
"""

import copy
from typing import Any, Dict, Hashable, Mapping, MutableMapping, Set

import smartconfig
from .exceptions import ConfigurationError, ConfigurationKeyError

global_configuration: Dict[Hashable, Any] = {}
used_paths: Set["smartconfig.ConfigEntry"] = set()
overwritten_attributes: Set[str] = set()
mapping_cache: Dict[str, Mapping] = {}


def _get_child_node(node_name: str, root: Any) -> Any:
    """
    Retrieve the value of the node `node_name` which is a child of the `root` node.

    Args:
        node_name: The name of the child node to retrieve.
        root: The parent node of the node to retrieve.

    Returns:
        The value of the child node.

    Raises:
        ConfigurationError: The parent is not a mapping node.
        ConfigurationKeyError: The child node does not exist.
    """
    if not isinstance(root, Mapping):
        raise ConfigurationError(f"Cannot retrieve node {node_name!r}: its parent is not a mapping node.")

    if node_name not in root:
        raise ConfigurationKeyError(f"Cannot retrieve node {node_name!r}: it does not exist.")

    node = root[node_name]

    # Use __get__ if the node is a descriptor.
    if hasattr(node, '__get__'):
        node = node.__get__()

    return node


def unload_defaults(path: str) -> None:
    """
    Remove the default values of all children of `path`.

    Args:
        path: The dot-delimited path to the parent node.
    """
    try:
        node = get_node(path)
    except (ConfigurationError, ConfigurationKeyError):
        return

    if not isinstance(node, MutableMapping):
        return

    for attribute in copy.copy(node):
        if attribute not in overwritten_attributes:
            node.pop(attribute)


def get_node(path: str) -> Any:
    """
    Retrieve the value of the node located at `path` from the global configuration.

    Cache the node if it's a mapping. If the path is cached, retrieve the node from the cache.

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

    node = global_configuration

    for node_name in path.split('.'):
        node = _get_child_node(node_name, node)

    # Only cache mapping nodes.
    if isinstance(node, Mapping):
        mapping_cache[path] = node

    return node


def get_attribute(path: str, attribute: str) -> Any:
    """
    Retrieve the value of the `attribute` under `path` from the global configuration.

    Args:
        path: The dot-delimited path to the parent of the attribute to retrieve.
        attribute: The name of the attribute to find

    Returns:
        The value of the attribute.

    Raises:
        ConfigurationError: A node along the path is not a mapping node.
        ConfigurationKeyError: The path or the attribute doesn't exist.
    """
    parent = get_node(path)
    return _get_child_node(attribute, parent)

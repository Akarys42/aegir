from os import PathLike
from typing import Mapping, MutableMapping, Set, Union

import yaml

from smartconfig import ConfigurationError, _registry
from smartconfig._registry import used_paths
from smartconfig.constructors import _ref_constructor


def _update_mapping(
        source: Mapping,
        dest: MutableMapping,
        path: str = "",
        node_paths: Set[str] = set()  # noqa: B006, this is safe since we don't mutate it
) -> MutableMapping:
    """
    Recursively update the `dest` mapping with values from `source`.

    Overwrite any non-mapping value in `dest` with the value from `source`.
    Expand keys which are strings of dot-delimited paths into nested mapping nodes. For example,

    a.b.c: 1

    becomes

    a:
      b:
        c: 1

    Args:
        source: The mapping with the new values.
        dest: The mapping to update.
        path: The dot-delimited path to `dest`.
        node_paths: Set of paths to ensure that no non-mapping node is set to.

    Returns:
        The updated dest mapping.

    Raises:
        ConfigurationError: Tried to set a non-mapping attribute on a path in `node_paths`.
    """
    for key, value in source.items():
        if path:
            new_path = f"{path}.{key}"
        else:
            new_path = key

        if '.' in key:
            key, child_node = key.split('.', maxsplit=1)
            dest[key] = _update_mapping({child_node: value}, dest.get(key, {}), f"{path}.{key}", node_paths)

        elif isinstance(value, Mapping):
            dest[key] = _update_mapping(value, dest.get(key, {}), new_path, node_paths)
        else:
            if new_path in node_paths:
                raise ConfigurationError(f"Node at path {new_path!r} must be a mapping.")

            _registry.overwritten_attributes.add(new_path)
            dest[key] = value

    return dest


def load(path: Union[str, bytes, PathLike]) -> None:
    """
    Read a YAML file at `path` and update the configuration with its values.

    Overwrite default values set in `ConfigEntry` objects with values from the YAML file. A YAML node overwrites an
    attribute of a `ConfigEntry` if their paths are equal. The path of the node is the dot-delimited concatenation of
    its parents' keys with its own key. In the following example, the path of the node 'class' is 'module.class'.

    module:
      class:
        attribute_1: value

    Nodes may be fully expanded (like above), partially collapsed, or fully collapsed. A `ConfigEntry` node's definition
    could be split by using different levels of expansion. For example,

    module:
      class:
        attribute_1: value

    module.class:
      attribute_2: value

    module.class:
      attribute_3: value

    would overwrite `attribute_1` and `attribute_3` of the `ConfigEntry` for the path 'package.module'. When a key is
    defined multiple times, the last definition is the one used. Therefore, `attribute_2` is not included.

    The YAML does not strictly have to contain nodes that correspond to `ConfigEntry` objects. For example, it's valid
    to have a non-`ConfigEntry` node marked by an anchor which is later referenced in some node that does correspond to
    a `ConfigEntry`. There could be nodes that are simply not used at all. It's even valid for the root to not be a
    mapping node. Such file would effectively configure nothing, but loading it is still supported.

    A special !REF construct can be used to point to another attribute. For instance,

    module_1:
      class:
        attribute_1: value

    module_2:
      class:
        reference: !REF module_1.class.attribute_1

    module_2.class.reference will have the same value as module_1.class.attribute_1 even if it is later overwrote by
    a configuration file.

    Args:
        path: The path to the configuration file.

    Raises:
        FileNotFoundError: The configuration file doesn't exist.
        IOError: An error occurred when reading the file.
        yaml.YAMLError: PyYAML failed to load the YAML.
    """
    with open(path) as file:
        yaml_content = yaml.full_load(file)

    if isinstance(yaml_content, Mapping):
        _registry.global_configuration = _update_mapping(
            yaml_content,
            _registry.global_configuration,
            node_paths=used_paths
        )


yaml.FullLoader.add_constructor("!REF", _ref_constructor)

from os import PathLike
from typing import AnyStr, IO, Mapping, MutableMapping, Optional, Set, Type, Union

import yaml

from smartconfig import ConfigurationError, _registry
from smartconfig._registry import used_paths
from smartconfig.constructors import _ref_constructor, _unchecked_constructors


class SmartconfigYamlFullLoader(yaml.FullLoader):
    """Independent YAML loader to add constructors on it."""


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


def load(
        path: Union[AnyStr, PathLike],
        encoding: Optional[str] = None,
        yaml_loader: Type[yaml.Loader] = SmartconfigYamlFullLoader
) -> None:
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

    A !REF constructor can be used to reference another attribute of a `ConfigEntry`. For example,

    module_1:
      class:
        attribute_1: value

    module_2:
      class:
        attribute_2: !REF module_1.class.attribute_1

    would make `attribute_2` have the same value as `attribute_1`. As described above, the value of `attribute_1`
    follows the same behaviour expected for any other attribute.

    Args:
        path: The path to the configuration file.
        encoding: The encoding with which to open the file. Same as the `encoding` parameter of the `open()` built-in.
            PyYAML only supports utf-16-le, utf-16-be, and utf-8. utf-8 is assumed if the former two are not detected.
        yaml_loader: The YAML loader to use. Default to a full loader with the !REF constructor added.

    Raises:
        FileNotFoundError: The configuration file doesn't exist.
        IOError: An error occurred while reading the file.
        yaml.YAMLError: PyYAML failed to load the YAML.
        InvalidOperation: A !REF constructor contains a circular reference.
    """
    with open(path, encoding=encoding) as file:
        load_stream(file, yaml_loader)


def load_stream(stream: Union[AnyStr, IO[AnyStr]], yaml_loader: Type[yaml.Loader] = SmartconfigYamlFullLoader) -> None:
    """
    Read a YAML config from `stream` and update the configuration with its values.

    See the documentation of `smartconfig.load()`.

    Args:
        stream: The content of the YAML config to load.
            Must be a `str`, Unicode-encoded `bytes`, or readable file-like object which yields one of the former.
        yaml_loader: The YAML loader to use. Default to a full loader with the !REF constructor added.

    Raises:
        IOError: An error occurred while reading the stream.
        yaml.YAMLError: PyYAML failed to load the YAML.
        InvalidOperation: A !REF constructor contains a circular reference.
    """
    yaml_content = yaml.load(stream, Loader=yaml_loader)

    if isinstance(yaml_content, Mapping):
        _registry.global_configuration = _update_mapping(
            yaml_content,
            _registry.global_configuration,
            node_paths=used_paths
        )

    # Check constructors for circular references
    while _unchecked_constructors:
        _unchecked_constructors.pop().check_circular_reference()


SmartconfigYamlFullLoader.add_constructor("!REF", _ref_constructor)

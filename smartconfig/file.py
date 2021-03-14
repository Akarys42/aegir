import yaml
from os import PathLike
from typing import Mapping, MutableMapping, Union

from smartconfig import _registry
from smartconfig.constructors import _ref_constructor


def _update_mapping(source: Mapping, dest: MutableMapping, path: str = "") -> MutableMapping:
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

    Returns:
        The updated dest mapping.
    """
    for key, value in source.items():
        if '.' in key:
            key, child_node = key.split('.', maxsplit=1)
            dest[key] = _update_mapping({child_node: value}, dest.get(key, {}), path + key)

        elif isinstance(value, Mapping):
            dest[key] = _update_mapping(value, dest.get(key, {}), path + key)
        else:
            _registry.overwritten_attributes.add(path + key)
            dest[key] = value

    return dest


def load(path: Union[str, bytes, PathLike]) -> None:
    """
    Load a YAML configuration file and update configuration entries.

    The values set in the YAML file will override values already defined in the `ConfigEntry`.
    For each section, the name of previous sections will be concatenated in order to make the full path of the entry
    to override.

    Args:
        path: The path to the configuration file. Can be a string or an object defining `os.PathLike`.

    Raises:
        FileNotFoundError: The configuration file doesn't exist.
        IOError: An error occurred when reading the file.
    """
    with open(path) as file:
        yaml_content = yaml.full_load(file)

    if isinstance(yaml_content, Mapping):
        _registry.global_configuration = _update_mapping(yaml_content, _registry.global_configuration)


yaml.FullLoader.add_constructor("!REF", _ref_constructor)

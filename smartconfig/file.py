import yaml

from smartconfig import _registry
from smartconfig.constructors import _ref_constructor
from smartconfig.typehints import YAMLStructure, _FilePath


def _recursively_update_mapping(source: YAMLStructure, dest: YAMLStructure) -> YAMLStructure:
    """
    Recursively update the dest mapping with source.

    If a key contains a dot, it will be considered as two nested dictionaries.

    Args:
        source: The update to apply.
        dest: The mapping to update.

    Returns:
        The modified dest mapping.
    """
    for key, value in source.items():
        if '.' in key:
            key, child_node = key.split('.', maxsplit=1)
            dest[key] = _recursively_update_mapping({child_node: value}, dest.get(key, {}))

        elif isinstance(value, dict):
            dest[key] = _recursively_update_mapping(value, dest.get(key, {}))
        else:
            dest[key] = value

    return dest


def load(path: _FilePath) -> None:
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

    _registry.global_configuration = _recursively_update_mapping(yaml_content, _registry.global_configuration)


yaml.FullLoader.add_constructor("!REF", _ref_constructor)

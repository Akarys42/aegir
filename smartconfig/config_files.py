from typing import List

import yaml

from smartconfig._registry import registry
from smartconfig.typehints import _EntryMappingRegister, _FilePath


def _restructure_yaml(
        yaml_content: ...,
        node_name: str,
        node_path: List[str] = None,
        result: _EntryMappingRegister = None
) -> _EntryMappingRegister:
    """
    Recursively fold the dictionary structure given by the YAML parser into a dotted path.

    Args:
        yaml_content: The YAML dictionary structure containing the node to process.
        node_name: The name of the node to process.
        node_path: List of all the nodes needed to access this particular node.
        result: The output constructed so far.

    Returns:
         `result` will all the subnodes of `node_name` converted to a dotted path.
    """
    if not node_path:
        node_path = []
    if not result:
        result = {}

    for subnode_name, subnode_value in yaml_content[node_name].items():
        if isinstance(yaml_content[node_name][subnode_name], dict):
            result = _restructure_yaml(
                yaml_content[node_name],
                subnode_name,
                node_path + [node_name],
                result
            )
        else:
            path = '.'.join(node_path + [node_name])

            if path not in result:
                result[path] = {}
            result[path][subnode_name] = subnode_value

    return result


def load_config_file(path: _FilePath) -> None:
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
        yaml_content = yaml.load(file, Loader=yaml.FullLoader)

    for rootnode_name, rootnode_content in yaml_content.items():
        if not isinstance(rootnode_content, dict):
            raise ...

        restructured_yaml = _restructure_yaml(yaml_content, rootnode_name)

        for path, patch in restructured_yaml.items():
            # Update the global registry.
            if path not in registry.global_configuration:
                registry.global_configuration[path] = {}
            registry.global_configuration[path].update(patch)

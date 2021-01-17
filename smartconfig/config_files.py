from typing import List

import yaml

from smartconfig._registry import registry
from smartconfig.typehints import _EntryMappingRegister, _FilePath


def _restructure_yaml(
        node: ...,
        node_path: List[str] = None,
        result: _EntryMappingRegister = None
) -> _EntryMappingRegister:
    """
    Recursively fold the dictionary structure given by the YAML parser into a dotted path.

    Args:
        node: The YAML dictionary structure of the node to process.
        node_path: List of all the nodes needed to access this particular node, including the node itself.
        result: The output constructed so far.

    Returns:
         `result` will all the subnodes of `node_name` converted to a dotted path.
    """
    if not node_path:
        node_path = []
    if not result:
        result = {}

    for child_node_name, child_node_value in node.items():
        if isinstance(node[child_node_name], dict):
            result = _restructure_yaml(
                child_node_value,
                node_path + [child_node_name],
                result
            )
        else:
            path = '.'.join(node_path)

            if path not in result:
                result[path] = {}
            result[path][child_node_name] = child_node_value

    return result


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

    for root_node_name, root_node_value in yaml_content.items():
        if not isinstance(root_node_value, dict):
            raise ...

        restructured_yaml = _restructure_yaml(root_node_value, [root_node_name])

        for path, patch in restructured_yaml.items():
            # Update the global registry.
            if path not in registry.global_configuration:
                registry.global_configuration[path] = {}
            registry.global_configuration[path].update(patch)

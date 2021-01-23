from typing import Any

import yaml

from smartconfig import _registry
from smartconfig.exceptions import ConfigurationKeyError


class AttributeReference:
    """
    A descriptor referencing another attribute.

    Args:
        path: A comma separated path to the attribute you want to reference.
    """

    def __init__(self, path: str) -> None:
        if '.' in path:
            self.path, self.attribute = path.rsplit('.', maxsplit=1)
        else:
            self.path = path
            self.attribute = None

    def __get__(self, *_) -> Any:
        if self.path not in _registry.global_configuration:
            raise ConfigurationKeyError(f"Configuration path {self.path} isn't defined.")

        if self.attribute:
            if self.attribute not in _registry.global_configuration[self.path]:
                raise ConfigurationKeyError(f"Entry {self.path} doesn't define any {self.attribute} entry.")

            return _registry.global_configuration[self.path][self.attribute]
        else:
            return _registry.global_configuration[self.path]

    def __set__(self, *_) -> None:
        return

    def __repr__(self):
        return f"{self.__class__.__name__}(path={self.path}.{self.attribute})"


def _ref_constructor(loader: yaml.SafeLoader, node: yaml.Node) -> AttributeReference:
    """Return a descriptor which references another node."""
    return AttributeReference(node.value)

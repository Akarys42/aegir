from typing import Any

import yaml

from smartconfig._registry import lookup_global_configuration


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
        return lookup_global_configuration(self.path, self.attribute)

    def __set__(self, *_) -> None:
        return

    def __repr__(self):
        return f"{self.__class__.__name__}(path={self.path}.{self.attribute})"


def _ref_constructor(loader: yaml.SafeLoader, node: yaml.Node) -> AttributeReference:
    """Return a descriptor which references another node."""
    return AttributeReference(node.value)

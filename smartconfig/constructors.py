from typing import Any

import yaml

from smartconfig.exceptions import InvalidOperation
from smartconfig._registry import get_attribute, get_node

_used_constructors = set()


class AttributeReference:
    """
    A descriptor referencing another attribute.

    Args:
        path: A comma separated path to the attribute you want to reference.
    """

    def __init__(self, path: str) -> None:
        if path in _used_constructors:
            raise InvalidOperation("Cannot point a REF constructor to another one.")
        _used_constructors.add(path)

        if '.' in path:
            self.path, self.attribute = path.rsplit('.', maxsplit=1)
        else:
            self.path = path
            self.attribute = None

    def __get__(self, *_) -> Any:
        if self.attribute is not None:
            return get_attribute(self.path, self.attribute)
        else:
            return get_node(self.path)

    def __set__(self, *_) -> None:
        return

    def __repr__(self):
        return f"{self.__class__.__name__}(path={self.path}.{self.attribute})"


def _ref_constructor(loader: yaml.SafeLoader, node: yaml.Node) -> AttributeReference:
    """Return a descriptor which references another node."""
    return AttributeReference(node.value)
